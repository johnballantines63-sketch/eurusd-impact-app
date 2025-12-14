"""
SESSION 86 - CLARIFICATION TIMEZONE FINALE

RÈGLE CORRECTE :
- Events stockés en UTC (ex: 12:30 UTC)
- Prices stockés en Bern (+02:00)
- Conversion : 12:30 UTC = 14:30 Bern = 14:30+02:00 dans prices

DONC : Si event 12:30 UTC → chercher prix 14:30+02:00
"""

import duckdb
import pandas as pd
from pathlib import Path

DB_PATH = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/data/warehouse.duckdb")

def final_timezone_test():
    """
    Test final avec règle correcte
    """
    print("=" * 70)
    print("TEST TIMEZONE - RÈGLE FINALE CLARIFIÉE")
    print("=" * 70)
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # 1. Vérifier VRAIE heure événement 01.08.2025
    print("\n📋 ÉTAPE 1 : Vérifier heure RÉELLE événement NFP 01.08.2025")
    event_query = """
    SELECT 
        event_title,
        ts_utc,
        actual,
        forecast
    FROM events
    WHERE date_part('year', ts_utc) = 2025
      AND date_part('month', ts_utc) = 8
      AND date_part('day', ts_utc) = 1
      AND (event_title LIKE '%Nonfarm%' OR event_title LIKE '%NFP%')
    ORDER BY ts_utc
    """
    
    events = conn.execute(event_query).fetchdf()
    
    if len(events) > 0:
        print(f"\n   Événements trouvés : {len(events)}")
        for idx, row in events.iterrows():
            print(f"\n   Event {idx+1}:")
            print(f"      Titre    : {row['event_title']}")
            print(f"      Heure DB : {row['ts_utc']}")
            print(f"      Actual   : {row['actual']}")
            print(f"      Forecast : {row['forecast']}")
        
        # Prendre premier événement
        event_time = events.iloc[0]['ts_utc']
        event_time_str = str(event_time)
        
        print(f"\n   🎯 Heure à utiliser pour query prix :")
        print(f"      Event DB : {event_time_str}")
        
        # Parser l'heure
        if 'T' in event_time_str:
            date_part = event_time_str.split('T')[0]
            time_part = event_time_str.split('T')[1].split('+')[0] if '+' in event_time_str else event_time_str.split('T')[1].split('-')[0]
        else:
            # Format alternatif
            parts = event_time_str.split()
            date_part = parts[0]
            time_part = parts[1].split('+')[0] if len(parts) > 1 else '12:30:00'
        
        print(f"      Date     : {date_part}")
        print(f"      Heure    : {time_part}")
        
        # Query prix
        print("\n" + "=" * 70)
        print("📋 ÉTAPE 2 : Query prix à cette heure (avec +02:00)")
        print("=" * 70)
        
        price_query = f"""
        SELECT 
            datetime,
            close,
            high,
            low
        FROM prices_1m
        WHERE datetime >= '{date_part} {time_part}+02:00'::TIMESTAMP - INTERVAL '5 minutes'
          AND datetime <= '{date_part} {time_part}+02:00'::TIMESTAMP + INTERVAL '10 minutes'
        ORDER BY datetime
        """
        
        print(f"\n✅ Query prix (±5min autour événement) :")
        print(f"   Timestamp : {date_part} {time_part}+02:00")
        
        result = conn.execute(price_query).fetchdf()
        
        print(f"\n📊 Résultats :")
        print(f"   Lignes : {len(result)}")
        
        if len(result) > 0:
            min_price = result['close'].min()
            max_price = result['close'].max()
            range_pips = (max_price - min_price) * 10000
            
            print(f"   Min   : {min_price:.5f}")
            print(f"   Max   : {max_price:.5f}")
            print(f"   Range : {range_pips:.1f} pips")
            
            # Test MT5
            EXPECTED_MIN = 1.13925
            EXPECTED_RANGE = 195
            
            min_diff = abs(min_price - EXPECTED_MIN) * 10000
            range_diff = abs(range_pips - EXPECTED_RANGE)
            
            print(f"\n🎯 Validation MT5 :")
            print(f"   Min attendu   : {EXPECTED_MIN:.5f}")
            print(f"   Écart min     : {min_diff:.1f} pips")
            print(f"   Range attendu : {EXPECTED_RANGE} pips")
            print(f"   Écart range   : {range_diff:.1f} pips")
            
            print(f"\n📈 Données :")
            print(result.to_string())
            
            if min_diff < 20 and range_diff < 30:
                print(f"\n✅✅✅ SUCCÈS ✅✅✅")
                return True
            else:
                print(f"\n⚠️  Spike non capturé - investigation nécessaire")
                return False
    else:
        print("\n❌ Aucun événement NFP trouvé le 01.08.2025")
        return False
    
    conn.close()


if __name__ == "__main__":
    success = final_timezone_test()
