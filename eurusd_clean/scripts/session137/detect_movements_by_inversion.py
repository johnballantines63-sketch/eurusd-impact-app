#!/usr/bin/env python3
"""
Détection de mouvements forts par méthode d'inversion de tendance
Basé sur la méthode validée Session 107

Principe :
1. Scanner les prix pour identifier les extrema locaux (peaks/troughs)
2. Détecter les inversions de tendance (HIGH→LOW ou LOW→HIGH)
3. Identifier les mouvements forts depuis ces inversions
4. Calculer les métriques réelles (impact, durée, direction)

Cette méthode est plus robuste que les seuils fixes car elle détecte
mathématiquement les vraies inversions de tendance.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from scipy.stats import linregress
import duckdb


def find_extrema_improved(prices: pd.DataFrame, 
                         window_minutes: int = 30) -> List[Dict]:
    """
    Trouve les extrema locaux avec une fenêtre glissante
    Plus robuste que la version précédente
    """
    extrema = []
    
    # Fenêtre pour détecter les extrema locaux
    window_size = window_minutes
    
    for i in range(window_size, len(prices) - window_size):
        # Peak local : high plus élevé que les window_size minutes avant et après
        if prices.iloc[i]['high'] == prices.iloc[i-window_size:i+window_size+1]['high'].max():
            extrema.append({
                'type': 'HIGH',
                'index': i,
                'datetime': prices.iloc[i]['datetime'],
                'price': prices.iloc[i]['high']
            })
        
        # Trough local : low plus bas que les window_size minutes avant et après
        if prices.iloc[i]['low'] == prices.iloc[i-window_size:i+window_size+1]['low'].min():
            extrema.append({
                'type': 'LOW',
                'index': i,
                'datetime': prices.iloc[i]['datetime'],
                'price': prices.iloc[i]['low']
            })
    
    # Filtrer par distance temporelle (au moins 1h entre extrema)
    filtered = []
    for ext in extrema:
        too_close = False
        for prev in filtered:
            time_diff = abs((ext['datetime'] - prev['datetime']).total_seconds() / 3600)
            if time_diff < 1.0:  # Au moins 1h
                too_close = True
                break
        if not too_close:
            filtered.append(ext)
    
    # Trier par index
    filtered.sort(key=lambda x: x['index'])
    
    return filtered


def find_extrema(prices: pd.DataFrame, 
                 top_n: int = 5,
                 min_hours_apart: int = 2) -> List[Dict]:
    """
    Trouve les extrema locaux (peaks et troughs)
    
    Args:
        prices: DataFrame avec colonnes ['datetime', 'high', 'low']
        top_n: Nombre d'extrema à trouver (peaks et troughs séparément)
        min_hours_apart: Heures minimum entre deux extrema
    
    Returns:
        List de dict avec 'type' ('HIGH' ou 'LOW'), 'index', 'datetime', 'price'
    """
    extrema = []
    
    # Trouver les peaks (highs locaux)
    for i in range(1, len(prices) - 1):
        if prices.iloc[i]['high'] > prices.iloc[i-1]['high'] and \
           prices.iloc[i]['high'] > prices.iloc[i+1]['high']:
            extrema.append({
                'type': 'HIGH',
                'index': i,
                'datetime': prices.iloc[i]['datetime'],
                'price': prices.iloc[i]['high']
            })
    
    # Trouver les troughs (lows locaux)
    for i in range(1, len(prices) - 1):
        if prices.iloc[i]['low'] < prices.iloc[i-1]['low'] and \
           prices.iloc[i]['low'] < prices.iloc[i+1]['low']:
            extrema.append({
                'type': 'LOW',
                'index': i,
                'datetime': prices.iloc[i]['datetime'],
                'price': prices.iloc[i]['low']
            })
    
    # Trier par prix (descendant pour HIGH, ascendant pour LOW)
    extrema.sort(key=lambda x: x['price'] if x['type'] == 'HIGH' else -x['price'], reverse=True)
    
    # Filtrer par distance temporelle
    filtered = []
    for ext in extrema[:top_n * 2]:  # Prendre plus pour filtrer
        # Vérifier distance avec extrema déjà sélectionnés
        too_close = False
        for prev in filtered:
            time_diff = abs((ext['datetime'] - prev['datetime']).total_seconds() / 3600)
            if time_diff < min_hours_apart:
                too_close = True
                break
        
        if not too_close:
            filtered.append(ext)
            if len(filtered) >= top_n:
                break
    
    # Trier par index pour ordre chronologique
    filtered.sort(key=lambda x: x['index'])
    
    return filtered


def detect_inversions(extrema: List[Dict], 
                      prices: pd.DataFrame,
                      min_amplitude_pips: float = 30.0) -> List[Dict]:
    """
    Détecte les inversions de tendance entre extrema
    
    Args:
        extrema: Liste d'extrema de find_extrema()
        prices: DataFrame avec colonnes ['datetime', 'high', 'low', 'close']
        min_amplitude_pips: Amplitude minimum pour inversion valide
    
    Returns:
        List de dict avec 'type' ('PEAK' ou 'TROUGH'), 'datetime', 'price', 'amplitude'
    """
    inversions = []
    
    for i in range(len(extrema) - 1):
        ext1 = extrema[i]
        ext2 = extrema[i + 1]
        
        # Inversion HIGH→LOW (PEAK)
        if ext1['type'] == 'HIGH' and ext2['type'] == 'LOW':
            # Vérifier que le prix baisse effectivement
            start_idx = ext1['index']
            end_idx = ext2['index']
            
            if end_idx > start_idx:
                segment = prices.iloc[start_idx:end_idx+1]
                amplitude = (segment['high'].max() - segment['low'].min()) * 10000
                
                if amplitude >= min_amplitude_pips:
                    inversions.append({
                        'type': 'PEAK',
                        'datetime': ext1['datetime'],
                        'price': ext1['price'],
                        'amplitude': amplitude,
                        'start_idx': start_idx,
                        'end_idx': end_idx
                    })
        
        # Inversion LOW→HIGH (TROUGH)
        elif ext1['type'] == 'LOW' and ext2['type'] == 'HIGH':
            # Vérifier que le prix monte effectivement
            start_idx = ext1['index']
            end_idx = ext2['index']
            
            if end_idx > start_idx:
                segment = prices.iloc[start_idx:end_idx+1]
                amplitude = (segment['high'].max() - segment['low'].min()) * 10000
                
                if amplitude >= min_amplitude_pips:
                    inversions.append({
                        'type': 'TROUGH',
                        'datetime': ext1['datetime'],
                        'price': ext1['price'],
                        'amplitude': amplitude,
                        'start_idx': start_idx,
                        'end_idx': end_idx
                    })
    
    return inversions


def detect_movements_from_inversions(inversions: List[Dict],
                                     prices: pd.DataFrame,
                                     min_impact_pips: float = 35.0) -> List[Dict]:
    """
    Détecte les mouvements forts depuis les inversions
    
    Args:
        inversions: Liste d'inversions de detect_inversions()
        prices: DataFrame avec colonnes ['datetime', 'high', 'low', 'close']
        min_impact_pips: Impact minimum pour mouvement valide
    
    Returns:
        List de dict avec mouvement détecté
    """
    movements = []
    
    for inv in inversions:
        start_idx = inv['start_idx']
        end_idx = inv['end_idx']
        
        # Segment depuis inversion
        segment = prices.iloc[start_idx:end_idx+1]
        
        if len(segment) < 10:  # Au moins 10 minutes
            continue
        
        # Calculer impact
        if inv['type'] == 'TROUGH':  # Mouvement UP
            baseline_price = segment.iloc[0]['low']
            peak_price = segment['high'].max()
            peak_idx = segment['high'].idxmax()
            impact_pips = (peak_price - baseline_price) * 10000
            direction = 'UP'
        else:  # PEAK - Mouvement DOWN
            baseline_price = segment.iloc[0]['high']
            trough_price = segment['low'].min()
            trough_idx = segment['low'].idxmin()
            impact_pips = (baseline_price - trough_price) * 10000
            direction = 'DOWN'
        
        # Filtrer par impact minimum
        if impact_pips < min_impact_pips:
            continue
        
        # Calculer durée
        start_time = segment.iloc[0]['datetime']
        if inv['type'] == 'TROUGH':
            peak_time = segment.loc[peak_idx, 'datetime']
            duration_minutes = (peak_time - start_time).total_seconds() / 60
        else:
            trough_time = segment.loc[trough_idx, 'datetime']
            duration_minutes = (trough_time - start_time).total_seconds() / 60
        
        movements.append({
            'movement_datetime': start_time,
            'direction': direction,
            'impact_pips': impact_pips,
            'baseline_price': baseline_price,
            'peak_time': peak_time if inv['type'] == 'TROUGH' else trough_time,
            'peak_price': peak_price if inv['type'] == 'TROUGH' else trough_price,
            'duration_minutes': duration_minutes,
            'inversion_type': inv['type']
        })
    
    return movements


def scan_movements_by_inversion(db_path: Path,
                                start_date: pd.Timestamp,
                                end_date: pd.Timestamp,
                                min_impact_pips: float = 35.0) -> pd.DataFrame:
    """
    Scanne les mouvements forts par méthode d'inversion
    
    Args:
        db_path: Chemin vers la base de données DuckDB
        start_date: Date de début
        end_date: Date de fin
        min_impact_pips: Impact minimum
    
    Returns:
        DataFrame avec mouvements détectés
    """
    conn = duckdb.connect(str(db_path), read_only=True)
    
    # Charger prix
    query = """
    SELECT datetime, open, high, low, close
    FROM prices_bern
    WHERE datetime >= ?
      AND datetime < ?
    ORDER BY datetime
    """
    
    df_prices = conn.execute(query, [start_date, end_date]).df()
    conn.close()
    
    if len(df_prices) < 100:
        return pd.DataFrame()
    
    if df_prices['datetime'].dtype == 'object':
        df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
    
    # Trouver extrema avec méthode améliorée
    extrema = find_extrema_improved(df_prices, window_minutes=30)
    
    print(f"\n📊 Extrema trouvés: {len(extrema)}")
    if len(extrema) > 0:
        for ext in extrema[:5]:
            print(f"   {ext['type']} à {ext['datetime'].strftime('%H:%M')}: {ext['price']:.5f}")
    
    if len(extrema) < 2:
        print(f"   ❌ Pas assez d'extrema ({len(extrema)} < 2)")
        return pd.DataFrame()
    
    # Détecter inversions
    inversions = detect_inversions(extrema, df_prices, min_amplitude_pips=30.0)
    
    print(f"\n📊 Inversions détectées: {len(inversions)}")
    if len(inversions) > 0:
        for inv in inversions:
            print(f"   {inv['type']} à {inv['datetime'].strftime('%H:%M')}: {inv['amplitude']:.1f} pips")
    
    if len(inversions) == 0:
        print(f"   ❌ Aucune inversion détectée")
        return pd.DataFrame()
    
    # Détecter mouvements depuis inversions
    movements = detect_movements_from_inversions(
        inversions, df_prices, min_impact_pips=min_impact_pips
    )
    
    print(f"\n📊 Mouvements détectés: {len(movements)}")
    if len(movements) > 0:
        for mov in movements:
            print(f"   {mov['movement_datetime'].strftime('%H:%M')}: {mov['direction']} - {mov['impact_pips']:.1f} pips")
    
    if len(movements) == 0:
        print(f"   ❌ Aucun mouvement avec impact >= {min_impact_pips} pips")
        return pd.DataFrame()
    
    return pd.DataFrame(movements)


if __name__ == '__main__':
    # Test sur 22.8.2025
    db_path = Path('data/warehouse.duckdb')
    start_date = pd.to_datetime('2025-08-22 00:00:00+02:00')
    end_date = pd.to_datetime('2025-08-23 00:00:00+02:00')
    
    df_movements = scan_movements_by_inversion(
        db_path, start_date, end_date, min_impact_pips=35.0
    )
    
    print("=" * 80)
    print("DÉTECTION MOUVEMENTS PAR INVERSION - 22.8.2025")
    print("=" * 80)
    
    if len(df_movements) > 0:
        df_movements['movement_datetime_bern'] = pd.to_datetime(df_movements['movement_datetime'])
        
        print(f"\n📊 {len(df_movements)} mouvements détectés:\n")
        for idx, row in df_movements.iterrows():
            mov_time = row['movement_datetime_bern']
            print(f"   {mov_time.strftime('%H:%M')}: {row['direction']} - {row['impact_pips']:.1f} pips")
            print(f"      Pic: {pd.to_datetime(row['peak_time']).strftime('%H:%M')}")
            print(f"      Durée: {row['duration_minutes']:.0f} min")
    else:
        print("\n❌ Aucun mouvement détecté")

