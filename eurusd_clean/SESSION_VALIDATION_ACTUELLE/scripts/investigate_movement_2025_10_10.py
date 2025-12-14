"""
Investigation : Mouvement fort 2025-10-10

Objectif : Trouver le mouvement réel (pips et heure) pour 2025-10-10

Date : 2025-12-06
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import duckdb
import pytz
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from config import DB_PATH

TZ_BERN = pytz.timezone('Europe/Zurich')

def investigate_movement_2025_10_10():
    """Investigation complète du mouvement 2025-10-10"""
    
    print("="*100)
    print("INVESTIGATION : MOUVEMENT 2025-10-10")
    print("="*100)
    print()
    
    date_str = '2025-10-10'
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # Charger toutes les données de prix pour la journée
    query_prices = f"""
    SELECT datetime, open, high, low, close
    FROM prices_finnhub_m1
    WHERE DATE(datetime) = '{date_str}'
    ORDER BY datetime ASC
    """
    
    df_prices = conn.execute(query_prices).df()
    
    if df_prices.empty:
        print("❌ Aucune donnée de prix trouvée")
        conn.close()
        return
    
    df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
    df_prices = df_prices.set_index('datetime')
    
    print(f"📊 {len(df_prices)} bougies M1 chargées")
    print(f"   Période : {df_prices.index[0].strftime('%H:%M')} - {df_prices.index[-1].strftime('%H:%M')}")
    print()
    
    # Analyser mouvements par fenêtre horaire
    print("="*100)
    print("ANALYSE MOUVEMENTS PAR HEURE")
    print("="*100)
    print()
    
    # Grouper par heure
    df_prices['hour'] = df_prices.index.hour
    
    movements_by_hour = []
    
    for hour in sorted(df_prices['hour'].unique()):
        df_hour = df_prices[df_prices['hour'] == hour]
        
        if df_hour.empty:
            continue
        
        open_price = df_hour.iloc[0]['open']
        close_price = df_hour.iloc[-1]['close']
        max_high = df_hour['high'].max()
        min_low = df_hour['low'].min()
        
        movement_up = (max_high - open_price) * 10000
        movement_down = (open_price - min_low) * 10000
        movement_net = (close_price - open_price) * 10000
        movement_max = max(movement_up, movement_down)
        
        movements_by_hour.append({
            'hour': hour,
            'open': open_price,
            'close': close_price,
            'max_high': max_high,
            'min_low': min_low,
            'movement_up': movement_up,
            'movement_down': movement_down,
            'movement_net': movement_net,
            'movement_max': movement_max
        })
    
    # Afficher mouvements par heure
    print(f"{'Heure':<8} {'Open':<12} {'Close':<12} {'Max High':<12} {'Min Low':<12} {'Mvt UP':<12} {'Mvt DOWN':<12} {'Mvt NET':<12} {'Mvt MAX':<12}")
    print("-"*120)
    
    for m in movements_by_hour:
        print(f"{m['hour']:02d}:00    {m['open']:>11.5f} {m['close']:>11.5f} {m['max_high']:>11.5f} {m['min_low']:>11.5f} {m['movement_up']:>11.2f} {m['movement_down']:>11.2f} {m['movement_net']:>11.2f} {m['movement_max']:>11.2f}")
    
    print()
    
    # Trouver mouvement maximum
    max_movement = max(movements_by_hour, key=lambda x: x['movement_max'])
    
    print("="*100)
    print("MOUVEMENT MAXIMUM")
    print("="*100)
    print()
    print(f"Heure : {max_movement['hour']:02d}:00")
    print(f"Mouvement maximum : {max_movement['movement_max']:.2f} pips")
    print(f"  UP : {max_movement['movement_up']:.2f} pips")
    print(f"  DOWN : {max_movement['movement_down']:.2f} pips")
    print(f"  NET : {max_movement['movement_net']:.2f} pips")
    print()
    
    # Analyser fenêtre 14:00-20:00 (heures d'événements)
    print("="*100)
    print("ANALYSE FENÊTRE 14:00-20:00 (Événements)")
    print("="*100)
    print()
    
    window_start = TZ_BERN.localize(datetime.combine(pd.to_datetime(date_str).date(), datetime.min.time().replace(hour=14, minute=0)))
    window_end = TZ_BERN.localize(datetime.combine(pd.to_datetime(date_str).date(), datetime.min.time().replace(hour=20, minute=0)))
    
    df_window = df_prices[(df_prices.index >= window_start) & (df_prices.index <= window_end)]
    
    if not df_window.empty:
        baseline_price = df_window.iloc[0]['open']
        max_high = df_window['high'].max()
        min_low = df_window['low'].min()
        final_close = df_window.iloc[-1]['close']
        
        impact_up = (max_high - baseline_price) * 10000
        impact_down = (baseline_price - min_low) * 10000
        impact_net = (final_close - baseline_price) * 10000
        impact_max = max(impact_up, impact_down)
        
        print(f"Baseline (14:00 OPEN) : {baseline_price:.5f}")
        print(f"Max High : {max_high:.5f}")
        print(f"Min Low : {min_low:.5f}")
        print(f"Final Close : {final_close:.5f}")
        print()
        print(f"Impact UP : {impact_up:.2f} pips")
        print(f"Impact DOWN : {impact_down:.2f} pips")
        print(f"Impact NET : {impact_net:.2f} pips")
        print(f"Impact MAX : {impact_max:.2f} pips")
        print()
        
        # Trouver heure du pic
        if impact_up > impact_down:
            peak_time = df_window[df_window['high'] == max_high].index[0]
            print(f"Pic UP à : {peak_time.strftime('%H:%M')}")
        else:
            low_time = df_window[df_window['low'] == min_low].index[0]
            print(f"Pic DOWN à : {low_time.strftime('%H:%M')}")
        print()
        
        # Analyser par tranches de 30 minutes
        print("="*100)
        print("ANALYSE PAR TRANCHES DE 30 MINUTES (14:00-20:00)")
        print("="*100)
        print()
        
        print(f"{'Période':<15} {'Open':<12} {'High':<12} {'Low':<12} {'Close':<12} {'Mvt UP':<12} {'Mvt DOWN':<12} {'Mvt MAX':<12}")
        print("-"*120)
        
        current_time = window_start
        while current_time < window_end:
            period_end = current_time + pd.Timedelta(minutes=30)
            df_period = df_window[(df_window.index >= current_time) & (df_window.index < period_end)]
            
            if not df_period.empty:
                open_p = df_period.iloc[0]['open']
                high_p = df_period['high'].max()
                low_p = df_period['low'].min()
                close_p = df_period.iloc[-1]['close']
                
                mvt_up = (high_p - open_p) * 10000
                mvt_down = (open_p - low_p) * 10000
                mvt_max = max(mvt_up, mvt_down)
                
                period_str = f"{current_time.strftime('%H:%M')}-{period_end.strftime('%H:%M')}"
                print(f"{period_str:<15} {open_p:>11.5f} {high_p:>11.5f} {low_p:>11.5f} {close_p:>11.5f} {mvt_up:>11.2f} {mvt_down:>11.2f} {mvt_max:>11.2f}")
            
            current_time = period_end
        
        print()
    
    # Vérifier événements
    print("="*100)
    print("ÉVÉNEMENTS DU JOUR")
    print("="*100)
    print()
    
    query_events = f"""
    SELECT 
        ts_utc,
        event_key,
        country,
        importance_n,
        actual,
        estimate
    FROM events
    WHERE DATE(ts_utc) = '{date_str}'
      AND importance_n <= 3
    ORDER BY ts_utc
    """
    
    df_events = conn.execute(query_events).df()
    
    if not df_events.empty:
        print(f"{'Heure':<8} {'Event Key':<50} {'Country':<8} {'Imp':<4} {'Actual':<12} {'Estimate':<12}")
        print("-"*100)
        
        for _, event in df_events.iterrows():
            event_time = pd.to_datetime(event['ts_utc']).strftime('%H:%M')
            event_key = str(event['event_key'])[:50]
            country = event['country']
            importance = event['importance_n']
            actual = event['actual']
            estimate = event['estimate']
            
            actual_str = f"{actual:.2f}" if actual is not None and not pd.isna(actual) else "N/A"
            estimate_str = f"{estimate:.2f}" if estimate is not None and not pd.isna(estimate) else "N/A"
            
            print(f"{event_time:<8} {event_key:<50} {country:<8} {importance:<4} {actual_str:<12} {estimate_str:<12}")
    else:
        print("❌ Aucun événement trouvé")
    
    print()
    conn.close()
    
    print("="*100)
    print("RÉSUMÉ")
    print("="*100)
    print()
    print(f"Date : {date_str}")
    if not df_window.empty:
        print(f"Mouvement maximum (14:00-20:00) : {impact_max:.2f} pips")
        if impact_up > impact_down:
            peak_time = df_window[df_window['high'] == max_high].index[0]
            print(f"Heure du pic : {peak_time.strftime('%H:%M')}")
        else:
            low_time = df_window[df_window['low'] == min_low].index[0]
            print(f"Heure du pic : {low_time.strftime('%H:%M')}")
    print()

if __name__ == '__main__':
    investigate_movement_2025_10_10()




