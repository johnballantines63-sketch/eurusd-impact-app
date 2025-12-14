"""
DIAGNOSTIC : Comparer scores validation_events vs event_families

Objectif : Comprendre si validation_events contient scores bruts ou ajustés
"""
import sys
from pathlib import Path
import duckdb

sys.path.insert(0, str(Path(__file__).parent / "fx_impact_app" / "src"))
from config import get_db_path

print("=" * 80)
print("🔍 DIAGNOSTIC SCORES - validation_events vs event_families")
print("=" * 80)

db_path = get_db_path()
conn = duckdb.connect(str(db_path))

# 1. Scores dans validation_events
print("\n📊 SCORES DANS validation_events (11 sept):")
print("-" * 80)

query_val = """
SELECT 
    family,
    surprise_pct,
    empirical_score
FROM validation_events
WHERE event_date = '2025-09-11'
ORDER BY family
"""

results_val = conn.execute(query_val).fetchall()

scores_val = {}
for row in results_val:
    family, surprise, score = row
    surprise = surprise if surprise is not None else 0.0
    scores_val[family] = {'surprise': surprise, 'score': score}
    print(f"{family:25s} | Score: {score:6.1f} | Surprise: {surprise:6.1f}%")

# 2. Scores dans event_families (scores "bruts" moyens)
print("\n\n📊 SCORES DANS event_families (moyennes historiques):")
print("-" * 80)

# Récupérer toutes les familles US
families = list(scores_val.keys())
families_str = "', '".join(families)

query_ef = f"""
SELECT 
    family,
    empirical_score
FROM event_families
WHERE country = 'US'
    AND family IN ('{families_str}')
ORDER BY family
"""

results_ef = conn.execute(query_ef).fetchall()

scores_ef = {}
for row in results_ef:
    family, score = row
    scores_ef[family] = score
    print(f"{family:25s} | Score: {score:6.1f}")

# 3. Comparaison
print("\n\n📊 COMPARAISON:")
print("=" * 80)
print(f"{'Famille':<25} | {'Val_Events':>10} | {'Families':>10} | {'Diff':>10} | {'Surprise':>10}")
print("-" * 80)

for family in sorted(scores_val.keys()):
    score_val = scores_val[family]['score']
    surprise = scores_val[family]['surprise']
    score_ef = scores_ef.get(family, 0)
    diff = score_val - score_ef
    
    print(f"{family:<25} | {score_val:>10.1f} | {score_ef:>10.1f} | {diff:>+10.1f} | {surprise:>9.1f}%")

# 4. Statistiques
print("\n\n📊 STATISTIQUES:")
print("=" * 80)

diffs = [scores_val[f]['score'] - scores_ef.get(f, 0) for f in scores_val.keys() if f in scores_ef]
avg_diff = sum(diffs) / len(diffs) if diffs else 0

print(f"\nDifférence moyenne : {avg_diff:+.1f}")
print(f"Différence min : {min(diffs):+.1f}")
print(f"Différence max : {max(diffs):+.1f}")

# Si diffs proche de 0 → scores bruts
# Si diffs significatifs → scores ajustés

if avg_diff < 1:
    print("\n✅ CONCLUSION : Les scores dans validation_events sont BRUTS (identiques à event_families)")
    print("   → test_4_formules fonctionne SANS ajustement car scores bruts")
    print("   → planificateur_11sept_FINAL ajuste à tort → double ajustement !")
else:
    print(f"\n⚠️ CONCLUSION : Les scores dans validation_events sont AJUSTÉS (+{avg_diff:.1f} en moyenne)")
    print("   → test_4_formules fonctionne car scores déjà ajustés")
    print("   → planificateur_11sept_FINAL ré-ajuste → double ajustement !")

conn.close()

print("\n" + "=" * 80)
