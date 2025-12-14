"""
VALIDATION TTR - 11 SEPTEMBRE 2025

Objectif : Vérifier si les formules TTR prédisent correctement 5 minutes

Données réelles MT5 :
- Annonce : 12:30:00 UTC
- Pic (TTR) : 12:35:00 UTC  
- TTR réel : 5 minutes
"""

import sys
from pathlib import Path
import duckdb

sys.path.insert(0, str(Path(__file__).parent / "fx_impact_app" / "src"))
from config import get_db_path

print("=" * 80)
print("🔍 VALIDATION TTR - 11 SEPTEMBRE 2025")
print("=" * 80)
print("\n🎯 TTR réel observé (MT5) : 5 minutes (12:30 → 12:35 UTC)")
print("=" * 80)

# Connexion DB
db_path = get_db_path()
conn = duckdb.connect(str(db_path))

# 1. Récupérer TTR médian des familles concernées
print("\n📊 ÉTAPE 1 : TTR MÉDIAN EN DB")
print("-" * 80)

families = ['Jobless_Claims', 'CPI']

for family in families:
    query = f"""
    SELECT 
        family,
        ttr_median,
        latency_median,
        mfe_p80
    FROM event_statistics
    WHERE family = '{family}'
    """
    
    result = conn.execute(query).fetchone()
    
    if result:
        fam, ttr_med, lat_med, mfe = result
        print(f"\n✅ {fam}")
        print(f"   TTR médian    : {ttr_med:.1f} secondes ({ttr_med/60:.1f} minutes)")
        print(f"   Latency médian: {lat_med:.1f} secondes ({lat_med/60:.1f} minutes)")
        print(f"   MFE P80       : {mfe:.1f} pips")
    else:
        print(f"\n❌ {family} : Pas de stats en DB")

# 2. Calculer TTR selon Formule A
print("\n\n📊 ÉTAPE 2 : TTR SELON FORMULE A (predict_impact_fast)")
print("-" * 80)
print("Formule : ttr = ttr_median × 0.23 si ttr_median > 1200 sec (20 min)")
print("          ttr = ttr_median sinon")

for family in families:
    query = f"""
    SELECT ttr_median
    FROM event_statistics
    WHERE family = '{family}'
    """
    
    result = conn.execute(query).fetchone()
    
    if result:
        ttr_med = result[0]
        
        # Formule A
        if ttr_med > 1200:  # > 20 minutes
            ttr_formule_a = ttr_med * 0.23
            correction = "✅ (correction appliquée)"
        else:
            ttr_formule_a = ttr_med
            correction = "⚠️  (pas de correction)"
        
        ttr_minutes_a = ttr_formule_a / 60
        
        print(f"\n{family}")
        print(f"   TTR DB       : {ttr_med/60:.1f} minutes")
        print(f"   TTR Formule A: {ttr_minutes_a:.1f} minutes {correction}")
        print(f"   Écart vs réel (5 min) : {abs(ttr_minutes_a - 5):.1f} minutes")

# 3. Calculer TTR selon Formule B
print("\n\n📊 ÉTAPE 3 : TTR SELON FORMULE B (predict_impact)")
print("-" * 80)
print("Formule : ttr = latency × 1.5")

for family in families:
    query = f"""
    SELECT latency_median, ttr_median
    FROM event_statistics
    WHERE family = '{family}'
    """
    
    result = conn.execute(query).fetchone()
    
    if result:
        lat_med, ttr_med = result
        
        # Formule B
        ttr_formule_b = lat_med * 1.5
        ttr_minutes_b = ttr_formule_b / 60
        
        print(f"\n{family}")
        print(f"   Latency DB   : {lat_med/60:.1f} minutes")
        print(f"   TTR Formule B: {ttr_minutes_b:.1f} minutes")
        print(f"   Écart vs réel (5 min) : {abs(ttr_minutes_b - 5):.1f} minutes")

# 4. Vérifier si données 11 septembre ont TTR
print("\n\n📊 ÉTAPE 4 : TTR DANS VALIDATION_EVENTS")
print("-" * 80)

query = """
SELECT 
    family,
    event_key,
    ttr_median,
    latency_median
FROM validation_events
WHERE event_date = '2025-09-11'
  AND family IN ('Jobless_Claims', 'CPI')
ORDER BY family, event_key
LIMIT 5
"""

results = conn.execute(query).fetchall()

if results:
    print("\n✅ Événements trouvés dans validation_events :")
    for row in results:
        fam, key, ttr, lat = row
        ttr_min = ttr / 60 if ttr else 0
        lat_min = lat / 60 if lat else 0
        print(f"\n   {key} ({fam})")
        print(f"      TTR      : {ttr_min:.1f} min")
        print(f"      Latency  : {lat_min:.1f} min")
else:
    print("\n⚠️  Pas de TTR dans validation_events")

# 5. Résumé et recommandations
print("\n\n" + "=" * 80)
print("📊 RÉSUMÉ VALIDATION TTR")
print("=" * 80)

print("\n🎯 TTR RÉEL (11 sept) : 5 minutes")

# Récupérer les valeurs pour résumé
query_jobless = """
SELECT ttr_median, latency_median 
FROM event_statistics 
WHERE family = 'Jobless_Claims'
"""
jc = conn.execute(query_jobless).fetchone()

query_cpi = """
SELECT ttr_median, latency_median 
FROM event_statistics 
WHERE family = 'CPI'
"""
cpi = conn.execute(query_cpi).fetchone()

if jc and cpi:
    # Moyennes
    ttr_med_avg = (jc[0] + cpi[0]) / 2
    lat_med_avg = (jc[1] + cpi[1]) / 2
    
    # Formules
    ttr_a = ttr_med_avg * 0.23 if ttr_med_avg > 1200 else ttr_med_avg
    ttr_b = lat_med_avg * 1.5
    
    print(f"\n📊 Formule A (avec correction) : {ttr_a/60:.1f} minutes")
    print(f"   Écart : {abs(ttr_a/60 - 5):.1f} minutes")
    print(f"   Précision : {(1 - abs(ttr_a/60 - 5)/5)*100:.1f}%")
    
    print(f"\n📊 Formule B (latency × 1.5) : {ttr_b/60:.1f} minutes")
    print(f"   Écart : {abs(ttr_b/60 - 5):.1f} minutes")
    print(f"   Précision : {(1 - abs(ttr_b/60 - 5)/5)*100:.1f}%")
    
    # Meilleure formule
    if abs(ttr_a/60 - 5) < abs(ttr_b/60 - 5):
        print(f"\n✅ MEILLEURE : Formule A")
        print(f"   MAE : {abs(ttr_a/60 - 5):.1f} minutes")
    else:
        print(f"\n✅ MEILLEURE : Formule B")
        print(f"   MAE : {abs(ttr_b/60 - 5):.1f} minutes")

print("\n" + "=" * 80)
print("✅ VALIDATION TTR TERMINÉE")
print("=" * 80)

conn.close()
