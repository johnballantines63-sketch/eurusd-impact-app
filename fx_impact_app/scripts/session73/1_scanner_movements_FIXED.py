#!/usr/bin/env python3
"""
SESSION 73 - PHASE 1 : SCANNER MOUVEMENTS FORTS EUR/USD

Objectif : Identifier 40 mouvements forts (50-150+ pips) depuis prices_1m
- 20 mouvements en 2024
- 20 mouvements en 2025
- Fenêtre de calcul : 60 minutes
- Pays : US + EU + autres

Output : movements_session73.csv
"""

import duckdb
import pandas as pd
from pathlib import Path
from datetime import datetime

# ==============================================================================
# CONFIGURATION
# ==============================================================================

# Chemin base de données
DB_PATH = Path(__file__).parent.parent.parent / "data" / "warehouse.duckdb"

# Paramètres scanner
MIN_IMPACT_PIPS = 50.0           # Seuil minimum (moyen)
MAX_IMPACT_PIPS = None           # Pas de limite haute (inclut forts 150+)
LOOKBACK_MINUTES = 60            # Fenêtre glissante
MOVEMENTS_PER_YEAR = 20          # 20 par année

# Périodes
PERIODS = [
    ("2024-01-01", "2024-12-31", "2024"),
    ("2025-01-01", "2025-10-24", "2025")
]

# Output
OUTPUT_FILE = Path(__file__).parent / "movements_session73.csv"


# ==============================================================================
# FONCTIONS
# ==============================================================================

def scan_movements(conn, start_date, end_date, limit):
    """
    Scanner mouvements forts dans prices_1m avec fenêtre glissante.
    
    Logique :
    1. Pour chaque point : calculer impact sur 60 min suivantes
    2. Garder seulement mouvements > MIN_IMPACT_PIPS
    3. Trier par impact absolu décroissant
    4. Limiter à top N
    
    Args:
        conn: Connexion DuckDB
        start_date: Date début (str YYYY-MM-DD)
        end_date: Date fin (str YYYY-MM-DD)
        limit: Nombre max mouvements
        
    Returns:
        DataFrame avec colonnes : date, time, datetime, price_start, price_peak, 
                                  impact_pips, duration_min, direction
    """
    
    query = f"""
    WITH price_windows AS (
        SELECT 
            datetime as start_time,
            close as price_start,
            CAST(DATE(datetime) AS VARCHAR) as date,
            strftime(datetime, '%H:%M') as time,
            
            -- Chercher peak dans 60 min suivantes
            (
                SELECT close
                FROM prices_1m p2
                WHERE p2.datetime >= p1.datetime 
                  AND p2.datetime <= p1.datetime + INTERVAL '60 minutes'
                ORDER BY ABS(p2.close - p1.close) DESC
                LIMIT 1
            ) as price_peak,
            
            -- Temps du peak
            (
                SELECT p2.datetime
                FROM prices_1m p2
                WHERE p2.datetime >= p1.datetime 
                  AND p2.datetime <= p1.datetime + INTERVAL '60 minutes'
                ORDER BY ABS(p2.close - p1.close) DESC
                LIMIT 1
            ) as peak_time
            
        FROM prices_1m p1
        WHERE DATE(p1.datetime) >= '{start_date}'
          AND DATE(p1.datetime) <= '{end_date}'
    ),
    movements AS (
        SELECT 
            date,
            time,
            start_time as datetime,
            price_start,
            price_peak,
            (price_peak - price_start) * 10000 as impact_pips,
            CASE 
                WHEN price_peak > price_start THEN 1 
                ELSE -1 
            END as direction,
            EXTRACT(EPOCH FROM (peak_time - start_time)) / 60 as duration_min
        FROM price_windows
        WHERE price_peak IS NOT NULL
          AND ABS((price_peak - price_start) * 10000) >= {MIN_IMPACT_PIPS}
    )
    SELECT 
        date,
        time,
        datetime,
        ROUND(price_start, 5) as price_start,
        ROUND(price_peak, 5) as price_peak,
        ROUND(impact_pips, 1) as impact_pips,
        ROUND(duration_min, 1) as duration_min,
        direction
    FROM movements
    ORDER BY ABS(impact_pips) DESC
    LIMIT {limit}
    """
    
    print(f"   Exécution query SQL...")
    df = conn.execute(query).fetchdf()
    print(f"   ✅ {len(df)} mouvements trouvés")
    
    return df


