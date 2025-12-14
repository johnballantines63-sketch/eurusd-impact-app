"""
Scanner complet 2024-2025 avec DB EODHD 125k événements

Re-scan pour détecter patterns avec events COMPLETS
Comparaison vs Session 117 (DB 58k)

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
Session : 123
"""

import duckdb
from pathlib import Path
import json
import pandas as pd
from datetime import datetime, timedelta
import pytz
from collections import defaultdict

# Configuration
DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'warehouse.duckdb'  # DB unifiée
OUTPUT_DIR = Path(__file__).parent / 'scan_results'
OUTPUT_DIR.mkdir(exist_ok=True)

# Paramètres détection
SPIKE_THRESHOLD = 35  # pips (même que Session 117)
LOOKBACK_MINUTES = 30
LOOKFORWARD_MINUTES = 60

def load_prices(conn, start_date, end_date):
    """Charger prix 1min depuis DB"""
    
    print(f"📊 Chargement prix {start_date} → {end_date}...")
    
    query = """
    SELECT datetime, open, high, low, close
    FROM prices_bern
    WHERE datetime >= ? AND datetime <= ?
    ORDER BY datetime
    """
    
    df = conn.execute(query, [start_date, end_date]).df()
    
    if len(df) == 0:
        return None
    
    # Convertir timezone
    df['datetime'] = pd.to_datetime(df['datetime'], utc=True).dt.tz_convert('Europe/Zurich')
    df = df.set_index('datetime')
    
    print(f"   ✅ {len(df):,} bars chargées")
    
    return df

def detect_spikes(prices_df, threshold_pips=35):
    """Détecter spikes > threshold"""
    
    print(f"\n🔍 Détection spikes > {threshold_pips} pips...")
    
    spikes = []
    
    for i in range(len(prices_df)):
        if i == 0:
            continue
        
        current = prices_df.iloc[i]
        baseline = prices_df.iloc[i-1]['close']
        
        # Mouvement depuis baseline
        move_up = (current['high'] - baseline) * 10000
        move_down = (baseline - current['low']) * 10000
        
        max_move = max(move_up, abs(move_down))
        
        if max_move >= threshold_pips:
            spike = {
                'datetime': current.name,
                'baseline': baseline,
                'high': current['high'],
                'low': current['low'],
                'close': current['close'],
                'move_up': move_up,
                'move_down': move_down,
                'max_move': max_move,
                'direction': 'UP' if move_up > abs(move_down) else 'DOWN'
            }
            spikes.append(spike)
    
    print(f"   ✅ {len(spikes)} spikes détectés")
    
    return spikes

def classify_pattern(prices_df, spike_time, spike_info):
    """Classifier pattern (Double Wave, Single Wave, etc.)"""
    
    # Fenêtre analyse
    start = spike_time - timedelta(minutes=10)
    end = spike_time + timedelta(minutes=120)
    
    window = prices_df[start:end]
    
    if len(window) < 10:
        return 'INSUFFICIENT_DATA'
    
    baseline = spike_info['baseline']
    
    # Détecter pics
    peaks = []
    for i in range(1, len(window)-1):
        current = window.iloc[i]
        prev = window.iloc[i-1]
        next = window.iloc[i+1]
        
        if spike_info['direction'] == 'UP':
            if current['high'] > prev['high'] and current['high'] > next['high']:
                peaks.append({
                    'time': current.name,
                    'price': current['high'],
                    'amplitude': (current['high'] - baseline) * 10000
                })
        else:
            if current['low'] < prev['low'] and current['low'] < next['low']:
                peaks.append({
                    'time': current.name,
                    'price': current['low'],
                    'amplitude': abs(current['low'] - baseline) * 10000
                })
    
    # Classification
    if len(peaks) == 0:
        return 'NO_PATTERN'
    elif len(peaks) == 1:
        if peaks[0]['amplitude'] > 40:
            return 'SINGLE_WAVE_FORT'
        else:
            return 'SINGLE_WAVE_INTERMEDIATE'
    elif len(peaks) == 2:
        return 'DOUBLE_WAVE'
    elif len(peaks) >= 3:
        return 'ZIG_ZAG'
    
    return 'UNKNOWN'

