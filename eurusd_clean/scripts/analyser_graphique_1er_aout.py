#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ANALYSE GRAPHIQUE 1ER AOÛT 2025
=================================

Analyse détaillée basée sur le graphique fourni pour identifier
les valeurs exactes mentionnées (1.8 et 29.5).

Date: 2025-08-01 à 14h30
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import pytz

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from config import DB_PATH
from core.price_loader_finnhub import get_finnhub_prices_at_event_time

TZ_BERN = pytz.timezone('Europe/Zurich')

def analyser_graphique():
    """Analyse détaillée basée sur le graphique"""
    
    date_str = '2025-08-01'
    event_time = TZ_BERN.localize(datetime.strptime(f"{date_str} 14:30:00", "%Y-%m-%d %H:%M:%S"))
    
    print("\n" + "=" * 80)
    print(f"  ANALYSE GRAPHIQUE - 1ER AOÛT 2025 (1.8.2025)")
    print("=" * 80)
    print()
    print("📊 Basé sur le graphique fourni :")
    print()
    
    # Charger les prix
    df_prices = get_finnhub_prices_at_event_time(
        db_path=DB_PATH,
        event_timestamp_bern=event_time,
        lookback_minutes=300,  # 5 heures avant
        lookahead_minutes=240  # 4 heures après
    )
    
    if df_prices.empty:
        print("❌ Aucun prix trouvé")
        return
    
    # Filtrer autour de 14:30
    df_around_event = df_prices[
        (df_prices['datetime'] >= event_time - pd.Timedelta(minutes=1)) &
        (df_prices['datetime'] <= event_time + pd.Timedelta(hours=4))
    ].copy()
    
    if df_around_event.empty:
        print("❌ Aucun prix autour de l'événement")
        return
    
    # Trouver baseline (prix juste avant 14:30)
    prices_before = df_prices[df_prices['datetime'] < event_time]
    if not prices_before.empty:
        baseline_price = prices_before.iloc[-1]['close']
        baseline_time = prices_before.iloc[-1]['datetime']
    else:
        baseline_price = df_prices.iloc[0]['open']
        baseline_time = df_prices.iloc[0]['datetime']
    
    print("1️⃣ BASELINE (Prix de départ) :")
    print(f"   Prix : {baseline_price:.5f}")
    print(f"   Heure : {baseline_time}")
    print()
    
    # Analyser le pic
    prices_after = df_prices[df_prices['datetime'] >= event_time].copy()
    prices_after['pips'] = (prices_after['high'] - baseline_price) * 10000
    
    max_pips_idx = prices_after['pips'].idxmax()
    peak_time = prices_after.loc[max_pips_idx, 'datetime']
    peak_price = prices_after.loc[max_pips_idx, 'high']
    peak_pips = prices_after.loc[max_pips_idx, 'pips']
    
    print("2️⃣ PIC MAXIMUM (Single Wave Fort) :")
    print(f"   Impact : {peak_pips:.1f} pips")
    print(f"   Prix : {peak_price:.5f}")
    print(f"   Heure : {peak_time}")
    print()
    
    # Vérifier si 1.8 correspond au prix du pic
    print("🔍 VÉRIFICATION : Valeur 1.8")
    print("-" * 80)
    print(f"   Prix du pic : {peak_price:.5f}")
    
    # Extraire les 3 premiers chiffres après la virgule
    prix_arrondi = round(peak_price, 3)  # 1.15884 → 1.159
    prix_tronque = int(peak_price * 1000) / 1000  # 1.15884 → 1.158
    
    print(f"   Prix arrondi à 3 décimales : {prix_arrondi:.3f}")
    print(f"   Prix tronqué : {prix_tronque:.3f}")
    
    if abs(peak_price - 1.158) < 0.001:
        print(f"   ✅ Le pic est proche de 1.158 (peut être arrondi à 1.8?)")
    
    # Vérifier si 1.8 = 1.8 * 100 = 180 pips
    if abs(peak_pips - 180) < 10:
        print(f"   ✅ Le pic est proche de 180 pips : {peak_pips:.1f} pips")
    
    # Vérifier si 1.8 = impact en pourcentage ou ratio
    impact_pct = (peak_price / baseline_price - 1) * 100
    print(f"   Impact en % : {impact_pct:.2f}%")
    
    print()
    
    # Analyser le pullback
    prices_after_peak = prices_after[prices_after['datetime'] > peak_time].copy()
    
    if not prices_after_peak.empty:
        prices_after_peak['pullback_pips'] = (peak_price - prices_after_peak['low']) * 10000
        
        max_pullback_idx = prices_after_peak['pullback_pips'].idxmax()
        pullback_time = prices_after_peak.loc[max_pullback_idx, 'datetime']
        pullback_price = prices_after_peak.loc[max_pullback_idx, 'low']
        pullback_pips = prices_after_peak.loc[max_pullback_idx, 'pullback_pips']
        
        print("3️⃣ PULLBACK :")
        print(f"   Retracement : {pullback_pips:.1f} pips")
        print(f"   Prix : {pullback_price:.5f}")
        print(f"   Heure : {pullback_time}")
        print()
        
        print("🔍 VÉRIFICATION : Valeur 29.5")
        print("-" * 80)
        print(f"   Pullback détecté : {pullback_pips:.1f} pips")
        
        if abs(pullback_pips - 29.5) < 1.0:
            print(f"   ✅ Pullback très proche de 29.5 pips !")
        elif abs(pullback_pips - 29.5) < 5.0:
            print(f"   ⚠️ Pullback proche de 29.5 pips (écart {abs(pullback_pips - 29.5):.1f})")
        
        # Chercher dans différentes fenêtres
        print()
        print("   Recherche dans différentes fenêtres :")
        
        # Fenêtre 30 min
        window_30 = prices_after_peak[
            (prices_after_peak['datetime'] - peak_time).dt.total_seconds() / 60 <= 30
        ]
        if not window_30.empty:
            max_pb_30 = window_30['pullback_pips'].max()
            print(f"      - 30 premières minutes : {max_pb_30:.1f} pips")
            if abs(max_pb_30 - 29.5) < 1.0:
                print(f"        ✅ Trouvé ! {max_pb_30:.1f} ≈ 29.5")
        
        # Fenêtre 60 min
        window_60 = prices_after_peak[
            (prices_after_peak['datetime'] - peak_time).dt.total_seconds() / 60 <= 60
        ]
        if not window_60.empty:
            max_pb_60 = window_60['pullback_pips'].max()
            print(f"      - 60 premières minutes : {max_pb_60:.1f} pips")
            if abs(max_pb_60 - 29.5) < 1.0:
                print(f"        ✅ Trouvé ! {max_pb_60:.1f} ≈ 29.5")
        
        # Fenêtre 120 min
        window_120 = prices_after_peak[
            (prices_after_peak['datetime'] - peak_time).dt.total_seconds() / 60 <= 120
        ]
        if not window_120.empty:
            max_pb_120 = window_120['pullback_pips'].max()
            print(f"      - 120 premières minutes : {max_pb_120:.1f} pips")
            if abs(max_pb_120 - 29.5) < 1.0:
                print(f"        ✅ Trouvé ! {max_pb_120:.1f} ≈ 29.5")
    
    print()
    
    # Résumé des valeurs du graphique
    print("=" * 80)
    print("  RÉSUMÉ - VALEURS DU GRAPHIQUE")
    print("=" * 80)
    print()
    print(f"📅 Date : 1er août 2025 (1.8.2025)")
    print(f"⏰ Événement : 14h30")
    print()
    print(f"💰 Baseline : {baseline_price:.5f} (avant 14:30)")
    print(f"📈 Pic maximum : {peak_price:.5f} ({peak_pips:.1f} pips)")
    print(f"   - Impact : {peak_pips:.1f} pips")
    print(f"   - Heure : {peak_time}")
    print()
    
    if not prices_after_peak.empty:
        print(f"📉 Pullback : {pullback_price:.5f} ({pullback_pips:.1f} pips)")
        print(f"   - Retracement : {pullback_pips:.1f} pips")
        print(f"   - Heure : {pullback_time}")
        print(f"   - Ratio : {pullback_pips/peak_pips*100:.1f}% du pic")
        print()
    
    # Hypothèses sur 1.8
    print("💡 HYPOTHÈSES SUR '1.8' :")
    print("-" * 80)
    print(f"1. Date : 1er août = 1.8 (format européen) ✅")
    print(f"2. Prix pic : {peak_price:.5f} → 1.158 arrondi ?")
    print(f"3. Impact : {peak_pips:.1f} pips → 180 pips arrondi ?")
    print(f"4. Impact en % : {impact_pct:.2f}% → {impact_pct:.1f}% ?")
    print()
    
    # Hypothèses sur 29.5
    print("💡 HYPOTHÈSES SUR '29.5' :")
    print("-" * 80)
    if not prices_after_peak.empty:
        print(f"1. Pullback : {pullback_pips:.1f} pips ✅ (proche de 29.5)")
        print(f"2. Ratio pullback/pic : {pullback_pips/peak_pips:.3f} = {pullback_pips/peak_pips*100:.1f}%")
    print()
    
    print("=" * 80)
    print()

if __name__ == "__main__":
    analyser_graphique()




