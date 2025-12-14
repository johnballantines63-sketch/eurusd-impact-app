#!/usr/bin/env python3
"""
CALCUL DES IMPACTS GROUPÉS PAR MINUTE

Objectif : Corriger l'erreur du script calculate_real_impacts.py qui calculait
           les impacts individuellement au lieu de par groupe temporel.

Principe :
  1. Grouper les événements par minute (time_group)
  2. Calculer UN SEUL impact par groupe temporel
  3. Stocker avec la liste des événements du groupe

Métrique utilisée : RANGE TOTAL
  - Range = Prix_Max - Prix_Min dans la fenêtre d'observation
  - Mesure la violence totale du mouvement
  - Exemple 11 sept : 111.5 pips (vs 59.2 pips du script incorrect)

Durée estimée : 10-20 minutes pour tous les événements groupés
"""

import duckdb
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    print("⚠️ tqdm non installé - pas de barre de progression")
import warnings
warnings.filterwarnings('ignore')


def calculate_group_impact(time_group, prices_df, lookback_minutes=5, lookforward_minutes=60):
    """
    Calcule l'impact réel d'un GROUPE d'événements simultanés
    
    Args:
        time_group: Timestamp du groupe (minute exacte, ex: 14:30:00)
        prices_df: DataFrame avec colonnes [datetime, close]
        lookback_minutes: Minutes avant pour prix de référence
        lookforward_minutes: Minutes après pour observer le mouvement
    
    Returns:
        dict avec mfe_pips (range), mae_pips, ttr_minutes, direction, etc.
        ou None si données insuffisantes
    """
    try:
        # 1. Prix de référence (5 min avant le groupe)
        ref_time = time_group - timedelta(minutes=lookback_minutes)
        ref_prices = prices_df[
            (prices_df['datetime'] >= ref_time - timedelta(minutes=5)) &
            (prices_df['datetime'] <= ref_time)
        ]
        
        if len(ref_prices) == 0:
            return None
        
        reference_price = ref_prices['close'].iloc[-1]
        
        # 2. Prix dans la fenêtre d'observation (après le groupe)
        window_start = time_group
        window_end = time_group + timedelta(minutes=lookforward_minutes)
        
        window_prices = prices_df[
            (prices_df['datetime'] >= window_start) &
            (prices_df['datetime'] <= window_end)
        ]
        
        if len(window_prices) == 0:
            return None
        
        # 3. Trouver les extrêmes
        max_price = window_prices['close'].max()
        min_price = window_prices['close'].min()
        
        # Index des extrêmes
        max_idx = window_prices['close'].idxmax()
        min_idx = window_prices['close'].idxmin()
        
        # Timestamps des extrêmes
        max_time = window_prices.loc[max_idx, 'datetime']
        min_time = window_prices.loc[min_idx, 'datetime']
        
        # 4. Calculer le RANGE TOTAL (métrique principale)
        range_pips = abs(max_price - min_price) / 0.0001
        
        # 5. Déterminer la direction dominante
        # Direction = sens du mouvement net depuis la référence
        final_price = window_prices['close'].iloc[-1]
        net_movement = (final_price - reference_price) / 0.0001
        
        if net_movement > 0:
            direction = 'UP'
            # MFE = mouvement haussier max
            mfe_pips = (max_price - reference_price) / 0.0001
            # MAE = mouvement baissier max (adverse)
            mae_pips = abs((min_price - reference_price) / 0.0001)
            peak_price = max_price
            peak_time = max_time
        else:
            direction = 'DOWN'
            # MFE = mouvement baissier max
            mfe_pips = abs((min_price - reference_price) / 0.0001)
            # MAE = mouvement haussier max (adverse)
            mae_pips = (max_price - reference_price) / 0.0001
            peak_price = min_price
            peak_time = min_time
        
        # 6. TTR (Time To Return) - Temps pour revenir proche de référence
        # Chercher après le pic
        prices_after_peak = prices_df[
            (prices_df['datetime'] > peak_time) &
            (prices_df['datetime'] <= window_end)
        ]
        
        ttr_minutes = None
        if len(prices_after_peak) > 0:
            # Tolérance : ±3 pips
            tolerance = 3
            returns = prices_after_peak[
                abs((prices_after_peak['close'] - reference_price) / 0.0001) <= tolerance
            ]
            
            if len(returns) > 0:
                return_time = returns['datetime'].iloc[0]
                ttr_minutes = (return_time - time_group).total_seconds() / 60
        
        return {
            'mfe_pips': round(mfe_pips, 2),
            'mae_pips': round(mae_pips, 2),
            'range_pips': round(range_pips, 2),  # Range total
            'ttr_minutes': round(ttr_minutes, 1) if ttr_minutes else None,
            'direction': direction,
            'reference_price': reference_price,
            'peak_price': peak_price,
            'peak_time': peak_time,
            'max_price': max_price,
            'min_price': min_price,
            'final_price': final_price,
            'net_movement_pips': round(net_movement, 2)
        }
    
    except Exception as e:
        print(f"Erreur calcul impact groupe: {e}")
        return None


