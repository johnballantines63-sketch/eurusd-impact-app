#!/usr/bin/env python3
"""
Build Pattern Truth V4 - Génération massive de vérité terrain
================================================================

Script CLI pour générer la table daily_pattern_truth_v4 depuis prices_finnhub_m1
et events_enriched_v1.

Usage:
    python research/build_pattern_truth_v4.py --db data/warehouse.duckdb --years 5
    python research/build_pattern_truth_v4.py --db data/warehouse.duckdb --start 2025-08-01 --end 2025-09-11
    python research/build_pattern_truth_v4.py --db data/warehouse.duckdb --dates "2025-08-01,2025-09-11"
    python research/build_pattern_truth_v4.py --db data/warehouse.duckdb --panel-file data/panel.csv
    python research/build_pattern_truth_v4.py --db data/warehouse.duckdb --years 5 --dry-run
"""

import sys
import argparse
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import warnings

import duckdb
import pandas as pd

# Ajouter le projet au path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from research.pattern_labeler_m1 import label_day, PatternConfig


def get_config_hash(config: PatternConfig) -> str:
    """Calcule le hash SHA256 de la configuration pour reproductibilité."""
    config_dict = {
        'window_before_minutes': config.window_before_minutes,
        'window_after_minutes': config.window_after_minutes,
        'smoothing_window': config.smoothing_window,
        'direction_window_minutes': config.direction_window_minutes,
        'retracement_threshold_pct': config.retracement_threshold_pct,
        'breakout_pips': config.breakout_pips,
        'min_swings': config.min_swings,
        'swing_threshold_pips': config.swing_threshold_pips,
        'end_reversal_pips': config.end_reversal_pips,
        'stabilization_band_pips': config.stabilization_band_pips,
        'stabilization_minutes': config.stabilization_minutes,
        'kernel_country': config.kernel_country,
        'kernel_importance_min': config.kernel_importance_min,
        'kernel_window_start_local': config.kernel_window_start_local,
        'kernel_window_end_local': config.kernel_window_end_local,
    }
    config_json = json.dumps(config_dict, sort_keys=True)
    return hashlib.sha256(config_json.encode()).hexdigest()[:16]


def get_config_json(config: PatternConfig) -> str:
    """Retourne la configuration en JSON."""
    config_dict = {
        'window_before_minutes': config.window_before_minutes,
        'window_after_minutes': config.window_after_minutes,
        'smoothing_window': config.smoothing_window,
        'direction_window_minutes': config.direction_window_minutes,
        'retracement_threshold_pct': config.retracement_threshold_pct,
        'breakout_pips': config.breakout_pips,
        'min_swings': config.min_swings,
        'swing_threshold_pips': config.swing_threshold_pips,
        'end_reversal_pips': config.end_reversal_pips,
        'stabilization_band_pips': config.stabilization_band_pips,
        'stabilization_minutes': config.stabilization_minutes,
        'kernel_country': config.kernel_country,
        'kernel_importance_min': config.kernel_importance_min,
        'kernel_window_start_local': config.kernel_window_start_local,
        'kernel_window_end_local': config.kernel_window_end_local,
    }
    return json.dumps(config_dict, indent=2)


def check_table_exists(conn: duckdb.DuckDBPyConnection, table_name: str = "daily_pattern_truth_v4") -> bool:
    """Vérifie si une table existe dans la base de données."""
    try:
        # Essayer de récupérer les infos de la table
        conn.execute(f"PRAGMA table_info('{table_name}')")
        return True
    except Exception:
        # Si PRAGMA échoue, essayer SHOW TABLES
        try:
            tables = conn.execute("SHOW TABLES").df()
            return table_name in tables['name'].values
        except Exception:
            return False


def create_table_if_not_exists(conn: duckdb.DuckDBPyConnection) -> None:
    """Crée la table daily_pattern_truth_v4 si elle n'existe pas."""
    sql_file = PROJECT_ROOT / "sql" / "create_daily_pattern_truth_v4.sql"
    
    if not sql_file.exists():
        raise FileNotFoundError(f"Fichier SQL introuvable: {sql_file}")
    
    sql_content = sql_file.read_text()
    
    # Exécuter les statements SQL (séparés par ;)
    statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]
    
    for stmt in statements:
        if stmt:
            try:
                conn.execute(stmt)
            except Exception as e:
                if "already exists" not in str(e).lower() and "does not exist" not in str(e).lower():
                    # Ignorer erreurs "already exists" mais relancer les autres
                    warnings.warn(f"⚠️  Erreur création table (peut être ignorée): {e}")


