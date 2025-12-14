#!/usr/bin/env python3
"""
Examen de la situation : Données disponibles pour analyse V4
=============================================================
Vérifier quelles données on a pour Phase 1, Pullback, Impact NET
"""

import duckdb

print("="*80)
print("🔍 EXAMEN DONNÉES DISPONIBLES POUR ANALYSE V4")
print("="*80)

conn = duckdb.connect('fx_impact_app/data/warehouse.duckdb')

# ═══════════════════════════════════════════════════════════════
# PARTIE 1 : LISTER TOUTES LES TABLES
# ═══════════════════════════════════════════════════════════════

print("\n📊 PARTIE 1 : TABLES DISPONIBLES DANS LA DB")
print("="*80)

tables = conn.execute("SHOW TABLES").fetchall()
print(f"\nNombre de tables : {len(tables)}\n")
for table in tables:
    print(f"   • {table[0]}")

# ═══════════════════════════════════════════════════════════════
# PARTIE 2 : STRUCTURE event_group_impacts (utilisée actuellement)
# ═══════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("📋 PARTIE 2 : STRUCTURE event_group_impacts")
print("="*80)

schema = conn.execute("DESCRIBE event_group_impacts").fetchall()
print(f"\nColonnes disponibles :\n")
for col in schema:
    print(f"   • {col[0]:30s} {col[1]:20s}")

# Vérifier si cette table contient des infos sur pullback
print(f"\n🔍 Recherche colonnes liées au pullback :")
pullback_cols = [col for col in schema if 'pullback' in col[0].lower() or 'correction' in col[0].lower()]
if pullback_cols:
    print(f"   ✅ Colonnes pullback trouvées :")
    for col in pullback_cols:
        print(f"      • {col[0]}")
else:
    print(f"   ❌ Aucune colonne pullback dans event_group_impacts")

# ═══════════════════════════════════════════════════════════════
# PARTIE 3 : EXAMINER LES AUTRES TABLES PERTINENTES
# ═══════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("📋 PARTIE 3 : AUTRES TABLES PERTINENTES")
print("="*80)

# Chercher des tables qui pourraient contenir des données de pullback
relevant_tables = [t[0] for t in tables if any(keyword in t[0].lower() 
                   for keyword in ['impact', 'pullback', 'phase', 'movement', 'backtest', 'price'])]

print(f"\nTables potentiellement pertinentes : {len(relevant_tables)}\n")
for table in relevant_tables:
    print(f"   📊 Table : {table}")
    try:
        schema = conn.execute(f"DESCRIBE {table}").fetchall()
        print(f"      Colonnes ({len(schema)}) :")
        for col in schema[:10]:  # Montrer les 10 premières colonnes
            print(f"         • {col[0]:30s} {col[1]}")
        if len(schema) > 10:
            print(f"         ... et {len(schema) - 10} autres colonnes")
        print()
    except Exception as e:
        print(f"      ⚠️  Erreur lecture structure : {e}\n")

# ═══════════════════════════════════════════════════════════════
# PARTIE 4 : CAS SPÉCIFIQUE 11 SEPTEMBRE
# ═══════════════════════════════════════════════════════════════

print("="*80)
print("🎯 PARTIE 4 : CAS SPÉCIFIQUE 11 SEPTEMBRE 2025")
print("="*80)

# Données dans event_group_impacts
print("\n📊 Données event_group_impacts pour 11 sept :")
sept11_egi = conn.execute("""
    SELECT *
    FROM event_group_impacts
    WHERE strftime(time_group, '%Y-%m-%d %H:%M') = '2025-09-11 14:30'
""").fetchone()

if sept11_egi:
    print("   ✅ Groupe trouvé")
    # Obtenir les noms de colonnes
    cols = conn.execute("DESCRIBE event_group_impacts").fetchall()
    for i, col_info in enumerate(cols):
        col_name = col_info[0]
        value = sept11_egi[i]
        if value is not None and col_name != 'event_keys' and col_name != 'event_titles':
            print(f"      {col_name:25s} : {value}")
else:
    print("   ❌ Groupe non trouvé")

# Chercher dans d'autres tables
print(f"\n🔍 Recherche données 11 septembre dans autres tables :")

