"""
Créer la vue prices_1h pour agrégation H1 des prix
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from config import DB_PATH
import duckdb

print('='*80)
print('CRÉATION VUE prices_1h')
print('='*80)
print()

conn = duckdb.connect(str(DB_PATH))

# Supprimer la vue si elle existe déjà
try:
    conn.execute("DROP VIEW IF EXISTS prices_1h")
    print('✅ Vue prices_1h supprimée (si elle existait)')
except:
    pass

# Créer la vue H1
query = """
CREATE VIEW prices_1h AS
WITH prices_with_1h AS (
    SELECT 
        datetime,
        DATE_TRUNC('hour', datetime) AS datetime_1h,
        open,
        high,
        low,
        close
    FROM prices_bern
),
prices_agg AS (
    SELECT 
        datetime_1h,
        FIRST_VALUE(open) OVER (PARTITION BY datetime_1h ORDER BY datetime) AS open,
        MAX(high) OVER (PARTITION BY datetime_1h) AS high,
        MIN(low) OVER (PARTITION BY datetime_1h) AS low,
        LAST_VALUE(close) OVER (PARTITION BY datetime_1h ORDER BY datetime ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS close
    FROM prices_with_1h
)
SELECT DISTINCT
    datetime_1h AS datetime,
    open,
    high,
    low,
    close
FROM prices_agg
ORDER BY datetime
"""

try:
    conn.execute(query)
    print('✅ Vue prices_1h créée avec succès')
    print()
    
    # Tester la vue
    test_query = """
    SELECT COUNT(*) as nb_bougies, 
           MIN(datetime) as date_min, 
           MAX(datetime) as date_max
    FROM prices_1h
    """
    result = conn.execute(test_query).fetchone()
    print(f'✅ Test de la vue :')
    print(f'   Nombre de bougies H1 : {result[0]:,}')
    print(f'   Date min : {result[1]}')
    print(f'   Date max : {result[2]}')
    print()
    
    # Vérifier quelques bougies autour du pic attendu (09.09.2025 05:00-08:00)
    sample_query = """
    SELECT datetime, open, high, low, close
    FROM prices_1h
    WHERE datetime >= '2025-09-09 05:00:00+02:00'
      AND datetime <= '2025-09-09 08:00:00+02:00'
    ORDER BY datetime
    """
    sample = conn.execute(sample_query).df()
    print('✅ Exemple de bougies H1 (09.09.2025 05:00-08:00):')
    for _, row in sample.iterrows():
        print(f'   {row["datetime"]} : high={row["high"]:.5f}, close={row["close"]:.5f}')
    
    # Trouver le maximum dans cette fenêtre
    if len(sample) > 0:
        max_idx = sample['high'].idxmax()
        max_row = sample.loc[max_idx]
        print()
        print(f'✅ Maximum dans cette fenêtre : {max_row["high"]:.5f} à {max_row["datetime"]}')
    
except Exception as e:
    print(f'❌ Erreur lors de la création de la vue : {e}')
    import traceback
    traceback.print_exc()

conn.close()


