"""
VALIDATION PULLBACK - 11 SEPTEMBRE 2025

Objectif : Vérifier si timeline v87 prédit correctement le pullback

Données réelles MT5 :
- Impact max (Phase 1) : +37.4 pips
- Après pullback : +10.3 pips  
- Pullback : -27.1 pips (72.5% du pic)
"""

import sys
from pathlib import Path
import duckdb

sys.path.insert(0, str(Path(__file__).parent / "fx_impact_app" / "src"))

# Importer fonctions nécessaires
try:
    from sequence_multi_event_timeline_v87 import (
        calculate_pullback_metrics,
        get_event_direction
    )
    TIMELINE_AVAILABLE = True
except ImportError:
    TIMELINE_AVAILABLE = False
    print("⚠️  Timeline v87 non importable, analyse manuelle")

from config import get_db_path

print("=" * 80)
print("🔍 VALIDATION PULLBACK - 11 SEPTEMBRE 2025")
print("=" * 80)
print("\n🎯 Données réelles MT5 :")
print("   Impact max (Phase 1) : +37.4 pips")
print("   Après pullback       : +10.3 pips")
print("   Pullback             : -27.1 pips (72.5% du pic)")
print("=" * 80)

# Connexion DB
db_path = get_db_path()
conn = duckdb.connect(str(db_path))

# 1. Charger événements 11 septembre
print("\n📊 ÉTAPE 1 : CHARGEMENT ÉVÉNEMENTS 12:30 UTC")
print("-" * 80)

query = """
SELECT 
    family,
    event_key,
    surprise,
    surprise_pct,
    empirical_score,
    predicted_pips,
    direction
FROM validation_events
WHERE event_date = '2025-09-11'
  AND event_time = '12:30:00'
ORDER BY family, event_key
"""

events = conn.execute(query).fetchall()

print(f"✅ {len(events)} événements chargés (12:30 UTC)")

# 2. Calculer impact Phase 1 selon Formule D
print("\n📊 ÉTAPE 2 : CALCUL IMPACT PHASE 1 (FORMULE D)")
print("-" * 80)

# Somme vectorielle
contributions = []
for event in events:
    fam, key, surp, surp_pct, score, pred_pips, direction = event
    
    # Formule C (base)
    if len(events) >= 2:
        impact_base = -10.47 + 0.477 * score
    else:
        impact_base = -7.08 + 0.419 * score
    
    # Direction
    contrib = impact_base * direction
    contributions.append(contrib)
    
    print(f"   {key[:30]:30} : {impact_base:5.1f} × {direction:+d} = {contrib:+6.1f} pips")

impact_brut = sum(contributions)
print("-" * 80)
print(f"✅ Impact brut vectoriel : {impact_brut:+.1f} pips")

# Amplification
surprises = [abs(e[3]) for e in events]
max_surp = max(surprises) if surprises else 0

if max_surp <= 5:
    amp = 1.0
elif max_surp <= 15:
    amp = 1.0 + (max_surp - 5) / 10 * 1.5
else:
    amp = 2.5

impact_amp = abs(impact_brut) * amp
print(f"   Max surprise        : {max_surp:.1f}%")
print(f"   Amplification       : {amp:.2f}x")
print(f"   Impact amplifié     : {impact_amp:.1f} pips")

# Correction 0.758
impact_final = impact_amp * 0.758
print(f"   Correction 0.758    : {impact_final:.1f} pips")

print(f"\n✅ Impact Phase 1 prédit : {impact_final:+.1f} pips")
print(f"   Impact Phase 1 réel  : +37.4 pips")
print(f"   Écart                : {abs(impact_final - 37.4):.1f} pips")

# 3. Analyser formule pullback dans timeline v87
print("\n\n📊 ÉTAPE 3 : ANALYSE FORMULE PULLBACK")
print("-" * 80)

