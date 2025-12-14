#!/usr/bin/env python3
"""
Diagnostic complet : Pourquoi le Calendrier trouve 88 événements mais 0 scores ?
"""

import duckdb
from pathlib import Path
from datetime import datetime, timedelta
import re

# Import des patterns
import sys
sys.path.insert(0, 'fx_impact_app/src')
from event_families import FAMILY_PATTERNS

def get_db_path():
    return "fx_impact_app/data/warehouse.duckdb"

def identify_family(event_key):
    """Copie de la fonction du Calendrier"""
    for family_name, pattern in FAMILY_PATTERNS.items():
        clean_pattern = pattern.replace('(?i)', '')
        if re.search(clean_pattern, event_key, re.IGNORECASE):
            return family_name
    return None

def diagnose():
    print("🔍 DIAGNOSTIC CALENDRIER - POURQUOI 0 SCORES ?")
    print("="*70)
    
    # Paramètres de test (comme dans vos captures)
    date_from = datetime.now()
    date_to = datetime.now() + timedelta(days=7)
    countries = ['US', 'EU']
    min_importance = 2  # Medium
    
    # Expansion pays (comme dans le code)
    expanded_countries = []
    eurozone_countries = ['EU', 'DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'AT', 'PT', 'IE', 'GR']
    
    for country in countries:
        if country == 'EU':
            expanded_countries.extend(eurozone_countries)
        else:
            expanded_countries.append(country)
    
    expanded_countries = list(set(expanded_countries))
    
    print(f"\n📅 Période : {date_from.strftime('%Y-%m-%d')} → {date_to.strftime('%Y-%m-%d')}")
    print(f"🌍 Pays : {', '.join(expanded_countries)}")
    print(f"⭐ Importance <= {min_importance}")
    
    # Query (exactement comme dans le code)
    conn = duckdb.connect(get_db_path())
    
    country_filter = "', '".join(expanded_countries)
    
    query = f"""
    SELECT 
        e.ts_utc, e.event_key, e.country, e.importance_n,
        e.actual, e.forecast, e.previous,
        ef.empirical_score, ef.empirical_impact, ef.impact_level,
        ef.avg_movement_pips, ef.avg_latency_min, ef.reaction_rate
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key AND e.country = ef.country
    WHERE e.ts_utc >= '{date_from.strftime('%Y-%m-%d %H:%M')}'
      AND e.ts_utc <= '{date_to.strftime('%Y-%m-%d %H:%M')}'
      AND e.country IN ('{country_filter}')
      AND e.importance_n <= {min_importance}
    ORDER BY e.ts_utc
    """
    
    df = conn.execute(query).fetchdf()
    conn.close()
    
    print(f"\n✅ Événements trouvés : {len(df)}")
    
    if len(df) == 0:
        print("❌ Aucun événement trouvé !")
        return
    
    # Analyser les résultats
    print("\n" + "="*70)
    print("📊 ANALYSE DES RÉSULTATS")
    print("="*70)
    
    # Compter par importance
    for imp in [1, 2, 3]:
        count = len(df[df['importance_n'] == imp])
        label = {1: 'High', 2: 'Medium', 3: 'Low'}[imp]
        print(f"   {label:8s} (importance={imp}): {count:3d} événements")
    
    # Compter ceux avec scores empiriques
    with_scores = df['empirical_score'].notna().sum()
    without_scores = df['empirical_score'].isna().sum()
    
    print(f"\n📈 Scores empiriques :")
    print(f"   Avec score    : {with_scores:3d} événements ({with_scores/len(df)*100:.1f}%)")
    print(f"   Sans score    : {without_scores:3d} événements ({without_scores/len(df)*100:.1f}%)")
    
    if without_scores > 0:
        print(f"\n⚠️  {without_scores} événements sans scores → seront filtrés !")
    
    # Identifier les familles avec Python
    print("\n" + "="*70)
    print("🔍 TEST identify_family() SUR LES ÉVÉNEMENTS")
    print("="*70)
    
    df['family_python'] = df['event_key'].apply(identify_family)
    
    with_family = df['family_python'].notna().sum()
    without_family = df['family_python'].isna().sum()
    
    print(f"   Avec famille  : {with_family:3d} événements ({with_family/len(df)*100:.1f}%)")
    print(f"   Sans famille  : {without_family:3d} événements ({without_family/len(df)*100:.1f}%)")
    
    # Afficher échantillon d'événements SANS famille
    if without_family > 0:
        print(f"\n❌ Exemples d'événements SANS famille (max 10) :")
        no_family = df[df['family_python'].isna()].head(10)
        for idx, row in no_family.iterrows():
            print(f"   {row['ts_utc'].strftime('%Y-%m-%d %H:%M')} | "
                  f"{row['country']:3s} | imp={row['importance_n']} | "
                  f"{row['event_key'][:60]}")
    
    # Afficher événements AVEC famille
    if with_family > 0:
        print(f"\n✅ Exemples d'événements AVEC famille (max 10) :")
        has_family = df[df['family_python'].notna()].head(10)
        for idx, row in has_family.iterrows():
            print(f"   {row['ts_utc'].strftime('%Y-%m-%d %H:%M')} | "
                  f"{row['country']:3s} | {row['family_python']:20s} | "
                  f"score={row['empirical_score'] if pd.notna(row['empirical_score']) else 'N/A':>6s} | "
                  f"{row['event_key'][:40]}")
    
    # Comparer famille Python vs DB
    print("\n" + "="*70)
    print("🔍 COMPARAISON identify_family() vs event_families (DB)")
    print("="*70)
    
    # Événements avec famille Python MAIS sans score DB
    python_yes_db_no = df[(df['family_python'].notna()) & (df['empirical_score'].isna())]
    
    if len(python_yes_db_no) > 0:
        print(f"\n⚠️  {len(python_yes_db_no)} événements avec famille Python MAIS sans score DB :")
        for idx, row in python_yes_db_no.head(10).iterrows():
            print(f"   {row['family_python']:20s} | {row['country']:3s} | {row['event_key'][:50]}")
        
        print(f"\n💡 Ces événements devraient avoir des scores mais n'en ont pas !")
        print(f"   → Vérifier la table event_families pour ces event_keys")
    
    # Statistiques finales
    print("\n" + "="*70)
    print("📊 RÉSUMÉ")
    print("="*70)
    
    print(f"\n1️⃣  Query trouve : {len(df)} événements")
    print(f"2️⃣  Avec scores DB : {with_scores} événements")
    print(f"3️⃣  Identifiables Python : {with_family} événements")
    print(f"4️⃣  Avec scores ET famille : {len(df[(df['empirical_score'].notna()) & (df['family_python'].notna())])} événements")
    
    # Le problème
    if with_scores == 0:
        print(f"\n❌ PROBLÈME IDENTIFIÉ :")
        print(f"   Aucun événement n'a de score empirique dans la DB !")
        print(f"   → La table event_families est vide ou incomplète")
        print(f"   → OU le JOIN ne fonctionne pas (event_key + country ne matchent pas)")
    
    elif with_scores < with_family:
        print(f"\n⚠️  PROBLÈME PARTIEL :")
        print(f"   {with_family - with_scores} événements ont une famille Python")
        print(f"   mais PAS de scores dans event_families")
        print(f"   → Ces événements devraient être dans event_families")
    
    else:
        print(f"\n✅ Pas de problème de mapping")

if __name__ == "__main__":
    import pandas as pd
    diagnose()
