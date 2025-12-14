"""
Détail Complet du Noyau Dur pour 2025-09-11

Objectif : Montrer exactement quels événements composent le noyau dur CPI
pour cette date, avec leurs caractéristiques (estimate, actual, surprise, etc.)

Date : 2025-12-06
"""

import sys
from pathlib import Path
import pandas as pd
import duckdb
from datetime import datetime
import pytz
import re

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from config import DB_PATH
from scripts.run_pipeline_complete import PipelineExecutor

TZ_BERN = pytz.timezone('Europe/Zurich')

# Patterns pour exclure événements sans estimate
EVENTS_WITHOUT_ESTIMATE_PATTERNS = [
    r'(?i)(speech|discours|statement|remarks|testimony|testifies)',
    r'(?i)(fed.*speech|ecb.*speech|boe.*speech)',
    r'(?i)(press conference|conference de presse)',
    r'(?i)(meeting minutes|compte-rendu)',
    r'(?i)(beige book|livre beige)',
]

def is_event_without_estimate(event: pd.Series) -> bool:
    """Vérifie si un événement ne peut pas avoir de surprise calculée"""
    event_key = str(event.get('event_key', '') or '')
    event_title = str(event.get('event_title', '') or '')
    estimate = event.get('estimate')
    forecast = event.get('forecast')
    previous = event.get('previous')
    
    has_valid_estimate = (
        (estimate is not None and not pd.isna(estimate) and estimate != 'nan') or
        (forecast is not None and not pd.isna(forecast) and forecast != 'nan') or
        (previous is not None and not pd.isna(previous) and previous != 'nan')
    )
    
    if not has_valid_estimate:
        return True
    
    text_to_check = f"{event_key} {event_title}".lower()
    for pattern in EVENTS_WITHOUT_ESTIMATE_PATTERNS:
        if re.search(pattern, text_to_check):
            return True
    
    return False

