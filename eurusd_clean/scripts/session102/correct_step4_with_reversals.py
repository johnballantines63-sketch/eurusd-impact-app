#!/usr/bin/env python3
"""
CORRECTION ÉTAPE 4 : DÉTECTION TENDANCES AVEC INVERSIONS
=========================================================

Méthodologie correcte :
1. Charger 14 jours de prix avant événement
2. Détecter extrema (peaks et troughs)
3. Identifier dernière inversion majeure
4. Calculer tendance DEPUIS inversion → événement
5. Durée = Temps depuis inversion (PAS 14 jours fixes !)
"""

import sys
from pathlib import Path
import duckdb
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from scipy import stats
from scipy.signal import find_peaks

# Chemins
project_root = Path(__file__).resolve().parents[2]
fx_impact_app = project_root.parent / "fx_impact_app"
sys.path.insert(0, str(fx_impact_app / "src"))

from config import get_db_path

print("=" * 80)
print("CORRECTION ÉTAPE 4 : DÉTECTION TENDANCES AVEC INVERSIONS")
print("=" * 80)
print()

# ============================================================================
# FONCTIONS DÉTECTION INVERSIONS
# ============================================================================

def detect_extrema(prices, prominence_pips=20):
    """
    Détecte peaks et troughs dans série de prix
    
    prominence_pips : Prominence minimum en pips (20 pips = changement significatif)
    """
    prices_pips = prices * 10000  # Convertir en pips
    
    # Détecter peaks (maxima locaux)
    peaks, _ = find_peaks(prices_pips, prominence=prominence_pips)
    
    # Détecter troughs (minima locaux) = peaks de -prices
    troughs, _ = find_peaks(-prices_pips, prominence=prominence_pips)
    
    return peaks, troughs


def find_last_major_reversal(df_prices, prominence_pips=20):
    """
    Trouve la dernière inversion majeure avant l'événement
    
    Returns:
        reversal_idx : Index de la dernière inversion
        reversal_type : 'peak' ou 'trough'
        reversal_time : Datetime de l'inversion
        duration_hours : Durée depuis inversion (heures)
        trend_direction : 'up' ou 'down' depuis inversion
    """
    if len(df_prices) < 50:
        return None
    
    prices = df_prices['close'].values
    
    # Détecter extrema
    peaks, troughs = detect_extrema(prices, prominence_pips)
    
    # Fusionner tous les extrema avec leur type
    extrema = []
    for idx in peaks:
        extrema.append({'idx': idx, 'type': 'peak', 'price': prices[idx]})
    for idx in troughs:
        extrema.append({'idx': idx, 'type': 'trough', 'price': prices[idx]})
    
    # Trier par index (ordre chronologique)
    extrema = sorted(extrema, key=lambda x: x['idx'])
    
    if len(extrema) < 2:
        # Pas assez d'extrema, prendre début de période
        return {
            'reversal_idx': 0,
            'reversal_type': 'start',
            'reversal_time': df_prices.iloc[0]['datetime'],
            'duration_hours': (df_prices.iloc[-1]['datetime'] - df_prices.iloc[0]['datetime']).total_seconds() / 3600,
            'trend_direction': 'up' if prices[-1] > prices[0] else 'down',
            'extrema_count': len(extrema)
        }
    
    # Prendre le DERNIER extremum comme point d'inversion
    last_extremum = extrema[-1]
    reversal_idx = last_extremum['idx']
    reversal_type = last_extremum['type']
    
    # Calculer durée depuis inversion
    reversal_time = df_prices.iloc[reversal_idx]['datetime']
    event_time = df_prices.iloc[-1]['datetime']
    duration_hours = (event_time - reversal_time).total_seconds() / 3600
    
    # Direction de la tendance depuis inversion
    if reversal_type == 'peak':
        trend_direction = 'down'  # Depuis un peak, on descend
    else:
        trend_direction = 'up'    # Depuis un trough, on monte
    
    return {
        'reversal_idx': reversal_idx,
        'reversal_type': reversal_type,
        'reversal_time': reversal_time,
        'duration_hours': duration_hours,
        'trend_direction': trend_direction,
        'extrema_count': len(extrema)
    }


