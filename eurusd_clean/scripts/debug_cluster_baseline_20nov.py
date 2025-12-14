"""
Debug : Vérifier pourquoi le cluster est à 13:30 et la baseline à 14:00
==========================================================================
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'streamlit_app' / 'pages'))

from Planificateur_V3_CLEAN import (
    load_events_for_date,
    build_clusters_for_date,
    scan_price_movements,
    detect_pattern_type
)

DB_PATH = PROJECT_ROOT / 'data' / 'warehouse.duckdb'
target_date = datetime(2025, 11, 20)

print("=" * 80)
print("🔍 DEBUG : CLUSTER ET BASELINE - 20.11.2025")
print("=" * 80)
print()

# 1. Charger les événements
print("1️⃣ CHARGEMENT DES ÉVÉNEMENTS")
print("-" * 80)

df_events = load_events_for_date(
    target_date,
    DB_PATH,
    timezone_str='Europe/Zurich',
    min_importance=1,
    countries=['US', 'DE'],
    exclude_no_actual=False
)

print(f"   ✅ {len(df_events)} événements chargés")
if not df_events.empty:
    print("   Premiers événements :")
    for idx, row in df_events.head(5).iterrows():
        ts_bern = row['ts_bern']
        if isinstance(ts_bern, pd.Timestamp):
            ts_str = ts_bern.strftime('%H:%M')
        else:
            ts_str = str(ts_bern)
        print(f"      {ts_str} | {row['country']:2s} | {row['event_key']}")

print()

# 2. Construire les clusters
print("2️⃣ CONSTRUCTION DES CLUSTERS")
print("-" * 80)

clusters = build_clusters_for_date(
    target_date,
    DB_PATH,
    timezone_str='Europe/Zurich',
    window_minutes=30,
    min_importance=1,
    countries=['US', 'DE'],
    exclude_no_actual=False
)

print(f"   ✅ {len(clusters)} cluster(s) trouvé(s)")
print()

if clusters:
    # Calculer scores
    for cluster in clusters:
        df_cluster_events = cluster.get('df_events', pd.DataFrame())
        if not df_cluster_events.empty:
            cluster['total_score'] = df_cluster_events['empirical_score'].sum()
            cluster['n_us_events'] = len(df_cluster_events[df_cluster_events['country'] == 'US'])
        else:
            cluster['total_score'] = 0.0
            cluster['n_us_events'] = 0
    
    # Sélectionner le cluster principal
    clusters_with_us = [c for c in clusters if c.get('n_us_events', 0) > 0]
    if clusters_with_us:
        cluster_principal = max(clusters_with_us, key=lambda x: (x.get('n_us_events', 0), x.get('total_score', 0.0)))
    else:
        cluster_principal = max(clusters, key=lambda x: x.get('total_score', 0.0))
    
    anchor_time = cluster_principal.get('anchor_time')
    if isinstance(anchor_time, pd.Timestamp):
        if anchor_time.tz is None:
            anchor_time = anchor_time.tz_localize('Europe/Zurich')
        else:
            anchor_time = anchor_time.tz_convert('Europe/Zurich')
        anchor_str = anchor_time.strftime('%H:%M')
    else:
        anchor_str = str(anchor_time)
    
    print(f"   ✅ Cluster principal :")
    print(f"      Heure d'ancrage : {anchor_str}")
    print(f"      Nombre d'événements : {cluster_principal.get('n_events', 0)}")
    print(f"      Événements US : {cluster_principal.get('n_us_events', 0)}")
    print(f"      Score total : {cluster_principal.get('total_score', 0.0):.1f}")
    print()
    
    # Vérifier si c'est à 13:30 ou 14:30
    if anchor_str == '13:30':
        print("   ⚠️ PROBLÈME : Le cluster est à 13:30 au lieu de 14:30")
        print("      → Vérifier la conversion de timezone dans build_clusters_for_date")
    elif anchor_str == '14:30':
        print("   ✅ CORRECT : Le cluster est à 14:30")
    else:
        print(f"   ⚠️ Heure inattendue : {anchor_str}")

print()

# 3. Scanner les mouvements de prix
print("3️⃣ SCAN DES MOUVEMENTS DE PRIX")
print("-" * 80)

from Planificateur_V3_CLEAN import load_prices_for_date

df_prices = load_prices_for_date(target_date, DB_PATH, 'Europe/Zurich')

if df_prices.empty:
    print("   ❌ Aucun prix chargé")
else:
    print(f"   ✅ {len(df_prices)} bougies de prix chargées")
    
    # Scanner les mouvements
    movements = scan_price_movements(df_prices, min_pips=35.0)
    
    print(f"   ✅ {len(movements)} mouvement(s) détecté(s)")
    print()
    
    if movements:
        print("   Mouvements détectés :")
        for i, mov in enumerate(movements, 1):
            start_ts = pd.Timestamp(mov['start_time'])
            peak_ts = pd.Timestamp(mov['peak_time'])
            if start_ts.tz is None:
                start_ts = start_ts.tz_localize('Europe/Zurich')
            else:
                start_ts = start_ts.tz_convert('Europe/Zurich')
            if peak_ts.tz is None:
                peak_ts = peak_ts.tz_localize('Europe/Zurich')
            else:
                peak_ts = peak_ts.tz_convert('Europe/Zurich')
            
            is_explosive = mov.get('is_explosive', False)
            explosive_mark = "💥 EXPLOSIF" if is_explosive else "📈 Normal"
            
            print(f"      {i}. {explosive_mark}")
            print(f"         Début: {start_ts.strftime('%H:%M')} | Pic: {peak_ts.strftime('%H:%M')}")
            print(f"         Impact: {mov['impact_pips']:.1f} pips | Direction: {mov['direction']}")
            
            # Vérifier si le mouvement à 14:29 est dans la liste
            if start_ts.hour == 14 and start_ts.minute >= 28 and start_ts.minute <= 30:
                print(f"         ✅ MOUVEMENT À 14:29-14:30 TROUVÉ !")
            elif start_ts.hour == 14 and start_ts.minute == 0:
                print(f"         ⚠️ Mouvement à 14:00 (peut-être pas le bon)")

print()

# 4. Détecter le pattern
print("4️⃣ DÉTECTION DU PATTERN")
print("-" * 80)

if not df_prices.empty and not df_events.empty:
    # Utiliser les événements du cluster principal
    df_events_cluster = cluster_principal.get('df_events', pd.DataFrame()).copy()
    
    if not df_events_cluster.empty:
        # Enrichir les événements
        from Planificateur_V3_CLEAN import enrich_events_with_surprises
        df_events_enriched = enrich_events_with_surprises(df_events_cluster)
        
        # Détecter le pattern
        pattern_result = detect_pattern_type(
            df_prices,
            df_events_enriched,
            min_pips=35.0,
            timezone='Europe/Zurich',
            cluster_anchor_time=anchor_time
        )
        
        print(f"   ✅ Pattern détecté : {pattern_result.get('pattern_type', 'INCONNU')}")
        print(f"      Confiance : {pattern_result.get('detection_confidence', 0.0)*100:.1f}%")
        
        movement = pattern_result.get('movement')
        if movement:
            start_time = movement.get('start_time')
            if start_time:
                if isinstance(start_time, pd.Timestamp):
                    if start_time.tz is None:
                        start_time = start_time.tz_localize('Europe/Zurich')
                    else:
                        start_time = start_time.tz_convert('Europe/Zurich')
                    start_str = start_time.strftime('%H:%M')
                else:
                    start_str = str(start_time)
                
                print(f"      Début du mouvement : {start_str}")
                print(f"      Impact : {movement.get('impact_pips', 0):.1f} pips")
                
                if start_str == '14:00':
                    print(f"      ⚠️ PROBLÈME : Le mouvement commence à 14:00 au lieu de 14:29/14:30")
                elif start_str in ['14:29', '14:30']:
                    print(f"      ✅ CORRECT : Le mouvement commence à {start_str}")
        else:
            print(f"      ⚠️ Aucun mouvement détecté dans le pattern_result")

print()
print("=" * 80)
print("✅ DEBUG TERMINÉ")
print("=" * 80)


