#!/usr/bin/env python3
"""
Vérification rapide état base de données - Session 23 (CORRIGÉ)
================================================================
"""

import duckdb

print("="*80)
print("🔍 VÉRIFICATION ÉTAT BASE DE DONNÉES")
print("="*80)

conn = duckdb.connect('fx_impact_app/data/warehouse.duckdb')

# 1. Vérifier event_families
print("\n📊 TABLE event_families :")
ef_count = conn.execute('SELECT COUNT(*) FROM event_families').fetchone()[0]
print(f"   Total lignes : {ef_count}")

ef_with_suffix = conn.execute("""
    SELECT COUNT(*) 
    FROM event_families 
    WHERE event_key LIKE '%_mom' OR event_key LIKE '%_yoy' OR event_key LIKE '%_qoq'
""").fetchone()[0]
ef_suffix_pct = (ef_with_suffix / ef_count * 100) if ef_count > 0 else 0
print(f"   Avec suffixes : {ef_with_suffix} ({ef_suffix_pct:.1f}%)")

# 2. Vérifier inflation_rate_mom US dans event_families
print("\n🔍 Recherche inflation_rate_mom US dans event_families :")
inflation_check = conn.execute("""
    SELECT event_key, country, empirical_score, avg_movement_pips
    FROM event_families
    WHERE event_key = 'inflation_rate_mom' AND country = 'US'
""").fetchone()

if inflation_check:
    print(f"   ✅ TROUVÉ :")
    print(f"      Event key : {inflation_check[0]}")
    print(f"      Country   : {inflation_check[1]}")
    print(f"      Score     : {inflation_check[2]:.2f}")
    print(f"      Avg mvt   : {inflation_check[3]:.2f} pips")
else:
    print(f"   ❌ NON TROUVÉ dans event_families")
    
    # Chercher des variations possibles
    print(f"\n   🔍 Recherche de variations proches...")
    variations = conn.execute("""
        SELECT event_key, country, empirical_score
        FROM event_families
        WHERE event_key LIKE '%inflation%rate%' AND country = 'US'
        ORDER BY event_key
    """).fetchall()
    
    if variations:
        print(f"      Trouvé {len(variations)} variation(s) :")
        for var in variations:
            print(f"         - {var[0]} (score: {var[2]:.2f})")
    else:
        print(f"      Aucune variation trouvée")

# 3. Vérifier event_group_impacts
print("\n📊 TABLE event_group_impacts :")
egi_count = conn.execute('SELECT COUNT(*) FROM event_group_impacts').fetchone()[0]
print(f"   Total groupes : {egi_count}")

# 4. Vérifier groupe 11 septembre
print("\n🔍 Groupe 11 septembre 14:30 dans event_group_impacts :")
sept11_group = conn.execute("""
    SELECT 
        time_group,
        event_keys,
        max_empirical_score,
        mfe
    FROM event_group_impacts
    WHERE strftime(time_group, '%Y-%m-%d %H:%M') = '2025-09-11 14:30'
""").fetchone()

if sept11_group:
    print(f"   ✅ TROUVÉ :")
    print(f"      Time group : {sept11_group[0]}")
    print(f"      Event keys : {sept11_group[1][:150]}...")
    print(f"      Score MAX  : {sept11_group[2]:.2f}")
    print(f"      MFE        : {sept11_group[3]:.2f} pips")
    
    if 'inflation_rate_mom' in sept11_group[1]:
        print(f"\n      ✅ inflation_rate_mom PRÉSENT dans event_keys")
    else:
        print(f"\n      ❌ inflation_rate_mom ABSENT de event_keys")
        print(f"\n      Event keys complets :")
        print(f"      {sept11_group[1]}")
else:
    print(f"   ❌ NON TROUVÉ")

# 5. Vérifier les événements bruts du 11 septembre dans table events
print("\n🔍 Événements bruts 11 septembre 14:30 dans table events :")
events_raw = conn.execute("""
    SELECT 
        event_key,
        country,
        actual,
        estimate
    FROM events
    WHERE strftime(ts_utc, '%Y-%m-%d %H:%M') = '2025-09-11 14:30'
      AND country = 'US'
    ORDER BY event_key
""").fetchall()

print(f"   Total événements : {len(events_raw)}")
if len(events_raw) > 0:
    print(f"\n   Liste des event_key :")
    for evt in events_raw:
        print(f"      - {evt[0]}")
    
    # Chercher inflation_rate_mom
    inflation_found = any(evt[0] == 'inflation_rate_mom' for evt in events_raw)
    if inflation_found:
        print(f"\n      ✅ inflation_rate_mom PRÉSENT dans events")
    else:
        print(f"\n      ❌ inflation_rate_mom ABSENT de events")
        print(f"\n      💡 Cherchons des variations...")
        inflation_vars = [evt[0] for evt in events_raw if 'inflation' in evt[0].lower() and 'rate' in evt[0].lower()]
        if inflation_vars:
            print(f"         Trouvé : {inflation_vars}")

conn.close()

print("\n" + "="*80)
print("✅ VÉRIFICATION TERMINÉE")
print("="*80)

print("\n💡 DIAGNOSTIC :")
print(f"   event_families       : {ef_count} lignes ({ef_suffix_pct:.1f}% suffixes)")
if ef_count >= 700 and ef_suffix_pct > 20:
    print(f"      ✅ Reconstruction semble correcte (attendu: 747, 23.8%)")
else:
    print(f"      ❌ Reconstruction semble obsolète")

print(f"\n   event_group_impacts  : {egi_count} groupes")
if egi_count >= 19000:
    print(f"      ✅ Reconstruction semble correcte (attendu: 19,653)")
else:
    print(f"      ❌ Reconstruction semble obsolète")

print(f"\n   🎯 CONCLUSION :")
if ef_count >= 700 and egi_count >= 19000:
    print(f"      Les tables semblent correctement reconstruites Session 22")
    print(f"      Mais inflation_rate_mom pourrait avoir un nom différent dans events")
else:
    print(f"      Les reconstructions Session 22 pourraient ne pas avoir été exécutées")
