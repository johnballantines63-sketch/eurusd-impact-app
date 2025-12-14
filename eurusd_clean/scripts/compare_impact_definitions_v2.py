#!/usr/bin/env python3
"""
Script d'audit comparatif des définitions d'impact – Version 2
==============================================================

Compare numériquement trois définitions d'impact :

1. impact_detecte_pips :
   - Ce que retourne detect_pattern_type() (movement['impact_pips'])
   - Baseline = segment détecté (Planificateur)

2. phase1_pips_legacy :
   - Mesure via measure_impact_from_finnhub(..., use_unified=False)
   - Ancienne logique interne (pré-refonte)

3. impact_unified_pips :
   - Mesure via measure_impact_from_finnhub(..., use_unified=True)
   - Nouvelle logique canonique IMPACT_SPEC_V1 (baseline = event_open, horizon = 120 min)

Usage:
    python scripts/compare_impact_definitions_v2.py
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
import warnings

import pandas as pd
import duckdb
import numpy as np
import pytz

# -----------------------------------------------------------------------------
# Chemins & imports internes
# -----------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "streamlit_app" / "pages"))

DB_PATH = PROJECT_ROOT / "data" / "warehouse.duckdb"
TIMEZONE_BERN = "Europe/Zurich"
MIN_IMPACT_PIPS = 35.0  # Seuil min pour detect_pattern_type

TZ_BERN = pytz.timezone(TIMEZONE_BERN)

warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)

# --- Import dynamique du Planificateur (comme dans catalog_all_clusters_from_db.py)
import importlib.util

planificateur_path = PROJECT_ROOT / "streamlit_app" / "pages" / "5_Planificateur_V3.2_Formule_Lineaire.py"
spec = importlib.util.spec_from_file_location("planificateur", planificateur_path)
planificateur = importlib.util.module_from_spec(spec)
spec.loader.exec_module(planificateur)

load_events_for_date = planificateur.load_events_for_date
enrich_events_with_surprises = planificateur.enrich_events_with_surprises
detect_pattern_type = planificateur.detect_pattern_type

# --- Import finnhub
from core.price_loader_finnhub import measure_impact_from_finnhub


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def get_nfp_events(
    conn,
    start_date: str = "2020-01-01",
    end_date: Optional[str] = None,
    country: str = "US",
    limit: Optional[int] = None,
) -> pd.DataFrame:
    """
    Récupère les événements NFP (Non-Farm Payrolls) depuis la DB.
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")

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
    min_pips: float = MIN_IMPACT_PIPS,
) -> Optional[Dict]:
    """
    Calcule l'impact détecté via detect_pattern_type() (Planificateur).

    Retourne:
        {
            'impact_detecte_pips': float,
            'direction': 'UP'/'DOWN'/...,
            'pattern_type': str,
            'detection_confidence': float,
        }
    ou None si échec.
    """
    try:
        # 1. Charger les prix pour cette date
        query_prices = """
        SELECT datetime, open, high, low, close
        FROM prices_finnhub_m1
        WHERE DATE(datetime) = ?
        ORDER BY datetime
        """
        df_prices = conn.execute(query_prices, [event_date.strftime("%Y-%m-%d")]).df()
        if df_prices.empty:
            return None

        # 2. Datetime + tz
        df_prices["datetime"] = pd.to_datetime(df_prices["datetime"])
        if df_prices["datetime"].dt.tz is None:
            df_prices["datetime"] = df_prices["datetime"].dt.tz_localize(timezone_str)
        else:
            df_prices["datetime"] = df_prices["datetime"].dt.tz_convert(timezone_str)
        df_prices = df_prices.set_index("datetime")

        # 3. Charger les événements du jour via le Planificateur
        df_events = load_events_for_date(
            event_date,
            DB_PATH,
            timezone_str,
            min_importance=1,
            countries=["US"],
        )
        # On continue même si vide (mais detect_pattern_type risque de renvoyer INCONNU)
        df_events_enriched = enrich_events_with_surprises(df_events)

        # 4. event_ts → timezone Bern
        if event_ts.tz is None:
            event_ts_tz = event_ts.tz_localize(timezone_str)
        else:
            event_ts_tz = event_ts.tz_convert(timezone_str)

        # 5. Détection pattern
        pattern_result = detect_pattern_type(
            df_prices,
            df_events_enriched,
            min_pips=min_pips,
            timezone=pytz.timezone(timezone_str),
            cluster_anchor_time=event_ts_tz.to_pydatetime(),
            silent_warning=True,
        )

        if pattern_result.get("pattern_type") == "INCONNU":
            return None

        movement = pattern_result.get("movement")
        if not movement:
            return None

        impact_pips = movement.get("impact_pips", None)
        if impact_pips is None or impact_pips <= 0:
            return None

        return {
            "impact_detecte_pips": float(impact_pips),
            "direction": movement.get("direction", "UNKNOWN"),
            "pattern_type": pattern_result.get("pattern_type", "INCONNU"),
            "detection_confidence": pattern_result.get("detection_confidence", 0.0),
        }

    except Exception as e:
        print(f"   ⚠️ Erreur calcul impact_detecte pour {event_date}: {e}")
        return None


