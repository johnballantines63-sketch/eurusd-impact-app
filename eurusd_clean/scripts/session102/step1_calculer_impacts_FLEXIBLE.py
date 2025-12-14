#!/usr/bin/env python3
"""
STEP1 FLEXIBLE - AVEC FILTRE CONFIGURABLE
==========================================

FILTRE ÉVÉNEMENTS : Deux modes disponibles

MODE 1 - HYBRIDE (OR) [RECOMMANDÉ] :
  (importance_n = 1) OR (empirical_score > 40)
  → Inclut HIGH + score fort
  → 11.09: 9 événements (CPI + jobless)

MODE 2 - STRICT (AND) :
  (importance_n = 1) AND (empirical_score > 40)
  → Seulement HIGH avec score fort
  → 11.09: 8 événements (CPI uniquement)

Configurable via variable FILTER_MODE
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd

# Chemins
project_root = Path(__file__).resolve().parents[2]
fx_impact_app = project_root.parent / "fx_impact_app"
sys.path.insert(0, str(fx_impact_app / "src"))

from config import get_db_path
from formulas_validated import (
    calculate_impact_d,
    calculate_adjusted_empirical_score
)

# ============================================================================
# CONFIGURATION FILTRE
# ============================================================================

# Choisir le mode :
# "OR"        : (importance=1 OR score>40) - Hybride basique
# "OR_JOBLESS": (importance=1 OR score>40 OR jobless>25) - Inclut TOUS jobless claims
# "AND"       : (importance=1 AND score>40) - Strict, seulement HIGH avec score fort
FILTER_MODE = "OR_JOBLESS"  # ← CHANGER ICI POUR TESTER

MIN_SCORE = 40
HIGH_IMPORTANCE = 1
JOBLESS_THRESHOLD = 25  # Seuil Jobless Claims basé sur score minimum réel (25.3)

print("=" * 80)
print("STEP1 FLEXIBLE - CALCUL IMPACTS")
print("=" * 80)
print()
print(f"🔧 MODE FILTRE : {FILTER_MODE}")
print(f"   Condition  : ", end="")
if FILTER_MODE == "OR":
    print(f"(importance_n = {HIGH_IMPORTANCE}) OR (empirical_score > {MIN_SCORE})")
    print(f"   → Inclut HIGH + événements score fort")
elif FILTER_MODE == "OR_JOBLESS":
    print(f"(importance_n = {HIGH_IMPORTANCE}) OR (score > {MIN_SCORE}) OR (Jobless > {JOBLESS_THRESHOLD})")
    print(f"   → Inclut HIGH + score fort + TOUS Jobless Claims")
else:
    print(f"(importance_n = {HIGH_IMPORTANCE}) AND (empirical_score > {MIN_SCORE})")
    print(f"   → Seulement HIGH avec score fort")
print()

# ============================================================================
# CHARGER DATES
# ============================================================================

data_dir = Path(__file__).parent / "data"
clusters_path = data_dir / "step0_clusters_HOURLY.csv"

if not clusters_path.exists():
    print(f"❌ Fichier manquant : {clusters_path.name}")
    print(f"   → Exécuter d'abord : python3 step0_extract_clusters_HOURLY.py")
    sys.exit(1)

df_clusters = pd.read_csv(clusters_path)
df_clusters['event_date'] = pd.to_datetime(df_clusters['event_date'])
df_clusters['event_hour'] = pd.to_datetime(df_clusters['event_hour'])

print(f"✅ {len(df_clusters)} clusters à traiter")
print()

# Connexion DB
db_path = get_db_path()
conn = duckdb.connect(str(db_path), read_only=True)

# ============================================================================
# FONCTION DÉDUPLICATION
# ============================================================================

def deduplicate_events(df_events):
    """Déduplique par (family, actual, estimate, ts_utc)"""
    if len(df_events) == 0:
        return df_events
    
    df_events['dedup_key'] = (
        df_events['family'].astype(str) + '_' +
        df_events['actual'].astype(str) + '_' +
        df_events['estimate'].astype(str) + '_' +
        df_events['ts_utc'].astype(str)
    )
    
    unique_events = []
    
    for key, group in df_events.groupby('dedup_key'):
        if len(group) == 1:
            unique_events.append(group.iloc[0])
        else:
            with_title = group[group['event_title'].notna()]
            if len(with_title) > 0:
                unique_events.append(with_title.iloc[0])
            else:
                unique_events.append(group.iloc[0])
    
    df_deduplicated = pd.DataFrame(unique_events)
    df_deduplicated = df_deduplicated.drop(columns=['dedup_key'])
    
    return df_deduplicated

# ============================================================================
# CALCULER IMPACTS
# ============================================================================

results = []

for idx, cluster in df_clusters.iterrows():
    event_date = cluster['event_date']
    event_hour = cluster['event_hour']
    
    # Construire requête selon mode
    if FILTER_MODE == "OR":
        filter_clause = f"""
        AND (
            e.importance_n = {HIGH_IMPORTANCE}
            OR ef.empirical_score > {MIN_SCORE}
        )
        """
    elif FILTER_MODE == "OR_JOBLESS":
        filter_clause = f"""
        AND (
            e.importance_n = {HIGH_IMPORTANCE}
            OR ef.empirical_score > {MIN_SCORE}
            OR (ef.family = 'Jobless Claims' AND ef.empirical_score > {JOBLESS_THRESHOLD})
        )
        """
    else:  # AND
        filter_clause = f"""
        AND e.importance_n = {HIGH_IMPORTANCE}
        AND ef.empirical_score > {MIN_SCORE}
        """
    
    query_events = f"""
    SELECT 
        e.event_key,
        e.event_title,
        e.actual,
        e.estimate,
        e.ts_utc,
        e.importance_n,
        ef.empirical_score,
        ef.family
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE DATE(e.ts_utc) = ?
        AND DATE_TRUNC('hour', e.ts_utc) = ?
        AND e.country = 'US'
        {filter_clause}
    ORDER BY e.ts_utc
    """
    
    df_events = conn.execute(query_events, [
        event_date.strftime('%Y-%m-%d'),
        event_hour
    ]).fetchdf()
    
    if len(df_events) == 0:
        continue
    
    num_events_raw = len(df_events)
    
    # DÉDUPLICATION
    df_events = deduplicate_events(df_events)
    num_events_dedup = len(df_events)
    num_duplicates = num_events_raw - num_events_dedup
    
    # Calculer score base
    base_score = df_events['empirical_score'].mean()
    
    # Calculer surprise max
    max_surprise = 0
    for _, event in df_events.iterrows():
        if pd.notna(event['actual']) and pd.notna(event['estimate']) and event['estimate'] != 0:
            surprise_pct = abs((event['actual'] - event['estimate']) / event['estimate']) * 100
            if surprise_pct > max_surprise:
                max_surprise = surprise_pct
    
    # Ajuster score
    adjusted_score = calculate_adjusted_empirical_score(base_score, max_surprise)
    
    # Calculer impact (amp=2.5)
    impact_predit = calculate_impact_d(
        empirical_score=adjusted_score,
        num_events=num_events_dedup,
        amplification=2.5
    )
    
    results.append({
        'event_date': event_date.strftime('%Y-%m-%d'),
        'event_hour': event_hour.strftime('%H:%M'),
        'num_events_raw': num_events_raw,
        'num_events_dedup': num_events_dedup,
        'num_duplicates': num_duplicates,
        'base_score': base_score,
        'max_surprise': max_surprise,
        'adjusted_score': adjusted_score,
        'impact_predit': impact_predit,
        'filter_mode': FILTER_MODE
    })
    
    status = "⚠️" if num_duplicates > 0 else "✅"
    print(f"{status} {event_date.strftime('%Y-%m-%d')} {event_hour.strftime('%H:%M')} : "
          f"{num_events_raw}→{num_events_dedup} events, "
          f"score={base_score:.1f}, surp={max_surprise:.1f}%, "
          f"impact={impact_predit:.1f} pips")

conn.close()

# ============================================================================
# SAUVEGARDER
# ============================================================================

df_results = pd.DataFrame(results)
output_filename = f"step1_impacts_{FILTER_MODE}.csv"
output_path = data_dir / output_filename
df_results.to_csv(output_path, index=False)

print()
print("=" * 80)
print(f"✅ TERMINÉ : {len(results)} clusters traités")
print(f"✅ Sauvegardé : {output_filename}")
print("=" * 80)
print()

# ============================================================================
# STATISTIQUES
# ============================================================================

print("📊 STATISTIQUES :")
print(f"   Impact moyen : {df_results['impact_predit'].mean():.1f} pips")
print(f"   Impact min   : {df_results['impact_predit'].min():.1f} pips")
print(f"   Impact max   : {df_results['impact_predit'].max():.1f} pips")
print()

total_dups = df_results['num_duplicates'].sum()
dates_with_dups = (df_results['num_duplicates'] > 0).sum()

print("🔍 DÉDUPLICATION :")
print(f"   Doublons supprimés : {total_dups}")
print(f"   Clusters avec dups : {dates_with_dups}/{len(df_results)}")
print()

print("➡️  PROCHAINE ÉTAPE :")
print(f"   python3 step2_mesurer_reels_FLEXIBLE.py")
print(f"   (Utiliser {output_filename})")
