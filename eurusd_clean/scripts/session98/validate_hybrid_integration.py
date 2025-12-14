"""
Script validation HYBRIDE S51-55 + Formules 92.xx - Session 98
Intégration EN COMPLÉMENT : Baseline S51-55 + Amélioration clusters connus

APPROCHE:
1. Baseline S51-55 TOUJOURS calculée (fallback sûr)
2. Détection cluster + formules 92.xx si cluster connu
3. Comparaison des deux approches vs réalité
"""

import pandas as pd
import duckdb
import sys
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np

# Ajouter scripts/session92 au path pour import
sys.path.insert(0, str(Path(__file__).parent.parent / "session92"))
from formulas_hybrid_empirical import calculate_impact_hybrid, identify_cluster

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_DIR = Path(__file__).parent.parent.parent
DB_PATH = BASE_DIR / "app" / "data" / "warehouse.duckdb"
INPUT_CSV = BASE_DIR / "scripts" / "session92.8" / "resultats_40_dates_s92_13.csv"
OUTPUT_CSV = BASE_DIR / "scripts" / "session98" / "validation_hybrid_s51_55_92xx.csv"

AMPLIFICATION = 2.5

print("=" * 100)
print("🔍 VALIDATION HYBRIDE S51-55 + FORMULES 92.XX")
print("=" * 100)
print(f"\n📊 Database: {DB_PATH}")
print(f"📄 Input CSV: {INPUT_CSV}")
print(f"💾 Output CSV: {OUTPUT_CSV}")
print(f"\n⚙️  Baseline: S51-55 (amplification {AMPLIFICATION})")
print(f"🎯 Amélioration: Formules 92.xx pour clusters connus")

# ============================================================================
# FONCTIONS FORMULES S51-55 (BASELINE)
# ============================================================================

def calculate_impact_d(empirical_score: float, num_events: int, amplification: float = 2.5) -> float:
    """Formule D validée Sessions 51-55"""
    base_impact = empirical_score / 10.0
    multi_event_factor = np.sqrt(num_events)
    impact = base_impact * amplification * multi_event_factor
    return impact

def calculate_ttr_b(empirical_score: float, num_events: int) -> float:
    """Formule TTR B validée Sessions 51-55"""
    log_component = np.log10(empirical_score + 1)
    multi_event_factor = np.sqrt(num_events)
    ttr = log_component * multi_event_factor + 1
    return ttr

# ============================================================================
# MAPPING EVENT → FAMILLE
# ============================================================================

def map_event_to_family(event_title: str, event_key: str) -> str:
    """
    Mappe un événement vers une famille pour formules 92.xx
    
    Returns:
        Famille: 'CPI', 'NFP', 'CONSTRUCTION', 'FOMC', 'UNKNOWN'
    """
    if event_title is None and event_key is None:
        return 'UNKNOWN'
    
    # Convertir en majuscules pour recherche
    title = str(event_title).upper() if event_title else ""
    key = str(event_key).upper() if event_key else ""
    combined = title + " " + key
    
    # Détection CPI
    if 'CPI' in combined or 'INFLATION' in combined:
        return 'CPI'
    
    # Détection NFP
    if 'NFP' in combined or 'NON-FARM' in combined or 'NONFARM' in combined:
        return 'NFP'
    
    # Détection FOMC
    if 'FOMC' in combined or 'FED ' in combined or 'FEDERAL RESERVE' in combined:
        return 'FOMC'
    
    # Détection Construction
    if 'CONSTRUCTION' in combined or 'BUILDING' in combined or 'HOUSING' in combined:
        return 'CONSTRUCTION'
    
    # Détection Employment (traiter comme NFP)
    if 'EMPLOYMENT' in combined or 'JOBLESS' in combined or 'UNEMPLOYMENT' in combined:
        return 'NFP'
    
    return 'UNKNOWN'

# ============================================================================
# CALCUL SURPRISES
# ============================================================================

def calculate_surprises(df_events):
    """
    Calcule les surprises pour chaque événement
    
    Returns:
        Liste des surprises en %
    """
    surprises = []
    
    for idx, row in df_events.iterrows():
        actual = row.get('actual')
        estimate = row.get('estimate')
        forecast = row.get('forecast')
        previous = row.get('previous')
        
        # Priorité : estimate > forecast > previous
        reference = estimate if pd.notna(estimate) and estimate != 0 else \
                    forecast if pd.notna(forecast) and forecast != 0 else \
                    previous if pd.notna(previous) and previous != 0 else None
        
        if pd.notna(actual) and reference is not None and reference != 0:
            surprise = abs((actual - reference) / reference) * 100
            surprises.append(surprise)
        else:
            surprises.append(0.0)
    
    return surprises

