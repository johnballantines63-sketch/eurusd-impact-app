#!/usr/bin/env python3
"""
Correction finale timezone - Session 25
SOUSTRAIT 2 heures de tous les timestamps
14:30 UTC → 12:30 UTC
"""

import duckdb
from pathlib import Path

def main():
    print("=" * 80)
    print("🔧 CORRECTION TIMEZONE - SOUSTRAIRE 2 HEURES")
    print("=" * 80)
    
    db_path = Path(__file__).parent / "fx_impact_app" / "data" / "warehouse.duckdb"
    con = duckdb.connect(str(db_path))
    
    # 1. Stats avant
    print("\n📊 AVANT CORRECTION:")
    print("-" * 80)
    
    count = con.execute("SELECT COUNT(*) FROM prices_1m").fetchone()[0]
    print(f"Total lignes: {count:,}")
    
    # Échantillon avant
    print("\nÉchantillon 14:30 UTC (AVANT):")
    before = con.execute("""
        SELECT datetime, close
        FROM prices_1m
        WHERE datetime >= '2025-09-11 14:30:00'
          AND datetime <= '2025-09-11 14:32:00'
        ORDER BY datetime
    """).df()
    
    for idx, row in before.iterrows():
        print(f"   {row['datetime']} | Close={row['close']:.5f}")
    
    # 2. Confirmation
    print("\n" + "=" * 80)
    print("⚠️  OPÉRATION À EFFECTUER")
    print("=" * 80)
    print("\nAction: SOUSTRAIRE 2 heures de tous les timestamps")
    print("Résultat:")
    print("   14:30 UTC → 12:30 UTC ✅")
    print("   Mouvement 41.2 pips sera à 12:30 UTC (= 14:30 Berne MT5)")
    print(f"\nLignes à corriger: {count:,}")
    
    response = input("\n   Confirmer la correction? (oui/non): ")
    
    if response.lower() not in ['oui', 'yes', 'o', 'y']:
        print("\n❌ Correction annulée.")
        con.close()
        return
    
    # 3. Correction
    print("\n🔧 Application de la correction...")
    
    # Créer table temporaire avec timestamps corrigés
    print("   Création table temporaire...")
    con.execute("""
        CREATE TEMPORARY TABLE prices_1m_corrected AS
        SELECT 
            datetime - INTERVAL '2 hours' AS datetime,
            timestamp,
            gmtoffset,
            open,
            high,
            low,
            close,
            volume
        FROM prices_1m
    """)
    print("   ✅ Table temporaire créée")
    
    # Vérifier échantillon corrigé
    print("\n   Vérification échantillon corrigé:")
    check = con.execute("""
        SELECT datetime, close
        FROM prices_1m_corrected
        WHERE datetime >= '2025-09-11 12:30:00'
          AND datetime <= '2025-09-11 12:32:00'
        ORDER BY datetime
    """).df()
    
    if not check.empty:
        for idx, row in check.iterrows():
            print(f"      {row['datetime']} | Close={row['close']:.5f}")
        
        # Calculer mouvement Phase 1 corrigé
        phase1_check = con.execute("""
            SELECT 
                MIN(close) as start_price,
                MAX(high) as high,
                MIN(low) as low
            FROM prices_1m_corrected
            WHERE datetime >= '2025-09-11 12:30:00'
              AND datetime < '2025-09-11 12:36:00'
        """).df().iloc[0]
        
        move_up = (phase1_check['high'] - phase1_check['start_price']) * 10000
        move_down = (phase1_check['start_price'] - phase1_check['low']) * 10000
        phase1 = max(move_up, move_down)
        
        print(f"\n      Phase 1 (12:30→12:35): {phase1:.2f} pips")
        print(f"      Attendu MT5: 37.4 pips")
        
        if abs(phase1 - 37.4) <= 10:
            print(f"      ✅ EXCELLENT! Écart de {abs(phase1 - 37.4):.2f} pips")
        else:
            print(f"      ⚠️ Écart de {abs(phase1 - 37.4):.2f} pips")
            response = input("\n   Continuer quand même? (oui/non): ")
            if response.lower() not in ['oui', 'yes', 'o', 'y']:
                con.execute("DROP TABLE prices_1m_corrected")
                con.close()
                return
    else:
        print("      ⚠️ Aucune donnée à 12:30 après correction")
        response = input("\n   Continuer quand même? (oui/non): ")
        if response.lower() not in ['oui', 'yes', 'o', 'y']:
            con.execute("DROP TABLE prices_1m_corrected")
            con.close()
            return
    
    # Remplacer les données
    print("\n   Remplacement des données...")
    con.execute("DELETE FROM prices_1m")
    print("      ✅ Table originale vidée")
    
    con.execute("""
        INSERT INTO prices_1m
        SELECT * FROM prices_1m_corrected
    """)
    print("      ✅ Données corrigées insérées")
    
    con.execute("DROP TABLE prices_1m_corrected")
    print("      ✅ Table temporaire supprimée")
    
    # 4. Vérification finale
    print("\n" + "=" * 80)
    print("✅ VÉRIFICATION FINALE")
    print("=" * 80)
    
    count_after = con.execute("SELECT COUNT(*) FROM prices_1m").fetchone()[0]
    print(f"\nTotal lignes: {count_after:,}")
    
    if count_after != count:
        print(f"⚠️ Nombre de lignes différent! ({count:,} → {count_after:,})")
    else:
        print(f"✅ Nombre de lignes identique")
    
    # Vérifier 12:30 UTC
    print("\n📋 Validation 11 septembre 12:30 UTC:")
    final = con.execute("""
        SELECT datetime, open, high, low, close
        FROM prices_1m
        WHERE datetime >= '2025-09-11 12:30:00'
          AND datetime <= '2025-09-11 12:35:00'
        ORDER BY datetime
    """).df()
    
    if not final.empty:
        print(f"   Trouvé: {len(final)} lignes")
        
        for idx, row in final.iterrows():
            print(f"   {row['datetime']} | O={row['open']:.5f} H={row['high']:.5f} L={row['low']:.5f} C={row['close']:.5f}")
        
        # Phase 1 finale
        start = final.iloc[0]['close']
        high = final['high'].max()
        low = final['low'].min()
        
        move_up = (high - start) * 10000
        move_down = (start - low) * 10000
        phase1_final = max(move_up, move_down)
        
        print(f"\n   📊 Phase 1: {phase1_final:.2f} pips")
        print(f"   🎯 Attendu: 37.4 pips")
        
        diff = abs(phase1_final - 37.4)
        if diff <= 5:
            print(f"   ✅ EXCELLENT! Écart de {diff:.2f} pips")
        elif diff <= 10:
            print(f"   ⚠️ Acceptable. Écart de {diff:.2f} pips")
        else:
            print(f"   ❌ Écart important: {diff:.2f} pips")
    else:
        print("   ❌ Aucune donnée à 12:30 UTC")
    
    # Stats période
    stats = con.execute("""
        SELECT 
            MIN(datetime) as min_date,
            MAX(datetime) as max_date
        FROM prices_1m
    """).df().iloc[0]
    
    print(f"\n📊 Période couverte:")
    print(f"   {stats['min_date']} → {stats['max_date']}")
    
    con.close()
    
    print("\n" + "=" * 80)
    print("✅ CORRECTION TERMINÉE")
    print("=" * 80)
    print("\n➡️ Prochaine étape:")
    print("   python3 validate_reference_case_session25.py")

if __name__ == "__main__":
    main()
