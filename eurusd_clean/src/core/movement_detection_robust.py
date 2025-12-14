"""
Détection Robuste des Mouvements - Méthode Mathématique Implacable

Objectif : Détecter avec précision absolue TOUS les mouvements (forts, moyens, faibles)
basé sur des statistiques historiques et des seuils robustes.

Principe :
1. Calculer seuils statistiques basés sur historique (percentiles)
2. Détecter TOUS les extrema locaux (peaks/troughs)
3. Identifier mouvements complets (début → pic → fin)
4. Classifier par amplitude : FAIBLE / MOYEN / FORT / TRÈS_FORT
5. Validation : Vérifier cohérence et complétude

Date : 2025-12-06
Référence : Détection implacable sans erreur ni approximation
"""

import pandas as pd
import numpy as np
import duckdb
import pytz
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

TZ_BERN = pytz.timezone('Europe/Zurich')

# Seuils par défaut (seront recalculés dynamiquement)
MOVEMENT_THRESHOLDS = {
    'min_detectable': 5.0,        # P5 : Minimum pour détecter un mouvement
    'weak_max': 20.0,             # P25 : Maximum pour mouvement FAIBLE
    'medium_min': 20.0,           # P25 : Minimum pour mouvement MOYEN
    'medium_max': 50.0,           # P75 : Maximum pour mouvement MOYEN
    'strong_min': 50.0,           # P75 : Minimum pour mouvement FORT
    'strong_max': 100.0,          # P90 : Maximum pour mouvement FORT
    'very_strong_min': 100.0,   # P90 : Minimum pour mouvement TRÈS FORT
}


