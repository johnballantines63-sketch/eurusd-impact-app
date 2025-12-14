"""
ÉTAPE 3 - CLASSIFIER PATTERNS DES MOUVEMENTS
Session 137 - Workflow LOO-CV DoubleWave_Overlap

Mission :
1. Pour chaque mouvement (396) : charger prix ±120 min
2. Détecter pattern : DOUBLE_WAVE, SINGLE_WAVE_FORT, SINGLE_WAVE_STANDARD, INCONNU
3. Mesurer métriques patterns (peaks, timing, amplitudes)
4. Enrichir CSV final

Critères détection (Sessions 132-133) :
- DOUBLE_WAVE : 2 pics distincts séparés par creux significatif
- SINGLE_WAVE_FORT : 1 pic fort, impact > seuil
- SINGLE_WAVE_STANDARD : 1 pic modéré
- INCONNU : pattern non classifiable

Auteur: André Valentin avec Claude
Date: 14 novembre 2025
"""

import duckdb
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import timedelta
from typing import Dict, List, Tuple

# =============================================================================
# CHEMINS
# =============================================================================

DB_PATH = Path(__file__).parent.parent.parent / "data" / "warehouse.duckdb"
INPUT_CSV = Path(__file__).parent / "step2_movements_with_clusters.csv"
OUTPUT_CSV = Path(__file__).parent / "step3_movements_with_patterns.csv"

# =============================================================================
# PARAMÈTRES DÉTECTION PATTERNS
# =============================================================================

# Fenêtre analyse
WINDOW_BEFORE_MIN = 10   # 10 min avant événement
WINDOW_AFTER_MIN = 120   # 120 min après événement

# Seuils DOUBLE_WAVE
DOUBLE_WAVE_MIN_DIP_PCT = 0.30  # Creux doit être 30% de pic1
DOUBLE_WAVE_MIN_PEAK2_RATIO = 0.70  # Pic2 doit être 70% de pic1

# Seuils impact
SINGLE_WAVE_FORT_MIN_PIPS = 35.0
SINGLE_WAVE_STANDARD_MIN_PIPS = 15.0

# =============================================================================
# FONCTION CHARGEMENT PRIX
# =============================================================================

def load_prices_window(conn, movement_datetime, window_before=10, window_after=120):
    """
    Charger prix dans fenêtre autour mouvement
    
    Args:
        conn: Connexion DuckDB
        movement_datetime: datetime mouvement (Europe/Zurich)
        window_before: minutes avant
        window_after: minutes après
    
    Returns:
        DataFrame: prix (datetime, open, high, low, close)
    """
    
    start_time = movement_datetime - timedelta(minutes=window_before)
    end_time = movement_datetime + timedelta(minutes=window_after)
    
    query = """
    SELECT datetime, open, high, low, close
    FROM prices_bern
    WHERE datetime >= ?
      AND datetime <= ?
    ORDER BY datetime
    """
    
    df_prices = conn.execute(query, [start_time, end_time]).df()
    
    return df_prices

# =============================================================================
# FONCTION DÉTECTION PICS
# =============================================================================

def detect_peaks(prices: pd.Series, window: int = 5) -> List[int]:
    """
    Détecter pics locaux dans série de prix
    
    Args:
        prices: Série de prix (HIGH)
        window: Fenêtre comparaison (min de chaque côté)
    
    Returns:
        List[int]: Indices des pics
    """
    
    peaks = []
    
    for i in range(window, len(prices) - window):
        # Prix central
        current = prices.iloc[i]
        
        # Vérifier si pic local (plus haut que voisins)
        is_peak = True
        
        for j in range(1, window + 1):
            if prices.iloc[i - j] >= current or prices.iloc[i + j] >= current:
                is_peak = False
                break
        
        if is_peak:
            peaks.append(i)
    
    return peaks

def detect_troughs(prices: pd.Series, window: int = 5) -> List[int]:
    """
    Détecter creux locaux dans série de prix
    
    Args:
        prices: Série de prix (LOW)
        window: Fenêtre comparaison
    
    Returns:
        List[int]: Indices des creux
    """
    
    troughs = []
    
    for i in range(window, len(prices) - window):
        current = prices.iloc[i]
        
        is_trough = True
        
        for j in range(1, window + 1):
            if prices.iloc[i - j] <= current or prices.iloc[i + j] <= current:
                is_trough = False
                break
        
        if is_trough:
            troughs.append(i)
    
    return troughs

# =============================================================================
# FONCTION CLASSIFICATION PATTERN
# =============================================================================

