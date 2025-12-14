#!/usr/bin/env python3
import sys
from pathlib import Path

src_path = Path(__file__).parent / "fx_impact_app" / "src"
sys.path.insert(0, str(src_path))

from config import get_db_path
from event_families import FAMILY_PATTERNS
from scoring_engine import ScoringEngine

print("=" * 70)
print("📊 RECALCUL SCORES EMPIRIQUES - Patterns Michigan")
print("=" * 70)
print()

new_families = [
    'Michigan_Inflation_Expectations',
    'Michigan_5Y_Inflation_Expectations',
    'Michigan_Consumer_Expectations',
    'Michigan_Current_Conditions',
    'Inflation_Expectations',
    'Baker_Hughes_Rig_Count',
    'Federal_Budget',
    'Monthly_Budget_Statement'
]

print(f"🎯 Calcul pour {len(new_families)} nouvelles familles")
print()

engine = ScoringEngine(get_db_path())

results = []
for family in new_families:
    if family not in FAMILY_PATTERNS:
        print(f"⚠️  {family}: Pattern non trouvé")
        continue
    
    print(f"⏳ {family:45}...", end=" ")
    
    try:
        score = engine.calculate_empirical_score(
            family_pattern=FAMILY_PATTERNS[family],
            lookback_years=3,
            min_events=3
        )
        
        if score:
            results.append({
                'family': family,
                'score': score['empirical_score'],
                'impact': score['empirical_impact'],
                'n_events': score['n_events']
            })
            print(f"✅ Score: {score['empirical_score']:3.0f} ({score['empirical_impact']:6}) - {score['n_events']} events")
        else:
            print(f"⚠️  Pas assez de données")
    except Exception as e:
        print(f"❌ {e}")

engine.close()

print()
print("=" * 70)
print("📊 RÉSUMÉ")
print("=" * 70)
print()

if results:
    print(f"✅ {len(results)} familles calculées:")
    print()
    for r in results:
        icon = "🔴" if r['impact'] == "HIGH" else "🟡" if r['impact'] == "MEDIUM" else "🟢"
        print(f"{icon} {r['family']:40} Score: {r['score']:3.0f}")
else:
    print("❌ Aucun score calculé")

print()
print("🔄 Redémarrez Streamlit pour voir les changements")
