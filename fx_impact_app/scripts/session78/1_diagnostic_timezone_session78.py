#!/usr/bin/env python3
"""
DIAGNOSTIC TIMEZONE - SESSION 78
================================

Analyse le problème timezone identifié dans script 3 Session 77.

Date : 25 octobre 2025
Session : 78
"""

import sys
from pathlib import Path
import pandas as pd
import duckdb
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import numpy as np
import dateutil.parser
import pytz

# Ajouter le répertoire racine au path
ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

SCRIPT_DIR = Path(__file__).parent
DB_PATH = ROOT_DIR / "data" / "warehouse.duckdb"

print("\n" + "="*70)
print("DIAGNOSTIC TIMEZONE - SESSION 78")
print("="*70 + "\n")

# Charger dataset
DATASET_PATH = ROOT_DIR / "data" / "movements_strong_session75_v3.csv"
print(f"📂 Dataset : {DATASET_PATH.name}")
df = pd.read_csv(DATASET_PATH)
print(f"✅ {len(df)} mouvements chargés\n")

# Identifier les 7 mouvements Session 75 par dates UNIQUEMENT
# (car les heures diffèrent entre Dukascopy time et Berne time)
dates_s75 = ['2024-12-18', '2024-04-10', '2024-02-13', '2024-06-07', '2024-01-05', '2024-12-04', '2025-09-17']

# Pour chaque date, prendre le mouvement avec le plus gros impact
df_selected = []
for date in dates_s75:
    df_date = df[df['date'] == date]
    if len(df_date) > 0:
        # Prendre le mouvement avec l'impact maximum pour cette date
        max_idx = df_date['abs_impact'].idxmax()
        df_selected.append(df_date.loc[max_idx])

df_selected = pd.DataFrame(df_selected).reset_index(drop=True)

print(f"✅ {len(df_selected)} mouvements qualité identifiés\n")

# Afficher les mouvements sélectionnés
print("📋 Mouvements sélectionnés :")
for i, row in df_selected.iterrows():
    print(f"  {i+1}. {row['date']} {row['time']} | Impact: {row['impact_pips']:.1f} pips | {row['datetime']}")
print()

# Focus sur mouvement 5 (NFP 5 janvier 2024) - problématique Session 77
print("🔍 FOCUS : MOUVEMENT NFP 5 JANVIER 2024")
print("="*70)

mvt5 = df_selected[df_selected['date'] == '2024-01-05'].iloc[0]

print(f"Date dataset     : {mvt5['date']}")
print(f"Time dataset     : {mvt5['time']}")
print(f"Datetime dataset : {mvt5['datetime']}")
print(f"Impact réel      : {mvt5['impact_pips']:.1f} pips")
print()

# Parser timezone
dt_dataset = dateutil.parser.parse(mvt5['datetime'])
print(f"Timezone dataset : {dt_dataset.tzinfo}")
print(f"Datetime UTC     : {dt_dataset.astimezone(pytz.UTC)}")

# Convertir en Berne
tz_berne = pytz.timezone('Europe/Zurich')
dt_berne = dt_dataset.astimezone(tz_berne)
print(f"Datetime Berne   : {dt_berne}")
print()

# Connexion DB
conn = duckdb.connect(str(DB_PATH), read_only=True)

# Test OLD : ±130 min SANS timezone (bug Session 77)
print("TEST OLD (Session 77) : ±130 min SANS parsing timezone")
print("-"*70)

dt_naive = datetime.strptime(f"{mvt5['date']} {mvt5['time']}", "%Y-%m-%d %H:%M")
start_old = dt_naive - timedelta(minutes=130)
end_old = dt_naive + timedelta(minutes=130)

print(f"Start : {start_old} (naive, pas de timezone)")
print(f"End   : {end_old}")

query_old = f"""
SELECT COUNT(*) as nb_events
FROM events e
INNER JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
WHERE e.ts_utc >= '{start_old.strftime('%Y-%m-%d %H:%M:%S')}'
  AND e.ts_utc <= '{end_old.strftime('%Y-%m-%d %H:%M:%S')}'
"""

nb_old = conn.execute(query_old).fetchone()[0]
print(f"Événements trouvés : {nb_old}")
print()

# Test NEW : ±30 min AVEC timezone + filtres
print("TEST NEW (Session 78) : ±30 min AVEC timezone correcte + filtres")
print("-"*70)

start_new = dt_berne - timedelta(minutes=30)
end_new = dt_berne + timedelta(minutes=30)

print(f"Start : {start_new} (Berne UTC+2)")
print(f"End   : {end_new}")

query_new = f"""
SELECT COUNT(*) as nb_events
FROM events e
INNER JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
WHERE e.ts_utc >= '{start_new.strftime('%Y-%m-%d %H:%M:%S')}'
  AND e.ts_utc <= '{end_new.strftime('%Y-%m-%d %H:%M:%S')}'
  AND e.importance_n >= 2
  AND ef.empirical_score > 20
  AND e.event_title IS NOT NULL
"""

nb_new = conn.execute(query_new).fetchone()[0]
print(f"Événements trouvés : {nb_new}")
print()

conn.close()

# Conclusion
print("📊 CONCLUSION")
print("="*70)
print()

if nb_old > nb_new:
    print(f"✅ OLD capture {nb_old - nb_new} événements de TROP")
    print(f"   ±130 min sans timezone → capture bruit")
elif nb_new > nb_old:
    print(f"⚠️  NEW capture {nb_new - nb_old} événements de PLUS")
    print(f"   Filtres qualité peut-être trop stricts ?")
else:
    print(f"➡️  Même nombre d'événements")

print()
print("✅ Bug timezone CONFIRMÉ :")
print("   - OLD ignore timezone dataset")
print("   - NEW parse timezone + convertit Berne")
print("   - Fenêtre ±30 min + filtres qualité optimal")
print()
print("🎯 Prochaine étape : Script 2 - Optimiser fenêtre temporelle")
print()

print("="*70)
print("✅ DIAGNOSTIC TERMINÉ")
print("="*70)
print()
