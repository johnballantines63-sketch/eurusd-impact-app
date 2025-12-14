"""
RECALCUL SCORES EMPIRIQUES PAR TRANCHES (ÉVITE DISQUE PLEIN)

Stratégie : Traiter par semestres 2020-2025
Avantage : Requêtes SQL petites → pas de saturation disque

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
Session : 124 - Recalcul scientifique par tranches
"""

import duckdb
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
from tqdm import tqdm

DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'warehouse.duckdb'
OUTPUT_DIR = Path(__file__).parent / 'validation_results'

def calculate_empirical_score(avg_movement, p80_movement, sample_size):
    """Calculer score empirique normalisé 0-100"""
    base_score = (avg_movement * 0.5 + p80_movement * 0.5)
    
    if sample_size >= 20:
        robustness = 1.0
    elif sample_size >= 10:
        robustness = 0.9
    elif sample_size >= 5:
        robustness = 0.8
    else:
        robustness = 0.7
    
    score = base_score * robustness
    return min(100.0, (score / 100.0) * 100.0)


def recalculate_by_periods():
    """Recalcul par semestres pour éviter saturation disque"""
    
    print("=" * 80)
    print("RECALCUL SCORES EMPIRIQUES PAR SEMESTRES")
    print("=" * 80)
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=False)
    
    # ========================================================================
    # 1. DÉFINIR PÉRIODES (SEMESTRES)
    # ========================================================================
    
    periods = [
        ("2020-01-01", "2020-06-30", "2020 S1"),
        ("2020-07-01", "2020-12-31", "2020 S2"),
        ("2021-01-01", "2021-06-30", "2021 S1"),
        ("2021-07-01", "2021-12-31", "2021 S2"),
        ("2022-01-01", "2022-06-30", "2022 S1"),
        ("2022-07-01", "2022-12-31", "2022 S2"),
        ("2023-01-01", "2023-06-30", "2023 S1"),
        ("2023-07-01", "2023-12-31", "2023 S2"),
        ("2024-01-01", "2024-06-30", "2024 S1"),
        ("2024-07-01", "2024-12-31", "2024 S2"),
        ("2025-01-01", "2025-06-30", "2025 S1"),
        ("2025-07-01", "2025-12-31", "2025 S2"),
    ]
    
    print(f"Périodes : {len(periods)} semestres (2020-2025)")
    print()
    
    # ========================================================================
    # 2. CALCULER IMPACTS PAR PÉRIODE
    # ========================================================================
    
    all_results = []
    
    for start_date, end_date, label in tqdm(periods, desc="Semestres"):
        
        print(f"\n{'='*80}")
        print(f"📊 Traitement {label} ({start_date} → {end_date})")
        print(f"{'='*80}")
        
        # Requête SQL optimisée PAR PÉRIODE
        query_period = f"""
        WITH event_baseline AS (
            SELECT 
                e.event_id,
                e.event_name,
                e.country,
                e.datetime_utc as event_time,
                -- Prix baseline (close précédent, en UTC)
                (SELECT p.close 
                 FROM prices_bern p 
                 WHERE p.datetime < TIMESTAMP '{start_date}' + (e.datetime_utc - TIMESTAMP '{start_date}')
                 ORDER BY p.datetime DESC 
                 LIMIT 1) as baseline_price
            FROM economic_events e
            WHERE e.datetime_utc >= TIMESTAMP '{start_date}'
              AND e.datetime_utc <= TIMESTAMP '{end_date}'
              AND e.country IN ('usd', 'eur', 'gbp', 'jpy', 'cad', 'aud', 'chf')
        ),
        event_impacts AS (
            SELECT 
                eb.event_name,
                eb.country,
                eb.event_time,
                eb.baseline_price,
                -- Maximum movement post-événement (60 min)
                GREATEST(
                    MAX(ABS((p.high - eb.baseline_price) * 10000)),
                    MAX(ABS((eb.baseline_price - p.low) * 10000))
                ) as max_movement_pips
            FROM event_baseline eb
            JOIN prices_bern p 
                ON p.datetime >= eb.event_time
                AND p.datetime <= eb.event_time + INTERVAL '60 minutes'
            WHERE eb.baseline_price IS NOT NULL
            GROUP BY eb.event_name, eb.country, eb.event_time, eb.baseline_price
        )
        SELECT 
            event_name,
            country,
            AVG(max_movement_pips) as avg_movement_pips,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY max_movement_pips) as median_movement_pips,
            PERCENTILE_CONT(0.8) WITHIN GROUP (ORDER BY max_movement_pips) as p80_movement_pips,
            COUNT(*) as sample_size
        FROM event_impacts
        WHERE max_movement_pips IS NOT NULL
          AND max_movement_pips > 0
        GROUP BY event_name, country
        HAVING COUNT(*) >= 2
        """
        
        try:
            # Exécuter requête période
            period_results = conn.execute(query_period).df()
            
            if len(period_results) > 0:
                print(f"✅ {len(period_results)} familles analysées")
                all_results.append(period_results)
            else:
                print(f"⚠️  Aucun résultat (période peut-être hors range données)")
            
        except Exception as e:
            if "No space left on device" in str(e):
                print(f"❌ Disque plein sur {label}")
                print(f"   → Réduire période ou libérer espace")
                break
            else:
                print(f"❌ Erreur: {e}")
                continue
    
    print()
    
    if len(all_results) == 0:
        print("❌ Aucun résultat obtenu")
        conn.close()
        return
    
    # ========================================================================
    # 3. AGRÉGER RÉSULTATS TOUTES PÉRIODES
    # ========================================================================
    
    print("=" * 80)
    print("AGRÉGATION RÉSULTATS")
    print("=" * 80)
    print()
    
    # Concaténer tous DataFrames
    df_all = pd.concat(all_results, ignore_index=True)
    
    print(f"Total lignes brutes : {len(df_all)}")
    print()
    
    # Agréger par event_name + country (moyenne pondérée par sample_size)
    agg_results = df_all.groupby(['event_name', 'country']).apply(
        lambda x: pd.Series({
            'avg_movement_pips': np.average(x['avg_movement_pips'], weights=x['sample_size']),
            'median_movement_pips': np.average(x['median_movement_pips'], weights=x['sample_size']),
            'p80_movement_pips': np.average(x['p80_movement_pips'], weights=x['sample_size']),
            'sample_size': x['sample_size'].sum()
        })
    ).reset_index()
    
    print(f"Familles uniques : {len(agg_results)}")
    print()
    
    # Calculer empirical_score
    agg_results['empirical_score'] = agg_results.apply(
        lambda row: calculate_empirical_score(
            row['avg_movement_pips'],
            row['p80_movement_pips'],
            row['sample_size']
        ),
        axis=1
    )
    
    # ========================================================================
    # 4. SAUVEGARDER CSV
    # ========================================================================
    
    csv_file = OUTPUT_DIR / 'event_families_eodhd_empirical.csv'
    agg_results.to_csv(csv_file, index=False)
    
    print(f"✅ Sauvegardé : {csv_file}")
    print(f"   {len(agg_results)} familles")
    print()
    
    # ========================================================================
    # 5. STATISTIQUES
    # ========================================================================
    
    print("DISTRIBUTION SCORES :")
    print("-" * 80)
    print()
    
    high = len(agg_results[agg_results['empirical_score'] >= 40])
    med = len(agg_results[(agg_results['empirical_score'] >= 20) & (agg_results['empirical_score'] < 40)])
    low = len(agg_results[agg_results['empirical_score'] < 20])
    
    print(f"   HIGH (>=40)  : {high:3d} ({high/len(agg_results)*100:.1f}%)")
    print(f"   MEDIUM (>=20): {med:3d} ({med/len(agg_results)*100:.1f}%)")
    print(f"   LOW (<20)    : {low:3d} ({low/len(agg_results)*100:.1f}%)")
    print()
    
    # TOP 20
    print("TOP 20 ÉVÉNEMENTS :")
    print("-" * 80)
    print()
    
    top20 = agg_results.nlargest(20, 'empirical_score')[
        ['event_name', 'country', 'empirical_score', 'avg_movement_pips', 'sample_size']
    ]
    print(top20.to_string(index=False))
    print()
    
    # ========================================================================
    # 6. CRÉER TABLE DB (OPTIONNEL)
    # ========================================================================
    
    print("CRÉATION TABLE DB (optionnel) :")
    print("-" * 80)
    print()
    
    user_input = input("Créer table event_families_eodhd_empirical dans DB ? [O/n] : ")
    
    if user_input.lower() in ['', 'o', 'oui', 'y', 'yes']:
        try:
            conn.execute("DROP TABLE IF EXISTS event_families_eodhd_empirical")
            conn.execute("""
            CREATE TABLE event_families_eodhd_empirical AS 
            SELECT * FROM agg_results
            """)
            print("✅ Table créée")
        except Exception as e:
            print(f"❌ Erreur création table: {e}")
            print("   → CSV disponible, utiliser reclassify_from_csv.py")
    else:
        print("Table non créée (CSV disponible)")
    
    print()
    
    conn.close()
    
    print("=" * 80)
    print("✅ RECALCUL TERMINÉ")
    print("=" * 80)
    print()
    print("Fichier créé : event_families_eodhd_empirical.csv")
    print()
    print("Prochaines étapes :")
    print("   python reclassify_from_empirical_csv.py")
    print("   python validate_cluster_sept11.py")
    print("   python validate_formula_s115_complete.py")
    print()


if __name__ == '__main__':
    recalculate_by_periods()
