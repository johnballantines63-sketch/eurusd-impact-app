#!/usr/bin/env python3
"""
Vérification format event_key - Session 22
===========================================
Vérifie si les event_key utilisent underscores ou espaces
"""

import duckdb

print("=" * 80)
print("🔍 VÉRIFICATION FORMAT EVENT_KEY")
print("=" * 80)

conn = duckdb.connect('fx_impact_app/data/warehouse.duckdb')

# TEST 1: event_key dans table EVENTS
print("\n📊 TEST 1 : Format event_key dans table EVENTS")
print("-" * 80)

query1 = """
SELECT DISTINCT event_key, country, comparison
FROM events 
WHERE event_key LIKE '%inflation%'
  AND comparison = 'mom'
ORDER BY event_key
LIMIT 5
"""

result1 = conn.execute(query1).fetchall()

if result1:
    print(f"✅ Trouvé {len(result1)} résultats avec 'inflation' + comparison='mom' :\n")
    for row in result1:
        print(f'   event_key: "{row[0]}"')
        print(f'   country: {row[1]}, comparison: {row[2]}')
        print()
    
    # Analyser format
    first_key = result1[0][0]
    has_underscore_mom = '_mom' in first_key
    has_space_mom = ' mom' in first_key or 'mom' in first_key.split('_')[-1]
    
    print("🔍 ANALYSE DU FORMAT:")
    print(f"   Contient '_mom' (underscore dans le suffixe) : {'✅ OUI' if has_underscore_mom else '❌ NON'}")
    print(f"   Finit par 'mom' ou ' mom' : {'✅ OUI' if has_space_mom else '❌ NON'}")
    
    if has_underscore_mom:
        print("\n✅ FORMAT EVENTS : underscore (ex: 'inflation_rate_mom')")
    else:
        print(f"\n⚠️  FORMAT EVENTS : autre format (vérifier)")
else:
    print("❌ Aucun événement trouvé avec inflation + mom")

# TEST 2: event_key dans table EVENT_FAMILIES
print("\n" + "=" * 80)
print("\n📊 TEST 2 : Format event_key dans table EVENT_FAMILIES")
print("-" * 80)

query2 = """
SELECT DISTINCT event_key, country
FROM event_families
WHERE event_key LIKE '%inflation%mom%'
ORDER BY event_key
LIMIT 5
"""

result2 = conn.execute(query2).fetchall()

if result2:
    print(f"✅ Trouvé {len(result2)} résultats avec 'inflation' + 'mom' :\n")
    for row in result2:
        print(f'   event_key: "{row[0]}"')
        print(f'   country: {row[1]}')
        print()
    
    # Analyser format
    first_key = result2[0][0]
    has_underscore_mom = '_mom' in first_key
    has_space_mom = ' mom' in first_key or first_key.endswith('mom')
    
    print("🔍 ANALYSE DU FORMAT:")
    print(f"   Contient '_mom' : {'✅ OUI' if has_underscore_mom else '❌ NON'}")
    print(f"   Contient ' mom' ou finit par 'mom' : {'✅ OUI' if has_space_mom else '❌ NON'}")
    
    if has_underscore_mom:
        print("\n✅ FORMAT EVENT_FAMILIES : underscore (ex: 'inflation_rate_mom')")
    else:
        print(f"\n✅ FORMAT EVENT_FAMILIES : espace (ex: 'inflation rate_mom')")
else:
    print("❌ Aucun événement trouvé")

# TEST 3: Comparer formats
print("\n" + "=" * 80)
print("\n📊 TEST 3 : COMPARAISON DES FORMATS")
print("-" * 80)

