#!/usr/bin/env python3
"""
Insert 8 familles Michigan dans event_families avec stats calculées
Utilise LatencyAnalyzer + ForecastEngine (comme Planificateur)
"""

import sys
from pathlib import Path
import duckdb

# Imports
sys.path.insert(0, str(Path(__file__).parent / 'fx_impact_app' / 'src'))
from config import get_db_path
from event_families import FAMILY_PATTERNS
from latency_analyzer import LatencyAnalyzer
from forecaster_mvp import ForecastEngine

MICHIGAN_FAMILIES = [
    'Michigan_Inflation_Expectations',
    'Michigan_5Y_Inflation_Expectations',
    'Michigan_Consumer_Expectations',
    'Michigan_Current_Conditions',
    'Inflation_Expectations',
    'Baker_Hughes_Rig_Count',
    'Federal_Budget',
    'Monthly_Budget_Statement'
]

def calculate_family_stats(family_name, years_back=3):
    """Calcule stats exactement comme predict_impact() du Planificateur"""
    
    pattern = FAMILY_PATTERNS.get(family_name, '')
    if not pattern:
        print(f"  ❌ Pattern non trouvé pour {family_name}")
        return None
    
    try:
        # 1. LatencyAnalyzer pour latences
        analyzer = LatencyAnalyzer(get_db_path())
        latency_stats = analyzer.calculate_family_latency_stats(
            family_pattern=pattern,
            threshold_pips=5.0,
            min_events=5,
            lookback_days=years_back * 365
        )
        analyzer.close()
        
        if not latency_stats or latency_stats.get('events_analyzed', 0) == 0:
            print(f"  ⚠️  Pas de données latence pour {family_name}")
            return None
        
        # 2. ForecastEngine pour MFE
        engine = ForecastEngine(get_db_path())
        mfe_stats = engine.calculate_family_stats(
            pattern,
            horizon_minutes=60,
            hist_years=years_back,
            countries=None
        )
        engine.close()
        
        # 3. Combiner
        stats = {
            'family': family_name,
            'n_events_latency': latency_stats['events_analyzed'],
            'latency_median': latency_stats['initial_reaction']['median_minutes'],
            'latency_p20': latency_stats['initial_reaction'].get('p20_minutes', 
                latency_stats['initial_reaction']['median_minutes'] * 0.5),
            'latency_p80': latency_stats['initial_reaction'].get('p80_minutes', 
                latency_stats['initial_reaction']['median_minutes'] * 1.5),
            'ttr_median': latency_stats['initial_reaction']['median_minutes'] * 2,
            'ttr_p20': latency_stats['initial_reaction']['median_minutes'] * 1.5,
            'ttr_p80': latency_stats['initial_reaction']['median_minutes'] * 3,
            'mfe_p80': mfe_stats.get('mfe_p80', 10.0)
        }
        
        return stats
        
    except Exception as e:
        print(f"  ❌ Erreur {family_name}: {e}")
        return None

def get_event_key_for_family(conn, family_name):
    """Trouve un event_key correspondant au pattern de la famille"""
    pattern = FAMILY_PATTERNS.get(family_name, '')
    if not pattern:
        return None
    
    # Simplifier pattern pour LIKE
    simple_pattern = family_name.lower().replace('_', '%')
    
    query = f"""
    SELECT DISTINCT event_key
    FROM events
    WHERE LOWER(event_key) LIKE '%{simple_pattern}%'
    LIMIT 1
    """
    
    try:
        result = conn.execute(query).fetchone()
        return result[0] if result else None
    except:
        return None

def insert_family_stats(conn, stats):
    """INSERT dans event_families"""
    
    # Trouver event_key correspondant
    event_key = get_event_key_for_family(conn, stats['family'])
    if not event_key:
        print(f"  ⚠️  Event_key non trouvé pour {stats['family']}")
        return False
    
    # Vérifier si existe déjà
    check = conn.execute(
        "SELECT family FROM event_families WHERE family = ?",
        [stats['family']]
    ).fetchone()
    
    if check:
        print(f"  ⚠️  {stats['family']} existe déjà, skip")
        return False
    
    # INSERT
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
            event_key,
            stats['family'],
            stats['latency_median'],
            stats['latency_p20'],
            stats['latency_p80'],
            stats['ttr_median'],
            stats['ttr_p20'],
            stats['ttr_p80'],
            stats['mfe_p80'],
            stats['n_events_latency']
        ])
        conn.commit()
        return True
    except Exception as e:
        print(f"  ❌ Erreur INSERT: {e}")
        return False

def main():
    print("📊 INSERTION FAMILLES MICHIGAN DANS event_families")
    print("=" * 60)
    
    conn = duckdb.connect(get_db_path())
    
    success_count = 0
    skip_count = 0
    
    for family in MICHIGAN_FAMILIES:
        print(f"\n📋 Traitement: {family}")
        
        # Calculer stats
        stats = calculate_family_stats(family, years_back=3)
        
        if stats is None:
            skip_count += 1
            continue
        
        print(f"  ✅ Stats calculées:")
        print(f"     - Latence: {stats['latency_median']:.1f} min")
        print(f"     - TTR: {stats['ttr_median']:.1f} min")
        print(f"     - MFE P80: {stats['mfe_p80']:.1f} pips")
        print(f"     - N events: {stats['n_events_latency']}")
        
        # Insérer
        if insert_family_stats(conn, stats):
            success_count += 1
            print(f"  ✅ Inséré dans event_families")
        else:
            skip_count += 1
    
    conn.close()
    
    print("\n" + "=" * 60)
    print(f"✅ {success_count} familles insérées")
    print(f"⚠️  {skip_count} familles skippées")
    print(f"\n💡 Le Planificateur chargera automatiquement ces familles !")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