for table in relevant_tables:
    if table == 'event_group_impacts':
        continue
    
    try:
        # Essayer de trouver des données pour le 11 septembre
        result = conn.execute(f"""
            SELECT COUNT(*) 
            FROM {table} 
            WHERE CAST(time_group AS VARCHAR) LIKE '%2025-09-11 14:3%'
               OR CAST(ts_utc AS VARCHAR) LIKE '%2025-09-11 14:3%'
               OR CAST(event_time AS VARCHAR) LIKE '%2025-09-11 14:3%'
        """).fetchone()
        
        if result and result[0] > 0:
            print(f"   ✅ {table} : {result[0]} lignes pour 11 sept 14:30")
            
            # Montrer un exemple
            sample = conn.execute(f"SELECT * FROM {table} LIMIT 1").fetchone()
            if sample:
                cols = conn.execute(f"DESCRIBE {table}").fetchall()
                print(f"      Exemple de colonnes disponibles :")
                for i, col_info in enumerate(cols[:5]):
                    print(f"         • {col_info[0]:25s} : {col_info[1]}")
                print()
    except:
        pass

# ═══════════════════════════════════════════════════════════════
# PARTIE 5 : TABLE prices_1m (pour calculer pullback manuellement ?)
# ═══════════════════════════════════════════════════════════════

print("="*80)
print("📊 PARTIE 5 : DONNÉES PRICES (pour calculer pullback)")
print("="*80)

price_tables = [t[0] for t in tables if 'price' in t[0].lower()]
print(f"\nTables de prix disponibles : {len(price_tables)}\n")

for table in price_tables:
    print(f"   📊 {table}")
    schema = conn.execute(f"DESCRIBE {table}").fetchall()
    print(f"      Colonnes :")
    for col in schema:
        print(f"         • {col[0]:25s} {col[1]}")
    
    # Compter les données
    count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"      Total lignes : {count:,}")
    
    # Vérifier si on a des données pour le 11 septembre
    if count > 0:
        sept11_prices = conn.execute(f"""
            SELECT COUNT(*)
            FROM {table}
            WHERE strftime(timestamp, '%Y-%m-%d') = '2025-09-11'
        """).fetchone()[0]
        print(f"      Données 11 sept : {sept11_prices:,} lignes")
    print()

# ═══════════════════════════════════════════════════════════════
# PARTIE 6 : RECOMMANDATIONS
# ═══════════════════════════════════════════════════════════════

print("="*80)
print("💡 PARTIE 6 : RECOMMANDATIONS")
print("="*80)

print("\n📊 RÉSUMÉ DE LA SITUATION :")
print("-" * 80)

print("\n✅ CE QU'ON A :")
print("   • event_group_impacts avec mfe_pips (mouvement brut ?)")
print("   • events (événements individuels)")
print("   • event_families (scores empiriques)")

if len(price_tables) > 0:
    print("   • Tables de prix (pour calculer pullback manuellement)")

print("\n❓ CE QU'ON NE SAIT PAS ENCORE :")
print("   • mfe_pips = Phase 1 brute OU Impact NET ?")
print("   • Existe-t-il des données de pullback précalculées ?")

print("\n💡 OPTIONS POUR ANALYSER AVEC PULLBACK :")
print("\n   Option A : Si mfe_pips = Phase 1 brute")
print("      → Calculer pullback manuellement depuis prices_1m")
print("      → Impact NET = mfe_pips - pullback")
print("      → Analyser Impact NET vs prédictions")

print("\n   Option B : Si mfe_pips = Impact NET déjà")
print("      → Utiliser directement mfe_pips")
print("      → L'analyse actuelle est correcte")

print("\n   Option C : Analyser les deux")
print("      → Comparer Phase 1 vs Impact NET")
print("      → Voir lequel est plus prédictible")

print("\n🎯 PROCHAINE ÉTAPE RECOMMANDÉE :")
print("   1. Vérifier la valeur mfe_pips pour 11 septembre")
print("   2. Si mfe_pips = 14.30 → c'est bizarre, à investiguer")
print("   3. Si mfe_pips = 522 → c'est Phase 1 brute")
print("   4. Si mfe_pips = 408 → c'est Impact NET")

conn.close()

print("\n" + "="*80)
print("✅ EXAMEN TERMINÉ")
print("="*80)
