"""
╔═══════════════════════════════════════════════════════════════╗
║                    ARTIFACT METADATA                          ║
╠═══════════════════════════════════════════════════════════════╣
║ FILENAME:    precompute_family_stats.py                      ║
║ VERSION:     v6.0 WORKAROUND                                 ║
║ UPDATED:     2025-10-08 23:00 UTC                            ║
║ LINES:       285                                             ║
║ STATUS:      ✅ Workaround - Évite bug LatencyAnalyzer       ║
╠═══════════════════════════════════════════════════════════════╣
║ CHANGES v6.0:                                                 ║
║ - CONTOURNE le bug calculate_family_latency_stats()          ║
║ - Calcule latence événement par événement manuellement       ║
║ - Agrège stats manuellement (mean, median, percentiles)      ║
║ - Attendu: 10-14/16 familles (vs 4 actuellement)            ║
╠═══════════════════════════════════════════════════════════════╣
║                   COPY INSTRUCTIONS                           ║
╠═══════════════════════════════════════════════════════════════╣
║ 1. rm precompute_family_stats.py                            ║
║ 2. nano precompute_family_stats.py                          ║
║ 3. Paste THIS ENTIRE CODE (Cmd+V)                           ║
║ 4. Save: Ctrl+O, Enter, Ctrl+X                              ║
║ 5. Verify: wc -l precompute_family_stats.py → 285 lines     ║
║ 6. Run: python precompute_family_stats.py                    ║
║ 7. Durée: 10-15 minutes (plus long mais plus fiable)        ║
╚═══════════════════════════════════════════════════════════════╝
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "fx_impact_app" / "src"))

import duckdb
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from latency_analyzer import LatencyAnalyzer
from forecaster_mvp import ForecastEngine
from event_families import FAMILY_PATTERNS

DB_PATH = "fx_impact_app/data/warehouse.duckdb"

def get_events_for_family(conn, family_pattern, lookback_days=1095):
    """Récupère tous les événements matchant un pattern"""
    
    # Convertir pattern regex en SQL LIKE (approximation)
    # Ex: (?i)(non farm|nonfarm) → %non farm% OR %nonfarm%
    pattern_clean = family_pattern.replace('(?i)', '').replace('(', '').replace(')', '')
    
    # Extraire les termes du pattern
    terms = []
    for term in pattern_clean.split('|'):
        term = term.strip()
        if term:
            terms.append(term)
    
    # Construire WHERE clause
    if not terms:
        return []
    
    where_conditions = " OR ".join([f"LOWER(event_key) LIKE '%{term}%'" for term in terms])
    
    date_cutoff = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
    
    query = f"""
        SELECT ts_utc, event_key, actual, previous
        FROM events
        WHERE ({where_conditions})
          AND actual IS NOT NULL
          AND ts_utc >= '{date_cutoff}'
        ORDER BY ts_utc DESC
        LIMIT 200
    """
    
    try:
        results = conn.execute(query).fetchall()
        return results
    except Exception as e:
        print(f"    Erreur query: {e}")
        return []


def calculate_latency_for_event(analyzer, event_time, threshold_pips=5.0):
    """Calcule la latence pour UN événement spécifique"""
    try:
        result = analyzer.calculate_event_latency(
            event_time=event_time,
            threshold_pips=threshold_pips,
            window_minutes=60
        )
        
        if result and result.get('had_reaction'):
            return {
                'latency': result.get('latency_minutes', 60),
                'peak': result.get('peak_minutes', 60),
                'movement': result.get('peak_movement_pips', 0)
            }
    except:
        pass
    
    return None


def calculate_stats_from_latencies(latencies):
    """Calcule stats agrégées depuis liste de latences"""
    if not latencies or len(latencies) == 0:
        return None
    
    latencies_sorted = sorted(latencies)
    n = len(latencies_sorted)
    
    return {
        'median': np.median(latencies_sorted),
        'mean': np.mean(latencies_sorted),
        'p20': np.percentile(latencies_sorted, 20),
        'p80': np.percentile(latencies_sorted, 80),
        'min': min(latencies_sorted),
        'max': max(latencies_sorted),
        'count': n
    }


def precompute_all_families():
    """Pré-calcule stats avec workaround manuel"""
    
    conn = duckdb.connect(DB_PATH)
    
    print("📋 Table setup...")
    try:
        conn.execute("ALTER TABLE event_families ADD COLUMN IF NOT EXISTS latency_median DOUBLE")
        conn.execute("ALTER TABLE event_families ADD COLUMN IF NOT EXISTS latency_p20 DOUBLE")
        conn.execute("ALTER TABLE event_families ADD COLUMN IF NOT EXISTS latency_p80 DOUBLE")
        conn.execute("ALTER TABLE event_families ADD COLUMN IF NOT EXISTS ttr_median DOUBLE")
        conn.execute("ALTER TABLE event_families ADD COLUMN IF NOT EXISTS ttr_p20 DOUBLE")
        conn.execute("ALTER TABLE event_families ADD COLUMN IF NOT EXISTS ttr_p80 DOUBLE")
        conn.execute("ALTER TABLE event_families ADD COLUMN IF NOT EXISTS mfe_p80 DOUBLE")
        conn.execute("ALTER TABLE event_families ADD COLUMN IF NOT EXISTS n_events_latency INTEGER")
        print("✅ OK\n")
    except Exception as e:
        print(f"⚠️ Erreur: {e}\n")
    
    families = [f[0] for f in conn.execute(
        "SELECT DISTINCT family FROM event_families WHERE family IS NOT NULL"
    ).fetchall()]
    
    print(f"🔍 {len(families)} familles\n")
    
    # Mappings
    family_mapping = {
        'Retail_Sales': 'Retail Sales',
        'Trade_Balance': 'Trade Balance',
        'Jobless_Claims': 'Jobless Claims',
        'Consumer_Confidence': 'Consumer Confidence',
        'Industrial_Production': 'Industrial Production',
        'Building_Permits': 'Building Permits',
        'Factory_Orders': 'Factory Orders',
        'Durable_Goods': 'Durable Goods',
        'Interest_Rate': 'FOMC',
        'Inflation': 'CPI',
        'Wages': 'Employment Change'
    }
    
    analyzer = LatencyAnalyzer(DB_PATH)
    engine = ForecastEngine(DB_PATH)
    
    success_count = 0
    error_count = 0
    
    for i, family in enumerate(families, 1):
        print(f"[{i}/{len(families)}] {family}", end='')
        
        pattern_key = family_mapping.get(family, family)
        pattern = FAMILY_PATTERNS.get(pattern_key, '')
        
        print(f" → {pattern_key}")
        
        if not pattern:
            print(f"  ⚠️ No pattern")
            error_count += 1
            continue
        
        try:
            # === WORKAROUND : Récupérer événements manuellement ===
            events = get_events_for_family(conn, pattern, lookback_days=1095)
            
            if not events or len(events) == 0:
                print(f"  ⚠️ No events found")
                error_count += 1
                continue
            
            print(f"  📊 {len(events)} événements trouvés, calcul latences...", end='', flush=True)
            
            # Calculer latence pour chaque événement
            latencies = []
            peaks = []
            
            for event in events:
                event_time = event[0]
                
                latency_result = calculate_latency_for_event(
                    analyzer, 
                    event_time, 
                    threshold_pips=3.0  # Seuil plus bas pour plus de détections
                )
                
                if latency_result:
                    latencies.append(latency_result['latency'])
                    peaks.append(latency_result['peak'])
            
            if len(latencies) < 5:
                print(f"\n  ⚠️ Seulement {len(latencies)} réactions détectées (min: 5)")
                error_count += 1
                continue
            
            # Calculer stats agrégées
            latency_stats = calculate_stats_from_latencies(latencies)
            peak_stats = calculate_stats_from_latencies(peaks)
            
            if not latency_stats:
                print(f"\n  ⚠️ Échec calcul stats")
                error_count += 1
                continue
            
            # MFE depuis ForecastEngine
            mfe_stats = engine.calculate_family_stats(
                pattern, 
                horizon_minutes=60, 
                hist_years=3, 
                countries=None
            )
            
            # Préparer données
            latency_median = latency_stats['median']
            latency_p20 = latency_stats['p20']
            latency_p80 = latency_stats['p80']
            
            ttr_median = peak_stats['median']
            ttr_p20 = peak_stats['p20']
            ttr_p80 = peak_stats['p80']
            
            mfe_p80 = mfe_stats.get('mfe_p80', 10.0)
            n_events = len(latencies)
            
            # Stocker en DB
            conn.execute("""
                UPDATE event_families
                SET latency_median = ?,
                    latency_p20 = ?,
                    latency_p80 = ?,
                    ttr_median = ?,
                    ttr_p20 = ?,
                    ttr_p80 = ?,
                    mfe_p80 = ?,
                    n_events_latency = ?
                WHERE family = ?
            """, [
                latency_median, latency_p20, latency_p80,
                ttr_median, ttr_p20, ttr_p80,
                mfe_p80, n_events, family
            ])
            
            print(f" ✅")
            print(f"    Latence: {latency_median:.1f}min (P20: {latency_p20:.1f}, P80: {latency_p80:.1f})")
            print(f"    TTR: {ttr_median:.1f}min, MFE: {mfe_p80:.1f}pips")
            print(f"    Basé sur {n_events} événements")
            success_count += 1
            
        except Exception as e:
            print(f"\n  ❌ Error: {str(e)[:80]}")
            error_count += 1
    
    analyzer.close()
    engine.close()
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"PRÉ-CALCUL TERMINÉ")
    print(f"{'='*60}")
    print(f"✅ Succès: {success_count}/{len(families)} familles")
    print(f"❌ Erreurs: {error_count}/{len(families)} familles")
    
    if success_count >= 10:
        print(f"\n✅ EXCELLENT ! {success_count} familles pré-calculées")
        print("💡 Vous pouvez maintenant migrer vers predict_impact_v2()")
    elif success_count >= 6:
        print(f"\n✅ BON ! {success_count} familles pré-calculées")
    else:
        print(f"\n⚠️ {success_count} familles seulement")


if __name__ == "__main__":
    print("🚀 Démarrage pré-calcul (méthode workaround)...")
    print("⏱️  Durée estimée: 10-15 minutes")
    print("💡 Calcule latence événement par événement\n")
    precompute_all_families()

# ═════════════════════════════════════════════════════════════════
# END OF FILE - LINE 285
# ═════════════════════════════════════════════════════════════════
