#!/usr/bin/env python3
"""
Mesure Accuracy Directionnelle Actuelle
========================================

Objectif :
- Analyser les résultats de validation existants
- Mesurer l'accuracy directionnelle actuelle
- Identifier les cas où la direction est incorrecte

Date : 2025-12-07
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src' / 'core'))

from src.core.formulas_validated import get_event_direction

# Chemin vers résultats de validation
VALIDATION_RESULTS_FILE = Path(__file__).parent.parent / 'outputs' / 'validation_new_dates_results.csv'
DB_PATH = Path('../fx_impact_app/data/warehouse.duckdb')


def load_validation_results() -> pd.DataFrame:
    """Charge les résultats de validation existants"""
    if not VALIDATION_RESULTS_FILE.exists():
        print(f"❌ Fichier de résultats introuvable : {VALIDATION_RESULTS_FILE}")
        print("   Lancez d'abord validate_on_new_dates.py")
        return pd.DataFrame()
    
    df = pd.read_csv(VALIDATION_RESULTS_FILE)
    return df


def calculate_direction_for_date(date_str: str) -> str:
    """
    Calcule la direction prédite pour une date en utilisant get_event_direction()
    """
    import duckdb
    from datetime import datetime
    
    if not DB_PATH.exists():
        return 'UNKNOWN'
    
    try:
        conn = duckdb.connect(str(DB_PATH), read_only=True)
        
        # Charger événements pour cette date
        query = """
        SELECT 
            e.event_key,
            e.actual,
            e.estimate,
            e.previous,
            ef.family
        FROM events e
        LEFT JOIN event_families ef 
            ON e.event_key = ef.event_key 
            AND e.country = ef.country
        WHERE DATE(e.ts_utc) = ?
            AND e.country = 'US'
            AND ef.empirical_score IS NOT NULL
            AND ef.empirical_score > 40
        ORDER BY e.ts_utc
        """
        
        events_df = conn.execute(query, [date_str]).df()
        conn.close()
        
        if events_df.empty:
            return 'UNKNOWN'
        
        # Calculer direction pour chaque événement
        directions = []
        for _, row in events_df.iterrows():
            family = row.get('family', 'Unknown')
            actual = row.get('actual')
            estimate = row.get('estimate')
            
            if pd.notna(actual) and pd.notna(estimate):
                surprise = actual - estimate
            else:
                surprise = 0.0
            
            direction = get_event_direction(family=family, surprise=surprise)
            directions.append(direction)
        
        # Direction dominante
        direction_sum = sum(directions)
        if direction_sum > 0:
            return 'UP'
        elif direction_sum < 0:
            return 'DOWN'
        else:
            return 'UNKNOWN'
    
    except Exception as e:
        print(f"⚠️  Erreur calcul direction {date_str}: {e}")
        return 'UNKNOWN'


def analyze_direction_accuracy():
    """
    Analyse l'accuracy directionnelle des résultats de validation
    """
    print("=" * 80)
    print("MESURE ACCURACY DIRECTIONNELLE")
    print("=" * 80)
    print()
    
    # Charger résultats
    df = load_validation_results()
    
    if df.empty:
        print("❌ Aucun résultat à analyser")
        return
    
    print(f"✅ {len(df)} résultats chargés")
    print()
    
    # Vérifier si direction_predicted existe déjà
    if 'direction_predicted' in df.columns:
        print("✅ Colonne 'direction_predicted' déjà présente dans les résultats")
        print()
    else:
        print("📊 Calcul des directions prédites...")
        print("   (Cela peut prendre quelques minutes...)")
        print()
        
        # Calculer direction pour chaque date
        directions_predicted = []
        for idx, row in df.iterrows():
            date_str = row['date']
            direction = calculate_direction_for_date(date_str)
            directions_predicted.append(direction)
            
            if (idx + 1) % 10 == 0:
                print(f"   Traité {idx + 1}/{len(df)} dates...")
        
        df['direction_predicted'] = directions_predicted
        print(f"✅ Directions calculées pour {len(df)} dates")
        print()
    
    # Vérifier si direction_real existe
    if 'direction_real' not in df.columns:
        print("⚠️  Colonne 'direction_real' manquante")
        print("   Relancez validate_on_new_dates.py pour obtenir les directions réelles")
        return
    
    # Calculer accuracy
    df['direction_correct'] = df['direction_predicted'] == df['direction_real']
    accuracy = df['direction_correct'].mean() * 100
    
    print("=" * 80)
    print("📊 RÉSULTATS ACCURACY DIRECTIONNELLE")
    print("=" * 80)
    print()
    
    print(f"{'Métrique':<40} {'Valeur':<20}")
    print("-" * 60)
    print(f"{'Nombre de dates analysées':<40} {len(df):<20}")
    print(f"{'Accuracy directionnelle':<40} {accuracy:>18.1f}%")
    print(f"{'Directions correctes':<40} {df['direction_correct'].sum():>18d}")
    print(f"{'Directions incorrectes':<40} {(~df['direction_correct']).sum():>18d}")
    print()
    
    # Matrice de confusion
    print("📊 Matrice de Confusion :")
    print()
    confusion = pd.crosstab(
        df['direction_real'],
        df['direction_predicted'],
        margins=True
    )
    print(confusion)
    print()
    
    # Détails par direction réelle
    print("📊 Détails par Direction Réelle :")
    print()
    for direction in ['UP', 'DOWN']:
        df_dir = df[df['direction_real'] == direction]
        if len(df_dir) > 0:
            correct = df_dir['direction_correct'].sum()
            total = len(df_dir)
            dir_accuracy = (correct / total) * 100 if total > 0 else 0.0
            mae = df_dir['error_abs'].mean() if 'error_abs' in df_dir.columns else 0.0
            
            print(f"   {direction:5s} réel ({total:3d} cas) :")
            print(f"      - Accuracy : {dir_accuracy:5.1f}% ({correct}/{total})")
            print(f"      - MAE moyen : {mae:5.1f} pips")
    print()
    
    # Cas avec direction incorrecte
    df_wrong = df[~df['direction_correct']]
    if len(df_wrong) > 0:
        print("⚠️  Cas avec Direction Incorrecte :")
        print()
        print(df_wrong[['date', 'direction_real', 'direction_predicted', 'impact_real', 'impact_predicted', 'error_abs']].to_string(index=False))
        print()
    
    # Sauvegarder résultats enrichis
    output_file = Path(__file__).parent.parent / 'outputs' / 'validation_direction_accuracy.csv'
    df.to_csv(output_file, index=False)
    print(f"💾 Résultats sauvegardés : {output_file}")
    print()
    
    print("=" * 80)
    print("✅ ANALYSE TERMINÉE")
    print("=" * 80)


if __name__ == '__main__':
    analyze_direction_accuracy()


