"""
Chercher le prix 1.17736 autour de 08:00 le 09.09.2025
"""

import sys
from pathlib import Path
from datetime import datetime
import pytz
import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from config import DB_PATH
import duckdb


def main():
    tz = pytz.timezone('Europe/Zurich')
    target_dt = tz.localize(datetime(2025, 9, 9, 8, 0))
    target_price = 1.17736
    
    conn = duckdb.connect(str(DB_PATH))
    
    # Chercher dans une fenêtre large autour de 08:00
    query = f"""
    SELECT datetime, close, high, low
    FROM prices_bern
    WHERE DATE(datetime) = '2025-09-09'
      AND EXTRACT(HOUR FROM datetime) BETWEEN 6 AND 10
    ORDER BY datetime
    """
    
    df = conn.execute(query).df()
    conn.close()
    
    df['datetime'] = pd.to_datetime(df['datetime'])
    if df['datetime'].dt.tz is None:
        df['datetime'] = df['datetime'].dt.tz_localize('Europe/Zurich')
    else:
        df['datetime'] = df['datetime'].dt.tz_convert('Europe/Zurich')
    
    print("=" * 80)
    print(f"RECHERCHE PRIX {target_price} AUTOUR DE 08:00 LE 09.09.2025")
    print("=" * 80)
    print()
    
    # Chercher le prix le plus proche de 1.17736
    df['diff'] = abs(df['close'] - target_price)
    closest_idx = df['diff'].idxmin()
    closest_row = df.loc[closest_idx]
    
    print(f"Prix le plus proche de {target_price} :")
    print(f"  Datetime : {closest_row['datetime']}")
    print(f"  Close : {closest_row['close']:.5f}")
    print(f"  High : {closest_row['high']:.5f}")
    print(f"  Low : {closest_row['low']:.5f}")
    print(f"  Différence : {closest_row['diff']:.5f}")
    print()
    
    # Afficher les prix autour de 08:00
    print("Prix autour de 08:00 (07:30-08:30) :")
    df_around = df[(df['datetime'] >= target_dt - pd.Timedelta(minutes=30)) & 
                   (df['datetime'] <= target_dt + pd.Timedelta(minutes=30))]
    print(df_around[['datetime', 'close', 'high', 'low']].to_string(index=False))
    print()
    
    # Chercher si 1.17736 est dans les high
    df_high_match = df[abs(df['high'] - target_price) < 0.0001]
    if len(df_high_match) > 0:
        print(f"✅ Prix {target_price} trouvé dans les HIGH :")
        for _, row in df_high_match.iterrows():
            print(f"  {row['datetime']} : high={row['high']:.5f}, close={row['close']:.5f}")
    else:
        print(f"❌ Prix {target_price} non trouvé dans les HIGH")
    
    # Chercher le maximum dans cette fenêtre
    max_idx = df['close'].idxmax()
    max_row = df.loc[max_idx]
    print()
    print(f"Maximum dans la fenêtre 06:00-10:00 :")
    print(f"  Datetime : {max_row['datetime']}")
    print(f"  Close : {max_row['close']:.5f}")
    print(f"  High : {max_row['high']:.5f}")


if __name__ == '__main__':
    main()


