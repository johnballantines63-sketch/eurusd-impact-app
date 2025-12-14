"""
Script d'Analyse Empirique des Événements Multiples
Objectif : Observer le comportement réel du marché lors d'événements simultanés

Date de création : 14 Octobre 2025
Contexte : Analyse des bugs d'amplitude et pullback manquant

Version 2 : Adapté au schéma réel de la base de données
"""

import duckdb
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Ajouter le chemin pour importer config depuis fx_impact_app/src
project_root = Path(__file__).parent
fx_app_src = project_root / "fx_impact_app" / "src"
sys.path.insert(0, str(fx_app_src))

try:
    from config import get_db_path
except ImportError as e:
    print(f"❌ Erreur : Impossible d'importer config.py depuis {fx_app_src}")
    print(f"   Erreur détaillée : {e}")
    print("   Utilisation du chemin par défaut...")
    def get_db_path():
        return str(project_root / "fx_impact_app" / "data" / "warehouse.duckdb")


def find_multi_events_days(time_gap_minutes=15):
    """
    Identifie les jours avec événements multiples (écart < time_gap_minutes)
    
    Returns:
        DataFrame avec date, nombre d'événements, liste des familles
    """
    
    try:
        conn = duckdb.connect(get_db_path(), read_only=True)
    except Exception as e:
        print(f"❌ Erreur connexion DB : {e}")
        return pd.DataFrame()
    
    # Calculer la surprise dans la requête
    query = f"""
    WITH events_with_surprise AS (
        SELECT 
            DATE(ts_utc) as event_date,
            ts_utc,
            event_title,
            country,
            actual,
            forecast,
            estimate,
            previous,
            -- Calculer la surprise : actual - estimate (forecast est toujours NULL)
            CASE 
                WHEN actual IS NOT NULL AND estimate IS NOT NULL THEN actual - estimate
                ELSE NULL
            END as surprise,
            LAG(ts_utc) OVER (ORDER BY ts_utc) as prev_time,
            EXTRACT(EPOCH FROM (ts_utc - LAG(ts_utc) OVER (ORDER BY ts_utc))) / 60 as gap_minutes
        FROM events
        WHERE actual IS NOT NULL
            AND (country = 'US' OR country IN ('EU', 'DE', 'FR', 'IT', 'ES'))
            AND (importance_n >= 1 OR importance_n IS NOT NULL)
        ORDER BY ts_utc
    ),
    multi_event_groups AS (
        SELECT 
            event_date,
            ts_utc,
            event_title,
            country,
            surprise,
            gap_minutes,
            CASE 
                WHEN gap_minutes <= {time_gap_minutes} THEN 1 
                ELSE 0 
            END as is_multi
        FROM events_with_surprise
        WHERE surprise IS NOT NULL
    )
    SELECT 
        event_date,
        COUNT(*) as num_events,
        STRING_AGG(COALESCE(event_title, 'Unknown') || ' (' || country || ')', ', ') as events_list,
        STRING_AGG(CAST(ts_utc AS VARCHAR), ', ') as timestamps,
        SUM(is_multi) as num_simultaneous
    FROM multi_event_groups
    WHERE is_multi = 1
    GROUP BY event_date
    HAVING COUNT(*) >= 2
    ORDER BY event_date DESC
    LIMIT 50
    """
    
    try:
        df = conn.execute(query).df()
        conn.close()
        return df
    except Exception as e:
        print(f"❌ Erreur requête : {e}")
        import traceback
        traceback.print_exc()
        conn.close()
        return pd.DataFrame()


