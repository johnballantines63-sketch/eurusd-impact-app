"""
Validation Empirique - Prédictions vs Réalité Prices
===================================================

Compare les prédictions du module avec les impacts réels mesurés
dans prices_bern pour valider les amplifications.

Auteur: Session 132
Date: 13 novembre 2025
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd
from datetime import timedelta

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from core.doublewave_prediction import predict_doublewave_overlap

DB_PATH = project_root / 'data' / 'warehouse.duckdb'

print("\n" + "="*70)
print(" VALIDATION EMPIRIQUE - PRÉDICTIONS VS RÉALITÉ")
print("="*70)

conn = duckdb.connect(str(DB_PATH), read_only=True)

# Clusters prédictibles identifiés par find_clusters.py
clusters_to_validate = [
    # (date, heure, description, prédiction_pips)
    ("2023-02-03", "10:00:00", "EU PMI", 24.66),
    ("2023-02-03", "16:00:00", "US ISM", 24.72),
    ("2023-02-03", "19:30:00", "US Unemployment", 48.26),
    ("2023-03-22", "19:30:00", "US EIA", 30.74),
    ("2025-02-03", "10:00:00", "EU Manufacturing", 22.76),
    ("2025-09-11", "14:15:00", "EU ECB Rates", 32.11),
    # Cas spéciaux superposition
    ("2025-02-03", "11:00:00", "EU HICP Superposition", 12.67),
    ("2025-09-11", "14:30:00", "US CPI Superposition", 9.74),
]

def load_cluster_events(date_str, time_str):
    """Charge événements d'un cluster spécifique (fenêtre ±5 min)."""
    query = """
    WITH event_scores AS (
        SELECT 
            event_key,
            empirical_score as score
        FROM event_families
        WHERE empirical_score > 0
    )
    SELECT 
        e.ts_utc,
        e.country,
        e.event_key,
        e.event_title,
        e.importance_n,
        e.actual,
        e.estimate,
        e.forecast,
        e.previous,
        COALESCE(es.score, 0) as score
    FROM events e
    LEFT JOIN event_scores es ON e.event_key = es.event_key
    WHERE e.ts_utc BETWEEN ? AND ?
      AND e.country IN ('US', 'EU', 'UK', 'CA', 'JP', 'CH', 'RS', 'MK', 'UZ', 'CO', 'GR', 'ES', 'DE', 'IT', 'RU', 'CN')
    ORDER BY e.ts_utc
    """
    
    ts_utc = pd.Timestamp(f"{date_str} {time_str}", tz='UTC')
    start_time = ts_utc - timedelta(minutes=5)
    end_time = ts_utc + timedelta(minutes=5)
    
    df = conn.execute(query, [start_time, end_time]).df()
    return df.to_dict('records')

def measure_real_impact(date_str, time_str, window_minutes=60):
    """
    Mesure l'impact réel dans prices_bern.
    
    Baseline = close 1 minute avant événement
    Peak = maximum dans les window_minutes minutes suivantes
    Impact = Peak - Baseline (en pips)
    """
    ts_event = pd.Timestamp(f"{date_str} {time_str}", tz='Europe/Zurich')
    
    # Charger prix (baseline + fenêtre après)
    query = """
    SELECT 
        datetime,
        open,
        high,
        low,
        close
    FROM prices_bern
    WHERE datetime BETWEEN ? AND ?
    ORDER BY datetime
    """
    
    start_time = ts_event - timedelta(minutes=5)
    end_time = ts_event + timedelta(minutes=window_minutes)
    
    df_prices = conn.execute(query, [start_time, end_time]).df()
    
    if len(df_prices) == 0:
        return None, None, "Pas de prix disponibles"
    
    # Convertir timestamps (garder timezone Europe/Zurich)
    df_prices['datetime'] = pd.to_datetime(df_prices['datetime'], utc=False)
    if df_prices['datetime'].dt.tz is None:
        df_prices['datetime'] = df_prices['datetime'].dt.tz_localize('Europe/Zurich')
    df_prices = df_prices.set_index('datetime').sort_index()
    
    # Trouver baseline (close juste avant événement)
    baseline_candidates = df_prices[df_prices.index < ts_event]
    
    if len(baseline_candidates) == 0:
        return None, None, "Pas de baseline disponible"
    
    baseline = baseline_candidates['close'].iloc[-1]
    
    # Trouver peak (maximum après événement)
    after_event = df_prices[df_prices.index >= ts_event]
    
    if len(after_event) == 0:
        return None, None, "Pas de prix après événement"
    
    peak = after_event['high'].max()
    peak_time = after_event['high'].idxmax()
    
    # Calculer impact en pips (EUR/USD : 1 pip = 0.0001)
    impact_pips = (peak - baseline) * 10000
    
    return impact_pips, peak_time, None

# Validation de chaque cluster
results = []
total_mae = 0
n_valid = 0

