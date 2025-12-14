"""
SESSION 86 - Workflow Timezone CORRECT

WORKFLOW :
1. Event dans DB à 12:30 UTC (colonne ts_utc)
2. Conversion : 12:30 UTC + 2h = 14:30 Bern
3. Chercher prix à 14:30+02:00 dans prices_1m
"""

import duckdb
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

DB_PATH = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/data/warehouse.duckdb")

def correct_workflow_test():
    """
    Workflow correct : Event UTC → +2h → Prix Bern
    """
    print("=" * 70)
    print("WORKFLOW TIMEZONE CORRECT")
    print("=" * 70)
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # ============================================================
    # ÉTAPE 1 : Chercher events à 12:30 UTC le 01.08.2025
    # ============================================================
    print("\n📋 ÉTAPE 1 : Chercher events NFP à 12:30 UTC")
    
    event_query = """
    SELECT 
        event_title,
        ts_utc,
        actual,
        forecast,
        previous
    FROM events
    WHERE date_part('year', ts_utc) = 2025
      AND date_part('month', ts_utc) = 8
      AND date_part('day', ts_utc) = 1
      AND date_part('hour', ts_utc) = 12
      AND date_part('minute', ts_utc) = 30
      AND (event_title LIKE '%Nonfarm%' OR event_title LIKE '%NFP%')
    ORDER BY ts_utc
    """
    
    events = conn.execute(event_query).fetchdf()
    
    print(f"\n   Events trouvés à 12:30 UTC : {len(events)}")
    
    if len(events) > 0:
        for idx, row in events.iterrows():
            print(f"\n   Event {idx+1}:")
            print(f"      Titre    : {row['event_title']}")
            print(f"      Heure    : {row['ts_utc']} (UTC)")
            print(f"      Actual   : {row['actual']}")
            print(f"      Forecast : {row['forecast']}")
        
        # ============================================================
        # ÉTAPE 2 : Conversion +2h → 14:30 Bern
        # ============================================================
        print("\n" + "=" * 70)
        print("📋 ÉTAPE 2 : Conversion UTC → Bern (+2h)")
        print("=" * 70)
        
        event_time_utc = events.iloc[0]['ts_utc']
        print(f"\n   Event heure UTC  : 12:30")
        print(f"   Conversion +2h   : 12:30 + 2h = 14:30 Bern")
        print(f"   Query prix à     : 14:30+02:00")
        
        # ============================================================
        # ÉTAPE 3 : Chercher prix à 14:30+02:00
        # ============================================================
        print("\n" + "=" * 70)
        print("📋 ÉTAPE 3 : Chercher prix à 14:30+02:00")
        print("=" * 70)
        
        price_query = """
        SELECT 
            datetime,
            close,
            high,
            low
        FROM prices_1m
        WHERE datetime >= '2025-08-01 14:25:00+02:00'
          AND datetime <= '2025-08-01 14:35:00+02:00'
        ORDER BY datetime
        """
        
        print("\n✅ Query prix (14:25-14:35 Bern) :")
        print(price_query)
        
        result = conn.execute(price_query).fetchdf()
        
        print(f"\n📊 Résultats :")
        print(f"   Lignes trouvées : {len(result)}")
        
        if len(result) > 0:
            min_price = result['close'].min()
            max_price = result['close'].max()
            range_pips = (max_price - min_price) * 10000
            
            print(f"   Min price : {min_price:.5f}")
            print(f"   Max price : {max_price:.5f}")
            print(f"   Range     : {range_pips:.1f} pips")
            
            # Validation MT5
            EXPECTED_MIN = 1.13925
            EXPECTED_MAX = 1.15875
            EXPECTED_RANGE = 195
            
            min_diff = abs(min_price - EXPECTED_MIN) * 10000
            max_diff = abs(max_price - EXPECTED_MAX) * 10000
            range_diff = abs(range_pips - EXPECTED_RANGE)
            
            print(f"\n🎯 Validation vs MT5 :")
            print(f"   Min attendu    : {EXPECTED_MIN:.5f}")
            print(f"   Min trouvé     : {min_price:.5f}")
            print(f"   Écart min      : {min_diff:.1f} pips")
            print(f"\n   Max attendu    : {EXPECTED_MAX:.5f}")
            print(f"   Max trouvé     : {max_price:.5f}")
            print(f"   Écart max      : {max_diff:.1f} pips")
            print(f"\n   Range attendu  : {EXPECTED_RANGE} pips")
            print(f"   Range trouvé   : {range_pips:.1f} pips")
            print(f"   Écart range    : {range_diff:.1f} pips")
            
            # Afficher données
            print(f"\n📈 Données minute par minute :")
            print(result.to_string())
            
            # Validation
            if min_diff < 20 and range_diff < 30:
                print(f"\n" + "=" * 70)
                print("✅✅✅ SUCCÈS ! SPIKE MT5 CAPTURÉ ✅✅✅")
                print("=" * 70)
                print("\n✅ WORKFLOW VALIDÉ :")
                print("   1. Event 12:30 UTC dans events ✓")
                print("   2. Conversion +2h → 14:30 Bern ✓")
                print("   3. Prix 14:30+02:00 dans prices_1m ✓")
                print(f"   4. Spike capturé : {min_price:.5f} → {max_price:.5f} ✓")
                
                return True
            else:
                print(f"\n⚠️  ATTENTION : Écarts importants")
                print(f"   Le spike à 1.13925 N'EST PAS capturé dans cette fenêtre")
                print(f"   → Données possiblement incomplètes dans DB")
                
                return False
        else:
            print("\n❌ Aucune donnée trouvée à 14:30+02:00")
            return False
    else:
        print("\n❌ Aucun événement NFP trouvé à 12:30 UTC le 01.08.2025")
        print("   Vérifier si événement existe à une autre heure")
        
        # Chercher tous les events du jour
        print("\n🔍 Recherche large : Tous events 01.08.2025")
        all_events = conn.execute("""
            SELECT event_title, ts_utc
            FROM events
            WHERE date_part('year', ts_utc) = 2025
              AND date_part('month', ts_utc) = 8
              AND date_part('day', ts_utc) = 1
              AND (event_title LIKE '%Nonfarm%' OR event_title LIKE '%NFP%' OR event_title LIKE '%Employment%')
            ORDER BY ts_utc
        """).fetchdf()
        
        if len(all_events) > 0:
            print(f"\n   Events trouvés : {len(all_events)}")
            print(all_events.to_string())
        else:
            print("\n   Aucun événement NFP trouvé le 01.08.2025")
        
        return False
    
    conn.close()


if __name__ == "__main__":
    success = correct_workflow_test()
    
    if success:
        print("\n✅ TEST VALIDÉ - Workflow timezone correct !")
    else:
        print("\n⚠️  Investigation supplémentaire nécessaire")