def analyze_specific_day(date_str, time_gap_minutes=15):
    """
    Analyse détaillée d'une journée spécifique avec événements multiples
    
    Args:
        date_str: Date au format 'YYYY-MM-DD'
    
    Returns:
        Dict avec événements, prix réels, et métriques calculées
    """
    
    try:
        conn = duckdb.connect(get_db_path(), read_only=True)
    except Exception as e:
        print(f"❌ Erreur connexion DB : {e}")
        return None
    
    # 1. Récupérer les événements du jour avec surprise calculée
    query_events = f"""
    SELECT 
        ts_utc,
        event_title,
        country,
        actual,
        forecast,
        estimate,
        previous,
        CASE 
            WHEN actual IS NOT NULL AND estimate IS NOT NULL THEN actual - estimate
            ELSE NULL
        END as surprise
    FROM events
    WHERE DATE(ts_utc) = '{date_str}'
        AND actual IS NOT NULL
        AND (country = 'US' OR country IN ('EU', 'DE', 'FR', 'IT', 'ES'))
        AND (importance_n >= 1 OR importance_n IS NOT NULL)
    ORDER BY ts_utc
    """
    
    try:
        events_df = conn.execute(query_events).df()
    except Exception as e:
        print(f"❌ Erreur requête événements : {e}")
        conn.close()
        return None
    
    if len(events_df) == 0:
        conn.close()
        return None
    
    # Filtrer les événements avec surprise
    events_df = events_df[events_df['surprise'].notna()]
    
    if len(events_df) == 0:
        conn.close()
        return None
    
    # 2. Grouper les événements simultanés (gap <= time_gap_minutes)
    events_df['ts_utc'] = pd.to_datetime(events_df['ts_utc'])
    events_df = events_df.sort_values('ts_utc')
    
    phase_groups = []
    current_group = [events_df.iloc[0].to_dict()]
    
    for i in range(1, len(events_df)):
        prev_time = events_df.iloc[i-1]['ts_utc']
        curr_time = events_df.iloc[i]['ts_utc']
        gap = (curr_time - prev_time).total_seconds() / 60
        
        if gap <= time_gap_minutes:
            current_group.append(events_df.iloc[i].to_dict())
        else:
            if len(current_group) > 0:
                phase_groups.append(current_group)
            current_group = [events_df.iloc[i].to_dict()]
    
    if len(current_group) > 0:
        phase_groups.append(current_group)
    
    # 3. Pour chaque groupe, récupérer les prix réels
    analysis_results = {
        'date': date_str,
        'num_phases': len(phase_groups),
        'phases': []
    }
    
    for phase_idx, group in enumerate(phase_groups):
        phase_start = group[0]['ts_utc']
        
        # Récupérer prix de -10 min à +60 min depuis prices_1m
        query_prices = f"""
        SELECT 
            datetime,
            open,
            high,
            low,
            close
        FROM prices_1m
        WHERE datetime >= '{phase_start - timedelta(minutes=10)}'
            AND datetime <= '{phase_start + timedelta(minutes=60)}'
        ORDER BY datetime
        """
        
        try:
            prices_df = conn.execute(query_prices).df()
            
            if len(prices_df) > 0:
                # Calculer métriques
                prices_df['datetime'] = pd.to_datetime(prices_df['datetime'])
                start_price = prices_df.iloc[0]['close']
                
                # Trouver le peak dans les 30 premières minutes
                phase_prices = prices_df.head(30)
                max_price = phase_prices['high'].max()
                min_price = phase_prices['low'].min()
                
                max_movement = (max_price - start_price) * 10000
                min_movement = (min_price - start_price) * 10000
                
                # Direction dominante
                if abs(max_movement) > abs(min_movement):
                    dominant_direction = 'UP'
                    dominant_movement = max_movement
                    peak_price = max_price
                else:
                    dominant_direction = 'DOWN'
                    dominant_movement = min_movement
                    peak_price = min_price
                
                # TTR réel (où le prix retrace de 20% du mouvement)
                ttr_real = None
                for idx in range(len(phase_prices)):
                    current_price = phase_prices.iloc[idx]['close']
                    
                    if dominant_direction == 'UP':
                        retracement = (peak_price - current_price) * 10000
                    else:
                        retracement = (current_price - peak_price) * 10000
                    
                    if retracement > abs(dominant_movement) * 0.20:
                        ttr_real = idx
                        break
                
                phase_info = {
                    'phase_num': phase_idx + 1,
                    'start_time': str(phase_start),
                    'num_events': len(group),
                    'events': [
                        {
                            'title': evt['event_title'] if evt['event_title'] else 'Unknown',
                            'country': evt['country'],
                            'surprise': float(evt['surprise'])
                        }
                        for evt in group
                    ],
                    'start_price': float(start_price),
                    'peak_price': float(peak_price),
                    'dominant_direction': dominant_direction,
                    'dominant_movement_pips': float(dominant_movement),
                    'ttr_real_minutes': int(ttr_real) if ttr_real else None,
                    'prices_available': True
                }
                
            else:
                phase_info = {
                    'phase_num': phase_idx + 1,
                    'start_time': str(phase_start),
                    'num_events': len(group),
                    'events': [
                        {
                            'title': evt['event_title'] if evt['event_title'] else 'Unknown',
                            'country': evt['country'],
                            'surprise': float(evt['surprise'])
                        }
                        for evt in group
                    ],
                    'prices_available': False
                }
        
        except Exception as e:
            phase_info = {
                'phase_num': phase_idx + 1,
                'error': str(e),
                'prices_available': False
            }
        
        analysis_results['phases'].append(phase_info)
    
    conn.close()
    
    return analysis_results


