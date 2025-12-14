"""
SCRIPT 1 V3 EXTENDED - SCANNER MOUVEMENTS ÉLARGI (SESSION 76)
==============================================================

OBJECTIF : Créer dataset 30-50 mouvements pour ML robuste

CRITÈRES ASSOUPLIS vs Session 75 :
- Score > 5 (vs 10) - Events connus + moyenne
- Surprise < 200% (vs 100%) - Moins strict
- Nb events ≥ 2 (vs 3) - Clusters + single HIGH
- Impact ≥ 30 pips (vs 40) - Mouvements moyens
- Top 50 par année (vs 30) - Plus de mouvements
- Années : 2023-2025 (vs 2024-2025) - Plus de données

Date : 25 octobre 2025
Session : 76
"""

import sys
import os
from pathlib import Path

fx_app_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(fx_app_path))

import duckdb
import pandas as pd
from datetime import datetime, timedelta


# ════════════════════════════════════════════════════════════════
# CONFIGURATION ÉTENDUE
# ════════════════════════════════════════════════════════════════

SCRIPT_DIR = Path(__file__).parent
DB_PATH = fx_app_path / "data" / "warehouse.duckdb"
OUTPUT_PATH = SCRIPT_DIR / "dataset_session76_extended.csv"

# ✅ CRITÈRES ASSOUPLIS SESSION 76
COUNTRIES = ['US', 'EU']  # Pays majeurs (identique S75)
SCORE_MIN = 5.0  # vs 10.0 - Events connus + moyenne
SURPRISE_MAX = 200.0  # vs 100.0 - Moins strict
NB_EVENTS_MIN = 2  # vs 3 - Clusters + single HIGH
IMPACT_MIN = 30  # vs 40 pips - Mouvements moyens
TOP_N_PER_YEAR = 50  # vs 30 - Plus de mouvements

# ✅ PÉRIODE ÉTENDUE
YEARS = [2023, 2024, 2025]  # vs [2024, 2025]

# Scanner parameters (identique S75)
WINDOW_SIZE = 60
MIN_MOVEMENT = 50
MAX_MOVEMENT = 200
DEDUP_WINDOW = 120


# ════════════════════════════════════════════════════════════════
# FONCTIONS SCANNER (IDENTIQUES S75)
# ════════════════════════════════════════════════════════════════

def scan_movements_year(conn, year):
    """Scanner mouvements significatifs pour une année"""
    print(f"\n{'='*70}")
    print(f"SCANNER ANNÉE {year}")
    print(f"{'='*70}")
    
    # Test si année existe dans DB
    test_query = f"""
    SELECT COUNT(*) as count
    FROM prices_1m
    WHERE YEAR(datetime) = {year}
    """
    
    count = conn.execute(test_query).fetchone()[0]
    
    if count == 0:
        print(f"⚠️  Aucun prix pour {year} dans DB - SKIP")
        return []
    
    print(f"✅ {count:,} prix trouvés pour {year}")
    
    query = f"""
    SELECT datetime, close
    FROM prices_1m
    WHERE YEAR(datetime) = {year}
    ORDER BY datetime ASC
    """
    
    print(f"Chargement prix {year}...")
    df_prices = conn.execute(query).fetchdf()
    print(f"✅ {len(df_prices):,} prix chargés")
    
    df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
    
    movements = []
    print(f"\nScanning mouvements (fenêtre {WINDOW_SIZE} min)...")
    
    for i in range(len(df_prices) - WINDOW_SIZE):
        if i % 100000 == 0:
            print(f"   Position {i:,}/{len(df_prices):,} ({i/len(df_prices)*100:.1f}%)", end='\r')
        
        window = df_prices.iloc[i:i+WINDOW_SIZE]
        
        start_time = window.iloc[0]['datetime']
        start_price = window.iloc[0]['close']
        
        max_price = window['close'].max()
        min_price = window['close'].min()
        
        movement_up = (max_price - start_price) * 10000
        movement_down = (start_price - min_price) * 10000
        
        if movement_up >= movement_down:
            impact = movement_up
            direction = 1
            peak_price = max_price
            peak_idx = window['close'].idxmax()
        else:
            impact = movement_down
            direction = -1
            peak_price = min_price
            peak_idx = window['close'].idxmin()
        
        if MIN_MOVEMENT <= impact <= MAX_MOVEMENT:
            peak_time = window.loc[peak_idx, 'datetime']
            duration = (peak_time - start_time).total_seconds() / 60
            
            movements.append({
                'year': year,
                'date': start_time.date(),
                'time': start_time.time(),
                'datetime': start_time,
                'impact_pips': round(impact, 1),
                'duration_min': round(duration, 1),
                'direction': direction
            })
    
    print()
    print(f"✅ {len(movements):,} mouvements bruts détectés")
    
    return movements


