#!/usr/bin/env python3
"""
VERSION FINALE CORRIGÉE : Pré-calcul via event_key matching
============================================================

Comprend maintenant que event_families mappe event_key → family
et non family → stats globales
"""

import sys
from pathlib import Path
import duckdb
import re

# Setup paths
project_root = Path(__file__).parent
src_path = project_root / "fx_impact_app" / "src"
sys.path.insert(0, str(src_path))

from config import get_db_path
from event_families import FAMILY_PATTERNS
from latency_analyzer import LatencyAnalyzer
from forecaster_mvp import ForecastEngine

def find_event_keys_for_family(conn, pattern):
    """
    Trouve tous les event_keys qui matchent le pattern de la famille
    
    Returns:
        list of (event_key, country) tuples
    """
    # Récupérer tous les event_keys distincts
    query = """
    SELECT DISTINCT event_key, country
    FROM event_families
    """
    
    all_events = conn.execute(query).fetchall()
    
    # Filtrer ceux qui matchent le pattern
    clean_pattern = pattern.replace('(?i)', '')
    matched = []
    
    for event_key, country in all_events:
        if re.search(clean_pattern, event_key, re.IGNORECASE):
            matched.append((event_key, country))
    
    return matched


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
        print(f"\n      ❌ Erreur calcul: {e}")
        return None


def update_event_keys(conn, event_keys, stats, family_name):
    """
    Met à jour tous les event_keys avec les stats
    
    Args:
        event_keys: list of (event_key, country) tuples
        stats: dict avec les stats calculées
        family_name: nom de la famille (pour info)
    """
    update_query = """
    UPDATE event_families
    SET 
        family = ?,
        latency_median = ?,
        latency_p20 = ?,
        latency_p80 = ?,
        ttr_median = ?,
        ttr_p20 = ?,
        ttr_p80 = ?,
        mfe_p80 = ?,
        n_events_latency = ?
    WHERE event_key = ? AND country = ?
    """
    
    updated_count = 0
    
    for event_key, country in event_keys:
        params = [
            family_name,  # Mettre à jour le nom de famille aussi
            stats['latency_median'],
            stats['latency_p20'],
            stats['latency_p80'],
            stats['ttr_median'],
            stats['ttr_p20'],
            stats['ttr_p80'],
            stats['mfe_p80'],
            stats['n_events_latency'],
            event_key,
            country
        ]
        
        try:
            conn.execute(update_query, params)
            updated_count += 1
        except Exception as e:
            print(f"\n      ⚠️  Erreur UPDATE {event_key}: {e}")
    
    # Commit après tous les UPDATEs de cette famille
    conn.commit()
    
    return updated_count


def main():
    print("=" * 80)
    print("PRÉ-CALCUL STATS (VERSION FINALE - event_key mapping)")
    print("=" * 80)
    print()
    
    db_path = get_db_path()
    print(f"📂 DB: {db_path}")
    print(f"📊 Familles à traiter: {len(FAMILY_PATTERNS)}")
    print()
    print("🔍 Méthode : Trouve event_keys via pattern → UPDATE ces lignes")
    print()
    
    conn = duckdb.connect(db_path)  # Mode READ-WRITE
    
    total = len(FAMILY_PATTERNS)
    success = 0
    skipped = 0
    total_rows_updated = 0
    
    print("-" * 80)
    print()
    
    for idx, (family_name, pattern) in enumerate(FAMILY_PATTERNS.items(), 1):
        print(f"[{idx}/{total}] 🔄 {family_name}...", end=" ", flush=True)
        
        # 1. Trouver event_keys qui matchent le pattern
        event_keys = find_event_keys_for_family(conn, pattern)
        
        if not event_keys:
            print(f"⚠️  SKIP (aucun event_key ne matche le pattern)")
            skipped += 1
            continue
        
        # 2. Calculer stats
        stats = precompute_family_stats(family_name, pattern, db_path)
        
        if stats is None:
            print(f"⚠️  SKIP (pas assez de données, {len(event_keys)} event_keys trouvés)")
            skipped += 1
            continue
        
        # 3. UPDATE toutes les lignes matchées
        rows_updated = update_event_keys(conn, event_keys, stats, family_name)
        total_rows_updated += rows_updated
        
        print(f"✅ OK ({rows_updated} lignes, "
              f"n={stats['n_events_latency']}, "
              f"lat={stats['latency_median']:.1f}min, "
              f"mfe={stats['mfe_p80']:.1f}pips)")
        success += 1
    
    conn.close()
    
    # Résumé
    print()
    print("=" * 80)
    print("RÉSUMÉ")
    print("=" * 80)
    print(f"✅ Familles réussies  : {success}/{total}")
    print(f"⚠️  Familles ignorées  : {skipped}/{total}")
    print(f"📝 Lignes DB mises à jour : {total_rows_updated}")
    print()
    
    if success > 0:
        print("🎉 PRÉ-CALCUL TERMINÉ !")
        print()
        print("📋 Vérification :")
        print("   python3 check_precomputed_families_status.py")
        print()
        print("💡 Redémarrez Streamlit pour voir les changements")
    else:
        print("⚠️  Aucune famille n'a pu être calculée")
        print()
        print("💡 Vérifiez :")
        print("   - Que la DB contient des données historiques")
        print("   - Que les patterns dans FAMILY_PATTERNS sont corrects")
    
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
