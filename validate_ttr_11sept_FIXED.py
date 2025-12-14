"""
VALIDATION TTR - 11 SEPTEMBRE 2025 (VERSION CORRIGÉE)

Objectif : Vérifier si les formules TTR prédisent correctement 5 minutes

Données réelles MT5 :
- Annonce : 12:30:00 UTC
- Pic (TTR) : 12:35:00 UTC  
- TTR réel : 5 minutes

CORRECTION : Utilise event_families au lieu de event_statistics
"""

import sys
from pathlib import Path
import duckdb

sys.path.insert(0, str(Path(__file__).parent / "fx_impact_app" / "src"))
from config import get_db_path

print("=" * 80)
print("🔍 VALIDATION TTR - 11 SEPTEMBRE 2025 (VERSION CORRIGÉE)")
print("=" * 80)
print("\n🎯 TTR réel observé (MT5) : 5 minutes (12:30 → 12:35 UTC)")
print("=" * 80)

# Connexion DB
db_path = get_db_path()
conn = duckdb.connect(str(db_path))

# 1. Récupérer TTR médian des familles concernées depuis event_families
print("\n📊 ÉTAPE 1 : TTR MÉDIAN DANS event_families")
print("-" * 80)

# Vérifier quelles familles sont dans les événements du 11 sept
query_families = """
SELECT DISTINCT family
FROM validation_events
WHERE event_date = '2025-09-11'
ORDER BY family
"""

families_list = conn.execute(query_families).fetchall()
print(f"\n✅ Familles trouvées dans validation_events (11 sept) :")
for fam in families_list:
    print(f"   • {fam[0]}")

families = [f[0] for f in families_list]

print("\n" + "-" * 80)
print("📊 Données TTR/Latency dans event_families :")
print("-" * 80)

ttr_data = {}
for family in families:
    query = f"""
    SELECT 
        family,
        ttr_median,
        latency_median,
        avg_movement_pips,
        empirical_score
    FROM event_families
    WHERE family = '{family}'
    LIMIT 1
    """
    
    result = conn.execute(query).fetchone()
    
    if result:
        fam, ttr_med, lat_med, avg_pips, score = result
        ttr_data[fam] = {
            'ttr_median': ttr_med,
            'latency_median': lat_med,
            'avg_pips': avg_pips,
            'score': score
        }
        
        print(f"\n✅ {fam}")
        print(f"   TTR médian    : {ttr_med:.1f} sec ({ttr_med/60:.1f} min)")
        print(f"   Latency médian: {lat_med:.1f} sec ({lat_med/60:.1f} min)")
        print(f"   Avg movement  : {avg_pips:.1f} pips")
        print(f"   Score empirique: {score:.1f}")
    else:
        print(f"\n❌ {family} : Pas de stats dans event_families")

# 2. Calculer TTR selon Formule A
print("\n\n📊 ÉTAPE 2 : TTR SELON FORMULE A (predict_impact_fast)")
print("-" * 80)
print("Formule : ttr = ttr_median × 0.23 si ttr_median > 1200 sec (20 min)")
print("          ttr = ttr_median sinon")

ttr_formule_a = {}
for family, data in ttr_data.items():
    ttr_med = data['ttr_median']
    
    # Formule A
    if ttr_med > 1200:  # > 20 minutes
        ttr_a = ttr_med * 0.23
        correction = "✅ (correction appliquée)"
    else:
        ttr_a = ttr_med
        correction = "⚠️  (pas de correction)"
    
    ttr_minutes_a = ttr_a / 60
    ttr_formule_a[family] = ttr_a
    
    print(f"\n{family}")
    print(f"   TTR DB       : {ttr_med/60:.1f} minutes")
    print(f"   TTR Formule A: {ttr_minutes_a:.1f} minutes {correction}")
    print(f"   Écart vs réel (5 min) : {abs(ttr_minutes_a - 5):.1f} minutes")

# 3. Calculer TTR selon Formule B
print("\n\n📊 ÉTAPE 3 : TTR SELON FORMULE B (predict_impact)")
print("-" * 80)
print("Formule : ttr = latency × 1.5")

ttr_formule_b = {}
for family, data in ttr_data.items():
    lat_med = data['latency_median']
    ttr_med = data['ttr_median']
    
    # Formule B
    ttr_b = lat_med * 1.5
    ttr_minutes_b = ttr_b / 60
    ttr_formule_b[family] = ttr_b
    
    print(f"\n{family}")
    print(f"   Latency DB   : {lat_med/60:.1f} minutes")
    print(f"   TTR Formule B: {ttr_minutes_b:.1f} minutes")
    print(f"   Écart vs réel (5 min) : {abs(ttr_minutes_b - 5):.1f} minutes")

# 4. Vérifier si données 11 septembre ont TTR directement
print("\n\n📊 ÉTAPE 4 : TTR DANS validation_events")
print("-" * 80)

query = """
SELECT 
    family,
    event_key,
    ttr_median,
    latency_median
FROM validation_events
WHERE event_date = '2025-09-11'
ORDER BY family, event_key
"""

