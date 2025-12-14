"""
SCRIPT 1 - SCANNER MOUVEMENTS V2 FILTRÉ (SESSION 75)
=====================================================

Objectif : Scanner mouvements QUALITÉ avec critères stricts
         
DIFFÉRENCES vs Session 73 :
- Pays : US + EU uniquement (80% volume trading)
- Importance : HIGH only (importance_n = 3)
- Surprise : < 100% (cas normaux, pas extrêmes)
- Nb events : ≥ 3 (vrais clusters)
- Impact : ≥ 40 pips (significatif)

RÉSULTAT ATTENDU :
- 40-50 mouvements de qualité
- 30+ dates différentes
- Events connus avec scores DB
- Surprises normales (<100%)
- Clusters significatifs (3-15 events)

Date : 25 octobre 2025
Session : 75
"""

import sys
import os
from pathlib import Path

# Ajouter le chemin vers fx_impact_app pour imports
fx_app_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(fx_app_path))

import duckdb
import pandas as pd
from datetime import datetime, timedelta


# ════════════════════════════════════════════════════════════════
# CONFIGURATION
# ════════════════════════════════════════════════════════════════

# Chemins
SCRIPT_DIR = Path(__file__).parent
DB_PATH = fx_app_path / "data" / "warehouse.duckdb"
OUTPUT_PATH = SCRIPT_DIR / "movements_session75_filtered.csv"

# Critères filtrage STRICTS
COUNTRIES = ['US', 'EU']  # Pays majeurs uniquement
IMPORTANCE_MIN = 3  # HIGH importance only
SURPRISE_MAX = 100.0  # % - Surprises réalistes
NB_EVENTS_MIN = 3  # Vrais clusters
IMPACT_MIN = 40  # pips - Mouvements significatifs

# Scanner parameters
WINDOW_SIZE = 60  # minutes
MIN_MOVEMENT = 50  # pips (détection initiale)
MAX_MOVEMENT = 200  # pips (plafond)
DEDUP_WINDOW = 120  # minutes entre mouvements
TOP_N_PER_YEAR = 30  # Par année (2024, 2025)

# Années à scanner
YEARS = [2024, 2025]


# ════════════════════════════════════════════════════════════════
# FONCTIONS SCANNER
# ════════════════════════════════════════════════════════════════

def scan_movements_year(conn, year):
    """
    Scanner mouvements pour une année
    
    Args:
        conn: Connexion DuckDB
        year: Année à scanner
        
    Returns:
        list: Mouvements détectés
    """
    print(f"\n{'='*70}")
    print(f"SCANNER ANNÉE {year}")
    print(f"{'='*70}")
    
    # Query prix
    query = f"""
    SELECT 
        datetime,
        close
    FROM prices_1m
    WHERE YEAR(datetime) = {year}
    ORDER BY datetime ASC
    """
    
    print(f"Chargement prix {year}...")
    df_prices = conn.execute(query).fetchdf()
    print(f"✅ {len(df_prices):,} prix chargés")
    
    # Convertir datetime
    df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
    
    # Scanner avec fenêtre glissante
    movements = []
    
    print(f"\nScanning mouvements (fenêtre {WINDOW_SIZE} min)...")
    
    for i in range(len(df_prices) - WINDOW_SIZE):
        if i % 100000 == 0:
            print(f"   Position {i:,}/{len(df_prices):,} ({i/len(df_prices)*100:.1f}%)", end='\r')
        
        window = df_prices.iloc[i:i+WINDOW_SIZE]
        
        start_time = window.iloc[0]['datetime']
        start_price = window.iloc[0]['close']
        
        # Trouver max et min dans fenêtre
        max_price = window['close'].max()
        min_price = window['close'].min()
        
        # Calculer mouvement absolu
        movement_up = (max_price - start_price) * 10000  # pips
        movement_down = (start_price - min_price) * 10000  # pips
        
        # Garder mouvement le plus fort
        if movement_up >= movement_down:
            impact = movement_up
            direction = 1  # UP
            peak_price = max_price
            peak_idx = window['close'].idxmax()
        else:
            impact = movement_down
            direction = -1  # DOWN
            peak_price = min_price
            peak_idx = window['close'].idxmin()
        
        # Filtrer par seuil
        if MIN_MOVEMENT <= impact <= MAX_MOVEMENT:
            peak_time = window.loc[peak_idx, 'datetime']
            duration = (peak_time - start_time).total_seconds() / 60  # minutes
            
            movements.append({
                'year': year,
                'date': start_time.date(),
                'time': start_time.time(),
                'datetime': start_time,
                'impact_pips': round(impact, 1),
                'duration_min': round(duration, 1),
                'direction': direction,
                'peak_time': peak_time,
                'start_price': start_price,
                'peak_price': peak_price
            })
    
    print()  # Nouvelle ligne après progress
    print(f"✅ {len(movements):,} mouvements bruts détectés")
    
    return movements