def find_causal_events(conn, spike_time, lookback=30, lookforward=10):
    """Trouver events causaux dans fenêtre temporelle"""
    
    # Convertir spike_time en UTC pour query
    spike_utc = spike_time.astimezone(pytz.UTC)
    
    start = spike_utc - timedelta(minutes=lookback)
    end = spike_utc + timedelta(minutes=lookforward)
    
    query = """
    SELECT 
        datetime_utc,
        event_name,
        country,
        importance,
        actual,
        forecast,
        previous
    FROM economic_events
    WHERE datetime_utc >= ?
      AND datetime_utc <= ?
      AND country IN ('usd', 'eur', 'gbp', 'jpy', 'cad', 'aud', 'chf')
    ORDER BY datetime_utc
    """
    
    events = conn.execute(query, [start, end]).fetchall()
    
    events_list = []
    for e in events:
        dt_utc = pd.to_datetime(e[0], utc=True)  # Force UTC
        dt_bern = dt_utc.tz_convert('Europe/Zurich')
        
        # Calculer delta temporel
        delta_minutes = (dt_bern - spike_time).total_seconds() / 60.0
        
        events_list.append({
            'datetime': str(dt_bern),
            'event_name': e[1],
            'country': e[2],
            'importance': e[3],
            'actual': e[4],
            'forecast': e[5],
            'previous': e[6],
            'delta_minutes': delta_minutes
        })
    
    return events_list

def scan_period(conn, year, month_start=1, month_end=12):
    """Scanner période complète"""
    
    print("=" * 80)
    print(f"SCAN {year}")
    print("=" * 80)
    print()
    
    all_spikes = []
    
    for month in range(month_start, month_end + 1):
        print(f"\n📅 {year}-{month:02d}")
        print("-" * 70)
        
        # Dates
        start = f"{year}-{month:02d}-01"
        if month == 12:
            end = f"{year}-12-31"
        else:
            end = f"{year}-{month+1:02d}-01"
        
        # Charger prix
        prices = load_prices(conn, start, end)
        
        if prices is None:
            print("   ⚠️  Pas de données prix")
            continue
        
        # Détecter spikes
        spikes = detect_spikes(prices, SPIKE_THRESHOLD)
        
        # Analyser chaque spike
        for spike in spikes:
            spike_time = spike['datetime']
            
            # Classifier pattern
            pattern = classify_pattern(prices, spike_time, spike)
            spike['pattern'] = pattern
            
            # Chercher events causaux
            events = find_causal_events(conn, spike_time, LOOKBACK_MINUTES, LOOKFORWARD_MINUTES)
            spike['events'] = events
            spike['num_events'] = len(events)
            
            # Convertir datetime pour JSON
            spike['datetime'] = str(spike['datetime'])
            
            all_spikes.append(spike)
        
        print(f"   ✅ {len(spikes)} spikes ce mois")
    
    print()
    print(f"✅ {year} : {len(all_spikes)} spikes total")
    print()
    
    return all_spikes

