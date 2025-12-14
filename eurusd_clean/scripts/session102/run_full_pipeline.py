#!/usr/bin/env python3
"""
PIPELINE COMPLET : ANALYSE AMPLIFICATION vs TENDANCE
=====================================================

Exécute toutes les étapes de l'analyse sur les 22 clusters sélectionnés :

ÉTAPE 1 : Calculer impacts prédits (amp=2.5, formules S51-55)
ÉTAPE 2 : Mesurer impacts réels (prices_1m, UTC timezone)
ÉTAPE 3 : Calculer amplifications parfaites
ÉTAPE 4 : Détecter tendances dynamiques (14 jours avant)
ÉTAPE 5 : Analyser corrélations amp_parfaite vs tendance

Hypothèse testée :
"Tendance forte (R² élevé) → Amplification faible (corrélation NÉGATIVE)"
"""

import sys
from pathlib import Path
import duckdb
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt

# Chemins
project_root = Path(__file__).resolve().parents[2]
fx_impact_app = project_root.parent / "fx_impact_app"
sys.path.insert(0, str(fx_impact_app / "src"))

from config import get_db_path
from formulas_validated import (
    calculate_impact_d,
    calculate_adjusted_empirical_score
)

print("=" * 80)
print("PIPELINE COMPLET : ANALYSE AMPLIFICATION vs TENDANCE")
print("=" * 80)
print()

# ============================================================================
# CHARGER CLUSTERS SÉLECTIONNÉS
# ============================================================================

data_dir = Path(__file__).parent / "data"
clusters_path = data_dir / "step0_selected_clusters.csv"

if not clusters_path.exists():
    print(f"❌ Fichier non trouvé : {clusters_path}")
    print(f"   → Exécuter d'abord : step0_extract_30_clusters.py")
    sys.exit(1)

df_clusters = pd.read_csv(clusters_path)
print(f"✅ Chargé {len(df_clusters)} clusters depuis {clusters_path.name}")
print()

# Connexion DB
db_path = get_db_path()
conn = duckdb.connect(str(db_path), read_only=True)

# ============================================================================
# ÉTAPE 1 : CALCUL IMPACTS PRÉDITS
# ============================================================================

print("=" * 80)
print("ÉTAPE 1 : CALCUL IMPACTS PRÉDITS (amp=2.5)")
print("=" * 80)
print()

results_step1 = []