def deduplicate_movements(movements):
    """
    Déduplication : Garder meilleurs mouvements espacés
    
    Args:
        movements: Liste mouvements bruts
        
    Returns:
        list: Mouvements dédupliqués
    """
    print(f"\n{'='*70}")
    print("DÉDUPLICATION")
    print(f"{'='*70}")
    
    if not movements:
        return []
    
    # Convertir en DataFrame
    df = pd.DataFrame(movements)
    
    # Trier par impact décroissant
    df = df.sort_values('impact_pips', ascending=False)
    
    print(f"Mouvements bruts : {len(df)}")
    print(f"Fenêtre déduplication : {DEDUP_WINDOW} minutes")
    
    # Déduplication
    keep = []
    used_times = []
    
    for idx, row in df.iterrows():
        current_time = row['datetime']
        
        # Vérifier si trop proche d'un mouvement déjà gardé
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
    print(f"   Réduction : {(1 - len(keep)/len(df))*100:.1f}%")
    
    # Statistiques
    df_keep = pd.DataFrame(keep)
    print(f"\nStatistiques mouvements gardés :")
    print(f"   Impact moyen : {df_keep['impact_pips'].mean():.1f} pips")
    print(f"   Impact min : {df_keep['impact_pips'].min():.1f} pips")
    print(f"   Impact max : {df_keep['impact_pips'].max():.1f} pips")
    
    return keep


