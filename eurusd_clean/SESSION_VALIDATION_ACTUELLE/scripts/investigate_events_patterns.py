#!/usr/bin/env python3
"""
Investigation Approfondie : Analyse des Événements Réels

Approche inverse :
1. Prendre les dates avec mouvements FORT/TRÈS_FORT connus
2. Analyser les événements réels (familles, surprises, scores)
3. Comparer patterns entre UP et DOWN
4. Identifier incohérences et erreurs dans nos calculs

Objectif : Comprendre d'où viennent les erreurs de prédiction
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import duckdb
from collections import defaultdict
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

DB_PATH = Path(__file__).parent.parent.parent.parent / 'fx_impact_app' / 'data' / 'warehouse.duckdb'
RESULTS_FILE = Path(__file__).parent.parent / 'outputs' / 'validation_new_dates_results.csv'

def load_events_for_date_detailed(date_str: str) -> pd.DataFrame:
    """Charge tous les détails des événements pour une date"""
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    try:
        query = """
        SELECT 
            e.event_key,
            e.event_title,
            e.ts_utc,
            e.actual,
            e.estimate,
            e.previous,
            e.forecast,
            e.country,
            ef.family,
            ef.empirical_score,
            ef.latency_median
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
        
        df = conn.execute(query, [date_str]).df()
        
        # Calculer surprise pour chaque événement
        def calculate_surprise(row):
            actual = row.get('actual')
            estimate = row.get('estimate')
            previous = row.get('previous')
            event_key = row.get('event_key', '')
            
            if pd.isna(actual):
                return None
            
            reference = estimate if pd.notna(estimate) else previous
            if pd.isna(reference) or abs(reference) < 0.001:
                return None
            
            # Détection événements "taux/pourcentage"
            rate_keywords = ['rate', 'inflation', 'yield', 'interest']
            is_rate_event = any(keyword in str(event_key).lower() for keyword in rate_keywords)
            
            if is_rate_event:
                # Pour les taux : surprise = différence en POINTS
                surprise = actual - reference
            else:
                # Pour les autres : surprise = changement relatif en %
                surprise = ((actual - reference) / abs(reference)) * 100
            
            return max(min(surprise, 100.0), -100.0)
        
        df['surprise'] = df.apply(calculate_surprise, axis=1)
        
        return df
    
    except Exception as e:
        print(f"⚠️  Erreur chargement {date_str}: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def analyze_events_by_direction():
    """Analyse les événements groupés par direction réelle"""
    print("=" * 80)
    print("INVESTIGATION APPROFONDIE : ANALYSE DES ÉVÉNEMENTS RÉELS")
    print("=" * 80)
    print()
    
    # Charger résultats validation
    df_results = pd.read_csv(RESULTS_FILE)
    
    # Filtrer FORT et TRÈS_FORT uniquement
    df_strong = df_results[df_results['movement_class'].isin(['FORT', 'TRÈS_FORT'])].copy()
    
    print(f"📊 Dates analysées : {len(df_strong)} (FORT/TRÈS_FORT uniquement)")
    print()
    
    # Grouper par direction
    events_up = []
    events_down = []
    
    for _, row in df_strong.iterrows():
        date_str = row['date']
        direction_real = row['direction_real']
        
        events_df = load_events_for_date_detailed(date_str)
        if len(events_df) == 0:
            continue
        
        # Ajouter métadonnées
        events_df['date'] = date_str
        events_df['direction_real'] = direction_real
        events_df['impact_real'] = row['impact_real']
        events_df['impact_predicted'] = row['impact_predicted']
        events_df['direction_predicted'] = row['direction_predicted']
        events_df['direction_correct'] = row['direction_correct']
        events_df['surprise_max'] = row['surprise_max']
        
        if direction_real == 'UP':
            events_up.append(events_df)
        elif direction_real == 'DOWN':
            events_down.append(events_df)
    
    df_up = pd.concat(events_up, ignore_index=True) if events_up else pd.DataFrame()
    df_down = pd.concat(events_down, ignore_index=True) if events_down else pd.DataFrame()
    
    print(f"📊 Événements UP   : {len(df_up)} événements sur {len([e for e in events_up])} dates")
    print(f"📊 Événements DOWN : {len(df_down)} événements sur {len([e for e in events_down])} dates")
    print()
    
    return df_up, df_down, df_strong

def analyze_family_patterns(df_up: pd.DataFrame, df_down: pd.DataFrame):
    """Analyse les patterns par famille d'événements"""
    print("=" * 80)
    print("1. ANALYSE PAR FAMILLE D'ÉVÉNEMENTS")
    print("=" * 80)
    print()
    
    # Familles présentes
    families_up = df_up['family'].value_counts()
    families_down = df_down['family'].value_counts()
    
    all_families = set(families_up.index) | set(families_down.index)
    
    print("📊 Distribution des familles :")
    print("-" * 80)
    print(f"{'Famille':<30} {'UP':>10} {'DOWN':>10} {'Ratio UP/DOWN':>15}")
    print("-" * 80)
    
    for family in sorted(all_families):
        count_up = families_up.get(family, 0)
        count_down = families_down.get(family, 0)
        total = count_up + count_down
        if total > 0:
            ratio = count_up / count_down if count_down > 0 else float('inf')
            print(f"{family:<30} {count_up:>10} {count_down:>10} {ratio:>15.2f}")
    print()
    
    # Analyser surprise moyenne par famille et direction
    print("📊 Surprise moyenne par famille et direction :")
    print("-" * 80)
    print(f"{'Famille':<30} {'UP (surprise)':>15} {'DOWN (surprise)':>15} {'Diff':>15}")
    print("-" * 80)
    
    for family in sorted(all_families):
        df_up_fam = df_up[df_up['family'] == family]
        df_down_fam = df_down[df_down['family'] == family]
        
        if len(df_up_fam) == 0 and len(df_down_fam) == 0:
            continue
        
        surprise_up = df_up_fam['surprise'].mean() if len(df_up_fam) > 0 else None
        surprise_down = df_down_fam['surprise'].mean() if len(df_down_fam) > 0 else None
        
        if surprise_up is not None and surprise_down is not None:
            diff = surprise_up - surprise_down
            print(f"{family:<30} {surprise_up:>15.2f} {surprise_down:>15.2f} {diff:>15.2f}")
        elif surprise_up is not None:
            print(f"{family:<30} {surprise_up:>15.2f} {'N/A':>15}")
        elif surprise_down is not None:
            print(f"{family:<30} {'N/A':>15} {surprise_down:>15.2f}")
    print()

def analyze_surprise_patterns(df_up: pd.DataFrame, df_down: pd.DataFrame):
    """Analyse les patterns de surprise"""
    print("=" * 80)
    print("2. ANALYSE DES SURPRISES")
    print("=" * 80)
    print()
    
    # Surprise globale
    print("📊 Statistiques globales de surprise :")
    print("-" * 80)
    print(f"{'Direction':<20} {'Moyenne':>12} {'Médiane':>12} {'Std':>12} {'Min':>12} {'Max':>12}")
    print("-" * 80)
    
    for direction, df_dir in [('UP', df_up), ('DOWN', df_down)]:
        surprises = df_dir['surprise'].dropna()
        if len(surprises) > 0:
            print(f"{direction:<20} {surprises.mean():>12.2f} {surprises.median():>12.2f} {surprises.std():>12.2f} {surprises.min():>12.2f} {surprises.max():>12.2f}")
    print()
    
    # Distribution surprise positive vs négative
    print("📊 Distribution surprise positive/négative :")
    print("-" * 80)
    
    for direction, df_dir in [('UP', df_up), ('DOWN', df_down)]:
        surprises = df_dir['surprise'].dropna()
        if len(surprises) > 0:
            positive = len(surprises[surprises > 0])
            negative = len(surprises[surprises < 0])
            zero = len(surprises[abs(surprises) < 0.1])
            total = len(surprises)
            
            print(f"{direction} :")
            print(f"   Positive (> 0)  : {positive:>4} ({positive/total*100:>5.1f}%)")
            print(f"   Négative (< 0)  : {negative:>4} ({negative/total*100:>5.1f}%)")
            print(f"   Nulle (≈ 0)     : {zero:>4} ({zero/total*100:>5.1f}%)")
    print()

def analyze_scores_patterns(df_up: pd.DataFrame, df_down: pd.DataFrame):
    """Analyse les patterns de scores"""
    print("=" * 80)
    print("3. ANALYSE DES SCORES EMPIRIQUES")
    print("=" * 80)
    print()
    
    # Scores globaux
    print("📊 Statistiques globales des scores :")
    print("-" * 80)
    print(f"{'Direction':<20} {'Moyenne':>12} {'Médiane':>12} {'Std':>12} {'Min':>12} {'Max':>12}")
    print("-" * 80)
    
    for direction, df_dir in [('UP', df_up), ('DOWN', df_down)]:
        scores = df_dir['empirical_score'].dropna()
        if len(scores) > 0:
            print(f"{direction:<20} {scores.mean():>12.2f} {scores.median():>12.2f} {scores.std():>12.2f} {scores.min():>12.2f} {scores.max():>12.2f}")
    print()
    
    # Relation score vs impact réel (par date)
    print("📊 Relation Score moyen vs Impact réel (par date) :")
    print("-" * 80)
    
    # Grouper par date
    for direction, df_dir in [('UP', df_up), ('DOWN', df_down)]:
        if len(df_dir) == 0:
            continue
        
        print(f"\n{direction} :")
        date_stats = df_dir.groupby('date').agg({
            'empirical_score': 'mean',
            'impact_real': 'first',
            'impact_predicted': 'first',
            'surprise_max': 'first',
            'direction_correct': 'first'
        }).reset_index()
        
        # Corrélation score vs impact
        if len(date_stats) > 1:
            corr = date_stats['empirical_score'].corr(date_stats['impact_real'])
            print(f"   Corrélation score moyen / impact réel : {corr:.3f}")
            
            # Top dates par impact
            print(f"   Top 5 dates par impact réel :")
            top_dates = date_stats.nlargest(5, 'impact_real')
            for _, row in top_dates.iterrows():
                status = "✅" if row['direction_correct'] else "❌"
                print(f"      {status} {row['date']:12s} : score={row['empirical_score']:>6.2f} | impact_réel={row['impact_real']:>6.1f} | impact_prédit={row['impact_predicted']:>6.1f} | surprise={row['surprise_max']:>6.2f}%")
    print()

def analyze_prediction_errors(df_up: pd.DataFrame, df_down: pd.DataFrame):
    """Analyse les erreurs de prédiction en détail"""
    print("=" * 80)
    print("4. ANALYSE DES ERREURS DE PRÉDICTION")
    print("=" * 80)
    print()
    
    # Erreurs UP
    df_up_errors = df_up[df_up['direction_correct'] == False].groupby('date').first().reset_index()
    df_up_correct = df_up[df_up['direction_correct'] == True].groupby('date').first().reset_index()
    
    if len(df_up_errors) > 0:
        print("📊 Dates UP avec erreur de direction :")
        print("-" * 80)
        print(f"   Nombre d'erreurs : {len(df_up_errors)}")
        
        # Analyser événements de ces dates
        print("\n   Détails des événements (dates avec erreur) :")
        for date in df_up_errors['date'].head(5):
            events_date = df_up[df_up['date'] == date]
            pred = events_date['direction_predicted'].iloc[0]
            print(f"\n      📅 {date} : Prédit={pred} (attendu UP)")
            print(f"         Familles : {', '.join(events_date['family'].unique())}")
            print(f"         Surprises : {events_date['surprise'].dropna().tolist()}")
            print(f"         Scores : {events_date['empirical_score'].dropna().tolist()}")
    
    # Erreurs DOWN
    df_down_errors = df_down[df_down['direction_correct'] == False].groupby('date').first().reset_index()
    df_down_correct = df_down[df_down['direction_correct'] == True].groupby('date').first().reset_index()
    
    if len(df_down_errors) > 0:
        print("\n📊 Dates DOWN avec erreur de direction :")
        print("-" * 80)
        print(f"   Nombre d'erreurs : {len(df_down_errors)}")
        
        # Analyser événements de ces dates
        print("\n   Détails des événements (dates avec erreur) :")
        for date in df_down_errors['date'].head(5):
            events_date = df_down[df_down['date'] == date]
            pred = events_date['direction_predicted'].iloc[0]
            print(f"\n      📅 {date} : Prédit={pred} (attendu DOWN)")
            print(f"         Familles : {', '.join(events_date['family'].unique())}")
            print(f"         Surprises : {events_date['surprise'].dropna().tolist()}")
            print(f"         Scores : {events_date['empirical_score'].dropna().tolist()}")
    
    print()

def main():
    """Fonction principale"""
    df_up, df_down, df_strong = analyze_events_by_direction()
    
    if len(df_up) == 0 and len(df_down) == 0:
        print("❌ Aucun événement trouvé")
        return
    
    analyze_family_patterns(df_up, df_down)
    analyze_surprise_patterns(df_up, df_down)
    analyze_scores_patterns(df_up, df_down)
    analyze_prediction_errors(df_up, df_down)
    
    print("=" * 80)
    print("✅ INVESTIGATION TERMINÉE")
    print("=" * 80)

if __name__ == '__main__':
    main()