def detail_noyau_dur_2025_09_11():
    """Affiche le détail complet du noyau dur pour 2025-09-11"""
    
    print("="*100)
    print("DÉTAIL NOYAU DUR - 2025-09-11")
    print("="*100)
    print()
    
    date_str = '2025-09-11'
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    executor = PipelineExecutor(db_path=str(DB_PATH), verbose=False)
    
    # 1. Détecter mouvement fort
    print("ÉTAPE 1 : DÉTECTION MOUVEMENT FORT")
    print("-"*100)
    print()
    
    date_dt = pd.to_datetime(date_str)
    window_start = TZ_BERN.localize(datetime.combine(date_dt.date(), datetime.min.time().replace(hour=14, minute=0)))
    window_end = TZ_BERN.localize(datetime.combine(date_dt.date(), datetime.min.time().replace(hour=20, minute=0)))
    
    query_prices = f"""
    SELECT datetime, open, high, low, close
    FROM prices_finnhub_m1
    WHERE DATE(datetime) = '{date_str}'
      AND datetime >= '{window_start.strftime('%Y-%m-%d %H:%M:%S')}'
      AND datetime <= '{window_end.strftime('%Y-%m-%d %H:%M:%S')}'
    ORDER BY datetime ASC
    """
    
    df_prices = conn.execute(query_prices).df()
    
    if not df_prices.empty:
        df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
        df_prices = df_prices.set_index('datetime')
        
        baseline_time = TZ_BERN.localize(datetime.combine(date_dt.date(), datetime.min.time().replace(hour=14, minute=30)))
        prices_at_baseline = df_prices[df_prices.index >= baseline_time]
        
        if not prices_at_baseline.empty:
            baseline_price = prices_at_baseline.iloc[0]['open']
            
            # Détecter pic
            max_high = prices_at_baseline['high'].max()
            min_low = prices_at_baseline['low'].min()
            impact_up = (max_high - baseline_price) * 10000
            impact_down = (baseline_price - min_low) * 10000
            impact = max(impact_up, impact_down)
            
            print(f"✅ Mouvement fort détecté : {impact:.2f} pips")
            print(f"   Baseline (14:30 OPEN) : {baseline_price:.5f}")
            print(f"   Pic : {max_high:.5f} (UP) / {min_low:.5f} (DOWN)")
            print()
    
    # 2. Trouver événements correspondants
    print("ÉTAPE 2 : ÉVÉNEMENTS CORRESPONDANTS")
    print("-"*100)
    print()
    
    # Utiliser le pipeline pour obtenir les événements
    result = executor.execute_complete_pipeline(
        date_str,
        window_minutes=30,
        support_threshold=0.8,
        jaccard_threshold=0.6,
        years_lookback=5
    )
    
    if not result or not result.get('success'):
        print("❌ Pipeline échoué")
        conn.close()
        return
    
    # Extraire cluster principal
    results_dict = result.get('results', {})
    etape2_clusters = results_dict.get('etape2_clusters', [])
    
    # Le cluster principal est celui utilisé dans etape3
    etape3_cluster_info = results_dict.get('etape3_cluster_info', {})
    main_cluster = etape3_cluster_info.get('cluster', {})
    
    if not main_cluster or main_cluster.get('events') is None:
        # Fallback : prendre le plus grand cluster
        if etape2_clusters:
            main_cluster = max(etape2_clusters, key=lambda c: c.get('n_events', 0))
        else:
            print("❌ Aucun cluster trouvé")
            conn.close()
            return
    
    cluster_events = main_cluster.get('events', pd.DataFrame())
    if cluster_events.empty:
        print("❌ Cluster vide")
        conn.close()
        return
    
    anchor_time = main_cluster.get('anchor_time')
    
    print(f"✅ Cluster principal trouvé : {len(cluster_events)} événements")
    print(f"   Anchor time : {anchor_time.strftime('%H:%M') if hasattr(anchor_time, 'strftime') else anchor_time}")
    print()
    
    # 3. Afficher tous les événements du cluster
    print("ÉTAPE 3 : TOUS LES ÉVÉNEMENTS DU CLUSTER")
    print("-"*100)
    print()
    
    print(f"{'Heure':<8} {'Event Key':<40} {'Country':<8} {'Imp':<4} {'Estimate':<12} {'Actual':<12} {'Surprise':<10} {'Score':<8} {'Inclu':<6}")
    print("-"*100)
    
    events_included = []
    events_excluded = []
    
    for _, event in cluster_events.iterrows():
        event_time = pd.to_datetime(event['ts_utc']).strftime('%H:%M')
        event_key = str(event.get('event_key', 'Unknown'))[:40]
        country = event.get('country', 'N/A')
        importance = event.get('importance_n', 'N/A')
        estimate = event.get('estimate') or event.get('forecast') or event.get('previous')
        actual = event.get('actual')
        empirical_score = event.get('empirical_score', 0.0)
        
        # Calculer surprise
        surprise_str = 'N/A'
        if actual is not None and estimate is not None and estimate != 0:
            surprise = (actual - estimate) / abs(estimate) * 100
            surprise_str = f"{surprise:+.1f}%"
        elif actual is not None and estimate is not None:
            surprise = actual - estimate
            surprise_str = f"{surprise:+.2f}"
        
        # Vérifier si inclus (avec estimate)
        is_included = not is_event_without_estimate(event)
        included_str = "✅ OUI" if is_included else "❌ NON"
        
        estimate_str = f"{estimate:.2f}" if estimate is not None and not pd.isna(estimate) else "NaN"
        actual_str = f"{actual:.2f}" if actual is not None and not pd.isna(actual) else "NaN"
        score_str = f"{empirical_score:.1f}" if empirical_score > 0 else "N/A"
        
        print(f"{event_time:<8} {event_key:<40} {country:<8} {importance:<4} {estimate_str:<12} {actual_str:<12} {surprise_str:<10} {score_str:<8} {included_str:<6}")
        
        if is_included:
            events_included.append(event)
        else:
            events_excluded.append(event)
    
    print()
    print(f"✅ Événements inclus (avec estimate) : {len(events_included)}")
    print(f"❌ Événements exclus (sans estimate) : {len(events_excluded)}")
    print()
    
    # 4. Identifier noyau dur
    print("ÉTAPE 4 : IDENTIFICATION NOYAU DUR")
    print("-"*100)
    print()
    
    etape3 = results_dict.get('etape3_noyau_dur', {})
    core_type = etape3.get('core_type', 'UNKNOWN')
    core_events_list = etape3.get('core_events', [])
    
    print(f"Core Type détecté : {core_type}")
    print(f"Événements core : {len(core_events_list)}")
    print()
    
    # Afficher événements core
    print("ÉVÉNEMENTS COMPOSANT LE NOYAU DUR :")
    print("-"*100)
    print()
    
    if core_type == 'CPI':
        CPI_PATTERN = r'(?i)(cpi|consumer price|inflation rate|core inflation|harmonised inflation)'
        
        print(f"{'Heure':<8} {'Event Key':<50} {'Country':<8} {'Imp':<4} {'Estimate':<12} {'Actual':<12} {'Surprise':<10} {'Score':<8}")
        print("-"*100)
        
        core_events_displayed = []
        for _, event in cluster_events.iterrows():
            event_key = str(event.get('event_key', '') or '')
            event_key_norm = event_key.lower().strip()
            
            if re.search(CPI_PATTERN, event_key_norm):
                event_time = pd.to_datetime(event['ts_utc']).strftime('%H:%M')
                country = event.get('country', 'N/A')
                importance = event.get('importance_n', 'N/A')
                estimate = event.get('estimate') or event.get('forecast') or event.get('previous')
                actual = event.get('actual')
                empirical_score = event.get('empirical_score', 0.0)
                
                surprise_str = 'N/A'
                if actual is not None and estimate is not None and estimate != 0:
                    surprise = (actual - estimate) / abs(estimate) * 100
                    surprise_str = f"{surprise:+.1f}%"
                
                estimate_str = f"{estimate:.2f}" if estimate is not None and not pd.isna(estimate) else "NaN"
                actual_str = f"{actual:.2f}" if actual is not None and not pd.isna(actual) else "NaN"
                score_str = f"{empirical_score:.1f}" if empirical_score > 0 else "N/A"
                
                print(f"{event_time:<8} {event_key[:50]:<50} {country:<8} {importance:<4} {estimate_str:<12} {actual_str:<12} {surprise_str:<10} {score_str:<8}")
                core_events_displayed.append(event)
        
        print()
        print(f"✅ {len(core_events_displayed)} événements CPI composent le noyau dur")
    
    # 5. Détail des événements exclus
    if events_excluded:
        print()
        print("ÉTAPE 5 : ÉVÉNEMENTS EXCLUS (SANS ESTIMATE)")
        print("-"*100)
        print()
        
        print(f"{'Heure':<8} {'Event Key':<50} {'Raison Exclusion':<30}")
        print("-"*100)
        
        for _, event in events_excluded:
            event_time = pd.to_datetime(event['ts_utc']).strftime('%H:%M')
            event_key = str(event.get('event_key', 'Unknown'))
            
            estimate = event.get('estimate')
            forecast = event.get('forecast')
            previous = event.get('previous')
            has_estimate = (
                (estimate is not None and not pd.isna(estimate) and estimate != 'nan') or
                (forecast is not None and not pd.isna(forecast) and forecast != 'nan') or
                (previous is not None and not pd.isna(previous) and previous != 'nan')
            )
            
            if not has_estimate:
                raison = "Pas d'estimate/forecast/previous"
            else:
                event_title = str(event.get('event_title', '') or '')
                text = f"{event_key} {event_title}".lower()
                if any(re.search(p, text) for p in EVENTS_WITHOUT_ESTIMATE_PATTERNS):
                    raison = "Pattern discours/statement"
                else:
                    raison = "Autre raison"
            
            print(f"{event_time:<8} {event_key[:50]:<50} {raison:<30}")
    
    # 6. Résumé final
    print()
    print("="*100)
    print("RÉSUMÉ FINAL")
    print("="*100)
    print()
    
    print(f"Date : {date_str}")
    print(f"Core Type : {core_type}")
    print(f"Événements totaux dans cluster : {len(cluster_events)}")
    print(f"Événements inclus (avec estimate) : {len(events_included)}")
    print(f"Événements exclus (sans estimate) : {len(events_excluded)}")
    print(f"Événements composant le noyau dur : {len(core_events_list)}")
    print()
    
    if core_type == 'CPI':
        cpi_events = [e for e in cluster_events.iterrows() if re.search(r'(?i)(cpi|consumer price|inflation)', str(e[1].get('event_key', '')).lower())]
        print(f"✅ Le noyau dur CPI est composé de {len(cpi_events)} événements CPI")
        print(f"   Ces événements sont utilisés pour identifier le cluster comme CPI")
        print(f"   et pour rechercher des clusters identiques dans l'historique")
    
    conn.close()

if __name__ == '__main__':
    detail_noyau_dur_2025_09_11()

