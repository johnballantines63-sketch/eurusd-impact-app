"""
Script d'inspection rapide de validation_events
Pour comprendre quels scores sont stockés (bruts ou ajustés)
"""
import sys
from pathlib import Path

# Ajouter chemins
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "fx_impact_app"))

import duckdb
from fx_impact_app.src.config import get_db_path

def inspect_validation_events():
    """Inspecte les événements du 11 sept dans validation_events"""
    db_path = get_db_path()
    print(f"📂 DB path: {db_path}\n")
    
    conn = duckdb.connect(str(db_path))
    
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
    
    result = conn.execute(query).fetchall()
    conn.close()
    
    print("="*80)
    print("📊 ÉVÉNEMENTS 11 SEPTEMBRE 2025 - TABLE validation_events")
    print("="*80)
    print(f"{'Family':<20} {'Surprise':>10} {'Surp %':>10} {'Score':>10}")
    print("-"*80)
    
    total_score = 0
    for row in result:
        family, surprise, surprise_pct, score, dt = row
        print(f"{family:<20} {surprise:>10.2f} {surprise_pct:>10.1f}% {score:>10.1f}")
        total_score += score
    
    print("-"*80)
    print(f"{'TOTAL':<20} {'':<10} {'':<10} {total_score:>10.1f}")
    print("="*80)
    
    print(f"\n📊 Nombre d'événements: {len(result)}")
    print(f"📊 Score moyen: {total_score/len(result):.1f}")
    
    # Vérifier si scores semblent ajustés
    avg_score = total_score / len(result)
    if avg_score > 60:
        print(f"\n⚠️  SCORES SEMBLENT AJUSTÉS (moyenne {avg_score:.1f} >> 44.8 brut)")
        print("    Les scores dans validation_events ont déjà été ajustés")
    else:
        print(f"\n✅ SCORES SEMBLENT BRUTS (moyenne {avg_score:.1f} ≈ 44.8 attendu)")
        print("    Les scores dans validation_events sont bruts")

if __name__ == "__main__":
    inspect_validation_events()