def display_statistics(df, year):
    """Afficher statistiques descriptives."""
    
    print(f"\n📊 STATISTIQUES {year}")
    print("=" * 60)
    
    print(f"\n🎯 Impact (pips)")
    print(f"   Minimum    : {df['impact_pips'].abs().min():.1f} pips")
    print(f"   Maximum    : {df['impact_pips'].abs().max():.1f} pips")
    print(f"   Moyenne    : {df['impact_pips'].abs().mean():.1f} pips")
    print(f"   Médiane    : {df['impact_pips'].abs().median():.1f} pips")
    
    print(f"\n⏱️  Durée jusqu'au peak")
    print(f"   Minimum    : {df['duration_min'].min():.1f} min")
    print(f"   Maximum    : {df['duration_min'].max():.1f} min")
    print(f"   Moyenne    : {df['duration_min'].mean():.1f} min")
    print(f"   Médiane    : {df['duration_min'].median():.1f} min")
    
    print(f"\n📈 Direction")
    up = (df['direction'] == 1).sum()
    down = (df['direction'] == -1).sum()
    print(f"   UP (+)     : {up} mouvements ({up/len(df)*100:.1f}%)")
    print(f"   DOWN (-)   : {down} mouvements ({down/len(df)*100:.1f}%)")
    
    print(f"\n📅 Distribution mensuelle")
    # Convertir date en string pour groupby
    monthly = df.groupby(df['date'].str[:7]).size().sort_index()
    for month, count in monthly.items():
        print(f"   {month}    : {count} mouvements")


def display_top_movements(df, n=10):
    """Afficher top N mouvements."""
    
    print(f"\n🏆 TOP {n} MOUVEMENTS")
    print("=" * 100)
    print(f"{'Date':<12} {'Heure':<6} {'Impact':<12} {'Durée':<10} {'Direction':<10} {'Prix Départ → Peak'}")
    print("-" * 100)
    
    for _, row in df.head(n).iterrows():
        impact = f"{row['impact_pips']:+.1f} pips"
        duration = f"{row['duration_min']:.0f} min"
        direction = "UP ↑" if row['direction'] == 1 else "DOWN ↓"
        prices = f"{row['price_start']:.5f} → {row['price_peak']:.5f}"
        
        print(f"{row['date']:<12} {row['time']:<6} {impact:<12} {duration:<10} {direction:<10} {prices}")


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    print("\n" + "="*80)
    print("SESSION 73 - PHASE 1 : SCANNER MOUVEMENTS FORTS")
    print("="*80)
    
    # Vérifier DB existe
    if not DB_PATH.exists():
        print(f"\n❌ ERREUR : Base de données introuvable : {DB_PATH}")
        return
    
    print(f"\n✅ Base de données : {DB_PATH}")
    print(f"   Taille : {DB_PATH.stat().st_size / 1024 / 1024:.1f} MB")
    
    # Connexion
    print(f"\n🔗 Connexion DuckDB...")
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # Scanner chaque période
    all_movements = []
    
    for start_date, end_date, year in PERIODS:
        print(f"\n" + "="*60)
        print(f"📅 PÉRIODE {year} : {start_date} → {end_date}")
        print("="*60)
        
        df = scan_movements(conn, start_date, end_date, MOVEMENTS_PER_YEAR)
        
        if len(df) > 0:
            df['year'] = year
            all_movements.append(df)
            
            # Statistiques
            display_statistics(df, year)
            
            # Top mouvements
            display_top_movements(df, n=5)
    
    # Combiner résultats
    if all_movements:
        df_final = pd.concat(all_movements, ignore_index=True)
        
        print(f"\n" + "="*80)
        print(f"💾 EXPORT RÉSULTATS")
        print("="*80)
        
        # Réorganiser colonnes
        df_final = df_final[['year', 'date', 'time', 'datetime', 'price_start', 
                             'price_peak', 'impact_pips', 'duration_min', 'direction']]
        
        # Export CSV
        df_final.to_csv(OUTPUT_FILE, index=False)
        print(f"\n✅ Fichier créé : {OUTPUT_FILE}")
        print(f"   Total mouvements : {len(df_final)}")
        print(f"   Colonnes : {', '.join(df_final.columns)}")
        
        # Résumé final
        print(f"\n📊 RÉSUMÉ GLOBAL")
        print("="*60)
        print(f"   2024 : {len(df_final[df_final['year']=='2024'])} mouvements")
        print(f"   2025 : {len(df_final[df_final['year']=='2025'])} mouvements")
        print(f"   Impact moyen : {df_final['impact_pips'].abs().mean():.1f} pips")
        print(f"   Impact max : {df_final['impact_pips'].abs().max():.1f} pips")
        print(f"   Durée moyenne : {df_final['duration_min'].mean():.1f} min")
        
    else:
        print(f"\n❌ Aucun mouvement trouvé")
    
    # Fermer connexion
    conn.close()
    
    print(f"\n✅ PHASE 1 TERMINÉE")
    print("="*80)


if __name__ == "__main__":
    main()
