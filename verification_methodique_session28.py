#!/usr/bin/env python3
"""
Vérification MÉTHODIQUE - Session 28 (CORRIGÉ)
"""

import duckdb
import pandas as pd

con = duckdb.connect('fx_impact_app/data/warehouse.duckdb')

print("="*70)
print("VÉRIFICATION MÉTHODIQUE - SESSION 28")
print("="*70)

# 1. État event_impacts_v2
print("\n1. ÉTAT EVENT_IMPACTS_V2")
print("-"*70)

count = con.execute("SELECT COUNT(*) FROM event_impacts_v2").fetchone()[0]
print(f"Total événements : {count:,}")

if count == 8344:
    print("✅ Correspond au RAPPORT_SESSION27 (8,344)")
else:
    print(f"⚠️  RAPPORT_SESSION27 dit 8,344, base a {count:,}")

# 2. Colonnes
print("\n2. COLONNES")
print("-"*70)

cols = con.execute("DESCRIBE event_impacts_v2").df()
required_cols = ['ts_utc', 'surprise_pct', 'phase1_pips', 'ttr_minutes', 'direction']

for col in required_cols:
    if col in cols['column_name'].values:
        print(f"✅ {col} existe")
    else:
        print(f"❌ {col} MANQUANT")

# 3. Recherche 11 septembre
print("\n3. RECHERCHE 11 SEPTEMBRE")
print("-"*70)
print("RAPPORT_SESSION27 dit : '4. Inflation Rate MoM (US) : 33.3% ✅'")
print()

sept11_all = con.execute("""
    SELECT 
        ts_utc,
        event_title,
        country,
        surprise_pct,
        phase1_pips
    FROM event_impacts_v2
    WHERE ts_utc::DATE = '2025-09-11'
    ORDER BY surprise_pct DESC
""").df()

print(f"Événements 11 septembre trouvés : {len(sept11_all)}")

if len(sept11_all) == 0:
    print("❌ PROBLÈME CRITIQUE : Aucun événement 11 septembre")
    con.close()
    exit(1)

print()
inflation_found = False
for i, evt in sept11_all.iterrows():
    # Gérer NULL
    title = evt['event_title'] if pd.notna(evt['event_title']) else "NULL"
    country = evt['country'] if pd.notna(evt['country']) else "NULL"
    surprise = evt['surprise_pct'] if pd.notna(evt['surprise_pct']) else 0
    phase1 = evt['phase1_pips']
    
    print(f"{i+1}. {title} ({country})")
    print(f"   Heure: {evt['ts_utc']}")
    print(f"   Surprise: {surprise:.1f}%")
    
    # Chercher Inflation Rate MoM US
    if pd.notna(evt['event_title']) and 'Inflation Rate MoM' in evt['event_title'] and country == 'US':
        inflation_found = True
        if abs(surprise - 33.3) < 1.0:
            print(f"   ✅ CORRESPOND au RAPPORT_SESSION27 (33.3%)")
        else:
            print(f"   ⚠️  RAPPORT dit 33.3%, base a {surprise:.1f}%")
    
    if pd.isna(phase1):
        print(f"   Phase 1: NULL")
    else:
        print(f"   Phase 1: {phase1:.2f} pips")
    print()

if not inflation_found:
    print("⚠️  'Inflation Rate MoM (US)' pas trouvé dans les résultats")
    print("   Mais RAPPORT_SESSION27 dit qu'il devrait être là")

# 4. Vérification Phase 1
print("\n4. PHASE 1 - ÉTAT GLOBAL")
print("-"*70)
print("RAPPORT_SESSION27 dit : 'phase1_pips (NULL)' pour tous")
print()

phase1_check = con.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(phase1_pips) as with_phase1,
        COUNT(*) - COUNT(phase1_pips) as without_phase1
    FROM event_impacts_v2
""").fetchone()

print(f"Total : {phase1_check[0]:,}")
print(f"Avec Phase 1 : {phase1_check[1]:,}")
print(f"Sans Phase 1 : {phase1_check[2]:,}")

if phase1_check[1] == 0:
    print("✅ Aucune Phase 1 calculée (conforme RAPPORT_SESSION27)")
elif phase1_check[2] == 0:
    print("✅ Toutes les Phase 1 calculées")
else:
    print(f"⚠️  Partiellement calculé : {phase1_check[1]:,} avec / {phase1_check[2]:,} sans")

# 5. Vérification surprise
print("\n5. SURPRISE - DISTRIBUTION")
print("-"*70)
print("RAPPORT_SESSION27 dit :")
print("  - Surprise moyenne : 277.5%")
print("  - Surprise min : 30.0%")
print("  - Surprise max : 100,700.6%")
print()

surprise_stats = con.execute("""
    SELECT 
        MIN(surprise_pct) as min,
        AVG(surprise_pct) as avg,
        MAX(surprise_pct) as max
    FROM event_impacts_v2
""").fetchone()

print(f"Base de données :")
print(f"  - Min : {surprise_stats[0]:.1f}%")
print(f"  - Avg : {surprise_stats[1]:.1f}%")
print(f"  - Max : {surprise_stats[2]:.1f}%")

errors = []
if abs(surprise_stats[0] - 30.0) > 0.1:
    errors.append(f"Min surprise : base={surprise_stats[0]:.1f}% vs rapport=30.0%")
if abs(surprise_stats[1] - 277.5) > 10:
    errors.append(f"Avg surprise : base={surprise_stats[1]:.1f}% vs rapport=277.5%")
if abs(surprise_stats[2] - 100700.6) > 100:
    errors.append(f"Max surprise : base={surprise_stats[2]:.1f}% vs rapport=100,700.6%")

if len(errors) == 0:
    print("\n✅ Statistiques conformes au RAPPORT_SESSION27")
else:
    print("\n⚠️  Différences détectées :")
    for err in errors:
        print(f"   - {err}")

con.close()

# CONCLUSION
print("\n" + "="*70)
print("CONCLUSION")
print("="*70)

if inflation_found and phase1_check[1] == 0:
    print("✅ event_impacts_v2 CONFORME au RAPPORT_SESSION27")
    print()
    print("PROCHAINE ÉTAPE (selon RAPPORT_SESSION27) :")
    print("'Calculer Phase 1 depuis prices_1m pour les 8,344 événements'")
    print()
    print("Puis créer formule V4")
elif phase1_check[1] == 0:
    print("✅ Table cohérente (Phase 1 = NULL pour tous)")
    if not inflation_found:
        print("⚠️  Mais 'Inflation Rate MoM (US)' pas trouvé explicitement")
        print("   À vérifier si présent avec un autre event_title")
else:
    print("⚠️  Vérifications supplémentaires nécessaires")
