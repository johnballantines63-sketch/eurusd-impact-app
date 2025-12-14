#!/usr/bin/env python3
"""Vérifier que les familles sont bien dans event_families"""

import sys
from pathlib import Path
import duckdb

sys.path.insert(0, str(Path(__file__).parent / 'fx_impact_app' / 'src'))
from config import get_db_path

FAMILIES = [
    'Michigan_Inflation_Expectations',
    'Michigan_5Y_Inflation_Expectations',
    'Michigan_Consumer_Expectations',
    'Michigan_Current_Conditions',
    'Inflation_Expectations',
    'Baker_Hughes_Rig_Count',
    'Federal_Budget',
    'Monthly_Budget_Statement'
]

conn = duckdb.connect(get_db_path(), read_only=True)

print("✅ VÉRIFICATION event_families")
print("=" * 60)

for family in FAMILIES:
    result = conn.execute("""
        SELECT event_key, latency_median, mfe_p80, n_events_latency
        FROM event_families
        WHERE family = ?
    """, [family]).fetchall()
    
    if result:
        print(f"\n✅ {family}")
        for row in result:
            print(f"   - {row[0]}")
            print(f"     Latence: {row[1]:.1f} min | MFE: {row[2]:.1f} pips | Events: {row[3]}")
    else:
        print(f"\n❌ {family} - ABSENT")

conn.close()

print("\n" + "=" * 60)
print("💡 Redémarrez Streamlit pour charger les familles !")
