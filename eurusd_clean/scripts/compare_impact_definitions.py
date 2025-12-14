#!/usr/bin/env python3
"""
Script d'audit comparatif des définitions d'impact
==================================================

Compare numériquement deux définitions d'impact :
1. impact_detecte_pips : ce que retourne detect_pattern_type() (movement['impact_pips'])
2. phase1_pips : ce que mesure measure_impact_from_finnhub() ou ce qui est stocké dans event_impacts_v2

Usage:
    python scripts/compare_impact_definitions.py

Objectif:
    Obtenir une vision chiffrée de la relation entre "Impact détecté" et phase1_pips
    pour décider, sur base empirique, quelle définition prendre comme référence.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import warnings

import pandas as pd
import duckdb
import numpy as np
import pytz

# Ajouter les chemins nécessaires
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'streamlit_app' / 'pages'))

# Imports depuis le Planificateur (même méthode que catalog_all_clusters_from_db.py)
# Utiliser importlib pour charger dynamiquement le module
import importlib.util
planificateur_path = PROJECT_ROOT / 'streamlit_app' / 'pages' / '5_Planificateur_V3.2_Formule_Lineaire.py'
spec = importlib.util.spec_from_file_location("planificateur", planificateur_path)
planificateur = importlib.util.module_from_spec(spec)
spec.loader.exec_module(planificateur)

# Extraire les fonctions nécessaires
load_events_for_date = planificateur.load_events_for_date
enrich_events_with_surprises = planificateur.enrich_events_with_surprises
detect_pattern_type = planificateur.detect_pattern_type

# Import depuis price_loader_finnhub
from core.price_loader_finnhub import measure_impact_from_finnhub

# Configuration
DB_PATH = PROJECT_ROOT / 'data' / 'warehouse.duckdb'
TIMEZONE_BERN = 'Europe/Zurich'
MIN_IMPACT_PIPS = 35.0  # Seuil minimum pour detect_pattern_type

# Supprimer les warnings pandas pour la lisibilité
warnings.filterwarnings('ignore', category=pd.errors.PerformanceWarning)


def get_nfp_events(
    conn,
    start_date: str = '2020-01-01',
    end_date: Optional[str] = None,
    country: str = 'US',
    limit: Optional[int] = None
) -> pd.DataFrame:
    """
    Récupère les événements NFP (Non-Farm Payrolls) depuis la DB.
    
    Args:
        conn: Connexion DuckDB
        start_date: Date de début (format 'YYYY-MM-DD')
        end_date: Date de fin (format 'YYYY-MM-DD'), None = aujourd'hui
        country: Pays (défaut: 'US')
        limit: Limite du nombre d'événements (None = pas de limite)
    
    Returns:
        DataFrame avec colonnes: ts_utc, event_key, event_title, country, actual, estimate, previous
    """
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    # Rechercher les événements NFP (variantes possibles du nom)
    query = """
    SELECT 
        ts_utc,
        event_key,
        event_title,
        country,
        actual,
        estimate,
        forecast,
        previous,
        importance_n
    FROM events
    WHERE country = ?
      AND DATE(ts_utc) >= ?
      AND DATE(ts_utc) <= ?
      AND (
          LOWER(event_key) LIKE '%nonfarm payrolls%'
          OR LOWER(event_key) LIKE '%non farm payrolls%'
          OR LOWER(event_key) LIKE '%non-farm payrolls%'
          OR LOWER(event_title) LIKE '%nonfarm payrolls%'
          OR LOWER(event_title) LIKE '%non farm payrolls%'
          OR LOWER(event_title) LIKE '%non-farm payrolls%'
          OR LOWER(event_title) LIKE '%employment situation%'
      )
    ORDER BY ts_utc ASC
    """
    
    if limit:
        query += f" LIMIT {limit}"
    
    df = conn.execute(query, [country, start_date, end_date]).df()
    
    return df


def calculate_impact_detecte(
    event_ts: pd.Timestamp,
    event_date: datetime,
    conn,
    timezone_str: str = TIMEZONE_BERN,
    min_pips: float = MIN_IMPACT_PIPS
) -> Optional[Dict]:
    """
    Calcule l'impact détecté via detect_pattern_type().
    
    Args:
        event_ts: Timestamp de l'événement (pandas Timestamp)
        event_date: Date de l'événement (datetime)
        conn: Connexion DuckDB
        timezone_str: Timezone (défaut: 'Europe/Zurich')
        min_pips: Seuil minimum (défaut: 35.0)
    
    Returns:
        Dict avec impact_pips, direction, pattern_type, ou None si échec
    """
    try:
        # 1. Charger les prix pour cette date
        query_prices = """
        SELECT datetime, open, high, low, close
        FROM prices_finnhub_m1
        WHERE DATE(datetime) = ?
        ORDER BY datetime
        """
        
        df_prices = conn.execute(query_prices, [event_date.strftime('%Y-%m-%d')]).df()
        
        if df_prices.empty:
            return None
        
        # 2. Convertir en timezone et indexer
        df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
        if df_prices['datetime'].dt.tz is None:
            df_prices['datetime'] = df_prices['datetime'].dt.tz_localize(timezone_str)
        else:
            df_prices['datetime'] = df_prices['datetime'].dt.tz_convert(timezone_str)
        df_prices = df_prices.set_index('datetime')
        
        # 3. Charger les événements pour cette date
        df_events = load_events_for_date(
            event_date,
            DB_PATH,
            timezone_str,
            min_importance=1,
            countries=['US']
        )
        
        # Note: load_events_for_date peut retourner un DataFrame vide si aucun événement
        # On continue même si vide pour essayer de détecter un mouvement quand même
        
        if df_events.empty:
            return None
        
        # 4. Enrichir les événements
        df_events_enriched = enrich_events_with_surprises(df_events)
        
        # 5. Convertir event_ts en timezone si nécessaire
        if event_ts.tz is None:
            event_ts_tz = event_ts.tz_localize(timezone_str)
        else:
            event_ts_tz = event_ts.tz_convert(timezone_str)
        
        # 6. Détecter le pattern
        pattern_result = detect_pattern_type(
            df_prices,
            df_events_enriched,
            min_pips=min_pips,
            timezone=pytz.timezone(timezone_str),
            cluster_anchor_time=event_ts_tz.to_pydatetime(),
            silent_warning=True
        )
        
        if pattern_result.get('pattern_type') == 'INCONNU':
            return None
        
        movement = pattern_result.get('movement')
        if not movement:
            return None
        
        impact_pips = movement.get('impact_pips', None)
        if impact_pips is None or impact_pips <= 0:
            return None
        
        return {
            'impact_detecte_pips': float(impact_pips),
            'direction': movement.get('direction', 'UNKNOWN'),
            'pattern_type': pattern_result.get('pattern_type', 'INCONNU'),
            'detection_confidence': pattern_result.get('detection_confidence', 0.0)
        }
    
    except Exception as e:
        print(f"   ⚠️ Erreur calcul impact_detecte pour {event_date}: {e}")
        return None


def get_phase1_pips(
    event_ts: pd.Timestamp,
    conn,
    db_path: Path = DB_PATH,
    use_db: bool = True
) -> Optional[float]:
    """
    Récupère phase1_pips soit depuis event_impacts_v2, soit via measure_impact_from_finnhub().
    
    Args:
        event_ts: Timestamp de l'événement
        conn: Connexion DuckDB
        db_path: Chemin vers la DB
        use_db: True = essayer event_impacts_v2 d'abord, False = utiliser measure_impact_from_finnhub() directement
    
    Returns:
        phase1_pips (float) ou None si non disponible
    """
    # Option B : Essayer event_impacts_v2 d'abord si use_db=True
    if use_db:
        try:
            # Vérifier si la table existe
            tables = conn.execute("SHOW TABLES").df()
            if 'event_impacts_v2' in tables['name'].values:
                # Récupérer depuis la table
                query = """
                SELECT phase1_pips
                FROM event_impacts_v2
                WHERE ts_utc = ?
                  AND country = 'US'
                LIMIT 1
                """
                
                result = conn.execute(query, [event_ts]).df()
                if not result.empty and pd.notna(result.iloc[0]['phase1_pips']):
                    phase1 = float(result.iloc[0]['phase1_pips'])
                    if phase1 > 0:
                        return phase1
        except Exception as e:
            # Si échec, continuer avec Option A
            pass
    
    # Option A : Utiliser measure_impact_from_finnhub()
    try:
        # Convertir event_ts en datetime si nécessaire
        if isinstance(event_ts, pd.Timestamp):
            event_dt = event_ts.to_pydatetime()
        else:
            event_dt = event_ts
        
        # S'assurer que c'est en timezone Bern
        if event_dt.tzinfo is None:
            tz_bern = pytz.timezone(TIMEZONE_BERN)
            event_dt = tz_bern.localize(event_dt)
        elif str(event_dt.tzinfo) != TIMEZONE_BERN:
            tz_bern = pytz.timezone(TIMEZONE_BERN)
            event_dt = event_dt.astimezone(tz_bern)
        
        # Mesurer l'impact
        result = measure_impact_from_finnhub(
            db_path=db_path,
            event_timestamp=event_dt,
            lookback_minutes=5,
            lookahead_minutes=120,
            debug=False
        )
        
        if result and result.get('impact_pips'):
            return float(result['impact_pips'])
    
    except Exception as e:
        print(f"   ⚠️ Erreur mesure phase1_pips pour {event_ts}: {e}")
    
    return None


def main():
    """
    Fonction principale du script d'audit.
    """
    print("=" * 80)
    print("AUDIT COMPARATIF DES DÉFINITIONS D'IMPACT")
    print("=" * 80)
    print()
    print("Comparaison entre :")
    print("  1. impact_detecte_pips : detect_pattern_type() → movement['impact_pips']")
    print("  2. phase1_pips : measure_impact_from_finnhub() ou event_impacts_v2")
    print()
    
    # Connexion DB
    if not DB_PATH.exists():
        print(f"❌ Erreur : DB introuvable : {DB_PATH}")
        return
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    try:
        # 1. Sélectionner l'échantillon d'événements
        print("1️⃣ Sélection de l'échantillon d'événements (NFP US)...")
        print("-" * 80)
        
        df_events = get_nfp_events(
            conn,
            start_date='2020-01-01',
            end_date=None,
            country='US',
            limit=100  # Limiter à 100 événements pour un premier audit
        )
        
        if df_events.empty:
            print("❌ Aucun événement NFP trouvé")
            return
        
        print(f"   ✅ {len(df_events)} événements NFP trouvés")
        print(f"      Période : {df_events['ts_utc'].min()} → {df_events['ts_utc'].max()}")
        print()
        
        # 2. Calculer les deux types d'impact pour chaque événement
        print("2️⃣ Calcul des impacts pour chaque événement...")
        print("-" * 80)
        
        results = []
        
        for idx, row in df_events.iterrows():
            event_ts = pd.to_datetime(row['ts_utc'])
            event_date = event_ts.to_pydatetime().date()
            event_title = row.get('event_title', row.get('event_key', 'Unknown'))
            
            print(f"   📅 {event_date} {event_ts.strftime('%H:%M')} - {event_title[:50]}...")
            
            # Calculer impact_detecte_pips
            impact_detecte_result = calculate_impact_detecte(
                event_ts=event_ts,
                event_date=datetime.combine(event_date, datetime.min.time()),
                conn=conn,
                timezone_str=TIMEZONE_BERN,
                min_pips=MIN_IMPACT_PIPS
            )
            
            impact_detecte_pips = impact_detecte_result['impact_detecte_pips'] if impact_detecte_result else None
            
            # Récupérer phase1_pips
            phase1_pips = get_phase1_pips(
                event_ts=event_ts,
                conn=conn,
                db_path=DB_PATH,
                use_db=True  # Essayer DB d'abord, puis measure_impact_from_finnhub()
            )
            
            # Ajouter au résultat si les deux valeurs sont disponibles
            if impact_detecte_pips is not None and phase1_pips is not None:
                diff_pips = impact_detecte_pips - phase1_pips
                ratio = impact_detecte_pips / phase1_pips if phase1_pips > 0 else None
                
                results.append({
                    'event_ts': event_ts,
                    'event_date': event_date,
                    'event_title': event_title,
                    'country': row.get('country', 'US'),
                    'impact_detecte_pips': impact_detecte_pips,
                    'phase1_pips': phase1_pips,
                    'diff_pips': diff_pips,
                    'ratio_detecte_sur_phase1': ratio,
                    'direction': impact_detecte_result.get('direction', 'UNKNOWN') if impact_detecte_result else None,
                    'pattern_type': impact_detecte_result.get('pattern_type', 'INCONNU') if impact_detecte_result else None
                })
                
                print(f"      ✅ impact_detecte={impact_detecte_pips:.1f} | phase1={phase1_pips:.1f} | ratio={ratio:.2f}")
            else:
                missing = []
                if impact_detecte_pips is None:
                    missing.append("impact_detecte")
                if phase1_pips is None:
                    missing.append("phase1")
                print(f"      ⚠️ Valeurs manquantes : {', '.join(missing)}")
        
        print()
        
        if not results:
            print("❌ Aucun résultat valide (les deux valeurs disponibles)")
            return
        
        # 3. Construire le DataFrame de comparaison
        print("3️⃣ Construction du DataFrame de comparaison...")
        print("-" * 80)
        
        df_comparison = pd.DataFrame(results)
        
        # Filtrer les lignes où ratio est valide (phase1_pips > 0)
        df_comparison = df_comparison[df_comparison['ratio_detecte_sur_phase1'].notna()]
        
        n_valid = len(df_comparison)
        print(f"   ✅ {n_valid} événements avec les deux valeurs disponibles")
        print()
        
        # 4. Stats descriptives
        print("=" * 80)
        print("STATS DESCRIPTIVES")
        print("=" * 80)
        print()
        
        print("📊 Distribution des deux mesures :")
        print(df_comparison[['impact_detecte_pips', 'phase1_pips']].describe())
        print()
        
        # 5. Corrélation
        print("📈 Corrélation entre les deux mesures :")
        corr = df_comparison[['impact_detecte_pips', 'phase1_pips']].corr()
        print(corr)
        print()
        print(f"   Corrélation Pearson : {corr.iloc[0, 1]:.3f}")
        print()
        
        # 6. Ratio impact_detecte / phase1_pips
        print("📐 Ratio impact_detecte / phase1_pips :")
        print(df_comparison['ratio_detecte_sur_phase1'].describe())
        print()
        
        # Stats supplémentaires sur le ratio
        ratio_median = df_comparison['ratio_detecte_sur_phase1'].median()
        ratio_mean = df_comparison['ratio_detecte_sur_phase1'].mean()
        ratio_std = df_comparison['ratio_detecte_sur_phase1'].std()
        ratio_q25 = df_comparison['ratio_detecte_sur_phase1'].quantile(0.25)
        ratio_q75 = df_comparison['ratio_detecte_sur_phase1'].quantile(0.75)
        
        print(f"   Médiane : {ratio_median:.2f}")
        print(f"   Moyenne : {ratio_mean:.2f}")
        print(f"   Écart-type : {ratio_std:.2f}")
        print(f"   IQR (Q25-Q75) : {ratio_q25:.2f} - {ratio_q75:.2f}")
        print()
        
        # 7. Différence absolue
        print("📉 Différence absolue (impact_detecte - phase1_pips) :")
        print(df_comparison['diff_pips'].describe())
        print()
        
        # 8. Exemples concrets
        print("=" * 80)
        print("EXEMPLES D'ÉVÉNEMENTS")
        print("=" * 80)
        print()
        
        # Trier par ratio pour voir les cas extrêmes
        df_sorted = df_comparison.sort_values('ratio_detecte_sur_phase1', ascending=False)
        
        print("🔝 Top 10 événements (ratio le plus élevé) :")
        print()
        display_cols = ['event_date', 'event_title', 'impact_detecte_pips', 'phase1_pips', 'ratio_detecte_sur_phase1', 'diff_pips']
        print(df_sorted[display_cols].head(10).to_string(index=False))
        print()
        
        print("🔻 Bottom 10 événements (ratio le plus faible) :")
        print()
        print(df_sorted[display_cols].tail(10).to_string(index=False))
        print()
        
        # 9. Résumé final
        print("=" * 80)
        print("RÉSUMÉ")
        print("=" * 80)
        print()
        print(f"Nombre d'événements analysés : {n_valid}")
        print(f"Corrélation Pearson : {corr.iloc[0, 1]:.3f}")
        print(f"Ratio médian (impact_detecte / phase1_pips) : {ratio_median:.2f}")
        print(f"Ratio moyen : {ratio_mean:.2f}")
        print()
        
        if ratio_median > 1.0:
            print(f"⚠️ impact_detecte est en moyenne {ratio_median:.1f}x plus élevé que phase1_pips")
        elif ratio_median < 1.0:
            print(f"⚠️ impact_detecte est en moyenne {1/ratio_median:.1f}x plus faible que phase1_pips")
        else:
            print("✅ Les deux mesures sont similaires en moyenne")
        print()
    
    finally:
        conn.close()


if __name__ == '__main__':
    main()