if result1 and result2:
    events_key = result1[0][0]
    families_key = result2[0][0]
    
    print(f"\nExemple EVENTS       : '{events_key}'")
    print(f"Exemple EVENT_FAMILIES : '{families_key}'")
    
    # Normaliser pour comparaison
    events_normalized = events_key.replace(' ', '_').lower()
    families_normalized = families_key.replace(' ', '_').lower()
    
    if events_normalized == families_normalized:
        print("\n✅ FORMATS COMPATIBLES (après normalisation)")
    else:
        print("\n⚠️  FORMATS DIFFÉRENTS")
        print(f"    Events (norm)   : '{events_normalized}'")
        print(f"    Families (norm) : '{families_normalized}'")

# TEST 4: Vérifier jointure réelle
print("\n" + "=" * 80)
print("\n📊 TEST 4 : TEST DE JOINTURE RÉELLE")
print("-" * 80)

query4 = """
SELECT 
    e.event_key as events_key,
    ef.event_key as families_key,
    e.country,
    e.comparison
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE e.event_key LIKE '%inflation%'
  AND e.comparison = 'mom'
  AND e.country = 'US'
LIMIT 5
"""

result4 = conn.execute(query4).fetchall()

if result4:
    print(f"✅ Résultats jointure (5 premiers) :\n")
    match_count = 0
    for row in result4:
        events_key, families_key, country, comparison = row
        matched = families_key is not None
        match_count += 1 if matched else 0
        
        print(f"   Events: '{events_key}' | Families: '{families_key}' | {country}")
        print(f"   Match: {'✅ OUI' if matched else '❌ NON'}")
        print()
    
    match_rate = (match_count / len(result4) * 100) if result4 else 0
    print(f"📊 Taux de matching: {match_rate:.1f}% ({match_count}/{len(result4)})")
    
    if match_rate == 0:
        print("\n⚠️  PROBLÈME CRITIQUE : Aucun événement ne matche !")
        print("    🔥 Les formats sont INCOMPATIBLES")
        print("    💡 Solution : Corriger le script de reconstruction")
    elif match_rate < 100:
        print("\n⚠️  ATTENTION : Matching partiel")
    else:
        print("\n✅ PARFAIT : Tous les événements matchent")

# TEST 5: Le cas du 11 septembre
print("\n" + "=" * 80)
print("\n📊 TEST 5 : CAS SPÉCIFIQUE 11 SEPTEMBRE 2025")
print("-" * 80)

query5 = """
SELECT 
    e.event_key,
    e.country,
    e.comparison,
    e.actual,
    e.estimate,
    ef.empirical_score,
    CASE 
        WHEN ef.event_key IS NOT NULL THEN 'MATCH ✅'
        ELSE 'NO MATCH ❌'
    END as match_status
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE strftime(e.ts_utc, '%Y-%m-%d') = '2025-09-11'
  AND e.country = 'US'
  AND e.event_key LIKE '%inflation%'
ORDER BY e.ts_utc
"""

result5 = conn.execute(query5).fetchall()

if result5:
    print(f"\n✅ Événements inflation US du 11 septembre :\n")
    for row in result5:
        event_key, country, comparison, actual, estimate, score, match_status = row
        surprise = abs((actual - estimate) / estimate * 100) if estimate and estimate != 0 else 0
        
        print(f"   Event: '{event_key}'")
        print(f"   Comparison: {comparison}, Actual: {actual}, Estimate: {estimate}")
        print(f"   Surprise: {surprise:.1f}%")
        print(f"   Score: {score if score else 'N/A'}")
        print(f"   {match_status}")
        print()
    
    matched = sum(1 for row in result5 if row[6] == 'MATCH ✅')
    print(f"📊 Résultat: {matched}/{len(result5)} événements matchent avec event_families")
    
    if matched == 0:
        print("\n🔥 PROBLÈME CRITIQUE : inflation_rate_mom du 11 sept ne matche PAS !")
        print("   C'est exactement le problème identifié en Session 21")
    else:
        print("\n✅ Bon matching pour le 11 septembre")
else:
    print("❌ Aucun événement inflation trouvé le 11 septembre")

print("\n" + "=" * 80)
print("✅ VÉRIFICATION TERMINÉE")
print("=" * 80)

conn.close()
