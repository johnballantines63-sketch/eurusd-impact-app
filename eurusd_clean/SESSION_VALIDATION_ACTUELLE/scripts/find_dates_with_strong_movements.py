#!/usr/bin/env python3
"""
Trouver Dates avec Mouvements Significatifs (MOYEN, FORT, TRÈS_FORT)

Objectif :
- Scanner toutes les dates avec événements HIGH US
- Détecter le mouvement réel pour chaque date
- Filtrer uniquement les mouvements >= 20 pips
- Retourner la liste des dates intéressantes pour validation

Date : 2025-12-07
"""

import sys
from pathlib import Path
import pandas as pd
import duckdb
from datetime import datetime, timedelta
from typing import List, Dict, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

DB_PATH = Path('../fx_impact_app/data/warehouse.duckdb')

# Seuils de classification
MOVEMENT_THRESHOLDS = {
    'FAIBLE': 20.0,      # < 20 pips
    'MOYEN': 50.0,       # 20-50 pips
    'FORT': 100.0,       # 50-100 pips
    'TRÈS_FORT': float('inf')  # >= 100 pips
}


def classify_movement(impact_pips: float) -> str:
    """Classifie le mouvement selon son impact"""
    if impact_pips < 20.0:
        return 'FAIBLE'
    elif impact_pips < 50.0:
        return 'MOYEN'
    elif impact_pips < 100.0:
        return 'FORT'
    else:
        return 'TRÈS_FORT'


def detect_movement_for_date(date_str: str, event_time: datetime) -> Optional[Dict]:
    """
    Détecte le mouvement réel pour une date donnée
    Retourne None si aucun mouvement détecté ou mouvement trop faible
    """
    if not DB_PATH.exists():
        return None
    
    try:
        conn = duckdb.connect(str(DB_PATH), read_only=True)
        
        # Fenêtre de temps : 5 min avant à 120 min après
        start_time = event_time - timedelta(minutes=5)
        end_time = event_time + timedelta(minutes=120)
        
        # Charger prix depuis prices_1m_v
        query = """
        SELECT 
            ts_utc,
            close
        FROM prices_1m_v
        WHERE ts_utc >= ? AND ts_utc <= ?
        ORDER BY ts_utc
        """
        
        prices_df = conn.execute(query, [start_time, end_time]).df()
        conn.close()
        
        if len(prices_df) < 10:
            return None
        
        # Convertir ts_utc et normaliser timezone
        prices_df['ts_utc'] = pd.to_datetime(prices_df['ts_utc'])
        if prices_df['ts_utc'].dt.tz is not None:
            prices_df['ts_utc'] = prices_df['ts_utc'].dt.tz_localize(None)
        prices_df = prices_df.set_index('ts_utc')
        
        # Créer open/high/low depuis close (approximation)
        prices_df['open'] = prices_df['close'].shift(1).fillna(prices_df['close'].iloc[0])
        prices_df['high'] = prices_df[['open', 'close']].max(axis=1)
        prices_df['low'] = prices_df[['open', 'close']].min(axis=1)
        
        # Normaliser event_time
        if hasattr(event_time, 'tzinfo') and event_time.tzinfo is not None:
            event_time_naive = event_time.replace(tzinfo=None)
        else:
            event_time_naive = event_time
        
        # Trouver prix de départ
        event_idx = prices_df.index.get_indexer([event_time_naive], method='nearest')[0]
        if event_idx < 0 or event_idx >= len(prices_df):
            return None
        
        # Prix de départ
        if event_idx > 0:
            start_price = prices_df.iloc[event_idx - 1]['close']
        else:
            start_price = prices_df.iloc[event_idx]['open']
        
        # Chercher pic dans les 120 minutes suivantes
        window_df = prices_df.iloc[event_idx:event_idx+120]
        
        if len(window_df) == 0:
            return None
        
        # Pic haut et bas
        peak_high = window_df['high'].max()
        peak_low = window_df['low'].min()
        
        # Direction
        move_up = peak_high - start_price
        move_down = start_price - peak_low
        
        if move_up > move_down:
            direction = 'UP'
            peak_pips = move_up * 10000
        else:
            direction = 'DOWN'
            peak_pips = move_down * 10000
        
        # Classifier mouvement
        movement_class = classify_movement(peak_pips)
        
        return {
            'date': date_str,
            'peak_pips': peak_pips,
            'direction': direction,
            'movement_class': movement_class
        }
    
    except Exception as e:
        return None


