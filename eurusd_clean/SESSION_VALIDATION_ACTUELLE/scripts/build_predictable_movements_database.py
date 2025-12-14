#!/usr/bin/env python3
"""
Construction Base de Données des Mouvements Prédictibles

Objectif :
1. Filtrer les mouvements avec événements (97.6% - prédictibles)
2. Pour chaque mouvement, identifier le cluster d'événements
3. Identifier le noyau dur (core events) avec support >= 80%
4. Calculer toutes les métriques : scores, surprises, tendances, etc.
5. Sauvegarder dans une base de données structurée pour utilisation dans les calculs

Date : 2025-01-XX
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import duckdb
import pytz
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict

# Ajouter le répertoire racine au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src' / 'core'))

# Imports des modules core
try:
    from src.core.formulas_validated import (
        calculate_adjusted_empirical_score,
        calculate_impact_d
    )
    from src.core.event_loader import load_high_impact_events
except ImportError:
    # Fallback si imports échouent
    print("⚠️ Imports core échoués, utilisation de fonctions locales")

# Essayer plusieurs chemins possibles pour la DB
DB_PATHS = [
    Path(__file__).parent.parent.parent / 'data' / 'warehouse.duckdb',
    Path(__file__).parent.parent.parent / 'warehouse.duckdb',
]

DB_PATH = None
for db_path in DB_PATHS:
    if db_path.exists():
        DB_PATH = db_path
        break

if DB_PATH is None:
    raise FileNotFoundError("Aucune base de données trouvée")

TZ_BERN = pytz.timezone('Europe/Zurich')
TZ_UTC = pytz.timezone('UTC')

# Fenêtre de matching : ±60 minutes autour du début du mouvement
MATCHING_WINDOW_MINUTES = 60

# Seuil d'importance minimum pour les événements
MIN_IMPORTANCE = 3  # HIGH importance seulement

# Support minimum pour noyau dur (80%)
CORE_EVENTS_SUPPORT_THRESHOLD = 0.80


def normalize_event_key(event_key: str) -> str:
    """
    Normalise une clé d'événement pour comparaison
    
    Exemples:
        "Non-Farm Payrolls" → "non farm payrolls"
        "CPI (MoM)" → "cpi mom"
    """
    if not event_key:
        return ""
    
    # Convertir en minuscules
    normalized = event_key.lower()
    
    # Supprimer caractères spéciaux
    normalized = normalized.replace('-', ' ')
    normalized = normalized.replace('(', '')
    normalized = normalized.replace(')', '')
    normalized = normalized.replace(',', '')
    
    # Supprimer espaces multiples
    normalized = ' '.join(normalized.split())
    
    return normalized


def calculate_surprise_pct(actual: float, estimate: float = None, 
                          forecast: float = None, previous: float = None) -> float:
    """
    Calcule le pourcentage de surprise d'un événement
    
    Formule : |actual - reference| / |reference| × 100
    Priorité : estimate > forecast > previous
    """
    if pd.isna(actual) or actual is None:
        return 0.0
    
    # Priorité : estimate > forecast > previous
    reference = None
    if pd.notna(estimate) and estimate != 0:
        reference = estimate
    elif pd.notna(forecast) and forecast != 0:
        reference = forecast
    elif pd.notna(previous) and previous != 0:
        reference = previous
    
    if reference is None or reference == 0:
        return 0.0
    
    surprise_pct = abs((actual - reference) / abs(reference)) * 100
    return surprise_pct


def calculate_adjusted_empirical_score_local(
    base_empirical_score: float,
    surprise_pct: float
) -> float:
    """
    Ajuste le score empirique selon la surprise (version locale)
    
    Formule validée Session 55
    """
    if pd.isna(base_empirical_score) or base_empirical_score <= 0:
        return 0.0
    
    if surprise_pct < 5.0:
        factor = 1.0
    elif surprise_pct < 15.0:
        # Interpolation linéaire 1.0 → 1.5
        factor = 1.0 + (surprise_pct - 5.0) / 10.0 * 0.5
    elif surprise_pct < 30.0:
        # Interpolation linéaire 1.5 → 1.9
        factor = 1.5 + (surprise_pct - 15.0) / 15.0 * 0.4
    else:
        factor = 1.9
    
    return base_empirical_score * factor


def find_events_for_movement(
    conn: duckdb.DuckDBPyConnection,
    movement_start_time: pd.Timestamp,
    window_minutes: int = MATCHING_WINDOW_MINUTES
) -> pd.DataFrame:
    """
    Trouve tous les événements dans une fenêtre autour du début du mouvement
    """
    # Définir fenêtre
    window_start = movement_start_time - timedelta(minutes=window_minutes)
    window_end = movement_start_time + timedelta(minutes=window_minutes)
    
    # Convertir en UTC pour requête DB
    if movement_start_time.tzinfo is None:
        movement_start_time = TZ_BERN.localize(movement_start_time)
    
    window_start_utc = window_start.astimezone(TZ_UTC) if window_start.tzinfo else TZ_BERN.localize(window_start).astimezone(TZ_UTC)
    window_end_utc = window_end.astimezone(TZ_UTC) if window_end.tzinfo else TZ_BERN.localize(window_end).astimezone(TZ_UTC)
    
    # Requête événements avec scores empiriques
    query = """
    SELECT 
        e.ts_utc,
        e.event_key,
        e.event_title,
        e.country,
        e.importance_n,
        e.actual,
        e.estimate,
        e.forecast,
        e.previous,
        ef.empirical_score,
        ef.latency_median,
        ef.family
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE e.ts_utc >= ?
      AND e.ts_utc <= ?
      AND e.importance_n <= ?
    ORDER BY e.ts_utc
    """
    
    try:
        df_events = conn.execute(
            query, 
            [window_start_utc, window_end_utc, MIN_IMPORTANCE]
        ).df()
        
        # Enrichir avec surprises et scores ajustés
        if not df_events.empty:
            df_events['surprise_pct'] = df_events.apply(
                lambda row: calculate_surprise_pct(
                    row['actual'], 
                    row['estimate'], 
                    row['forecast'], 
                    row['previous']
                ), 
                axis=1
            )
            
            df_events['empirical_score_adjusted'] = df_events.apply(
                lambda row: calculate_adjusted_empirical_score_local(
                    row['empirical_score'] if pd.notna(row['empirical_score']) else 0.0,
                    row['surprise_pct']
                ),
                axis=1
            )
            
            # Créer clé canonique pour cluster
            df_events['canonical_key'] = df_events.apply(
                lambda row: f"{row['country'].upper()}__{normalize_event_key(row['event_key'])}__{row['importance_n']}",
                axis=1
            )
        
        return df_events
    except Exception as e:
        print(f"⚠️ Erreur requête événements : {e}")
        return pd.DataFrame()


def identify_core_events(
    clusters_by_date: Dict[datetime.date, Set[str]],
    cluster_ref: Set[str],
    support_threshold: float = CORE_EVENTS_SUPPORT_THRESHOLD
) -> Set[str]:
    """
    Identifie le noyau dur (core events) d'un cluster
    
    Le noyau dur = événements présents dans >= support_threshold% des clusters similaires
    
    Args:
        clusters_by_date: Dictionnaire date → set d'événements canoniques
        cluster_ref: Cluster de référence (événements du mouvement actuel)
        support_threshold: Seuil de support (0.80 = 80%)
    
    Returns:
        Set des événements core
    """
    if not cluster_ref:
        return set()
    
    # Trouver clusters similaires (contenant au moins 50% des événements du cluster_ref)
    similar_clusters = []
    for date_obj, cluster in clusters_by_date.items():
        intersection = cluster_ref.intersection(cluster)
        jaccard = len(intersection) / len(cluster_ref.union(cluster)) if cluster_ref.union(cluster) else 0.0
        if jaccard >= 0.5:  # Au moins 50% de similarité
            similar_clusters.append(cluster)
    
    if not similar_clusters:
        # Pas de clusters similaires → utiliser cluster_ref comme noyau dur
        return cluster_ref
    
    # Calculer support pour chaque événement du cluster_ref
    n_similar = len(similar_clusters)
    event_support = defaultdict(int)
    
    for event in cluster_ref:
        for cluster in similar_clusters:
            if event in cluster:
                event_support[event] += 1
    
    # Extraire noyau dur (support >= threshold)
    core_events = {
        event for event, count in event_support.items()
        if count / n_similar >= support_threshold
    }
    
    # Si aucun noyau dur trouvé, utiliser cluster_ref
    if not core_events:
        return cluster_ref
    
    return core_events


def build_cluster_signature(events: pd.DataFrame) -> str:
    """
    Construit la signature d'un cluster (pour identification)
    
    Signature = tri alphabétique des clés canoniques
    """
    if events.empty:
        return ""
    
    canonical_keys = sorted(events['canonical_key'].unique().tolist())
    return "|".join(canonical_keys)


def process_movement(
    conn: duckdb.DuckDBPyConnection,
    row: pd.Series,
    clusters_by_date: Dict[datetime.date, Set[str]]
) -> Optional[Dict]:
    """
    Traite un mouvement : identifie cluster, noyau dur, calcule métriques
    """
    movement_start = row['movement_start_time']
    date_str = row['date']
    
    # 1. Trouver événements dans la fenêtre
    df_events = find_events_for_movement(conn, movement_start)
    
    if df_events.empty:
        return None  # Pas d'événements → mouvement non prédictible
    
    # 2. Construire cluster
    cluster_signature = build_cluster_signature(df_events)
    cluster_events = set(df_events['canonical_key'].unique())
    
    # 3. Identifier noyau dur
    date_obj = pd.to_datetime(date_str).date()
    core_events = identify_core_events(clusters_by_date, cluster_events)
    
    # 4. Calculer métriques du cluster
    # Scores empiriques
    base_scores = df_events['empirical_score'].dropna()
    avg_base_score = base_scores.mean() if not base_scores.empty else 0.0
    
    adjusted_scores = df_events['empirical_score_adjusted'].dropna()
    avg_adjusted_score = adjusted_scores.mean() if not adjusted_scores.empty else 0.0
    
    # Surprises
    surprises = df_events['surprise_pct'].dropna()
    avg_surprise = surprises.mean() if not surprises.empty else 0.0
    max_surprise = surprises.max() if not surprises.empty else 0.0
    
    # Surprise nette (somme algébrique pour tenir compte des annulations)
    # Pour l'instant, utiliser moyenne absolue
    surprise_net = avg_surprise
    
    # Pays
    countries = df_events['country'].value_counts().to_dict()
    n_events_us = countries.get('US', 0)
    n_events_eu = countries.get('EU', 0)
    n_events_de = countries.get('DE', 0)
    
    # Importance
    importance_counts = df_events['importance_n'].value_counts().to_dict()
    n_events_high = importance_counts.get(3, 0)
    n_events_medium = importance_counts.get(2, 0)
    n_events_low = importance_counts.get(1, 0)
    
    # 5. Construire résultat
    result = {
        # Informations mouvement
        'date': date_str,
        'movement_start_time': movement_start,
        'peak_time': row['peak_time'],
        'peak_pips': row['peak_pips'],
        'movement_class': row['movement_class'],
        'direction': row['direction'],
        'confidence': row['confidence'],
        
        # Cluster
        'cluster_signature': cluster_signature,
        'n_events_total': len(df_events),
        'n_events_us': n_events_us,
        'n_events_eu': n_events_eu,
        'n_events_de': n_events_de,
        'n_events_high': n_events_high,
        'n_events_medium': n_events_medium,
        'n_events_low': n_events_low,
        
        # Noyau dur
        'n_core_events': len(core_events),
        'core_events_signature': "|".join(sorted(core_events)),
        
        # Métriques
        'avg_base_empirical_score': avg_base_score,
        'avg_adjusted_empirical_score': avg_adjusted_score,
        'avg_surprise_pct': avg_surprise,
        'max_surprise_pct': max_surprise,
        'surprise_net': surprise_net,
        
        # Événements (sérialisés)
        'event_keys': ','.join(df_events['event_key'].tolist()),
        'event_canonical_keys': ','.join(df_events['canonical_key'].tolist()),
    }
    
    return result


def load_all_clusters_from_db(conn: duckdb.DuckDBPyConnection) -> Dict[datetime.date, Set[str]]:
    """
    Charge tous les clusters historiques depuis la DB pour identification noyau dur
    """
    print("📊 Chargement clusters historiques depuis DB...")
    
    # Charger tous les événements HIGH importance
    query = """
    SELECT 
        DATE(e.ts_utc) as date_bern,
        e.country,
        e.event_key,
        e.importance_n
    FROM events e
    WHERE e.importance_n <= ?
      AND DATE(e.ts_utc) >= '2020-01-01'
    ORDER BY date_bern, e.ts_utc
    """
    
    df_all = conn.execute(query, [MIN_IMPORTANCE]).df()
    
    if df_all.empty:
        print("⚠️ Aucun événement historique trouvé")
        return {}
    
    # Construire clusters par date
    clusters_by_date = defaultdict(set)
    
    for _, row in df_all.iterrows():
        date_obj = pd.to_datetime(row['date_bern']).date()
        canonical_key = f"{row['country'].upper()}__{normalize_event_key(row['event_key'])}__{row['importance_n']}"
        clusters_by_date[date_obj].add(canonical_key)
    
    print(f"✅ {len(clusters_by_date)} dates historiques chargées")
    
    return clusters_by_date


def main():
    """
    Fonction principale : Construit la base de données complète
    """
    
    print("=" * 80)
    print("CONSTRUCTION BASE DE DONNÉES MOUVEMENTS PRÉDICTIBLES")
    print("=" * 80)
    print()
    
    # 1. Charger mouvements avec événements
    print("📊 ÉTAPE 1 : Chargement des mouvements avec événements")
    print("-" * 80)
    
    matched_file = Path(__file__).parent.parent / 'outputs' / 'movements_matched_with_events.csv'
    
    if not matched_file.exists():
        print(f"❌ Fichier non trouvé : {matched_file}")
        print("   Exécutez d'abord match_movements_with_events.py")
        return
    
    df_matched = pd.read_csv(matched_file)
    
    # Filtrer seulement les mouvements avec événements (prédictibles)
    df_predictable = df_matched[df_matched['has_events'] == True].copy()
    
    # Convertir colonnes datetime
    datetime_cols = ['movement_start_time', 'peak_time']
    for col in datetime_cols:
        if col in df_predictable.columns:
            df_predictable[col] = pd.to_datetime(df_predictable[col], utc=True)
            df_predictable[col] = df_predictable[col].dt.tz_convert('Europe/Zurich')
    
    print(f"✅ {len(df_predictable)} mouvements prédictibles (avec événements)")
    print(f"   Période : {df_predictable['date'].min()} → {df_predictable['date'].max()}")
    print()
    
    # 2. Connecter DB et charger clusters historiques
    print("📊 ÉTAPE 2 : Connexion DB et chargement clusters historiques")
    print("-" * 80)
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    clusters_by_date = load_all_clusters_from_db(conn)
    print()
    
    # 3. Traiter chaque mouvement
    print(f"📊 ÉTAPE 3 : Traitement des mouvements (identification clusters et noyaux durs)")
    print("-" * 80)
    
    results = []
    
    for idx, row in df_predictable.iterrows():
        if (idx + 1) % 500 == 0:
            print(f"   Progression : {idx + 1}/{len(df_predictable)} mouvements traités...")
        
        result = process_movement(conn, row, clusters_by_date)
        
        if result:
            results.append(result)
    
    print(f"✅ Traitement terminé : {len(results)} mouvements avec clusters identifiés")
    print()
    
    # 4. Statistiques
    print("=" * 80)
    print("RÉSULTATS")
    print("=" * 80)
    print()
    
    df_results = pd.DataFrame(results)
    
    if df_results.empty:
        print("❌ Aucun résultat")
        return
    
    print(f"📊 Statistiques globales :")
    print(f"   Total mouvements traités     : {len(df_results):,}")
    print(f"   Clusters uniques             : {df_results['cluster_signature'].nunique():,}")
    print(f"   Noyaux durs uniques          : {df_results['core_events_signature'].nunique():,}")
    print()
    
    print(f"📊 Par classe de mouvement :")
    for movement_class in df_results['movement_class'].unique():
        df_class = df_results[df_results['movement_class'] == movement_class]
        avg_pips = df_class['peak_pips'].mean()
        avg_events = df_class['n_events_total'].mean()
        avg_core = df_class['n_core_events'].mean()
        print(f"   {movement_class:12s} : {len(df_class):4d} mouvements | {avg_pips:6.1f} pips moy. | {avg_events:4.1f} événements moy. | {avg_core:4.1f} core moy.")
    print()
    
    print(f"📊 Métriques moyennes :")
    print(f"   Score empirique base        : {df_results['avg_base_empirical_score'].mean():.2f}")
    print(f"   Score empirique ajusté      : {df_results['avg_adjusted_empirical_score'].mean():.2f}")
    print(f"   Surprise moyenne            : {df_results['avg_surprise_pct'].mean():.2f}%")
    print(f"   Surprise max moyenne        : {df_results['max_surprise_pct'].mean():.2f}%")
    print()
    
    # 5. Sauvegarder
    output_file = Path(__file__).parent.parent / 'outputs' / 'predictable_movements_database.csv'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Préparer pour CSV
    df_csv = df_results.copy()
    for col in ['movement_start_time', 'peak_time']:
        if col in df_csv.columns:
            df_csv[col] = df_csv[col].apply(
                lambda x: x.strftime('%Y-%m-%d %H:%M:%S%z') if pd.notna(x) else None
            )
    
    df_csv.to_csv(output_file, index=False)
    print(f"💾 Base de données sauvegardée : {output_file}")
    print()
    
    # 6. Sauvegarder aussi dans DuckDB pour requêtes rapides
    db_output_file = Path(__file__).parent.parent / 'outputs' / 'predictable_movements_database.duckdb'
    conn_output = duckdb.connect(str(db_output_file))
    
    # Créer table
    conn_output.execute("DROP TABLE IF EXISTS predictable_movements")
    conn_output.execute("""
        CREATE TABLE predictable_movements AS
        SELECT * FROM df_results
    """)
    
    conn_output.close()
    print(f"💾 Base DuckDB sauvegardée : {db_output_file}")
    print()
    
    conn.close()
    
    print("=" * 80)
    print("✅ CONSTRUCTION TERMINÉE")
    print("=" * 80)
    print()
    print(f"📊 {len(df_results)} mouvements prédictibles avec clusters et noyaux durs identifiés")
    print(f"📁 Fichiers créés :")
    print(f"   - {output_file}")
    print(f"   - {db_output_file}")
    print()
    
    return df_results


if __name__ == '__main__':
    main()


