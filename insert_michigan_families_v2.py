#!/usr/bin/env python3
"""
Insert familles Michigan avec event_keys EXACTS (pas regex)
"""

import sys
from pathlib import Path
import duckdb

sys.path.insert(0, str(Path(__file__).parent / 'fx_impact_app' / 'src'))
from config import get_db_path
from latency_analyzer import LatencyAnalyzer
from forecaster_mvp import ForecastEngine

# Mapping famille → event_keys exacts
MICHIGAN_MAPPING = {
    'Michigan_Inflation_Expectations': ['michigan inflation expectations'],
    'Michigan_5Y_Inflation_Expectations': ['michigan 5 year inflation expectations'],
    'Michigan_Consumer_Expectations': ['michigan consumer expectations'],
    'Michigan_Current_Conditions': ['michigan current conditions'],
    'Inflation_Expectations': ['inflation expectations'],
    'Baker_Hughes_Rig_Count': [
        'baker hughes oil rig count',
        'baker hughes total rig count',
        'baker hughes total rigs count'
    ],
    'Federal_Budget': ['federal budget'],
    'Monthly_Budget_Statement': ['monthly budget statement']
}

def calculate_stats_exact(event_key):
    """Calcule stats avec event_key exact (pattern simple)"""
    
    analyzer = LatencyAnalyzer(get_db_path())
    
    # Pattern = event_key exact (pas de regex)
    stats = analyzer.calculate_family_latency_stats(
        family_pattern=event_key,  # Pattern exact
        threshold_pips=5.0,
        min_events=3,
        lookback_days=3 * 365
    )
    
    analyzer.close()
    
    if not stats or stats.get('events_analyzed', 0) == 0:
        return None
    
    # MFE avec ForecastEngine
    engine = ForecastEngine(get_db_path())
    mfe_stats = engine.calculate_family_stats(
        event_key,  # Pattern exact
        horizon_minutes=60,
        hist_years=3,
        countries=None
    )
    engine.close()
    
    return {
        'n_events': stats['events_analyzed'],
        'latency_median': stats['initial_reaction']['median_minutes'],
        'latency_p20': stats['initial_reaction'].get('p20_minutes', 
            stats['initial_reaction']['median_minutes'] * 0.5),
        'latency_p80': stats['initial_reaction'].get('p80_minutes',
            stats['initial_reaction']['median_minutes'] * 1.5),
        'ttr_median': stats['initial_reaction']['median_minutes'] * 2,
        'ttr_p20': stats['initial_reaction']['median_minutes'] * 1.5,
        'ttr_p80': stats['initial_reaction']['median_minutes'] * 3,
        'mfe_p80': mfe_stats.get('mfe_p80', 10.0)
    }

def aggregate_stats(stats_list):
    """Agrège stats de plusieurs event_keys"""
    if not stats_list:
        return None
    
    # Moyenne pondérée par n_events
    total_events = sum(s['n_events'] for s in stats_list)
    
    def weighted_avg(field):
        return sum(s[field] * s['n_events'] for s in stats_list) / total_events
    
    return {
        'n_events': total_events,
        'latency_median': weighted_avg('latency_median'),
        'latency_p20': weighted_avg('latency_p20'),
        'latency_p80': weighted_avg('latency_p80'),
        'ttr_median': weighted_avg('ttr_median'),
        'ttr_p20': weighted_avg('ttr_p20'),
        'ttr_p80': weighted_avg('ttr_p80'),
        'mfe_p80': weighted_avg('mfe_p80')
    }

def insert_family(conn, family_name, event_key, stats):
    """INSERT dans event_families"""
    
    # Vérifier si existe
    check = conn.execute(
        "SELECT family FROM event_families WHERE event_key = ?",
        [event_key]
    ).fetchone()
    
    if check:
        print(f"  ⚠️  {event_key} existe déjà")
        return False
    
    query = """
    INSERT INTO event_families (
        event_key, family, country,
        latency_median, latency_p20, latency_p80,
        ttr_median, ttr_p20, ttr_p80,
        mfe_p80, n_events_latency,
        is_tradable, created_at
    ) VALUES (?, ?, 'US', ?, ?, ?, ?, ?, ?, ?, ?, true, CURRENT_TIMESTAMP)
    """
    
    try:
        conn.execute(query, [
            event_key, family_name,
            stats['latency_median'], stats['latency_p20'], stats['latency_p80'],
            stats['ttr_median'], stats['ttr_p20'], stats['ttr_p80'],
            stats['mfe_p80'], stats['n_events']
        ])
        conn.commit()
        return True
    except Exception as e:
        print(f"  ❌ Erreur INSERT: {e}")
        return False

def main():
    print("📊 INSERTION FAMILLES MICHIGAN (patterns exacts)")
    print("=" * 60)
    
    conn = duckdb.connect(get_db_path())
    
    total_inserted = 0
    
    for family, event_keys in MICHIGAN_MAPPING.items():
        print(f"\n📋 {family}")
        print(f"   Event_keys: {', '.join(event_keys)}")
        
        # Calculer stats pour chaque event_key
        all_stats = []
        for ek in event_keys:
            stats = calculate_stats_exact(ek)
            if stats:
                all_stats.append(stats)
                print(f"   ✅ {ek}: {stats['n_events']} events")
        
        if not all_stats:
            print(f"   ❌ Aucune donnée trouvée")
            continue
        
        # Agréger si plusieurs event_keys
        final_stats = aggregate_stats(all_stats)
        
        print(f"   📊 Stats finales:")
        print(f"      Latence: {final_stats['latency_median']:.1f} min")
        print(f"      TTR: {final_stats['ttr_median']:.1f} min")
        print(f"      MFE P80: {final_stats['mfe_p80']:.1f} pips")
        print(f"      Total events: {final_stats['n_events']}")
        
        # Insérer (un par event_key)
        for ek in event_keys:
            if insert_family(conn, family, ek, final_stats):
                total_inserted += 1
                print(f"   ✅ Inséré: {ek}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print(f"✅ {total_inserted} entrées insérées dans event_families")
    print(f"\n💡 Redémarrez Streamlit pour voir les familles !")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