def classify_pattern(df_prices: pd.DataFrame, baseline_price: float, 
                     impact_pips: float) -> Dict:
    """
    Classifier pattern mouvement
    
    Args:
        df_prices: DataFrame prix (datetime, high, low)
        baseline_price: Prix de référence (début mouvement)
        impact_pips: Impact détecté ÉTAPE 1
    
    Returns:
        Dict: {
            'pattern_type': str,
            'peak1_idx': int,
            'peak1_price': float,
            'peak1_time_min': float,
            'peak2_idx': int or None,
            'peak2_price': float or None,
            'peak2_time_min': float or None,
            'trough_idx': int or None,
            'trough_price': float or None,
            'confidence': float
        }
    """
    
    if len(df_prices) < 10:
        return {
            'pattern_type': 'INCONNU',
            'reason': 'insufficient_data',
            'confidence': 0.0
        }
    
    # 1. Détecter pics dans HIGH
    peaks_idx = detect_peaks(df_prices['high'], window=5)
    
    if len(peaks_idx) == 0:
        return {
            'pattern_type': 'INCONNU',
            'reason': 'no_peaks_detected',
            'confidence': 0.0
        }
    
    # 2. Trier pics par amplitude (descending)
    peaks_amplitudes = []
    for idx in peaks_idx:
        peak_price = df_prices['high'].iloc[idx]
        amplitude_pips = (peak_price - baseline_price) * 10000
        peaks_amplitudes.append((idx, peak_price, amplitude_pips))
    
    peaks_amplitudes.sort(key=lambda x: x[2], reverse=True)
    
    # 3. Premier pic (plus fort)
    peak1_idx, peak1_price, peak1_amp = peaks_amplitudes[0]
    peak1_time_min = (df_prices['datetime'].iloc[peak1_idx] - df_prices['datetime'].iloc[0]).total_seconds() / 60
    
    # 4. Vérifier DOUBLE_WAVE
    if len(peaks_amplitudes) >= 2:
        # Candidats pic2 : après pic1 ET amplitude significative
        peak2_candidates = [
            (idx, price, amp) for idx, price, amp in peaks_amplitudes[1:]
            if idx > peak1_idx and amp >= peak1_amp * DOUBLE_WAVE_MIN_PEAK2_RATIO
        ]
        
        if peak2_candidates:
            # Chercher creux entre peak1 et peak2
            peak2_idx, peak2_price, peak2_amp = peak2_candidates[0]
            
            # Trouver creux entre peak1 et peak2
            between_slice = df_prices['low'].iloc[peak1_idx:peak2_idx+1]
            
            if len(between_slice) > 0:
                trough_idx_relative = between_slice.idxmin()
                trough_idx = between_slice.index.get_loc(trough_idx_relative) + peak1_idx
                trough_price = df_prices['low'].iloc[trough_idx]
                
                # Vérifier profondeur creux
                dip_from_peak1 = (peak1_price - trough_price) * 10000
                dip_ratio = dip_from_peak1 / peak1_amp if peak1_amp > 0 else 0
                
                if dip_ratio >= DOUBLE_WAVE_MIN_DIP_PCT:
                    # DOUBLE_WAVE détecté !
                    peak2_time_min = (df_prices['datetime'].iloc[peak2_idx] - df_prices['datetime'].iloc[0]).total_seconds() / 60
                    
                    return {
                        'pattern_type': 'DOUBLE_WAVE',
                        'peak1_idx': peak1_idx,
                        'peak1_price': peak1_price,
                        'peak1_amplitude_pips': peak1_amp,
                        'peak1_time_min': peak1_time_min,
                        'peak2_idx': peak2_idx,
                        'peak2_price': peak2_price,
                        'peak2_amplitude_pips': peak2_amp,
                        'peak2_time_min': peak2_time_min,
                        'trough_idx': trough_idx,
                        'trough_price': trough_price,
                        'dip_ratio': dip_ratio,
                        'confidence': 0.9
                    }
    
    # 5. SINGLE_WAVE (pas de double wave détecté)
    
    # Classifier selon amplitude
    if peak1_amp >= SINGLE_WAVE_FORT_MIN_PIPS:
        pattern_type = 'SINGLE_WAVE_FORT'
        confidence = 0.85
    elif peak1_amp >= SINGLE_WAVE_STANDARD_MIN_PIPS:
        pattern_type = 'SINGLE_WAVE_STANDARD'
        confidence = 0.75
    else:
        pattern_type = 'SINGLE_WAVE_FAIBLE'
        confidence = 0.60
    
    return {
        'pattern_type': pattern_type,
        'peak1_idx': peak1_idx,
        'peak1_price': peak1_price,
        'peak1_amplitude_pips': peak1_amp,
        'peak1_time_min': peak1_time_min,
        'peak2_idx': None,
        'peak2_price': None,
        'peak2_amplitude_pips': None,
        'peak2_time_min': None,
        'trough_idx': None,
        'trough_price': None,
        'dip_ratio': None,
        'confidence': confidence
    }

# =============================================================================
# FONCTION PRINCIPALE
# =============================================================================

