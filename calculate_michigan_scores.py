#!/usr/bin/env python3
"""
Calculer empirical_score pour familles Michigan
Utilise ScoringEngine avec les stats déjà dans event_families
"""

import sys
from pathlib import Path
import duckdb
import numpy as np

sys.path.insert(0, str(Path(__file__).parent / 'fx_impact_app' / 'src'))
from config import get_db_path
from scoring_engine import ScoringEngine

FAMILIES = [
    'Michigan_Inflation_Expectations',
    'Michigan_5Y_Inflation_Expectations',
    'Michigan_Consumer_Expectations',
    'Michigan_Current_Conditions',
    'Inflation_Expectations',
    'Baker_Hughes_Rig_Count',
    'Monthly_Budget_Statement'
]

def calculate_p_up_p_down(conn, event_key):
    """Calcule p_up et p_down depuis événements historiques"""
    
    query = """
    SELECT 
        actual, previous, estimate
    FROM events
    WHERE event_key = ?
    AND actual IS NOT NULL
    AND previous IS NOT NULL
    LIMIT 100
    """
    
    results = conn.execute(query, [event_key]).fetchall()
    
    if not results or len(results) < 5:
        return 0.5, 0.5  # Default neutre
    
    # Calculer directions
    directions = []
    for actual, previous, estimate in results:
        ref = estimate if estimate is not None else previous
        if actual > ref:
            directions.append('up')
        elif actual < ref:
            directions.append('down')
    
    if not directions:
        return 0.5, 0.5
    
    p_up = sum(1 for d in directions if d == 'up') / len(directions)
    p_down = sum(1 for d in directions if d == 'down') / len(directions)
    
    return p_up, p_down

def main():
    print("📊 CALCUL SCORES EMPIRIQUES MICHIGAN")
    print("=" * 60)
    
    conn = duckdb.connect(get_db_path())
    engine = ScoringEngine()
    
    updated = 0
    
    for family in FAMILIES:
        print(f"\n📋 {family}")
        
        # Lire stats existantes
        result = conn.execute("""
            SELECT event_key, latency_median, ttr_median, mfe_p80, n_events_latency
            FROM event_families
            WHERE family = ?
            LIMIT 1
        """, [family]).fetchone()
        
        if not result:
            print(f"  ⚠️  Pas trouvé dans event_families")
            continue
        
        event_key, latency_median, ttr_median, mfe_p80, n_events = result
        
        # Calculer p_up, p_down
        p_up, p_down = calculate_p_up_p_down(conn, event_key)
        
        # Préparer stats pour ScoringEngine
        stats = {
            'n_events': n_events,
            'mfe_p80': mfe_p80,
            'latency_median': latency_median,
            'ttr_median': ttr_median,
            'p_up': p_up,
            'p_down': p_down
        }
        
        # Calculer score
        score_result = engine.calculate_score(stats, importance=2)
        
        print(f"  📊 Stats:")
        print(f"     MFE P80: {mfe_p80:.1f} pips")
        print(f"     Latence: {latency_median:.1f} min")
        print(f"     TTR: {ttr_median:.1f} min")
        print(f"     P_up: {p_up:.2f} | P_down: {p_down:.2f}")
        print(f"  🎯 Score: {score_result['score']:.1f}/100 ({score_result['grade']})")
        print(f"     Tradability: {score_result['tradability']}")
        
        # UPDATE dans DB
        update_query = """
        UPDATE event_families
        SET empirical_score = ?,
            empirical_impact = ?,
            avg_movement_pips = ?,
            reaction_rate = ?
        WHERE event_key = ?
        """
        
        # Déterminer impact level
        if mfe_p80 >= 25:
            impact_level = 'HIGH'
        elif mfe_p80 >= 15:
            impact_level = 'MEDIUM'
        else:
            impact_level = 'LOW'
        
        conn.execute(update_query, [
            score_result['score'],
            impact_level,
            mfe_p80,
            max(p_up, p_down),
            event_key
        ])
        
        conn.commit()
        updated += 1
        print(f"  ✅ Score mis à jour")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print(f"✅ {updated} scores calculés et mis à jour")
    print(f"\n💡 Rechargez Streamlit (F5) pour voir les scores !")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