def parse_dates_string(dates_str: str) -> List[str]:
    """
    Parse une chaîne de dates séparées par des virgules.
    
    Args:
        dates_str: Chaîne de dates "YYYY-MM-DD,YYYY-MM-DD,..."
    
    Returns:
        Liste de dates (YYYY-MM-DD) normalisées et validées
    """
    dates = [d.strip() for d in dates_str.split(',') if d.strip()]
    
    # Valider et normaliser chaque date
    normalized_dates = []
    for date_str in dates:
        try:
            # Valider le format
            dt = pd.to_datetime(date_str, format='%Y-%m-%d')
            normalized_dates.append(dt.strftime('%Y-%m-%d'))
        except ValueError:
            raise ValueError(f"Format de date invalide: {date_str} (attendu: YYYY-MM-DD)")
    
    # Supprimer les doublons tout en préservant l'ordre
    seen = set()
    unique_dates = []
    for d in normalized_dates:
        if d not in seen:
            seen.add(d)
            unique_dates.append(d)
    
    return sorted(unique_dates)  # Trier chronologiquement


def read_panel_file(panel_file: str) -> List[str]:
    """
    Lit un fichier CSV contenant une colonne date_local.
    
    Args:
        panel_file: Chemin vers le fichier CSV
    
    Returns:
        Liste de dates (YYYY-MM-DD) normalisées et validées
    """
    panel_path = Path(panel_file)
    if not panel_path.is_absolute():
        panel_path = PROJECT_ROOT / panel_path
    
    if not panel_path.exists():
        raise FileNotFoundError(f"Fichier panel introuvable: {panel_path}")
    
    # Lire CSV
    try:
        df = pd.read_csv(panel_path)
    except Exception as e:
        raise ValueError(f"Impossible de lire le CSV {panel_path}: {e}")
    
    # Vérifier présence colonne date_local
    if 'date_local' not in df.columns:
        raise ValueError(
            f"Colonne 'date_local' absente du CSV {panel_path}. "
            f"Colonnes disponibles: {', '.join(df.columns)}"
        )
    
    # Extraire et normaliser dates
    dates_raw = df['date_local'].dropna().astype(str).tolist()
    normalized_dates = []
    
    for date_str in dates_raw:
        try:
            # Supporte plusieurs formats (YYYY-MM-DD, YYYY/MM/DD, etc.)
            dt = pd.to_datetime(date_str)
            normalized_dates.append(dt.strftime('%Y-%m-%d'))
        except (ValueError, TypeError):
            # Ignorer les dates invalides avec warning
            warnings.warn(f"Date ignorée (format invalide): {date_str}")
            continue
    
    # Supprimer doublons et trier
    unique_dates = sorted(list(set(normalized_dates)))
    
    if not unique_dates:
        raise ValueError(f"Aucune date valide trouvée dans {panel_path}")
    
    return unique_dates