def measure_phase1(
    event_ts: pd.Timestamp,
    use_unified: bool,
    db_path: Path = DB_PATH,
) -> Optional[float]:
    """
    Mesure phase1_pips via measure_impact_from_finnhub().

    Args:
        event_ts: Timestamp de l'événement (colonne ts_utc de la DB)
        use_unified:
            - True  => nouvelle logique canonique IMPACT_SPEC_V1
            - False => ancienne logique (legacy)
    """
    try:
        # On part du ts_utc tel quel ; la fonction interne se charge du TZ
        if isinstance(event_ts, pd.Timestamp):
            event_dt = event_ts.to_pydatetime()
        else:
            event_dt = event_ts

        result = measure_impact_from_finnhub(
            db_path=db_path,
            event_timestamp=event_dt,
            lookback_minutes=5,
            lookahead_minutes=120,
            debug=False,
            use_unified=use_unified,
        )
        if result and result.get("impact_pips") is not None:
            val = float(result["impact_pips"])
            if val > 0:
                return val
    except Exception as e:
        mode = "unified" if use_unified else "legacy"
        print(f"   ⚠️ Erreur measure_phase1 (mode={mode}) pour {event_ts}: {e}")

    return None


# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------

def main():
    print("=" * 80)
    print("AUDIT COMPARATIF – 3 DÉFINITIONS D'IMPACT")
    print("=" * 80)
    print()
    print("Comparaison entre :")
    print("  1. impact_detecte_pips    : detect_pattern_type() (Planificateur)")
    print("  2. phase1_pips_legacy     : measure_impact_from_finnhub(..., use_unified=False)")
    print("  3. impact_unified_pips    : measure_impact_from_finnhub(..., use_unified=True)")
    print()

    if not DB_PATH.exists():
        print(f"❌ Erreur : DB introuvable : {DB_PATH}")
        return

    conn = duckdb.connect(str(DB_PATH), read_only=True)

    try:
        # 1) Échantillon NFP
        print("1️⃣ Sélection de l'échantillon d'événements (NFP US)...")
        print("-" * 80)
        df_events = get_nfp_events(
            conn,
            start_date="2020-01-01",
            end_date=None,
            country="US",
            limit=100,
        )

        if df_events.empty:
            print("❌ Aucun événement NFP trouvé")
            return

        print(f"   ✅ {len(df_events)} événements NFP trouvés")
        print(f"      Période : {df_events['ts_utc'].min()} → {df_events['ts_utc'].max()}")
        print()

        # 2) Calcul des 3 métriques
        print("2️⃣ Calcul des impacts pour chaque événement...")
        print("-" * 80)

        results: List[Dict] = []

        for idx, row in df_events.iterrows():
            event_ts = pd.to_datetime(row["ts_utc"])
            event_date = event_ts.to_pydatetime().date()
            event_title = row.get("event_title", row.get("event_key", "Unknown"))

            print(f"   📅 {event_date} {event_ts.strftime('%H:%M')} - {event_title[:50]}...")

            # impact_detecte_pips (Planificateur)
            impact_detecte_result = calculate_impact_detecte(
                event_ts=event_ts,
                event_date=datetime.combine(event_date, datetime.min.time()),
                conn=conn,
                timezone_str=TIMEZONE_BERN,
                min_pips=MIN_IMPACT_PIPS,
            )
            impact_detecte_pips = (
                impact_detecte_result["impact_detecte_pips"]
                if impact_detecte_result
                else None
            )

            # phase1_pips_legacy (ancienne logique)
            phase1_legacy = measure_phase1(
                event_ts=event_ts,
                use_unified=False,
                db_path=DB_PATH,
            )

            # impact_unified_pips (nouvelle logique IMPACT_SPEC_V1)
            impact_unified = measure_phase1(
                event_ts=event_ts,
                use_unified=True,
                db_path=DB_PATH,
            )

            # Si au moins 2 valeurs sont présentes, ça vaut le coup de garder la ligne
            available = sum(
                v is not None
                for v in [impact_detecte_pips, phase1_legacy, impact_unified]
            )
            if available >= 2:
                results.append(
                    {
                        "event_ts": event_ts,
                        "event_date": event_date,
                        "event_title": event_title,
                        "country": row.get("country", "US"),
                        "impact_detecte_pips": impact_detecte_pips,
                        "phase1_pips_legacy": phase1_legacy,
                        "impact_unified_pips": impact_unified,
                        "direction_detecte": impact_detecte_result.get("direction", "UNKNOWN")
                        if impact_detecte_result
                        else None,
                        "pattern_type": impact_detecte_result.get("pattern_type", "INCONNU")
                        if impact_detecte_result
                        else None,
                    }
                )

                print(
                    f"      ✅ detecte={impact_detecte_pips} | "
                    f"legacy={phase1_legacy} | unified={impact_unified}"
                )
            else:
                print("      ⚠️ Moins de 2 valeurs disponibles, ligne exclue")

        print()
        if not results:
            print("❌ Aucun résultat exploitable (au moins 2 valeurs requises)")
            return

        # 3) DataFrame de comparaison
        print("3️⃣ Construction du DataFrame de comparaison...")
        print("-" * 80)

        df_cmp = pd.DataFrame(results)
        n_rows = len(df_cmp)
        print(f"   ✅ {n_rows} lignes avec au moins 2 métriques disponibles")
        print()

        # 4) Stats pair à pair
        print("=" * 80)
        print("STATS DESCRIPTIVES – Pair à pair")
        print("=" * 80)
        print()

        def describe_pair(col_a: str, col_b: str):
            sub = df_cmp[[col_a, col_b]].dropna()
            if len(sub) == 0:
                print(f"❌ Pas de données pour {col_a} vs {col_b}")
                print()
                return
            print(f"🔹 {col_a} vs {col_b} (n={len(sub)})")
            print(sub[[col_a, col_b]].describe())
            print()

            corr = sub[[col_a, col_b]].corr().iloc[0, 1]
            print(f"   Corrélation Pearson {col_a} / {col_b} : {corr:.3f}")
            ratio_col = f"ratio_{col_a}_sur_{col_b}"
            sub[ratio_col] = sub[col_a] / sub[col_b]
            print("   Distribution du ratio :")
            print(sub[ratio_col].describe())
            print()

        # detecte vs legacy
        describe_pair("impact_detecte_pips", "phase1_pips_legacy")

        # detecte vs unified
        describe_pair("impact_detecte_pips", "impact_unified_pips")

        # legacy vs unified
        describe_pair("phase1_pips_legacy", "impact_unified_pips")

        # 5) Résumé final
        print("=" * 80)
        print("RÉSUMÉ")
        print("=" * 80)
        print()
        print(f"Nombre total de lignes analysées : {n_rows}")
        print(
            "Voir les corrélations et distributions ci-dessus pour décider "
            "quelle définition adopter comme référence."
        )
        print()

    finally:
        conn.close()


if __name__ == "__main__":
    main()
