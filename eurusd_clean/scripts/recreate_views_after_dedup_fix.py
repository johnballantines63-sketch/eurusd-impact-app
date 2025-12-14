#!/usr/bin/env python3
"""
Script pour recréer les vues après le fix de déduplication.
Attend que le lock sur la base soit libéré avant de procéder.
"""
import sys
from pathlib import Path
import time
import duckdb

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

DB_PATH = Path(__file__).parent.parent / "data" / "warehouse.duckdb"

def wait_for_lock(max_wait=60, check_interval=2):
    """Attend que le lock soit libéré."""
    print(f"⏳ Attente de libération du lock (max {max_wait}s)...")
    start = time.time()
    while time.time() - start < max_wait:
        try:
            conn = duckdb.connect(str(DB_PATH), read_only=False)
            conn.close()
            print("✅ Lock libéré")
            return True
        except Exception as e:
            if "lock" in str(e).lower():
                time.sleep(check_interval)
                print(".", end="", flush=True)
            else:
                raise
    print("\n❌ Timeout: le lock n'a pas été libéré")
    return False

def main():
    if not wait_for_lock():
        print("❌ Impossible de continuer: base verrouillée")
        return 1
    
    print("\n" + "=" * 80)
    print("RECRÉATION DES VUES APRÈS FIX DÉDUPLICATION")
    print("=" * 80)
    
    # 1. Recréer event_priors_rolling_v1
    print("\n1️⃣ Recréation de event_priors_rolling_v1...")
    try:
        from scripts.create_event_priors_rolling_v1 import main as create_priors
        create_priors()
        print("✅ event_priors_rolling_v1 recréée")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return 1
    
    # 2. Recréer events_with_pred_score_v1
    print("\n2️⃣ Recréation de events_with_pred_score_v1...")
    try:
        from scripts.create_events_with_pred_score_v1_view import main as create_pred_score
        create_pred_score()
        print("✅ events_with_pred_score_v1 recréée")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return 1
    
    # 3. Recréer daily_pred_score_robust_v1
    print("\n3️⃣ Recréation de daily_pred_score_robust_v1...")
    try:
        from scripts.create_daily_pred_score_robust_v1_view import main as create_daily_robust
        create_daily_robust()
        print("✅ daily_pred_score_robust_v1 recréée")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return 1
    
    # 4. Vérification finale
    print("\n" + "=" * 80)
    print("VÉRIFICATION FINALE")
    print("=" * 80)
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    for v in ["events_with_ts_local_v1", "event_priors_rolling_v1", 
              "events_with_pred_score_v1", "daily_pred_score_robust_v1"]:
        n = conn.execute(f"SELECT COUNT(*) FROM {v}").fetchone()[0]
        print(f"{v}: {n}")
    
    # Vérifier les duplications
    print("\nVérification duplications event_priors_rolling_v1:")
    df = conn.execute("""
        SELECT
          ts_local, country, event_key,
          COUNT(*) AS n
        FROM event_priors_rolling_v1
        GROUP BY 1,2,3
        HAVING COUNT(*) > 1
        ORDER BY n DESC
        LIMIT 5
    """).df()
    
    if df.empty:
        print("  ✅ Aucune duplication")
    else:
        print("  ⚠️ Duplications restantes:")
        print(df.to_string(index=False))
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ TERMINÉ")
    print("=" * 80)
    return 0

if __name__ == "__main__":
    sys.exit(main())
