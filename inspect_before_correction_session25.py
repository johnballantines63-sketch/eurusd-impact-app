#!/usr/bin/env python3
"""
Inspection complète DB avant correction - Session 25
Vérifie structure et données avant d'ajouter 2h
"""

import duckdb
import pandas as pd
from pathlib import Path

def main():
    print("=" * 80)
    print("🔍 INSPECTION COMPLÈTE DB AVANT CORRECTION")
    print("=" * 80)
    
    db_path = Path(__file__).parent / "fx_impact_app" / "data" / "warehouse.duckdb"
    con = duckdb.connect(str(db_path))
    
    # 1. Structure table
    print("\n📋 STRUCTURE TABLE prices_1m:")
    print("-" * 80)
    
    schema = con.execute("DESCRIBE prices_1m").df()
    print(schema.to_string(index=False))
    
    # 2. Types de données
    print("\n📊 TYPES DE DONNÉES:")
    print("-" * 80)
    for idx, row in schema.iterrows():
        print(f"   {row['column_name']:<15} : {row['column_type']}")
    
    # 3. Statistiques
    print("\n📊 STATISTIQUES GÉNÉRALES:")
    print("-" * 80)
    
    stats = con.execute("""
        SELECT 
            COUNT(*) as total,
            MIN(datetime) as min_dt,
            MAX(datetime) as max_dt,
            COUNT(DISTINCT DATE(datetime)) as days
        FROM prices_1m
    """).df().iloc[0]
    
    print(f"Total lignes: {stats['total']:,}")
    print(f"Min datetime: {stats['min_dt']}")
    print(f"Max datetime: {stats['max_dt']}")
    print(f"Jours uniques: {stats['days']}")
    
    # 4. Échantillons à différentes heures
    print("\n📋 ÉCHANTILLONS 11 SEPTEMBRE 2025:")
    print("-" * 80)
    
    times_to_check = [
        ("12:30", "12:30:00", "12:35:00"),
        ("13:30", "13:30:00", "13:35:00"),
        ("14:30", "14:30:00", "14:35:00"),
        ("15:30", "15:30:00", "15:35:00"),
    ]
    
    for label, start, end in times_to_check:
        query = f"""
            SELECT datetime, close
            FROM prices_1m
            WHERE datetime >= '2025-09-11 {start}'
              AND datetime <= '2025-09-11 {end}'
            ORDER BY datetime
            LIMIT 3
        """
        
        df = con.execute(query).df()
        
        if not df.empty:
            print(f"\n{label} UTC: {len(df)} lignes")
            for idx, row in df.iterrows():
                print(f"   {row['datetime']} | Close={row['close']:.5f}")
        else:
            print(f"\n{label} UTC: Aucune donnée")
    
    # 5. Calcul mouvements à chaque heure
    print("\n" + "=" * 80)
    print("📊 MOUVEMENTS PHASE 1 (5 minutes) PAR HEURE:")
    print("=" * 80)
    
    movements = []
    
    for label, start, end in times_to_check:
        query = f"""
            SELECT datetime, open, high, low, close
            FROM prices_1m
            WHERE datetime >= '2025-09-11 {start}'
              AND datetime < '2025-09-11 {start.split(':')[0]}:35:00'
            ORDER BY datetime
        """
        
        df = con.execute(query).df()
        
        if not df.empty and len(df) >= 2:
            start_price = df.iloc[0]['close']
            high = df['high'].max()
            low = df['low'].min()
            
            move_up = (high - start_price) * 10000
            move_down = (start_price - low) * 10000
            phase1 = max(move_up, move_down)
            
            movements.append({
                'heure': label,
                'pips': phase1,
                'lignes': len(df)
            })
        else:
            movements.append({
                'heure': label,
                'pips': 0,
                'lignes': 0
            })
    
    print("\n" + "-" * 80)
    for m in movements:
        if m['lignes'] > 0:
            marker = "🎯" if abs(m['pips'] - 37.4) <= 5 else "  "
            print(f"{marker} {m['heure']} UTC: {m['pips']:.2f} pips ({m['lignes']} lignes)")
        else:
            print(f"   {m['heure']} UTC: Pas de données")
    
    print("\n🎯 Référence MT5: 37.4 pips à 14:30 Berne (= 12:30 UTC attendu)")
    
    # 6. Vérification cohérence OHLC
    print("\n" + "=" * 80)
    print("🔍 VÉRIFICATION COHÉRENCE OHLC:")
    print("=" * 80)
    
    check_ohlc = con.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN high < low THEN 1 ELSE 0 END) as high_lt_low,
            SUM(CASE WHEN high < open THEN 1 ELSE 0 END) as high_lt_open,
            SUM(CASE WHEN high < close THEN 1 ELSE 0 END) as high_lt_close,
            SUM(CASE WHEN low > open THEN 1 ELSE 0 END) as low_gt_open,
            SUM(CASE WHEN low > close THEN 1 ELSE 0 END) as low_gt_close,
            SUM(CASE WHEN open IS NULL THEN 1 ELSE 0 END) as null_open,
            SUM(CASE WHEN close IS NULL THEN 1 ELSE 0 END) as null_close
        FROM prices_1m
    """).df().iloc[0]
    
    print(f"\nTotal lignes: {check_ohlc['total']:,}")
    print(f"\nIncohérences détectées:")
    print(f"   High < Low:   {check_ohlc['high_lt_low']:,}")
    print(f"   High < Open:  {check_ohlc['high_lt_open']:,}")
    print(f"   High < Close: {check_ohlc['high_lt_close']:,}")
    print(f"   Low > Open:   {check_ohlc['low_gt_open']:,}")
    print(f"   Low > Close:  {check_ohlc['low_gt_close']:,}")
    print(f"   Open NULL:    {check_ohlc['null_open']:,}")
    print(f"   Close NULL:   {check_ohlc['null_close']:,}")
    
    if (check_ohlc['high_lt_low'] == 0 and 
        check_ohlc['null_open'] == 0 and 
        check_ohlc['null_close'] == 0):
        print("\n✅ Données cohérentes - OK pour correction")
    else:
        print("\n⚠️ Incohérences détectées - Attention !")
    
    # 7. Résumé et recommandation
    print("\n" + "=" * 80)
    print("📋 RÉSUMÉ ET RECOMMANDATION:")
    print("=" * 80)
    
    # Trouver quelle heure a le mouvement ~37 pips
    best_match = min(movements, key=lambda x: abs(x['pips'] - 37.4) if x['lignes'] > 0 else 999)
    
    if best_match['pips'] > 0:
        print(f"\n✅ Mouvement de {best_match['pips']:.2f} pips trouvé à {best_match['heure']} UTC")
        print(f"   MT5 attend ce mouvement à 14:30 Berne = 12:30 UTC")
        
        if best_match['heure'] == "12:30":
            print(f"\n   ✅ Pas de correction nécessaire !")
        elif best_match['heure'] == "14:30":
            print(f"\n   ⚠️ Décalage de 2h détecté")
            print(f"   → SOLUTION: SOUSTRAIRE 2h de tous les timestamps")
            print(f"   → 14:30 UTC deviendra 12:30 UTC")
        elif best_match['heure'] == "13:30":
            print(f"\n   ⚠️ Décalage de 1h détecté")
            print(f"   → SOLUTION: SOUSTRAIRE 1h de tous les timestamps")
        elif best_match['heure'] == "15:30":
            print(f"\n   ⚠️ Décalage de 3h détecté")
            print(f"   → SOLUTION: SOUSTRAIRE 3h de tous les timestamps")
    else:
        print(f"\n❌ Mouvement de ~37 pips non trouvé aux heures testées")
    
    con.close()
    
    print("\n" + "=" * 80)
    print("Fin de l'inspection")
    print("=" * 80)

if __name__ == "__main__":
    main()
