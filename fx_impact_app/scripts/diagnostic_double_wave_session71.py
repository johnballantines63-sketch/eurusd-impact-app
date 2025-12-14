"""
DIAGNOSTIC DETECTION DOUBLE WAVE - Session 71
==============================================

Teste pourquoi Double Wave est détecté à tort
"""

import sys
from pathlib import Path
from datetime import datetime

file_dir = Path(__file__).resolve().parent
fx_impact_app_dir = file_dir.parent
src_path = fx_impact_app_dir / "src"
sys.path.insert(0, str(src_path))

from config import get_db_path
import duckdb

def test_date(target_date: str):
    """Teste une date"""
    print(f"\n{'='*70}")
    print(f"DIAGNOSTIC DATE : {target_date}")
    print('='*70)
    
    db_path = get_db_path()
    conn = duckdb.connect(str(db_path), read_only=True)
    
    query = """
    SELECT 
        e.event_key,
        e.event_title as label,
        e.ts_utc,
        e.actual,
        e.estimate,
        e.importance_n,
        ef.family,
        ef.empirical_score
    FROM events e
    LEFT JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
    WHERE DATE(e.ts_utc) = ?
        AND e.country = 'US'
        AND ef.empirical_score IS NOT NULL
        AND ef.empirical_score > 40
    ORDER BY e.ts_utc
    """
    
    df = conn.execute(query, [target_date]).df()
    conn.close()
    
    print(f"\n✅ {len(df)} événements HIGH trouvés\n")
    
    if df.empty:
        print("Aucun événement HIGH")
        return
    
    # Afficher détails
    for idx, row in df.iterrows():
        label = row['label'] if row['label'] else f"[{row['family']}]"
        score = row['empirical_score']
        imp = row['importance_n']
        
        # Calculer surprise
        if row['actual'] and row['estimate'] and row['estimate'] != 0:
            surprise = abs((row['actual'] - row['estimate']) / row['estimate']) * 100
        else:
            surprise = 0
        
        print(f"{idx+1}. {label:<40} | Score: {score:.1f} | Imp: {imp} | Surprise: {surprise:.1f}%")
    
    # Calculs détection
    print(f"\n{'='*70}")
    print("CALCULS DÉTECTION")
    print('='*70)
    
    # Surprise max
    surprises = []
    for _, row in df.iterrows():
        if row['actual'] and row['estimate'] and row['estimate'] != 0:
            surprise = abs((row['actual'] - row['estimate']) / row['estimate']) * 100
            surprises.append(surprise)
    
    max_surprise = max(surprises) if surprises else 0
    cluster_size = len(df)
    
    # Importance HIGH ?
    has_high = any(df['importance_n'].fillna(0) == 3)
    
    print(f"\nSurprise max : {max_surprise:.1f}%")
    print(f"Cluster size : {cluster_size}")
    print(f"Importance HIGH (3) : {has_high}")
    
    # Conditions Double Wave
    print(f"\n{'='*70}")
    print("CONDITIONS DOUBLE WAVE")
    print('='*70)
    
    cond_surprise = max_surprise > 20.0
    cond_cluster = cluster_size >= 5
    cond_importance = has_high
    
    print(f"\n1. Surprise > 20% : {cond_surprise} ({'✅' if cond_surprise else '❌'})")
    print(f"2. Cluster ≥ 5    : {cond_cluster} ({'✅' if cond_cluster else '❌'})")
    print(f"3. Importance HIGH: {cond_importance} ({'✅' if cond_importance else '❌'})")
    
    is_double_wave = cond_surprise and cond_cluster and cond_importance
    
    print(f"\n🔴 Double Wave détecté : {is_double_wave}")
    
    # Conditions Single Wave Fort
    print(f"\n{'='*70}")
    print("CONDITIONS SINGLE WAVE FORT")
    print('='*70)
    
    cond_surprise_swf = max_surprise > 15.0
    cond_cluster_swf = cluster_size >= 3
    
    print(f"\n1. Surprise > 15% : {cond_surprise_swf} ({'✅' if cond_surprise_swf else '❌'})")
    print(f"2. Cluster ≥ 3    : {cond_cluster_swf} ({'✅' if cond_cluster_swf else '❌'})")
    
    is_swf = cond_surprise_swf and cond_cluster_swf
    
    print(f"\n🟢 Single Wave Fort détecté : {is_swf}")
    
    # Conclusion
    print(f"\n{'='*70}")
    print("TYPE MOUVEMENT ATTENDU")
    print('='*70)
    
    if is_double_wave:
        print("\n🔴 DOUBLE WAVE MOMENTUM")
    elif is_swf:
        print("\n🟢 SINGLE WAVE FORT")
    else:
        print("\n⚪ SINGLE WAVE STANDARD")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("DIAGNOSTIC DETECTION DOUBLE WAVE - SESSION 71")
    print("="*70)
    
    # Test 2025-02-12
    test_date('2025-02-12')
    
    # Test 2025-08-01
    test_date('2025-08-01')
    
    print("\n" + "="*70)
    print("FIN DIAGNOSTIC")
    print("="*70)
