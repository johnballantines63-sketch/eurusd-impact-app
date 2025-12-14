#!/usr/bin/env python3
"""
ANALYSE CAS PAR CAS - MÉTHODOLOGIE COMPLÈTE
============================================

Pour chaque des 22 cas, RECALCULER TOUT depuis le début :
1. Charger events depuis DB
2. Calculer impact_predit avec formules S51-55 (amp=2.5)
3. Mesurer impact_real depuis prices
4. Calculer amp_parfaite
5. Calculer métriques tendance
6. TESTER stratégies d'amplification alternatives
7. Comparer erreurs EN PIPS

MÉTHODOLOGIE ANDRÉ - RIGOUREUSE
"""

import sys
from pathlib import Path
import duckdb
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from scipy import signal

# Chemins
project_root = Path(__file__).resolve().parents[2]
fx_impact_app = project_root.parent / "fx_impact_app"
sys.path.insert(0, str(fx_impact_app / "src"))

from config import get_db_path
from formulas_validated import (
    calculate_impact_d,
    calculate_adjusted_empirical_score
)

print("=" * 100)
print("ANALYSE CAS PAR CAS - MÉTHODOLOGIE COMPLÈTE")
print("=" * 100)
print()

# ============================================================================
# CHARGER DATES À ANALYSER
# ============================================================================

data_dir = Path(__file__).parent / "data"
df_clusters = pd.read_csv(data_dir / "step0_selected_clusters.csv")
df_clusters['event_date'] = pd.to_datetime(df_clusters['event_date'])

print(f"✅ {len(df_clusters)} dates à analyser")
print()

# Connexion DB
db_path = get_db_path()
conn = duckdb.connect(str(db_path), read_only=True)

# ============================================================================
# FONCTIONS STRATÉGIES D'AMPLIFICATION
# ============================================================================

def amp_baseline():
    """Baseline : toujours 2.5"""
    return 2.5

def amp_surprise(max_surprise_pct):
    """Selon surprise (formule actuelle planificateur)"""
    if max_surprise_pct <= 5:
        return 1.0
    elif max_surprise_pct <= 15:
        return 1.0 + (max_surprise_pct - 5) / 10 * 1.5
    else:
        return 2.5

def amp_r2(r_squared):
    """Selon R² (hypothèse Session 102)"""
    if r_squared < 0.3:
        return 3.0  # Marché latéral
    elif r_squared < 0.6:
        return 4.2  # Sweet spot (amp_parfaite moyenne 1.70 × 2.5)
    else:
        return 2.4  # Tendance forte (amp_parfaite moyenne 0.97 × 2.5)

def amp_duration(duration_hours):
    """Selon durée"""
    if duration_hours < 5:
        return 2.4  # Court
    elif duration_hours < 15:
        return 4.3  # Moyen (sweet spot)
    else:
        return 2.3  # Long

def amp_combined(r_squared, duration_hours):
    """Combiné R² + Durée"""
    # Sweet spot
    if 0.3 <= r_squared <= 0.6 and 5 <= duration_hours <= 15:
        return 4.2
    # Zone risque
    elif r_squared > 0.7 and duration_hours < 5:
        return 2.0
    # Standard
    else:
        return 2.8

# ============================================================================
# DÉTECTION TENDANCE (AVEC INVERSIONS)
# ============================================================================

