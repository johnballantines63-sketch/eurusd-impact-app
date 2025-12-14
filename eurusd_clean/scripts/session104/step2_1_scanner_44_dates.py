#!/usr/bin/env python3
"""
ÉTAPE 2.1 - SCANNER 44 DATES HIGH IMPACT
=========================================

Objectif : Identifier 44 dates avec événements HIGH IMPACT (score > 40)
Critères :
- Diversité événements (CPI, NFP, Jobless Claims, autres)
- Dates distinctes (pas plusieurs du même jour)
- Données prix disponibles

Output : CSV avec dates + métadonnées

Auteur : André Valentin
Date   : 31 octobre 2025 - Session 104
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd
import importlib.util
from datetime import datetime

print("=" * 80)
print("ÉTAPE 2.1 - SCANNER 44 DATES HIGH IMPACT")
print("=" * 80)
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
db_path = Path(config.get_db_path())  # Convertir en Path

print(f"📂 Database : {db_path}")
print(f"   Existe : {db_path.exists()}")
print()

if not db_path.exists():
    print("❌ ERREUR : Database introuvable")
    sys.exit(1)

# Connexion
conn = duckdb.connect(str(db_path), read_only=True)

# Query dates avec événements HIGH IMPACT
print("🔍 Recherche dates HIGH IMPACT (score > 40)...")
print()

query = """
SELECT 
    DATE(e.ts_utc) as event_date,
    COUNT(DISTINCT e.event_key) as num_events,
    COUNT(DISTINCT ef.family) as num_families,
    MAX(ef.empirical_score) as max_score,
    AVG(ef.empirical_score) as avg_score,
    SUM(CASE 
        WHEN ef.family = 'Consumer' THEN 1 
        ELSE 0 
    END) as num_consumer,
    SUM(CASE 
        WHEN ef.family = 'Employment' THEN 1 
        ELSE 0 
    END) as num_employment,
    SUM(CASE 
        WHEN ef.family = 'Inflation' THEN 1 
        ELSE 0 
    END) as num_inflation,
    STRING_AGG(DISTINCT ef.family, '|') as families
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE e.country = 'US'
    AND ef.empirical_score IS NOT NULL
    AND ef.empirical_score > 40
    AND DATE(e.ts_utc) >= '2024-01-01'
    AND DATE(e.ts_utc) <= '2025-10-31'  -- Jusqu'à aujourd'hui
