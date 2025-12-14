#!/usr/bin/env python3
"""
VERSION CORRIGÉE : Pré-calcul avec COMMIT explicite
"""

import sys
from pathlib import Path
import duckdb

# Setup paths
project_root = Path(__file__).parent
src_path = project_root / "fx_impact_app" / "src"
sys.path.insert(0, str(src_path))

from config import get_db_path
from event_families import FAMILY_PATTERNS
from latency_analyzer import LatencyAnalyzer
from forecaster_mvp import ForecastEngine

def precompute_family_stats(family_name, pattern, db_path):
    """Calcule stats pour une famille"""
    try:
        # Calcul latence
        analyzer = LatencyAnalyzer(db_path)
        latency_stats = analyzer.calculate_family_latency_stats(
            family_pattern=pattern,
            threshold_pips=5.0,
            min_events=5,
            lookback_days=3 * 365
        )
        analyzer.close()
        
        if not latency_stats or latency_stats.get('events_analyzed', 0) == 0:
            return None
        if 'initial_reaction' not in latency_stats:
            return None
        
        # Calcul MFE
        engine = ForecastEngine(db_path)
        mfe_stats = engine.calculate_family_stats(pattern, horizon_minutes=60, hist_years=3, countries=None)
        engine.close()
        
        # Préparer stats
        lat_median = latency_stats['initial_reaction']['median_minutes']
        return {
            'latency_median': lat_median,
            'latency_p20': latency_stats['initial_reaction'].get('p20_minutes', lat_median * 0.5),
            'latency_p80': latency_stats['initial_reaction'].get('p80_minutes', lat_median * 1.5),
            'ttr_median': lat_median * 1.5,
            'ttr_p20': lat_median * 1.0,
            'ttr_p80': lat_median * 2.0,
            'mfe_p80': mfe_stats.get('mfe_p80', 10.0),
            'n_events_latency': latency_stats['events_analyzed']
        }
    except Exception as e:
        print(f"\n      ❌ Erreur: {e}")
        return None


def main():
    print("=" * 80)
    print("PRÉ-CALCUL STATS (VERSION CORRIGÉE AVEC COMMIT)")
    print("=" * 80)
    print()
    
    db_path = get_db_path()
    print(f"📂 DB: {db_path}")
    print(f"📊 Familles: {len(FAMILY_PATTERNS)}")
    print()
    
    # ⚠️ CORRECTION : Pas de read_only !
    conn = duckdb.connect(db_path)  # Mode READ-WRITE
    
    total = len(FAMILY_PATTERNS)
    success = 0
    skipped = 0
    
    print("-" * 80)
    print()
    
    for idx, (family_name, pattern) in enumerate(FAMILY_PATTERNS.items(), 1):
        print(f"[{idx}/{total}] 🔄 {family_name}...", end=" ", flush=True)
        
        stats = precompute_family_stats(family_name, pattern, db_path)
        
        if stats is None:
            print("⚠️  SKIP")
            skipped += 1
            continue
        
        # UPDATE avec paramètres bindés (sécurisé)
        try:
            update_query = """
            UPDATE event_families
            SET 
                latency_median = ?,
                latency_p20 = ?,
                latency_p80 = ?,
                ttr_median = ?,
                ttr_p20 = ?,
                ttr_p80 = ?,
                mfe_p80 = ?,
                n_events_latency = ?
            WHERE family = ?
            """
            
            params = [
                stats['latency_median'],
                stats['latency_p20'],
                stats['latency_p80'],
                stats['ttr_median'],
                stats['ttr_p20'],
                stats['ttr_p80'],
                stats['mfe_p80'],
                stats['n_events_latency'],
                family_name  # WHERE family = ?
            ]
            
            conn.execute(update_query, params)
            
            # ⭐ CORRECTION : COMMIT explicite !
            conn.commit()
            
            print(f"✅ OK (n={stats['n_events_latency']}, "
                  f"lat={stats['latency_median']:.1f}min, "
                  f"ttr={stats['ttr_median']:.1f}min, "
                  f"mfe={stats['mfe_p80']:.1f}pips)")
            success += 1
            
        except Exception as e:
            print(f"❌ ERREUR UPDATE: {e}")
    
    conn.close()
    
    # Résumé
    print()
    print("=" * 80)
    print("RÉSUMÉ")
    print("=" * 80)
    print(f"✅ Succès   : {success}/{total}")
    print(f"⚠️  Ignorées : {skipped}/{total}")
    print()
    
    if success > 0:
        print("🎉 PRÉ-CALCUL TERMINÉ !")
        print()
        print("📋 Vérification :")
        print("   python3 check_precomputed_families_status.py")
        print()
        print("💡 Redémarrez Streamlit :")
        print("   cd fx_impact_app && streamlit run streamlit_app/Home.py")
    else:
        print("⚠️  Aucune famille calculée")
    
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