results = conn.execute(query).fetchall()

if results:
    print("\n✅ Événements trouvés dans validation_events :")
    for row in results:
        fam, key, ttr, lat = row
        if ttr and lat:
            ttr_min = ttr / 60
            lat_min = lat / 60
            print(f"\n   {key} ({fam})")
            print(f"      TTR      : {ttr_min:.1f} min")
            print(f"      Latency  : {lat_min:.1f} min")
        else:
            print(f"\n   {key} ({fam})")
            print(f"      TTR/Latency : NULL (utilise event_families)")
else:
    print("\n⚠️  Pas de données dans validation_events")

# 5. Calculer moyennes pondérées par événement
print("\n\n📊 ÉTAPE 5 : MOYENNES PAR ÉVÉNEMENT (11 SEPT)")
print("-" * 80)

query_events = """
SELECT 
    event_key,
    family,
    surprise_pct
FROM validation_events
WHERE event_date = '2025-09-11'
  AND event_time = '12:30:00'
ORDER BY ABS(surprise_pct) DESC
"""

events_11sept = conn.execute(query_events).fetchall()

if events_11sept:
    print(f"\n✅ {len(events_11sept)} événements à 12:30 UTC :")
    
    total_weight = 0
    weighted_ttr_a = 0
    weighted_ttr_b = 0
    
    for event_key, family, surprise in events_11sept:
        weight = abs(surprise) if surprise else 1.0
        total_weight += weight
        
        if family in ttr_formule_a:
            ttr_a = ttr_formule_a[family] / 60
            ttr_b = ttr_formule_b[family] / 60
            
            weighted_ttr_a += ttr_a * weight
            weighted_ttr_b += ttr_b * weight
            
            print(f"\n   {event_key} ({family})")
            print(f"      Surprise : {surprise:.1f}%")
            print(f"      TTR A    : {ttr_a:.1f} min (poids: {weight:.1f})")
            print(f"      TTR B    : {ttr_b:.1f} min")
    
    if total_weight > 0:
        avg_ttr_a = weighted_ttr_a / total_weight
        avg_ttr_b = weighted_ttr_b / total_weight
        
        print("\n" + "-" * 80)
        print("📊 MOYENNES PONDÉRÉES (par surprise) :")
        print(f"   Formule A : {avg_ttr_a:.1f} minutes")
        print(f"   Formule B : {avg_ttr_b:.1f} minutes")

# 6. Résumé et recommandations
print("\n\n" + "=" * 80)
print("📊 RÉSUMÉ VALIDATION TTR")
print("=" * 80)

print("\n🎯 TTR RÉEL (11 sept) : 5 minutes")

if ttr_data:
    # Calculer moyennes simples
    ttr_a_values = [v / 60 for v in ttr_formule_a.values()]
    ttr_b_values = [v / 60 for v in ttr_formule_b.values()]
    
    avg_ttr_a_simple = sum(ttr_a_values) / len(ttr_a_values)
    avg_ttr_b_simple = sum(ttr_b_values) / len(ttr_b_values)
    
    mae_a = abs(avg_ttr_a_simple - 5)
    mae_b = abs(avg_ttr_b_simple - 5)
    
    precision_a = max(0, (1 - mae_a / 5) * 100)
    precision_b = max(0, (1 - mae_b / 5) * 100)
    
    print(f"\n📊 Formule A (moyenne simple) : {avg_ttr_a_simple:.1f} minutes")
    print(f"   MAE       : {mae_a:.1f} minutes")
    print(f"   Précision : {precision_a:.1f}%")
    
    print(f"\n📊 Formule B (moyenne simple) : {avg_ttr_b_simple:.1f} minutes")
    print(f"   MAE       : {mae_b:.1f} minutes")
    print(f"   Précision : {precision_b:.1f}%")
    
    # Déterminer meilleure formule
    print("\n" + "=" * 80)
    if mae_a < mae_b:
        print(f"✅ MEILLEURE : Formule A")
        print(f"   MAE : {mae_a:.1f} minutes")
        if mae_a < 2:
            print(f"   ✅ EXCELLENT (< 2 min)")
        elif mae_a < 3:
            print(f"   ⚠️  ACCEPTABLE (< 3 min)")
        else:
            print(f"   ❌ À AMÉLIORER (> 3 min)")
    else:
        print(f"✅ MEILLEURE : Formule B")
        print(f"   MAE : {mae_b:.1f} minutes")
        if mae_b < 2:
            print(f"   ✅ EXCELLENT (< 2 min)")
        elif mae_b < 3:
            print(f"   ⚠️  ACCEPTABLE (< 3 min)")
        else:
            print(f"   ❌ À AMÉLIORER (> 3 min)")
else:
    print("\n❌ Impossible de calculer - pas de données TTR")

print("\n" + "=" * 80)
print("✅ VALIDATION TTR TERMINÉE")
print("=" * 80)

conn.close()
