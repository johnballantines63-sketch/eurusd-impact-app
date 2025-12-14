"""
SESSION 110 - MODULE FORMULES DYNAMIQUES PRÉDICTION
====================================================

Module pour prédire l'amplification AVANT événement en utilisant
les formules validées Session 109 sur données historiques.

Formules validées :
- Cluster #1 (Manufacturing) : amp = 0.0339 × volatility_pips + 0.5352 (+41.8% amélioration)
- Cluster #3 (CPI)           : amp = 0.5490 × R²_72h + 1.6988 (+95% amélioration)

Date : 3 novembre 2025
Auteur : Session 110
"""

import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path
from datetime import timedelta
from typing import Tuple, Dict, Optional

# ============================================================================
# CONSTANTES - FORMULES VALIDÉES SESSION 109
# ============================================================================

# Cluster #1 (Manufacturing, 8 events)
C1_SLOPE = 0.0339
C1_INTERCEPT = 0.5352
C1_BASELINE_FIXE = 1.451  # Backup si calcul échoue

# Cluster #3 (CPI, 11 events)
C3_SLOPE = 0.5490
C3_INTERCEPT = 1.6988
C3_BASELINE_FIXE = 2.545  # Backup si calcul échoue

# Configuration
HOURS_PRE_EVENT = 72  # Fenêtre d'analyse avant événement


# ============================================================================
# FONCTION 1 : CALCUL VOLATILITÉ PRÉ-ÉVÉNEMENT
# ============================================================================

def calculate_volatility_72h_pre(
    prices_df: pd.DataFrame,
    event_time: pd.Timestamp
) -> Optional[float]:
    """
    Calcule la volatilité (écart-type) des prix sur 72h AVANT événement
    
    Utilisé pour Cluster #1 (Manufacturing)
    
    Parameters
    ----------
    prices_df : pd.DataFrame
        DataFrame avec colonnes ['datetime', 'close'] (ou 'high', 'low')
    event_time : pd.Timestamp
        Timestamp de l'événement (timezone-aware)
    
    Returns
    -------
    float or None
        Volatilité en pips (écart-type × 10000)
        None si données insuffisantes
    
    Example
    -------
    >>> volatility = calculate_volatility_72h_pre(prices, event_time)
    >>> print(f"Volatilité 72h pré-événement : {volatility:.2f} pips")
    """
    try:
        # Définir fenêtre 72h avant événement
        start_time = event_time - timedelta(hours=HOURS_PRE_EVENT)
        end_time = event_time
        
        # Filtrer prix dans fenêtre
        mask = (prices_df['datetime'] >= start_time) & (prices_df['datetime'] < end_time)
        window_prices = prices_df[mask].copy()
        
        if len(window_prices) < 10:  # Minimum 10 points
            print(f"⚠️ Pas assez de données : {len(window_prices)} points")
            return None
        
        # Calculer volatilité (écart-type des prix close)
        prices_close = window_prices['close'].values
        volatility_normalized = np.std(prices_close)
        volatility_pips = volatility_normalized * 10000
        
        return volatility_pips
        
    except Exception as e:
        print(f"❌ Erreur calcul volatilité : {e}")
        return None


# ============================================================================
# FONCTION 2 : CALCUL R² PRÉ-ÉVÉNEMENT
# ============================================================================

