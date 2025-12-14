"""
SESSION 110 - MODULE AMPLIFICATION DYNAMIQUE
=============================================

Module pour calculer le facteur d'amplification dynamique selon le cluster
et les métriques de marché calculées DEPUIS dernière inversion de tendance.

Architecture :
1. Détecter cluster (C#1 Manufacturing ou C#3 CPI)
2. Détecter dernière inversion de tendance (méthode Session 107)
3. Calculer métrique appropriée DEPUIS inversion
4. Appliquer formule validée Session 109

Formules validées Session 109 :
- Cluster #1 : amp = 0.0339 × volatility_pips + 0.5352 (+41.8% amélioration)
- Cluster #3 : amp = 0.5490 × R²_trend + 1.6988 (+95% amélioration)

Date : 3 novembre 2025
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy.stats import linregress
from typing import Dict, List, Optional, Tuple
import duckdb
from pathlib import Path

# ============================================================================
# CONSTANTES - FORMULES VALIDÉES SESSION 109
# ============================================================================

# Cluster #1 (Manufacturing, 11 dates)
C1_SLOPE = 0.0339
C1_INTERCEPT = 0.5352
C1_BASELINE_FIXE = 1.451

# Cluster #3 (CPI, 6 dates)
C3_SLOPE = 0.5490
C3_INTERCEPT = 1.6988
C3_BASELINE_FIXE = 2.545

# FORMULE UNIVERSELLE (17 dates combinées) - SESSION 109 RANG 3
# Prédit l'écart par rapport à baseline
ECARTS_SLOPE = 0.0166
ECARTS_INTERCEPT = -0.9878

# Configuration détection inversion (Session 107)
SEGMENT_HOURS = 12  # Durée segments pour analyse tendance
MIN_R2_FOR_TREND = 0.3  # R² minimum pour tendance valide
LOOKBACK_DAYS = 14  # Jours historiques à analyser
MIN_HOURS_BEFORE_EVENT = 24  # Ignorer inversions trop récentes


# ============================================================================
# FONCTION 1 : DÉTECTION CLUSTER
# ============================================================================

def detect_cluster(events_list: List[dict]) -> int:
    """
    Détecte le cluster d'événements
    
    Règles :
    - Si 'CPI' dans n'importe quel event_key → Cluster #3
    - Si 'Manufacturing' ou 'ISM' dans event_key → Cluster #1
    - Défaut → Cluster #3 (conservateur)
    
    Parameters
    ----------
    events_list : List[dict]
        Liste événements avec 'event_key' ou 'label'
    
    Returns
    -------
    int
        1 = Manufacturing, 3 = CPI
    
    Example
    -------
    >>> events = [{'event_key': 'US_CPI_MOM', 'label': 'CPI m/m'}]
    >>> cluster = detect_cluster(events)
    >>> print(f"Cluster détecté : C#{cluster}")
    """
    # Chercher dans event_key ou label
    for event in events_list:
        event_key = event.get('event_key', '').upper()
        label = event.get('label', '').upper()
        combined = event_key + ' ' + label
        
        # CPI → C#3
        if 'CPI' in combined:
            return 3
        
        # Manufacturing → C#1
        if 'MANUFACTURING' in combined or 'ISM' in combined or 'PMI' in combined:
            return 1
    
    # Défaut : CPI (plus conservateur)
    return 3


# ============================================================================
# FONCTION 2 : DÉTECTION INVERSION TENDANCE (SESSION 107)
# ============================================================================

def detect_trend_by_inversion(
    prices_df: pd.DataFrame,
    event_time: pd.Timestamp,
    lookback_days: int = LOOKBACK_DAYS,
    segment_hours: int = SEGMENT_HOURS,
    min_r2_for_trend: float = MIN_R2_FOR_TREND,
    min_hours_before_event: int = MIN_HOURS_BEFORE_EVENT
) -> Optional[Dict]:
    """
    Détecte dernière inversion de tendance AVANT événement
    Méthode validée Session 107-108
    
    Algorithme :
    1. Découper période en segments (12h)
    2. Calculer tendance (régression) pour chaque segment
    3. Détecter inversions : UP→DOWN (pic) ou DOWN→UP (creux)
    4. Valider R² > seuil sur les deux côtés
    5. Retourner dernière inversion valide
    
    Parameters
    ----------
    prices_df : pd.DataFrame
        Prix avec colonnes ['datetime', 'close', 'high', 'low']
    event_time : pd.Timestamp
        Timestamp événement
    
    Returns
    -------
    dict or None
        {
            'inversion_time': Timestamp,
            'inversion_type': 'peak' ou 'trough',
            'trend_before': 'UP' ou 'DOWN',
            'trend_after': 'UP' ou 'DOWN',
            'r2_before': float,
            'r2_after': float
        }
    """
    try:
        # Période d'analyse : lookback_days AVANT événement
        query_time = event_time  # JUSQU'À l'événement (pas -2h !)
        start_time = query_time - timedelta(days=lookback_days)
        
        # Filtrer prix dans période
        mask = (prices_df['datetime'] >= start_time) & (prices_df['datetime'] <= query_time)
        df_window = prices_df[mask].copy()
        
        if len(df_window) < 1000:
            print(f"⚠️ Pas assez de données : {len(df_window)} points")
            return None
        
        # === ÉTAPE 1 : DÉCOUPER EN SEGMENTS ET CALCULER TENDANCES ===
        segment_duration = timedelta(hours=segment_hours)
        current_time = start_time
        segments = []
        
        while current_time < query_time:
            end_time = current_time + segment_duration
            
            # Filtrer données segment
            mask_seg = (df_window['datetime'] >= current_time) & (df_window['datetime'] < end_time)
            df_segment = df_window[mask_seg].copy()
            
            if len(df_segment) < 100:
                current_time = end_time
                continue
            
            # Régression linéaire
            df_segment['time_numeric'] = (df_segment['datetime'] - df_segment['datetime'].iloc[0]).dt.total_seconds()
            X = df_segment['time_numeric'].values
            y = df_segment['close'].values
            
            try:
                slope, intercept, r_value, p_value, std_err = linregress(X, y)
                r2 = r_value ** 2
                
                # Direction
                direction = 'UP' if slope > 0 else 'DOWN' if slope < 0 else 'FLAT'
                
                segments.append({
                    'start': current_time,
                    'end': end_time,
                    'direction': direction,
                    'slope': slope,
                    'r2': r2,
                    'price_start': df_segment['close'].iloc[0],
                    'price_end': df_segment['close'].iloc[-1],
                    'num_points': len(df_segment)
                })
                
            except Exception as e:
                pass
            
            current_time = end_time
        
        if len(segments) < 3:
            print(f"⚠️ Pas assez de segments : {len(segments)}")
            return None
        
        # === ÉTAPE 2 : DÉTECTER INVERSIONS ===
        inversions = []
        
        for i in range(1, len(segments)):
            seg_prev = segments[i-1]
            seg_curr = segments[i]
            
            # Vérifier R² suffisant des deux côtés
            if seg_prev['r2'] < min_r2_for_trend or seg_curr['r2'] < min_r2_for_trend:
                continue
            
            # Détecter inversion
            inversion_type = None
            
            if seg_prev['direction'] == 'UP' and seg_curr['direction'] == 'DOWN':
                inversion_type = 'peak'
            elif seg_prev['direction'] == 'DOWN' and seg_curr['direction'] == 'UP':
                inversion_type = 'trough'
            
            if inversion_type:
                inversion_time = seg_curr['start']
                
                # Vérifier distance minimum avec événement
                hours_before_event = (event_time - inversion_time).total_seconds() / 3600
                if hours_before_event < min_hours_before_event:
                    continue
                
                inversions.append({
                    'inversion_time': inversion_time,
                    'inversion_type': inversion_type,
                    'trend_before': seg_prev['direction'],
                    'trend_after': seg_curr['direction'],
                    'r2_before': seg_prev['r2'],
                    'r2_after': seg_curr['r2'],
                    'hours_before_event': hours_before_event
                })
        
        # === ÉTAPE 3 : SÉLECTIONNER DERNIÈRE INVERSION VALIDE ===
        if not inversions:
            print("⚠️ Aucune inversion détectée")
            return None
        
        # Trier par temps (plus récente en dernier)
        inversions_sorted = sorted(inversions, key=lambda x: x['inversion_time'])
        last_inversion = inversions_sorted[-1]
        
        return last_inversion
        
    except Exception as e:
        print(f"❌ Erreur détection inversion : {e}")
        return None


# ============================================================================
# FONCTION 3 : CALCUL VOLATILITÉ DEPUIS INVERSION (CLUSTER #1)
# ============================================================================

def calculate_volatility_since_inversion(
    prices_df: pd.DataFrame,
    inversion_point: Dict,
    event_time: pd.Timestamp
) -> Optional[float]:
    """
    Calcule volatilité (écart-type) DEPUIS dernière inversion
    Utilisé pour Cluster #1 (Manufacturing)
    
    Parameters
    ----------
    prices_df : pd.DataFrame
        Prix avec colonnes ['datetime', 'close']
    inversion_point : dict
        Résultat de detect_trend_by_inversion()
    event_time : pd.Timestamp
        Timestamp événement
    
    Returns
    -------
    float or None
        Volatilité en pips (écart-type × 10000)
    """
    if inversion_point is None:
        return None
    
    try:
        inversion_time = inversion_point['inversion_time']
        
        # Fenêtre : depuis inversion jusqu'à événement
        end_time = event_time
        
        # Filtrer prix
        mask = (prices_df['datetime'] >= inversion_time) & (prices_df['datetime'] <= end_time)
        df_trend = prices_df[mask].copy()
        
        if len(df_trend) < 100:
            print(f"⚠️ Pas assez de points depuis inversion : {len(df_trend)}")
            return None
        
        # Calculer volatilité (écart-type)
        prices_close = df_trend['close'].values
        volatility_normalized = np.std(prices_close)
        volatility_pips = volatility_normalized * 10000
        
        return volatility_pips
        
    except Exception as e:
        print(f"❌ Erreur calcul volatilité : {e}")
        return None


# ============================================================================
# FONCTION 4 : CALCUL R² SUR 72H FIXES (CLUSTER #3 - SESSION 107)
# ============================================================================

def calculate_r2_72h_fixed(
    prices_df: pd.DataFrame,
    event_time: pd.Timestamp,
    hours: int = 72
) -> Optional[float]:
    """
    Calcule R² de régression linéaire sur 72H FIXES avant événement
    Utilisé pour Cluster #3 (CPI) - Méthode Session 107 Phase 2B
    
    Parameters
    ----------
    prices_df : pd.DataFrame
        Prix avec colonnes ['datetime', 'close']
    event_time : pd.Timestamp
        Timestamp événement
    hours : int
        Nombre d'heures fixes (défaut: 72)
    
    Returns
    -------
    float or None
        R² de la régression linéaire (0 à 1)
    """
    try:
        # Fenêtre FIXE : 72h avant événement (event-2h)
        # Session 107 : Soustraire 2h pour éviter mouvement événement
        query_time = event_time - timedelta(hours=2)
        start_time = query_time - timedelta(hours=hours)
        end_time = query_time  # Jusqu'à event-2h, pas event
        
        # Filtrer prix
        mask = (prices_df['datetime'] >= start_time) & (prices_df['datetime'] <= end_time)
        df_window = prices_df[mask].copy()
        
        if len(df_window) < 100:
            print(f"⚠️ Pas assez de points sur 72h : {len(df_window)}")
            return None
        
        # Régression linéaire
        df_window['time_numeric'] = (df_window['datetime'] - df_window['datetime'].iloc[0]).dt.total_seconds()
        X = df_window['time_numeric'].values
        y = df_window['close'].values
        
        slope, intercept, r_value, p_value, std_err = linregress(X, y)
        r2 = r_value ** 2
        
        return r2
        
    except Exception as e:
        print(f"❌ Erreur calcul R² 72h : {e}")
        return None


# ============================================================================
# FONCTION 4BIS : CALCUL R² DEPUIS INVERSION (ANCIENNE MÉTHODE - BACKUP)
# ============================================================================

def calculate_r2_since_inversion(
    prices_df: pd.DataFrame,
    inversion_point: Dict,
    event_time: pd.Timestamp
) -> Optional[float]:
    """
    Calcule R² de régression linéaire DEPUIS dernière inversion
    Utilisé pour Cluster #3 (CPI)
    
    Parameters
    ----------
    prices_df : pd.DataFrame
        Prix avec colonnes ['datetime', 'close']
    inversion_point : dict
        Résultat de detect_trend_by_inversion()
    event_time : pd.Timestamp
        Timestamp événement
    
    Returns
    -------
    float or None
        R² de la régression linéaire (0 à 1)
    """
    if inversion_point is None:
        return None
    
    try:
        inversion_time = inversion_point['inversion_time']
        
        # Fenêtre : depuis inversion jusqu'à événement
        end_time = event_time
        
        # Filtrer prix
        mask = (prices_df['datetime'] >= inversion_time) & (prices_df['datetime'] <= end_time)
        df_trend = prices_df[mask].copy()
        
        if len(df_trend) < 100:
            print(f"⚠️ Pas assez de points depuis inversion : {len(df_trend)}")
            return None
        
        # Régression linéaire
        df_trend['time_numeric'] = (df_trend['datetime'] - df_trend['datetime'].iloc[0]).dt.total_seconds()
        X = df_trend['time_numeric'].values
        y = df_trend['close'].values
        
        slope, intercept, r_value, p_value, std_err = linregress(X, y)
        r2 = r_value ** 2
        
        return r2
        
    except Exception as e:
        print(f"❌ Erreur calcul R² : {e}")
        return None


# ============================================================================
# FONCTION 5 : APPROCHE ÉCARTS COMBINÉS (SESSION 109 RANG 3)
# ============================================================================

def calculate_amplification_ecarts(
    events_list: List[dict],
    prices_df: pd.DataFrame,
    event_time: pd.Timestamp,
    verbose: bool = True
) -> Dict:
    """
    Approche "Ecarts_Combined" Session 109 Rang 3 (+70.3%)
    
    Prédit l'ÉCART par rapport à baseline fixe du cluster
    Formule universelle : écart = 0.0166 × duration_hours - 0.9878
    
    amp_final = baseline_cluster + écart
    
    Parameters
    ----------
    events_list : List[dict]
        Liste événements
    prices_df : pd.DataFrame
        Prix historiques
    event_time : pd.Timestamp
        Timestamp événement
    verbose : bool
        Logs
    
    Returns
    -------
    dict
        {
            'cluster': int,
            'amplification': float,
            'method': 'ecarts_combined',
            'metric_name': 'duration_hours',
            'metric_value': float or None,
            'baseline_cluster': float,
            'ecart_predicted': float,
            'inversion_detected': bool
        }
    """
    if verbose:
        print("\n" + "="*80)
        print("🎯 CALCUL AMPLIFICATION - APPROCHE ÉCARTS COMBINÉS (SESSION 109)")
        print("="*80)
    
    result = {
        'cluster': None,
        'amplification': None,
        'method': 'ecarts_combined',
        'metric_name': 'duration_hours',
        'metric_value': None,
        'baseline_cluster': None,
        'ecart_predicted': None,
        'inversion_detected': False,
        'fallback_used': False
    }
    
    # ÉTAPE 1 : Détecter cluster
    cluster = detect_cluster(events_list)
    result['cluster'] = cluster
    
    # Baseline selon cluster
    baseline = C1_BASELINE_FIXE if cluster == 1 else C3_BASELINE_FIXE
    result['baseline_cluster'] = baseline
    
    if verbose:
        print(f"\n📊 Cluster détecté : C#{cluster}")
        print(f"   Baseline : {baseline:.3f}")
    
    # ÉTAPE 2 : Détecter inversion
    if verbose:
        print(f"\n🔍 Détection inversion de tendance...")
    
    inversion = detect_trend_by_inversion(prices_df, event_time)
    
    if inversion:
        result['inversion_detected'] = True
        
        # ÉTAPE 3 : Calculer duration depuis inversion
        duration_hours = inversion['hours_before_event']
        result['metric_value'] = duration_hours
        
        # ÉTAPE 4 : Calculer écart
        ecart = ECARTS_SLOPE * duration_hours + ECARTS_INTERCEPT
        result['ecart_predicted'] = ecart
        
        # ÉTAPE 5 : Amplification finale
        amp_final = baseline + ecart
        amp_final = max(0.5, min(amp_final, 5.0))  # Limites sécurité
        result['amplification'] = amp_final
        
        if verbose:
            print(f"   ✅ Inversion détectée !")
            print(f"   Type : {inversion['inversion_type']}")
            print(f"   Durée : {duration_hours:.2f}h")
            print(f"\n📊 Calcul écart :")
            print(f"   Écart = 0.0166 × {duration_hours:.2f} - 0.9878 = {ecart:.3f}")
            print(f"\n🎯 Amplification finale :")
            print(f"   amp = {baseline:.3f} + {ecart:.3f} = {amp_final:.3f}")
    else:
        # Fallback baseline
        result['fallback_used'] = True
        result['amplification'] = baseline
        
        if verbose:
            print(f"   ⚠️ Aucune inversion détectée")
            print(f"   → Fallback baseline : {baseline:.3f}")
    
    if verbose:
        print("="*80 + "\n")
    
    return result


# ============================================================================
# FONCTION 6 : CALCUL AMPLIFICATION DYNAMIQUE PRINCIPALE
# ============================================================================

def calculate_amplification_dynamic(
    events_list: List[dict],
    prices_df: pd.DataFrame,
    event_time: pd.Timestamp,
    verbose: bool = True
) -> Dict:
    """
    Calcule facteur d'amplification dynamique selon cluster et marché
    
    SÉQUENCE (Session 110) :
    1. Détecter cluster (C#1 ou C#3)
    2. Détecter dernière inversion de tendance
    3. Calculer métrique appropriée DEPUIS inversion
    4. Appliquer formule validée Session 109
    
    Parameters
    ----------
    events_list : List[dict]
        Liste événements avec 'event_key', 'label', etc.
    prices_df : pd.DataFrame
        Prix historiques avec ['datetime', 'close', 'high', 'low']
    event_time : pd.Timestamp
        Timestamp événement
    verbose : bool
        Afficher logs détaillés
    
    Returns
    -------
    dict
        {
            'cluster': int,
            'amplification': float,
            'method': str,
            'metric_name': str,
            'metric_value': float or None,
            'inversion_detected': bool,
            'inversion_info': dict or None,
            'fallback_used': bool
        }
    
    Example
    -------
    >>> events = [{'event_key': 'US_CPI_MOM', 'label': 'CPI m/m'}]
    >>> result = calculate_amplification_dynamic(events, prices, event_time)
    >>> print(f"Amplification : {result['amplification']:.3f}")
    """
    if verbose:
        print("\n" + "="*80)
        print("🎯 CALCUL AMPLIFICATION DYNAMIQUE (SESSION 110)")
        print("="*80)
    
    result = {
        'cluster': None,
        'amplification': None,
        'method': None,
        'metric_name': None,
        'metric_value': None,
        'inversion_detected': False,
        'inversion_info': None,
        'fallback_used': False
    }
    
    # === ÉTAPE 1 : DÉTECTER CLUSTER ===
    cluster = detect_cluster(events_list)
    result['cluster'] = cluster
    
    if verbose:
        print(f"\n📊 Cluster détecté : C#{cluster}")
        if cluster == 1:
            print("   Type : Manufacturing (ISM, PMI)")
            print("   Formule : amp = 0.0339 × volatility_pips + 0.5352")
        else:
            print("   Type : CPI (Inflation)")
            print("   Formule : amp = 0.5490 × R²_trend + 1.6988")
    
    # === ÉTAPE 2 : DÉTECTER INVERSION ===
    if verbose:
        print(f"\n🔍 Détection inversion de tendance...")
    
    inversion = detect_trend_by_inversion(prices_df, event_time)
    
    if inversion:
        result['inversion_detected'] = True
        result['inversion_info'] = inversion
        
        if verbose:
            print(f"   ✅ Inversion détectée !")
            print(f"   Type : {inversion['inversion_type']}")
            print(f"   Temps : {inversion['inversion_time']}")
            print(f"   Tendance : {inversion['trend_before']} → {inversion['trend_after']}")
            print(f"   R² avant : {inversion['r2_before']:.3f}")
            print(f"   R² après : {inversion['r2_after']:.3f}")
            print(f"   Distance événement : {inversion['hours_before_event']:.1f}h")
    else:
        if verbose:
            print(f"   ⚠️ Aucune inversion détectée")
    
    # === ÉTAPE 3 : CALCULER MÉTRIQUE DEPUIS INVERSION ===
    
    if cluster == 1:
        # CLUSTER #1 : VOLATILITÉ
        result['method'] = 'volatility_since_inversion'
        result['metric_name'] = 'volatility_pips'
        
        if inversion:
            volatility = calculate_volatility_since_inversion(prices_df, inversion, event_time)
            result['metric_value'] = volatility
            
            if volatility is not None:
                # Appliquer formule Session 109
                amp = C1_SLOPE * volatility + C1_INTERCEPT
                amp = max(0.5, min(amp, 4.0))  # Limites sécurité
                result['amplification'] = amp
                
                if verbose:
                    print(f"\n📊 Métrique calculée : volatility_pips = {volatility:.2f}")
                    print(f"   Formule : amp = 0.0339 × {volatility:.2f} + 0.5352")
                    print(f"   ✅ Amplification dynamique : {amp:.3f}")
            else:
                # Fallback baseline
                result['fallback_used'] = True
                result['amplification'] = C1_BASELINE_FIXE
                if verbose:
                    print(f"\n⚠️ Calcul métrique échoué → Fallback baseline : {C1_BASELINE_FIXE:.3f}")
        else:
            # Pas d'inversion → Fallback
            result['fallback_used'] = True
            result['amplification'] = C1_BASELINE_FIXE
            if verbose:
                print(f"\n⚠️ Pas d'inversion → Fallback baseline : {C1_BASELINE_FIXE:.3f}")
    
    elif cluster == 3:
        # CLUSTER #3 : R² SUR 72H FIXES (SESSION 107 PHASE 2B)
        result['method'] = 'r2_72h_fixed'
        result['metric_name'] = 'r2_72h'
        result['baseline_fixe'] = C3_BASELINE_FIXE
        
        # Calculer R² sur 72h FIXES (pas depuis inversion !)
        r2 = calculate_r2_72h_fixed(prices_df, event_time)
        result['metric_value'] = r2
        
        if r2 is not None:
            # Appliquer formule Session 107 Phase 2B
            amp = C3_SLOPE * r2 + C3_INTERCEPT
            amp = max(1.0, min(amp, 5.0))  # Limites sécurité
            result['amplification'] = amp
            
            if verbose:
                print(f"\n📊 Métrique calculée : R²_72h = {r2:.4f}")
                print(f"   Formule : amp = 0.5490 × {r2:.4f} + 1.6988")
                print(f"   ✅ Amplification dynamique : {amp:.3f}")
        else:
            # Fallback baseline
            result['fallback_used'] = True
            result['amplification'] = C3_BASELINE_FIXE
            if verbose:
                print(f"\n⚠️ Calcul métrique échoué → Fallback baseline : {C3_BASELINE_FIXE:.3f}")
    
    if verbose:
        print("="*80 + "\n")
    
    return result


# ============================================================================
# FONCTION HELPER : CHARGER PRIX DEPUIS DUCKDB
# ============================================================================

def load_prices_from_db(db_path: Path, event_time: pd.Timestamp, lookback_days: int = 14) -> pd.DataFrame:
    """
    Charge prix depuis DuckDB pour période lookback
    
    Parameters
    ----------
    db_path : Path
        Chemin base de données
    event_time : pd.Timestamp
        Timestamp événement
    lookback_days : int
        Jours historiques à charger
    
    Returns
    -------
    pd.DataFrame
        Prix avec colonnes ['datetime', 'close', 'high', 'low']
    """
    conn = duckdb.connect(str(db_path), read_only=True)
    
    # Période
    end_time = event_time  # JUSQU'À l'événement
    start_time = end_time - timedelta(days=lookback_days)
    
    query = f"""
    SELECT datetime, close, high, low
    FROM prices_1m
    WHERE datetime >= '{start_time.strftime('%Y-%m-%d %H:%M:%S')}'::TIMESTAMP
      AND datetime <= '{end_time.strftime('%Y-%m-%d %H:%M:%S')}'::TIMESTAMP
    ORDER BY datetime ASC
    """
    
    df_prices = conn.execute(query).fetchdf()
    conn.close()
    
    df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
    
    return df_prices


# ============================================================================
# TESTS UNITAIRES
# ============================================================================

if __name__ == "__main__":
    print("="*80)
    print("MODULE AMPLIFICATION DYNAMIQUE - TESTS UNITAIRES")
    print("="*80)
    
    # Test 1 : Détection cluster
    print("\n✅ Test 1 : Détection cluster")
    events_cpi = [{'event_key': 'US_CPI_MOM', 'label': 'CPI m/m'}]
    cluster = detect_cluster(events_cpi)
    print(f"   CPI → Cluster #{cluster} (attendu: 3)")
    assert cluster == 3, "Erreur détection CPI"
    
    events_manuf = [{'event_key': 'US_ISM_MANUFACTURING', 'label': 'ISM Manufacturing PMI'}]
    cluster = detect_cluster(events_manuf)
    print(f"   Manufacturing → Cluster #{cluster} (attendu: 1)")
    assert cluster == 1, "Erreur détection Manufacturing"
    
    print("\n" + "="*80)
    print("✅✅✅ TESTS BASIQUES PASSENT")
    print("="*80)
    print("\nℹ️ Pour tests complets, utiliser script de validation avec données réelles")
