#!/usr/bin/env python3
"""
Vérification directe dans DuckDB - 11 septembre 2025
Vérifie si les données prices_1m sont correctes
"""

import duckdb
import pandas as pd

print("=" * 70)
print("VÉRIFICATION DIRECTE BASE DE DONNÉES - 11 SEPTEMBRE 2025")
print("=" * 70)

# Connexion à la base
con = duckdb.connect('fx_impact_app/data/warehouse.duckdb')

# Vérifier le 11 septembre dans prices_1m
print("\n📊 Extraction données 11 septembre 12:30-12:45 UTC...")

query = """
SELECT datetime, open, high, low, close
FROM prices_1m
WHERE datetime >= '2025-09-11 12:30:00'
  AND datetime <= '2025-09-11 12:45:00'
ORDER BY datetime
"""

try:
    df = con.execute(query).df()
    
    if len(df) == 0:
        print("\n❌ AUCUNE DONNÉE TROUVÉE pour cette période")
        
        # Vérifier si des données existent pour le 11 septembre
        query_day = """
        SELECT datetime, open, high, low, close
        FROM prices_1m
        WHERE datetime >= '2025-09-11 00:00:00'
          AND datetime < '2025-09-12 00:00:00'
        ORDER BY datetime
        LIMIT 10
        """
        df_day = con.execute(query_day).df()
        
        if len(df_day) > 0:
            print(f"\n⚠️  Mais il y a {len(df_day)} lignes pour le 11 septembre")
            print("\nPremières lignes disponibles:")
            print(df_day.to_string())
        else:
            print("\n❌ Aucune donnée du tout pour le 11 septembre 2025")
            
    else:
        print(f"\n✅ {len(df)} minutes de données trouvées\n")
        print(df.to_string())
        
        # Calculer Phase 1
        print("\n" + "=" * 70)
        print("CALCUL PHASE 1")
        print("=" * 70)
        
        start_price = df.iloc[0]['open']
        max_high = df['high'].max()
        min_low = df['low'].min()
        
        phase1_up = (max_high - start_price) * 10000
        phase1_down = (start_price - min_low) * 10000
        phase1 = max(phase1_up, phase1_down)
        
        print(f"\n📍 Prix départ (12:30 open): {start_price:.5f}")
        print(f"📈 Plus haut sur 15 min:      {max_high:.5f}")
        print(f"📉 Plus bas sur 15 min:       {min_low:.5f}")
        
        print(f"\n🎯 Phase 1 calculée: {phase1:.2f} pips")
        print(f"   Direction: {'UP' if phase1_up > phase1_down else 'DOWN'}")
        
        # VALIDATION vs référence
        print("\n" + "=" * 70)
        print("VALIDATION VS RÉFÉRENCE MT5")
        print("=" * 70)
        
        expected_start = 1.16816
        expected_phase1 = 37.4
        
        error_start = abs(start_price - expected_start) * 10000
        error_phase1 = abs(phase1 - expected_phase1)
        error_pct = (error_phase1 / expected_phase1) * 100
        
        print(f"\n📍 Prix départ:")
        print(f"   Attendu (MT5):  1.16816")
        print(f"   Trouvé (DB):    {start_price:.5f}")
        print(f"   Écart:          {error_start:.1f} pips")
        
        if error_start <= 5:
            print(f"   Statut: ✅ EXCELLENT")
        elif error_start <= 10:
            print(f"   Statut: ⚠️  ACCEPTABLE")
        else:
            print(f"   Statut: ❌ PROBLÈME")
        
        print(f"\n🎯 Phase 1:")
        print(f"   Attendu (MT5):  37.4 pips")
        print(f"   Trouvé (DB):    {phase1:.2f} pips")
        print(f"   Écart:          {error_phase1:.2f} pips ({error_pct:.1f}%)")
        
        if error_phase1 <= 5:
            print(f"   Statut: ✅ EXCELLENT")
        elif error_phase1 <= 10:
            print(f"   Statut: ⚠️  ACCEPTABLE")
        else:
            print(f"   Statut: ❌ PROBLÈME")
            
        # CONCLUSION
        print("\n" + "=" * 70)
        print("CONCLUSION")
        print("=" * 70)
        
        if error_start <= 10 and error_phase1 <= 10:
            print("\n✅✅✅ DONNÉES VALIDÉES - Base de données correcte")
            print("\nLe problème vient du CSV, pas de la DB.")
            print("Il faut régénérer le CSV depuis la DB.")
        elif error_start > 50:
            print("\n❌ DONNÉES INCORRECTES - Problème de timezone probable")
            print("\nLes prix sont décalés de ~50 pips = problème d'heure")
        else:
            print("\n⚠️  DONNÉES PARTIELLEMENT CORRECTES")
            print("\nInvestigation nécessaire.")

except Exception as e:
    print(f"\n❌ ERREUR: {e}")

finally:
    con.close()

print("\n" + "=" * 70)