def get_date_range(
    conn: duckdb.DuckDBPyConnection,
    dates_str: Optional[str] = None,
    panel_file: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    years: int = 5
) -> List[str]:
    """
    Détermine la plage de dates à traiter selon la priorité:
    --dates > --panel-file > --start/--end > --years
    
    Args:
        conn: Connexion DuckDB
        dates_str: Liste de dates séparées par virgules "YYYY-MM-DD,YYYY-MM-DD,..."
        panel_file: Chemin vers un CSV contenant une colonne date_local
        start_date: Date de début (YYYY-MM-DD) ou None
        end_date: Date de fin (YYYY-MM-DD) ou None
        years: Nombre d'années glissantes depuis aujourd'hui (si dates non spécifiées)
    
    Returns:
        Liste de dates (YYYY-MM-DD)
    """
    # Priorité 1: --dates
    if dates_str:
        return parse_dates_string(dates_str)
    
    # Priorité 2: --panel-file
    if panel_file:
        return read_panel_file(panel_file)
    
    # Priorité 3: --start/--end
    if start_date and end_date:
        # Plage spécifiée
        start = pd.to_datetime(start_date).date()
        end = pd.to_datetime(end_date).date()
        
        # Vérifier quelles dates ont des événements dans events_enriched_v1
        query = """
            SELECT DISTINCT date_local
            FROM events_enriched_v1
            WHERE date_local >= CAST(? AS DATE)
              AND date_local <= CAST(? AS DATE)
            ORDER BY date_local
        """
        
        df_dates = conn.execute(query, [start.isoformat(), end.isoformat()]).df()
        
        if df_dates.empty:
            return []
        
        dates = [d.strftime('%Y-%m-%d') for d in pd.to_datetime(df_dates['date_local']).dt.date]
        return dates
    
    # Priorité 4: --years (défaut)
    # Plage glissante depuis aujourd'hui
    today = datetime.now().date()
    end = today
    start = today - timedelta(days=years * 365)
    
    # Vérifier quelles dates ont des événements dans events_enriched_v1
    query = """
        SELECT DISTINCT date_local
        FROM events_enriched_v1
        WHERE date_local >= CAST(? AS DATE)
          AND date_local <= CAST(? AS DATE)
        ORDER BY date_local
    """
    
    df_dates = conn.execute(query, [start.isoformat(), end.isoformat()]).df()
    
    if df_dates.empty:
        return []
    
    dates = [d.strftime('%Y-%m-%d') for d in pd.to_datetime(df_dates['date_local']).dt.date]
    return dates


