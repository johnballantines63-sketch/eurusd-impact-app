"""
ÉTAPE 3 V2 - CLASSIFIER PATTERNS (DIRECTION-AWARE)
Session 138 - Refonte algorithme avec direction-awareness

Corrections majeures vs V1:
- Direction-awareness obligatoire (UP/DOWN)
- Logiques séparées: classify_bullish_pattern() / classify_bearish_pattern()
- Critères stricts: MIN_AMPLITUDE=20, dip_ratio=[0.30,0.70]
- Vérification position trough/peak vs baseline
- 6 patterns distincts: UP et DOWN pour chaque type

Mission:
1. Charger mouvements avec direction (step1 CSV)
2. Router selon direction vers logique appropriée
3. Appliquer critères stricts
4. Créer step3_movements_with_patterns_v2.csv

Auteur: André Valentin avec Claude
Date: 14 novembre 2025
Session: 138
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

# INPUT: Utiliser step2_movements_with_clusters.csv (contient colonne 'direction')
INPUT_CSV = Path(__file__).parent / "step2_movements_with_clusters.csv"
OUTPUT_CSV = Path(__file__).parent / "step3_movements_with_patterns_v2.csv"

# =============================================================================
# PARAMÈTRES DÉTECTION PATTERNS (CRITÈRES STRICTS)
# =============================================================================

# Fenêtre analyse
WINDOW_BEFORE_MIN = 10   # 10 min avant événement
WINDOW_AFTER_MIN = 120   # 120 min après événement

# CRITÈRES STRICTS (nouveaux)
MIN_AMPLITUDE = 20.0            # pips minimum (filtrer bruit)
MIN_DIP_RATIO = 0.30           # 30% minimum
MAX_DIP_RATIO = 0.70           # 70% maximum (filtrer extrêmes)

# Seuils classification finale
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
# FONCTIONS DÉTECTION PICS/CREUX
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
# FONCTION CLASSIFICATION BULLISH (MOUVEMENTS UP)
# =============================================================================

def classify_bullish_pattern(df_prices: pd.DataFrame, baseline_price: float, 
                            impact_pips: float) -> Dict:
    """
    Classifier pattern mouvement BULLISH (montant)
    
    Logique:
    1. Détecter pics dans HIGH
    2. Premier pic = plus fort
    3. CRITÈRE STRICT: peak1 >= 20 pips
    4. Chercher peak2 après peak1
    5. Si peak2 existe:
        a. Trouver trough entre peak1 et peak2
        b. CRITÈRE STRICT: trough > baseline (sinon CRASH_RECOVERY)
        c. Calculer dip_ratio = (peak1 - trough) / peak1_amplitude
        d. CRITÈRE STRICT: 0.30 ≤ dip_ratio ≤ 0.70
    6. Sinon SINGLE_WAVE selon amplitude
    
    Args:
        df_prices: DataFrame prix
        baseline_price: Prix référence
        impact_pips: Impact détecté step1
    
    Returns:
        Dict: pattern_type et métriques
    """
    
    if len(df_prices) < 10:
        return {
            'pattern_type': 'INCONNU',
            'reason': 'insufficient_data',
            'confidence': 0.0
        }
    
    # ÉTAPE 1: Détecter pics dans HIGH
    peaks_idx = detect_peaks(df_prices['high'], window=5)
    
    if len(peaks_idx) == 0:
        return {
            'pattern_type': 'INCONNU',
            'reason': 'no_peaks_detected',
            'confidence': 0.0
        }
    
    # ÉTAPE 2: Calculer amplitudes tous pics (filtre positifs)
    peaks_amplitudes = []
    for idx in peaks_idx:
        peak_price = df_prices['high'].iloc[idx]
        amplitude_pips = (peak_price - baseline_price) * 10000
        
        # Ne garder que pics au-dessus baseline
        if amplitude_pips > 0:
            peaks_amplitudes.append((idx, peak_price, amplitude_pips))
    
    if len(peaks_amplitudes) == 0:
        return {
            'pattern_type': 'INCONNU',
            'reason': 'no_peaks_above_baseline',
            'confidence': 0.0
        }
    
    # Trier par amplitude (descending)
    peaks_amplitudes.sort(key=lambda x: x[2], reverse=True)
    
    # ÉTAPE 3: Premier pic (plus fort)
    peak1_idx, peak1_price, peak1_amp = peaks_amplitudes[0]
    peak1_time_min = (df_prices['datetime'].iloc[peak1_idx] - df_prices['datetime'].iloc[0]).total_seconds() / 60
    
    # CRITÈRE STRICT: Peak1 minimum 20 pips
    if peak1_amp < MIN_AMPLITUDE:
        return {
            'pattern_type': 'SINGLE_WAVE_FAIBLE_UP',
            'reason': 'peak1_below_minimum',
            'peak1_amplitude_pips': peak1_amp,
            'peak1_time_min': peak1_time_min,
            'confidence': 0.5
        }
    
    # ÉTAPE 4: Chercher peak2 candidats (après peak1, amplitude >= 20 pips)
    peak2_candidates = [
        (idx, price, amp) for idx, price, amp in peaks_amplitudes[1:]
        if idx > peak1_idx and amp >= MIN_AMPLITUDE
    ]
    
    if peak2_candidates:
        # Prendre premier candidat (plus fort après peak1)
        peak2_idx, peak2_price, peak2_amp = peak2_candidates[0]
        
        # ÉTAPE 5: Trouver trough entre peak1 et peak2
        between_slice = df_prices['low'].iloc[peak1_idx:peak2_idx+1]
        
        if len(between_slice) > 0:
            trough_idx_relative = between_slice.idxmin()
            trough_idx = between_slice.index.get_loc(trough_idx_relative) + peak1_idx
            trough_price = df_prices['low'].iloc[trough_idx]
            
            # CRITÈRE STRICT: Trough doit être > baseline
            if trough_price < baseline_price:
                # Pattern = CRASH puis RECOVERY (pas double wave)
                return {
                    'pattern_type': 'CRASH_RECOVERY_UP',
                    'reason': 'trough_below_baseline',
                    'peak1_amplitude_pips': peak1_amp,
                    'peak1_time_min': peak1_time_min,
                    'trough_price': trough_price,
                    'baseline_price': baseline_price,
                    'confidence': 0.8
                }
            
            # ÉTAPE 6: Calculer dip_ratio
            dip_from_peak1 = (peak1_price - trough_price) * 10000
            dip_ratio = dip_from_peak1 / peak1_amp if peak1_amp > 0 else 0
            
            # CRITÈRE STRICT: dip_ratio dans [0.30, 0.70]
            if MIN_DIP_RATIO <= dip_ratio <= MAX_DIP_RATIO:
                # DOUBLE_WAVE détecté !
                peak2_time_min = (df_prices['datetime'].iloc[peak2_idx] - df_prices['datetime'].iloc[0]).total_seconds() / 60
                
                return {
                    'pattern_type': 'DOUBLE_WAVE_UP',
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
            # Si dip_ratio hors range [0.30,0.70] → continue vers SINGLE_WAVE
    
    # ÉTAPE 7: SINGLE_WAVE (pas de double wave valide)
    
    # Classifier selon amplitude peak1
    if peak1_amp >= SINGLE_WAVE_FORT_MIN_PIPS:
        pattern_type = 'SINGLE_WAVE_FORT_UP'
        confidence = 0.85
    elif peak1_amp >= SINGLE_WAVE_STANDARD_MIN_PIPS:
        pattern_type = 'SINGLE_WAVE_STANDARD_UP'
        confidence = 0.75
    else:
        pattern_type = 'SINGLE_WAVE_FAIBLE_UP'
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
# FONCTION CLASSIFICATION BEARISH (MOUVEMENTS DOWN)
# =============================================================================

def classify_bearish_pattern(df_prices: pd.DataFrame, baseline_price: float, 
                            impact_pips: float) -> Dict:
    """
    Classifier pattern mouvement BEARISH (descendant)
    
    Logique INVERSÉE:
    1. Détecter creux dans LOW
    2. Premier creux = plus profond
    3. CRITÈRE STRICT: trough1 >= 20 pips
    4. Chercher trough2 après trough1
    5. Si trough2 existe:
        a. Trouver peak entre trough1 et trough2
        b. CRITÈRE STRICT: peak < baseline (sinon SPIKE_REVERSAL)
        c. Calculer rise_ratio = (peak - trough1) / trough1_amplitude
        d. CRITÈRE STRICT: 0.30 ≤ rise_ratio ≤ 0.70
    6. Sinon SINGLE_WAVE selon amplitude
    
    Args:
        df_prices: DataFrame prix
        baseline_price: Prix référence
        impact_pips: Impact détecté step1
    
    Returns:
        Dict: pattern_type et métriques
    """
    
    if len(df_prices) < 10:
        return {
            'pattern_type': 'INCONNU',
            'reason': 'insufficient_data',
            'confidence': 0.0
        }
    
    # ÉTAPE 1: Détecter creux dans LOW
    troughs_idx = detect_troughs(df_prices['low'], window=5)
    
    if len(troughs_idx) == 0:
        return {
            'pattern_type': 'INCONNU',
            'reason': 'no_troughs_detected',
            'confidence': 0.0
        }
    
    # ÉTAPE 2: Calculer amplitudes tous creux (filtre positifs)
    troughs_amplitudes = []
    for idx in troughs_idx:
        trough_price = df_prices['low'].iloc[idx]
        amplitude_pips = (baseline_price - trough_price) * 10000  # Inversé !
        
        # Ne garder que creux en dessous baseline
        if amplitude_pips > 0:
            troughs_amplitudes.append((idx, trough_price, amplitude_pips))
    
    if len(troughs_amplitudes) == 0:
        return {
            'pattern_type': 'INCONNU',
            'reason': 'no_troughs_below_baseline',
            'confidence': 0.0
        }
    
    # Trier par amplitude (descending)
    troughs_amplitudes.sort(key=lambda x: x[2], reverse=True)
    
    # ÉTAPE 3: Premier creux (plus profond)
    trough1_idx, trough1_price, trough1_amp = troughs_amplitudes[0]
    trough1_time_min = (df_prices['datetime'].iloc[trough1_idx] - df_prices['datetime'].iloc[0]).total_seconds() / 60
    
    # CRITÈRE STRICT: Trough1 minimum 20 pips
    if trough1_amp < MIN_AMPLITUDE:
        return {
            'pattern_type': 'SINGLE_WAVE_FAIBLE_DOWN',
            'reason': 'trough1_below_minimum',
            'trough1_amplitude_pips': trough1_amp,
            'trough1_time_min': trough1_time_min,
            'confidence': 0.5
        }
    
    # ÉTAPE 4: Chercher trough2 candidats (après trough1, amplitude >= 20 pips)
    trough2_candidates = [
        (idx, price, amp) for idx, price, amp in troughs_amplitudes[1:]
        if idx > trough1_idx and amp >= MIN_AMPLITUDE
    ]
    
    if trough2_candidates:
        # Prendre premier candidat (plus profond après trough1)
        trough2_idx, trough2_price, trough2_amp = trough2_candidates[0]
        
        # ÉTAPE 5: Trouver peak entre trough1 et trough2 (recovery)
        between_slice = df_prices['high'].iloc[trough1_idx:trough2_idx+1]
        
        if len(between_slice) > 0:
            peak_idx_relative = between_slice.idxmax()
            peak_idx = between_slice.index.get_loc(peak_idx_relative) + trough1_idx
            peak_price = df_prices['high'].iloc[peak_idx]
            
            # CRITÈRE STRICT: Peak doit être < baseline
            if peak_price > baseline_price:
                # Pattern = SPIKE puis REVERSAL (pas double wave)
                return {
                    'pattern_type': 'SPIKE_REVERSAL_DOWN',
                    'reason': 'peak_above_baseline',
                    'trough1_amplitude_pips': trough1_amp,
                    'trough1_time_min': trough1_time_min,
                    'peak_price': peak_price,
                    'baseline_price': baseline_price,
                    'confidence': 0.8
                }
            
            # ÉTAPE 6: Calculer rise_ratio (équivalent dip_ratio)
            rise_from_trough1 = (peak_price - trough1_price) * 10000
            rise_ratio = rise_from_trough1 / trough1_amp if trough1_amp > 0 else 0
            
            # CRITÈRE STRICT: rise_ratio dans [0.30, 0.70]
            if MIN_DIP_RATIO <= rise_ratio <= MAX_DIP_RATIO:
                # DOUBLE_WAVE détecté !
                trough2_time_min = (df_prices['datetime'].iloc[trough2_idx] - df_prices['datetime'].iloc[0]).total_seconds() / 60
                
                return {
                    'pattern_type': 'DOUBLE_WAVE_DOWN',
                    'trough1_idx': trough1_idx,
                    'trough1_price': trough1_price,
                    'trough1_amplitude_pips': trough1_amp,
                    'trough1_time_min': trough1_time_min,
                    'trough2_idx': trough2_idx,
                    'trough2_price': trough2_price,
                    'trough2_amplitude_pips': trough2_amp,
                    'trough2_time_min': trough2_time_min,
                    'peak_idx': peak_idx,
                    'peak_price': peak_price,
                    'rise_ratio': rise_ratio,
                    'confidence': 0.9
                }
            # Si rise_ratio hors range [0.30,0.70] → continue vers SINGLE_WAVE
    
    # ÉTAPE 7: SINGLE_WAVE (pas de double wave valide)
    
    # Classifier selon amplitude trough1
    if trough1_amp >= SINGLE_WAVE_FORT_MIN_PIPS:
        pattern_type = 'SINGLE_WAVE_FORT_DOWN'
        confidence = 0.85
    elif trough1_amp >= SINGLE_WAVE_STANDARD_MIN_PIPS:
        pattern_type = 'SINGLE_WAVE_STANDARD_DOWN'
        confidence = 0.75
    else:
        pattern_type = 'SINGLE_WAVE_FAIBLE_DOWN'
        confidence = 0.60
    
    return {
        'pattern_type': pattern_type,
        'trough1_idx': trough1_idx,
        'trough1_price': trough1_price,
        'trough1_amplitude_pips': trough1_amp,
        'trough1_time_min': trough1_time_min,
        'trough2_idx': None,
        'trough2_price': None,
        'trough2_amplitude_pips': None,
        'trough2_time_min': None,
        'peak_idx': None,
        'peak_price': None,
        'rise_ratio': None,
        'confidence': confidence
    }

# =============================================================================
# FONCTION ROUTAGE PRINCIPAL (DIRECTION-AWARE)
# =============================================================================

def classify_pattern(df_prices: pd.DataFrame, baseline_price: float, 
                     impact_pips: float, direction: str) -> Dict:
    """
    Router vers logique appropriée selon direction
    
    Args:
        df_prices: DataFrame prix (datetime, high, low)
        baseline_price: Prix de référence (début mouvement)
        impact_pips: Impact détecté ÉTAPE 1
        direction: "UP" ou "DOWN" depuis step1 CSV
    
    Returns:
        Dict: pattern_type et métriques
    """
    
    if direction == "UP":
        return classify_bullish_pattern(df_prices, baseline_price, impact_pips)
    elif direction == "DOWN":
        return classify_bearish_pattern(df_prices, baseline_price, impact_pips)
    else:
        return {
            'pattern_type': 'INCONNU',
            'reason': f'direction_unknown: {direction}',
            'confidence': 0.0
        }

# =============================================================================
# FONCTION PRINCIPALE
# =============================================================================

def classify_all_patterns_v2():
    """
    Classifier patterns pour tous mouvements (direction-aware)
    """
    
    print("=" * 80)
    print("ÉTAPE 3 V2 - CLASSIFICATION PATTERNS (DIRECTION-AWARE)")
    print("=" * 80)
    
    # 1. Charger CSV step2 (avec direction)
    print("\n📊 ÉTAPE 1 : Chargement mouvements (step2)")
    print("-" * 80)
    
    if not INPUT_CSV.exists():
        print(f"   ❌ ERREUR: {INPUT_CSV} introuvable")
        return None
    
    df = pd.read_csv(INPUT_CSV)
    df['movement_datetime'] = pd.to_datetime(df['movement_datetime'], utc=True).dt.tz_convert('Europe/Zurich')
    
    # Vérifier colonne direction
    if 'direction' not in df.columns:
        print("   ❌ ERREUR: Colonne 'direction' absente dans step2 CSV")
        return None
    
    print(f"   ✅ {len(df)} mouvements chargés")
    print(f"   Direction UP   : {(df['direction'] == 'UP').sum()} ({100.0 * (df['direction'] == 'UP').sum() / len(df):.1f}%)")
    print(f"   Direction DOWN : {(df['direction'] == 'DOWN').sum()} ({100.0 * (df['direction'] == 'DOWN').sum() / len(df):.1f}%)")
    
    # 2. Connecter DB
    print("\n📊 ÉTAPE 2 : Connexion database")
    print("-" * 80)
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    print(f"   ✅ Connexion établie")
    
    # 3. Classifier patterns
    print("\n📊 ÉTAPE 3 : Classification patterns (direction-aware)")
    print("-" * 80)
    print(f"   Fenêtre analyse : -{WINDOW_BEFORE_MIN}min à +{WINDOW_AFTER_MIN}min")
    print(f"   CRITÈRES STRICTS :")
    print(f"      MIN_AMPLITUDE   : {MIN_AMPLITUDE} pips")
    print(f"      dip/rise_ratio  : [{MIN_DIP_RATIO}, {MAX_DIP_RATIO}]")
    print(f"      FORT threshold  : {SINGLE_WAVE_FORT_MIN_PIPS} pips")
    print(f"      STD threshold   : {SINGLE_WAVE_STANDARD_MIN_PIPS} pips")
    print()
    
    results = []
    
    for idx, row in df.iterrows():
        movement_datetime = row['movement_datetime']
        impact_pips = row['impact_pips']
        direction = row['direction']
        
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
                
                # Classifier avec direction
                pattern_result = classify_pattern(df_prices, baseline_price, impact_pips, direction)
            
            # Stocker
            results.append({
                'movement_id': row['movement_id'],
                **pattern_result
            })
            
            # Progress
            if (idx + 1) % 50 == 0:
                print(f"   Progression : {idx + 1}/{len(df)} mouvements ({100.0 * (idx + 1) / len(df):.1f}%)")
                
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
        print(f"      {pattern:30s} : {count:3d} ({100.0 * count / len(df_final):.1f}%)")
    
    # DOUBLE_WAVE UP détails
    df_double_up = df_final[df_final['pattern_type'] == 'DOUBLE_WAVE_UP']
    if len(df_double_up) > 0:
        print(f"\n   DOUBLE_WAVE_UP détails (n={len(df_double_up)}) :")
        print(f"      dip_ratio moyen       : {df_double_up['dip_ratio'].mean():.3f}")
        print(f"      dip_ratio médian      : {df_double_up['dip_ratio'].median():.3f}")
        if 'peak2_time_min' in df_double_up.columns and 'peak1_time_min' in df_double_up.columns:
            print(f"      Temps peak1→peak2 moy : {(df_double_up['peak2_time_min'] - df_double_up['peak1_time_min']).mean():.1f} min")
    
    # DOUBLE_WAVE DOWN détails
    df_double_down = df_final[df_final['pattern_type'] == 'DOUBLE_WAVE_DOWN']
    if len(df_double_down) > 0:
        print(f"\n   DOUBLE_WAVE_DOWN détails (n={len(df_double_down)}) :")
        print(f"      rise_ratio moyen      : {df_double_down['rise_ratio'].mean():.3f}")
        print(f"      rise_ratio médian     : {df_double_down['rise_ratio'].median():.3f}")
        if 'trough2_time_min' in df_double_down.columns and 'trough1_time_min' in df_double_down.columns:
            print(f"      Temps trough1→trough2 : {(df_double_down['trough2_time_min'] - df_double_down['trough1_time_min']).mean():.1f} min")
    
    # SINGLE_WAVE_FORT UP/DOWN détails
    df_fort_up = df_final[df_final['pattern_type'] == 'SINGLE_WAVE_FORT_UP']
    if len(df_fort_up) > 0:
        print(f"\n   SINGLE_WAVE_FORT_UP détails (n={len(df_fort_up)}) :")
        print(f"      Amplitude moyenne     : {df_fort_up['peak1_amplitude_pips'].mean():.1f} pips")
        print(f"      Amplitude médiane     : {df_fort_up['peak1_amplitude_pips'].median():.1f} pips")
    
    df_fort_down = df_final[df_final['pattern_type'] == 'SINGLE_WAVE_FORT_DOWN']
    if len(df_fort_down) > 0:
        print(f"\n   SINGLE_WAVE_FORT_DOWN détails (n={len(df_fort_down)}) :")
        print(f"      Amplitude moyenne     : {df_fort_down['trough1_amplitude_pips'].mean():.1f} pips")
        print(f"      Amplitude médiane     : {df_fort_down['trough1_amplitude_pips'].median():.1f} pips")
    
    # 6. Sauvegarder
    print("\n📊 ÉTAPE 6 : Sauvegarde CSV final")
    print("-" * 80)
    
    df_final.to_csv(OUTPUT_CSV, index=False)
    
    print(f"   ✅ Fichier créé : {OUTPUT_CSV}")
    print(f"   Colonnes : {len(df_final.columns)}")
    print(f"   Lignes   : {len(df_final)}")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("ÉTAPE 3 V2 COMPLÉTÉE !")
    print("=" * 80)
    print(f"\n📋 RÉSULTAT : {len(df)} mouvements classifiés (direction-aware)")
    
    return df_final, pattern_counts

if __name__ == '__main__':
    df_final, counts = classify_all_patterns_v2()
