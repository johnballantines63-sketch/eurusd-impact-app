#!/usr/bin/env python3
"""
ÉTAPE 1 : CALCUL IMPACTS PRÉDITS
=================================

Pour chaque date :
1. Charger événements depuis DB (validation_events ou events)
2. Calculer adjusted_score avec calculate_adjusted_empirical_score()
3. Calculer impact_predit avec calculate_impact_d(amp=2.5)

SORTIE : step1_impacts_predits.csv
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
print("ÉTAPE 1 : CALCUL IMPACTS PRÉDITS")
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
# CALCULER IMPACTS POUR CHAQUE DATE
# ============================================================================

results = []

for idx, cluster in df_clusters.iterrows():
    event_date = cluster['event_date']
    
    # Charger événements US du jour avec score > 40
    query_events = """
    SELECT 
        e.event_key,
        e.event_title as label,
        e.actual,
        e.estimate,
        ef.empirical_score
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
    
    num_events = len(df_events)
    
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
        num_events=num_events,
        amplification=2.5  # BASELINE FIXE
    )
    
    results.append({
        'event_date': event_date.strftime('%Y-%m-%d'),
        'num_events': num_events,
        'base_score': base_score,
        'max_surprise': max_surprise,
        'adjusted_score': adjusted_score,
        'impact_predit': impact_predit
    })
    
    print(f"✅ {event_date.strftime('%Y-%m-%d')} : {num_events} events, "
          f"score={base_score:.1f}, surprise={max_surprise:.1f}%, "
          f"adjusted={adjusted_score:.1f}, impact={impact_predit:.1f} pips")

conn.close()

# ============================================================================
# SAUVEGARDER
# ============================================================================

df_results = pd.DataFrame(results)
output_path = data_dir / "step1_impacts_predits_NEW.csv"
df_results.to_csv(output_path, index=False)

print()
print("=" * 80)
print(f"✅ ÉTAPE 1 TERMINÉE : {len(results)} cas traités")
print(f"✅ Sauvegardé : {output_path.name}")
print("=" * 80)
print()
print("📊 STATISTIQUES :")
print(f"   Impact moyen : {df_results['impact_predit'].mean():.1f} pips")
print(f"   Impact min   : {df_results['impact_predit'].min():.1f} pips")
print(f"   Impact max   : {df_results['impact_predit'].max():.1f} pips")
print()
print("➡️  PROCHAINE ÉTAPE : python3 step2_mesurer_reels_NEW.py")