def classify_all_patterns():
    """
    Classifier patterns pour tous les 396 mouvements
    """
    
    print("=" * 80)
    print("ÉTAPE 3 - CLASSIFICATION PATTERNS")
    print("=" * 80)
    
    # 1. Charger CSV
    print("\n📊 ÉTAPE 1 : Chargement mouvements")
    print("-" * 80)
    
    df = pd.read_csv(INPUT_CSV)
    df['movement_datetime'] = pd.to_datetime(df['movement_datetime'], utc=True).dt.tz_convert('Europe/Zurich')
    
    print(f"   ✅ {len(df)} mouvements chargés")
    
    # 2. Connecter DB
    print("\n📊 ÉTAPE 2 : Connexion database")
    print("-" * 80)
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    print(f"   ✅ Connexion établie")
    
    # 3. Classifier patterns
    print("\n📊 ÉTAPE 3 : Classification patterns")
    print("-" * 80)
    print(f"   Fenêtre analyse : -{WINDOW_BEFORE_MIN}min à +{WINDOW_AFTER_MIN}min")
    print(f"   Seuils : FORT≥{SINGLE_WAVE_FORT_MIN_PIPS} pips, STANDARD≥{SINGLE_WAVE_STANDARD_MIN_PIPS} pips")
    print()
    
    results = []
    
    for idx, row in df.iterrows():
        movement_datetime = row['movement_datetime']
        impact_pips = row['impact_pips']
        
        try:
            # Charger prix
            df_prices = load_prices_window(
                conn, 
                movement_datetime,
                window_before=WINDOW_BEFORE_MIN,
                window_after=WINDOW_AFTER_MIN
            )
            
            if len(df_prices) == 0:
                pattern_result = {
                    'pattern_type': 'INCONNU',
                    'reason': 'no_price_data',
                    'confidence': 0.0
                }
            else:
                # Baseline = premier CLOSE
                baseline_price = df_prices['close'].iloc[0]
                
                # Classifier
                pattern_result = classify_pattern(df_prices, baseline_price, impact_pips)
            
            # Stocker
            results.append({
                'movement_id': row['movement_id'],
                **pattern_result
            })
            
            # Progress
            if (idx + 1) % 50 == 0:
                print(f"   Progression : {idx + 1}/396 mouvements ({100.0 * (idx + 1) / 396:.1f}%)")
                
        except Exception as e:
            print(f"      ❌ Erreur mouvement {idx}: {e}")
            results.append({
                'movement_id': row['movement_id'],
                'pattern_type': 'INCONNU',
                'reason': f'error: {str(e)}',
                'confidence': 0.0
            })
    
    # 4. Merger avec DataFrame
    print("\n📊 ÉTAPE 4 : Enrichissement CSV")
    print("-" * 80)
    
    df_patterns = pd.DataFrame(results)
    df_final = df.merge(df_patterns, on='movement_id', how='left')
    
    print(f"   ✅ Patterns ajoutés")
    
    # 5. Statistiques
    print("\n📊 ÉTAPE 5 : Statistiques patterns")
    print("-" * 80)
    
    pattern_counts = df_final['pattern_type'].value_counts()
    
    print(f"\n   Distribution patterns :")
    for pattern, count in pattern_counts.items():
        print(f"      {pattern:25s} : {count:3d} ({100.0 * count / len(df_final):.1f}%)")
    
    # DOUBLE_WAVE détails
    df_double = df_final[df_final['pattern_type'] == 'DOUBLE_WAVE']
    if len(df_double) > 0:
        print(f"\n   DOUBLE_WAVE détails (n={len(df_double)}) :")
        print(f"      dip_ratio moyen       : {df_double['dip_ratio'].mean():.2f}")
        print(f"      dip_ratio médian      : {df_double['dip_ratio'].median():.2f}")
        print(f"      Temps peak1→peak2 moy : {(df_double['peak2_time_min'] - df_double['peak1_time_min']).mean():.1f} min")
    
    # SINGLE_WAVE_FORT détails
    df_fort = df_final[df_final['pattern_type'] == 'SINGLE_WAVE_FORT']
    if len(df_fort) > 0:
        print(f"\n   SINGLE_WAVE_FORT détails (n={len(df_fort)}) :")
        print(f"      Amplitude moyenne     : {df_fort['peak1_amplitude_pips'].mean():.1f} pips")
        print(f"      Amplitude médiane     : {df_fort['peak1_amplitude_pips'].median():.1f} pips")
        print(f"      Temps peak moyen      : {df_fort['peak1_time_min'].mean():.1f} min")
    
    # 6. Sauvegarder
    print("\n📊 ÉTAPE 6 : Sauvegarde CSV final")
    print("-" * 80)
    
    df_final.to_csv(OUTPUT_CSV, index=False)
    
    print(f"   ✅ Fichier créé : {OUTPUT_CSV}")
    print(f"   Colonnes : {len(df_final.columns)}")
    print(f"   Lignes   : {len(df_final)}")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("ÉTAPE 3 COMPLÉTÉE !")
    print("=" * 80)
    print(f"\n📋 RÉSULTAT : 396 mouvements classifiés par pattern")
    
    return pattern_counts

if __name__ == '__main__':
    counts = classify_all_patterns()