def deduplicate_movements(movements):
    """Dédupliquer mouvements proches temporellement"""
    print(f"\n{'='*70}")
    print("DÉDUPLICATION")
    print(f"{'='*70}")
    
    if not movements:
        return []
    
    df = pd.DataFrame(movements)
    df = df.sort_values('impact_pips', ascending=False)
    
    print(f"Mouvements bruts : {len(df)}")
    
    keep = []
    used_times = []
    
    for idx, row in df.iterrows():
        current_time = row['datetime']
        
        too_close = False
        for used_time in used_times:
            time_diff = abs((current_time - used_time).total_seconds() / 60)
            if time_diff < DEDUP_WINDOW:
                too_close = True
                break
        
        if not too_close:
            keep.append(row.to_dict())
            used_times.append(current_time)
    
    print(f"✅ Mouvements dédupliqués : {len(keep)}")
    
    return keep


def cross_with_events_extended(conn, movements):
    """
    Croisement avec events + filtres ASSOUPLIS Session 76
    
    Filtres :
    - Pays : US, EU
    - Score DB > 5 (vs 10)
    - Surprise < 200% (vs 100%)
    - Nb events ≥ 2 (vs 3)
    - Impact ≥ 30 pips (vs 40)
    """
    print(f"\n{'='*70}")
    print("CROISEMENT AVEC EVENTS + FILTRES ASSOUPLIS")
    print(f"{'='*70}")
    
    print(f"Filtres appliqués (ASSOUPLIS vs S75) :")
    print(f"   Pays : {', '.join(COUNTRIES)}")
    print(f"   Score DB : > {SCORE_MIN} (vs 10)")
    print(f"   Surprise : < {SURPRISE_MAX}% (vs 100%)")
    print(f"   Nb events : ≥ {NB_EVENTS_MIN} (vs 3)")
    print(f"   Impact : ≥ {IMPACT_MIN} pips (vs 40)")
    
    results = []
    n_filtered_score = 0
    n_filtered_surprise = 0
    n_filtered_nb_events = 0
    n_filtered_impact = 0
    
    for i, mov in enumerate(movements):
        if (i + 1) % 10 == 0:
            print(f"   Mouvement {i+1}/{len(movements)}", end='\r')
        
        movement_time = mov['datetime']
        movement_time_utc2 = movement_time + timedelta(hours=2)
        
        start_time = movement_time_utc2 - timedelta(minutes=10)
        end_time = movement_time_utc2 + timedelta(minutes=10)
        
        query = f"""
        SELECT 
            e.event_key,
            e.country,
            e.event_title,
            e.actual,
            e.previous,
            e.estimate,
            e.forecast,
            ef.family,
            ef.empirical_score
        FROM events e
        LEFT JOIN event_families ef 
            ON e.event_key = ef.event_key 
            AND e.country = ef.country
        WHERE e.ts_utc >= '{start_time}'
          AND e.ts_utc <= '{end_time}'
          AND e.country IN ({','.join([f"'{c}'" for c in COUNTRIES])})
        ORDER BY e.ts_utc
        """
        
        df_events = conn.execute(query).fetchdf()
        
        nb_events = len(df_events)
        
        if nb_events == 0:
            continue
        
        # Calculer métriques
        scores = df_events['empirical_score'].dropna()
        if len(scores) > 0:
            score_cumule = scores.sum()
            score_moyen = scores.mean()
        else:
            score_cumule = 0.0
            score_moyen = 0.0
        
        # ✅ Filtre score assouplé : > 5
        if score_moyen < SCORE_MIN:
            n_filtered_score += 1
            continue
        
        # Surprise
        surprises = []
        for _, event in df_events.iterrows():
            actual = event['actual']
            forecast = event.get('estimate') or event.get('forecast') or event.get('previous')
            
            if pd.notna(actual) and pd.notna(forecast) and forecast != 0:
                surprise = abs(actual - forecast) / abs(forecast) * 100
                surprises.append(surprise)
        
        if surprises:
            surprise_max = max(surprises)
            surprise_moyenne = sum(surprises) / len(surprises)
            surprise_cumule = sum(surprises)
        else:
            surprise_max = 0.0
            surprise_moyenne = 0.0
            surprise_cumule = 0.0
        
        # ✅ Filtres assouplis
        if surprise_max >= SURPRISE_MAX:
            n_filtered_surprise += 1
            continue
        
        if nb_events < NB_EVENTS_MIN:
            n_filtered_nb_events += 1
            continue
        
        if mov['impact_pips'] < IMPACT_MIN:
            n_filtered_impact += 1
            continue
        
        # Métriques complémentaires
        ratio_concordance = 1.0
        
        families = df_events['family'].dropna()
        if len(families) > 0:
            most_common_family = families.mode()[0] if len(families.mode()) > 0 else families.iloc[0]
            coherence_famille = (families == most_common_family).sum() / len(families)
        else:
            coherence_famille = 0.0
        
        has_high_importance = (score_moyen >= 10.0)  # Heuristique
        
        events_list = ' | '.join([f"{row['country']}:{row['event_title']}" for _, row in df_events.iterrows()])
        families_list = ' | '.join(families.unique())
        
        results.append({
            **mov,
            'nb_events': nb_events,
            'score_cumule': score_cumule,
            'score_moyen': score_moyen,
            'surprise_max': surprise_max,
            'surprise_moyenne': surprise_moyenne,
            'surprise_cumule': surprise_cumule,
            'ratio_concordance': ratio_concordance,
            'coherence_famille': coherence_famille,
            'has_high_importance': has_high_importance,
            'events_list': events_list,
            'families_list': families_list
        })
    
    print()
    print(f"\n✅ Mouvements QUALITÉ : {len(results)}")
    print(f"\nFiltrage détaillé :")
    print(f"   Mouvements input : {len(movements)}")
    print(f"   ❌ Filtrés score < {SCORE_MIN} : {n_filtered_score}")
    print(f"   ❌ Filtrés surprise ≥ {SURPRISE_MAX}% : {n_filtered_surprise}")
    print(f"   ❌ Filtrés nb_events < {NB_EVENTS_MIN} : {n_filtered_nb_events}")
    print(f"   ❌ Filtrés impact < {IMPACT_MIN} pips : {n_filtered_impact}")
    print(f"   ✅ QUALITÉ FINALE : {len(results)}")
    
    if len(results) > 0:
        df_results = pd.DataFrame(results)
        print(f"\n📊 Statistiques dataset étendu :")
        print(f"   Nb mouvements : {len(df_results)}")
        print(f"   Nb jours distincts : {df_results['date'].nunique()}")
        print(f"   Impact moyen : {df_results['impact_pips'].mean():.1f} pips")
        print(f"   Nb events moyen : {df_results['nb_events'].mean():.1f}")
        print(f"   Score moyen : {df_results['score_moyen'].mean():.1f}")
        print(f"   Surprise max moyenne : {df_results['surprise_max'].mean():.1f}%")
    
    return results