for date_str, time_str, description, prediction_pips in clusters_to_validate:
    print(f"\n{'='*70}")
    print(f"CLUSTER : {date_str} {time_str} - {description}")
    print(f"{'='*70}")
    
    # 1. Charger événements du cluster
    events = load_cluster_events(date_str, time_str)
    
    print(f"\nÉvénements : {len(events)} trouvés")
    scored = [e for e in events if e.get('score', 0) > 0]
    print(f"Scorés : {len(scored)}")
    
    if len(scored) > 0:
        total_score = sum(e.get('score', 0) for e in scored)
        print(f"Score total : {total_score:.1f}")
        
        # Afficher échantillon
        for e in scored[:3]:
            print(f"  - {e['country']:3s} {e['event_key']:30s} (score: {e['score']:.1f})")
        if len(scored) > 3:
            print(f"  ... +{len(scored)-3} autres")
    
    # 2. Prédiction du module
    result_pred = predict_doublewave_overlap(events, debug=False)
    
    print(f"\nPRÉDICTION MODULE :")
    print(f"  Status        : {result_pred['status']}")
    print(f"  Amplification : {result_pred['amplification']}")
    print(f"  Prédiction    : {result_pred['prediction']} pips")
    
    # 3. Mesurer impact réel dans prices
    real_impact, peak_time, error = measure_real_impact(date_str, time_str)
    
    if error:
        print(f"\n❌ IMPOSSIBLE MESURER IMPACT RÉEL : {error}")
        results.append({
            'cluster': f"{date_str} {time_str}",
            'description': description,
            'prediction': prediction_pips,
            'real_impact': None,
            'error': None,
            'status': 'no_data'
        })
        continue
    
    print(f"\nIMPACT RÉEL (PRICES) :")
    print(f"  Impact mesuré : {real_impact:.2f} pips")
    if peak_time:
        print(f"  Peak atteint  : {peak_time.strftime('%H:%M:%S')}")
    
    # 4. Calculer erreur
    if result_pred['prediction'] is not None and real_impact is not None:
        error_pips = abs(result_pred['prediction'] - real_impact)
        error_pct = (error_pips / real_impact * 100) if real_impact != 0 else 0
        
        print(f"\n{'─'*70}")
        print(f"COMPARAISON :")
        print(f"  Prédiction    : {result_pred['prediction']:.2f} pips")
        print(f"  Réalité       : {real_impact:.2f} pips")
        print(f"  Erreur (MAE)  : {error_pips:.2f} pips ({error_pct:.1f}%)")
        print(f"{'─'*70}")
        
        if error_pips < 10:
            print("✅ EXCELLENTE PRÉDICTION (MAE < 10 pips)")
        elif error_pips < 20:
            print("✓ BONNE PRÉDICTION (MAE < 20 pips)")
        else:
            print("⚠️ PRÉDICTION À AMÉLIORER (MAE > 20 pips)")
        
        total_mae += error_pips
        n_valid += 1
        
        results.append({
            'cluster': f"{date_str} {time_str}",
            'description': description,
            'prediction': result_pred['prediction'],
            'real_impact': real_impact,
            'error': error_pips,
            'error_pct': error_pct,
            'status': 'validated'
        })
    else:
        print("\n⚠️ Prédiction ou impact réel manquant")
        results.append({
            'cluster': f"{date_str} {time_str}",
            'description': description,
            'prediction': result_pred['prediction'],
            'real_impact': real_impact,
            'error': None,
            'status': 'incomplete'
        })

conn.close()

# Rapport final
print("\n\n" + "="*70)
print(" RAPPORT FINAL VALIDATION EMPIRIQUE")
print("="*70)

print(f"\nClusters testés : {len(clusters_to_validate)}")
print(f"Validations complètes : {n_valid}")

if n_valid > 0:
    mean_mae = total_mae / n_valid
    print(f"\n📊 MAE MOYENNE : {mean_mae:.2f} pips")
    
    if mean_mae < 10:
        print("🎉 OBJECTIF ATTEINT (MAE < 10 pips) - MODULE VALIDÉ ✅")
    elif mean_mae < 20:
        print("✓ BON RÉSULTAT (MAE < 20 pips) - Module fonctionnel")
    else:
        print("⚠️ MAE ÉLEVÉE - Ajustements nécessaires")
    
    # Détails par cluster
    print("\n" + "─"*70)
    print("DÉTAILS PAR CLUSTER :")
    print("─"*70)
    
    for r in results:
        if r['status'] == 'validated':
            status_icon = "✅" if r['error'] < 10 else "✓" if r['error'] < 20 else "⚠️"
            print(f"{status_icon} {r['cluster']:20s} | Pred: {r['prediction']:6.2f} | Réel: {r['real_impact']:6.2f} | MAE: {r['error']:5.2f} pips")
        elif r['status'] == 'no_data':
            print(f"❌ {r['cluster']:20s} | Pas de données prix")
else:
    print("\n❌ AUCUNE VALIDATION COMPLÈTE POSSIBLE")
    print("   → Vérifier disponibilité données prices_bern")

print("\n" + "="*70)
print()