# ============================================================================
# CHARGEMENT DONNÉES
# ============================================================================

print("\n" + "=" * 100)
print("📥 CHARGEMENT DONNÉES")
print("=" * 100)

df_real = pd.read_csv(INPUT_CSV)
print(f"\n✅ CSV chargé: {len(df_real)} dates")

conn = duckdb.connect(str(DB_PATH), read_only=True)
print(f"✅ Connexion DB établie")

# ============================================================================
# FONCTION CHARGEMENT ÉVÉNEMENTS
# ============================================================================

def load_events_for_date(conn, date_str: str, time_str: str):
    """Charge événements avec timezone fix"""
    time_obj = datetime.strptime(time_str, "%H:%M:%S")
    hour = time_obj.hour
    minute = time_obj.minute
    
    query = """
    SELECT 
        e.event_title,
        e.event_key,
        e.country,
        ef.empirical_score,
        e.actual,
        e.estimate,
        e.forecast,
        e.previous
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE DATE(e.ts_utc) = ?
      AND EXTRACT(HOUR FROM e.ts_utc) = ?
      AND EXTRACT(MINUTE FROM e.ts_utc) = ?
    ORDER BY ef.empirical_score DESC NULLS LAST
    """
    
    df_events = conn.execute(query, [date_str, hour, minute]).df()
    return df_events

# ============================================================================
# VALIDATION DATE PAR DATE
# ============================================================================

print("\n" + "=" * 100)
print("🧪 VALIDATION HYBRIDE DATE PAR DATE")
print("=" * 100)

results = []

for idx, row in df_real.iterrows():
    date_str = row['date']
    time_str = row['event_time']
    impact_real = row['impact_real']
    
    print(f"\n{'=' * 80}")
    print(f"📅 Date {idx+1}/{len(df_real)}: {date_str} {time_str}")
    print(f"{'=' * 80}")
    
    try:
        df_events = load_events_for_date(conn, date_str, time_str)
        
        if len(df_events) == 0:
            print(f"⚠️  Aucun événement")
            results.append({
                'date': date_str,
                'event_time': time_str,
                'impact_real': impact_real,
                'impact_baseline': None,
                'impact_hybrid': None,
                'error_baseline': None,
                'error_hybrid': None,
                'status': 'NO_EVENTS'
            })
            continue
        
        df_events_valid = df_events[df_events['empirical_score'].notna()].copy()
        
        if len(df_events_valid) == 0:
            print(f"⚠️  Aucun score empirique")
            results.append({
                'date': date_str,
                'event_time': time_str,
                'impact_real': impact_real,
                'impact_baseline': None,
                'impact_hybrid': None,
                'error_baseline': None,
                'error_hybrid': None,
                'status': 'NO_SCORE'
            })
            continue
        
        num_events = len(df_events_valid)
        score_max = df_events_valid['empirical_score'].max()
        score_avg = df_events_valid['empirical_score'].mean()
        
        print(f"✅ {num_events} événements | Score max: {score_max:.1f} | Score moy: {score_avg:.1f}")
        
        # ================================================================
        # PRÉDICTION 1 : BASELINE S51-55
        # ================================================================
        
        impact_baseline = calculate_impact_d(score_avg, num_events, AMPLIFICATION)
        error_baseline = abs(impact_baseline - impact_real)
        
        print(f"\n📊 BASELINE S51-55:")
        print(f"   Impact: {impact_baseline:.2f} pips")
        print(f"   Erreur: {error_baseline:.2f} pips")
        
        # ================================================================
        # PRÉDICTION 2 : HYBRIDE 92.XX
        # ================================================================
        
        # Mapper événements vers familles
        families = []
        for _, evt in df_events_valid.iterrows():
            family = map_event_to_family(evt.get('event_title'), evt.get('event_key'))
            families.append(family)
        
        # Calculer surprises
        surprises = calculate_surprises(df_events_valid)
        
        # Identifier cluster
        cluster_type, cluster_size = identify_cluster(families, num_events)
        
        # Calculer impact hybride
        result_hybrid = calculate_impact_hybrid(families, surprises, num_events)
        impact_hybrid = result_hybrid['impact_predicted']
        cluster_found = result_hybrid['cluster_found']
        error_hybrid = abs(impact_hybrid - impact_real)
        
        print(f"\n🎯 HYBRIDE 92.XX:")
        print(f"   Cluster: {cluster_type} ({num_events} events) {'✅' if cluster_found else '⚠️ fallback'}")
        print(f"   Surprise vectorielle: {result_hybrid['surprise_vectorielle']:.1f}%")
        print(f"   Impact: {impact_hybrid:.2f} pips")
        print(f"   Erreur: {error_hybrid:.2f} pips")
        
        # ================================================================
        # COMPARAISON
        # ================================================================
        
        print(f"\n📊 IMPACT RÉEL: {impact_real:.2f} pips")
        
        improvement = error_baseline - error_hybrid
        improvement_pct = (improvement / error_baseline * 100) if error_baseline > 0 else 0
        
        if error_hybrid < error_baseline:
            print(f"✅ HYBRIDE MEILLEUR: -{improvement:.2f} pips ({improvement_pct:.1f}%)")
            best = 'HYBRID'
        elif error_baseline < error_hybrid:
            print(f"⚠️ BASELINE MEILLEUR: +{abs(improvement):.2f} pips")
            best = 'BASELINE'
        else:
            print(f"➡️  ÉGALITÉ")
            best = 'EQUAL'
        
        # Stocker résultats
        results.append({
            'date': date_str,
            'event_time': time_str,
            'num_events': num_events,
            'cluster_type': cluster_type,
            'cluster_found': cluster_found,
            'impact_real': impact_real,
            'impact_baseline': impact_baseline,
            'impact_hybrid': impact_hybrid,
            'error_baseline': error_baseline,
            'error_hybrid': error_hybrid,
            'improvement': improvement,
            'improvement_pct': improvement_pct,
            'best': best,
            'status': 'VALIDATED'
        })
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