def main():
    """Scanner complet 2024-2025"""
    
    print("=" * 80)
    print("SCANNER COMPLET 2024-2025 - DB 125K ÉVÉNEMENTS")
    print("=" * 80)
    print()
    
    # Connexion DB unifiée
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # Vérifier DB
    total_events = conn.execute("SELECT COUNT(*) FROM economic_events").fetchone()[0]
    total_prices = conn.execute("SELECT COUNT(*) FROM prices_bern").fetchone()[0]
    
    print(f"📊 DB Unifiée : {total_events:,} événements | {total_prices:,} bars prix")
    print()
    
    # Scanner 2024
    spikes_2024 = scan_period(conn, 2024)
    
    # Scanner 2025
    spikes_2025 = scan_period(conn, 2025, month_end=11)  # Jusqu'à novembre
    
    # Combiner
    all_spikes = spikes_2024 + spikes_2025
    
    # Statistiques
    print("=" * 80)
    print("STATISTIQUES GLOBALES")
    print("=" * 80)
    print()
    
    print(f"📊 Total spikes : {len(all_spikes)}")
    print()
    
    # Par pattern
    by_pattern = defaultdict(int)
    for s in all_spikes:
        by_pattern[s['pattern']] += 1
    
    print("Par pattern :")
    for pattern, count in sorted(by_pattern.items(), key=lambda x: x[1], reverse=True):
        pct = count / len(all_spikes) * 100
        print(f"   {pattern:30s} : {count:3d} ({pct:5.1f}%)")
    
    print()
    
    # Avec/sans events
    with_events = sum(1 for s in all_spikes if s['num_events'] > 0)
    without_events = len(all_spikes) - with_events
    
    print("Events causaux :")
    print(f"   Avec events    : {with_events} ({with_events/len(all_spikes)*100:.1f}%)")
    print(f"   Sans events    : {without_events} ({without_events/len(all_spikes)*100:.1f}%)")
    print()
    
    # Double Wave spécifiquement
    double_waves = [s for s in all_spikes if s['pattern'] == 'DOUBLE_WAVE']
    dw_with_events = [s for s in double_waves if s['num_events'] > 0]
    
    print(f"🎯 DOUBLE WAVE :")
    print(f"   Total         : {len(double_waves)}")
    
    if len(double_waves) > 0:
        print(f"   Avec events   : {len(dw_with_events)} ({len(dw_with_events)/len(double_waves)*100:.1f}%)")
        print(f"   Sans events   : {len(double_waves) - len(dw_with_events)}")
    else:
        print(f"   ⚠️  AUCUN Double Wave détecté avec seuil {SPIKE_THRESHOLD} pips")
        print(f"   Tous classifiés : {list(by_pattern.keys())}")
    print()
    
    # Sauvegarder
    output_file = OUTPUT_DIR / 'spikes_2024_2025_db125k.json'
    with open(output_file, 'w') as f:
        json.dump(all_spikes, f, indent=2)
    
    print(f"💾 Résultats : {output_file}")
    print()
    
    # Double Wave séparé
    dw_file = OUTPUT_DIR / 'double_waves_db125k.json'
    with open(dw_file, 'w') as f:
        json.dump(double_waves, f, indent=2)
    
    print(f"💾 Double Wave : {dw_file}")
    print()
    
    # Comparaison Session 117
    print("=" * 80)
    print("COMPARAISON VS SESSION 117")
    print("=" * 80)
    print()
    
    print("Session 117 (DB 58k) :")
    print("   Spikes total  : 74")
    print("   Double Wave   : 15")
    print("   DW avec events: 13")
    print()
    
    print("Session 123 (DB 125k) :")
    print(f"   Spikes total  : {len(all_spikes)}")
    print(f"   Double Wave   : {len(double_waves)}")
    print(f"   DW avec events: {len(dw_with_events)}")
    print()
    
    if len(double_waves) > 15:
        print(f"✅ AMÉLIORATION : +{len(double_waves) - 15} Double Wave détectés")
    elif len(double_waves) < 15:
        print(f"⚠️  DIFFÉRENCE : {15 - len(double_waves)} Double Wave en moins (variations détection)")
    else:
        print("⚖️  IDENTIQUE : Même nombre Double Wave")
    
    print()
    
    conn.close()
    
    print("=" * 80)
    print("✅ SCAN TERMINÉ")
    print("=" * 80)
    print()
    print("Fichiers créés :")
    print(f"   • {output_file.name}")
    print(f"   • {dw_file.name}")
    print()

if __name__ == '__main__':
    main()
