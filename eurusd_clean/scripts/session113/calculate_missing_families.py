"""
CALCUL FAMILLE MANQUANTE - Session 113
=======================================

Objectif : Calculer empirical_score UNIQUEMENT pour :
- current account (DE) - Evenement QUANTITATIF

ECB Press Conference (EU) est EXCLU car evenement QUALITATIF
(pas de actual/estimate/previous mesurables)

Utilise impact_measurement.py v4.0 (vue prices_bern)
"""
import sys
from pathlib import Path
import duckdb
import pandas as pd

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config import DB_PATH
from src.core.impact_measurement import measure_event_impact

print("=" * 80)
print("CALCUL FAMILLE MANQUANTE : current account (DE)")
print("=" * 80)

conn = duckdb.connect(str(DB_PATH))

# ============================================================================
# ETAPE 1 : Identifier occurrences historiques
# ============================================================================

print("\nETAPE 1 : IDENTIFICATION OCCURRENCES HISTORIQUES")
print("-" * 80)

print("\nCurrent Account (DE) - Evenement QUANTITATIF...")
result = conn.execute("""
    SELECT 
        ts_utc,
        event_key,
        country,
        actual,
        estimate,
        previous
    FROM events
    WHERE event_key = 'current account'
        AND country = 'DE'
        AND ts_utc >= '2023-01-01'
        AND actual IS NOT NULL
    ORDER BY ts_utc DESC
    LIMIT 30
""").fetchdf()

print(f"Trouve {len(result)} occurrences Current Account (DE)")
if not result.empty:
    print("\nEchantillon:")
    print(result[['ts_utc', 'actual', 'estimate']].head(10).to_string(index=False))

current_account_de = result

print("\n\nECB Press Conference (EU)...")
print("  [EXCLU] Evenement QUALITATIF (discours)")
print("  Impossible de calculer empirical_score historique")

# ============================================================================
# ETAPE 2 : Mesurer impacts avec impact_measurement.py v4.0
# ============================================================================

print("\n\nETAPE 2 : MESURE IMPACTS REELS")
print("-" * 80)

if current_account_de.empty:
    print("ERREUR: Aucune occurrence trouvee pour Current Account (DE)")
    conn.close()
    sys.exit(1)

print(f"\nCalcul pour current account (DE) - {len(current_account_de)} evenements")

impacts = []
latencies = []
ttrs = []
mfes = []

for idx, event in current_account_de.iterrows():
    event_time = pd.to_datetime(event['ts_utc'])
    
    try:
        # Mesurer impact avec impact_measurement.py v4.0
        result = measure_event_impact(
            event_datetime=event_time,
            lookback_minutes=5,
            lookahead_minutes=120
        )
        
        if result and result.get('impact_pips'):
            impact = abs(result['impact_pips'])
            impacts.append(impact)
            
            if result.get('latency_minutes'):
                latencies.append(result['latency_minutes'])
            if result.get('ttr_minutes'):
                ttrs.append(result['ttr_minutes'])
            if result.get('mfe_pips'):
                mfes.append(abs(result['mfe_pips']))
            
            print(f"  OK {event_time.strftime('%Y-%m-%d %H:%M')} : {impact:.1f} pips")
        else:
            print(f"  SKIP {event_time.strftime('%Y-%m-%d %H:%M')} : Pas de donnees prix")
    
    except Exception as e:
        print(f"  ERR {event_time.strftime('%Y-%m-%d %H:%M')} : {str(e)}")
        continue

# Calculer metriques
if not impacts:
    print("\nERREUR: Aucun impact mesure")
    conn.close()
    sys.exit(1)

empirical_score = sum(impacts) / len(impacts)
avg_movement_pips = empirical_score
sample_size = len(impacts)

latency_median = sorted(latencies)[len(latencies)//2] if latencies else None
ttr_median = sorted(ttrs)[len(ttrs)//2] if ttrs else None

latency_p20 = sorted(latencies)[int(len(latencies)*0.2)] if len(latencies) > 5 else None
latency_p80 = sorted(latencies)[int(len(latencies)*0.8)] if len(latencies) > 5 else None
ttr_p20 = sorted(ttrs)[int(len(ttrs)*0.2)] if len(ttrs) > 5 else None
ttr_p80 = sorted(ttrs)[int(len(ttrs)*0.8)] if len(ttrs) > 5 else None
mfe_p80 = sorted(mfes)[int(len(mfes)*0.8)] if len(mfes) > 5 else None

print(f"\nMetriques calculees:")
print(f"  Empirical Score: {empirical_score:.2f}")
print(f"  Sample Size: {sample_size}")
if latency_median:
    print(f"  Latency Median: {latency_median:.2f} min")

# ============================================================================
# ETAPE 3 : Inserer dans event_families
# ============================================================================

print("\n\nETAPE 3 : INSERTION DANS EVENT_FAMILIES")
print("-" * 80)

try:
    conn.execute("""
        INSERT OR REPLACE INTO event_families (
            event_key,
            country,
            family,
            empirical_score,
            avg_movement_pips,
            sample_size,
            latency_median,
            latency_p20,
            latency_p80,
            ttr_median,
            ttr_p20,
            ttr_p80,
            mfe_p80,
            n_events_latency
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        'current account',
        'DE',
        None,
        round(empirical_score, 6),
        round(avg_movement_pips, 6),
        sample_size,
        round(latency_median, 6) if latency_median else None,
        round(latency_p20, 6) if latency_p20 else None,
        round(latency_p80, 6) if latency_p80 else None,
        round(ttr_median, 6) if ttr_median else None,
        round(ttr_p20, 6) if ttr_p20 else None,
        round(ttr_p80, 6) if ttr_p80 else None,
        round(mfe_p80, 6) if mfe_p80 else None,
        len(latencies)
    ])
    
    print("\nSUCCES: Famille inseree dans event_families")
    print(f"  Event: current account (DE)")
    print(f"  Score: {empirical_score:.2f}")

except Exception as e:
    print(f"\nERREUR insertion: {str(e)}")
    conn.close()
    sys.exit(1)

# ============================================================================
# ETAPE 4 : Verification
# ============================================================================

print("\n\nETAPE 4 : VERIFICATION")
print("-" * 80)

result = conn.execute("""
    SELECT 
        event_key,
        country,
        empirical_score,
        sample_size
    FROM event_families
    WHERE event_key = 'current account' AND country = 'DE'
""").fetchdf()

if not result.empty:
    print("\nFamille ajoutee:")
    print(result.to_string(index=False))
else:
    print("\nERREUR: Famille non trouvee apres insertion")

conn.close()

# ============================================================================
# RESUME
# ============================================================================

print("\n" + "=" * 80)
print("RESUME")
print("=" * 80)
print("\nSUCCES COMPLET - current account (DE) ajoute !")
print(f"  Empirical Score: {empirical_score:.2f}")
print(f"  Sample Size: {sample_size}")
print("\nNote: ECB Press Conference (EU) exclu (evenement qualitatif)")
print("\nPROCHAINE ETAPE:")
print("  bash scripts/session113/run_test_cluster_calculator.sh")
print("=" * 80)