conn.close()

# ============================================================================
# RÉSULTATS GLOBAUX
# ============================================================================

print("\n" + "=" * 100)
print("📊 RÉSULTATS GLOBAUX COMPARATIFS")
print("=" * 100)

df_results = pd.DataFrame(results)
df_valid = df_results[df_results['error_baseline'].notna()].copy()

if len(df_valid) > 0:
    mae_baseline = df_valid['error_baseline'].mean()
    mae_hybrid = df_valid['error_hybrid'].mean()
    improvement_global = mae_baseline - mae_hybrid
    improvement_pct_global = (improvement_global / mae_baseline * 100)
    
    print(f"\n📈 MAE COMPARAISON:")
    print(f"   Baseline S51-55: {mae_baseline:.2f} pips")
    print(f"   Hybride 92.xx: {mae_hybrid:.2f} pips")
    print(f"   Amélioration: {improvement_global:.2f} pips ({improvement_pct_global:.1f}%)")
    
    if mae_hybrid < mae_baseline:
        print(f"   ✅ HYBRIDE GAGNE")
    elif mae_baseline < mae_hybrid:
        print(f"   ⚠️ BASELINE GAGNE")
    else:
        print(f"   ➡️  ÉGALITÉ")
    
    # Compteurs
    hybrid_better = (df_valid['best'] == 'HYBRID').sum()
    baseline_better = (df_valid['best'] == 'BASELINE').sum()
    equal = (df_valid['best'] == 'EQUAL').sum()
    
    print(f"\n🏆 VICTOIRES PAR APPROCHE:")
    print(f"   Hybride meilleur: {hybrid_better}/{len(df_valid)} ({hybrid_better/len(df_valid)*100:.1f}%)")
    print(f"   Baseline meilleur: {baseline_better}/{len(df_valid)} ({baseline_better/len(df_valid)*100:.1f}%)")
    print(f"   Égalité: {equal}/{len(df_valid)}")
    
    # Clusters trouvés
    clusters_found = df_valid[df_valid['cluster_found'] == True]
    if len(clusters_found) > 0:
        print(f"\n🎯 PERFORMANCE CLUSTERS CONNUS ({len(clusters_found)} dates):")
        mae_clusters = clusters_found['error_hybrid'].mean()
        print(f"   MAE hybride: {mae_clusters:.2f} pips")

# ============================================================================
# SAUVEGARDE
# ============================================================================

print("\n" + "=" * 100)
print("💾 SAUVEGARDE")
print("=" * 100)

df_results.to_csv(OUTPUT_CSV, index=False)
print(f"✅ Résultats: {OUTPUT_CSV}")

print("\n" + "=" * 100)
print("✅ VALIDATION TERMINÉE")
print("=" * 100)