def detect_phases(grouped_impacts, min_gap_minutes=5):
    """
    Détecte les phases successives dans une séquence de groupes temporels
    
    Args:
        grouped_impacts: DataFrame des impacts groupés, triés par time_group
        min_gap_minutes: Gap minimum pour considérer une nouvelle phase
    
    Returns:
        List de listes, chaque sous-liste contient les indices des groupes d'une phase
    """
    if len(grouped_impacts) == 0:
        return []
    
    phases = []
    current_phase = [0]
    
    for i in range(1, len(grouped_impacts)):
        prev_time = grouped_impacts.iloc[i-1]['time_group']
        curr_time = grouped_impacts.iloc[i]['time_group']
        
        gap_minutes = (curr_time - prev_time).total_seconds() / 60
        
        if gap_minutes > min_gap_minutes:
            # Nouvelle phase
            phases.append(current_phase)
            current_phase = [i]
        else:
            # Même phase
            current_phase.append(i)
    
    # Ajouter la dernière phase
    if current_phase:
        phases.append(current_phase)
    
    return phases


def main():
    """Fonction principale"""
    
    print("=" * 80)
    print("📊 CALCUL DES IMPACTS GROUPÉS PAR MINUTE (CORRECTION SESSION 8)")
    print("=" * 80)
    
    # Connexion à la base de données
    conn = duckdb.connect('fx_impact_app/data/warehouse.duckdb', read_only=False)
    
    # 1. Charger tous les événements
    print("\n1️⃣ Chargement des événements...")
    
    events_query = """
    SELECT 
        e.ts_utc,
        e.event_key,
        e.event_title,
        e.country,
        e.actual,
        e.forecast,
        e.estimate,
        e.previous,
        ef.family,
        ef.empirical_score,
        ef.impact_level
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE e.ts_utc >= '2024-01-01'
        AND ef.empirical_score IS NOT NULL
        AND ef.empirical_score > 0
    ORDER BY e.ts_utc
    """
    
    events_df = conn.execute(events_query).fetchdf()
    print(f"   ✅ {len(events_df)} événements chargés")
    
    # Convertir en datetime
    if not pd.api.types.is_datetime64_any_dtype(events_df['ts_utc']):
        events_df['ts_utc'] = pd.to_datetime(events_df['ts_utc'])
    
    # 2. Grouper les événements par minute
    print("\n2️⃣ Groupement des événements par minute...")
    
    # Arrondir à la minute (floor)
    events_df['time_group'] = events_df['ts_utc'].dt.floor('1min')
    
    # Grouper et compter
    grouped = events_df.groupby('time_group')
    print(f"   ✅ {len(grouped)} groupes temporels identifiés")
    
    # Statistiques des groupes
    group_sizes = grouped.size()
    print(f"\n   📊 Distribution des tailles de groupes:")
    print(f"      • Groupes avec 1 événement : {(group_sizes == 1).sum()}")
    print(f"      • Groupes avec 2-5 événements : {((group_sizes >= 2) & (group_sizes <= 5)).sum()}")
    print(f"      • Groupes avec 6-10 événements : {((group_sizes >= 6) & (group_sizes <= 10)).sum()}")
    print(f"      • Groupes avec 11+ événements : {(group_sizes >= 11).sum()}")
    print(f"      • Groupe maximum : {group_sizes.max()} événements")
    
    # 3. Charger tous les prix
    print("\n3️⃣ Chargement des prix minute par minute...")
    
    prices_query = """
    SELECT 
        datetime,
        close
    FROM prices_1m
    WHERE datetime >= '2024-01-01'
    ORDER BY datetime
    """
    
    prices_df = conn.execute(prices_query).fetchdf()
    print(f"   ✅ {len(prices_df)} minutes de prix chargées")
    
    # Convertir en datetime
    if not pd.api.types.is_datetime64_any_dtype(prices_df['datetime']):
        prices_df['datetime'] = pd.to_datetime(prices_df['datetime'])
    
    # 4. Calculer les impacts pour chaque GROUPE
    print("\n4️⃣ Calcul des impacts PAR GROUPE (pas par événement)...")
    print("    Cela devrait être beaucoup plus rapide (~10-20 min)...")
    
    results = []
    
    if HAS_TQDM:
        iterator = tqdm(grouped, total=len(grouped), desc="   Calcul groupes")
    else:
        iterator = grouped
        print("    Progression :")
    
    for time_group, group_events in iterator:
        # Calculer l'impact du GROUPE
        impact = calculate_group_impact(
            time_group,
            prices_df,
            lookback_minutes=5,
            lookforward_minutes=60
        )
        
        if impact is not None:
            # Agréger les informations du groupe
            results.append({
                'time_group': time_group,
                'num_events': len(group_events),
                'event_keys': ','.join(group_events['event_key'].astype(str).tolist()),
                'event_titles': ' | '.join(group_events['event_title'].astype(str).tolist()[:3]),  # Max 3 titres
                'countries': ','.join(sorted(set(group_events['country'].dropna().tolist()))),
                'families': ','.join(sorted(set(group_events['family'].dropna().tolist()))),
                'max_empirical_score': group_events['empirical_score'].max(),
                'mean_empirical_score': group_events['empirical_score'].mean(),
                'impact_levels': ','.join(sorted(set(group_events['impact_level'].dropna().tolist()))),
                
                # Impacts calculés
                'mfe_pips': impact['mfe_pips'],
                'mae_pips': impact['mae_pips'],
                'range_pips': impact['range_pips'],
                'ttr_minutes': impact['ttr_minutes'],
                'direction': impact['direction'],
                'net_movement_pips': impact['net_movement_pips'],
                
                # Prix
                'reference_price': impact['reference_price'],
                'peak_price': impact['peak_price'],
                'peak_time': impact['peak_time'],
                'max_price': impact['max_price'],
                'min_price': impact['min_price'],
                'final_price': impact['final_price'],
                
                # Métadonnées
                'lookforward_window': 60,
                'calculation_date': datetime.now()
            })
        
        # Checkpoint tous les 100 groupes
        if len(results) > 0 and len(results) % 100 == 0 and not HAS_TQDM:
            print(f"      {len(results)} groupes calculés...")
    
    print(f"\n   ✅ {len(results)} impacts de groupes calculés avec succès")
    print(f"   ⚠️ {len(grouped) - len(results)} groupes sans données de prix")
    
    # 5. Créer la table des impacts groupés
    print("\n5️⃣ Création de la table event_group_impacts...")
    
    results_df = pd.DataFrame(results)
    
    # Supprimer la table si elle existe déjà
    conn.execute("DROP TABLE IF EXISTS event_group_impacts")
    
    # Créer la nouvelle table
    conn.execute("""
        CREATE TABLE event_group_impacts AS 
        SELECT * FROM results_df
    """)
    
    print(f"   ✅ Table créée avec {len(results_df)} lignes")
    
    # 6. Statistiques par niveau d'impact
    print("\n6️⃣ Statistiques des impacts groupés:")
    
    # Créer colonne dominant_impact_level
    results_df['dominant_impact_level'] = results_df['impact_levels'].str.split(',').str[0]
    
    stats = results_df.groupby('dominant_impact_level').agg({
        'range_pips': ['count', 'mean', 'median', 'std', 'min', 'max'],
        'mfe_pips': ['mean', 'median'],
        'mae_pips': ['mean', 'median'],
        'ttr_minutes': ['mean', 'median'],
        'num_events': ['mean', 'max']
    }).round(2)
    
    print(stats)
    
    # 7. Exemple du 11 septembre 2025
    print("\n7️⃣ Validation : 11 septembre 2025")
    
    sept_11_query = """
    SELECT 
        strftime(time_group, '%H:%M:%S') as time,
        num_events,
        event_titles,
        max_empirical_score,
        range_pips,
        mfe_pips,
        mae_pips,
        ttr_minutes,
        direction,
        net_movement_pips
    FROM event_group_impacts
    WHERE CAST(time_group AS DATE) = '2025-09-11'
    ORDER BY time_group
    """
    
    sept_11_data = conn.execute(sept_11_query).fetchdf()
    
    if len(sept_11_data) > 0:
        print(f"\n   📊 {len(sept_11_data)} groupes trouvés le 11 septembre 2025:")
        print(sept_11_data.to_string(index=False))
        
        # Vérification critique : le groupe de 14:30
        group_1430 = sept_11_data[sept_11_data['time'] == '14:30:00']
        if len(group_1430) > 0:
            print(f"\n   🎯 VALIDATION CRITIQUE - Groupe 14:30:")
            print(f"      • Nombre d'événements : {group_1430['num_events'].iloc[0]}")
            print(f"      • Range calculé : {group_1430['range_pips'].iloc[0]:.1f} pips")
            print(f"      • MFE : {group_1430['mfe_pips'].iloc[0]:.1f} pips")
            print(f"      • Direction : {group_1430['direction'].iloc[0]}")
            print(f"\n      📏 Comparaison avec MT5:")
            print(f"      • MT5 mesuré : 111.5 pips (range)")
            print(f"      • Script v7 : 59.2 pips (incorrect)")
            print(f"      • Script v8 : {group_1430['range_pips'].iloc[0]:.1f} pips ← Nouveau calcul")
            
            diff_pct = abs(group_1430['range_pips'].iloc[0] - 111.5) / 111.5 * 100
            if diff_pct < 10:
                print(f"      ✅ Écart avec MT5 : {diff_pct:.1f}% (excellent !)")
            elif diff_pct < 20:
                print(f"      ⚠️ Écart avec MT5 : {diff_pct:.1f}% (acceptable)")
            else:
                print(f"      ❌ Écart avec MT5 : {diff_pct:.1f}% (à investiguer)")
    else:
        print("   ⚠️ Pas de données pour le 11 septembre 2025")
    
    # 8. Détection des phases
    print("\n8️⃣ Détection des phases successives...")
    
    # Exemple : détecter phases sur le 11 septembre
    if len(sept_11_data) > 0:
        sept_11_full = results_df[
            results_df['time_group'].dt.date == pd.to_datetime('2025-09-11').date()
        ].sort_values('time_group').reset_index(drop=True)
        
        phases = detect_phases(sept_11_full, min_gap_minutes=5)
        print(f"   ✅ {len(phases)} phases détectées le 11 septembre:")
        
        for phase_idx, phase_indices in enumerate(phases, 1):
            phase_groups = sept_11_full.iloc[phase_indices]
            times = [t.strftime('%H:%M') for t in phase_groups['time_group']]
            total_events = phase_groups['num_events'].sum()
            total_range = phase_groups['range_pips'].sum()
            
            print(f"      Phase {phase_idx}: {times[0]} → {times[-1]}")
            print(f"         • {len(phase_indices)} groupes, {total_events} événements")
            print(f"         • Range total: {total_range:.1f} pips")
    
    # 9. Comparaison avec l'ancien calcul
    print("\n9️⃣ Comparaison avec ancien calcul (calculate_real_impacts)...")
    
    # Vérifier si l'ancienne table existe
    try:
        old_table_check = conn.execute("""
            SELECT COUNT(*) as n 
            FROM information_schema.tables 
            WHERE table_name = 'event_impacts_calculated'
        """).fetchdf()
        
        if old_table_check['n'].iloc[0] > 0:
            comparison_query = """
            SELECT 
                'Ancien (individuel)' as method,
                COUNT(*) as n_lignes,
                AVG(mfe_pips) as avg_mfe,
                MAX(mfe_pips) as max_mfe
            FROM event_impacts_calculated
            WHERE CAST(ts_utc AS DATE) = '2025-09-11'
            
            UNION ALL
            
            SELECT 
                'Nouveau (groupé)' as method,
                COUNT(*) as n_lignes,
                AVG(range_pips) as avg_mfe,
                MAX(range_pips) as max_mfe
            FROM event_group_impacts
            WHERE CAST(time_group AS DATE) = '2025-09-11'
            """
            
            comparison = conn.execute(comparison_query).fetchdf()
            print(comparison.to_string(index=False))
            
            print(f"\n   💡 Observation:")
            print(f"      L'ancien calcul créait {comparison.iloc[0]['n_lignes']:.0f} lignes")
            print(f"      Le nouveau calcul crée {comparison.iloc[1]['n_lignes']:.0f} groupes")
            print(f"      → Réduction de {(1 - comparison.iloc[1]['n_lignes']/comparison.iloc[0]['n_lignes'])*100:.0f}%")
        else:
            print("   ⚠️ Table event_impacts_calculated non trouvée (normal si pas encore exécuté)")
    
    except Exception as e:
        print(f"   ⚠️ Impossible de comparer avec ancien calcul: {e}")
    
    # 10. Créer des index
    print("\n🔟 Création des index...")
    
    try:
        conn.execute("CREATE INDEX idx_group_impacts_time ON event_group_impacts(time_group)")
        conn.execute("CREATE INDEX idx_group_impacts_date ON event_group_impacts(CAST(time_group AS DATE))")
        print("   ✅ Index créés")
    except Exception as e:
        print(f"   ⚠️ Erreur création index: {e}")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ CALCUL TERMINÉ")
    print("=" * 80)
    print(f"\n📊 Résumé:")
    print(f"   • Événements analysés : {len(events_df)}")
    print(f"   • Groupes temporels : {len(grouped)}")
    print(f"   • Impacts groupés calculés : {len(results_df)}")
    print(f"   • Taux de succès : {len(results_df)/len(grouped)*100:.1f}%")
    print(f"\n💾 Table créée : event_group_impacts")
    print(f"   Colonnes : time_group, num_events, range_pips, mfe_pips, direction, etc.")
    print(f"\n🎯 Différence clé avec ancien script:")
    print(f"   • Ancien : 1 ligne par événement (dupliquait le MFE)")
    print(f"   • Nouveau : 1 ligne par groupe temporel (impact unique)")
    print(f"\n🚀 Prochaine étape : Ré-analyser et générer formule v9")

if __name__ == '__main__':
    main()