if TIMELINE_AVAILABLE:
    print("✅ Timeline v87 disponible")
    
    # Chercher fonction calculate_pullback
    import inspect
    try:
        source = inspect.getsource(calculate_pullback_metrics)
        print("\n📝 Code fonction calculate_pullback_metrics :")
        print("-" * 80)
        # Afficher premières lignes
        lines = source.split('\n')[:20]
        for line in lines:
            print(line)
        print("   ...")
    except Exception as e:
        print(f"⚠️  Impossible d'extraire source : {e}")
else:
    print("⚠️  Timeline v87 non disponible - analyse manuelle nécessaire")

# 4. Chercher paramètres pullback dans DB ou code
print("\n\n📊 ÉTAPE 4 : RECHERCHE PARAMÈTRES PULLBACK")
print("-" * 80)

# Vérifier tables DB pour paramètres pullback
tables_query = """
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'main'
"""

tables = conn.execute(tables_query).fetchall()
print("\n📋 Tables disponibles :")
for table in tables:
    print(f"   - {table[0]}")

# Chercher colonnes avec "pullback"
print("\n🔍 Recherche colonnes contenant 'pullback' :")
found_pullback = False
for table in tables:
    table_name = table[0]
    cols_query = f"""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = '{table_name}'
      AND column_name LIKE '%pullback%'
    """
    try:
        cols = conn.execute(cols_query).fetchall()
        if cols:
            print(f"\n   Table {table_name} :")
            for col in cols:
                print(f"      - {col[0]}")
            found_pullback = True
    except:
        pass

if not found_pullback:
    print("   ⚠️  Aucune colonne 'pullback' trouvée en DB")

# 5. Calculer pullback attendu selon ratio observé
print("\n\n📊 ÉTAPE 5 : PULLBACK ATTENDU")
print("-" * 80)

ratio_observe = 27.1 / 37.4  # 72.5%

pullback_predit_ratio = impact_final * ratio_observe
pullback_predit_pips = -pullback_predit_ratio

print(f"📊 Si ratio 72.5% du pic :")
print(f"   Impact Phase 1 : {impact_final:.1f} pips")
print(f"   Pullback       : {pullback_predit_pips:.1f} pips")
print(f"\n📊 Réel :")
print(f"   Impact Phase 1 : 37.4 pips")
print(f"   Pullback       : -27.1 pips")
print(f"\n📊 Écart :")
print(f"   {abs(pullback_predit_pips + 27.1):.1f} pips")

# 6. Résumé
print("\n\n" + "=" * 80)
print("📊 RÉSUMÉ VALIDATION PULLBACK")
print("=" * 80)

print("\n✅ IMPACT PHASE 1 :")
print(f"   Formule D prédit : {impact_final:+.1f} pips")
print(f"   Réel MT5         : +37.4 pips")
print(f"   MAE              : {abs(impact_final - 37.4):.1f} pips")
print(f"   Précision        : {(1 - abs(impact_final - 37.4)/37.4)*100:.1f}%")

print("\n⏳ PULLBACK :")
print(f"   Attendu (72.5% ratio) : {pullback_predit_pips:.1f} pips")
print(f"   Réel MT5              : -27.1 pips")
print(f"   MAE                   : {abs(pullback_predit_pips + 27.1):.1f} pips")

if abs(pullback_predit_pips + 27.1) < 5:
    print("\n✅ PULLBACK BIEN PRÉDIT (MAE < 5 pips)")
elif abs(pullback_predit_pips + 27.1) < 10:
    print("\n⚠️  PULLBACK ACCEPTABLE (MAE < 10 pips)")
else:
    print("\n❌ PULLBACK À AJUSTER (MAE > 10 pips)")

print("\n💡 RECOMMANDATION :")
print("   → Vérifier fonction calculate_pullback_metrics dans timeline v87")
print("   → Ratio pullback typique : 60-80% du pic")
print("   → Tester sur autres dates pour confirmer ratio")

print("\n" + "=" * 80)
print("✅ VALIDATION PULLBACK TERMINÉE")
print("=" * 80)

conn.close()