def analyze_multi_phase_interactions(results):
    """
    Analyse les interactions entre phases pour un jour donné
    """
    
    if results is None or results['num_phases'] < 2:
        return None
    
    interactions = {
        'date': results['date'],
        'num_phases': results['num_phases'],
        'phase_comparisons': []
    }
    
    for i in range(len(results['phases']) - 1):
        phase1 = results['phases'][i]
        phase2 = results['phases'][i + 1]
        
        if not (phase1.get('prices_available') and phase2.get('prices_available')):
            continue
        
        # Analyser la transition Phase 1 → Phase 2
        phase1_movement = phase1['dominant_movement_pips']
        phase2_movement = phase2['dominant_movement_pips']
        
        # Calculer si même direction
        same_direction = (
            (phase1['dominant_direction'] == 'UP' and phase2['dominant_direction'] == 'UP') or
            (phase1['dominant_direction'] == 'DOWN' and phase2['dominant_direction'] == 'DOWN')
        )
        
        # Si même direction, observer l'atténuation
        if same_direction:
            expected_combined = abs(phase1_movement) + abs(phase2_movement)
            actual_net = abs(phase2['peak_price'] - phase1['start_price']) * 10000
            attenuation_factor = actual_net / expected_combined if expected_combined > 0 else 0
        else:
            expected_combined = abs(phase1_movement) - abs(phase2_movement)
            actual_net = abs(phase2['peak_price'] - phase1['start_price']) * 10000
            attenuation_factor = None  # Non applicable pour directions opposées
        
        comparison = {
            'phase1_movement': phase1_movement,
            'phase2_movement': phase2_movement,
            'same_direction': same_direction,
            'expected_combined_pips': expected_combined if same_direction else None,
            'actual_net_pips': actual_net,
            'attenuation_factor': attenuation_factor,
            'note': (
                f"Même direction : Atténuation de {attenuation_factor:.2%}" 
                if same_direction and attenuation_factor 
                else "Directions opposées"
            )
        }
        
        interactions['phase_comparisons'].append(comparison)
    
    return interactions