def calculate_r2_72h_pre(
    prices_df: pd.DataFrame,
    event_time: pd.Timestamp
) -> Optional[float]:
    """
    Calcule le R² de régression linéaire sur 72h AVANT événement
    
    Utilisé pour Cluster #3 (CPI)
    
    Parameters
    ----------
    prices_df : pd.DataFrame
        DataFrame avec colonnes ['datetime', 'close']
    event_time : pd.Timestamp
        Timestamp de l'événement (timezone-aware)
    
    Returns
    -------
    float or None
        R² de la régression linéaire (0 à 1)
        None si données insuffisantes
    
    Example
    -------
    >>> r2 = calculate_r2_72h_pre(prices, event_time)
    >>> print(f"R² 72h pré-événement : {r2:.4f}")
    """
    try:
        # Définir fenêtre 72h avant événement
        start_time = event_time - timedelta(hours=HOURS_PRE_EVENT)
        end_time = event_time
        
        # Filtrer prix dans fenêtre
        mask = (prices_df['datetime'] >= start_time) & (prices_df['datetime'] < end_time)
        window_prices = prices_df[mask].copy()
        
        if len(window_prices) < 10:  # Minimum 10 points
            print(f"⚠️ Pas assez de données : {len(window_prices)} points")
            return None
        
        # Préparer données pour régression
        y = window_prices['close'].values
        x = np.arange(len(y))
        
        # Régression linéaire
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        r2 = r_value ** 2
        
        return r2
        
    except Exception as e:
        print(f"❌ Erreur calcul R² : {e}")
        return None


# ============================================================================
# FONCTION 3 : PRÉDICTION AMP CLUSTER #1
# ============================================================================

def predict_amp_C1(volatility_pips: Optional[float]) -> float:
    """
    Prédit l'amplification pour Cluster #1 (Manufacturing)
    
    Formule validée Session 109 :
    amp = 0.0339 × volatility_pips + 0.5352
    
    Amélioration : +41.8% vs baseline fixe (1.451)
    
    Parameters
    ----------
    volatility_pips : float or None
        Volatilité calculée sur 72h pré-événement
    
    Returns
    -------
    float
        Amplification prédite
        Retourne baseline fixe si volatility=None
    
    Example
    -------
    >>> amp = predict_amp_C1(21.5)
    >>> print(f"Amplification prédite C#1 : {amp:.3f}")
    """
    if volatility_pips is None:
        print(f"⚠️ Volatilité None → Utilisation baseline fixe C#1 = {C1_BASELINE_FIXE:.3f}")
        return C1_BASELINE_FIXE
    
    amp_predicted = C1_SLOPE * volatility_pips + C1_INTERCEPT
    
    # Limites de sécurité (basées sur données Session 109)
    amp_predicted = max(0.5, min(amp_predicted, 4.0))
    
    return amp_predicted


# ============================================================================
# FONCTION 4 : PRÉDICTION AMP CLUSTER #3
# ============================================================================

def predict_amp_C3(r2_72h: Optional[float]) -> float:
    """
    Prédit l'amplification pour Cluster #3 (CPI)
    
    Formule validée Session 107 (re-validée Session 109) :
    amp = 0.5490 × R²_72h + 1.6988
    
    Amélioration : +95% vs baseline fixe (2.545)
    
    Parameters
    ----------
    r2_72h : float or None
        R² calculé sur 72h pré-événement
    
    Returns
    -------
    float
        Amplification prédite
        Retourne baseline fixe si r2=None
    
    Example
    -------
    >>> amp = predict_amp_C3(0.742)
    >>> print(f"Amplification prédite C#3 : {amp:.3f}")
    """
    if r2_72h is None:
        print(f"⚠️ R² None → Utilisation baseline fixe C#3 = {C3_BASELINE_FIXE:.3f}")
        return C3_BASELINE_FIXE
    
    amp_predicted = C3_SLOPE * r2_72h + C3_INTERCEPT
    
    # Limites de sécurité (basées sur données Session 109)
    amp_predicted = max(1.0, min(amp_predicted, 5.0))
    
    return amp_predicted


# ============================================================================
# FONCTION 5 : PRÉDICTION PRINCIPALE (AUTO-DÉTECTION CLUSTER)
# ============================================================================

