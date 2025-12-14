#!/usr/bin/env python3
"""
Diagnostic complet direction V3 - Étape A puis B

Étape A : Tester grille de seuils θ pour trouver compromis coverage/accuracy/F1
Étape B : Diagnostiquer scores S proches de 0 (distribution, contributions, signe)
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import json
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, balanced_accuracy_score
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

BASE_DIR = Path(__file__).parent.parent / 'outputs'
RESULTS_FILE = BASE_DIR / 'validation_new_dates_results.csv'
ALPHA_WEIGHTS_FILE = BASE_DIR / 'alpha_weights.csv'
EVENTS_FILE = BASE_DIR / 'events.csv'
DIRECTION_THRESHOLDS_FILE = BASE_DIR / 'direction_thresholds.json'

# Import des fonctions du pipeline
from validate_on_new_dates import (
    load_alpha_map, load_surprise_stats, predict_direction_empirical,
    load_events_for_date
)
import duckdb
from datetime import datetime

DB_PATH = Path(__file__).parent.parent.parent.parent / 'fx_impact_app' / 'data' / 'warehouse.duckdb'

# ============================================================================
# ÉTAPE A : GRILLE DE SEUILS θ
# ============================================================================

def test_theta_grid():
    """Teste grille de seuils θ et calcule métriques"""
    print("="*80)
    print("ÉTAPE A : TEST GRILLE DE SEUILS θ")
    print("="*80)
    print()
    
    # Charger résultats existants ou recalculer
    if RESULTS_FILE.exists():
        df_results = pd.read_csv(RESULTS_FILE)
        print(f"✅ {len(df_results)} résultats chargés depuis {RESULTS_FILE.name}")
    else:
        print("❌ Fichier de résultats introuvable")
        return None
    
    # Charger alpha et stats
    alpha_map = load_alpha_map(horizon='1h')
    stats_map = load_surprise_stats()
    
    print(f"✅ Alpha map : {len(alpha_map)} événements")
    print(f"✅ Stats surprise : {len(stats_map)} événements")
    print()
    
    # Recalculer scores S pour toutes les dates
    print("📊 Recalcul des scores S pour toutes les dates...")
    scores_S = []
    directions_real = []
    dates_list = []
    
    for _, row in df_results.iterrows():
        date_str = row['date']
        dates_list.append(date_str)
        
        # Charger événements
        events_df = load_events_for_date(date_str)
        if len(events_df) > 0:
            # Calculer S
            direction_pred, S, method = predict_direction_empirical(
                events_df, alpha_map, stats_map, theta=0.0  # Pas de seuil pour obtenir S brut
            )
            scores_S.append(S)
            directions_real.append(row['direction_real'])
        else:
            scores_S.append(0.0)
            directions_real.append(row['direction_real'])
    
    scores_S = np.array(scores_S)
    directions_real = np.array(directions_real)
    
    print(f"   ✅ {len(scores_S)} scores S calculés")
    print()
    
    # Grille de seuils (ajout de 0.03, 0.04 pour plus de granularité autour de 0.05)
    theta_grid = [0.00, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10, 0.12]
    
    print("="*80)
    print("📊 RÉSULTATS PAR SEUIL θ")
    print("="*80)
    print()
    
    results_theta = []
    
    for theta in theta_grid:
        # Appliquer seuil
        predictions = []
        for S in scores_S:
            if S > theta:
                pred = 'UP'
            elif S < -theta:
                pred = 'DOWN'
            else:
                pred = 'UNKNOWN'
            predictions.append(pred)
        
        predictions = np.array(predictions)
        mask = predictions != 'UNKNOWN'
        
        if mask.sum() > 0:
            y_true = directions_real[mask]
            y_pred = predictions[mask]
            
            y_true_bin = (y_true == 'UP').astype(int)
            y_pred_bin = (y_pred == 'UP').astype(int)
            
            accuracy = accuracy_score(y_true_bin, y_pred_bin) * 100
            balanced_acc = balanced_accuracy_score(y_true_bin, y_pred_bin) * 100
            f1_macro = f1_score(y_true_bin, y_pred_bin, average='macro', zero_division=0) * 100
            f1_up = f1_score(y_true_bin, y_pred_bin, pos_label=1, zero_division=0) * 100
            f1_down = f1_score(y_true_bin, y_pred_bin, pos_label=0, zero_division=0) * 100
            
            coverage = (mask.sum() / len(predictions)) * 100
            
            # Confusion matrix
            cm = confusion_matrix(y_true_bin, y_pred_bin)
            if cm.shape == (2, 2):
                tp, fn = cm[1, 1], cm[1, 0]
                fp, tn = cm[0, 1], cm[0, 0]
            else:
                tp = fp = fn = tn = 0
            
            results_theta.append({
                'theta': theta,
                'coverage': coverage,
                'n_valid': mask.sum(),
                'n_total': len(predictions),
                'accuracy': accuracy,
                'balanced_accuracy': balanced_acc,
                'f1_macro': f1_macro,
                'f1_up': f1_up,
                'f1_down': f1_down,
                'tp': tp,
                'fp': fp,
                'fn': fn,
                'tn': tn
            })
        else:
            results_theta.append({
                'theta': theta,
                'coverage': 0.0,
                'n_valid': 0,
                'n_total': len(predictions),
                'accuracy': 0.0,
                'balanced_accuracy': 0.0,
                'f1_macro': 0.0,
                'f1_up': 0.0,
                'f1_down': 0.0,
                'tp': 0, 'fp': 0, 'fn': 0, 'tn': 0
            })
    
    df_theta = pd.DataFrame(results_theta)
    
    # Afficher résultats
    print(f"{'θ':<8} {'Coverage':<12} {'Accuracy':<12} {'Bal.Acc':<12} {'F1 Macro':<12} {'F1 UP':<12} {'F1 DOWN':<12}")
    print("-" * 80)
    for _, row in df_theta.iterrows():
        print(f"{row['theta']:<8.2f} {row['coverage']:<12.1f} {row['accuracy']:<12.1f} {row['balanced_accuracy']:<12.1f} "
              f"{row['f1_macro']:<12.1f} {row['f1_up']:<12.1f} {row['f1_down']:<12.1f}")
    print()
    
    # Matrices de confusion
    print("="*80)
    print("📊 MATRICES DE CONFUSION PAR SEUIL")
    print("="*80)
    print()
    
    for theta in theta_grid:
        row = df_theta[df_theta['theta'] == theta].iloc[0]
        if row['n_valid'] > 0:
            print(f"θ = {theta:.2f} (Coverage: {row['coverage']:.1f}%)")
            print(f"   TP={int(row['tp']):2d}  FP={int(row['fp']):2d}")
            print(f"   FN={int(row['fn']):2d}  TN={int(row['tn']):2d}")
            print()
    
    # Trouver meilleur compromis
    print("="*80)
    print("💡 ANALYSE & RECOMMANDATION")
    print("="*80)
    print()
    
    # Score composite : accuracy × coverage (normalisé)
    df_theta['composite_score'] = df_theta['accuracy'] * (df_theta['coverage'] / 100)
    best_composite = df_theta.loc[df_theta['composite_score'].idxmax()]
    
    print(f"⭐ Meilleur compromis (accuracy × coverage) :")
    print(f"   θ = {best_composite['theta']:.2f}")
    print(f"   Coverage : {best_composite['coverage']:.1f}%")
    print(f"   Accuracy : {best_composite['accuracy']:.1f}%")
    print(f"   Balanced Accuracy : {best_composite['balanced_accuracy']:.1f}%")
    print(f"   F1 Macro : {best_composite['f1_macro']:.1f}%")
    print()
    
    # Interprétation
    theta_0 = df_theta[df_theta['theta'] == 0.0].iloc[0]
    theta_10 = df_theta[df_theta['theta'] == 0.10].iloc[0]
    
    if theta_0['accuracy'] > 50 and theta_0['coverage'] > 80:
        print("✅ CAS 1 : Signal directionnel existe mais masqué par seuil")
        print(f"   θ=0.0 → Accuracy={theta_0['accuracy']:.1f}%, Coverage={theta_0['coverage']:.1f}%")
        print(f"   → Recommandation : Utiliser θ optimal ({best_composite['theta']:.2f})")
    elif theta_0['accuracy'] < 50 and theta_0['coverage'] > 80:
        print("⚠️  CAS 2 : Signal neutre structurel")
        print(f"   θ=0.0 → Accuracy={theta_0['accuracy']:.1f}%, Coverage={theta_0['coverage']:.1f}%")
        print(f"   → Nécessite diagnostic approfondi (Étape B)")
    else:
        print("🔍 CAS 3 : Situation intermédiaire")
        print(f"   → Nécessite diagnostic approfondi (Étape B)")
    print()
    
    # Sauvegarder
    output_file = BASE_DIR / 'theta_grid_results.csv'
    df_theta.to_csv(output_file, index=False)
    print(f"✅ Résultats sauvegardés : {output_file}")
    print()
    
    return scores_S, directions_real, df_theta

# ============================================================================
# ÉTAPE B : DIAGNOSTIC SCORES S
# ============================================================================

def diagnose_scores_S(scores_S, directions_real):
    """Diagnostique pourquoi scores S sont proches de 0"""
    print("="*80)
    print("ÉTAPE B : DIAGNOSTIC SCORES S PROCHES DE 0")
    print("="*80)
    print()
    
    # B1. Distribution de S
    print("="*80)
    print("B1. DISTRIBUTION DE S")
    print("="*80)
    print()
    
    print(f"📊 Statistiques S :")
    print(f"   Min  : {scores_S.min():.4f}")
    print(f"   Max  : {scores_S.max():.4f}")
    print(f"   Médiane : {np.median(scores_S):.4f}")
    print(f"   Moyenne : {scores_S.mean():.4f}")
    print(f"   Écart-type : {scores_S.std():.4f}")
    print()
    
    # Pourcentages autour de 0 (avec nouveau seuil 0.05 comme référence)
    pct_002 = (np.abs(scores_S) < 0.02).sum() / len(scores_S) * 100
    pct_005 = (np.abs(scores_S) < 0.05).sum() / len(scores_S) * 100
    pct_01 = (np.abs(scores_S) < 0.1).sum() / len(scores_S) * 100
    
    print(f"📊 Concentration autour de 0 :")
    print(f"   |S| < 0.02 : {pct_002:.1f}%")
    print(f"   |S| < 0.05 : {pct_005:.1f}% ⭐ (nouveau seuil)")
    print(f"   |S| < 0.10 : {pct_01:.1f}%")
    print()
    
    # Histogramme
    try:
        plt.figure(figsize=(10, 6))
        plt.hist(scores_S, bins=50, edgecolor='black', alpha=0.7)
        plt.axvline(0, color='red', linestyle='--', linewidth=2, label='S = 0')
        plt.xlabel('Score S')
        plt.ylabel('Fréquence')
        plt.title('Distribution des scores S')
        plt.legend()
        plt.grid(True, alpha=0.3)
        hist_file = BASE_DIR / 'distribution_scores_S.png'
        plt.savefig(hist_file, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"✅ Histogramme sauvegardé : {hist_file}")
    except Exception as e:
        print(f"⚠️  Erreur génération histogramme : {e}")
    print()
    
    # B2. Contribution par alpha
    print("="*80)
    print("B2. CONTRIBUTION PAR ALPHA")
    print("="*80)
    print()
    
    alpha_map = load_alpha_map(horizon='1h')
    stats_map = load_surprise_stats()
    
    # Charger dates et recalculer contributions
    if RESULTS_FILE.exists():
        df_results = pd.read_csv(RESULTS_FILE)
        dates_list = df_results['date'].tolist()
    else:
        print("❌ Fichier de résultats introuvable")
        return
    
    # Analyser contributions par alpha
    alpha_contributions = defaultdict(list)
    alpha_frequencies = defaultdict(int)
    
    print("📊 Calcul contributions par alpha...")
    for date_str in dates_list[:50]:  # Limiter pour performance
        events_df = load_events_for_date(date_str)
        if len(events_df) == 0:
            continue
        
        for _, row in events_df.iterrows():
            actual = row.get('actual')
            estimate = row.get('estimate')
            family = str(row.get('family', 'Other')).strip()
            event_key = str(row.get('event_key', '')).strip().lower()
            
            if pd.isna(actual) or pd.isna(estimate):
                continue
            
            surprise = float(actual) - float(estimate)
            mu_sigma = stats_map.get(event_key)
            if mu_sigma is None:
                continue
            
            mu, sigma = mu_sigma
            if sigma == 0:
                continue
            
            z = (surprise - mu) / sigma
            sign = "pos" if z > 0 else "neg"
            alpha_key = f"{family}_surp_{sign}"
            alpha = float(alpha_map.get(alpha_key, 0.0))
            
            contribution = alpha * z
            alpha_contributions[alpha_key].append(contribution)
            alpha_frequencies[alpha_key] += 1
    
    # Statistiques par alpha
    alpha_stats = []
    for alpha_key, contributions in alpha_contributions.items():
        if len(contributions) > 0:
            contrib_array = np.array(contributions)
            alpha_stats.append({
                'alpha_key': alpha_key,
                'n_contributions': len(contributions),
                'mean_contrib': contrib_array.mean(),
                'std_contrib': contrib_array.std(),
                'abs_mean_contrib': np.abs(contrib_array).mean(),
                'freq': alpha_frequencies[alpha_key]
            })
    
    df_alpha_stats = pd.DataFrame(alpha_stats)
    df_alpha_stats = df_alpha_stats.sort_values('abs_mean_contrib', ascending=False)
    
    print(f"📊 Top 10 alphas par contribution absolue moyenne :")
    print()
    print(f"{'Alpha Key':<40} {'Freq':<8} {'Mean Contrib':<15} {'Abs Mean':<15}")
    print("-" * 80)
    for _, row in df_alpha_stats.head(10).iterrows():
        print(f"{row['alpha_key']:<40} {row['freq']:<8} {row['mean_contrib']:<15.4f} {row['abs_mean_contrib']:<15.4f}")
    print()
    
    # Détecter alphas antagonistes
    print("🔍 Analyse alphas antagonistes :")
    print()
    
    # Grouper par famille (sans _surp_pos/neg)
    family_contributions = defaultdict(lambda: {'pos': [], 'neg': []})
    for alpha_key, contributions in alpha_contributions.items():
        if '_surp_pos' in alpha_key:
            family = alpha_key.replace('_surp_pos', '')
            family_contributions[family]['pos'].extend(contributions)
        elif '_surp_neg' in alpha_key:
            family = alpha_key.replace('_surp_neg', '')
            family_contributions[family]['neg'].extend(contributions)
    
    antagonist_families = []
    for family, contribs in family_contributions.items():
        if len(contribs['pos']) > 0 and len(contribs['neg']) > 0:
            mean_pos = np.array(contribs['pos']).mean()
            mean_neg = np.array(contribs['neg']).mean()
            if mean_pos * mean_neg < 0:  # Signes opposés
                antagonist_families.append({
                    'family': family,
                    'mean_pos': mean_pos,
                    'mean_neg': mean_neg,
                    'sum': mean_pos + mean_neg
                })
    
    if antagonist_families:
        print(f"   ⚠️  {len(antagonist_families)} familles avec contributions opposées :")
        for fam in antagonist_families[:5]:
            print(f"      {fam['family']:<30} : pos={fam['mean_pos']:+.4f}, neg={fam['mean_neg']:+.4f}, sum={fam['sum']:+.4f}")
    else:
        print("   ✅ Pas d'annulation majeure détectée")
    print()
    
    # B3. Sens du signe
    print("="*80)
    print("B3. SENS DU SIGNE")
    print("="*80)
    print()
    
    # Corrélation S vs direction réelle
    directions_bin = (directions_real == 'UP').astype(int)
    corr_S_direction = np.corrcoef(scores_S, directions_bin)[0, 1]
    
    print(f"📊 Corrélation S vs direction réelle :")
    print(f"   Corrélation : {corr_S_direction:.4f}")
    print()
    
    if corr_S_direction < -0.3:
        print("   ⚠️  CAS 3 : Signe probablement inversé !")
        print(f"   → Corrélation négative forte ({corr_S_direction:.4f})")
        print(f"   → Recommandation : Inverser signe de S ou d'un sous-ensemble d'alphas")
    elif corr_S_direction > 0.3:
        print("   ✅ Signe correct")
        print(f"   → Corrélation positive ({corr_S_direction:.4f})")
    else:
        print("   ⚠️  Signal faible ou neutre")
        print(f"   → Corrélation proche de 0 ({corr_S_direction:.4f})")
    print()
    
    # B4. Qualité des surprise stats
    print("="*80)
    print("B4. QUALITÉ DES SURPRISE STATS")
    print("="*80)
    print()
    
    # Charger événements
    try:
        df_events = pd.read_csv(EVENTS_FILE)
        df_events['actual'] = pd.to_numeric(df_events['actual'], errors='coerce')
        df_events['estimate'] = pd.to_numeric(df_events['estimate'], errors='coerce')
        df_events = df_events.dropna(subset=['actual', 'estimate'])
        df_events['surprise'] = df_events['actual'] - df_events['estimate']
        
        print(f"📊 Statistiques surprises brutes :")
        print(f"   Nombre d'événements : {len(df_events):,}")
        print(f"   Moyenne surprise : {df_events['surprise'].mean():.4f}")
        print(f"   Écart-type surprise : {df_events['surprise'].std():.4f}")
        print(f"   Min : {df_events['surprise'].min():.4f}")
        print(f"   Max : {df_events['surprise'].max():.4f}")
        print()
        
        # Vérifier normalisation par event_key
        print(f"📊 Normalisation par event_key :")
        g = df_events.groupby('event_key')['surprise']
        mu_all = g.mean()
        sigma_all = g.std(ddof=0)
        
        print(f"   Nombre d'event_keys : {len(mu_all)}")
        print(f"   Moyenne des mu : {mu_all.mean():.4f}")
        print(f"   Moyenne des sigma : {sigma_all.mean():.4f}")
        print(f"   Sigma min : {sigma_all.min():.4f}")
        print(f"   Sigma max : {sigma_all.max():.4f}")
        print()
        
        # Vérifier si sigma trop faible (sur-normalisation)
        low_sigma = (sigma_all < 0.01).sum()
        if low_sigma > 0:
            print(f"   ⚠️  {low_sigma} event_keys avec sigma < 0.01 (sur-normalisation possible)")
        else:
            print(f"   ✅ Pas de sur-normalisation détectée")
        print()
        
    except Exception as e:
        print(f"⚠️  Erreur analyse surprise stats : {e}")
        print()
    
    # Sauvegarder diagnostics
    output_file = BASE_DIR / 'diagnostic_scores_S.csv'
    diagnostic_data = {
        'metric': [
            'mean_S', 'median_S', 'std_S', 'min_S', 'max_S',
            'pct_abs_S_002', 'pct_abs_S_005', 'pct_abs_S_01',
            'corr_S_direction'
        ],
        'value': [
            scores_S.mean(), np.median(scores_S), scores_S.std(),
            scores_S.min(), scores_S.max(),
            pct_002, pct_005, pct_01,
            corr_S_direction
        ]
    }
    pd.DataFrame(diagnostic_data).to_csv(output_file, index=False)
    print(f"✅ Diagnostic sauvegardé : {output_file}")
    print()
    
    # Sauvegarder stats alpha
    alpha_stats_file = BASE_DIR / 'alpha_contributions_stats.csv'
    df_alpha_stats.to_csv(alpha_stats_file, index=False)
    print(f"✅ Stats contributions alpha sauvegardées : {alpha_stats_file}")
    print()

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("="*80)
    print("DIAGNOSTIC COMPLET DIRECTION V3")
    print("="*80)
    print()
    
    # Étape A
    result = test_theta_grid()
    
    if result is None:
        return
    
    scores_S, directions_real, df_theta = result
    
    print()
    print("="*80)
    print()
    
    # Étape B
    diagnose_scores_S(scores_S, directions_real)
    
    # Synthèse finale
    print("="*80)
    print("📋 SYNTHÈSE FINALE")
    print("="*80)
    print()
    
    theta_0 = df_theta[df_theta['theta'] == 0.0].iloc[0]
    theta_005 = df_theta[df_theta['theta'] == 0.05].iloc[0] if len(df_theta[df_theta['theta'] == 0.05]) > 0 else None
    best_composite = df_theta.loc[df_theta['composite_score'].idxmax()]
    
    print(f"📊 Résultats clés :")
    print(f"   θ=0.0 : Accuracy={theta_0['accuracy']:.1f}%, Coverage={theta_0['coverage']:.1f}%")
    if theta_005 is not None:
        print(f"   θ=0.05 ⭐ : Accuracy={theta_005['accuracy']:.1f}%, Coverage={theta_005['coverage']:.1f}%")
    print(f"   Meilleur θ : {best_composite['theta']:.2f} (Accuracy={best_composite['accuracy']:.1f}%, Coverage={best_composite['coverage']:.1f}%)")
    print()
    
    corr_S_dir = np.corrcoef(scores_S, (directions_real == 'UP').astype(int))[0, 1]
    pct_neutral_01 = (np.abs(scores_S) < 0.1).sum() / len(scores_S) * 100
    pct_neutral_005 = (np.abs(scores_S) < 0.05).sum() / len(scores_S) * 100
    
    print(f"📊 Diagnostic S :")
    print(f"   Corrélation S ↔ direction : {corr_S_dir:.4f}")
    print(f"   % scores neutres (|S|<0.1) : {pct_neutral_01:.1f}%")
    print(f"   % scores neutres (|S|<0.05) ⭐ : {pct_neutral_005:.1f}%")
    print()
    
    # Recommandation finale
    if theta_0['accuracy'] > 50 and corr_S_dir > 0.2:
        print("✅ RECOMMANDATION : Utiliser θ optimal pour meilleur compromis")
        print(f"   → θ = {best_composite['theta']:.2f}")
    elif corr_S_dir < -0.3:
        print("⚠️  RECOMMANDATION : Inverser signe de S ou d'alphas")
        print(f"   → Corrélation négative ({corr_S_dir:.4f})")
    elif pct_neutral > 70:
        print("⚠️  RECOMMANDATION : Revoir weights ou sélection d'alphas")
        print(f"   → {pct_neutral:.1f}% des scores sont neutres")
    else:
        print("🔍 RECOMMANDATION : Analyse approfondie nécessaire")
    print()

if __name__ == '__main__':
    main()