GROUP BY DATE(e.ts_utc)
HAVING COUNT(DISTINCT e.event_key) >= 1
ORDER BY event_date DESC
"""

df = conn.execute(query).fetchdf()

print(f"✅ {len(df)} dates trouvées avec événements HIGH IMPACT")
print()

if len(df) == 0:
    print("❌ Aucune date HIGH IMPACT trouvée")
    conn.close()
    sys.exit(1)

# Statistiques
print("=" * 80)
print("STATISTIQUES DATES TROUVÉES")
print("=" * 80)
print()
print(f"Total dates              : {len(df)}")
print(f"Dates avec Consumer  (CPI)     : {(df['num_consumer'] > 0).sum()}")
print(f"Dates avec Employment (NFP+JC) : {(df['num_employment'] > 0).sum()}")
print(f"Dates avec Inflation           : {(df['num_inflation'] > 0).sum()}")
print()

# Distribution par type
print("📊 DISTRIBUTION PAR TYPE D'ÉVÉNEMENT PRINCIPAL :")
print("-" * 80)

df['primary_type'] = 'OTHER'
df.loc[df['num_consumer'] > 0, 'primary_type'] = 'CONSUMER'
df.loc[df['num_employment'] > 0, 'primary_type'] = 'EMPLOYMENT'
df.loc[df['num_inflation'] > 0, 'primary_type'] = 'INFLATION'

print(df['primary_type'].value_counts())
print()

# Sélection 44 dates diversifiées
print("=" * 80)
print("SÉLECTION 44 DATES DIVERSIFIÉES")
print("=" * 80)
print()

# Stratégie : 
# - 15 Consumer (CPI - très important)
# - 15 Employment (NFP + Jobless - très important)
# - 8 Inflation
# - 6 Autres (Interest Rates, Manufacturing, etc)

selected_dates = []

# 1. Consumer (15 dates max)
consumer_dates = df[df['num_consumer'] > 0].head(15)
selected_dates.append(consumer_dates)
print(f"✅ {len(consumer_dates)} dates Consumer (CPI) sélectionnées")

# 2. Employment (15 dates max, pas déjà dans Consumer)
employment_dates = df[(df['num_employment'] > 0) & (~df['event_date'].isin(consumer_dates['event_date']))].head(15)
selected_dates.append(employment_dates)
print(f"✅ {len(employment_dates)} dates Employment (NFP+JC) sélectionnées")

# 3. Inflation (8 dates max, pas déjà sélectionnées)
already_selected = pd.concat(selected_dates)['event_date']
inflation_dates = df[(df['num_inflation'] > 0) & (~df['event_date'].isin(already_selected))].head(8)
selected_dates.append(inflation_dates)
print(f"✅ {len(inflation_dates)} dates Inflation sélectionnées")

# 4. Autres (compléter jusqu'à 44)
already_selected = pd.concat(selected_dates)['event_date']
remaining_needed = 44 - len(already_selected)
other_dates = df[~df['event_date'].isin(already_selected)].head(remaining_needed)
selected_dates.append(other_dates)
print(f"✅ {len(other_dates)} dates autres événements sélectionnées")

# Combiner
df_selected = pd.concat(selected_dates).sort_values('event_date', ascending=False)

print()
print(f"📊 TOTAL SÉLECTIONNÉ : {len(df_selected)} dates")
print()

# Vérifier disponibilité prix
print("=" * 80)
print("VÉRIFICATION DISPONIBILITÉ PRIX")
print("=" * 80)
print()

print("Vérification échantillon (5 premières dates)...")

for idx, row in df_selected.head(5).iterrows():
    date_str = str(row['event_date'])
    
    # Query rapide pour vérifier prix disponibles
    query_check = f"""
    SELECT COUNT(*) as count
    FROM prices_1m
    WHERE DATE(datetime) = '{date_str}'
    """
    
    count = conn.execute(query_check).fetchone()[0]
    marker = "✅" if count > 0 else "❌"
    print(f"   {date_str} : {count} prix M1 {marker}")

print()
print("✅ Vérification OK (données prix disponibles)")
print()

# Sauvegarder CSV
output_file = Path(__file__).parent / "dates_44_high_impact.csv"

df_selected.to_csv(output_file, index=False)

print("=" * 80)
print("RÉSULTATS SAUVEGARDÉS")
print("=" * 80)
print()
print(f"📁 Fichier : {output_file.name}")
print(f"📊 Lignes  : {len(df_selected)}")
print()

# Preview
print("=" * 80)
print("PREVIEW - 10 PREMIÈRES DATES")
print("=" * 80)
print()

preview_cols = ['event_date', 'num_events', 'max_score', 'primary_type', 'num_consumer', 'num_employment', 'num_inflation']
print(df_selected[preview_cols].head(10).to_string(index=False))
print()

# Résumé final
print("=" * 80)
print("RÉSUMÉ SÉLECTION")
print("=" * 80)
print()

summary = df_selected['primary_type'].value_counts()
print("Distribution par type :")
for type_name, count in summary.items():
    pct = (count / len(df_selected)) * 100
    print(f"   {type_name:15s} : {count:2d} dates ({pct:.1f}%)")

print()
print(f"Score moyen       : {df_selected['avg_score'].mean():.1f}")
print(f"Score max absolu  : {df_selected['max_score'].max():.1f}")
print(f"Événements moyen  : {df_selected['num_events'].mean():.1f}")
print()

print("=" * 80)
print("✅ ÉTAPE 2.1 TERMINÉE")
print("=" * 80)
print()
print("🎯 Prochaine étape : 2.2 - Extraction événements + prix pour chaque date")
print()

conn.close()
