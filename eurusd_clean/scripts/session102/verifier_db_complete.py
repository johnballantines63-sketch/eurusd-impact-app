#!/usr/bin/env python3
"""
VÉRIFICATION BASE DE DONNÉES - ÉVÉNEMENTS COMPLETS
===================================================

Afficher TOUS les champs DB pour une date donnée
pour vérification manuelle sur MyFxBook
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd

# Chemins
project_root = Path(__file__).resolve().parents[2]
fx_impact_app = project_root.parent / "fx_impact_app"
sys.path.insert(0, str(fx_impact_app / "src"))

from config import get_db_path

# ============================================================================
# CHOISIR DATE À VÉRIFIER
# ============================================================================

# Date AVANT 11.09 pour être sûr que les données ne sont pas manuelles
TEST_DATE = '2024-11-13'

print("=" * 100)
print(f"VÉRIFICATION DB - DATE {TEST_DATE}")
print("=" * 100)
print()

db_path = get_db_path()
conn = duckdb.connect(str(db_path), read_only=True)

# ============================================================================
# REQUÊTE COMPLÈTE - TOUS LES CHAMPS
# ============================================================================

query = """
SELECT 
    e.event_key,
    e.event_title,
    e.label,
    e.country,
    e.ts_utc,
    e.actual,
    e.estimate,
    e.previous,
    ef.empirical_score,
    ef.family
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE DATE(e.ts_utc) = ?
    AND e.country = 'US'
    AND ef.empirical_score > 40
ORDER BY e.ts_utc
"""

df = conn.execute(query, [TEST_DATE]).fetchdf()

print(f"✅ {len(df)} événements trouvés\n")

if len(df) == 0:
    print("❌ Aucun événement trouvé pour cette date !")
    print("   Essayer une autre date ?")
    conn.close()
    sys.exit(1)

# ============================================================================
# AFFICHER DÉTAILS COMPLETS
# ============================================================================

print("=" * 100)
print("DÉTAILS COMPLETS PAR ÉVÉNEMENT")
print("=" * 100)
print()

for idx, event in df.iterrows():
    print(f"{'='*100}")
    print(f"ÉVÉNEMENT {idx+1}/{len(df)}")
    print(f"{'='*100}")
    print(f"event_key       : {event['event_key']}")
    print(f"event_title     : {event['event_title']}")
    print(f"label           : {event['label']}")
    print(f"family          : {event['family']}")
    print(f"country         : {event['country']}")
    print(f"ts_utc          : {event['ts_utc']}")
    print(f"actual          : {event['actual']}")
    print(f"estimate        : {event['estimate']}")
    print(f"previous        : {event['previous']}")
    print(f"empirical_score : {event['empirical_score']}")
    
    # Calculer surprise
    if pd.notna(event['actual']) and pd.notna(event['estimate']) and event['estimate'] != 0:
        surprise = abs((event['actual'] - event['estimate']) / event['estimate']) * 100
        print(f"surprise_pct    : {surprise:.1f}%")
    else:
        print(f"surprise_pct    : N/A (données manquantes)")
    
    print()

# ============================================================================
# RÉSUMÉ POUR VÉRIFICATION MYFXBOOK
# ============================================================================

print("=" * 100)
print("RÉSUMÉ POUR VÉRIFICATION MYFXBOOK")
print("=" * 100)
print()

print(f"📅 Date à vérifier : {TEST_DATE}")
print(f"🕐 Heure UTC       : {df.iloc[0]['ts_utc'] if len(df) > 0 else 'N/A'}")
print(f"📊 Nombre events   : {len(df)}")
print()

print("Liste événements (pour recherche MyFxBook) :")
print("-" * 100)

for idx, event in df.iterrows():
    event_name = event['event_title'] if pd.notna(event['event_title']) else event['label']
    if pd.isna(event_name):
        event_name = "INCONNU"
    
    actual = f"{event['actual']:.2f}" if pd.notna(event['actual']) else "NaN"
    estimate = f"{event['estimate']:.2f}" if pd.notna(event['estimate']) else "NaN"
    
    print(f"{idx+1:2d}. {event_name:30s} | Actual: {actual:>8s} | Estimate: {estimate:>8s}")

print()

# ============================================================================
# DIAGNOSTIC PROBLÈMES
# ============================================================================

print("=" * 100)
print("DIAGNOSTIC PROBLÈMES")
print("=" * 100)
print()

# Problème 1 : Labels manquants
null_titles = df['event_title'].isna().sum()
null_labels = df['label'].isna().sum()

print(f"⚠️  event_title NULL : {null_titles}/{len(df)}")
print(f"⚠️  label NULL       : {null_labels}/{len(df)}")

if null_titles > 0 or null_labels > 0:
    print("\n❌ PROBLÈME : Labels manquants dans DB !")
    print("   → Les event_title et/ou label devraient être remplis")

# Problème 2 : Actual manquants
null_actual = df['actual'].isna().sum()

print(f"\n⚠️  actual NULL      : {null_actual}/{len(df)}")

if null_actual > 0:
    print("\n❌ PROBLÈME : Valeurs actual manquantes !")
    print("   → Vérifier l'import des données")

# Problème 3 : Estimate manquants
null_estimate = df['estimate'].isna().sum()

print(f"\n⚠️  estimate NULL    : {null_estimate}/{len(df)}")

if null_estimate > 0:
    print("\n❌ PROBLÈME : Valeurs estimate manquantes !")

conn.close()

print()
print("=" * 100)
print("INSTRUCTIONS VÉRIFICATION")
print("=" * 100)
print()
print("1. Aller sur MyFxBook Calendar : https://www.myfxbook.com/forex-economic-calendar")
print(f"2. Chercher date : {TEST_DATE}")
print("3. Filtrer pays : United States")
print("4. Comparer les événements affichés ci-dessus avec le calendrier")
print("5. Vérifier :")
print("   - Noms des événements")
print("   - Valeurs actual")
print("   - Valeurs forecast (estimate)")
print()
