"""
EXTRACTION DÉTAILS PRIX DOUBLE_WAVE
Pour vérification manuelle MT5

Mission :
Pour chaque mouvement DOUBLE_WAVE, extraire :
- Baseline (prix début)
- Peak1 (prix + heure)
- Trough (creux entre peaks, prix + heure)
- Peak2 (prix + heure)
- TTR et pullback si applicable

Auteur: André Valentin avec Claude
Date: 14 novembre 2025
"""

import duckdb
import pandas as pd
from pathlib import Path
from datetime import timedelta

# =============================================================================
# CHEMINS
# =============================================================================

DB_PATH = Path(__file__).parent.parent.parent / "data" / "warehouse.duckdb"
DETAILS_CSV = Path(__file__).parent / "step4_pattern_groups_details.csv"

# =============================================================================
# FONCTION EXTRACTION PRIX DÉTAILS
# =============================================================================

def extract_price_details(conn, movement_datetime, movement_id):
    """
    Extraire détails prix complets pour un mouvement DOUBLE_WAVE
    
    Returns:
        Dict avec baseline, peak1, trough, peak2 (prix + heure)
    """
    
    # Charger prix ±120 min
    start_time = movement_datetime - timedelta(minutes=10)
    end_time = movement_datetime + timedelta(minutes=120)
    
    query = """
    SELECT datetime, open, high, low, close
    FROM prices_bern
    WHERE datetime >= ?
      AND datetime <= ?
    ORDER BY datetime
    """
    
    df_prices = conn.execute(query, [start_time, end_time]).df()
    
    if len(df_prices) == 0:
        return None
    
    # Baseline (premier CLOSE)
    baseline_time = df_prices['datetime'].iloc[0]
    baseline_price = df_prices['close'].iloc[0]
    
    # Trouver peak1 (HIGH max)
    peak1_idx = df_prices['high'].idxmax()
    peak1_time = df_prices.loc[peak1_idx, 'datetime']
    peak1_price = df_prices.loc[peak1_idx, 'high']
    peak1_minutes = (peak1_time - baseline_time).total_seconds() / 60
    
    # Trouver tous les pics locaux (fenêtre 5 min)
    peaks_idx = []
    for i in range(5, len(df_prices) - 5):
        current = df_prices['high'].iloc[i]
        is_peak = True
        for j in range(1, 6):
            if df_prices['high'].iloc[i - j] >= current or df_prices['high'].iloc[i + j] >= current:
                is_peak = False
                break
        if is_peak:
            peaks_idx.append(i)
    
    # Trier pics par amplitude
    peaks_amplitudes = []
    for idx in peaks_idx:
        peak_price = df_prices['high'].iloc[idx]
        amplitude_pips = abs(peak_price - baseline_price) * 10000
        peaks_amplitudes.append((idx, peak_price, amplitude_pips))
    
    peaks_amplitudes.sort(key=lambda x: x[2], reverse=True)
    
    # Peak2 = deuxième pic le plus fort APRÈS peak1
    peak2_idx = None
    peak2_price = None
    peak2_time = None
    peak2_minutes = None
    
    if len(peaks_amplitudes) >= 2:
        # Chercher peak2 après peak1
        peak1_actual_idx = df_prices.index.get_loc(peak1_idx)
        
        for idx, price, amp in peaks_amplitudes[1:]:
            if idx > peak1_actual_idx:
                peak2_idx = idx
                peak2_price = price
                peak2_time = df_prices['datetime'].iloc[idx]
                peak2_minutes = (peak2_time - baseline_time).total_seconds() / 60
                break
    
    # Trough (creux entre peak1 et peak2)
    trough_idx = None
    trough_price = None
    trough_time = None
    trough_minutes = None
    
    if peak2_idx is not None:
        peak1_actual_idx = df_prices.index.get_loc(peak1_idx)
        # Slice entre peak1 et peak2
        between_slice = df_prices['low'].iloc[peak1_actual_idx:peak2_idx+1]
        
        if len(between_slice) > 0:
            trough_idx_relative = between_slice.idxmin()
            trough_idx = between_slice.index.get_loc(trough_idx_relative) + peak1_actual_idx
            trough_price = df_prices['low'].iloc[trough_idx]
            trough_time = df_prices['datetime'].iloc[trough_idx]
            trough_minutes = (trough_time - baseline_time).total_seconds() / 60
    
    return {
        'movement_id': movement_id,
        'movement_datetime': movement_datetime,
        'baseline_time': baseline_time,
        'baseline_price': baseline_price,
        'peak1_time': peak1_time,
        'peak1_price': peak1_price,
        'peak1_minutes': peak1_minutes,
        'peak1_pips': abs(peak1_price - baseline_price) * 10000,
        'trough_time': trough_time,
        'trough_price': trough_price,
        'trough_minutes': trough_minutes,
        'trough_pips': abs(trough_price - baseline_price) * 10000 if trough_price else None,
        'peak2_time': peak2_time,
        'peak2_price': peak2_price,
        'peak2_minutes': peak2_minutes,
        'peak2_pips': abs(peak2_price - baseline_price) * 10000 if peak2_price else None,
        'n_candles': len(df_prices)
    }

