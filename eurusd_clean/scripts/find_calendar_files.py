#!/usr/bin/env python3
"""Trouver TOUS les fichiers de données calendrier dans fx_impact_app"""

import os
from pathlib import Path

root = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app")

print("=" * 70)
print("RECHERCHE FICHIERS CALENDRIER/SCORES")
print("=" * 70)

# 1. Bases de données
print("\n📁 Bases de données (.db, .duckdb, .sqlite):")
db_files = []
for ext in ['.db', '.duckdb', '.sqlite']:
    db_files.extend(root.rglob(f"*{ext}"))

for db in sorted(db_files):
    size_mb = db.stat().st_size / (1024 * 1024)
    print(f"  {size_mb:>8.1f} MB  {db.relative_to(root)}")

# 2. Fichiers CSV calendrier
print("\n📊 Fichiers CSV (calendrier, scores, events):")
csv_keywords = ['calendar', 'event', 'score', 'famille', 'family']
csv_files = []
for csv in root.rglob("*.csv"):
    name_lower = csv.name.lower()
    if any(kw in name_lower for kw in csv_keywords):
        csv_files.append(csv)

for csv in sorted(csv_files):
    size_kb = csv.stat().st_size / 1024
    print(f"  {size_kb:>8.1f} KB  {csv.relative_to(root)}")

# 3. Fichiers JSON
print("\n📋 Fichiers JSON (config, data):")
json_files = list(root.rglob("*.json"))[:20]  # Limite à 20
for json in sorted(json_files):
    size_kb = json.stat().st_size / 1024
    if size_kb > 1:  # > 1 KB
        print(f"  {size_kb:>8.1f} KB  {json.relative_to(root)}")

# 4. Dossiers data/
print("\n📂 Dossiers 'data':")
data_dirs = list(root.rglob("data"))
for d in data_dirs:
    if d.is_dir():
        files = list(d.iterdir())
        print(f"  {d.relative_to(root)} ({len(files)} fichiers)")
        for f in files[:10]:  # Premiers 10 fichiers
            if f.is_file():
                size = f.stat().st_size / (1024 * 1024)
                print(f"    - {f.name} ({size:.1f} MB)")

print("\n" + "=" * 70)