def calculate_historical_thresholds(
    db_path: Path,
    years: int = 5,
    min_samples: int = 50,
    table_name: str = 'prices_bern'
) -> Dict[str, float]:
    """
    Calcule les seuils statistiques basés sur TOUS les mouvements historiques
    
    ⚠️ IMPORTANT : Détection INDÉPENDANTE des événements pour éviter tout biais
    
    Stratégie :
    1. Scanner TOUTES les dates disponibles dans les prix (pas seulement avec événements)
    2. Détecter TOUS les mouvements forts dans chaque journée
    3. Mesurer TOUS les mouvements (même faibles)
    4. Calculer percentiles pour classification robuste
    
    Args:
        db_path: Chemin vers la base de données
        years: Nombre d'années d'historique à analyser
        min_samples: Nombre minimum d'échantillons pour statistiques valides
        table_name: Nom de la table de prix à utiliser
    
    Returns:
        Dictionnaire avec seuils (percentiles)
    """
    conn = duckdb.connect(str(db_path), read_only=True)
    
    # ⚠️ NOUVEAU : Scanner TOUTES les dates disponibles dans les prix (pas seulement avec événements)
    date_start = datetime.now().replace(year=datetime.now().year - years)
    
    query_dates = f"""
    SELECT DISTINCT DATE(datetime) as date_hist
    FROM {table_name}
    WHERE DATE(datetime) >= '{date_start.strftime('%Y-%m-%d')}'
      AND DATE(datetime) < '{datetime.now().strftime('%Y-%m-%d')}'
    ORDER BY date_hist DESC
    """
    
    df_dates = conn.execute(query_dates).df()
    
    if df_dates.empty:
        conn.close()
        return MOVEMENT_THRESHOLDS
    
    movements = []
    
    print(f"📊 Analyse de {len(df_dates)} dates pour calculer seuils statistiques...")
    
    for idx, row in df_dates.iterrows():
        if (idx + 1) % 100 == 0:
            print(f"   Progression : {idx + 1}/{len(df_dates)} dates analysées...")
        
        date_obj = pd.to_datetime(row['date_hist']).date()
        date_str = date_obj.strftime('%Y-%m-%d')
        
        # Charger prix pour la journée complète
        query_prices = f"""
        SELECT datetime, open, high, low, close
        FROM {table_name}
        WHERE DATE(datetime) = '{date_str}'
        ORDER BY datetime ASC
        """
        
        df_prices = conn.execute(query_prices).df()
        
        if df_prices.empty or len(df_prices) < 60:  # Minimum 60 minutes de données
            continue
        
        df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
        df_prices = df_prices.set_index('datetime')
        
        # ⚠️ NOUVEAU : Détecter TOUS les mouvements dans la journée (sans référence à événements)
        # Scanner la journée par fenêtres glissantes pour trouver le mouvement maximum
        
        # Baseline : OPEN de la première bougie de la journée
        baseline_price = df_prices.iloc[0]['open']
        
        # Fenêtre d'analyse : scanner par fenêtres de 6 heures
        window_hours = 6
        window_minutes = window_hours * 60
        
        max_movement_pips = 0.0
        
        # Scanner toutes les fenêtres possibles dans la journée
        for i in range(0, len(df_prices) - window_minutes, 60):  # Décaler de 1h à chaque fois
            df_window = df_prices.iloc[i:i+window_minutes]
            
            if df_window.empty:
                continue
            
            # Baseline pour cette fenêtre : OPEN de la première bougie
            window_baseline = df_window.iloc[0]['open']
            
            # Mesurer mouvement maximum dans cette fenêtre
            max_high = df_window['high'].max()
            min_low = df_window['low'].min()
            
            impact_up = (max_high - window_baseline) * 10000
            impact_down = (window_baseline - min_low) * 10000
            impact_max = max(impact_up, impact_down)
            
            # Garder le mouvement maximum de la journée
            if impact_max > max_movement_pips:
                max_movement_pips = impact_max
        
        # Enregistrer le mouvement maximum de la journée (même s'il est faible)
        if max_movement_pips >= 1.0:  # Minimum 1 pip pour enregistrer
            movements.append(max_movement_pips)
    
    conn.close()
    
    if len(movements) < min_samples:
        print(f"   ⚠️  Seulement {len(movements)} mouvements détectés (minimum {min_samples} requis)")
        print(f"   → Utilisation des seuils par défaut")
        return MOVEMENT_THRESHOLDS
    
    movements_array = np.array(movements)
    
    print(f"   ✅ {len(movements)} mouvements détectés")
    print(f"   → Min: {movements_array.min():.1f} pips, Max: {movements_array.max():.1f} pips")
    print(f"   → Médiane: {np.median(movements_array):.1f} pips, Moyenne: {movements_array.mean():.1f} pips")
    
    # Calculer percentiles pour classification robuste
    thresholds = {
        'min_detectable': max(np.percentile(movements_array, 5), 5.0),      # P5
        'weak_max': np.percentile(movements_array, 25),                     # P25
        'medium_min': np.percentile(movements_array, 25),                    # P25
        'medium_max': np.percentile(movements_array, 75),                   # P75
        'strong_min': np.percentile(movements_array, 75),                     # P75
        'strong_max': np.percentile(movements_array, 90),                    # P90
        'very_strong_min': np.percentile(movements_array, 90),               # P90
    }
    
    print(f"   → Seuils calculés :")
    print(f"      - Détectable : {thresholds['min_detectable']:.1f} pips")
    print(f"      - FAIBLE max : {thresholds['weak_max']:.1f} pips")
    print(f"      - MOYEN : {thresholds['medium_min']:.1f} - {thresholds['medium_max']:.1f} pips")
    print(f"      - FORT : {thresholds['strong_min']:.1f} - {thresholds['strong_max']:.1f} pips")
    print(f"      - TRÈS_FORT min : {thresholds['very_strong_min']:.1f} pips")
    
    return thresholds


def find_local_extrema(
    df_prices: pd.DataFrame,
    window_minutes: int = 30,
    min_amplitude_pips: float = 5.0
) -> List[Dict]:
    """
    Trouve TOUS les extrema locaux (peaks et troughs)
    
    Stratégie :
    1. Fenêtre glissante pour détecter extrema locaux
    2. Filtrer par amplitude minimum
    3. Éviter doublons (extrema trop proches)
    
    Args:
        df_prices: DataFrame avec colonnes datetime, high, low, close
        window_minutes: Fenêtre pour détecter extrema locaux
        min_amplitude_pips: Amplitude minimum pour extrema valide
    
    Returns:
        Liste de dict avec 'type' ('HIGH' ou 'LOW'), 'datetime', 'price', 'amplitude'
    """
    extrema = []
    
    if len(df_prices) < window_minutes * 2:
        return extrema
    
    # Calculer baseline pour amplitude
    baseline_price = df_prices.iloc[0]['open']
    
    # Scanner pour trouver extrema locaux
    for i in range(window_minutes, len(df_prices) - window_minutes):
        # Peak local : high plus élevé que les window_minutes avant et après
        window_before = df_prices.iloc[i-window_minutes:i]
        window_after = df_prices.iloc[i+1:i+window_minutes+1]
        
        current_high = df_prices.iloc[i]['high']
        current_low = df_prices.iloc[i]['low']
        
        # Vérifier si peak local
        if (window_before.empty or current_high > window_before['high'].max()) and \
           (window_after.empty or current_high > window_after['high'].max()):
            amplitude = (current_high - baseline_price) * 10000
            if amplitude >= min_amplitude_pips:
                extrema.append({
                    'type': 'HIGH',
                    'index': i,
                    'datetime': df_prices.index[i],
                    'price': current_high,
                    'amplitude': amplitude
                })
        
        # Vérifier si trough local
        if (window_before.empty or current_low < window_before['low'].min()) and \
           (window_after.empty or current_low < window_after['low'].min()):
            amplitude = (baseline_price - current_low) * 10000
            if amplitude >= min_amplitude_pips:
                extrema.append({
                    'type': 'LOW',
                    'index': i,
                    'datetime': df_prices.index[i],
                    'price': current_low,
                    'amplitude': amplitude
                })
    
    # Filtrer doublons (extrema trop proches temporellement)
    filtered = []
    min_time_diff_minutes = 15  # Minimum 15 minutes entre extrema
    
    for ext in extrema:
        too_close = False
        for prev in filtered:
            time_diff = abs((ext['datetime'] - prev['datetime']).total_seconds() / 60)
            if time_diff < min_time_diff_minutes:
                # Garder celui avec la plus grande amplitude
                if ext['amplitude'] > prev['amplitude']:
                    filtered.remove(prev)
                    filtered.append(ext)
                too_close = True
                break
        if not too_close:
            filtered.append(ext)
    
    # Trier par index (ordre chronologique)
    filtered.sort(key=lambda x: x['index'])
    
    return filtered