def detect_trend_with_reversals(event_date, conn):
    """
    Détecte tendance depuis dernière inversion (comme step4 corrigé)
    """
    # Charger 14 jours de données avant événement
    time_start = event_date - timedelta(days=14)
    time_end = event_date - timedelta(hours=1)
    
    query = """
    SELECT datetime, close
    FROM prices_1m
    WHERE datetime >= ? AND datetime < ?
    ORDER BY datetime ASC
    """
    
    df_prices = conn.execute(query, [time_start, time_end]).fetchdf()
    
    if len(df_prices) < 100:
        return None, None, None
    
    prices = df_prices['close'].values
    
    # Détecter inversions
    peaks, _ = signal.find_peaks(prices, prominence=0.0020)  # 20 pips
    troughs, _ = signal.find_peaks(-prices, prominence=0.0020)
    
    extrema = sorted(list(peaks) + list(troughs))
    
    if len(extrema) == 0:
        # Pas d'inversion : tendance sur 14j complets
        last_idx = 0
    else:
        # Dernière inversion
        last_idx = extrema[-1]
    
    # Tendance depuis dernière inversion
    trend_prices = prices[last_idx:]
    
    if len(trend_prices) < 10:
        return None, None, None
    
    # Régression linéaire
    x = np.arange(len(trend_prices))
    coeffs = np.polyfit(x, trend_prices, 1)
    trend_line = np.polyval(coeffs, x)
    
    # R²
    ss_res = np.sum((trend_prices - trend_line) ** 2)
    ss_tot = np.sum((trend_prices - np.mean(trend_prices)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    
    # Amplitude (pips)
    amplitude_pips = (np.max(trend_prices) - np.min(trend_prices)) * 10000
    
    # Durée (heures)
    duration_hours = len(trend_prices) / 60
    
    return r_squared, amplitude_pips, duration_hours

# ============================================================================
# ANALYSE CHAQUE CAS
# ============================================================================

print("=" * 100)
print("ANALYSE DÉTAILLÉE CHAQUE CAS")
print("=" * 100)
print()

results = []

for idx, cluster in df_clusters.iterrows():
    event_date = cluster['event_date']
    
    print(f"\n{'='*100}")
    print(f"CAS {idx+1}/22 : {event_date.strftime('%Y-%m-%d')}")
    print(f"{'='*100}")
    
    # ========================================================================
    # ÉTAPE 1 : CALCUL IMPACT AVEC PLANIFICATEUR
    # ========================================================================
    
    print(f"\n📊 ÉTAPE 1 : Calcul impact avec formules S51-55")
    
    # Charger événements
    query_events = """
    SELECT 
        e.event_key,
        e.label as family,
        e.actual,
        e.estimate,
        ef.empirical_score
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE DATE(e.ts_utc) = ?
        AND e.country = 'US'
        AND ef.empirical_score > 40
    """
    
    df_events = conn.execute(query_events, [event_date.strftime('%Y-%m-%d')]).fetchdf()
    
    if len(df_events) == 0:
        print(f"   ⚠️ Aucun événement trouvé")
        continue
    
    num_events = len(df_events)
    print(f"   Événements : {num_events}")
    
    # Calculer scores et surprises
    base_score_avg = df_events['empirical_score'].mean()
    max_surprise = 0
    
    for _, event in df_events.iterrows():
        if pd.notna(event['actual']) and pd.notna(event['estimate']) and event['estimate'] != 0:
            surprise_pct = abs((event['actual'] - event['estimate']) / event['estimate']) * 100
            if surprise_pct > max_surprise:
                max_surprise = surprise_pct
    
    # Ajuster score
    adjusted_score = calculate_adjusted_empirical_score(base_score_avg, max_surprise)
    
    # Calculer impact avec amp=2.5 (BASELINE)
    impact_predit_baseline = calculate_impact_d(
        empirical_score=adjusted_score,
        num_events=num_events,
        amplification=2.5
    )
    
    print(f"   Score base : {base_score_avg:.1f}")
    print(f"   Surprise max : {max_surprise:.1f}%")
    print(f"   Score ajusté : {adjusted_score:.1f}")
    print(f"   Impact prédit (amp=2.5) : {impact_predit_baseline:.1f} pips")
    
    # ========================================================================
    # ÉTAPE 2 : MESURER IMPACT RÉEL
    # ========================================================================
    
    print(f"\n📊 ÉTAPE 2 : Mesure impact réel")
    
    # Événements à 14:30 Berne = 12:30 UTC
    event_time_utc = event_date.replace(hour=12, minute=30)
    time_start = event_time_utc - timedelta(minutes=1)
    
    # Prix départ
    query_start = """
    SELECT close FROM prices_1m
    WHERE datetime = ?
    LIMIT 1
    """
    df_start = conn.execute(query_start, [time_start]).fetchdf()
    
    if len(df_start) == 0:
        query_start = """
        SELECT close FROM prices_1m
        WHERE datetime < ?
        ORDER BY datetime DESC
        LIMIT 1
        """
        df_start = conn.execute(query_start, [event_time_utc]).fetchdf()
    
    if len(df_start) == 0:
        print(f"   ⚠️ Pas de prix départ")
        continue
    
    price_start = df_start.iloc[0]['close']
    
    # Charger fenêtre 120 min
    time_end = event_time_utc + timedelta(minutes=120)
    
    query_window = """
    SELECT datetime, close
    FROM prices_1m
    WHERE datetime > ? AND datetime <= ?
    ORDER BY datetime ASC
    """
    
    df_prices = conn.execute(query_window, [event_time_utc, time_end]).fetchdf()
    
    if len(df_prices) == 0:
        print(f"   ⚠️ Pas de prix fenêtre")
        continue
    
    # Trouver peak
    peak_close = df_prices['close'].max()
    impact_real = abs((peak_close - price_start) * 10000)
    
    print(f"   Prix départ : {price_start:.5f}")
    print(f"   Peak : {peak_close:.5f}")
    print(f"   Impact réel : {impact_real:.1f} pips")
    
    # ========================================================================
    # ÉTAPE 3 : CALCULER AMPLIFICATION PARFAITE
    # ========================================================================
    
    print(f"\n📊 ÉTAPE 3 : Amplification parfaite")
    
    # Quelle amp aurait donné impact_real ?
    amp_parfaite = (impact_real / impact_predit_baseline) * 2.5
    
    print(f"   Amp parfaite : {amp_parfaite:.3f}")
    
    # ========================================================================
    # ÉTAPE 4 : CALCULER MÉTRIQUES TENDANCE
    # ========================================================================
    
    print(f"\n📊 ÉTAPE 4 : Métriques tendance")
    
    r2, amplitude, duration = detect_trend_with_reversals(event_date, conn)
    
    if r2 is None:
        print(f"   ⚠️ Pas assez de données pour tendance")
        continue
    
    print(f"   R² : {r2:.3f}")
    print(f"   Amplitude : {amplitude:.1f} pips")
    print(f"   Durée : {duration:.1f}h")
    
    # ========================================================================
    # ÉTAPE 6 : TESTER STRATÉGIES D'AMPLIFICATION
    # ========================================================================
    
    print(f"\n📊 ÉTAPE 6 : Test stratégies amplification")
    
    strategies = {
        'Baseline (2.5)': amp_baseline(),
        'Surprise': amp_surprise(max_surprise),
        'R²': amp_r2(r2),
        'Durée': amp_duration(duration),
        'R²+Durée': amp_combined(r2, duration)
    }
    
    errors = {}
    
    for name, amp in strategies.items():
        # Recalculer impact avec cette amp
        impact_pred = (impact_predit_baseline / 2.5) * amp
        
        # Erreur en pips
        error_pips = abs(impact_real - impact_pred)
        errors[name] = error_pips
        
        gain_vs_baseline = errors['Baseline (2.5)'] - error_pips
        status = "✅" if gain_vs_baseline > 5 else "⚠️" if gain_vs_baseline > 0 else "❌"
        
        print(f"   {status} {name:15s} : amp={amp:.2f} → impact={impact_pred:5.1f} pips, erreur={error_pips:5.1f} pips ({gain_vs_baseline:+5.1f})")
    
    # Sauvegarder résultats
    result = {
        'event_date': event_date.strftime('%Y-%m-%d'),
        'num_events': num_events,
        'max_surprise': max_surprise,
        'adjusted_score': adjusted_score,
        'impact_predit_baseline': impact_predit_baseline,
        'impact_real': impact_real,
        'amp_parfaite': amp_parfaite,
        'r_squared': r2,
        'amplitude_pips': amplitude,
        'duration_hours': duration
    }
    
    # Ajouter erreurs
    for name, error in errors.items():
        result[f'error_{name.replace(" ", "_").replace("(", "").replace(")", "").lower()}'] = error
    
    results.append(result)

conn.close()

# ============================================================================
# SAUVEGARDER RÉSULTATS
# ============================================================================

df_results = pd.DataFrame(results)
df_results.to_csv(data_dir / "analyse_complete_recalculee.csv", index=False)

print(f"\n{'='*100}")
print(f"✅ Analyse terminée : {len(results)} cas traités")
print(f"✅ Résultats : analyse_complete_recalculee.csv")
print(f"{'='*100}")

# ============================================================================
# STATISTIQUES GLOBALES
# ============================================================================

print(f"\n{'='*100}")
print("STATISTIQUES GLOBALES")
print(f"{'='*100}\n")

strategies_names = ['baseline_2.5', 'surprise', 'r²', 'durée', 'r²durée']
strategy_labels = ['Baseline (2.5)', 'Surprise', 'R²', 'Durée', 'R²+Durée']

print("MAE (pips) par stratégie :\n")

for i, name in enumerate(strategies_names):
    col = f'error_{name}'
    if col in df_results.columns:
        mae = df_results[col].mean()
        baseline_mae = df_results['error_baseline_2.5'].mean()
        improvement = ((baseline_mae - mae) / baseline_mae) * 100
        
        n_improved = (df_results['error_baseline_2.5'] - df_results[col] > 0).sum()
        
        status = "✅✅" if improvement > 15 else "✅" if improvement > 5 else "⚠️" if improvement > 0 else "❌"
        
        print(f"   {status} {strategy_labels[i]:15s} : MAE={mae:5.1f} pips ({improvement:+5.1f}%) - {n_improved}/{len(df_results)} cas améliorés")

print(f"\n{'='*100}")
print("✅ ANALYSE CAS PAR CAS TERMINÉE")
print(f"{'='*100}")