def main():
    """
    Fonction principale d'analyse empirique
    """
    
    print("=" * 80)
    print("ANALYSE EMPIRIQUE DES ÉVÉNEMENTS MULTIPLES")
    print("=" * 80)
    print()
    
    # Étape 1 : Trouver les jours avec événements multiples
    print("📊 Étape 1 : Identification des jours avec événements multiples...")
    multi_days = find_multi_events_days(time_gap_minutes=15)
    
    if len(multi_days) == 0:
        print("❌ Aucun jour avec événements multiples trouvé")
        return
    
    print(f"\n✅ Trouvé {len(multi_days)} jours avec événements multiples (gap ≤ 15 min)\n")
    print(multi_days.head(10).to_string())
    print()
    
    # Étape 2 : Analyser les 5-10 jours les plus récents en détail
    print("=" * 80)
    print("📊 Étape 2 : Analyse détaillée des cas récents...")
    print("=" * 80)
    print()
    
    detailed_analyses = []
    
    for idx, row in multi_days.head(10).iterrows():
        date_str = str(row['event_date'])
        print(f"\n🔍 Analyse du {date_str}...")
        print(f"   Événements : {row['events_list'][:100]}...")
        
        analysis = analyze_specific_day(date_str)
        
        if analysis:
            detailed_analyses.append(analysis)
            
            print(f"\n   ✅ {analysis['num_phases']} phase(s) identifiée(s)")
            
            for phase in analysis['phases']:
                if phase.get('prices_available'):
                    print(f"\n   Phase {phase['phase_num']} :")
                    print(f"      - {phase['num_events']} événement(s)")
                    print(f"      - Direction : {phase['dominant_direction']}")
                    print(f"      - Mouvement : {phase['dominant_movement_pips']:.1f} pips")
                    if phase['ttr_real_minutes']:
                        print(f"      - TTR réel : {phase['ttr_real_minutes']} min")
        
        print("-" * 80)
    
    # Étape 3 : Analyser les interactions entre phases
    print("\n" + "=" * 80)
    print("📊 Étape 3 : Analyse des interactions multi-phases...")
    print("=" * 80)
    print()
    
    attenuation_factors = []
    
    for analysis in detailed_analyses:
        interactions = analyze_multi_phase_interactions(analysis)
        
        if interactions:
            print(f"\n📅 {interactions['date']} - {interactions['num_phases']} phases")
            
            for comp in interactions['phase_comparisons']:
                print(f"\n   Phase 1→2 :")
                print(f"      - Phase 1 : {comp['phase1_movement']:+.1f} pips")
                print(f"      - Phase 2 : {comp['phase2_movement']:+.1f} pips")
                
                if comp['same_direction']:
                    print(f"      - Somme attendue : {comp['expected_combined_pips']:.1f} pips")
                    print(f"      - Mouvement net réel : {comp['actual_net_pips']:.1f} pips")
                    print(f"      - ⚠️ FACTEUR D'ATTÉNUATION : {comp['attenuation_factor']:.2%}")
                    
                    if comp['attenuation_factor']:
                        attenuation_factors.append(comp['attenuation_factor'])
                else:
                    print(f"      - Directions opposées (vectoriel naturel)")
    
    # Statistiques d'atténuation
    if len(attenuation_factors) > 0:
        print("\n" + "=" * 80)
        print("📊 STATISTIQUES D'ATTÉNUATION (même direction)")
        print("=" * 80)
        print()
        print(f"Nombre d'observations : {len(attenuation_factors)}")
        print(f"Facteur moyen : {sum(attenuation_factors)/len(attenuation_factors):.2%}")
        print(f"Facteur médian : {sorted(attenuation_factors)[len(attenuation_factors)//2]:.2%}")
        print(f"Min : {min(attenuation_factors):.2%}")
        print(f"Max : {max(attenuation_factors):.2%}")
        print()
        print(f"💡 RECOMMANDATION : Utiliser facteur ~{sum(attenuation_factors)/len(attenuation_factors):.2f} pour événements simultanés")
    else:
        print("\n⚠️ Aucun cas avec même direction trouvé dans cet échantillon")
    
    print("\n" + "=" * 80)
    print("✅ ANALYSE TERMINÉE")
    print("=" * 80)


if __name__ == "__main__":
    main()