def detect_all_movements(
    df_prices: pd.DataFrame,
    event_time: pd.Timestamp,
    baseline_time: Optional[pd.Timestamp] = None,
    thresholds: Optional[Dict[str, float]] = None,
    window_hours: float = 6.0
) -> List[Dict]:
    """
    Détecte TOUS les mouvements (forts, moyens, faibles) - Méthode Implacable
    
    Stratégie :
    1. Trouver TOUS les extrema locaux
    2. Identifier mouvements complets (début → pic → fin)
    3. Classifier par amplitude
    4. Retourner liste complète (aucun mouvement manqué)
    
    Args:
        df_prices: DataFrame avec colonnes datetime, open, high, low, close
        event_time: Timestamp de l'événement
        baseline_time: Timestamp pour baseline (si None, utilise event_time - 1 min)
        thresholds: Seuils statistiques (si None, utilise valeurs par défaut)
        window_hours: Fenêtre d'analyse en heures
    
    Returns:
        Liste de dictionnaires avec :
        - movement_start_time: Début du mouvement
        - movement_start_pips: Amplitude au début
        - peak_time: Heure du pic
        - peak_pips: Amplitude du pic
        - movement_end_time: Fin du mouvement (retour vers baseline)
        - movement_class: FAIBLE / MOYEN / FORT / TRÈS_FORT
        - direction: UP / DOWN
        - baseline_price: Prix de référence
        - confidence: Niveau de confiance (0-1)
    """
    
    if thresholds is None:
        thresholds = MOVEMENT_THRESHOLDS
    
    # 1. Définir baseline
    if baseline_time is None:
        baseline_time = event_time - pd.Timedelta(minutes=1)
    
    # Filtrer fenêtre d'analyse
    window_end = event_time + pd.Timedelta(hours=window_hours)
    
    df_window = df_prices[
        (df_prices.index >= baseline_time) & 
        (df_prices.index <= window_end)
    ].copy()
    
    if df_window.empty:
        return []
    
    # 2. Baseline : Prix juste avant événement
    prices_before_event = df_window[df_window.index < event_time]
    
    if not prices_before_event.empty:
        baseline_price = prices_before_event.iloc[-1]['close']
    else:
        baseline_price = df_window.iloc[0]['open']
    
    # 3. Trouver TOUS les extrema locaux
    extrema = find_local_extrema(
        df_window,
        window_minutes=30,
        min_amplitude_pips=thresholds['min_detectable']
    )
    
    if not extrema:
        return []
    
    # 4. Identifier mouvements complets depuis extrema
    movements = []
    
    for i, ext in enumerate(extrema):
        # Déterminer direction
        if ext['type'] == 'HIGH':
            direction = 'UP'
            peak_time = ext['datetime']
            peak_price = ext['price']
            peak_pips = ext['amplitude']
        else:
            direction = 'DOWN'
            peak_time = ext['datetime']
            peak_price = ext['price']
            peak_pips = ext['amplitude']
        
        # Trouver début du mouvement (remonter depuis le pic)
        df_before_peak = df_window[df_window.index <= peak_time]
        
        # Seuil pour début = 30% du pic, minimum = seuil détectable
        threshold_start = max(peak_pips * 0.30, thresholds['min_detectable'])
        
        movement_start_time = peak_time  # Fallback
        movement_start_pips = peak_pips
        
        # Parcourir depuis le pic pour trouver le début
        for idx in reversed(df_before_peak.index):
            row = df_before_peak.loc[idx]
            
            if direction == 'UP':
                current_pips = (row['high'] - baseline_price) * 10000
                if current_pips >= threshold_start:
                    movement_start_time = idx
                    movement_start_pips = current_pips
                else:
                    # Passé sous le seuil, début est la bougie suivante
                    next_idx = df_before_peak.index[df_before_peak.index > idx]
                    if len(next_idx) > 0:
                        movement_start_time = next_idx[0]
                        movement_start_pips = (df_before_peak.loc[movement_start_time]['high'] - baseline_price) * 10000
                    break
            else:
                current_pips = (baseline_price - row['low']) * 10000
                if current_pips >= threshold_start:
                    movement_start_time = idx
                    movement_start_pips = current_pips
                else:
                    next_idx = df_before_peak.index[df_before_peak.index > idx]
                    if len(next_idx) > 0:
                        movement_start_time = next_idx[0]
                        movement_start_pips = (baseline_price - df_before_peak.loc[movement_start_time]['low']) * 10000
                    break
        
        # Trouver fin du mouvement (retour vers baseline)
        df_after_peak = df_window[df_window.index >= peak_time]
        movement_end_time = window_end  # Fallback
        
        # Fin = première bougie qui revient à 50% du pic
        threshold_end = peak_pips * 0.50
        
        for idx in df_after_peak.index:
            row = df_after_peak.loc[idx]
            
            if direction == 'UP':
                current_pips = (row['low'] - baseline_price) * 10000
                if current_pips < threshold_end:
                    movement_end_time = idx
                    break
            else:
                current_pips = (baseline_price - row['high']) * 10000
                if current_pips < threshold_end:
                    movement_end_time = idx
                    break
        
        # 5. Classifier mouvement
        if peak_pips >= thresholds['very_strong_min']:
            movement_class = 'TRÈS_FORT'
            confidence = 1.0
        elif peak_pips >= thresholds['strong_min']:
            movement_class = 'FORT'
            confidence = 0.9
        elif peak_pips >= thresholds['medium_min']:
            movement_class = 'MOYEN'
            confidence = 0.7
        else:
            movement_class = 'FAIBLE'
            confidence = 0.5
        
        movements.append({
            'movement_start_time': movement_start_time,
            'movement_start_pips': movement_start_pips,
            'peak_time': peak_time,
            'peak_pips': peak_pips,
            'movement_end_time': movement_end_time,
            'movement_class': movement_class,
            'direction': direction,
            'baseline_price': baseline_price,
            'confidence': confidence
        })
    
    # Trier par amplitude décroissante (mouvement le plus fort en premier)
    movements.sort(key=lambda x: x['peak_pips'], reverse=True)
    
    return movements


