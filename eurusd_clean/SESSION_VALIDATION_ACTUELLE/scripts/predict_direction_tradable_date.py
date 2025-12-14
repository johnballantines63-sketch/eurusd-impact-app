#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prédiction Direction pour Date Tradable - Intégration Router V6

Usage pour une date avec cluster d'events historiquement associés à moves forts :
1. Charger les actuals du cluster
2. Prédire direction avec router V6 (triggered)
3. Logger audit complet pour traçabilité

Exemple :
    python predict_direction_tradable_date.py --date 2024-11-15
"""

import sys
from pathlib import Path
import pandas as pd
import duckdb
import json
from datetime import datetime
from typing import Dict, Optional

# Ajouter le répertoire racine au path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(Path(__file__).parent))

from direction_router_v6 import (
    predict_direction_for_cluster,
    load_direction_router_dependencies,
    CORE_FAMILIES_V6,
    DEFAULT_TRIGGER_Z,
    DEFAULT_THETA
)

# ============================================================================
# CONFIGURATION
# ============================================================================

DB_PATH = Path(__file__).parent.parent.parent.parent / 'fx_impact_app' / 'data' / 'warehouse.duckdb'
ALPHA_WEIGHTS_FILE = Path(__file__).parent.parent / 'outputs' / 'alpha_weights.csv'
OUTPUT_AUDIT_DIR = Path(__file__).parent.parent / 'outputs' / 'direction_audit'

# ============================================================================
# CHARGEMENT ÉVÉNEMENTS POUR DATE
# ============================================================================

def load_events_for_tradable_date(
    date_str: str,
    conn: duckdb.DuckDBPyConnection,
    core_families: Optional[list] = None
) -> pd.DataFrame:
    """
    Charge les events core pour une date tradable (après actuals connus).
    
    Args:
        date_str: Date au format 'YYYY-MM-DD'
        conn: Connexion DuckDB
        core_families: Liste familles core (défaut: CORE_FAMILIES_V6)
    
    Returns:
        DataFrame avec colonnes ['event_key', 'actual', 'estimate', 'family', ...]
    """
    if core_families is None:
        core_families = CORE_FAMILIES_V6
    
    # Construire pattern SQL pour familles core
    # Note: On filtre par event_key patterns plutôt que par famille join
    # car la famille est calculée après
    
    query = """
    SELECT 
        e.event_key,
        e.event_title,
        e.ts_utc,
        e.country,
        e.actual,
        e.estimate,
        e.previous,
        e.forecast
    FROM events e
    WHERE DATE(e.ts_utc) = ?
      AND e.country IN ('US', 'EU', 'GB', 'DE')
      AND e.actual IS NOT NULL
      AND e.estimate IS NOT NULL
    ORDER BY e.ts_utc ASC
    """
    
    df = conn.execute(query, [date_str]).df()
    
    if len(df) == 0:
        return df
    
    # Ajouter colonne family
    from direction_router_v6 import map_event_to_family
    df['family'] = df['event_key'].apply(map_event_to_family)
    
    # Filtrer seulement core families
    df = df[df['family'].isin(core_families)].copy()
    
    return df

# ============================================================================
# PRÉDICTION DIRECTION POUR DATE TRADABLE
# ============================================================================

def predict_direction_for_date(
    date_str: str,
    trigger_z: float = DEFAULT_TRIGGER_Z,
    theta: float = DEFAULT_THETA,
    use_fallback: bool = False,
    db_path: Optional[Path] = None,
    alpha_file: Optional[Path] = None
) -> Dict:
    """
    Prédit la direction pour une date tradable après actuals connus.
    
    Args:
        date_str: Date au format 'YYYY-MM-DD'
        trigger_z: Seuil |z| pour triggered (défaut: 0.8)
        theta: Seuil neutralité (défaut: 0.05)
        use_fallback: Si True, utilise always-on si pas de trigger
        db_path: Chemin DB (défaut: DB_PATH)
        alpha_file: Chemin alpha_weights.csv (défaut: ALPHA_WEIGHTS_FILE)
    
    Returns:
        Dict avec direction, score, audit_log, métadonnées
    """
    if db_path is None:
        db_path = DB_PATH
    if alpha_file is None:
        alpha_file = ALPHA_WEIGHTS_FILE
    
    # Charger dépendances
    stats_map, alpha_map = load_direction_router_dependencies(
        db_path=db_path,
        alpha_file=alpha_file,
        horizon='1h'
    )
    
    # Charger events pour date
    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        events_df = load_events_for_tradable_date(date_str, conn)
    finally:
        conn.close()
    
    if len(events_df) == 0:
        return {
            'date': date_str,
            'direction': 'UNKNOWN',
            'score': 0.0,
            'has_trigger': False,
            'n_events': 0,
            'error': 'No core events found for date'
        }
    
    # Prédire direction avec router
    result = predict_direction_for_cluster(
        events_actuals=events_df,
        stats_map=stats_map,
        alpha_map=alpha_map,
        core_families=CORE_FAMILIES_V6,
        trigger_z=trigger_z,
        theta=theta,
        use_fallback_always_on=use_fallback
    )
    
    # Construire réponse complète
    response = {
        'date': date_str,
        'direction': result.direction,
        'score': result.score,
        'has_trigger': result.has_trigger,
        'n_events': len(events_df),
        'n_active': result.n_active,
        'trigger_z': trigger_z,
        'theta': theta,
        'audit_log': result.to_dict()['contributions'],
        'events_summary': [
            {
                'event_key': row['event_key'],
                'family': row['family'],
                'ts_utc': str(row['ts_utc']),
                'actual': float(row['actual']) if pd.notna(row['actual']) else None,
                'estimate': float(row['estimate']) if pd.notna(row['estimate']) else None
            }
            for _, row in events_df.iterrows()
        ]
    }
    
    return response

# ============================================================================
# LOGGING AUDIT
# ============================================================================

def save_audit_log(prediction_result: Dict, output_dir: Optional[Path] = None):
    """
    Sauvegarde l'audit log d'une prédiction directionnelle.
    
    Args:
        prediction_result: Résultat de predict_direction_for_date()
        output_dir: Répertoire de sortie (défaut: OUTPUT_AUDIT_DIR)
    """
    if output_dir is None:
        output_dir = OUTPUT_AUDIT_DIR
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    date_str = prediction_result['date']
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"direction_audit_{date_str}_{timestamp}.json"
    
    filepath = output_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(prediction_result, f, indent=2, ensure_ascii=False, default=str)
    
    return filepath

# ============================================================================
# MAIN / CLI
# ============================================================================

def main():
    """CLI pour prédiction direction d'une date"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Prédit direction EURUSD pour date tradable après actuals'
    )
    parser.add_argument('--date', type=str, required=True, help='Date YYYY-MM-DD')
    parser.add_argument('--trigger-z', type=float, default=DEFAULT_TRIGGER_Z, help=f'Seuil trigger |z| (défaut: {DEFAULT_TRIGGER_Z})')
    parser.add_argument('--theta', type=float, default=DEFAULT_THETA, help=f'Seuil neutralité (défaut: {DEFAULT_THETA})')
    parser.add_argument('--fallback', action='store_true', help='Utiliser always-on si pas de trigger')
    parser.add_argument('--save-audit', action='store_true', help='Sauvegarder audit log')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print(f"PRÉDICTION DIRECTION POUR DATE TRADABLE : {args.date}")
    print("=" * 80)
    print()
    
    # Prédire
    result = predict_direction_for_date(
        date_str=args.date,
        trigger_z=args.trigger_z,
        theta=args.theta,
        use_fallback=args.fallback
    )
    
    # Afficher résultats
    print(f"📊 Résultats :")
    print(f"   - Direction : {result['direction']}")
    print(f"   - Score S : {result['score']:.4f}")
    print(f"   - Trigger activé : {result['has_trigger']}")
    print(f"   - Events core : {result['n_events']}")
    print(f"   - Events actifs : {result['n_active']}")
    print()
    
    if result.get('error'):
        print(f"⚠️  Erreur : {result['error']}")
        return
    
    # Afficher contributions
    if result['audit_log']:
        print("📋 Contributions (audit) :")
        for contrib in result['audit_log']:
            trigger_mark = "🔥" if contrib['is_trigger'] else "  "
            print(f"   {trigger_mark} {contrib['family']:20s} | z={contrib['surprise_z']:7.3f} | contrib={contrib['contribution']:7.4f}")
        print()
    
    # Sauvegarder audit si demandé
    if args.save_audit:
        audit_file = save_audit_log(result)
        print(f"💾 Audit sauvegardé : {audit_file}")
        print()

if __name__ == '__main__':
    main()

