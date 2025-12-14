"""
RE-CALCUL STATS TTR/LATENCY - Session 52

Objectif : Re-calculer ttr_median et latency_median avec threshold_pips = 2.0

Familles à re-calculer (événements 11 sept) :
- CPI
- Jobless_Claims
- Current_Account
- Interest_Rate_Decision
"""

import sys
from pathlib import Path
import duckdb

sys.path.insert(0, str(Path(__file__).parent / "fx_impact_app" / "src"))

from config import get_db_path
from latency_analyzer import LatencyAnalyzer

print("=" * 80)
print("🔄 RE-CALCUL STATS TTR/LATENCY avec threshold_pips = 2.0")
print("=" * 80)

# Connexion DB
db_path = get_db_path()
conn = duckdb.connect(str(db_path))

# Familles à re-calculer
families_to_recalc = {
    'CPI': 'CPI|Consumer Price',
    'Jobless_Claims': 'Jobless Claims|Initial Claims|Continuing Claims',
    'Current_Account': 'Current Account',
    'Interest_Rate_Decision': 'Interest Rate|ECB|Press Conference'
}

print(f"\n📋 {len(families_to_recalc)} familles à re-calculer")
print("-" * 80)

analyzer = LatencyAnalyzer(str(db_path))

results = {}

for family_name, pattern in families_to_recalc.items():
    print(f"\n🔍 {family_name} (pattern: {pattern[:50]}...)")
    print("-" * 40)
    
    # Calculer nouvelles stats avec threshold_pips = 2.0
    stats = analyzer.calculate_family_latency_stats(
        family_pattern=pattern,
        threshold_pips=2.0,  # ✅ NOUVEAU SEUIL
        min_events=5,
        lookback_days=365
    )
    
    if "error" in stats:
        print(f"   ❌ Erreur : {stats['error']}")
        continue
    
    # Extraire métriques clés
    events_analyzed = stats.get('events_analyzed', 0)
    events_with_reaction = stats.get('events_with_reaction', 0)
    
    initial_reaction = stats.get('initial_reaction', {})
    latency_median = initial_reaction.get('median_minutes', 0)
    
    peak_timing = stats.get('peak_timing', {})
    ttr_median = peak_timing.get('mean_minutes', 0)  # TTR = pic
    
    print(f"   ✅ Événements analysés : {events_analyzed}")
    print(f"   ✅ Avec réaction : {events_with_reaction}")
    print(f"   📊 Latency médian : {latency_median:.1f} min (vs 0.1 min avant)")
    print(f"   📊 TTR médian : {ttr_median:.1f} min (vs 0.2 min avant)")
    
    results[family_name] = {
        'latency_median': latency_median * 60,  # Convertir en secondes
        'ttr_median': ttr_median * 60,
        'events_analyzed': events_analyzed
    }

analyzer.close()

# Mettre à jour event_families
print("\n\n" + "=" * 80)
print("💾 MISE À JOUR event_families EN DB")
print("=" * 80)

for family_name, data in results.items():
    latency_sec = data['latency_median']
    ttr_sec = data['ttr_median']
    
    print(f"\n🔄 {family_name}")
    print(f"   Latency : {latency_sec:.1f} sec ({latency_sec/60:.1f} min)")
    print(f"   TTR     : {ttr_sec:.1f} sec ({ttr_sec/60:.1f} min)")
    
    # Vérifier si famille existe
    check_query = f"""
    SELECT COUNT(*) FROM event_families WHERE family = '{family_name}'
    """
    count = conn.execute(check_query).fetchone()[0]
    
    if count > 0:
        # Update
        update_query = f"""
        UPDATE event_families
        SET latency_median = {latency_sec},
            ttr_median = {ttr_sec}
        WHERE family = '{family_name}'
        """
        conn.execute(update_query)
        print(f"   ✅ Mise à jour : {count} lignes")
    else:
        print(f"   ⚠️  Famille non trouvée en DB - skip")

# Vérifier les nouvelles valeurs
print("\n\n" + "=" * 80)
print("✅ VÉRIFICATION VALEURS MISES À JOUR")
print("=" * 80)

for family_name in results.keys():
    query = f"""
    SELECT family, latency_median, ttr_median
    FROM event_families
    WHERE family = '{family_name}'
    LIMIT 1
    """
    
    result = conn.execute(query).fetchone()
    
    if result:
        fam, lat, ttr = result
        print(f"\n{fam}")
        print(f"   Latency : {lat:.1f} sec ({lat/60:.1f} min)")
        print(f"   TTR     : {ttr:.1f} sec ({ttr/60:.1f} min)")

conn.close()

print("\n\n" + "=" * 80)
print("📊 RÉSUMÉ RE-CALCUL")
print("=" * 80)

print(f"\n✅ Familles re-calculées : {len(results)}")
print(f"✅ Stats mises à jour en DB")
print(f"\n💡 Prochaine étape : Re-tester TTR avec validate_ttr_11sept_FIXED.py")

print("\n" + "=" * 80)