def main():
    """Point d'entrée principal"""
    print(f"\n{'='*70}")
    print("SCANNER V3 ÉTENDU - SESSION 76")
    print(f"{'='*70}")
    print(f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    print("OBJECTIF : Dataset 30-50 mouvements pour ML robuste")
    print()
    print("CRITÈRES ASSOUPLIS vs Session 75 :")
    print(f"   Score > {SCORE_MIN} (vs 10)")
    print(f"   Surprise < {SURPRISE_MAX}% (vs 100%)")
    print(f"   Nb events ≥ {NB_EVENTS_MIN} (vs 3)")
    print(f"   Impact ≥ {IMPACT_MIN} pips (vs 40)")
    print(f"   Top {TOP_N_PER_YEAR} par année (vs 30)")
    print(f"   Années : {YEARS} (vs [2024, 2025])")
    print()
    
    if not DB_PATH.exists():
        print(f"❌ Base de données non trouvée : {DB_PATH}")
        return 1
    
    print(f"✅ Base de données : {DB_PATH}")
    
    SCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    try:
        # Test période disponible
        print(f"\n{'='*70}")
        print("TEST PÉRIODE DISPONIBLE")
        print(f"{'='*70}")
        
        date_range_query = "SELECT MIN(datetime) as min_date, MAX(datetime) as max_date FROM prices_1m"
        date_range = conn.execute(date_range_query).fetchone()
        
        print(f"Période disponible dans DB :")
        print(f"   Min : {date_range[0]}")
        print(f"   Max : {date_range[1]}")
        
        all_movements = []
        
        for year in YEARS:
            movements_year = scan_movements_year(conn, year)
            all_movements.extend(movements_year)
        
        print(f"\n{'='*70}")
        print(f"TOTAL MOUVEMENTS BRUTS : {len(all_movements)}")
        print(f"{'='*70}")
        
        if len(all_movements) == 0:
            print(f"⚠️  AUCUN MOUVEMENT DÉTECTÉ - Vérifier période disponible")
            return 0
        
        movements_dedup = deduplicate_movements(all_movements)
        
        df_dedup = pd.DataFrame(movements_dedup)
        
        print(f"\n{'='*70}")
        print(f"SÉLECTION TOP {TOP_N_PER_YEAR} PAR ANNÉE")
        print(f"{'='*70}")
        
        movements_top = []
        for year in YEARS:
            df_year = df_dedup[df_dedup['year'] == year]
            if len(df_year) > 0:
                df_year_top = df_year.nlargest(min(TOP_N_PER_YEAR, len(df_year)), 'impact_pips')
                movements_top.extend(df_year_top.to_dict('records'))
                print(f"Année {year} : {len(df_year_top)} mouvements gardés")
            else:
                print(f"Année {year} : 0 mouvements (pas de données)")
        
        print(f"✅ Total : {len(movements_top)} mouvements")
        
        movements_filtered = cross_with_events_extended(conn, movements_top)
        
        if movements_filtered:
            df_final = pd.DataFrame(movements_filtered)
            
            cols_order = [
                'year', 'date', 'time', 'datetime',
                'impact_pips', 'duration_min', 'direction',
                'nb_events', 'score_cumule', 'score_moyen',
                'surprise_max', 'surprise_moyenne', 'surprise_cumule',
                'ratio_concordance', 'coherence_famille', 'has_high_importance',
                'events_list', 'families_list'
            ]
            
            df_final = df_final[cols_order]
            df_final.to_csv(OUTPUT_PATH, index=False)
            
            print(f"\n{'='*70}")
            print("EXPORT RÉSULTATS")
            print(f"{'='*70}")
            print(f"✅ Fichier créé : {OUTPUT_PATH}")
            print(f"   Lignes : {len(df_final)}")
            
            print(f"\n📊 Distribution par année :")
            for year in YEARS:
                n = (df_final['year'] == year).sum()
                if n > 0:
                    print(f"   {year} : {n} mouvements")
            
            print(f"\n✅ SCANNER V3 ÉTENDU TERMINÉ AVEC SUCCÈS")
            print(f"\n📊 RÉSUMÉ FINAL :")
            print(f"   Dataset étendu : {len(df_final)} mouvements")
            print(f"   Jours distincts : {df_final['date'].nunique()}")
            print(f"   Impact moyen : {df_final['impact_pips'].mean():.1f} pips")
            print(f"   Nb events moyen : {df_final['nb_events'].mean():.1f}")
            
            # Vérification objectif
            if len(df_final) >= 30:
                print(f"\n✅ OBJECTIF ATTEINT : {len(df_final)} mouvements (≥30)")
            else:
                print(f"\n⚠️  OBJECTIF PARTIEL : {len(df_final)} mouvements (<30)")
            
        else:
            print(f"\n⚠️  AUCUN MOUVEMENT QUALITÉ TROUVÉ")
            print(f"   Essayer d'assouplir davantage les critères")
    
    except Exception as e:
        print(f"\n❌ ERREUR : {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        conn.close()
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