# =============================================================================
# FONCTION AFFICHAGE
# =============================================================================

def display_movement_details(details):
    """
    Afficher détails mouvement pour vérification MT5
    """
    
    if details is None:
        print("   ❌ Pas de données prix disponibles")
        return
    
    print(f"\n{'─' * 80}")
    print(f"MOUVEMENT #{details['movement_id']} - {details['movement_datetime']}")
    print(f"{'─' * 80}")
    
    print(f"\n📍 BASELINE (t=0)")
    print(f"   Heure : {details['baseline_time'].strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Prix  : {details['baseline_price']:.5f}")
    
    print(f"\n🔺 PEAK 1")
    print(f"   Heure    : {details['peak1_time'].strftime('%Y-%m-%d %H:%M:%S')} (t+{details['peak1_minutes']:.0f} min)")
    print(f"   Prix     : {details['peak1_price']:.5f}")
    print(f"   Amplitude: {details['peak1_pips']:.1f} pips depuis baseline")
    
    if details['trough_time']:
        print(f"\n🔻 CREUX (Trough)")
        print(f"   Heure    : {details['trough_time'].strftime('%Y-%m-%d %H:%M:%S')} (t+{details['trough_minutes']:.0f} min)")
        print(f"   Prix     : {details['trough_price']:.5f}")
        print(f"   Amplitude: {details['trough_pips']:.1f} pips depuis baseline")
        
        # Calcul dip
        dip_from_peak1 = abs(details['peak1_price'] - details['trough_price']) * 10000
        dip_ratio = dip_from_peak1 / details['peak1_pips'] if details['peak1_pips'] > 0 else 0
        print(f"   Dip      : {dip_from_peak1:.1f} pips depuis Peak1 ({dip_ratio*100:.1f}% de Peak1)")
    
    if details['peak2_time']:
        print(f"\n🔺 PEAK 2")
        print(f"   Heure    : {details['peak2_time'].strftime('%Y-%m-%d %H:%M:%S')} (t+{details['peak2_minutes']:.0f} min)")
        print(f"   Prix     : {details['peak2_price']:.5f}")
        print(f"   Amplitude: {details['peak2_pips']:.1f} pips depuis baseline")
        
        if details['trough_time']:
            recovery = abs(details['peak2_price'] - details['trough_price']) * 10000
            print(f"   Recovery : {recovery:.1f} pips depuis Trough")
    
    print(f"\n📊 RÉSUMÉ")
    print(f"   Baseline → Peak1 → Trough → Peak2")
    print(f"   {details['baseline_price']:.5f} → {details['peak1_price']:.5f} → ", end="")
    if details['trough_price']:
        print(f"{details['trough_price']:.5f} → ", end="")
    if details['peak2_price']:
        print(f"{details['peak2_price']:.5f}")
    else:
        print("(pas de Peak2 détecté)")
    
    print(f"\n   Total bougies analysées : {details['n_candles']}")

# =============================================================================
# FONCTION PRINCIPALE
# =============================================================================

def analyze_specific_movements(movement_ids):
    """
    Analyser mouvements spécifiques pour vérification manuelle
    
    Args:
        movement_ids: Liste IDs mouvements à analyser
    """
    
    print("=" * 80)
    print("EXTRACTION DÉTAILS PRIX DOUBLE_WAVE")
    print("Pour vérification manuelle MT5")
    print("=" * 80)
    
    # Charger CSV
    df = pd.read_csv(DETAILS_CSV)
    df['movement_datetime'] = pd.to_datetime(df['movement_datetime'], utc=True).dt.tz_convert('Europe/Zurich')
    
    # Connecter DB
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # Analyser chaque mouvement
    for movement_id in movement_ids:
        row = df[df['movement_id'] == movement_id]
        
        if len(row) == 0:
            print(f"\n❌ Mouvement #{movement_id} introuvable")
            continue
        
        row = row.iloc[0]
        
        print(f"\n\n{'═' * 80}")
        print(f"CAS #{movement_ids.index(movement_id) + 1} - MOUVEMENT #{movement_id}")
        print(f"{'═' * 80}")
        
        print(f"\nINFO CSV :")
        print(f"   Date           : {row['movement_datetime']}")
        print(f"   Impact         : {row['impact_pips']:.1f} pips")
        print(f"   Événements     : {row['num_events']}")
        print(f"   Total_score    : {row['total_score']:.1f}")
        print(f"   Pattern        : {row['pattern_type']}")
        print(f"   HIGH events    : {row['n_high_events']}")
        
        # Extraire détails prix
        details = extract_price_details(conn, row['movement_datetime'], movement_id)
        display_movement_details(details)
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("EXTRACTION COMPLÉTÉE")
    print("=" * 80)

if __name__ == '__main__':
    # Cas 3, 4, 5 demandés par André
    # Cas 3 : 2024-08-05 13:53 (1 événement)
    # Cas 4 : 2025-04-09 11:10 (dip_ratio 94%)
    # Cas 5 : 2025-04-23 15:14 (dip_ratio 147% suspect)
    
    movement_ids = [160, 279, 310]  # IDs correspondants
    
    analyze_specific_movements(movement_ids)