# ============================================================================
# CHARGER DONNÉES
# ============================================================================

data_dir = Path(__file__).parent / "data"
df_step1 = pd.read_csv(data_dir / "step1_impacts_predits.csv")
df_step1['event_date'] = pd.to_datetime(df_step1['event_date'])

db_path = get_db_path()
conn = duckdb.connect(str(db_path), read_only=True)

print(f"✅ Chargé {len(df_step1)} événements")
print()

# ============================================================================
# RECALCULER TENDANCES AVEC INVERSIONS
# ============================================================================

print("=" * 80)
print("RECALCUL TENDANCES (avec détection inversions)")
print("=" * 80)
print()

results_corrected = []

for idx, row in df_step1.iterrows():
    event_date = pd.to_datetime(row['event_date'])
    event_time_utc = event_date.replace(hour=12, minute=30)
    
    # Période 14 jours avant
    start_period = event_time_utc - timedelta(days=14)
    
    # Charger prix période
    query_period = """
    SELECT datetime, close
    FROM prices_1m
    WHERE datetime >= ?
      AND datetime < ?
    ORDER BY datetime ASC
    """
    
    df_period = conn.execute(query_period, [start_period, event_time_utc]).fetchdf()
    
    if len(df_period) < 100:
        print(f"⚠️ {event_date.strftime('%Y-%m-%d')} : Pas assez de données")
        continue
    
    # Convertir datetime
    df_period['datetime'] = pd.to_datetime(df_period['datetime'])
    if hasattr(df_period['datetime'].iloc[0], 'tz') and df_period['datetime'].iloc[0].tz is not None:
        df_period['datetime'] = df_period['datetime'].dt.tz_localize(None)
    
    # DÉTECTER DERNIÈRE INVERSION
    reversal_info = find_last_major_reversal(df_period, prominence_pips=20)
    
    if reversal_info is None:
        continue
    
    # Extraire segment DEPUIS inversion jusqu'à événement
    reversal_idx = reversal_info['reversal_idx']
    df_trend = df_period.iloc[reversal_idx:].copy()
    
    # Calculer R² sur CE segment seulement
    df_trend['time_numeric'] = range(len(df_trend))
    
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        df_trend['time_numeric'],
        df_trend['close']
    )
    
    r_squared = r_value ** 2
    
    # Amplitude du mouvement DEPUIS inversion
    amplitude_pips = (df_trend['close'].max() - df_trend['close'].min()) * 10000
    
    # Durée RÉELLE depuis inversion
    duration_hours = reversal_info['duration_hours']
    
    results_corrected.append({
        'event_date': event_date,
        'r_squared': r_squared,
        'slope': slope,
        'amplitude_pips': amplitude_pips,
        'duration_hours': duration_hours,  # ← CORRIGÉ : durée variable !
        'p_value': p_value,
        'reversal_type': reversal_info['reversal_type'],
        'trend_direction': reversal_info['trend_direction'],
        'extrema_count': reversal_info['extrema_count'],
        'reversal_time': reversal_info['reversal_time']
    })
    
    if idx < 5:
        print(f"✅ {event_date.strftime('%Y-%m-%d')}")
        print(f"   R²={r_squared:.3f}, Amp={amplitude_pips:.0f} pips, Durée={duration_hours:.1f}h")
        print(f"   Dernière inversion : {reversal_info['reversal_type']} ({reversal_info['extrema_count']} extrema)")
        print()

print(f"✅ Recalculé {len(results_corrected)} tendances (avec inversions)")
print()

conn.close()

# ============================================================================
# SAUVEGARDER
# ============================================================================

df_corrected = pd.DataFrame(results_corrected)
df_corrected.to_csv(data_dir / "step4_tendances_CORRECTED.csv", index=False)

print(f"✅ Sauvegardé : step4_tendances_CORRECTED.csv")
print()

