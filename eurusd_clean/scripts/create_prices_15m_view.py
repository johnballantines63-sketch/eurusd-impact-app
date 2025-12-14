"""
Créer la vue prices_15m pour agrégation M15 des prix
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from config import DB_PATH
import duckdb

print('='*80)
print('CRÉATION VUE prices_15m')
print('='*80)
print()

conn = duckdb.connect(str(DB_PATH))

# Supprimer la vue si elle existe déjà
try:
    conn.execute("DROP VIEW IF EXISTS prices_15m")
    print('✅ Vue prices_15m supprimée (si elle existait)')
except:
    pass

# Créer la vue M15
# Note: DuckDB ne supporte pas directement DATE_TRUNC avec minutes, donc on utilise une CTE
query = """
CREATE VIEW prices_15m AS
WITH prices_with_15m AS (
    SELECT 
        datetime,
        open,
        high,
        low,
        close,
        -- Arrondir à l'intervalle de 15 minutes le plus proche
        DATE_TRUNC('hour', datetime) + 
        (FLOOR(EXTRACT(MINUTE FROM datetime)::INTEGER / 15) * 15) * INTERVAL '1 minute' AS datetime_15m
    FROM prices_bern
)
SELECT 
    datetime_15m AS datetime,
    FIRST_VALUE(open) OVER (PARTITION BY datetime_15m ORDER BY datetime) AS open,
    MAX(high) OVER (PARTITION BY datetime_15m) AS high,
    MIN(low) OVER (PARTITION BY datetime_15m) AS low,
    LAST_VALUE(close) OVER (PARTITION BY datetime_15m ORDER BY datetime ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS close
FROM prices_with_15m
GROUP BY datetime_15m, open, high, low, close
ORDER BY datetime_15m
"""

# Utiliser window functions pour obtenir open et close
query = """
CREATE VIEW prices_15m AS
WITH prices_with_15m AS (
    SELECT 
        datetime,
        DATE_TRUNC('hour', datetime) + 
        (FLOOR(EXTRACT(MINUTE FROM datetime)::INTEGER / 15) * 15) * INTERVAL '1 minute' AS datetime_15m,
        open,
        high,
        low,
        close
    FROM prices_bern
),
prices_agg AS (
    SELECT 
        datetime_15m,
        FIRST_VALUE(open) OVER (PARTITION BY datetime_15m ORDER BY datetime) AS open,
        MAX(high) OVER (PARTITION BY datetime_15m) AS high,
        MIN(low) OVER (PARTITION BY datetime_15m) AS low,
        LAST_VALUE(close) OVER (PARTITION BY datetime_15m ORDER BY datetime ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS close
    FROM prices_with_15m
)
SELECT DISTINCT
    datetime_15m AS datetime,
    open,
    high,
    low,
    close
FROM prices_agg
ORDER BY datetime
"""

try:
    conn.execute(query)
    print('✅ Vue prices_15m créée avec succès')
    print()
    
    # Tester la vue
    test_query = """
    SELECT COUNT(*) as nb_bougies, 
           MIN(datetime) as date_min, 
           MAX(datetime) as date_max
    FROM prices_15m
    """
    result = conn.execute(test_query).fetchone()
    print(f'✅ Test de la vue :')
    print(f'   Nombre de bougies M15 : {result[0]:,}')
    print(f'   Date min : {result[1]}')
    print(f'   Date max : {result[2]}')
    print()
    
    # Vérifier quelques bougies
    sample_query = """
    SELECT datetime, open, high, low, close
    FROM prices_15m
    WHERE datetime >= '2025-09-09 05:00:00+02:00'
      AND datetime <= '2025-09-09 08:00:00+02:00'
    ORDER BY datetime
    LIMIT 10
    """
    sample = conn.execute(sample_query).df()
    print('✅ Exemple de bougies M15 (09.09.2025 05:00-08:00):')
    for _, row in sample.iterrows():
        print(f'   {row["datetime"]} : high={row["high"]:.5f}, close={row["close"]:.5f}')
    
except Exception as e:
    print(f'❌ Erreur lors de la création de la vue : {e}')
    import traceback
    traceback.print_exc()

conn.close()

