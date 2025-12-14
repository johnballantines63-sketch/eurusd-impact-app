#!/usr/bin/env python3
"""
SESSION 73 - PHASE 1 : SCANNER MOUVEMENTS FORTS EUR/USD (Version Dédupliquée)

Objectif : Identifier 40 mouvements forts DISTINCTS (50-150+ pips) depuis prices_1m
- 20 mouvements en 2024
- 20 mouvements en 2025
- Fenêtre de calcul : 60 minutes
- Déduplication : Garder 1 mouvement par fenêtre 2h (évite fragments même événement)

Output : movements_session73.csv
"""

import duckdb
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

# ==============================================================================
# CONFIGURATION
# ==============================================================================

# Chemin base de données
DB_PATH = Path(__file__).parent.parent.parent / "data" / "warehouse.duckdb"

# Paramètres scanner
MIN_IMPACT_PIPS = 50.0           # Seuil minimum (moyen)
LOOKBACK_MINUTES = 60            # Fenêtre glissante
DEDUP_WINDOW_HOURS = 2           # Déduplication : 2h entre mouvements
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

def scan_all_movements(conn, start_date, end_date):
    """
    Scanner TOUS les mouvements forts (pas de limite).
    La déduplication sera faite après en Python.
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
    """
    
    print(f"   Exécution query SQL (TOUS mouvements >50 pips)...")
    df = conn.execute(query).fetchdf()
    print(f"   ✅ {len(df)} mouvements bruts trouvés")
    
    return df


def deduplicate_movements(df, window_hours=2, target_count=20):
    """
    Déduplication intelligente : garder 1 mouvement par fenêtre de N heures.
    
    Algorithme :
    1. Trier par impact absolu décroissant
    2. Prendre le mouvement le plus fort
    3. Exclure tous mouvements dans fenêtre ±N heures
    4. Répéter jusqu'à avoir target_count mouvements
    
    Args:
        df: DataFrame avec colonne 'datetime' et 'impact_pips'
        window_hours: Fenêtre de déduplication (heures)
        target_count: Nombre de mouvements souhaités
        
    Returns:
        DataFrame dédupliqué
    """
    
    print(f"\n   🔄 Déduplication (fenêtre {window_hours}h)...")
    
    # Convertir datetime en timestamp pour comparaison
    df = df.copy()
    df['datetime_ts'] = pd.to_datetime(df['datetime'])
    
    # Trier par impact absolu décroissant
    df_sorted = df.sort_values('impact_pips', key=abs, ascending=False).reset_index(drop=True)
    
    selected = []
    excluded_times = set()
    
    for idx, row in df_sorted.iterrows():
        current_time = row['datetime_ts']
        
        # Vérifier si ce mouvement est trop proche d'un déjà sélectionné
        is_too_close = False
        for selected_time in excluded_times:
            time_diff = abs((current_time - selected_time).total_seconds() / 3600)
            if time_diff < window_hours:
                is_too_close = True
                break
        
        if not is_too_close:
            selected.append(row)
            excluded_times.add(current_time)
            
            # Stop si on a assez de mouvements
            if len(selected) >= target_count:
                break
    
    # Reconstruire DataFrame
    df_dedup = pd.DataFrame(selected)
    df_dedup = df_dedup.drop('datetime_ts', axis=1)
    
    print(f"   ✅ {len(df_dedup)} mouvements distincts gardés (sur {len(df)} bruts)")
    print(f"   📉 Réduction : {(1 - len(df_dedup)/len(df))*100:.1f}%")
    
    return df_dedup


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
    monthly = df.groupby(df['date'].str[:7]).size().sort_index()
    for month, count in monthly.items():
        print(f"   {month}    : {count} mouvements")
    
    print(f"\n📆 Jours uniques : {df['date'].nunique()} jours différents")


def display_top_movements(df, n=10):
    """Afficher top N mouvements."""
    
    print(f"\n🏆 TOP {n} MOUVEMENTS (Dédupliqués)")
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
    print("SESSION 73 - PHASE 1 : SCANNER MOUVEMENTS FORTS (Dédupliqué)")
    print("="*80)
    
    # Vérifier DB existe
    if not DB_PATH.exists():
        print(f"\n❌ ERREUR : Base de données introuvable : {DB_PATH}")
        return
    
    print(f"\n✅ Base de données : {DB_PATH}")
    print(f"   Taille : {DB_PATH.stat().st_size / 1024 / 1024:.1f} MB")
    
    print(f"\n⚙️  Paramètres déduplication")
    print(f"   Fenêtre : {DEDUP_WINDOW_HOURS}h (mouvements espacés)")
    print(f"   Objectif : {MOVEMENTS_PER_YEAR} mouvements par année")
    
    # Connexion
    print(f"\n🔗 Connexion DuckDB...")
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # Scanner chaque période
    all_movements = []
    
    for start_date, end_date, year in PERIODS:
        print(f"\n" + "="*60)
        print(f"📅 PÉRIODE {year} : {start_date} → {end_date}")
        print("="*60)
        
        # 1. Scanner TOUS les mouvements
        df_brut = scan_all_movements(conn, start_date, end_date)
        
        if len(df_brut) == 0:
            print(f"   ⚠️  Aucun mouvement trouvé")
            continue
        
        # 2. Dédupliquer
        df_dedup = deduplicate_movements(
            df_brut, 
            window_hours=DEDUP_WINDOW_HOURS,
            target_count=MOVEMENTS_PER_YEAR
        )
        
        if len(df_dedup) > 0:
            df_dedup['year'] = year
            all_movements.append(df_dedup)
            
            # Statistiques
            display_statistics(df_dedup, year)
            
            # Top mouvements
            display_top_movements(df_dedup, n=5)
    
    # Combiner résultats
    if all_movements:
        df_final = pd.concat(all_movements, ignore_index=True)
        
        print(f"\n" + "="*80)
        print(f"💾 EXPORT RÉSULTATS")
        print("="*80)
        
        # Réorganiser colonnes
        df_final = df_final[['year', 'date', 'time', 'datetime', 'price_start', 
                             'price_peak', 'impact_pips', 'duration_min', 'direction']]
        
        # Trier par date
        df_final = df_final.sort_values('datetime').reset_index(drop=True)
        
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
        print(f"   Jours distincts : {df_final['date'].nunique()} jours")
        print(f"   Impact moyen : {df_final['impact_pips'].abs().mean():.1f} pips")
        print(f"   Impact max : {df_final['impact_pips'].abs().max():.1f} pips")
        print(f"   Durée moyenne : {df_final['duration_min'].mean():.1f} min")
        
    else:
        print(f"\n❌ Aucun mouvement trouvé")
    
    # Fermer connexion
    conn.close()
    
    print(f"\n✅ PHASE 1 TERMINÉE (Dédupliqué)")
    print("="*80)


if __name__ == "__main__":
    main()