for idx, cluster in df_clusters.iterrows():
    event_date = pd.to_datetime(cluster['event_date'])
    
    # Charger événements du jour
    query_events = """
    SELECT 
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
        continue
    
    # Calculer score moyen et surprise max
    base_score_avg = df_events['empirical_score'].mean()
    
    surprises = []
    max_surprise = 0
    for _, event in df_events.iterrows():
        if pd.notna(event['actual']) and pd.notna(event['estimate']) and event['estimate'] != 0:
            surprise_pct = abs((event['actual'] - event['estimate']) / event['estimate']) * 100
            surprises.append(surprise_pct)
            if surprise_pct > max_surprise:
                max_surprise = surprise_pct
    
    # Ajuster score
    adjusted_score = calculate_adjusted_empirical_score(base_score_avg, max_surprise)
    
    # Calculer impact avec amp=2.5
    impact_predit = calculate_impact_d(
        empirical_score=adjusted_score,
        num_events=len(df_events),
        amplification=2.5
    )
    
    results_step1.append({
        'event_date': event_date,
        'num_events': len(df_events),
        'base_score': base_score_avg,
        'max_surprise': max_surprise,
        'adjusted_score': adjusted_score,
        'impact_predit': impact_predit
    })
    
    if idx < 3:
        print(f"✅ {event_date.strftime('%Y-%m-%d')} : {len(df_events)} events → {impact_predit:.1f} pips")

print(f"\n✅ Calculé {len(results_step1)} impacts prédits")
print()

df_step1 = pd.DataFrame(results_step1)
df_step1.to_csv(data_dir / "step1_impacts_predits.csv", index=False)

# ============================================================================
# ÉTAPE 2 : MESURE IMPACTS RÉELS (UTC TIMEZONE !)
# ============================================================================

print("=" * 80)
print("ÉTAPE 2 : MESURE IMPACTS RÉELS (UTC)")
print("=" * 80)
print()

results_step2 = []

for idx, row in df_step1.iterrows():
    event_date = pd.to_datetime(row['event_date'])
    
    # IMPORTANT : Événements à 14:30 Berne = 12:30 UTC
    event_time_utc = event_date.replace(hour=12, minute=30)
    
    # Prix départ : 12:29 UTC
    time_start = event_time_utc - timedelta(minutes=1)
    
    query_start = """
    SELECT datetime, close
    FROM prices_1m
    WHERE datetime = ?
    LIMIT 1
    """
    
    df_start = conn.execute(query_start, [time_start]).fetchdf()
    
    if len(df_start) == 0:
        # Fallback : dernier prix avant événement
        query_start = """
        SELECT datetime, close
        FROM prices_1m
        WHERE datetime < ?
        ORDER BY datetime DESC
        LIMIT 1
        """
        df_start = conn.execute(query_start, [event_time_utc]).fetchdf()
    
    if len(df_start) == 0:
        print(f"⚠️ {event_date.strftime('%Y-%m-%d')} : Pas de prix départ")
        continue
    
    price_start = df_start.iloc[0]['close']
    
    # Charger prix fenêtre 120 min après événement
    time_end = event_time_utc + timedelta(minutes=120)
    
    query_window = """
    SELECT datetime, close
    FROM prices_1m
    WHERE datetime > ?
      AND datetime <= ?
    ORDER BY datetime ASC
    """
    
    df_prices = conn.execute(query_window, [event_time_utc, time_end]).fetchdf()
    
    if len(df_prices) == 0:
        print(f"⚠️ {event_date.strftime('%Y-%m-%d')} : Pas de prix fenêtre")
        continue
    
    # Trouver peak CLOSE
    max_close = df_prices['close'].max()
    min_close = df_prices['close'].min()
    
    movement_up = (max_close - price_start) * 10000
    movement_down = (price_start - min_close) * 10000
    
    # Impact = plus grand mouvement
    if movement_up > movement_down:
        impact_real = movement_up
        direction = "UP"
        idx_peak = df_prices['close'].idxmax()
    else:
        impact_real = movement_down
        direction = "DOWN"
        idx_peak = df_prices['close'].idxmin()
    
    peak_time = df_prices.loc[idx_peak, 'datetime']
    peak_time_dt = pd.to_datetime(peak_time)
    
    # TTR en minutes
    if hasattr(peak_time_dt, 'tz') and peak_time_dt.tz is not None:
        peak_time_dt = peak_time_dt.tz_localize(None)
    
    ttr_minutes = (peak_time_dt - event_time_utc).total_seconds() / 60
    
    results_step2.append({
        'event_date': event_date,
        'price_start': price_start,
        'impact_real': impact_real,
        'direction': direction,
        'peak_time': peak_time,
        'ttr_minutes': ttr_minutes
    })
    
    if idx < 3:
        print(f"✅ {event_date.strftime('%Y-%m-%d')} : {impact_real:.1f} pips {direction}")

print(f"\n✅ Mesuré {len(results_step2)} impacts réels")
print()

df_step2 = pd.DataFrame(results_step2)
df_step2.to_csv(data_dir / "step2_impacts_reels.csv", index=False)

# ============================================================================
# ÉTAPE 3 : CALCUL AMPLIFICATIONS PARFAITES
# ============================================================================

print("=" * 80)
print("ÉTAPE 3 : CALCUL AMPLIFICATIONS PARFAITES")
print("=" * 80)
print()

# Fusionner step1 et step2
df_step3 = df_step1.merge(df_step2, on='event_date')

# Calculer amp_parfaite
df_step3['amp_parfaite'] = df_step3['impact_real'] / df_step3['impact_predit']
df_step3['erreur_pips'] = abs(df_step3['impact_real'] - df_step3['impact_predit'])
df_step3['erreur_pct'] = (df_step3['erreur_pips'] / df_step3['impact_real']) * 100

print(f"✅ Calculé {len(df_step3)} amplifications parfaites")
print()

print("Statistiques amp_parfaite :")
print(df_step3['amp_parfaite'].describe())
print()

df_step3.to_csv(data_dir / "step3_amplifications_parfaites.csv", index=False)

# ============================================================================
# ÉTAPE 4 : DÉTECTION TENDANCES DYNAMIQUES
# ============================================================================

print("=" * 80)
print("ÉTAPE 4 : DÉTECTION TENDANCES (14 jours avant)")
print("=" * 80)
print()

results_step4 = []

for idx, row in df_step3.iterrows():
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
    
    # Calculer tendance linéaire
    df_period['time_numeric'] = range(len(df_period))
    
    # Régression linéaire
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        df_period['time_numeric'],
        df_period['close']
    )
    
    r_squared = r_value ** 2
    
    # Amplitude mouvement (high - low sur période)
    amplitude_pips = (df_period['close'].max() - df_period['close'].min()) * 10000
    
    # Durée en heures
    duration_hours = (df_period['datetime'].max() - df_period['datetime'].min()).total_seconds() / 3600
    
    results_step4.append({
        'event_date': event_date,
        'r_squared': r_squared,
        'slope': slope,
        'amplitude_pips': amplitude_pips,
        'duration_hours': duration_hours,
        'p_value': p_value
    })
    
    if idx < 3:
        print(f"✅ {event_date.strftime('%Y-%m-%d')} : R²={r_squared:.3f}, Amp={amplitude_pips:.1f} pips")

print(f"\n✅ Détecté {len(results_step4)} tendances")
print()

df_step4 = pd.DataFrame(results_step4)
df_step4.to_csv(data_dir / "step4_tendances_detectees.csv", index=False)

# ============================================================================
# ÉTAPE 5 : ANALYSE CORRÉLATIONS
# ============================================================================

print("=" * 80)
print("ÉTAPE 5 : ANALYSE CORRÉLATIONS")
print("=" * 80)
print()

# Fusionner toutes les données
df_final = df_step3.merge(df_step4, on='event_date')

print(f"✅ {len(df_final)} observations complètes")
print()

# Calculer corrélations
corr_r2 = df_final['amp_parfaite'].corr(df_final['r_squared'])
corr_amplitude = df_final['amp_parfaite'].corr(df_final['amplitude_pips'])
corr_duration = df_final['amp_parfaite'].corr(df_final['duration_hours'])

print("CORRÉLATIONS AMP_PARFAITE vs TENDANCE :")
print(f"   vs R² (force tendance)    : {corr_r2:+.3f}")
print(f"   vs Amplitude (pips)       : {corr_amplitude:+.3f}")
print(f"   vs Durée (heures)         : {corr_duration:+.3f}")
print()

# Sauvegarder
df_final.to_csv(data_dir / "step5_analyse_finale.csv", index=False)

# ============================================================================
# GRAPHIQUES
# ============================================================================

print("=" * 80)
print("GÉNÉRATION GRAPHIQUES")
print("=" * 80)
print()

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Analyse Amplification vs Tendance', fontsize=16)

# Graph 1 : Amp vs R²
axes[0, 0].scatter(df_final['r_squared'], df_final['amp_parfaite'], alpha=0.6)
axes[0, 0].set_xlabel('R² (Force Tendance)')
axes[0, 0].set_ylabel('Amplification Parfaite')
axes[0, 0].set_title(f'Corrélation : {corr_r2:+.3f}')
axes[0, 0].grid(True, alpha=0.3)

# Ligne tendance
z = np.polyfit(df_final['r_squared'], df_final['amp_parfaite'], 1)
p = np.poly1d(z)
axes[0, 0].plot(df_final['r_squared'], p(df_final['r_squared']), "r--", alpha=0.5)

# Graph 2 : Amp vs Amplitude
axes[0, 1].scatter(df_final['amplitude_pips'], df_final['amp_parfaite'], alpha=0.6)
axes[0, 1].set_xlabel('Amplitude Tendance (pips)')
axes[0, 1].set_ylabel('Amplification Parfaite')
axes[0, 1].set_title(f'Corrélation : {corr_amplitude:+.3f}')
axes[0, 1].grid(True, alpha=0.3)

# Graph 3 : Amp vs Durée
axes[1, 0].scatter(df_final['duration_hours'], df_final['amp_parfaite'], alpha=0.6)
axes[1, 0].set_xlabel('Durée Tendance (heures)')
axes[1, 0].set_ylabel('Amplification Parfaite')
axes[1, 0].set_title(f'Corrélation : {corr_duration:+.3f}')
axes[1, 0].grid(True, alpha=0.3)

# Graph 4 : Distribution Amp_parfaite
axes[1, 1].hist(df_final['amp_parfaite'], bins=15, alpha=0.7, edgecolor='black')
axes[1, 1].axvline(df_final['amp_parfaite'].mean(), color='r', linestyle='--', label=f'Moyenne: {df_final["amp_parfaite"].mean():.3f}')
axes[1, 1].set_xlabel('Amplification Parfaite')
axes[1, 1].set_ylabel('Fréquence')
axes[1, 1].set_title('Distribution Amplifications')
axes[1, 1].legend()
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
graph_path = data_dir / "step5_graphiques_correlations.png"
plt.savefig(graph_path, dpi=150)
print(f"✅ Graphiques sauvegardés : {graph_path}")
print()

conn.close()

# ============================================================================
# CONCLUSIONS
# ============================================================================

print("=" * 80)
print("CONCLUSIONS")
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
print("Fichiers générés :")
print(f"   - step1_impacts_predits.csv")
print(f"   - step2_impacts_reels.csv")
print(f"   - step3_amplifications_parfaites.csv")
print(f"   - step4_tendances_detectees.csv")
print(f"   - step5_analyse_finale.csv")
print(f"   - step5_graphiques_correlations.png")

print()
print("=" * 80)
print("✅ PIPELINE TERMINÉ")
print("=" * 80)
