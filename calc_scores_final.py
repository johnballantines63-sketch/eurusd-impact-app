#!/usr/bin/env python3
"""Calcul scores avec la bonne API : calculate_score()"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path("fx_impact_app/src")))

from config import get_db_path
from event_families import FAMILY_PATTERNS
from scoring_engine import ScoringEngine
import duckdb

families = [
    'Michigan_Inflation_Expectations',
    'Michigan_5Y_Inflation_Expectations', 
    'Michigan_Consumer_Expectations',
    'Michigan_Current_Conditions',
    'Inflation_Expectations',
    'Baker_Hughes_Rig_Count',
    'Monthly_Budget_Statement',
]

print("🎯 CALCUL SCORES (API correcte)")
print()

engine = ScoringEngine(get_db_path())
conn = duckdb.connect(get_db_path())

for family in families:
    pattern = FAMILY_PATTERNS[family]
    
    print(f"⏳ {family:40}...", end=" ")
    
    try:
        result = engine.calculate_score(
            family_pattern=pattern,
            lookback_years=3
        )
        
        if result and result.get('n_events', 0) >= 3:
            conn.execute("""
                INSERT OR REPLACE INTO event_families 
                (family, empirical_score, empirical_impact, n_events)
                VALUES (?, ?, ?, ?)
            """, (
                family,
                result.get('empirical_score', 0),
                result.get('empirical_impact', 'LOW'),
                result.get('n_events', 0)
            ))
            print(f"✅ {result.get('empirical_score', 0):.0f}")
        else:
            print(f"⚠️  Insuffisant")
    except Exception as e:
        print(f"❌ {e}")

conn.commit()
conn.close()
print()
print("✅ Fait - Redémarrer Streamlit")