# ============================================================================
# COMPARAISON AVANT/APRÈS
# ============================================================================

print("=" * 80)
print("COMPARAISON AVANT/APRÈS CORRECTION")
print("=" * 80)
print()

df_old = pd.read_csv(data_dir / "step4_tendances_detectees.csv")

print("AVANT (incorrect) :")
print(f"   Durée moyenne : {df_old['duration_hours'].mean():.1f}h")
print(f"   Durée std     : {df_old['duration_hours'].std():.1f}h")
print(f"   Durée min     : {df_old['duration_hours'].min():.1f}h")
print(f"   Durée max     : {df_old['duration_hours'].max():.1f}h")
print()

print("APRÈS (corrigé) :")
print(f"   Durée moyenne : {df_corrected['duration_hours'].mean():.1f}h")
print(f"   Durée std     : {df_corrected['duration_hours'].std():.1f}h")
print(f"   Durée min     : {df_corrected['duration_hours'].min():.1f}h")
print(f"   Durée max     : {df_corrected['duration_hours'].max():.1f}h")
print()

print("Statistiques durées corrigées :")
print(df_corrected['duration_hours'].describe())
print()

# ============================================================================
# RECALCULER CORRÉLATIONS
# ============================================================================

print("=" * 80)
print("RECALCUL CORRÉLATIONS (avec durées corrigées)")
print("=" * 80)
print()

# Fusionner avec amplifications
df_amp = pd.read_csv(data_dir / "step3_amplifications_parfaites.csv")
df_amp['event_date'] = pd.to_datetime(df_amp['event_date'])

df_final_corrected = df_amp.merge(df_corrected, on='event_date')

# Nouvelles corrélations
corr_r2 = df_final_corrected['amp_parfaite'].corr(df_final_corrected['r_squared'])
corr_amplitude = df_final_corrected['amp_parfaite'].corr(df_final_corrected['amplitude_pips'])
corr_duration = df_final_corrected['amp_parfaite'].corr(df_final_corrected['duration_hours'])

print("CORRÉLATIONS AMP_PARFAITE vs TENDANCE (CORRIGÉES) :")
print(f"   vs R² (force tendance)    : {corr_r2:+.3f}")
print(f"   vs Amplitude (pips)       : {corr_amplitude:+.3f}")
print(f"   vs Durée (heures)         : {corr_duration:+.3f}  ← NOUVEAU CALCUL")
print()

# Sauvegarder analyse finale corrigée
df_final_corrected.to_csv(data_dir / "step5_analyse_finale_CORRECTED.csv", index=False)

print(f"✅ Analyse finale corrigée : step5_analyse_finale_CORRECTED.csv")
print()

# ============================================================================
# CONCLUSIONS
# ============================================================================

print("=" * 80)
print("CONCLUSIONS (avec correction)")
print("=" * 80)
print()

print(f"Hypothèse testée :")
print(f"   'Tendance forte (R² élevé) → Amplification faible'")
print()

if corr_r2 < -0.3:
    print(f"✅✅ HYPOTHÈSE VALIDÉE (corrélation négative forte : {corr_r2:+.3f})")
elif corr_r2 < -0.1:
    print(f"✅ HYPOTHÈSE PARTIELLEMENT VALIDÉE (corrélation négative modérée : {corr_r2:+.3f})")
elif abs(corr_r2) < 0.1:
    print(f"⚠️ PAS DE CORRÉLATION SIGNIFICATIVE ({corr_r2:+.3f})")
else:
    print(f"❌ HYPOTHÈSE RÉFUTÉE (corrélation positive : {corr_r2:+.3f})")

print()

if abs(corr_duration) > 0.3:
    print(f"💡 DÉCOUVERTE : Corrélation significative avec DURÉE tendance ({corr_duration:+.3f})")
    if corr_duration > 0:
        print(f"   → Tendance longue → Amplification forte")
    else:
        print(f"   → Tendance courte → Amplification forte")

print()
print("=" * 80)
print("✅ CORRECTION TERMINÉE")
print("=" * 80)
