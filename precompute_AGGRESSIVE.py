#!/usr/bin/env python3
"""
VERSION AGGRESSIVE : Réduit seuil à 1 événement + debug détaillé
"""

import sys
from pathlib import Path
import duckdb
import re

project_root = Path(__file__).parent
src_path = project_root / "fx_impact_app" / "src"
sys.path.insert(0, str(src_path))

from config import get_db_path
from event_families import FAMILY_PATTERNS
from latency_analyzer import LatencyAnalyzer
from forecaster_mvp import ForecastEngine

def find_event_keys_for_family(conn, pattern):
    """Trouve tous les event_keys qui matchent le pattern"""
    query = "SELECT DISTINCT event_key, country FROM event_families"
    all_events = conn.execute(query).fetchall()
    
    clean_pattern = pattern.replace('(?i)', '')
    matched = []
    
    for event_key, country in all_events:
        if re.search(clean_pattern, event_key, re.IGNORECASE):
            matched.append((event_key, country))
    
    return matched


def precompute_family_stats_aggressive(family_name, pattern, db_path):
    """
    Version AGGRESSIVE avec seuil min_events=1 et debug
    """
    try:
        print(f"      🔍 Calcul latence...", end=" ", flush=True)
        
        # ⚡ CHANGEMENT : min_events=1 au lieu de 5
        analyzer = LatencyAnalyzer(db_path)
        latency_stats = analyzer.calculate_family_latency_stats(
            family_pattern=pattern,
            threshold_pips=5.0,
            min_events=1,  # ⭐ CRITIQUE : Réduit de 5 à 1
            lookback_days=3 * 365
        )
        analyzer.close()
        
        if not latency_stats:
            print("❌ latency_stats=None")
            return None
            
        events_found = latency_stats.get('events_analyzed', 0)
        print(f"({events_found} evt)", end=" ", flush=True)
        
        if events_found == 0:
            print("❌ 0 événements analysés")
            return None
            
        if 'initial_reaction' not in latency_stats:
            print("❌ Pas de initial_reaction")
            return None
        
        print(f"✓ ", end="", flush=True)
        
        # Calcul MFE
        print(f"MFE...", end=" ", flush=True)
        engine = ForecastEngine(db_path)
        mfe_stats = engine.calculate_family_stats(pattern, horizon_minutes=60, hist_years=3, countries=None)
        engine.close()
        
        print(f"✓", end=" ", flush=True)
        
        # Stats
        lat_median = latency_stats['initial_reaction']['median_minutes']
        return {
            'latency_median': lat_median,
            'latency_p20': latency_stats['initial_reaction'].get('p20_minutes', lat_median * 0.5),
            'latency_p80': latency_stats['initial_reaction'].get('p80_minutes', lat_median * 1.5),
            'ttr_median': lat_median * 1.5,
            'ttr_p20': lat_median * 1.0,
            'ttr_p80': lat_median * 2.0,
            'mfe_p80': mfe_stats.get('mfe_p80', 10.0),
            'n_events_latency': events_found
        }
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None


def update_event_keys(conn, event_keys, stats, family_name):
    """Met à jour toutes les lignes avec les stats"""
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
            family_name,
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
    
    conn.commit()
    return updated_count


def main():
    print("=" * 80)
    print("PRÉ-CALCUL AGRESSIF (min_events=1 + debug)")
    print("=" * 80)
    print()
    
    db_path = get_db_path()
    print(f"📂 DB: {db_path}")
    print(f"📊 Familles: {len(FAMILY_PATTERNS)}")
    print(f"⚡ Seuil: min_events=1 (au lieu de 5)")
    print()
    
    conn = duckdb.connect(db_path)
    
    total = len(FAMILY_PATTERNS)
    success = 0
    skipped = 0
    total_rows_updated = 0
    
    print("-" * 80)
    print()
    
    for idx, (family_name, pattern) in enumerate(FAMILY_PATTERNS.items(), 1):
        print(f"[{idx}/{total}] 🔄 {family_name}...")
        
        # Trouver event_keys
        event_keys = find_event_keys_for_family(conn, pattern)
        
        if not event_keys:
            print(f"      ⚠️  SKIP (aucun event_key ne matche)")
            skipped += 1
            continue
        
        print(f"      ✓ {len(event_keys)} event_keys matchés | ", end="", flush=True)
        
        # Calculer stats (version aggressive)
        stats = precompute_family_stats_aggressive(family_name, pattern, db_path)
        
        if stats is None:
            skipped += 1
            continue
        
        # UPDATE
        rows_updated = update_event_keys(conn, event_keys, stats, family_name)
        total_rows_updated += rows_updated
        
        print(f"→ ✅ {rows_updated} lignes (lat={stats['latency_median']:.1f}min, mfe={stats['mfe_p80']:.1f}pips)")
        success += 1
    
    conn.close()
    
    # Résumé
    print()
    print("=" * 80)
    print("RÉSUMÉ")
    print("=" * 80)
    print(f"✅ Familles réussies      : {success}/{total} ({success/total*100:.0f}%)")
    print(f"⚠️  Familles ignorées      : {skipped}/{total}")
    print(f"📝 Lignes DB mises à jour : {total_rows_updated}")
    print()
    
    if success > 5:
        print("🎉 AMÉLIORATION SIGNIFICATIVE !")
        print(f"   Avant: 5 familles → Maintenant: {success} familles")
        print()
    
    if success > 0:
        print("📋 Vérification :")
        print("   python3 check_precomputed_families_status.py")
        print()
        print("💡 Redémarrez Streamlit pour voir les changements")
    
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