def cross_with_events_filtered(conn, movements):
    """
    Croiser mouvements avec events + FILTRES QUALITÉ
    
    Filtres appliqués :
    - Pays : US, EU uniquement
    - Importance : HIGH (3) only
    - Surprise : < 100%
    - Nb events : ≥ 3
    
    Args:
        conn: Connexion DuckDB
        movements: Liste mouvements
        
    Returns:
        list: Mouvements filtrés avec métriques events
    """
    print(f"\n{'='*70}")
    print("CROISEMENT AVEC EVENTS + FILTRES QUALITÉ")
    print(f"{'='*70}")
    
    print(f"Filtres appliqués :")
    print(f"   Pays : {', '.join(COUNTRIES)}")
    print(f"   Importance : ≥ {IMPORTANCE_MIN}")
    print(f"   Surprise : < {SURPRISE_MAX}%")
    print(f"   Nb events : ≥ {NB_EVENTS_MIN}")
    print(f"   Impact : ≥ {IMPACT_MIN} pips")
    
    results = []
    n_with_events = 0
    n_filtered_country = 0
    n_filtered_importance = 0
    n_filtered_surprise = 0
    n_filtered_nb_events = 0
    n_filtered_impact = 0
    
    for i, mov in enumerate(movements):
        if (i + 1) % 10 == 0:
            print(f"   Mouvement {i+1}/{len(movements)}", end='\r')
        
        movement_time = mov['datetime']
        
        # Correction timezone : Events en UTC+2 (Berne), Prices en UTC
        movement_time_utc2 = movement_time + timedelta(hours=2)
        
        # Fenêtre ±10 minutes
        start_time = movement_time_utc2 - timedelta(minutes=10)
        end_time = movement_time_utc2 + timedelta(minutes=10)
        
        # Query events avec filtres
        query = f"""
        SELECT 
            e.event_key,
            e.country,
            e.event_title,
            e.importance_n,
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
        
        # Filtre #1 : Au moins 1 event trouvé
        if nb_events == 0:
            continue
        
        # Filtre #2 : Importance HIGH uniquement
        df_events_high = df_events[df_events['importance_n'] >= IMPORTANCE_MIN]
        if len(df_events_high) == 0:
            n_filtered_importance += 1
            continue
        
        # Utiliser seulement events HIGH
        df_events = df_events_high
        nb_events = len(df_events)
        
        # Calculer métriques
        # Score
        scores = df_events['empirical_score'].dropna()
        if len(scores) > 0:
            score_cumule = scores.sum()
            score_moyen = scores.mean()
        else:
            score_cumule = 0.0
            score_moyen = 0.0
        
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
        
        # Filtre #3 : Surprise < 100%
        if surprise_max >= SURPRISE_MAX:
            n_filtered_surprise += 1
            continue
        
        # Filtre #4 : Nb events ≥ 3
        if nb_events < NB_EVENTS_MIN:
            n_filtered_nb_events += 1
            continue
        
        # Filtre #5 : Impact ≥ 40 pips
        if mov['impact_pips'] < IMPACT_MIN:
            n_filtered_impact += 1
            continue
        
        # Ratio concordance (direction)
        # Note : Pas de direction dans events pour simplifier
        ratio_concordance = 1.0  # Assumé
        
        # Cohérence famille
        families = df_events['family'].dropna()
        if len(families) > 0:
            most_common_family = families.mode()[0] if len(families.mode()) > 0 else families.iloc[0]
            coherence_famille = (families == most_common_family).sum() / len(families)
        else:
            coherence_famille = 0.0
        
        # Has HIGH importance (déjà filtré, donc True)
        has_high_importance = True
        
        # Listes events et familles
        events_list = ' | '.join([f"{row['country']}:{row['event_title']}" for _, row in df_events.iterrows()])
        families_list = ' | '.join(families.unique())
        
        # Ajouter résultat
        results.append({
            **mov,  # Toutes les colonnes mouvement
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
        
        n_with_events += 1
    
    print()  # Nouvelle ligne
    print(f"\n✅ Mouvements QUALITÉ : {len(results)}")
    print(f"\nFiltrage détaillé :")
    print(f"   Mouvements input : {len(movements)}")
    print(f"   Avec events (US/EU) : {n_with_events + n_filtered_importance + n_filtered_surprise + n_filtered_nb_events + n_filtered_impact}")
    print(f"   ❌ Filtrés importance < {IMPORTANCE_MIN} : {n_filtered_importance}")
    print(f"   ❌ Filtrés surprise ≥ {SURPRISE_MAX}% : {n_filtered_surprise}")
    print(f"   ❌ Filtrés nb_events < {NB_EVENTS_MIN} : {n_filtered_nb_events}")
    print(f"   ❌ Filtrés impact < {IMPACT_MIN} pips : {n_filtered_impact}")
    print(f"   ✅ QUALITÉ FINALE : {len(results)}")
    
    if len(results) > 0:
        df_results = pd.DataFrame(results)
        print(f"\n📊 Statistiques dataset qualité :")
        print(f"   Nb mouvements : {len(df_results)}")
        print(f"   Nb jours distincts : {df_results['date'].nunique()}")
        print(f"   Impact moyen : {df_results['impact_pips'].mean():.1f} pips")
        print(f"   Nb events moyen : {df_results['nb_events'].mean():.1f}")
        print(f"   Score moyen : {df_results['score_moyen'].mean():.1f}")
        print(f"   Surprise max moyenne : {df_results['surprise_max'].mean():.1f}%")
    
    return results


# ════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════

def main():
    """
    Fonction principale
    """
    print(f"\n{'='*70}")
    print("SCANNER V2 FILTRÉ - SESSION 75")
    print(f"{'='*70}")
    print(f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Vérifier DB
    if not DB_PATH.exists():
        print(f"❌ Base de données non trouvée : {DB_PATH}")
        return 1
    
    print(f"✅ Base de données : {DB_PATH}")
    print(f"   Taille : {DB_PATH.stat().st_size / (1024*1024):.1f} MB")
    
    # Créer répertoire output si nécessaire
    SCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Connexion DB
    print("\nConnexion à la base de données...")
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    print("✅ Connecté")
    
    try:
        # Scanner mouvements par année
        all_movements = []
        
        for year in YEARS:
            movements_year = scan_movements_year(conn, year)
            all_movements.extend(movements_year)
        
        print(f"\n{'='*70}")
        print(f"TOTAL MOUVEMENTS BRUTS : {len(all_movements)}")
        print(f"{'='*70}")
        
        # Déduplication
        movements_dedup = deduplicate_movements(all_movements)
        
        # Limiter top N par année
        df_dedup = pd.DataFrame(movements_dedup)
        
        print(f"\n{'='*70}")
        print(f"SÉLECTION TOP {TOP_N_PER_YEAR} PAR ANNÉE")
        print(f"{'='*70}")
        
        movements_top = []
        for year in YEARS:
            df_year = df_dedup[df_dedup['year'] == year]
            df_year_top = df_year.nlargest(TOP_N_PER_YEAR, 'impact_pips')
            movements_top.extend(df_year_top.to_dict('records'))
            print(f"Année {year} : {len(df_year_top)} mouvements gardés")
        
        print(f"✅ Total : {len(movements_top)} mouvements")
        
        # Croiser avec events + Filtres qualité
        movements_filtered = cross_with_events_filtered(conn, movements_top)
        
        # Export CSV
        if movements_filtered:
            df_final = pd.DataFrame(movements_filtered)
            
            # Réorganiser colonnes
            cols_order = [
                'year', 'date', 'time', 'datetime',
                'impact_pips', 'duration_min', 'direction',
                'nb_events', 'score_cumule', 'score_moyen',
                'surprise_max', 'surprise_moyenne', 'surprise_cumule',
                'ratio_concordance', 'coherence_famille', 'has_high_importance',
                'events_list', 'families_list'
            ]
            
            df_final = df_final[cols_order]
            
            # Sauvegarder
            df_final.to_csv(OUTPUT_PATH, index=False)
            
            print(f"\n{'='*70}")
            print("EXPORT RÉSULTATS")
            print(f"{'='*70}")
            print(f"✅ Fichier créé : {OUTPUT_PATH}")
            print(f"   Lignes : {len(df_final)}")
            print(f"   Colonnes : {len(df_final.columns)}")
            
            # Distribution par année
            print(f"\n📊 Distribution par année :")
            for year in YEARS:
                n = (df_final['year'] == year).sum()
                print(f"   {year} : {n} mouvements")
            
            print(f"\n✅ SCANNER V2 TERMINÉ AVEC SUCCÈS")
            print(f"\n📊 RÉSUMÉ FINAL :")
            print(f"   Dataset qualité : {len(df_final)} mouvements")
            print(f"   Jours distincts : {df_final['date'].nunique()}")
            print(f"   Couverture : {len(df_final)/len(movements_top)*100:.1f}%")
            
        else:
            print(f"\n⚠️  AUCUN MOUVEMENT QUALITÉ TROUVÉ")
            print("Critères trop stricts ou données insuffisantes")
    
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
