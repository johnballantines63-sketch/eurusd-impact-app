"""
VALIDATION DIRECTE PLANIFICATEUR V3.0 - 11 SEPTEMBRE 2025
=========================================================

Test manuel qui accède directement à la DB et simule les étapes 1-11
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
import pytz
import duckdb

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from core import config
DB_PATH = config.DB_PATH

print("="*80)
print("VALIDATION PLANIFICATEUR V3.0 - 11 SEPTEMBRE 2025")
print("="*80)
print()

# ==================================================================================
# PARAMÈTRES
# ==================================================================================

DATE_STR = "11.09.2025"
MIN_PIPS = 35.0
TIMEZONE_STR = "Europe/Zurich"
REFERENCE_IMPACT = 56.2  # pips (Session 115 validé)

print(f"📅 Date          : {DATE_STR}")
print(f"📏 min_pips      : {MIN_PIPS}")
print(f"🌍 Timezone      : {TIMEZONE_STR}")
print(f"🎯 Référence     : {REFERENCE_IMPACT} pips")
print()

# Parser date
target_date = datetime.strptime(DATE_STR, '%d.%m.%Y')
timezone = pytz.timezone(TIMEZONE_STR)

print(f"✅ Date validée  : {target_date.strftime('%Y-%m-%d')}")
print()

# ==================================================================================
# ÉTAPE 2 : CHARGER EVENTS HIGH
# ==================================================================================

print("ÉTAPE 2 : Chargement événements HIGH...")
print("-" * 80)

conn = duckdb.connect(str(DB_PATH), read_only=True)

query_events = f"""
SELECT 
    ts_utc, country, event_title, event_key, importance_n,
    actual, estimate, forecast, previous
FROM events
WHERE DATE(ts_utc AT TIME ZONE '{TIMEZONE_STR}') = ?
  AND importance_n = 3
