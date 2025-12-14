#!/usr/bin/env python3
"""
Scanner complet 11 septembre 2025 - Session 25
Cherche où se trouve le vrai mouvement de 37+ pips
"""

import duckdb
import pandas as pd
from pathlib import Path

def main():
    print("=" * 80)
    print("🔍 SCAN COMPLET 11 SEPTEMBRE 2025")
    print("=" * 80)
    
    db_path = Path(__file__).parent / "fx_impact_app" / "data" / "warehouse.duckdb"
    con = duckdb.connect(str(db_path))
    
    # Récupérer toute la journée
    print("\n📊 Chargement données 11 septembre...")
    query = """
        SELECT datetime, open, high, low, close
        FROM prices_1m
        WHERE DATE(datetime) = '2025-09-11'
        ORDER BY datetime
    """
    
    df = con.execute(query).df()
    
    if df.empty:
        print("❌ Aucune donnée pour le 11 septembre 2025")
        con.close()
        return
    
    print(f"   Lignes chargées: {len(df)}")
    print(f"   Période: {df['datetime'].min()} → {df['datetime'].max()}")
    
    # Chercher les plus grands mouvements sur fenêtres de 5 minutes
    print("\n" + "=" * 80)
    print("🔥 TOP 10 MOUVEMENTS (fenêtres 5 minutes)")
    print("=" * 80)
    
    movements = []
    
    for i in range(len(df) - 5):
        window = df.iloc[i:i+6]  # 6 lignes = 5 minutes
        
        start_time = window.iloc[0]['datetime']
        start_price = window.iloc[0]['close']
        
        high = window['high'].max()
        low = window['low'].min()
        
        move_up = (high - start_price) * 10000
        move_down = (start_price - low) * 10000
        move_max = max(move_up, move_down)
        direction = "UP" if move_up > move_down else "DOWN"
        
        movements.append({
            'start_time': start_time,
            'start_price': start_price,
            'high': high,
            'low': low,
            'movement_pips': move_max,
            'direction': direction
        })
    
    # Trier par mouvement décroissant
    movements_df = pd.DataFrame(movements)
    top_movements = movements_df.nlargest(10, 'movement_pips')
    
    print("\n" + "-" * 80)
    for idx, row in top_movements.iterrows():
        time_str = row['start_time'].strftime('%H:%M UTC')
        print(f"\n{idx+1}. {time_str} → {(row['start_time'] + pd.Timedelta(minutes=5)).strftime('%H:%M')}")
        print(f"   Mouvement: {row['movement_pips']:.2f} pips ({row['direction']})")
        print(f"   Prix départ: {row['start_price']:.5f}")
        print(f"   High: {row['high']:.5f}")
        print(f"   Low: {row['low']:.5f}")
    
    # Chercher spécifiquement autour de 12:30 (±1h)
    print("\n" + "=" * 80)
    print("🎯 FOCUS PÉRIODE 11:30 → 13:30 UTC (autour annonce 12:30)")
    print("=" * 80)
    
    focus = df[(df['datetime'] >= '2025-09-11 11:30:00') & 
               (df['datetime'] <= '2025-09-11 13:30:00')]
    
    print(f"\nMinutes disponibles: {len(focus)}")
    
    if not focus.empty:
        print("\n" + "-" * 80)
        print("Aperçu minute par minute (11:30 → 13:30):")
        print("-" * 80)
        
        ref_price = focus.iloc[0]['close']
        
        for idx, row in focus.iterrows():
            time_str = row['datetime'].strftime('%H:%M')
            move = (row['close'] - ref_price) * 10000
            range_pips = (row['high'] - row['low']) * 10000
            print(f"{time_str}: C={row['close']:.5f} | H={row['high']:.5f} L={row['low']:.5f} | "
                  f"Move={move:+6.1f}p | Range={range_pips:5.1f}p")
    
    # Statistiques globales journée
    print("\n" + "=" * 80)
    print("📊 STATISTIQUES JOURNÉE COMPLÈTE")
    print("=" * 80)
    
    day_high = df['high'].max()
    day_low = df['low'].min()
    day_range = (day_high - day_low) * 10000
    
    print(f"\nHigh journée: {day_high:.5f}")
    print(f"Low journée:  {day_low:.5f}")
    print(f"Range total:  {day_range:.2f} pips")
    
    # Trouver quand high et low
    high_time = df[df['high'] == day_high].iloc[0]['datetime']
    low_time = df[df['low'] == day_low].iloc[0]['datetime']
    
    print(f"\nHigh atteint: {high_time.strftime('%H:%M UTC')}")
    print(f"Low atteint:  {low_time.strftime('%H:%M UTC')}")
    
    con.close()
    
    print("\n" + "=" * 80)
    print("Fin du scan")
    print("=" * 80)

if __name__ == "__main__":
    main()
