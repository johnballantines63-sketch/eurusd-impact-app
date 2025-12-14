#!/usr/bin/env python3
"""
SESSION 107 - PHASE 2C CLUSTER #3 : DÉTECTION TENDANCE DYNAMIQUE
==================================================================
Méthode corrigée Session 102-103 :
- ❌ Fenêtre fixe 72h arbitraire
- ✅ Détection dynamique dernière inversion (durée variable)

Principe :
1. Charger 14 jours prix AVANT événement
2. Identifier extrema majeurs (prominence > seuil)
3. Détecter inversions tendance (HIGH→LOW, LOW→HIGH)  
4. Prendre DERNIÈRE inversion = début tendance actuelle
5. Mesurer R² depuis cette inversion (durée VARIABLE)
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import duckdb
from datetime import datetime, timedelta
from scipy.signal import find_peaks
from scipy.stats import linregress

print("="*80)
print("SESSION 107 - PHASE 2C : DÉTECTION TENDANCE DYNAMIQUE")
print("="*80)
print()
print("⚠️  CORRECTION MÉTHODOLOGIQUE")
print("   Fenêtre 72h fixe → Détection dynamique durée variable")
print()

# Setup
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

# Load config
import importlib.util
spec_config = importlib.util.spec_from_file_location(
    "config", 
    project_root / "eurusd_clean" / "app" / "config.py"
)
config_module = importlib.util.module_from_spec(spec_config)
spec_config.loader.exec_module(config_module)
config = config_module.Config()
db_path = Path(config.get_db_path())

# Charger résultats Phase 1
results_file = Path(__file__).parent.parent / "session106" / "phase1_cluster3_results_FINAL_CORRECTED.csv"
df = pd.read_csv(results_file)

print(f"✅ {len(df)} dates Cluster #3 chargées")
print()

# =============================================================================
# FONCTION DÉTECTION TENDANCE DYNAMIQUE
# =============================================================================

def detect_dynamic_trend(conn, event_datetime_bern, lookback_days=14):
    """
    Détecte tendance dynamiquement sans fenêtre temporelle fixe
    
    Retourne :
    - r2 : Qualité tendance
    - duration_hours : Durée tendance (variable!)
    - amplitude_pips : Amplitude tendance
    - reversal_time : Point de retournement
    """
    # Timestamp query (event 14:30 Bern → 12:30+02:00 DB)
    event_dt = pd.to_datetime(event_datetime_bern)
    query_dt = event_dt - timedelta(hours=2)
    
    # Charger lookback_days AVANT événement
    start_dt = query_dt - timedelta(days=lookback_days)
    
    query = f"""
    SELECT datetime, close, high, low
    FROM prices_1m
    WHERE datetime >= '{start_dt.strftime('%Y-%m-%d %H:%M:%S')}'::TIMESTAMP
      AND datetime < '{query_dt.strftime('%Y-%m-%d %H:%M:%S')}'::TIMESTAMP
    ORDER BY datetime ASC
    """
    
    df_prices = conn.execute(query).fetchdf()
    
    if len(df_prices) < 1000:
        return None
    
    # Convertir en pips
    df_prices['close_pips'] = df_prices['close'] * 10000
    df_prices['high_pips'] = df_prices['high'] * 10000
    df_prices['low_pips'] = df_prices['low'] * 10000
    
    # === ÉTAPE 1 : IDENTIFIER TOP 5 EXTREMA MAJEURS ===
    
    # Trouver peaks (HIGH) et troughs (LOW)
    window = 720  # 12h = 720 min
    
    # Peaks (HIGH)
    peaks_idx, _ = find_peaks(df_prices['high_pips'].values, distance=window, prominence=30)
    
    # Troughs (LOW) = peaks inversés
    troughs_idx, _ = find_peaks(-df_prices['low_pips'].values, distance=window, prominence=30)
    
    # Combiner et trier par temps
    extrema = []
    
    for idx in peaks_idx:
        extrema.append({
            'type': 'HIGH',
            'index': idx,
            'datetime': df_prices.iloc[idx]['datetime'],
            'price': df_prices.iloc[idx]['high'],
            'price_pips': df_prices.iloc[idx]['high_pips']
        })
    
    for idx in troughs_idx:
        extrema.append({
            'type': 'LOW',
            'index': idx,
            'datetime': df_prices.iloc[idx]['datetime'],
            'price': df_prices.iloc[idx]['low'],
            'price_pips': df_prices.iloc[idx]['low_pips']
        })
    
    # Trier par temps
    extrema = sorted(extrema, key=lambda x: x['datetime'])
    
    if len(extrema) < 2:
        return None
    
    # === ÉTAPE 2 : DÉTECTER DERNIÈRE INVERSION ===
    
    # Parcourir extrema en sens inverse pour trouver dernière inversion
    last_type = extrema[-1]['type']
    reversal_idx = None
    
    for i in range(len(extrema) - 2, -1, -1):
        if extrema[i]['type'] != last_type:
            reversal_idx = i
            break
    
    if reversal_idx is None:
        # Pas d'inversion détectée, prendre premier extremum
        reversal_idx = 0
    
    reversal = extrema[reversal_idx]
    
    # === ÉTAPE 3 : MESURER TENDANCE DEPUIS INVERSION ===
    
    # Filtrer prix depuis inversion jusqu'à événement
    reversal_datetime = pd.to_datetime(reversal['datetime'])
    df_trend = df_prices[df_prices['datetime'] >= reversal_datetime].copy()
    
    if len(df_trend) < 100:
        return None
    
    # Durée tendance (heures)
    duration_hours = (query_dt - reversal_datetime).total_seconds() / 3600
    
    # Régression linéaire
    df_trend['timestamp_numeric'] = (pd.to_datetime(df_trend['datetime']) - reversal_datetime).dt.total_seconds()
    X = df_trend['timestamp_numeric'].values
    y = df_trend['close'].values
    
    try:
        slope, intercept, r_value, p_value, std_err = linregress(X, y)
        r2 = r_value ** 2
    except:
        r2 = 0
    
    # Amplitude tendance
    amplitude_pips = (df_trend['high'].max() - df_trend['low'].min()) * 10000
    
    # Volatilité
    volatility_pips = df_trend['close'].std() * 10000
    
    return {
        'r2': r2,
        'duration_hours': duration_hours,
        'amplitude_pips': amplitude_pips,
        'volatility_pips': volatility_pips,
        'reversal_time': reversal_datetime,
        'reversal_type': reversal['type'],
        'num_points': len(df_trend),
        'num_extrema': len(extrema)
    }

# =============================================================================
# CALCUL MÉTRIQUES DYNAMIQUES
# =============================================================================

print("="*80)
print("DÉTECTION TENDANCES DYNAMIQUES (14 JOURS)")
print("="*80)
print()

conn = duckdb.connect(str(db_path), read_only=True)

metrics = []

for _, row in df.iterrows():
    date_str = row['date']
    
    print(f"📅 {date_str}")
    print("-"*80)
    
    event_datetime_bern = f"{date_str} 14:30:00+02:00"
    
    result = detect_dynamic_trend(conn, event_datetime_bern, lookback_days=14)
    
    if result is None:
        print(f"  ❌ Échec détection")
        print()
        continue
    
    print(f"  ✅ Tendance détectée")
    print(f"  📊 Type inversion  : {result['reversal_type']}")
    print(f"  📊 Point inversion : {result['reversal_time']}")
    print(f"  📊 Durée tendance  : {result['duration_hours']:.1f}h (VARIABLE !)")
    print(f"  📈 R²              : {result['r2']:.4f}")
    print(f"  📊 Amplitude       : {result['amplitude_pips']:.1f} pips")
    print(f"  📊 Volatilité      : {result['volatility_pips']:.1f} pips")
    print(f"  📊 Extrema trouvés : {result['num_extrema']}")
    print()
    
    metrics.append({
        'date': date_str,
        'r2_dynamic': result['r2'],
        'duration_hours': result['duration_hours'],
        'amplitude_dynamic': result['amplitude_pips'],
        'volatility_dynamic': result['volatility_pips'],
        'reversal_type': result['reversal_type'],
        'num_extrema': result['num_extrema']
    })

conn.close()

# =============================================================================
# FUSION AVEC RÉSULTATS PHASE 1
# =============================================================================

df_metrics = pd.DataFrame(metrics)
df_complete = df.merge(df_metrics, on='date', how='left')

print("="*80)
print("DONNÉES COMPLÈTES (MÉTHODE DYNAMIQUE)")
print("="*80)
print()

print(df_complete[['date', 'amp_optimal', 'r2_dynamic', 'duration_hours', 'amplitude_dynamic']].to_string(index=False))
print()

# =============================================================================
# CORRÉLATIONS
# =============================================================================

print("="*80)
print("CORRÉLATIONS amp_optimal vs MÉTRIQUES DYNAMIQUES")
print("="*80)
print()

vars_to_test = {
    'r2_dynamic': 'R² dynamique',
    'duration_hours': 'Durée tendance (h)',
    'amplitude_dynamic': 'Amplitude dynamique (pips)',
    'volatility_dynamic': 'Volatilité dynamique (pips)'
}

for var, label in vars_to_test.items():
    if var in df_complete.columns and not df_complete[var].isna().all():
        corr = df_complete['amp_optimal'].corr(df_complete[var])
        
        n = len(df_complete[df_complete[var].notna()])
        if n > 2:
            t_stat = corr * np.sqrt(n - 2) / np.sqrt(1 - corr**2 + 1e-10)
            from scipy.stats import t as t_dist
            p_value = 2 * (1 - t_dist.cdf(abs(t_stat), n - 2))
        else:
            p_value = 1.0
        
        print(f"📊 {label} :")
        print(f"   Corrélation  : {corr:+.3f}")
        print(f"   P-value      : {p_value:.4f}")
        print(f"   Significatif : {'✅ Oui' if p_value < 0.05 else '❌ Non (p≥0.05)'}")
        print()

# =============================================================================
# COMPARAISON 72H FIXE vs DYNAMIQUE
# =============================================================================

print("="*80)
print("COMPARAISON : FENÊTRE 72H FIXE vs DÉTECTION DYNAMIQUE")
print("="*80)
print()

# Charger résultats 72h si existent
results_72h_file = Path(__file__).parent / "cluster3_complete_analysis.csv"
if results_72h_file.exists():
    df_72h = pd.read_csv(results_72h_file)
    
    print("📊 Comparaison méthodes :")
    print()
    print("Date       | Durée dynamique | R² dynamique | R² 72h fixe | Différence")
    print("-"*80)
    
    for _, row in df_complete.iterrows():
        if pd.notna(row.get('duration_hours')):
            row_72h = df_72h[df_72h['date'] == row['date']].iloc[0] if len(df_72h[df_72h['date'] == row['date']]) > 0 else None
            
            if row_72h is not None and pd.notna(row_72h.get('r2_72h')):
                diff = row['r2_dynamic'] - row_72h['r2_72h']
                print(f"{row['date']} | {row['duration_hours']:6.1f}h        | "
                      f"{row['r2_dynamic']:.4f}      | {row_72h['r2_72h']:.4f}      | {diff:+.4f}")
    print()

# Sauvegarder
output_file = Path(__file__).parent / "cluster3_dynamic_analysis.csv"
df_complete.to_csv(output_file, index=False)

print("="*80)
print("ANALYSE DYNAMIQUE TERMINÉE ✅")
print("="*80)
print()
print(f"✅ Résultats sauvegardés : {output_file.name}")
print()
print("💡 PROCHAINE ÉTAPE : Tester formule avec R² dynamique")