ORDER BY ts_utc
"""

df_events = conn.execute(query_events, [target_date.strftime('%Y-%m-%d')]).df()

if len(df_events) == 0:
    print("❌ ÉCHEC : Aucun événement HIGH trouvé")
    conn.close()
    sys.exit(1)

df_events['ts_bern'] = pd.to_datetime(df_events['ts_utc']).dt.tz_convert(TIMEZONE_STR)

print(f"✅ {len(df_events)} événement(s) HIGH trouvé(s)")
print(f"\nPREMIERS ÉVÉNEMENTS:")
for idx in range(min(5, len(df_events))):
    row = df_events.iloc[idx]
    print(f"  {row['ts_bern'].strftime('%H:%M')} | {row['country']:2s} | {row['event_title'][:50]}")

if len(df_events) > 5:
    print(f"  ... et {len(df_events) - 5} autres événements")
    
print()

# ==================================================================================
# ÉTAPE 3 : CHARGER PRIX
# ==================================================================================

print("ÉTAPE 3 : Chargement prix 1-minute...")
print("-" * 80)

query_prix = """
SELECT datetime, open, high, low, close
FROM prices_bern
WHERE DATE(datetime) = ?
ORDER BY datetime
"""

df_prices = conn.execute(query_prix, [target_date.strftime('%Y-%m-%d')]).df()

if len(df_prices) == 0:
    print("❌ ÉCHEC : Aucun prix disponible")
    conn.close()
    sys.exit(1)

df_prices['datetime'] = pd.to_datetime(df_prices['datetime'], utc=True).dt.tz_convert(TIMEZONE_STR)
df_prices = df_prices.set_index('datetime')

print(f"✅ {len(df_prices)} prix chargés")
print(f"   Plage : {df_prices.index.min().strftime('%H:%M')} → {df_prices.index.max().strftime('%H:%M')}")
print()

# ==================================================================================
# ÉTAPE 4 : ENRICHIR AVEC SCORES
# ==================================================================================

print("ÉTAPE 4 : Enrichissement avec scores empiriques...")
print("-" * 80)

df_scores = conn.execute("SELECT event_key, country, empirical_score FROM event_families").df()

scores, surprises = [], []

for idx, row in df_events.iterrows():
    # Score
    score_match = df_scores[
        (df_scores['event_key'] == row['event_key']) & 
        (df_scores['country'] == row['country'])
    ]
    score = score_match.iloc[0]['empirical_score'] if len(score_match) > 0 else 0.0
    scores.append(score)
    
    # Surprise
    if pd.notna(row['actual']) and pd.notna(row['estimate']) and row['estimate'] != 0:
        surprise = (row['actual'] - row['estimate']) / abs(row['estimate']) * 100
    else:
        surprise = 0.0
    surprises.append(surprise)

df_events['score'] = scores
df_events['surprise'] = surprises
df_events['score_adjusted'] = df_events['score'] * (1 + df_events['surprise'] / 100)

events_scored = len(df_events[df_events['score'] > 0])
total_score = df_events['score'].sum()
score_adjusted_total = df_events['score_adjusted'].sum()

print(f"✅ {events_scored}/{len(df_events)} événements scorés")
print(f"   Score total     : {total_score:.1f}")
print(f"   Score adjusted  : {score_adjusted_total:.1f}")
print()

print("TOP 5 ÉVÉNEMENTS SCORÉS:")
df_scored = df_events[df_events['score'] > 0].sort_values('score', ascending=False).head(5)
for idx, row in df_scored.iterrows():
    print(f"  {row['ts_bern'].strftime('%H:%M')} | {row['country']:2s} | {row['score']:6.1f} | {row['event_title'][:40]}")
print()

conn.close()

# ==================================================================================
# ÉTAPE 5 : DÉTECTION PATTERN
# ==================================================================================

print("ÉTAPE 5 : Détection pattern...")
print("-" * 80)

# Baseline
first_event_time = df_events['ts_bern'].min()
baseline_time = first_event_time - pd.Timedelta(minutes=1)

valid_times = df_prices[df_prices.index < first_event_time].index
if len(valid_times) == 0:
    print("❌ ÉCHEC : Pas de prix avant événement")
    sys.exit(1)

baseline_time = valid_times[-1]
baseline = df_prices.loc[baseline_time, 'close']

print(f"Premier événement : {first_event_time.strftime('%H:%M:%S')}")
print(f"Baseline time     : {baseline_time.strftime('%H:%M:%S')}")
print(f"Baseline price    : {baseline:.5f}")
print()

# Scanner 6h après premier événement
scan_end = first_event_time + pd.Timedelta(hours=6)
df_after = df_prices[(df_prices.index >= first_event_time) & (df_prices.index <= scan_end)]

if len(df_after) == 0:
    print("❌ ÉCHEC : Pas de prix après événement")
    sys.exit(1)

# Calculer impact mesuré
diff = (df_after['close'] - baseline).abs()
max_idx = diff.idxmax()
max_impact = diff.max()
impact_pips = max_impact * 10000

print(f"Impact MAXIMUM mesuré : {impact_pips:.1f} pips")
print(f"Atteint à             : {max_idx.strftime('%H:%M:%S')}")
print(f"Prix max              : {df_after.loc[max_idx, 'close']:.5f}")
print()

# Métriques pour classification
num_scored = events_scored

print(f"MÉTRIQUES CLASSIFICATION:")
print(f"  Impact (pips)  : {impact_pips:.1f}")
print(f"  Total score    : {total_score:.1f}")
print(f"  Events total   : {len(df_events)}")
print(f"  Events scorés  : {num_scored}")
print()

# Classification simplifiée (Étape 5 Planificateur V3.0)
if impact_pips < MIN_PIPS:
    pattern_type = 'INCONNU'
    reason = f'Impact ({impact_pips:.1f}) < seuil ({MIN_PIPS})'
elif total_score >= 150 and num_scored >= 5:
    pattern_type = 'DOUBLE_WAVE'
    reason = f'Score élevé ({total_score:.1f} >= 150) + nombreux events ({num_scored} >= 5)'
elif impact_pips > 40:
    pattern_type = 'SINGLE_WAVE_FORT'
    reason = f'Impact élevé ({impact_pips:.1f} > 40 pips)'
elif impact_pips >= 20:
    pattern_type = 'SINGLE_WAVE_STANDARD'
    reason = f'Impact modéré ({impact_pips:.1f} >= 20 pips)'
else:
    pattern_type = 'INCONNU'
    reason = f'Critères non satisfaits'

print(f"PATTERN DÉTECTÉ : {pattern_type}")
print(f"Raison          : {reason}")
print()

# ==================================================================================
# ÉTAPES 6-9 : PRÉDICTION
# ==================================================================================

print(f"ÉTAPES 6-9 : Prédiction (pattern {pattern_type})...")
print("-" * 80)

prediction_pips = None
amplification = None
method = None
status = None
r2_trend = None

if pattern_type == "DOUBLE_WAVE":
    print("→ Module DoubleWave (Session 132)")
    print()
    
    # Import module
    from core.doublewave_prediction import predict_doublewave_overlap
    
    # Préparer events
    events_list = []
    for idx, row in df_events.iterrows():
        events_list.append({
            'event_key': row['event_key'],
            'country': row['country'],
            'score': row['score'],
            'actual': row['actual'] if pd.notna(row['actual']) else None,
            'estimate': row['estimate'] if pd.notna(row['estimate']) else None
        })
    
    result = predict_doublewave_overlap(events_list, debug=False)
    
    prediction_pips = result.get('prediction')
    amplification = result.get('amplification')
    method = 'doublewave_overlap'
    status = result['status']
    
    print(f"Status        : {status}")
    print(f"Prédiction    : {prediction_pips:.1f} pips" if prediction_pips else "Non disponible")
    print(f"Amplification : {amplification:.4f}" if amplification else "N/A")
    print(f"Pattern type  : {result.get('pattern_type', 'N/A')}")
    print(f"Raison        : {result.get('reason', 'N/A')}")
    
elif pattern_type in ["SINGLE_WAVE_STANDARD", "SINGLE_WAVE_FORT"]:
    print("→ Fonction Universelle (Sessions 125-126)")
    print()
    
    # Calculer R² tendance (60 min avant premier événement)
    from sklearn.linear_model import LinearRegression
    
    window_start = first_event_time - pd.Timedelta(minutes=60)
    window_end = first_event_time - pd.Timedelta(minutes=1)
    
    df_window = df_prices[(df_prices.index >= window_start) & (df_prices.index <= window_end)]
    
    print(f"Fenêtre R²    : {window_start.strftime('%H:%M')} → {window_end.strftime('%H:%M')}")
    print(f"Prix dans     : {len(df_window)} minutes")
    
    if len(df_window) >= 10:
        X = np.arange(len(df_window)).reshape(-1, 1)
        y = df_window['close'].values
        
        model = LinearRegression()
        model.fit(X, y)
        r2_trend = model.score(X, y)
        
        # Fonction universelle
        a, b, c = 0.040833, 0.050220, -0.006553
        r2_clipped = max(0.0, min(1.0, r2_trend))
        amplification = max(0.01, min(0.20, a + b*r2_clipped + c*r2_clipped**2))
        
        # Prédiction
        prediction_pips = score_adjusted_total * amplification
        
        method = 'universal_fallback'
        status = 'predicted'
        
        print(f"R² tendance   : {r2_trend:.3f}")
        print(f"Amplification : {amplification:.4f}")
        print(f"Score adjusted: {score_adjusted_total:.1f}")
        print(f"Prédiction    : {prediction_pips:.1f} pips")
        
        if pattern_type == 'SINGLE_WAVE_FORT':
            print()
            print("⚠️  Warning: Pattern Single_Wave_Fort détecté")
            print("    MAE élevé attendu selon Session 132")
    else:
        print(f"❌ Fenêtre insuffisante (< 10 min)")
        status = 'excluded'
        method = None
else:
    print("→ Pattern inconnu - Pas de prédiction")
    status = 'excluded'
    method = None

print()

# ==================================================================================
# RÉSULTATS FINAUX
# ==================================================================================

print("="*80)
print("RÉSULTATS FINAUX - 11 SEPTEMBRE 2025")
print("="*80)
print()

print("MÉTRIQUES PRINCIPALES:")
print(f"  Pattern détecté      : {pattern_type}")
print(f"  Impact mesuré        : {impact_pips:.1f} pips")
print(f"  Impact référence     : {REFERENCE_IMPACT} pips")
print(f"  Status prédiction    : {status}")

if prediction_pips:
    mae = abs(prediction_pips - REFERENCE_IMPACT)
    mae_pct = (mae / REFERENCE_IMPACT) * 100
    
    print(f"  Impact prédit        : {prediction_pips:.1f} pips")
    print(f"  MAE                  : {mae:.1f} pips ({mae_pct:.1f}%)")
    print(f"  Méthode              : {method}")
    print(f"  Amplification        : {amplification:.4f}")
    if r2_trend is not None:
        print(f"  R² tendance          : {r2_trend:.3f}")
    
    print()
    print("ÉVALUATION:")
    if mae < 5:
        print("  ⭐⭐⭐ EXCELLENT : MAE < 5 pips")
    elif mae < 10:
        print("  ✅✅ TRÈS BON : MAE < 10 pips")
    elif mae < 20:
        print("  ✅ ACCEPTABLE : MAE < 20 pips (critère session 135)")
    else:
        print("  ⚠️  À AMÉLIORER : MAE >= 20 pips")
        
else:
    print(f"  Impact prédit        : Non disponible")
    print()
    print("ÉVALUATION:")
    print("  ❌ ÉCHEC : Pas de prédiction générée")

print()

# ==================================================================================
# COMPARAISON AVEC RÉFÉRENCE
# ==================================================================================

print("COMPARAISON AVEC RÉFÉRENCE SESSION 115:")
print(f"  Référence validée    : {REFERENCE_IMPACT} pips (MAE 0.29 pips)")
print(f"  Impact prédit ici    : {prediction_pips:.1f} pips" if prediction_pips else "  Impact prédit ici    : Non disponible")
if prediction_pips:
    print(f"  Écart absolu         : {mae:.1f} pips")
    print(f"  Écart relatif        : {mae_pct:.1f}%")
print()

# ==================================================================================
# EXPORT CSV
# ==================================================================================

print("ÉTAPE 11 : Export résultats...")
print("-" * 80)

results = {
    'date': target_date.strftime('%Y-%m-%d'),
    'pattern': pattern_type,
    'impact_mesure_pips': round(impact_pips, 1),
    'impact_reference_pips': REFERENCE_IMPACT,
    'impact_predit_pips': round(prediction_pips, 1) if prediction_pips else None,
    'mae_pips': round(abs(prediction_pips - REFERENCE_IMPACT), 1) if prediction_pips else None,
    'mae_percent': round((abs(prediction_pips - REFERENCE_IMPACT) / REFERENCE_IMPACT) * 100, 1) if prediction_pips else None,
    'amplification': round(amplification, 4) if amplification else None,
    'r2_trend': round(r2_trend, 3) if r2_trend else None,
    'method': method,
    'status': status,
    'num_events': len(df_events),
    'num_scored': events_scored,
    'total_score': round(total_score, 1),
    'score_adjusted': round(score_adjusted_total, 1),
    'baseline_time': baseline_time.strftime('%H:%M:%S'),
    'baseline_price': round(baseline, 5),
    'max_impact_time': max_idx.strftime('%H:%M:%S')
}

df_result = pd.DataFrame([results])
output_file = Path(__file__).parent / 'test_11_septembre_results.csv'
df_result.to_csv(output_file, index=False)

print(f"✅ Résultats exportés : {output_file.name}")
print()

# Afficher CSV
print("CONTENU CSV:")
print(df_result.to_string(index=False))
print()

print("="*80)
print("TEST COMPLÉTÉ AVEC SUCCÈS")
print("="*80)
