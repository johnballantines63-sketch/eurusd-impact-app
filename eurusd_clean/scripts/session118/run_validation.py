"""
Script d'exécution validation formule S115
Session 118 - Exécution manuelle pas à pas

Auteur: André Valentin avec Claude
Date: 07 novembre 2025
"""

import sys
from pathlib import Path
import json
import duckdb
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns

# Path setup
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.cluster_impact_calculator import (
    calculate_cluster_impact,
    calculate_pullback_characteristics,
    calculate_double_wave_overlapping
)

print("=" * 80)
print("🚀 VALIDATION FORMULE S115 - SESSION 118")
print("=" * 80)

# ============================================================================
# ÉTAPE 1: CHARGEMENT DATASET
# ============================================================================
print("\n" + "=" * 80)
print("ÉTAPE 1: CHARGEMENT DATASET")
print("=" * 80)

dataset_path = project_root / 'scripts' / 'session117' / 'double_waves_enriched.json'
with open(dataset_path, 'r') as f:
    double_waves = json.load(f)

print(f"✅ Chargé {len(double_waves)} Double Wave depuis JSON")

# Filtrer cas avec events (validables)
validable_cases = [dw for dw in double_waves if dw.get('num_events', 0) > 0]
excluded_cases = [dw for dw in double_waves if dw.get('num_events', 0) == 0]

print(f"✅ {len(validable_cases)} cas avec events (validables)")
print(f"❌ {len(excluded_cases)} cas SANS events (exclus)")

if excluded_cases:
    print("\n🔴 CAS EXCLUS (patterns techniques SANS events):")
    for dw in excluded_cases:
        date = dw['baseline_time'][:10]
        impact = dw['total_impact_pips']
        print(f"   - {date}: {impact:.1f} pips")

# ============================================================================
# ÉTAPE 2: CONNEXION DATABASE
# ============================================================================
print("\n" + "=" * 80)
print("ÉTAPE 2: CONNEXION DATABASE")
print("=" * 80)

warehouse_path = project_root / 'data' / 'warehouse.duckdb'
conn = duckdb.connect(str(warehouse_path), read_only=True)
print(f"✅ Connecté à {warehouse_path.name}")

# ============================================================================
# ÉTAPE 3: VALIDATION CAS PAR CAS
# ============================================================================
print("\n" + "=" * 80)
print("ÉTAPE 3: VALIDATION FORMULE S115 SUR 13 CAS")
print("=" * 80)

results = []