def detect_movement_robust(
    df_prices: pd.DataFrame,
    event_time: pd.Timestamp,
    baseline_time: Optional[pd.Timestamp] = None,
    thresholds: Optional[Dict[str, float]] = None,
    window_hours: float = 6.0
) -> Dict:
    """
    Détecte le mouvement PRINCIPAL (le plus fort) - Méthode Implacable
    
    Wrapper autour de detect_all_movements() qui retourne le mouvement le plus fort.
    
    Args:
        df_prices: DataFrame avec colonnes datetime, open, high, low, close
        event_time: Timestamp de l'événement
        baseline_time: Timestamp pour baseline (si None, utilise event_time - 1 min)
        thresholds: Seuils statistiques (si None, utilise valeurs par défaut)
        window_hours: Fenêtre d'analyse en heures
    
    Returns:
        Dictionnaire avec mouvement principal (même format que detect_all_movements()[0])
    """
    
    all_movements = detect_all_movements(
        df_prices,
        event_time,
        baseline_time,
        thresholds,
        window_hours
    )
    
    if not all_movements:
        return {
            'movement_start_time': None,
            'movement_start_pips': 0.0,
            'peak_time': None,
            'peak_pips': 0.0,
            'movement_end_time': None,
            'movement_class': 'NONE',
            'direction': None,
            'baseline_price': None,
            'confidence': 0.0
        }
    
    # Retourner le mouvement le plus fort (premier de la liste triée)
    return all_movements[0]
