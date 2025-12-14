#!/usr/bin/env python3
"""
SESSION 105 - DIAGNOSTIC + CORRECTION FINALE
============================================
1. Vérifier pourquoi score base = 39.6 au lieu de 44.3
2. Appliquer ajustement score AVANT Formule C
3. Valider 11.09 = 56.8 pips avec amp=2.5
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd
import importlib.util
from scipy.optimize import minimize_scalar

print("="*80)
print("SESSION 105 - DIAGNOSTIC + CORRECTION SCORES")
print("="*80)
print()

# Config DB
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

spec_config = importlib.util.spec_from_file_location(
    "config",
    project_root / "app" / "config.py"
)
config_module = importlib.util.module_from_spec(spec_config)
spec_config.loader.exec_module(config_module)
Config = config_module.Config

config = Config()
db_path = config.get_db_path()

conn = duckdb.connect(str(db_path), read_only=True)

# Date référence
date_ref = "2025-09-11"

print("="*80)
print("DIAGNOSTIC : Pourquoi score base = 39.6 au lieu de 44.3 ?")
print("="*80)
print()

# Charger événements avec les 15 event_key
ref_keys = [
    'continuing jobless claims',
    'core inflation rate',
    'core inflation rate_mom',
    'core inflation rate_yoy',
    'cpi',
    'cpi s a',
    'cpi s.a',
    'inflation rate',
    'inflation rate_mom',
    'inflation rate_yoy',
    'initial jobless claims',
    'jobless claims 4 week average',
    'jobless claims 4-week average',
    'real earnings',
    'real earnings_mom'
]

event_keys_str = "', '".join(ref_keys)

query = f"""
SELECT 
    e.event_key,
    ef.family,
    ef.empirical_score,
    e.actual,
    e.estimate,
    e.forecast,
    COALESCE(
        CASE WHEN e.estimate != 0 THEN (e.actual - e.estimate) / e.estimate ELSE 0 END,
        CASE WHEN e.forecast != 0 THEN (e.actual - e.forecast) / e.forecast ELSE 0 END,
        0
    ) as surprise,
    COALESCE(
        CASE WHEN e.estimate != 0 THEN ((e.actual - e.estimate) / e.estimate) * 100 ELSE 0 END,
        CASE WHEN e.forecast != 0 THEN ((e.actual - e.forecast) / e.forecast) * 100 ELSE 0 END,
        0
    ) as surprise_pct
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE DATE(e.ts_utc) = '{date_ref}'
    AND e.country = 'US'
    AND e.event_key IN ('{event_keys_str}')