def predict_amplification_dynamic(
    prices_df: pd.DataFrame,
    event_time: pd.Timestamp,
    cluster: int,
    verbose: bool = True
) -> Dict[str, float]:
    """
    Prédit l'amplification dynamiquement selon le cluster
    
    AUTO-DÉTECTE le cluster et applique la formule appropriée :
    - Cluster #1 → Formule volatility_pips
    - Cluster #3 → Formule R²_72h
    - Autre → Baseline fixe moyenne
    
    Parameters
    ----------
    prices_df : pd.DataFrame
        Prix historiques avec ['datetime', 'close']
    event_time : pd.Timestamp
        Timestamp événement (timezone-aware)
    cluster : int
        1 = Manufacturing, 3 = CPI, autre = défaut
    verbose : bool
        Afficher logs détaillés
    
    Returns
    -------
    dict
        {
            'cluster': int,
            'amp_predicted': float,
            'method': str ('volatility', 'r2', 'baseline'),
            'metric_value': float or None,
            'baseline_fixe': float
        }
    
    Example
    -------
    >>> result = predict_amplification_dynamic(prices, event_time, cluster=1)
    >>> print(f"Amp prédite : {result['amp_predicted']:.3f}")
    """
    result = {
        'cluster': cluster,
        'amp_predicted': None,
        'method': None,
        'metric_value': None,
        'baseline_fixe': None
    }
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"🎯 PRÉDICTION AMPLIFICATION DYNAMIQUE")
        print(f"{'='*60}")
        print(f"Cluster : {cluster}")
        print(f"Événement : {event_time}")
    
    # CLUSTER #1 (Manufacturing) → Volatilité
    if cluster == 1:
        result['method'] = 'volatility'
        result['baseline_fixe'] = C1_BASELINE_FIXE
        
        volatility = calculate_volatility_72h_pre(prices_df, event_time)
        result['metric_value'] = volatility
        
        amp = predict_amp_C1(volatility)
        result['amp_predicted'] = amp
        
        if verbose:
            print(f"\n📊 Méthode : Volatilité 72h pré-événement")
            print(f"   Volatilité : {volatility:.2f} pips" if volatility else "   Volatilité : None")
            print(f"   Formule : amp = 0.0339 × {volatility:.2f} + 0.5352" if volatility else "   Formule : baseline fixe")
            print(f"   ✅ Amp prédite : {amp:.3f}")
    
    # CLUSTER #3 (CPI) → R² 72h
    elif cluster == 3:
        result['method'] = 'r2'
        result['baseline_fixe'] = C3_BASELINE_FIXE
        
        r2 = calculate_r2_72h_pre(prices_df, event_time)
        result['metric_value'] = r2
        
        amp = predict_amp_C3(r2)
        result['amp_predicted'] = amp
        
        if verbose:
            print(f"\n📊 Méthode : R² 72h pré-événement")
            print(f"   R² : {r2:.4f}" if r2 else "   R² : None")
            print(f"   Formule : amp = 0.5490 × {r2:.4f} + 1.6988" if r2 else "   Formule : baseline fixe")
            print(f"   ✅ Amp prédite : {amp:.3f}")
    
    # AUTRE CLUSTER → Baseline moyenne
    else:
        result['method'] = 'baseline_default'
        baseline_default = (C1_BASELINE_FIXE + C3_BASELINE_FIXE) / 2
        result['baseline_fixe'] = baseline_default
        result['amp_predicted'] = baseline_default
        
        if verbose:
            print(f"\n⚠️ Cluster {cluster} non reconnu")
            print(f"   Utilisation baseline moyenne : {baseline_default:.3f}")
    
    if verbose:
        print(f"{'='*60}\n")
    
    return result


# ============================================================================
# FONCTION 6 : BATCH PRÉDICTION (MULTIPLE DATES)
# ============================================================================

