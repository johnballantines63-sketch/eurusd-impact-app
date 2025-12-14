#!/usr/bin/env python3
"""
Validation Dukascopy - Cas de référence 11 septembre 2025
Session 25 - Vérification des valeurs MT5 confirmées par André
"""

import duckdb
import pandas as pd
from pathlib import Path

def main():
    print("=" * 80)
    print("🔍 VALIDATION DUKASCOPY - CAS 11 SEPTEMBRE 2025")
    print("=" * 80)
    
    db_path = Path(__file__).parent / "fx_impact_app" / "data" / "warehouse.duckdb"
    con = duckdb.connect(str(db_path))
    
    # Points de validation (valeurs confirmées par André depuis MT5)
    validation_points = [
        ("12:30:00", 1.16816, "Annonce initiale"),
        ("12:35:00", 1.17190, "TTR (Time To Return)"),
        ("12:45:00", 1.16919, "Après pullback"),
        ("13:10:00", 1.17378, "Stabilisation Phase 2")
    ]
    
    print("\n📊 VALIDATION DES POINTS CLÉS")
    print("-" * 80)
    
    results = []
    for time, expected_price, label in validation_points:
        query = f"""
            SELECT datetime, open, high, low, close
            FROM prices_1m
            WHERE datetime = '2025-09-11 {time}'
        """
        
        result = con.execute(query).fetchone()
        
        if result:
            dt, open_p, high, low, close = result
            actual_price = close
            diff_pips = abs(actual_price - expected_price) * 10000
            
            if diff_pips <= 5:
                status = "✅"
                verdict = "OK"
            elif diff_pips <= 10:
                status = "⚠️"
                verdict = "Tolérable"
            else:
                status = "❌"
                verdict = "ÉCART IMPORTANT"
            
            print(f"\n{status} {label} ({time} UTC):")
            print(f"   Attendu : {expected_price:.5f}")
            print(f"   Dukascopy: {actual_price:.5f}")
            print(f"   Écart    : {diff_pips:.2f} pips - {verdict}")
            print(f"   OHLC     : O={open_p:.5f} H={high:.5f} L={low:.5f} C={close:.5f}")
            
            results.append(diff_pips <= 10)
        else:
            print(f"\n❌ {label} ({time} UTC): DONNÉE MANQUANTE")
            results.append(False)
    
    # PHASE 1 : Mouvement 12:30 → 12:35
    print("\n" + "=" * 80)
    print("📈 VALIDATION PHASE 1 (12:30 → 12:35 UTC)")
    print("-" * 80)
    
    query_phase1 = """
        SELECT datetime, open, high, low, close
        FROM prices_1m
        WHERE datetime >= '2025-09-11 12:30:00'
          AND datetime < '2025-09-11 12:36:00'
        ORDER BY datetime
    """
    
    df = con.execute(query_phase1).df()
    
    if not df.empty:
        print(f"\nDonnées disponibles: {len(df)} minutes")
        print("\nDétail minute par minute:")
        
        start_price = df.iloc[0]['close']
        print(f"\n   Prix départ (12:30): {start_price:.5f}")
        
        for idx, row in df.iterrows():
            time_str = row['datetime'].strftime('%H:%M')
            move = (row['close'] - start_price) * 10000
            print(f"   {time_str}: O={row['open']:.5f} H={row['high']:.5f} L={row['low']:.5f} C={row['close']:.5f} | Move={move:+.1f}p")
        
        # Calculer Phase 1
        high = df['high'].max()
        low = df['low'].min()
        
        move_up = (high - start_price) * 10000
        move_down = (start_price - low) * 10000
        phase1_pips = max(move_up, move_down)
        direction = "UP" if move_up > move_down else "DOWN"
        
        print(f"\n   High période: {high:.5f} (+{move_up:.2f} pips)")
        print(f"   Low période:  {low:.5f} ({-move_down:.2f} pips)")
        print(f"\n   📊 PHASE 1: {phase1_pips:.2f} pips ({direction})")
        print(f"   🎯 ATTENDU: 37.4 pips")
        
        phase1_diff = abs(phase1_pips - 37.4)
        
        if phase1_diff <= 5:
            status = "✅"
            verdict = "EXCELLENT"
        elif phase1_diff <= 10:
            status = "⚠️"
            verdict = "ACCEPTABLE"
        else:
            status = "❌"
            verdict = "ÉCART IMPORTANT"
        
        print(f"\n   {status} Écart: {phase1_diff:.2f} pips - {verdict}")
        results.append(phase1_diff <= 10)
    else:
        print("\n❌ Aucune donnée Phase 1")
        results.append(False)
    
    # RÉSULTAT GLOBAL
    print("\n" + "=" * 80)
    print("🎯 RÉSULTAT VALIDATION GLOBALE")
    print("=" * 80)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nPoints validés: {passed}/{total}")
    
    if all(results):
        print("\n✅✅✅ VALIDATION COMPLÈTE RÉUSSIE ✅✅✅")
        print("\nDukascopy capte correctement les mouvements!")
        print("→ Prêt pour recalculer les 944 cas extrêmes")
        print("→ Prêt pour créer la formule V4")
    elif passed >= total * 0.8:
        print("\n⚠️ VALIDATION PARTIELLE (>80%)")
        print("\nDukascopy globalement correct mais quelques écarts")
        print("→ Peut être utilisé avec prudence")
    else:
        print("\n❌ VALIDATION ÉCHOUÉE")
        print("\nÉcarts trop importants - Investigation nécessaire")
    
    con.close()

if __name__ == "__main__":
    main()