ORDER BY ef.empirical_score DESC NULLS LAST
"""

events_df = conn.execute(query).fetchdf()

print(f"✅ {len(events_df)} événements chargés")
print()

# Afficher détails
print("📊 ÉVÉNEMENTS DÉTAILLÉS (triés par score) :")
print("-"*100)
print(f"{'event_key':<45} {'family':<12} {'score':<8} {'surprise %':<12}")
print("-"*100)

for _, row in events_df.iterrows():
    score = row['empirical_score']
    score_str = f"{score:.1f}" if pd.notna(score) else "NULL"
    family = row['family'] if pd.notna(row['family']) else "NULL"
    surprise = row['surprise_pct']
    surprise_str = f"{surprise:.1f}%" if pd.notna(surprise) else "0.0%"
    
    print(f"{row['event_key']:<45} {family:<12} {score_str:<8} {surprise_str:<12}")

print()

# Calculer moyenne
scores = events_df['empirical_score'].dropna()
score_base = scores.mean()

print(f"📊 STATISTIQUES SCORES :")
print(f"   Nombre événements : {len(events_df)}")
print(f"   Scores valides    : {len(scores)}")
print(f"   Score base moyen  : {score_base:.1f}")
print(f"   Score attendu     : 44.3")
print(f"   Différence        : {score_base - 44.3:.1f}")
print()

# Test ajustement score (Session 55)
def calculate_adjusted_empirical_score(base_score, surprise_pct):
    """Ajustement score selon surprise (Session 55)"""
    abs_surprise = abs(surprise_pct)
    
    if abs_surprise < 5:
        factor = 1.0
    elif abs_surprise < 15:
        factor = 1.0 + (abs_surprise - 5) / 10 * 0.5
    elif abs_surprise < 30:
        factor = 1.5 + (abs_surprise - 15) / 15 * 0.4
    else:
        factor = 1.9
    
    return base_score * factor

print("="*80)
print("TEST : Ajustement scores INDIVIDUELS")
print("="*80)
print()

events = events_df.to_dict('records')

print("📊 SCORES AJUSTÉS PAR ÉVÉNEMENT :")
print("-"*100)
print(f"{'event_key':<45} {'base':<8} {'surprise':<12} {'factor':<8} {'ajusté':<8}")
print("-"*100)

scores_adjusted = []
for event in events:
    base = event['empirical_score']
    surprise_pct = event['surprise_pct']
    
    if pd.isna(base) or pd.isna(surprise_pct):
        continue
    
    adjusted = calculate_adjusted_empirical_score(base, surprise_pct)
    
    abs_surprise = abs(surprise_pct)
    if abs_surprise < 5:
        factor = 1.0
    elif abs_surprise < 15:
        factor = 1.0 + (abs_surprise - 5) / 10 * 0.5
    elif abs_surprise < 30:
        factor = 1.5 + (abs_surprise - 15) / 15 * 0.4
    else:
        factor = 1.9
    
    scores_adjusted.append(adjusted)
    
    print(f"{event['event_key']:<45} {base:<8.1f} {surprise_pct:<12.1f} {factor:<8.2f} {adjusted:<8.1f}")

print()
print(f"📊 Score ajusté moyen : {sum(scores_adjusted)/len(scores_adjusted):.1f}")
print()

# Test Formule D CORRECTE
print("="*80)
print("TEST : Formule D AVEC SCORES AJUSTÉS")
print("="*80)
print()

FAMILY_SENTIMENT = {
    'Inflation': 1, 'Employment': 1, 'Other': 1
}

def get_event_direction(family: str, surprise: float) -> int:
    if abs(surprise) < 0.01:
        return 1
    sentiment = FAMILY_SENTIMENT.get(family, 1)
    return sentiment if surprise > 0 else -sentiment

# Formule D CORRECTE
contributions = []
surprises_pct = []
num_events = len(scores_adjusted)

print(f"Nombre événements : {num_events}")
print()

for i, event in enumerate(events):
    if i >= len(scores_adjusted):
        break
    
    family = event['family']
    surprise = event['surprise']
    surprise_pct = event['surprise_pct']
    score_adjusted = scores_adjusted[i]
    
    surprises_pct.append(abs(surprise_pct))
    
    # Formule C sur score AJUSTÉ
    if num_events >= 2:
        impact_abs = -10.47 + 0.477 * score_adjusted
    else:
        impact_abs = -7.08 + 0.419 * score_adjusted
    
    direction = get_event_direction(family, surprise)
    contribution = impact_abs * direction
    contributions.append(contribution)

# Somme vectorielle
impact_brut = sum(contributions)

print(f"Impact brut (somme vectorielle) : {impact_brut:.1f} pips")
print()

# Amplification
max_surprise_pct = max(surprises_pct)
print(f"Surprise max : {max_surprise_pct:.1f}%")

if max_surprise_pct <= 5:
    amplification_factor = 1.0
elif max_surprise_pct <= 15:
    amplification_factor = 1.0 + (max_surprise_pct - 5) / 10 * 1.5
else:
    amplification_factor = 2.5

print(f"Amplification factor : {amplification_factor:.2f}")
print()

impact_amplifie = abs(impact_brut) * amplification_factor
print(f"Impact amplifié : {impact_amplifie:.1f} pips")
print()

# Correction 0.758
impact_final = impact_amplifie * 0.758
print(f"Impact final (× 0.758) : {impact_final:.1f} pips")
print()

# Validation
print("="*80)
print("VALIDATION")
print("="*80)
print()

print(f"Impact calculé     : {impact_final:.1f} pips")
print(f"Impact attendu     : 56.8 pips (Session 103)")
print(f"Impact réel mesuré : 57.4 pips (mesure 5h)")
print()

ecart_s103 = abs(impact_final - 56.8)
ecart_reel = abs(impact_final - 57.4)

print(f"Écart vs Session 103 : {ecart_s103:.1f} pips")
print(f"Écart vs réel mesuré : {ecart_reel:.1f} pips")
print()

if ecart_s103 < 5 or ecart_reel < 5:
    print("✅✅✅ VALIDATION RÉUSSIE !")
    print("   → Scores ajustés correctement")
    print("   → Formule D correcte")
else:
    print(f"⚠️ Écart important")
    print(f"   Besoin investigation supplémentaire")

conn.close()

print()
print("="*80)
print("✅ DIAGNOSTIC TERMINÉ")
print("="*80)
