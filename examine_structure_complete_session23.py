#!/usr/bin/env python3
"""
Examen complet - CORRIGÉ pour gérer les NULL
=============================================
"""

import duckdb

print("="*80)
print("🎯 EXAMEN COMPLET - 11 SEPTEMBRE 2025")
print("="*80)

conn = duckdb.connect('fx_impact_app/data/warehouse.duckdb')

# ═══════════════════════════════════════════════════════════════
# VÉRIFICATION RAPIDE : TABLES RECONSTRUITES ?
# ═══════════════════════════════════════════════════════════════

print("\n✅ Vérification reconstructions Session 22 :")
ef_count = conn.execute('SELECT COUNT(*) FROM event_families').fetchone()[0]
ef_suffix = conn.execute("SELECT COUNT(*) FROM event_families WHERE event_key LIKE '%_mom' OR event_key LIKE '%_yoy' OR event_key LIKE '%_qoq'").fetchone()[0]
egi_count = conn.execute('SELECT COUNT(*) FROM event_group_impacts').fetchone()[0]

print(f"   event_families      : {ef_count} lignes ({ef_suffix/ef_count*100:.1f}% suffixes)")
print(f"   event_group_impacts : {egi_count} groupes")

if ef_count == 747 and egi_count == 19653:
    print(f"   ✅ Tables correctement reconstruites !")
else:
    print(f"   ⚠️  Nombres inattendus")

# ═══════════════════════════════════════════════════════════════
# CAS DU 11 SEPTEMBRE : ÉVÉNEMENTS DANS TABLE EVENTS
# ═══════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("📊 ÉVÉNEMENTS 11 SEPTEMBRE 14:30 (table events)")
print("="*80)

events_sept11 = conn.execute("""
    SELECT 
        event_key,
        actual,
        estimate,
        comparison
    FROM events
    WHERE strftime(ts_utc, '%Y-%m-%d %H:%M') = '2025-09-11 14:30'
      AND country = 'US'
    ORDER BY event_key
""").fetchall()

print(f"\nTotal : {len(events_sept11)} événements\n")

inflation_rate_mom_found = False
inflation_rate_mom_data = None

for i, evt in enumerate(events_sept11, 1):
    event_key = evt[0]
    actual = evt[1]
    estimate = evt[2]
    
    # Calculer surprise si possible
    if actual is not None and estimate is not None and estimate != 0:
        surprise = abs((actual - estimate) / estimate * 100)
        surprise_str = f"{surprise:5.1f}%"
    else:
        surprise_str = "  N/A "
    
    # Formater les valeurs
    actual_str = f"{actual:8.2f}" if actual is not None else "    NULL"
    estimate_str = f"{estimate:8.2f}" if estimate is not None else "    NULL"
    
    # Marquer inflation rate_mom
    marker = "🎯" if event_key == "inflation rate_mom" else "  "
    
    print(f"{marker} {i:2d}. {event_key:45s} | Act: {actual_str} | Est: {estimate_str} | Surp: {surprise_str}")
    
    # Mémoriser inflation rate_mom
    if event_key == "inflation rate_mom":
        inflation_rate_mom_found = True
        inflation_rate_mom_data = {
            'actual': actual,
            'estimate': estimate,
            'surprise': surprise if actual and estimate and estimate != 0 else 0
        }

# ═══════════════════════════════════════════════════════════════
# VÉRIFIER CORRESPONDANCE AVEC EVENT_FAMILIES
# ═══════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("🔍 CORRESPONDANCE AVEC event_families")
print("="*80)

# Vérifier inflation rate_mom spécifiquement
print("\n🎯 Recherche 'inflation rate_mom' (AVEC ESPACE) :")
inflation_family = conn.execute("""
    SELECT event_key, country, empirical_score, family
    FROM event_families
    WHERE event_key = 'inflation rate_mom' AND country = 'US'
""").fetchone()

if inflation_family:
    print(f"   ✅ TROUVÉ dans event_families !")
    print(f"      Event key : {inflation_family[0]}")
    print(f"      Country   : {inflation_family[1]}")
    print(f"      Score     : {inflation_family[2]:.2f}")
    print(f"      Family    : {inflation_family[3]}")
else:
    print(f"   ❌ NON TROUVÉ dans event_families")

# ═══════════════════════════════════════════════════════════════
# VÉRIFIER GROUPE DANS EVENT_GROUP_IMPACTS
# ═══════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("🔍 GROUPE 11 SEPTEMBRE dans event_group_impacts")
print("="*80)

sept11_group = conn.execute("""
    SELECT 
        time_group,
        num_events,
        event_keys,
        max_empirical_score,
        mfe_pips
    FROM event_group_impacts
    WHERE strftime(time_group, '%Y-%m-%d %H:%M') = '2025-09-11 14:30'
""").fetchone()

if sept11_group:
    print(f"\n✅ Groupe trouvé !")
    print(f"   Time group    : {sept11_group[0]}")
    print(f"   Num events    : {sept11_group[1]}")
    print(f"   Score MAX     : {sept11_group[3]:.2f}")
    print(f"   MFE           : {sept11_group[4]:.2f} pips")
    
    print(f"\n   Event keys dans le groupe :")
    event_keys_list = sept11_group[2].split(' + ')
    for key in event_keys_list:
        marker = "🎯" if key == "inflation rate_mom" else "  "
        print(f"   {marker} - {key}")
    
    # Vérifier présence inflation rate_mom
    if 'inflation rate_mom' in sept11_group[2]:
        print(f"\n   ✅ 'inflation rate_mom' PRÉSENT dans le groupe !")
    else:
        print(f"\n   ❌ 'inflation rate_mom' ABSENT du groupe")
else:
    print(f"\n❌ Groupe NON trouvé")

# ═══════════════════════════════════════════════════════════════
# DIAGNOSTIC FINAL
# ═══════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("💡 DIAGNOSTIC FINAL")
print("="*80)

print(f"\n✅ ÉTAT DES RECONSTRUCTIONS SESSION 22 :")
print(f"   • event_families : {ef_count} lignes ✅")
print(f"   • event_group_impacts : {egi_count} groupes ✅")
print(f"   • 11 septembre reconstruit : {'✅' if sept11_group else '❌'}")

print(f"\n🎯 PROBLÈME IDENTIFIÉ :")
print(f"   Le nom de l'événement est 'inflation rate_mom' (AVEC ESPACE)")
print(f"   et NON 'inflation_rate_mom' (AVEC UNDERSCORE)")

if inflation_rate_mom_found and inflation_rate_mom_data:
    print(f"\n📊 DONNÉES INFLATION RATE_MOM (11 sept 14:30) :")
    print(f"   Actual    : {inflation_rate_mom_data['actual']}")
    print(f"   Estimate  : {inflation_rate_mom_data['estimate']}")
    print(f"   Surprise  : {inflation_rate_mom_data['surprise']:.1f}%")
    
    if inflation_family:
        print(f"   Score     : {inflation_family[2]:.2f}")
        
        print(f"\n✅ TOUTES LES DONNÉES SONT PRÉSENTES !")
        print(f"   Il faut juste utiliser 'inflation rate_mom' (avec espace) dans les tests")

conn.close()

print("\n" + "="*80)
print("✅ EXAMEN TERMINÉ")
print("="*80)