def process_date(
    conn: duckdb.DuckDBPyConnection,
    date_str: str,
    config: PatternConfig,
    config_hash: str,
    config_json: str,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Traite une date et insère (upsert via DELETE+INSERT) dans daily_pattern_truth_v4.
    Returns:
        Dict avec 'status' ('success', 'skipped', 'error'), 'reason', 'row_data'
    """
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = label_day(date_str, conn, config=config)

        # 1) Cas "pas de prix" => on skip (pas de vérité terrain possible)
        if isinstance(result, dict) and result.get("error") == "no_prices":
            return {
                "status": "skipped",
                "reason": "No M1 prices available",
                "date": date_str
            }

        # 2) Construire row_data (cas normal OU unknown)
        if isinstance(result, dict) and "error" in result and result["error"] in ("no_events", "no_t0"):
            # Unknown mais on écrit quand même une ligne (comme tu l'as défini)
            row_data = {
                "date_local": date_str,
                "timezone": "Europe/Madrid",
                "t0_local": None,
                "kernel_first_ts_local": None,
                "kernel_event_count": 0,
                "kernel_keys_json": json.dumps([]),
                "pattern": "unknown",
                "direction": 0,
                "impact_mfe_pips": 0.0,
                "mae_pips": 0.0,
                "t_end_local": None,
                "time_to_peak_min": 0,
                "retracement_pips": 0.0,
                "n_swings": 0.0,
                "n_alternances": 0.0,
                "config_hash": config_hash,
                "config_json": config_json
            }
            reason = "OK (no events, pattern=unknown)"
        elif isinstance(result, dict) and "error" in result:
            return {
                "status": "error",
                "reason": f"Unknown error: {result.get('error')}",
                "date": date_str
            }
        else:
            metrics = (result or {}).get("metrics", {}) if isinstance(result, dict) else {}

            kernel_keys = (result or {}).get("kernel_keys", []) if isinstance(result, dict) else []
            kernel_event_count = int((result or {}).get("kernel_event_count", 0) or 0) if isinstance(result, dict) else 0
            kernel_first_ts_local = (result or {}).get("kernel_first_ts_local", None) if isinstance(result, dict) else None

            # timestamps (laisser NULL si absent)
            t0_local = (result or {}).get("t0", None) if isinstance(result, dict) else None
            t_end_local = (result or {}).get("t_end", None) if isinstance(result, dict) else None

            row_data = {
                "date_local": date_str,
                "timezone": "Europe/Madrid",
                "t0_local": t0_local,
                "kernel_first_ts_local": kernel_first_ts_local,
                "kernel_event_count": kernel_event_count,
                "kernel_keys_json": json.dumps(kernel_keys),

                "pattern": (result or {}).get("pattern_label", "unknown"),
                "direction": int((result or {}).get("direction", 0) or 0),

                "impact_mfe_pips": float(metrics.get("MFE_pips", 0.0) or 0.0),
                "mae_pips": float(metrics.get("MAE_pips", 0.0) or 0.0),
                "t_end_local": t_end_local,
                "time_to_peak_min": int(round(metrics.get("time_to_peak_min", 0.0) or 0.0)),
                "retracement_pips": float(metrics.get("retracement_pips", 0.0) or 0.0),
                "n_swings": float(metrics.get("n_swings", 0.0) or 0.0),
                "n_alternances": float(metrics.get("n_alternances", 0.0) or 0.0),

                "config_hash": config_hash,
                "config_json": config_json
            }
            reason = "OK"

        # 3) Write (DELETE + INSERT)
        if not dry_run:
            conn.execute(
                "DELETE FROM daily_pattern_truth_v4 WHERE date_local = CAST(? AS DATE)",
                [row_data["date_local"]]
            )

            insert_query = """
                INSERT INTO daily_pattern_truth_v4 (
                    date_local, timezone,
                    t0_local, kernel_first_ts_local, kernel_event_count, kernel_keys_json,
                    pattern, direction,
                    impact_mfe_pips, mae_pips, t_end_local, time_to_peak_min,
                    retracement_pips, n_swings, n_alternances,
                    config_hash, config_json
                ) VALUES (
                    CAST(? AS DATE), ?,
                    ?, ?, ?, ?,
                    ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?
                )
            """

            conn.execute(insert_query, [
                row_data["date_local"],
                row_data["timezone"],

                row_data["t0_local"],
                row_data["kernel_first_ts_local"],
                row_data["kernel_event_count"],
                row_data["kernel_keys_json"],

                row_data["pattern"],
                row_data["direction"],

                row_data["impact_mfe_pips"],
                row_data["mae_pips"],
                row_data["t_end_local"],
                row_data["time_to_peak_min"],

                row_data["retracement_pips"],
                row_data["n_swings"],
                row_data["n_alternances"],

                row_data["config_hash"],
                row_data["config_json"]
            ])

        return {
            "status": "success",
            "reason": reason,
            "date": date_str,
            "pattern": row_data["pattern"],
            "row_data": row_data
        }

    except Exception as e:
        return {
            "status": "error",
            "reason": str(e),
            "date": date_str
        }


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description='Génère la table daily_pattern_truth_v4 depuis prix M1 et événements'
    )
    parser.add_argument(
        '--db',
        type=str,
        default='data/warehouse.duckdb',
        help='Chemin vers warehouse.duckdb (défaut: data/warehouse.duckdb)'
    )
    parser.add_argument(
        '--dates',
        type=str,
        help='Liste de dates séparées par virgules "YYYY-MM-DD,YYYY-MM-DD,..." (priorité 1: panel manuel)'
    )
    parser.add_argument(
        '--panel-file',
        type=str,
        help='Chemin vers un CSV contenant une colonne date_local (priorité 2)'
    )
    parser.add_argument(
        '--start',
        type=str,
        help='Date de début (YYYY-MM-DD), optionnel (priorité 3, nécessite --end)'
    )
    parser.add_argument(
        '--end',
        type=str,
        help='Date de fin (YYYY-MM-DD), optionnel (priorité 3, nécessite --start)'
    )
    parser.add_argument(
        '--years',
        type=int,
        default=5,
        help='Nombre d\'années glissantes depuis aujourd\'hui (défaut: 5, priorité 4)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Mode test (n\'écrit pas dans la DB, ouvre en read-only)'
    )
    parser.add_argument(
        '--readonly',
        action='store_true',
        help='Ouvre DuckDB en mode read-only (aucune écriture, aucune création de table)'
    )
    
    args = parser.parse_args()
    
    # Résoudre chemin DB
    db_path = Path(args.db)
    if not db_path.is_absolute():
        db_path = PROJECT_ROOT / db_path
    
    if not db_path.exists():
        print(f"❌ Base de données introuvable: {db_path}")
        sys.exit(1)
    
    # Validation des arguments selon priorité
    mode_str = "unknown"
    if args.dates:
        mode_str = f"--dates ({len(args.dates.split(','))} dates)"
    elif args.panel_file:
        mode_str = f"--panel-file ({args.panel_file})"
    elif args.start and args.end:
        mode_str = f"--start/--end ({args.start} to {args.end})"
    else:
        mode_str = f"--years ({args.years} years)"
    
    # Déterminer mode read-only
    read_only_mode = args.readonly or args.dry_run
    
    print("=" * 80)
    print("BUILD PATTERN TRUTH V4")
    print("=" * 80)
    print(f"📁 DB: {db_path}")
    print(f"🧷 DB mode: {'READONLY' if read_only_mode else 'WRITE'}")
    print(f"📅 Mode: {mode_str}")
    print(f"🧪 Dry-run: {args.dry_run}")
    print("=" * 80)
    print()
    
    # Connexion DB
    conn = duckdb.connect(str(db_path), read_only=read_only_mode)
    
    try:
        # Gestion table selon mode
        if read_only_mode:
            # Mode read-only: vérifier que la table existe
            print("📋 Vérification présence table...")
            if not check_table_exists(conn):
                print(f"❌ Table 'daily_pattern_truth_v4' introuvable en mode read-only")
                print(f"   Veuillez créer la table d'abord ou utiliser sans --readonly/--dry-run")
                sys.exit(1)
            print("✅ Table existe")
            print()
        else:
            # Mode write: créer table si nécessaire
            print("📋 Création table si nécessaire...")
            create_table_if_not_exists(conn)
            print("✅ Table OK")
            print()
        
        # Configuration
        config = PatternConfig()
        config_hash = get_config_hash(config)
        config_json = get_config_json(config)
        
        print(f"⚙️  Configuration hash: {config_hash}")
        print()
        
        # Obtenir plage de dates (avec priorité)
        print("📅 Détermination plage de dates...")
        try:
            dates = get_date_range(
                conn,
                dates_str=args.dates,
                panel_file=args.panel_file,
                start_date=args.start,
                end_date=args.end,
                years=args.years
            )
            print(f"✅ {len(dates)} dates à traiter")
            if len(dates) > 0:
                print(f"   Première: {dates[0]}")
                print(f"   Dernière: {dates[-1]}")
        except (ValueError, FileNotFoundError) as e:
            print(f"❌ Erreur détermination dates: {e}")
            sys.exit(1)
        print()
        
        if len(dates) == 0:
            print("⚠️  Aucune date à traiter")
            return
        
        # Traiter chaque date
        print("🔄 Traitement des dates...")
        print()
        
        stats = {
            'total': len(dates),
            'success': 0,
            'skipped': 0,
            'error': 0
        }
        
        # Transaction pour performance (uniquement en mode write)
        if not read_only_mode:
            conn.execute("BEGIN TRANSACTION")
        
        try:
            for i, date_str in enumerate(dates, 1):
                if i % 10 == 0:
                    print(f"  Traité {i}/{len(dates)} dates...", end='\r')
                
                # En mode read-only, forcer dry_run=True pour éviter DELETE/INSERT
                result = process_date(conn, date_str, config, config_hash, config_json, dry_run=read_only_mode)
                
                stats[result['status']] += 1
                
                if result['status'] == 'error' and i <= 5:
                    # Afficher les 5 premières erreurs
                    print(f"\n⚠️  Erreur {date_str}: {result['reason']}")
            
            # Commit transaction (uniquement en mode write)
            if not read_only_mode:
                conn.execute("COMMIT")
                print(f"\n✅ Transaction commitée")
            else:
                print(f"\n🧪 Mode read-only: aucune écriture effectuée")
        
        except Exception as e:
            if not read_only_mode:
                conn.execute("ROLLBACK")
                print(f"\n❌ Erreur transaction, rollback: {e}")
            else:
                print(f"\n❌ Erreur: {e}")
            raise
        
        # Afficher stats finales
        print()
        print("=" * 80)
        print("📊 STATISTIQUES FINALES")
        print("=" * 80)
        print(f"Total dates:     {stats['total']}")
        print(f"✅ Success:      {stats['success']}")
        print(f"⏭️  Skipped:      {stats['skipped']}")
        print(f"❌ Erreurs:       {stats['error']}")
        print("=" * 80)
        
        # Vérifier résultats
        if not args.dry_run and stats['success'] > 0:
            count_query = "SELECT COUNT(*) FROM daily_pattern_truth_v4"
            count = conn.execute(count_query).fetchone()[0]
            print(f"\n📋 Total lignes dans daily_pattern_truth_v4: {count}")
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()

