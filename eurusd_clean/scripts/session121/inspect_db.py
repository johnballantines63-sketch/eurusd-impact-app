#!/usr/bin/env python3
"""
Script pour inspecter la structure de la table events
"""
import duckdb
import pandas as pd

db_path = '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb'
conn = duckdb.connect(db_path, read_only=True)

# Lister toutes les tables
print("Tables disponibles:")
print(conn.execute("SHOW TABLES").df())
print("\n" + "="*80 + "\n")

# Obtenir la structure de la table events
print("Structure de la table 'events':")
structure = conn.execute("DESCRIBE events").df()
print(structure)
print("\n" + "="*80 + "\n")

# Exemple de données (5 premières lignes)
print("Exemple de données (5 premières lignes):")
sample = conn.execute("SELECT * FROM events LIMIT 5").df()
print(sample)
print("\n" + "="*80 + "\n")

# Compter les événements par importance
print("Distribution importance_n:")
try:
    dist = conn.execute("SELECT importance_n, COUNT(*) as count FROM events GROUP BY importance_n ORDER BY importance_n").df()
    print(dist)
except Exception as e:
    print(f"Erreur: {e}")

conn.close()
