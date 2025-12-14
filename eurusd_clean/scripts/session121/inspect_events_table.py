#!/usr/bin/env python3
"""
Script pour inspecter la structure de la table events
"""
import duckdb

db_path = '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb'
conn = duckdb.connect(db_path, read_only=True)

# Obtenir la structure de la table
print("Structure de la table 'events':")
print(conn.execute("DESCRIBE events").df())

print("\n\nExemple de données (5 premières lignes):")
print(conn.execute("SELECT * FROM events LIMIT 5").df())

print("\n\nValeurs distinctes importance_n:")
print(conn.execute("SELECT DISTINCT importance_n FROM events").df())

conn.close()
