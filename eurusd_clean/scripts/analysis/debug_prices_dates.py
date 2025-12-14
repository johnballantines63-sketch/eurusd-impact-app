"""
Debug rapide pour comprendre pourquoi les prix ne sont pas trouvés
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'app'))

from config import get_db_path
import duckdb
import pandas as pd

db_path = get_db_path()
conn = duckdb.connect(str(db_path), read_only=True)

print("=" * 70)
print("🔍 Debug dates et prix")
print("=" * 70)

# 1. Vérifier un événement CPI du 12 août 2025
print("\n📅 Événements du 12 août 2025:")
query = """
SELECT 
    ts_utc,
    event_title,
    actual
FROM events
WHERE DATE(ts_utc) = '2025-08-12'
    AND (LOWER(event_title) LIKE '%inflation%' OR LOWER(event_title) LIKE '%cpi%')
ORDER BY ts_utc
"""
events = conn.execute(query).fetchdf()
print(events.to_string(index=False))

if len(events) > 0:
    event_time = events.iloc[0]['ts_utc']
    print(f"\n⏰ Premier événement: {event_time}")
    
    # 2. Chercher des prix autour de cette date
    print("\n💹 Prix autour de cet événement (±1 heure):")
    
    # Convertir en datetime pour manipulation
    event_dt = pd.to_datetime(event_time)
    start = event_dt - pd.Timedelta(hours=1)
    end = event_dt + pd.Timedelta(hours=1)
    
    query2 = f"""
    SELECT 
        datetime,
        close
    FROM prices_1m
    WHERE datetime >= '{start}'
        AND datetime <= '{end}'
    ORDER BY datetime
    LIMIT 10
    """
    
    prices = conn.execute(query2).fetchdf()
    
    if len(prices) > 0:
        print(f"✅ {len(prices)} prix trouvés (affichage 10 premiers):")
        print(prices.to_string(index=False))
    else:
        print("❌ Aucun prix trouvé")
        
        # Vérifier les dates disponibles dans prices_1m
        print("\n📊 Exemples de dates dans prices_1m:")
        query3 = """
        SELECT datetime
        FROM prices_1m
        ORDER BY datetime DESC
        LIMIT 5
        """
        sample = conn.execute(query3).fetchdf()
        print(sample.to_string(index=False))

conn.close()
print("\n" + "=" * 70)