def predict_amplification_batch(
    dates_df: pd.DataFrame,
    prices_df: pd.DataFrame,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Prédit amplification pour multiple dates en batch
    
    Parameters
    ----------
    dates_df : pd.DataFrame
        DataFrame avec colonnes ['date', 'cluster', 'amp_optimal']
    prices_df : pd.DataFrame
        Prix historiques complets
    verbose : bool
        Afficher détails pour chaque date
    
    Returns
    -------
    pd.DataFrame
        dates_df enrichi avec colonnes :
        - amp_predicted : Amplification prédite
        - method : Méthode utilisée
        - metric_value : Valeur métrique
        - error : abs(amp_predicted - amp_optimal)
    
    Example
    -------
    >>> results = predict_amplification_batch(dates, prices)
    >>> mae = results['error'].mean()
    >>> print(f"MAE global : {mae:.3f}")
    """
    results = []
    
    print(f"\n{'='*80}")
    print(f"🔄 BATCH PRÉDICTION - {len(dates_df)} dates")
    print(f"{'='*80}\n")
    
    for idx, row in dates_df.iterrows():
        date_str = row['date']
        cluster = int(row['cluster'])
        amp_optimal = row['amp_optimal']
        
        # Convertir date en timestamp
        event_time = pd.to_datetime(date_str)
        if event_time.tzinfo is None:
            event_time = event_time.tz_localize('Europe/Zurich')
        
        # Prédiction
        result = predict_amplification_dynamic(
            prices_df, 
            event_time, 
            cluster,
            verbose=verbose
        )
        
        # Calculer erreur
        error = abs(result['amp_predicted'] - amp_optimal)
        
        results.append({
            'date': date_str,
            'cluster': cluster,
            'amp_optimal': amp_optimal,
            'amp_predicted': result['amp_predicted'],
            'method': result['method'],
            'metric_value': result['metric_value'],
            'baseline_fixe': result['baseline_fixe'],
            'error': error
        })
        
        if not verbose:
            status = "✅" if error < 0.5 else "⚠️" if error < 1.0 else "❌"
            print(f"{status} {date_str} | C#{cluster} | Optimal: {amp_optimal:.3f} | Prédit: {result['amp_predicted']:.3f} | Erreur: {error:.3f}")
    
    results_df = pd.DataFrame(results)
    
    # Statistiques globales
    mae_global = results_df['error'].mean()
    mae_c1 = results_df[results_df['cluster'] == 1]['error'].mean()
    mae_c3 = results_df[results_df['cluster'] == 3]['error'].mean()
    
    print(f"\n{'='*80}")
    print(f"📊 STATISTIQUES GLOBALES")
    print(f"{'='*80}")
    print(f"MAE Global    : {mae_global:.3f}")
    print(f"MAE Cluster 1 : {mae_c1:.3f}")
    print(f"MAE Cluster 3 : {mae_c3:.3f}")
    print(f"{'='*80}\n")
    
    return results_df


# ============================================================================
# TESTS UNITAIRES
# ============================================================================

if __name__ == "__main__":
    print("="*80)
    print("MODULE FORMULES DYNAMIQUES PRÉDICTION - TESTS UNITAIRES")
    print("="*80)
    
    # Test 1 : Predict C#1
    print("\n✅ Test 1 : Prédiction C#1 avec volatilité")
    amp_c1 = predict_amp_C1(21.5)
    print(f"   Volatilité : 21.5 pips → Amp : {amp_c1:.3f}")
    assert 0.5 < amp_c1 < 4.0, "Amp C#1 hors limites"
    
    # Test 2 : Predict C#3
    print("\n✅ Test 2 : Prédiction C#3 avec R²")
    amp_c3 = predict_amp_C3(0.742)
    print(f"   R² : 0.742 → Amp : {amp_c3:.3f}")
    assert 1.0 < amp_c3 < 5.0, "Amp C#3 hors limites"
    
    # Test 3 : Fallback None
    print("\n✅ Test 3 : Fallback si métrique None")
    amp_c1_none = predict_amp_C1(None)
    print(f"   Volatilité : None → Amp : {amp_c1_none:.3f} (baseline)")
    assert amp_c1_none == C1_BASELINE_FIXE, "Fallback C#1 incorrect"
    
    print("\n" + "="*80)
    print("✅✅✅ TOUS LES TESTS PASSENT")
    print("="*80)
