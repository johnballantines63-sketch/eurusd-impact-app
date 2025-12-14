#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TROUVER PULLBACK DE 29.5 PIPS
==============================

Cherche précisément où apparaît un pullback de 29.5 pips
dans les 30 premières minutes après le pic.

Date: 2025-08-01
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import pytz

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from config import DB_PATH
from core.price_loader_finnhub import get_finnhub_prices_at_event_time

TZ_BERN = pytz.timezone('Europe/Zurich')

def trouver_pullback_precis():
    """Trouve précisément le pullback de 29.5 pips"""
    
    date_str = '2025-08-01'
    event_time = TZ_BERN.localize(datetime.strptime(f"{date_str} 14:30:00", "%Y-%m-%d %H:%M:%S"))
    
    print("\n" + "=" * 80)
    print(f"  RECHERCHE PRÉCISE DU PULLBACK - 1ER AOÛT 2025")
    print("=" * 80)
    print()
    
    # Charger les prix
    df_prices = get_finnhub_prices_at_event_time(
        db_path=DB_PATH,
        event_timestamp_bern=event_time,
        lookback_minutes=60,
        lookahead_minutes=120
    )
    
    if df_prices.empty:
        print("❌ Aucun prix trouvé")
        return
    
    # Baseline
    prices_before = df_prices[df_prices['datetime'] < event_time]
    baseline_price = prices_before.iloc[-1]['close']
    baseline_time = prices_before.iloc[-1]['datetime']
    
    print(f"💰 Baseline : {baseline_price:.5f} à {baseline_time}")
    print()
    
    # Trouver le pic
    prices_after = df_prices[df_prices['datetime'] >= event_time].copy()
    prices_after['pips'] = (prices_after['high'] - baseline_price) * 10000
    
    max_pips_idx = prices_after['pips'].idxmax()
    peak_time = prices_after.loc[max_pips_idx, 'datetime']
    peak_price = prices_after.loc[max_pips_idx, 'high']
    peak_pips = prices_after.loc[max_pips_idx, 'pips']
    
    print(f"📈 Pic maximum : {peak_price:.5f} ({peak_pips:.1f} pips) à {peak_time}")
    print()
    
    # Analyser tous les pullbacks dans les 30 premières minutes
    prices_after_peak = prices_after[prices_after['datetime'] > peak_time].copy()
    window_30min = prices_after_peak[
        (prices_after_peak['datetime'] - peak_time).dt.total_seconds() / 60 <= 30
    ]
    
    if window_30min.empty:
        print("❌ Aucune donnée dans les 30 premières minutes")
        return
    
    # Calculer pullback pour chaque barre
    window_30min = window_30min.copy()
    window_30min['pullback_pips'] = (peak_price - window_30min['low']) * 10000
    window_30min['minutes_from_peak'] = (
        (window_30min['datetime'] - peak_time).dt.total_seconds() / 60
    )
    
    print("🔍 RECHERCHE PULLBACK ≈ 29.5 PIPS (dans les 30 premières minutes) :")
    print("-" * 80)
    print()
    
    # Trier par pullback croissant
    window_30min_sorted = window_30min.sort_values('pullback_pips')
    
    # Chercher les valeurs proches de 29.5
    target_pips = 29.5
    tolerance = 1.0  # Tolérance de 1 pip
    
    matches = window_30min_sorted[
        abs(window_30min_sorted['pullback_pips'] - target_pips) <= tolerance
    ]
    
    if not matches.empty:
        print(f"✅ TROUVÉ {len(matches)} valeur(s) proche(s) de 29.5 pips :")
        print()
        
        for idx, row in matches.iterrows():
            print(f"   📍 Barre à {row['datetime']} :")
            print(f"      Pullback : {row['pullback_pips']:.1f} pips")
            print(f"      Prix : {row['low']:.5f}")
            print(f"      Minutes depuis pic : {row['minutes_from_peak']:.1f} min")
            print()
    else:
        print(f"⚠️ Aucune valeur exacte de {target_pips} pips trouvée")
        print()
        print("📊 Valeurs les plus proches :")
        print()
        
        # Les 5 valeurs les plus proches
        window_30min_sorted['diff'] = abs(window_30min_sorted['pullback_pips'] - target_pips)
        closest = window_30min_sorted.nsmallest(5, 'diff')
        
        for idx, row in closest.iterrows():
            diff = row['diff']
            print(f"   {row['datetime'].strftime('%H:%M')} : {row['pullback_pips']:.1f} pips (écart {diff:.1f})")
    
    print()
    
    # Afficher toutes les barres avec pullback significatif
    print("📋 TOUS LES PULLBACKS DANS LES 30 PREMIÈRES MINUTES :")
    print("-" * 80)
    print()
    
    significant_pullbacks = window_30min_sorted[window_30min_sorted['pullback_pips'] > 10].tail(10)
    
    for idx, row in significant_pullbacks.iterrows():
        print(f"   {row['datetime'].strftime('%H:%M:%S')} : {row['pullback_pips']:.1f} pips (T+{row['minutes_from_peak']:.1f} min)")
    
    print()
    
    # Maximum pullback dans les 30 premières minutes
    max_pullback_30min = window_30min['pullback_pips'].max()
    max_pullback_time = window_30min.loc[window_30min['pullback_pips'].idxmax(), 'datetime']
    max_pullback_minutes = (
        (max_pullback_time - peak_time).total_seconds() / 60
    )
    
    print("📊 RÉSUMÉ :")
    print("-" * 80)
    print(f"   Maximum pullback (30 min) : {max_pullback_30min:.1f} pips")
    print(f"   Heure : {max_pullback_time}")
    print(f"   Minutes depuis pic : {max_pullback_minutes:.1f} min")
    print()
    
    if abs(max_pullback_30min - 29.5) < 5.0:
        print(f"   ✅ Le pullback maximum ({max_pullback_30min:.1f} pips) est proche de 29.5 pips")
    
    print()
    print("=" * 80)
    print()

if __name__ == "__main__":
    trouver_pullback_precis()




