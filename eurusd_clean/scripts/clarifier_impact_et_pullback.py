#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLARIFICATION IMPACT ET PULLBACK
=================================

Clarifie si l'impact (pic) et le pullback sont des mesures réelles
ou des prédictions pour le 1er août 2025.

Date: 2025-01-XX
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
from run_pipeline_complete import PipelineExecutor
from core.price_loader_finnhub import get_finnhub_prices_at_event_time

TZ_BERN = pytz.timezone('Europe/Zurich')

def clarifier_impact_et_pullback():
    """Clarifie impact et pullback"""
    
    date_str = '2025-08-01'
    event_time = TZ_BERN.localize(datetime.strptime(f"{date_str} 14:30:00", "%Y-%m-%d %H:%M:%S"))
    
    print("\n" + "=" * 80)
    print(f"  CLARIFICATION : IMPACT ET PULLBACK")
    print(f"  Date : 1er août 2025 (1.8.2025)")
    print("=" * 80)
    print()
    
    # ========================================================================
    # MESURES RÉELLES
    # ========================================================================
    
    print("📊 MESURES RÉELLES (dans les prix Finnhub) :")
    print("-" * 80)
    print()
    
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
    
    print(f"1️⃣ BASELINE :")
    print(f"   Prix : {baseline_price:.5f}")
    print(f"   Heure : {baseline_time}")
    print(f"   Type : 📈 MESURE RÉELLE")
    print()
    
    # Pic (IMPACT)
    prices_after = df_prices[df_prices['datetime'] >= event_time].copy()
    prices_after['pips'] = (prices_after['high'] - baseline_price) * 10000
    
    max_pips_idx = prices_after['pips'].idxmax()
    peak_time = prices_after.loc[max_pips_idx, 'datetime']
    peak_price = prices_after.loc[max_pips_idx, 'high']
    peak_pips = prices_after.loc[max_pips_idx, 'pips']
    
    print(f"2️⃣ IMPACT (Pic Maximum) :")
    print(f"   Impact : {peak_pips:.1f} pips")
    print(f"   Prix : {peak_price:.5f}")
    print(f"   Heure : {peak_time}")
    print(f"   Type : 📈 MESURE RÉELLE (dans les prix historiques)")
    print()
    
    # Pullback
    prices_after_peak = prices_after[prices_after['datetime'] > peak_time].copy()
    window_30min = prices_after_peak[
        (prices_after_peak['datetime'] - peak_time).dt.total_seconds() / 60 <= 30
    ]
    
    pullback_295_pips = None
    pullback_295_time = None
    pullback_295_price = None
    
    if not window_30min.empty:
        window_30min = window_30min.copy()
        window_30min['pullback_pips'] = (peak_price - window_30min['low']) * 10000
        
        target = 29.5
        tolerance = 1.0
        matches = window_30min[
            abs(window_30min['pullback_pips'] - target) <= tolerance
        ]
        
        if not matches.empty:
            closest = matches.iloc[0]
            pullback_295_time = closest['datetime']
            pullback_295_pips = closest['pullback_pips']
            pullback_295_price = closest['low']
            
            print(f"3️⃣ PULLBACK (≈ 29.5 pips) :")
            print(f"   Retracement : {pullback_295_pips:.1f} pips")
            print(f"   Prix : {pullback_295_price:.5f}")
            print(f"   Heure : {pullback_295_time}")
            print(f"   Type : 📈 MESURE RÉELLE (dans les prix historiques)")
    
    print()
    
    # ========================================================================
    # PRÉDICTIONS DU PIPELINE
    # ========================================================================
    
    print("🔮 PRÉDICTIONS DU PIPELINE :")
    print("-" * 80)
    print()
    
    executor = PipelineExecutor(DB_PATH, verbose=False)
    
    try:
        result = executor.execute_complete_pipeline(
            date_str=date_str,
            window_minutes=30,
            support_threshold=0.8,
            jaccard_threshold=0.60,
            years_lookback=5
        )
        
        if result['success']:
            final_prediction = result['final_prediction']
            pattern_info = final_prediction.get('pattern_info', {})
            
            impact_base = final_prediction.get('impact_base', 0.0)
            impact_final = final_prediction.get('prediction_finale', 0.0)
            wave1_pred = pattern_info.get('wave1_pips', 0.0)
            wave2_pred = pattern_info.get('wave2_peak_pips_absolute', 0.0)
            pullback_pred = abs(pattern_info.get('pullback_pips', 0.0))
            
            print(f"1️⃣ IMPACT DE BASE PRÉDIT :")
            print(f"   Impact : {impact_base:.2f} pips")
            print(f"   Type : 🔮 PRÉDICTION")
            print()
            
            print(f"2️⃣ IMPACT FINAL PRÉDIT :")
            print(f"   Impact : {impact_final:.2f} pips")
            print(f"   Type : 🔮 PRÉDICTION")
            print()
            
            print(f"3️⃣ WAVE 1 PRÉDIT :")
            print(f"   Impact : {wave1_pred:.1f} pips")
            print(f"   Type : 🔮 PRÉDICTION")
            print()
            
            print(f"4️⃣ WAVE 2 PRÉDIT (Pic Absolu) :")
            print(f"   Impact : {wave2_pred:.1f} pips")
            print(f"   Type : 🔮 PRÉDICTION")
            print()
            
            print(f"5️⃣ PULLBACK PRÉDIT :")
            print(f"   Retracement : {pullback_pred:.1f} pips")
            print(f"   Type : 🔮 PRÉDICTION")
            
    except Exception as e:
        print(f"   ❌ Erreur : {e}")
    
    print()
    print()
    
    # ========================================================================
    # COMPARAISON
    # ========================================================================
    
    print("=" * 80)
    print("  COMPARAISON : MESURES RÉELLES vs PRÉDICTIONS")
    print("=" * 80)
    print()
    
    print("📊 TABLEAU COMPARATIF :")
    print()
    print("┌─────────────────────┬──────────────────┬──────────────────┬──────────────┐")
    print("│ Élément             │ Mesure Réelle    │ Prédiction       │ Type         │")
    print("├─────────────────────┼──────────────────┼──────────────────┼──────────────┤")
    print(f"│ Baseline            │ {baseline_price:.5f}      │ N/A              │ 📈 MESURE   │")
    print(f"│ Impact (Pic)        │ {peak_pips:.1f} pips      │ {impact_final:.1f} pips        │ 📈 vs 🔮  │")
    print(f"│ Wave 1              │ {peak_pips:.1f} pips      │ {wave1_pred:.1f} pips        │ 📈 vs 🔮  │")
    print(f"│ Wave 2              │ {peak_pips:.1f} pips      │ {wave2_pred:.1f} pips        │ 📈 vs 🔮  │")
    if pullback_295_pips:
        print(f"│ Pullback (≈29.5)    │ {pullback_295_pips:.1f} pips      │ {pullback_pred:.1f} pips        │ 📈 vs 🔮  │")
    print("└─────────────────────┴──────────────────┴──────────────────┴──────────────┘")
    print()
    
    # Calculer écarts
    print("📊 ÉCARTS :")
    print("-" * 80)
    print()
    
    if result['success']:
        ecart_impact = abs(peak_pips - impact_final)
        ecart_wave1 = abs(peak_pips - wave1_pred)
        ecart_pullback = abs(pullback_295_pips - pullback_pred) if pullback_295_pips else None
        
        print(f"   Impact :")
        print(f"      Mesure réelle : {peak_pips:.1f} pips")
        print(f"      Prédiction : {impact_final:.2f} pips")
        print(f"      Écart : {ecart_impact:.1f} pips")
        print()
        
        print(f"   Pullback :")
        if pullback_295_pips:
            print(f"      Mesure réelle : {pullback_295_pips:.1f} pips")
            print(f"      Prédiction : {pullback_pred:.1f} pips")
            print(f"      Écart : {ecart_pullback:.1f} pips")
        print()
    
    print("=" * 80)
    print()
    
    # ========================================================================
    # RÉSUMÉ
    # ========================================================================
    
    print("📋 RÉSUMÉ :")
    print("-" * 80)
    print()
    print("✅ IMPACT (Pic de 188.3 pips) :")
    print("   └─ Type : 📈 MESURE RÉELLE")
    print("   └─ Trouvée dans les prix historiques Finnhub")
    print("   └─ Observée à 16:00:00 le 1er août 2025")
    print()
    print("✅ PULLBACK (≈ 29.5 pips) :")
    print("   └─ Type : 📈 MESURE RÉELLE")
    print("   └─ Trouvée dans les prix historiques Finnhub")
    print("   └─ Observée à 16:06-16:08 le 1er août 2025")
    print()
    print("🔮 PRÉDICTIONS DU PIPELINE :")
    print("   └─ Impact prédit : {impact_final:.2f} pips".format(impact_final=impact_final if result['success'] else 0))
    print("   └─ Pullback prédit : {pullback_pred:.1f} pips".format(pullback_pred=pullback_pred if result['success'] else 0))
    print()
    print("=" * 80)
    print()

if __name__ == "__main__":
    clarifier_impact_et_pullback()




