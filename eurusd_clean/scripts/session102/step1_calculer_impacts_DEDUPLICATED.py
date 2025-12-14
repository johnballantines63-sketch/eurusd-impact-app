#!/usr/bin/env python3
"""
ÉTAPE 1 : CALCUL IMPACTS PRÉDITS - AVEC DÉDUPLICATION
======================================================

CORRECTION CRITIQUE : Dédupliquer les événements avant calcul !

Problème identifié : événements dupliqués dans DB avec différents event_key
- "core inflation rate" vs "core inflation rate_yoy"
- "cpi s a" vs "cpi s.a"
- etc.

Stratégie déduplication :
1. Grouper par (family, actual, estimate, ts_utc)
2. Garder UN SEUL événement par groupe
3. Privilégier celui avec event_title non NULL

SORTIE : step1_impacts_predits_DEDUPLICATED.csv
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

print("=" * 80)
print("ÉTAPE 1 : CALCUL IMPACTS PRÉDITS - AVEC DÉDUPLICATION")
print("=" * 80)
print()

# ============================================================================
# CHARGER DATES
# ============================================================================

data_dir = Path(__file__).parent / "data"
df_clusters = pd.read_csv(data_dir / "step0_selected_clusters.csv")
df_clusters['event_date'] = pd.to_datetime(df_clusters['event_date'])

print(f"✅ {len(df_clusters)} dates à traiter")
print()

# Connexion DB
db_path = get_db_path()
conn = duckdb.connect(str(db_path), read_only=True)

# ============================================================================
# FONCTION DÉDUPLICATION
# ============================================================================

def deduplicate_events(df_events):
    """
    Déduplique les événements selon (family, actual, estimate, ts_utc)
    
    Pour chaque groupe de doublons :
    - Privilégier événement avec event_title non NULL
    - Sinon prendre le premier
    """
    if len(df_events) == 0:
        return df_events
    
    # Créer clé de groupement
    df_events['dedup_key'] = (
        df_events['family'].astype(str) + '_' +
        df_events['actual'].astype(str) + '_' +
        df_events['estimate'].astype(str) + '_' +
        df_events['ts_utc'].astype(str)
    )
    
    # Grouper et garder meilleur de chaque groupe
    unique_events = []
    
    for key, group in df_events.groupby('dedup_key'):
        # Si un seul événement, le garder
        if len(group) == 1:
            unique_events.append(group.iloc[0])
        else:
            # Plusieurs événements : privilégier celui avec event_title
            with_title = group[group['event_title'].notna()]
            
            if len(with_title) > 0:
                # Prendre le premier avec titre
                unique_events.append(with_title.iloc[0])
            else:
                # Aucun titre : prendre le premier
                unique_events.append(group.iloc[0])
    
    df_deduplicated = pd.DataFrame(unique_events)
    df_deduplicated = df_deduplicated.drop(columns=['dedup_key'])
    
    return df_deduplicated

# ============================================================================
# CALCULER IMPACTS POUR CHAQUE DATE
# ============================================================================

results = []

for idx, cluster in df_clusters.iterrows():
    event_date = cluster['event_date']
    
    # Charger événements US du jour avec score > 40
    query_events = """
    SELECT 
        e.event_key,
        e.event_title,
        e.actual,
        e.estimate,
        e.ts_utc,
        ef.empirical_score,
        ef.family
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE DATE(e.ts_utc) = ?
        AND e.country = 'US'
        AND ef.empirical_score > 40
    ORDER BY e.ts_utc
    """
    
    df_events = conn.execute(query_events, [event_date.strftime('%Y-%m-%d')]).fetchdf()
    
    if len(df_events) == 0:
        print(f"⚠️  {event_date.strftime('%Y-%m-%d')} : Aucun événement trouvé")
        continue
    
    num_events_before = len(df_events)
    
    # DÉDUPLICATION
    df_events = deduplicate_events(df_events)
    
    num_events_after = len(df_events)
    num_duplicates = num_events_before - num_events_after
    
    # Calculer score base (moyenne)
    base_score = df_events['empirical_score'].mean()
    
    # Calculer surprise max
    max_surprise = 0
    surprises = []
    
    for _, event in df_events.iterrows():
        if pd.notna(event['actual']) and pd.notna(event['estimate']) and event['estimate'] != 0:
            surprise_pct = abs((event['actual'] - event['estimate']) / event['estimate']) * 100
            surprises.append(surprise_pct)
            if surprise_pct > max_surprise:
                max_surprise = surprise_pct
    
    # Ajuster score selon surprise
    adjusted_score = calculate_adjusted_empirical_score(base_score, max_surprise)
    
    # Calculer impact avec amp=2.5 (BASELINE)
    impact_predit = calculate_impact_d(
        empirical_score=adjusted_score,
        num_events=num_events_after,  # UTILISER NOMBRE DÉDUPLIQUÉ !
        amplification=2.5
    )
    
    results.append({
        'event_date': event_date.strftime('%Y-%m-%d'),
        'num_events_raw': num_events_before,
        'num_events_deduplicated': num_events_after,
        'num_duplicates': num_duplicates,
        'base_score': base_score,
        'max_surprise': max_surprise,
        'adjusted_score': adjusted_score,
        'impact_predit': impact_predit
    })
    
    status = "⚠️" if num_duplicates > 0 else "✅"
    print(f"{status} {event_date.strftime('%Y-%m-%d')} : "
          f"{num_events_before}→{num_events_after} events ({num_duplicates} doublons), "
          f"score={base_score:.1f}, surprise={max_surprise:.1f}%, "
          f"adjusted={adjusted_score:.1f}, impact={impact_predit:.1f} pips")

conn.close()

# ============================================================================
# SAUVEGARDER
# ============================================================================

df_results = pd.DataFrame(results)
output_path = data_dir / "step1_impacts_predits_DEDUPLICATED.csv"
df_results.to_csv(output_path, index=False)

print()
print("=" * 80)
print(f"✅ ÉTAPE 1 TERMINÉE : {len(results)} cas traités")
print(f"✅ Sauvegardé : {output_path.name}")
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

# Statistiques déduplication
total_duplicates = df_results['num_duplicates'].sum()
dates_with_dups = (df_results['num_duplicates'] > 0).sum()

print("🔍 DÉDUPLICATION :")
print(f"   Total doublons supprimés : {total_duplicates}")
print(f"   Dates avec doublons      : {dates_with_dups}/{len(df_results)}")
print()

if dates_with_dups > 0:
    print("⚠️  DATES AVEC DOUBLONS :")
    for _, row in df_results[df_results['num_duplicates'] > 0].iterrows():
        print(f"   - {row['event_date']} : {row['num_events_raw']}→{row['num_events_deduplicated']} "
              f"({row['num_duplicates']} doublons)")
    print()

print("➡️  PROCHAINE ÉTAPE : python3 step2_mesurer_reels_NEW.py")
print("   (Utiliser step1_impacts_predits_DEDUPLICATED.csv)")
