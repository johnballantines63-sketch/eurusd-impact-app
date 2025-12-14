#!/usr/bin/env python3
"""
CALCUL DES IMPACTS RÉELS PAR ÉVÉNEMENT

Objectif : Calculer les impacts réels (MFE, MAE, TTR) pour chaque événement
           en analysant les prix minute par minute autour de chaque événement.

Au lieu de se baser sur avg_movement_pips (moyenne historique),
on calcule l'impact RÉEL de chaque occurrence individuelle.

Durée estimée : 30-60 minutes pour 32,024 événements
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

def calculate_event_impact(event_ts, prices_df, lookback_minutes=30, lookforward_minutes=60):
    """
    Calcule l'impact réel d'un événement en analysant les prix
    
    Args:
        event_ts: Timestamp de l'événement
        prices_df: DataFrame avec colonnes [datetime, close]
        lookback_minutes: Minutes avant l'événement (pour prix de référence)
        lookforward_minutes: Minutes après l'événement (pour MFE/MAE)
    
    Returns:
        dict avec mfe_pips, mae_pips, ttr_minutes, direction
    """
    try:
        # Prix de référence (5 min avant l'événement)
        ref_time = event_ts - timedelta(minutes=5)
        ref_prices = prices_df[
            (prices_df['datetime'] >= ref_time - timedelta(minutes=5)) &
            (prices_df['datetime'] <= ref_time)
        ]
        
        if len(ref_prices) == 0:
            return None
        
        reference_price = ref_prices['close'].iloc[-1]
        
        # Prix après l'événement
        after_prices = prices_df[
            (prices_df['datetime'] > event_ts) &
            (prices_df['datetime'] <= event_ts + timedelta(minutes=lookforward_minutes))
        ]
        
        if len(after_prices) == 0:
            return None
        
        # Calculer les mouvements en pips (1 pip = 0.0001 pour EUR/USD)
        price_changes = (after_prices['close'] - reference_price) / 0.0001
        
        # MFE (Maximum Favorable Excursion) - Plus grand mouvement dans la direction favorable
        max_up = price_changes.max()
        max_down = abs(price_changes.min())
        
        if max_up > max_down:
            mfe_pips = max_up
            direction = 'bullish'
            # Trouver quand le MFE a été atteint
            mfe_idx = price_changes.idxmax()
        else:
            mfe_pips = max_down
            direction = 'bearish'
            # Trouver quand le MFE a été atteint
            mfe_idx = price_changes.idxmin()
        
        # MAE (Maximum Adverse Excursion) - Plus grand mouvement dans la direction défavorable
        if direction == 'bullish':
            mae_pips = max_down
        else:
            mae_pips = max_up
        
        # TTR (Time To Return) - Temps pour revenir au prix de référence après le MFE
        mfe_time = after_prices.loc[mfe_idx, 'datetime']
        
        # Prix après le MFE
        prices_after_mfe = prices_df[
            (prices_df['datetime'] > mfe_time) &
            (prices_df['datetime'] <= event_ts + timedelta(minutes=lookforward_minutes))
        ]
        
        ttr_minutes = None
        if len(prices_after_mfe) > 0:
            # Chercher quand le prix revient proche du prix de référence (±3 pips)
            tolerance = 3  # pips
            returns = prices_after_mfe[
                abs((prices_after_mfe['close'] - reference_price) / 0.0001) <= tolerance
            ]
            
            if len(returns) > 0:
                return_time = returns['datetime'].iloc[0]
                ttr_minutes = (return_time - event_ts).total_seconds() / 60
        
        return {
            'mfe_pips': round(mfe_pips, 2),
            'mae_pips': round(mae_pips, 2),
            'ttr_minutes': round(ttr_minutes, 1) if ttr_minutes else None,
            'direction': direction,
            'reference_price': reference_price
        }
    
    except Exception as e:
        print(f"Erreur calcul impact: {e}")
        return None

def main():
    """Fonction principale"""
    
    print("=" * 80)
    print("📊 CALCUL DES IMPACTS RÉELS PAR ÉVÉNEMENT")
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
    
    # 2. Charger tous les prix (pour éviter de requêter à chaque fois)
    print("\n2️⃣ Chargement des prix minute par minute...")
    
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
    
    # Convertir en datetime si nécessaire
    if not pd.api.types.is_datetime64_any_dtype(prices_df['datetime']):
        prices_df['datetime'] = pd.to_datetime(prices_df['datetime'])
    
    if not pd.api.types.is_datetime64_any_dtype(events_df['ts_utc']):
        events_df['ts_utc'] = pd.to_datetime(events_df['ts_utc'])
    
    # 3. Calculer les impacts pour chaque événement
    print("\n3️⃣ Calcul des impacts (cela peut prendre 30-60 minutes)...")
    print("    Progression :")
    
    results = []
    
    if HAS_TQDM:
        iterator = tqdm(events_df.iterrows(), total=len(events_df), desc="   Calcul")
    else:
        iterator = events_df.iterrows()
    
    for idx, event in iterator:
        # Calculer l'impact
        impact = calculate_event_impact(
            event['ts_utc'],
            prices_df,
            lookback_minutes=30,
            lookforward_minutes=60  # Réduit de 120 à 60 minutes
        )
        
        if impact is not None:
            results.append({
                'ts_utc': event['ts_utc'],
                'event_key': event['event_key'],
                'event_title': event['event_title'],
                'country': event['country'],
                'family': event['family'],
                'empirical_score': event['empirical_score'],
                'impact_level': event['impact_level'],
                'actual': event['actual'],
                'forecast': event['forecast'],
                'previous': event['previous'],
                'mfe_pips': impact['mfe_pips'],
                'mae_pips': impact['mae_pips'],
                'ttr_minutes': impact['ttr_minutes'],
                'direction': impact['direction'],
                'reference_price': impact['reference_price']
            })
        
        # Checkpoint tous les 1000 événements
        if len(results) > 0 and len(results) % 1000 == 0:
            print(f"\n   📊 Checkpoint: {len(results)} impacts calculés...")
    
    print(f"\n   ✅ {len(results)} impacts calculés avec succès")
    print(f"   ⚠️ {len(events_df) - len(results)} événements sans données de prix")
    
    # 4. Créer la table des impacts calculés
    print("\n4️⃣ Création de la table event_impacts_calculated...")
    
    results_df = pd.DataFrame(results)
    
    # Supprimer la table si elle existe déjà
    conn.execute("DROP TABLE IF EXISTS event_impacts_calculated")
    
    # Créer la nouvelle table
    conn.execute("""
        CREATE TABLE event_impacts_calculated AS 
        SELECT * FROM results_df
    """)
    
    print(f"   ✅ Table créée avec {len(results_df)} lignes")
    
    # 5. Statistiques
    print("\n5️⃣ Statistiques des impacts calculés:")
    
    stats = results_df.groupby('impact_level').agg({
        'mfe_pips': ['count', 'mean', 'median', 'std', 'min', 'max'],
        'mae_pips': ['mean', 'median'],
        'ttr_minutes': ['mean', 'median']
    }).round(2)
    
    print(stats)
    
    # 6. Comparaison avec moyennes historiques
    print("\n6️⃣ Comparaison impacts calculés vs moyennes historiques:")
    
    comparison_query = """
    SELECT 
        ic.impact_level,
        COUNT(*) as n_events,
        AVG(ic.mfe_pips) as avg_mfe_calculated,
        AVG(ef.avg_movement_pips) as avg_mfe_historical,
        AVG(ic.mfe_pips) - AVG(ef.avg_movement_pips) as difference
    FROM event_impacts_calculated ic
    LEFT JOIN event_families ef 
        ON ic.event_key = ef.event_key 
        AND ic.country = ef.country
    GROUP BY ic.impact_level
    ORDER BY ic.impact_level
    """
    
    comparison = conn.execute(comparison_query).fetchdf()
    print(comparison.to_string(index=False))
    
    # 7. Exemples du 11 septembre 2025
    print("\n7️⃣ Exemples : 11 septembre 2025")
    
    sept_11_query = """
    SELECT 
        strftime(ts_utc, '%H:%M:%S') as time,
        event_title,
        empirical_score,
        mfe_pips,
        mae_pips,
        ttr_minutes,
        direction
    FROM event_impacts_calculated
    WHERE CAST(ts_utc AS DATE) = '2025-09-11'
    ORDER BY ts_utc
    LIMIT 10
    """
    
    sept_11_data = conn.execute(sept_11_query).fetchdf()
    
    if len(sept_11_data) > 0:
        print(sept_11_data.to_string(index=False))
    else:
        print("   ⚠️ Pas de données pour le 11 septembre 2025")
    
    # 8. Créer des index pour optimiser les requêtes futures
    print("\n8️⃣ Création des index...")
    
    try:
        conn.execute("CREATE INDEX idx_impacts_date ON event_impacts_calculated(ts_utc)")
        conn.execute("CREATE INDEX idx_impacts_key ON event_impacts_calculated(event_key)")
        conn.execute("CREATE INDEX idx_impacts_country ON event_impacts_calculated(country)")
        print("   ✅ Index créés")
    except Exception as e:
        print(f"   ⚠️ Erreur création index (peut-être déjà existants): {e}")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ CALCUL TERMINÉ")
    print("=" * 80)
    print(f"\n📊 Résumé:")
    print(f"   • Événements analysés : {len(events_df)}")
    print(f"   • Impacts calculés : {len(results_df)}")
    print(f"   • Taux de succès : {len(results_df)/len(events_df)*100:.1f}%")
    print(f"\n💾 Table créée : event_impacts_calculated")
    print(f"   Colonnes : ts_utc, event_key, country, mfe_pips, mae_pips, ttr_minutes, direction")
    print(f"\n🎯 Prochaine étape : Ré-entraîner la formule sur ces impacts réels")

if __name__ == '__main__':
    main()
