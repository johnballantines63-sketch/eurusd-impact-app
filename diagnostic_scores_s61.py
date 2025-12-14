"""
DIAGNOSTIC PROBLÈME #7 - Double Ajustement Score
Session 61 - Comparaison test_4_formules vs planificateur

OBJECTIF:
Comprendre POURQUOI test_4_formules donne 57 pips correct
et POURQUOI planificateur donne 152 pips incorrect
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "fx_impact_app"))
sys.path.insert(0, str(project_root / "fx_impact_app" / "src"))

import duckdb
from fx_impact_app.src.config import get_db_path
from fx_impact_app.src.formulas_validated import calculate_adjusted_empirical_score

def inspect_scores():
    """Compare les scores entre validation_events et calcul ajusté"""
    
    print("\n" + "="*80)
    print("🔍 DIAGNOSTIC PROBLÈME #7 - DOUBLE AJUSTEMENT SCORE")
    print("="*80 + "\n")
    
    db_path = get_db_path()
    conn = duckdb.connect(str(db_path))
    
    # Charger événements
    query = """
    SELECT 
        family,
        surprise,
        surprise_pct,
        empirical_score,
        event_datetime
    FROM validation_events
    WHERE event_date = '2025-09-11'
    ORDER BY event_datetime, family
    """
    
    events = conn.execute(query).fetchall()
    conn.close()
    
    print("📊 ÉVÉNEMENTS 11 SEPTEMBRE 2025")
    print("-"*80)
    print(f"{'Family':<20} {'Surp%':>8} {'Score DB':>12} {'Score Ajusté':>15} {'Différence':>12}")
    print("-"*80)
    
    total_score_db = 0
    total_score_adjusted = 0
    
    for row in events:
        family, surprise, surprise_pct, score_db, dt = row
        
        # Calculer score ajusté
        score_adjusted = calculate_adjusted_empirical_score(score_db, surprise_pct)
        diff = score_adjusted - score_db
        
        total_score_db += score_db
        total_score_adjusted += score_adjusted
        
        print(f"{family:<20} {surprise_pct:>7.1f}% {score_db:>12.1f} {score_adjusted:>15.1f} {diff:>+12.1f}")
    
    print("-"*80)
    print(f"{'TOTAL':<20} {'':<8} {total_score_db:>12.1f} {total_score_adjusted:>15.1f} {total_score_adjusted - total_score_db:>+12.1f}")
    print("="*80)
    
    avg_db = total_score_db / len(events)
    avg_adjusted = total_score_adjusted / len(events)
    
    print(f"\n📊 ANALYSE:")
    print(f"   Nombre événements: {len(events)}")
    print(f"   Score moyen DB: {avg_db:.1f}")
    print(f"   Score moyen ajusté: {avg_adjusted:.1f}")
    print(f"   Facteur amplification moyen: {avg_adjusted/avg_db:.2f}x")
    
    # Diagnostic
    print(f"\n🔍 DIAGNOSTIC:")
    
    if avg_db > 60:
        print(f"   ⚠️  SCORES DB SEMBLENT DÉJÀ AJUSTÉS ({avg_db:.1f} >> 44.8)")
        print(f"   ⚠️  validation_events contient scores pré-ajustés")
        print(f"   ⚠️  Appeler calculate_adjusted_empirical_score() = DOUBLE AJUSTEMENT")
        print(f"   ✅ SOLUTION: Utiliser scores DB TEL QUEL (comme test_4_formules)")
    else:
        print(f"   ✅ SCORES DB SEMBLENT BRUTS ({avg_db:.1f} ≈ 44.8)")
        print(f"   ✅ validation_events contient scores bruts")
        print(f"   ✅ Appeler calculate_adjusted_empirical_score() = CORRECT")
        print(f"   ⚠️  MAIS ALORS pourquoi test_4_formules fonctionne sans ajustement ?")
    
    print("\n" + "="*80)
    print("📚 PROCHAINES ÉTAPES:")
    print("="*80)
    print("1. Vérifier quelle table utilise VRAIMENT test_4_formules")
    print("2. Comparer avec table event_families (scores de base)")
    print("3. Identifier si validation_events = scores bruts ou ajustés")
    print("="*80 + "\n")

if __name__ == "__main__":
    inspect_scores()