def find_dates_with_strong_movements(
    min_impact_pips: float = 20.0,
    max_dates: int = 100,
    exclude_training_dates: bool = True
) -> List[Dict]:
    """
    Trouve les dates avec mouvements significatifs (>= min_impact_pips)
    
    Args:
        min_impact_pips: Impact minimum en pips (défaut: 20.0 = MOYEN)
        max_dates: Nombre maximum de dates à retourner
        exclude_training_dates: Exclure les dates d'entraînement
    
    Returns:
        Liste de dicts avec date, impact, direction, movement_class
    """
    if not DB_PATH.exists():
        print(f"❌ Base de données introuvable : {DB_PATH}")
        return []
    
    # Charger dates d'entraînement si nécessaire
    training_dates = set()
    if exclude_training_dates:
        try:
            training_file = Path(__file__).parent.parent.parent / 'SESSION_VALIDATION_ACTUELLE' / 'data' / 'predictable_movements_database.csv'
            if training_file.exists():
                df_training = pd.read_csv(training_file)
                if 'date' in df_training.columns:
                    training_dates = set(df_training['date'].astype(str).str.split().str[0].tolist())
        except:
            pass
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    try:
        # Trouver toutes les dates avec événements HIGH US
        query = """
        SELECT DISTINCT 
            DATE(e.ts_utc) as date,
            MIN(e.ts_utc) as first_event_time
        FROM events e
        LEFT JOIN event_families ef 
            ON e.event_key = ef.event_key 
            AND e.country = ef.country
        WHERE e.country = 'US'
            AND ef.empirical_score IS NOT NULL
            AND ef.empirical_score > 40
        GROUP BY DATE(e.ts_utc)
        ORDER BY date DESC
        LIMIT 500
        """
        
        df_dates = conn.execute(query).df()
        
        print(f"📊 {len(df_dates)} dates avec événements HIGH US trouvées")
        print("🔍 Scan des mouvements en cours...")
        print()
        
        results = []
        
        for idx, row in df_dates.iterrows():
            date_str = str(row['date']).split()[0]  # Prendre juste la date
            
            # Exclure dates d'entraînement
            if date_str in training_dates:
                continue
            
            # Convertir event_time
            event_time_str = row['first_event_time']
            if isinstance(event_time_str, str):
                event_time = pd.to_datetime(event_time_str)
            else:
                event_time = event_time_str
            
            if isinstance(event_time, pd.Timestamp):
                event_time = event_time.to_pydatetime()
            
            # Détecter mouvement
            movement = detect_movement_for_date(date_str, event_time)
            
            if movement and movement['peak_pips'] >= min_impact_pips:
                results.append(movement)
                
                if len(results) % 10 == 0:
                    print(f"  ✅ {len(results)} dates trouvées... ({date_str}: {movement['peak_pips']:.1f} pips - {movement['movement_class']})")
            
            if len(results) >= max_dates:
                break
        
        conn.close()
        
        return results
    
    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
        conn.close()
        return []


def main():
    print("=" * 80)
    print("RECHERCHE DATES AVEC MOUVEMENTS SIGNIFICATIFS")
    print("=" * 80)
    print()
    print("🎯 Focus : MOYEN (>= 20 pips), FORT (>= 50 pips), TRÈS_FORT (>= 100 pips)")
    print()
    
    # Trouver dates avec mouvements >= 20 pips
    results = find_dates_with_strong_movements(
        min_impact_pips=20.0,
        max_dates=50,
        exclude_training_dates=True
    )
    
    if not results:
        print("❌ Aucune date avec mouvement significatif trouvée")
        return
    
    print()
    print("=" * 80)
    print(f"✅ {len(results)} dates trouvées avec mouvements >= 20 pips")
    print("=" * 80)
    print()
    
    # Trier par impact (décroissant)
    results.sort(key=lambda x: x['peak_pips'], reverse=True)
    
    # Classifier par type
    by_class = {
        'MOYEN': [],
        'FORT': [],
        'TRÈS_FORT': []
    }
    
    for r in results:
        class_type = r['movement_class']
        if class_type in by_class:
            by_class[class_type].append(r)
    
    # Afficher statistiques
    print("📊 Répartition par classe :")
    print(f"   MOYEN (20-50 pips)    : {len(by_class['MOYEN']):>3} dates")
    print(f"   FORT (50-100 pips)    : {len(by_class['FORT']):>3} dates")
    print(f"   TRÈS_FORT (>= 100)   : {len(by_class['TRÈS_FORT']):>3} dates")
    print()
    
    # Top 20
    print("📈 Top 20 mouvements les plus forts :")
    print("-" * 80)
    print(f"{'Date':<12} {'Impact':>8} {'Direction':<8} {'Classe':<12}")
    print("-" * 80)
    
    for r in results[:20]:
        print(f"{r['date']:<12} {r['peak_pips']:>7.1f}  {r['direction']:<8} {r['movement_class']:<12}")
    
    print()
    
    # Sauvegarder dans CSV
    output_dir = Path(__file__).parent.parent / 'outputs'
    output_dir.mkdir(exist_ok=True)
    
    df_results = pd.DataFrame(results)
    output_file = output_dir / 'dates_with_strong_movements.csv'
    df_results.to_csv(output_file, index=False)
    
    print(f"💾 Résultats sauvegardés dans : {output_file}")
    print()
    
    # Extraire juste les dates pour utilisation
    dates_list = [r['date'] for r in results]
    dates_file = output_dir / 'dates_strong_movements_list.txt'
    with open(dates_file, 'w') as f:
        f.write('\n'.join(dates_list))
    
    print(f"📝 Liste des dates sauvegardée dans : {dates_file}")
    print()
    print("=" * 80)
    print("✅ RECHERCHE TERMINÉE")
    print("=" * 80)


if __name__ == "__main__":
    main()