for i, case in enumerate(validable_cases, 1):
    date = case['baseline_time'][:10]
    print(f"\n[{i}/{len(validable_cases)}] Validation {date}...")
    
    try:
        # Extraire timestamps
        baseline_time = pd.to_datetime(case['baseline_time'])
        peak1_time = pd.to_datetime(case['peak1_time'])
        wave2_peak_time = pd.to_datetime(case['wave2_peak_time'])
        pullback_time = pd.to_datetime(case['pullback_time'])
        
        # Impact réel MT5
        baseline_price = case['baseline_price']
        wave2_peak_price = case['wave2_peak_price']
        direction = case['direction']
        
        if direction == 'bullish':
            real_impact = (wave2_peak_price - baseline_price) * 10000
        else:
            real_impact = (baseline_price - wave2_peak_price) * 10000
        
        # Timing delta
        timing_delta_minutes = (wave2_peak_time - peak1_time).total_seconds() / 60
        
        # Filtrer events par cluster (±5 min autour des pics)
        all_events = case.get('events', [])
        
        wave1_events = []
        wave2_events = []
        
        for event in all_events:
            event_time = pd.to_datetime(event['datetime'])
            
            # Distance temporelle aux pics
            dist_peak1 = abs((event_time - peak1_time).total_seconds() / 60)
            dist_wave2 = abs((event_time - wave2_peak_time).total_seconds() / 60)
            
            # Assigner au cluster le plus proche (tolérance ±5 min)
            if dist_peak1 <= 5 and dist_peak1 <= dist_wave2:
                wave1_events.append(event)
            elif dist_wave2 <= 5:
                wave2_events.append(event)
        
        # Créer DataFrames pour formule
        wave1_df = pd.DataFrame(wave1_events) if wave1_events else pd.DataFrame()
        wave2_df = pd.DataFrame(wave2_events) if wave2_events else pd.DataFrame()
        
        # Vérifier qu'on a des events
        if wave1_df.empty or wave2_df.empty:
            print(f"   ⚠️ Events manquants - W1: {len(wave1_events)}, W2: {len(wave2_events)}")
            # Utiliser tous les events pour les 2 clusters si filtrage échoue
            wave1_df = pd.DataFrame(all_events[:len(all_events)//2])
            wave2_df = pd.DataFrame(all_events[len(all_events)//2:])
        
        # Calculer impacts clusters
        wave1_result = calculate_cluster_impact(cluster_events=wave1_df, conn=conn)
        wave2_result = calculate_cluster_impact(cluster_events=wave2_df, conn=conn)
        
        # Calculer pullback characteristics
        pullback_result = calculate_pullback_characteristics(
            peak_impact=wave1_result['impact_pips'],
            peak_surprise=wave1_result['max_surprise'],
            num_events=wave1_result['num_events'],
            has_following_cluster=True,
            minutes_to_next_cluster=int(timing_delta_minutes)
        )
        
        # Calculer impact total avec formule S115
        total_result = calculate_double_wave_overlapping(
            wave1_cluster_result=wave1_result,
            wave2_cluster_result=wave2_result,
            pullback_characteristics=pullback_result,
            timing_delta_minutes=int(timing_delta_minutes),
            wave1_time=peak1_time,
            wave2_time=wave2_peak_time
        )
        
        predicted_impact = total_result['total_impact_pips']
        mae = abs(predicted_impact - real_impact)
        
        # Stocker résultat
        result = {
            'date': date,
            'baseline_time': case['baseline_time'],
            'real_impact_pips': float(real_impact),
            'predicted_impact_pips': float(predicted_impact),
            'mae_pips': float(mae),
            'direction': direction,
            'num_events': case['num_events'],
            'wave1_impact': float(wave1_result['impact_pips']),
            'wave2_impact': float(wave2_result['impact_pips']),
            'pullback_pips': float(pullback_result['pullback_pips']),
            'momentum_factor': float(total_result['momentum_factor']),
            'extension_factor': float(total_result['extension_factor']),
            'wave1_events_count': len(wave1_events),
            'wave2_events_count': len(wave2_events),
            'timing_delta_min': float(timing_delta_minutes)
        }
        
        results.append(result)
        
        # Affichage
        print(f"   Réel:    {real_impact:.2f} pips")
        print(f"   Prédit:  {predicted_impact:.2f} pips")
        print(f"   MAE:     {mae:.2f} pips {'✅' if mae < 5 else '⚠️' if mae < 10 else '🔴'}")
        print(f"   Wave1:   {wave1_result['impact_pips']:.2f} pips ({len(wave1_events)} events)")
        print(f"   Wave2:   {wave2_result['impact_pips']:.2f} pips ({len(wave2_events)} events)")
        print(f"   Momentum: {total_result['momentum_factor']:.3f}")
        
    except Exception as e:
        print(f"   ❌ ERREUR: {str(e)}")
        import traceback
        traceback.print_exc()
        continue

print("\n" + "=" * 80)
print(f"✅ Validation complétée: {len(results)}/{len(validable_cases)} cas")
print("=" * 80)

# ============================================================================
# ÉTAPE 4: STATISTIQUES
# ============================================================================
print("\n" + "=" * 80)
print("ÉTAPE 4: STATISTIQUES VALIDATION")
print("=" * 80)

if not results:
    print("❌ Aucun résultat à analyser")
    sys.exit(1)

df = pd.DataFrame(results)

# Statistiques MAE
mae_mean = df['mae_pips'].mean()
mae_median = df['mae_pips'].median()
mae_std = df['mae_pips'].std()
mae_max = df['mae_pips'].max()
mae_min = df['mae_pips'].min()

# RMSE
rmse = np.sqrt(np.mean(df['mae_pips'] ** 2))

# R²
y_true = df['real_impact_pips']
y_pred = df['predicted_impact_pips']
ss_res = np.sum((y_true - y_pred) ** 2)
ss_tot = np.sum((y_true - y_true.mean()) ** 2)
r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

# Outliers
outliers = df[df['mae_pips'] > 10]

print(f"\n📊 STATISTIQUES GLOBALES (N={len(df)}):")
print(f"   MAE moyen:      {mae_mean:.2f} pips {'✅' if mae_mean < 5 else '⚠️'}")
print(f"   MAE médian:     {mae_median:.2f} pips")
print(f"   MAE écart-type: {mae_std:.2f} pips")
print(f"   MAE min:        {mae_min:.2f} pips")
print(f"   MAE max:        {mae_max:.2f} pips")
print(f"   RMSE:           {rmse:.2f} pips {'✅' if rmse < 7 else '⚠️'}")
print(f"   R²:             {r2:.4f} {'✅' if r2 > 0.85 else '⚠️'}")

if len(outliers) > 0:
    print(f"\n⚠️  OUTLIERS (MAE > 10 pips): {len(outliers)} cas")
    for _, row in outliers.iterrows():
        print(f"   - {row['date']}: MAE {row['mae_pips']:.2f} pips (réel {row['real_impact_pips']:.1f}, prédit {row['predicted_impact_pips']:.1f})")
else:
    print("\n✅ Aucun outlier (tous MAE < 10 pips)")

# ============================================================================
# ÉTAPE 5: SAUVEGARDER RÉSULTATS
# ============================================================================
print("\n" + "=" * 80)
print("ÉTAPE 5: SAUVEGARDE RÉSULTATS")
print("=" * 80)

output_dir = Path(__file__).parent

# JSON
results_json = {
    'metadata': {
        'session': 118,
        'date': datetime.now().isoformat(),
        'formula': 'calculate_double_wave_overlapping',
        'num_cases': len(results)
    },
    'statistics': {
        'mae_mean': float(mae_mean),
        'mae_median': float(mae_median),
        'mae_std': float(mae_std),
        'mae_min': float(mae_min),
        'mae_max': float(mae_max),
        'rmse': float(rmse),
        'r2': float(r2),
        'num_outliers': len(outliers),
        'success': mae_mean < 5.0
    },
    'results': results
}

json_path = output_dir / 'validation_results.json'
with open(json_path, 'w') as f:
    json.dump(results_json, f, indent=2)
print(f"✅ Résultats JSON: {json_path.name}")

# CSV
csv_path = output_dir / 'validation_results.csv'
df.to_csv(csv_path, index=False)
print(f"✅ Résultats CSV: {csv_path.name}")

# ============================================================================
# ÉTAPE 6: GRAPHIQUES
# ============================================================================
print("\n" + "=" * 80)
print("ÉTAPE 6: GÉNÉRATION GRAPHIQUES")
print("=" * 80)

plots_dir = output_dir / 'validation_plots'
plots_dir.mkdir(exist_ok=True)

sns.set_style("whitegrid")

# GRAPHIQUE 1: Prédit vs Réel
fig, ax = plt.subplots(figsize=(10, 10))
ax.scatter(df['real_impact_pips'], df['predicted_impact_pips'], 
          s=100, alpha=0.6, edgecolors='black', linewidths=1.5)

min_val = min(df['real_impact_pips'].min(), df['predicted_impact_pips'].min())
max_val = max(df['real_impact_pips'].max(), df['predicted_impact_pips'].max())
ax.plot([min_val, max_val], [min_val, max_val], 
       'r--', linewidth=2, label='Prédiction parfaite')

ax.set_xlabel('Impact réel MT5 (pips)', fontsize=12, fontweight='bold')
ax.set_ylabel('Impact prédit S115 (pips)', fontsize=12, fontweight='bold')
ax.set_title(f'Formule S115: Prédiction vs Réalité (13 cas)\nMAE moyen: {mae_mean:.2f} pips, R²: {r2:.4f}', 
            fontsize=14, fontweight='bold')
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(plots_dir / 'predicted_vs_real.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"   ✅ predicted_vs_real.png")

# GRAPHIQUE 2: Distribution MAE
fig, ax = plt.subplots(figsize=(10, 6))
ax.hist(df['mae_pips'], bins=12, edgecolor='black', alpha=0.7, color='steelblue')
ax.axvline(mae_mean, color='red', linestyle='--', 
          linewidth=2, label=f'MAE moyen: {mae_mean:.2f} pips')
ax.axvline(5, color='green', linestyle='--', 
          linewidth=2, label='Objectif: 5 pips')

ax.set_xlabel('MAE (pips)', fontsize=12, fontweight='bold')
ax.set_ylabel('Fréquence', fontsize=12, fontweight='bold')
ax.set_title('Distribution MAE - Formule S115 (13 cas)', fontsize=14, fontweight='bold')
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(plots_dir / 'mae_distribution.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"   ✅ mae_distribution.png")

# GRAPHIQUE 3: MAE par date
fig, ax = plt.subplots(figsize=(14, 6))
dates = df['date'].tolist()
maes = df['mae_pips'].tolist()

colors = ['green' if mae < 5 else 'orange' if mae < 10 else 'red' for mae in maes]
bars = ax.bar(range(len(dates)), maes, color=colors, edgecolor='black', linewidth=1.5)

ax.axhline(5, color='green', linestyle='--', linewidth=2, alpha=0.7, label='Objectif: 5 pips')
ax.axhline(mae_mean, color='red', linestyle='--', 
          linewidth=2, alpha=0.7, label=f'MAE moyen: {mae_mean:.2f} pips')

ax.set_xlabel('Date', fontsize=12, fontweight='bold')
ax.set_ylabel('MAE (pips)', fontsize=12, fontweight='bold')
ax.set_title('MAE par Date - Formule S115', fontsize=14, fontweight='bold')
ax.set_xticks(range(len(dates)))
ax.set_xticklabels(dates, rotation=45, ha='right')
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(plots_dir / 'mae_by_date.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"   ✅ mae_by_date.png")

print(f"\n✅ 3 graphiques créés dans {plots_dir.name}/")

# ============================================================================
# RÉSUMÉ FINAL
# ============================================================================
print("\n" + "=" * 80)
print("🎉 VALIDATION COMPLÉTÉE")
print("=" * 80)
print(f"✅ {len(results)} cas testés")
print(f"✅ MAE moyen: {mae_mean:.2f} pips {'✅ SUCCÈS' if mae_mean < 5 else '⚠️ AJUSTEMENTS NÉCESSAIRES'}")
print(f"✅ RMSE: {rmse:.2f} pips")
print(f"✅ R²: {r2:.4f}")
print(f"✅ Outliers: {len(outliers)}")
print(f"✅ Fichiers créés:")
print(f"   - validation_results.json")
print(f"   - validation_results.csv")
print(f"   - validation_plots/ (3 PNG)")
print("=" * 80)

conn.close()
