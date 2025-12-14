"""
Analyse Relation : Scores Individuels → Surprises → Score Noyau Dur → Impact

Objectif : 
1. Calculer score global du noyau dur (combinaison scores individuels + surprises)
2. Analyser relation récurrente entre scores, surprises et impacts réels
3. Identifier patterns pour améliorer prédictions

Date : 2025-12-06
Référence : Données Finnhub validées
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import duckdb
from datetime import datetime
import pytz
from typing import Dict, List, Optional
import re

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from config import DB_PATH
from scripts.run_pipeline_complete import PipelineExecutor
from core.formulas_validated import calculate_adjusted_empirical_score, get_event_direction

TZ_BERN = pytz.timezone('Europe/Zurich')

# Patterns pour exclure événements sans estimate
EVENTS_WITHOUT_ESTIMATE_PATTERNS = [
    r'(?i)(speech|discours|statement|remarks|testimony|testifies)',
    r'(?i)(fed.*speech|ecb.*speech|boe.*speech)',
    r'(?i)(press conference|conference de presse)',
    r'(?i)(meeting minutes|compte-rendu)',
    r'(?i)(beige book|livre beige)',
]

def is_event_without_estimate(event: pd.Series) -> bool:
    """Vérifie si un événement ne peut pas avoir de surprise calculée"""
    event_key = str(event.get('event_key', '') or '')
    event_title = str(event.get('event_title', '') or '')
    estimate = event.get('estimate')
    forecast = event.get('forecast')
    previous = event.get('previous')
    
    has_valid_estimate = (
        (estimate is not None and not pd.isna(estimate) and estimate != 'nan') or
        (forecast is not None and not pd.isna(forecast) and forecast != 'nan') or
        (previous is not None and not pd.isna(previous) and previous != 'nan')
    )
    
    if not has_valid_estimate:
        return True
    
    text_to_check = f"{event_key} {event_title}".lower()
    for pattern in EVENTS_WITHOUT_ESTIMATE_PATTERNS:
        if re.search(pattern, text_to_check):
            return True
    
    return False

def calculate_core_score_global(
    core_events: pd.DataFrame,
    method: str = 'weighted_sum'
) -> Dict:
    """
    Calcule le score global du noyau dur
    
    Méthodes possibles :
    1. 'weighted_sum' : Somme pondérée (score × importance_n)
    2. 'weighted_avg' : Moyenne pondérée
    3. 'vectorial_sum' : Somme vectorielle (score × direction × surprise)
    4. 'max_score' : Score maximum
    5. 'adjusted_sum' : Somme avec ajustement surprise
    """
    if core_events.empty:
        return {
            'score_global': 0.0,
            'method': method,
            'n_events': 0,
            'details': {}
        }
    
    scores_individuels = []
    surprises_individuelles = []
    directions_individuelles = []
    importance_weights = []
    
    for _, event in core_events.iterrows():
        base_score = event.get('empirical_score', 0.0)
        if pd.isna(base_score) or base_score == 0:
            continue
        
        importance_n = event.get('importance_n', 1)
        actual = event.get('actual')
        estimate = event.get('estimate') or event.get('forecast') or event.get('previous')
        
        # Calculer surprise (seulement si estimate valide)
        surprise = None
        if actual is not None and estimate is not None and not pd.isna(estimate) and estimate != 0:
            surprise = (actual - estimate) / abs(estimate) * 100
        elif actual is not None and estimate is not None and not pd.isna(estimate):
            surprise = actual - estimate
        
        # Si pas de surprise calculable, exclure de l'analyse
        if surprise is None:
            continue
        
        # Calculer direction
        event_key = event.get('event_key') or event.get('event_title') or 'Unknown'
        family = event.get('family') or 'Unknown'
        direction = get_event_direction(family, surprise) if surprise != 0 and surprise is not None else 1
        
        # Ajuster score selon surprise (seulement si surprise valide)
        if surprise is not None:
            adjusted_score = calculate_adjusted_empirical_score(
                base_empirical_score=base_score,
                surprise_pct=abs(surprise)
            )
        else:
            adjusted_score = base_score
        
        scores_individuels.append({
            'base_score': base_score,
            'adjusted_score': adjusted_score,
            'surprise': surprise,
            'direction': direction,
            'importance_n': importance_n
        })
        
        surprises_individuelles.append(surprise)
        directions_individuelles.append(direction)
        importance_weights.append(importance_n)
    
    if not scores_individuels:
        return {
            'score_global': 0.0,
            'method': method,
            'n_events': 0,
            'details': {}
        }
    
    # Calculer selon méthode
    if method == 'weighted_sum':
        # Somme pondérée : sum(score × importance_n)
        score_global = sum(s['base_score'] * s['importance_n'] for s in scores_individuels)
        
    elif method == 'weighted_avg':
        # Moyenne pondérée : sum(score × importance_n) / sum(importance_n)
        total_weighted = sum(s['base_score'] * s['importance_n'] for s in scores_individuels)
        total_weights = sum(s['importance_n'] for s in scores_individuels)
        score_global = total_weighted / total_weights if total_weights > 0 else 0.0
        
    elif method == 'vectorial_sum':
        # Somme vectorielle : sum(score × direction × surprise_factor)
        # surprise_factor = 1 + (abs(surprise) / 100) pour amplifier
        score_global = sum(
            s['base_score'] * s['direction'] * (1.0 + abs(s['surprise']) / 100.0)
            for s in scores_individuels
        )
        
    elif method == 'max_score':
        # Score maximum
        score_global = max(s['base_score'] for s in scores_individuels)
        
    elif method == 'adjusted_sum':
        # Somme des scores ajustés selon surprise
        score_global = sum(s['adjusted_score'] for s in scores_individuels)
        
    else:
        # Par défaut : moyenne simple
        score_global = np.mean([s['base_score'] for s in scores_individuels])
    
    # Surprise nette (somme vectorielle) - exclure NaN
    surprises_valid = [s for s in surprises_individuelles if s is not None and not pd.isna(s)]
    surprise_net = sum(surprises_valid) if surprises_valid else 0.0
    surprise_abs = abs(surprise_net) if surprises_valid else 0.0
    
    # Direction nette
    direction_net = 1 if surprise_net >= 0 else -1
    
    return {
        'score_global': score_global,
        'method': method,
        'n_events': len(scores_individuels),
        'surprise_net': surprise_net,
        'surprise_abs': surprise_abs,
        'direction_net': direction_net,
        'scores_individuels': scores_individuels,
        'avg_base_score': np.mean([s['base_score'] for s in scores_individuels]),
        'avg_adjusted_score': np.mean([s['adjusted_score'] for s in scores_individuels]),
        'max_surprise': max([abs(s['surprise']) for s in scores_individuels]) if scores_individuels else 0.0
    }

def analyze_date_detailed(date_str: str) -> Dict:
    """Analyse détaillée d'une date avec calcul score global noyau dur"""
    
    print(f"\n{'='*100}")
    print(f"ANALYSE DÉTAILLÉE : {date_str}")
    print(f"{'='*100}")
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    executor = PipelineExecutor(db_path=str(DB_PATH), verbose=False)
    
    # Exécuter pipeline
    result = executor.execute_complete_pipeline(
        date_str,
        window_minutes=30,
        support_threshold=0.8,
        jaccard_threshold=0.6,
        years_lookback=5
    )
    
    if not result or not result.get('success'):
        print("❌ Pipeline échoué")
        conn.close()
        return {}
    
    # Extraire informations
    results_dict = result.get('results', {})
    etape3_cluster_info = results_dict.get('etape3_cluster_info', {})
    main_cluster = etape3_cluster_info.get('cluster', {})
    core_type = etape3_cluster_info.get('core_type', 'UNKNOWN')
    country = etape3_cluster_info.get('country', 'US')
    
    cluster_events = main_cluster.get('events', pd.DataFrame())
    if cluster_events.empty:
        print("❌ Cluster vide")
        conn.close()
        return {}
    
    # Identifier événements core
    core_events_list = etape3_cluster_info.get('core_events', [])
    
    # Filtrer événements core avec estimate
    core_events_df = pd.DataFrame()
    for _, event in cluster_events.iterrows():
        event_key = str(event.get('event_key', '') or '')
        event_key_norm = event_key.lower().strip()
        country_event = event.get('country', '')
        importance = event.get('importance_n', 3)
        event_id = f"{event_key_norm}_{country_event}_{importance}"
        
        if event_id in core_events_list and not is_event_without_estimate(event):
            core_events_df = pd.concat([core_events_df, event.to_frame().T], ignore_index=True)
    
    if core_events_df.empty:
        print("❌ Aucun événement core avec estimate")
        conn.close()
        return {}
    
    # Mesurer impact réel
    date_dt = pd.to_datetime(date_str)
    window_start = TZ_BERN.localize(datetime.combine(date_dt.date(), datetime.min.time().replace(hour=14, minute=0)))
    window_end = TZ_BERN.localize(datetime.combine(date_dt.date(), datetime.min.time().replace(hour=20, minute=0)))
    
    query_prices = f"""
    SELECT datetime, open, high, low, close
    FROM prices_finnhub_m1
    WHERE DATE(datetime) = '{date_str}'
      AND datetime >= '{window_start.strftime('%Y-%m-%d %H:%M:%S')}'
      AND datetime <= '{window_end.strftime('%Y-%m-%d %H:%M:%S')}'
    ORDER BY datetime ASC
    """
    
    df_prices = conn.execute(query_prices).df()
    impact_real = None
    
    if not df_prices.empty:
        df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
        df_prices = df_prices.set_index('datetime')
        
        baseline_time = TZ_BERN.localize(datetime.combine(date_dt.date(), datetime.min.time().replace(hour=14, minute=30)))
        prices_at_baseline = df_prices[df_prices.index >= baseline_time]
        
        if not prices_at_baseline.empty:
            baseline_price = prices_at_baseline.iloc[0]['open']
            max_high = prices_at_baseline['high'].max()
            min_low = prices_at_baseline['low'].min()
            impact_up = (max_high - baseline_price) * 10000
            impact_down = (baseline_price - min_low) * 10000
            impact_real = max(impact_up, impact_down)
    
    # Calculer scores globaux avec différentes méthodes
    print("ÉVÉNEMENTS CORE (avec estimate) :")
    print("-"*100)
    print()
    
    print(f"{'Event Key':<40} {'Score':<8} {'Imp':<4} {'Estimate':<12} {'Actual':<12} {'Surprise':<10} {'Dir':<4} {'Adj Score':<10}")
    print("-"*100)
    
    for _, event in core_events_df.iterrows():
        event_key = str(event.get('event_key', 'Unknown'))[:40]
        base_score = event.get('empirical_score', 0.0)
        importance = event.get('importance_n', 1)
        estimate = event.get('estimate') or event.get('forecast') or event.get('previous')
        actual = event.get('actual')
        
        # Calculer surprise (seulement si estimate valide)
        surprise = None
        if actual is not None and estimate is not None and not pd.isna(estimate) and estimate != 0:
            surprise = (actual - estimate) / abs(estimate) * 100
        
        event_key_clean = event.get('event_key') or 'Unknown'
        family = event.get('family') or 'Unknown'
        direction = get_event_direction(family, surprise) if surprise is not None and surprise != 0 else 1
        
        # Ajuster score selon surprise (seulement si surprise valide)
        if surprise is not None:
            adjusted_score = calculate_adjusted_empirical_score(
                base_empirical_score=base_score,
                surprise_pct=abs(surprise)
            )
        else:
            adjusted_score = base_score
        
        estimate_str = f"{estimate:.2f}" if estimate is not None and not pd.isna(estimate) else "NaN"
        actual_str = f"{actual:.2f}" if actual is not None and not pd.isna(actual) else "NaN"
        surprise_str = f"{surprise:+.1f}%" if surprise is not None and surprise != 0 else ("0.0%" if surprise is not None else "NaN")
        dir_str = "UP" if direction > 0 else "DOWN"
        
        print(f"{event_key:<40} {base_score:>7.1f} {importance:<4} {estimate_str:<12} {actual_str:<12} {surprise_str:<10} {dir_str:<4} {adjusted_score:>9.1f}")
    
    print()
    
    # Calculer scores globaux
    print("CALCUL SCORES GLOBAUX NOYAU DUR (différentes méthodes) :")
    print("-"*100)
    print()
    
    methods = ['weighted_sum', 'weighted_avg', 'vectorial_sum', 'max_score', 'adjusted_sum']
    scores_globaux = {}
    
    for method in methods:
        score_info = calculate_core_score_global(core_events_df, method=method)
        scores_globaux[method] = score_info
        
        print(f"{method.upper():<20} : {score_info['score_global']:>8.2f}")
        print(f"   N événements : {score_info['n_events']}")
        print(f"   Surprise nette : {score_info['surprise_net']:+.2f}%")
        print(f"   Surprise abs : {score_info['surprise_abs']:.2f}%")
        print(f"   Direction nette : {'UP' if score_info['direction_net'] > 0 else 'DOWN'}")
        print(f"   Score moyen base : {score_info['avg_base_score']:.2f}")
        print(f"   Score moyen ajusté : {score_info['avg_adjusted_score']:.2f}")
        print()
    
    # Récupérer score core_scores depuis DB
    query_core_score = """
    SELECT empirical_score, avg_impact_pips, p80_impact_pips, sample_size
    FROM core_scores
    WHERE core_type = ? AND country = ?
    """
    
    core_score_db = conn.execute(query_core_score, [core_type, country]).fetchone()
    core_score_value = core_score_db[0] if core_score_db else None
    
    # Afficher comparaison
    print("COMPARAISON SCORES :")
    print("-"*100)
    print()
    
    print(f"Score core_scores (DB) : {core_score_value:.2f}" if core_score_value else "Score core_scores (DB) : N/A")
    print(f"Score global (weighted_sum) : {scores_globaux['weighted_sum']['score_global']:.2f}")
    print(f"Score global (weighted_avg) : {scores_globaux['weighted_avg']['score_global']:.2f}")
    print(f"Score global (adjusted_sum) : {scores_globaux['adjusted_sum']['score_global']:.2f}")
    print()
    
    if impact_real:
        print(f"IMPACT RÉEL MESURÉ : {impact_real:.2f} pips")
        print()
        
        # Analyser relation score → impact
        print("RELATION SCORE → IMPACT :")
        print("-"*100)
        print()
        
        if core_score_value:
            ratio_core_score = impact_real / core_score_value if core_score_value > 0 else 0
            print(f"Impact réel / Score core_scores : {ratio_core_score:.3f}")
        
        for method, score_info in scores_globaux.items():
            if score_info['score_global'] > 0:
                ratio = impact_real / score_info['score_global']
                print(f"Impact réel / Score {method} : {ratio:.3f}")
        print()
    
    conn.close()
    
    return {
        'date': date_str,
        'core_type': core_type,
        'country': country,
        'n_core_events': len(core_events_df),
        'scores_globaux': scores_globaux,
        'core_score_db': core_score_value,
        'impact_real': impact_real,
        'surprise_net': scores_globaux['weighted_sum']['surprise_net'],
        'surprise_abs': scores_globaux['weighted_sum']['surprise_abs']
    }

def analyze_multiple_dates():
    """Analyse plusieurs dates pour trouver patterns récurrents"""
    
    print("="*100)
    print("ANALYSE RELATION SCORES → SURPRISES → IMPACTS")
    print("="*100)
    print()
    print("Objectif : Identifier des patterns récurrents pour améliorer prédictions")
    print()
    
    TEST_DATES = [
        '2025-09-11',  # CPI
        '2025-05-29',  # JOBLESS_PCE
        '2025-08-01',  # NFP ou CPI
        '2025-11-20',  # NFP ou CPI
    ]
    
    all_results = []
    
    for date_str in TEST_DATES:
        result = analyze_date_detailed(date_str)
        if result:
            all_results.append(result)
    
    # Analyse globale
    print()
    print("="*100)
    print("ANALYSE GLOBALE - PATTERNS RÉCURRENTS")
    print("="*100)
    print()
    
    if not all_results:
        print("❌ Aucun résultat à analyser")
        return
    
    df_results = pd.DataFrame(all_results)
    
    # Corrélations
    print("CORRÉLATIONS :")
    print("-"*100)
    print()
    
    # Score core_scores vs Impact réel
    if 'core_score_db' in df_results.columns and 'impact_real' in df_results.columns:
        valid_data = df_results[df_results['core_score_db'].notna() & df_results['impact_real'].notna()]
        if len(valid_data) > 1:
            correlation = valid_data['core_score_db'].corr(valid_data['impact_real'])
            print(f"Corrélation Score core_scores ↔ Impact réel : {correlation:.3f}")
    
    # Surprise abs vs Impact réel
    if 'surprise_abs' in df_results.columns and 'impact_real' in df_results.columns:
        valid_data = df_results[df_results['surprise_abs'].notna() & df_results['impact_real'].notna()]
        if len(valid_data) > 1:
            correlation = valid_data['surprise_abs'].corr(valid_data['impact_real'])
            print(f"Corrélation Surprise abs ↔ Impact réel : {correlation:.3f}")
    
    # Score global (weighted_sum) vs Impact réel
    if 'scores_globaux' in df_results.columns and 'impact_real' in df_results.columns:
        scores_weighted = [r['scores_globaux']['weighted_sum']['score_global'] for r in all_results if r.get('scores_globaux')]
        impacts = [r['impact_real'] for r in all_results if r.get('impact_real')]
        if len(scores_weighted) == len(impacts) and len(scores_weighted) > 1:
            correlation = pd.Series(scores_weighted).corr(pd.Series(impacts))
            print(f"Corrélation Score global (weighted_sum) ↔ Impact réel : {correlation:.3f}")
    
    print()
    
    # Tableau récapitulatif
    print("TABLEAU RÉCAPITULATIF :")
    print("-"*100)
    print()
    
    print(f"{'Date':<12} {'Core Type':<15} {'Score DB':<10} {'Score Global':<12} {'Surprise':<10} {'Impact Réel':<12} {'Ratio':<10}")
    print("-"*100)
    
    for result in all_results:
        date_str = result['date']
        core_type = result['core_type']
        core_score_db = result.get('core_score_db', 0.0) or 0.0
        score_global = result['scores_globaux']['weighted_sum']['score_global']
        surprise_abs = result['surprise_abs']
        impact_real = result.get('impact_real', 0.0) or 0.0
        
        ratio = impact_real / score_global if score_global > 0 else 0.0
        
        print(f"{date_str:<12} {core_type:<15} {core_score_db:>9.2f} {score_global:>11.2f} {surprise_abs:>9.2f}% {impact_real:>11.2f} {ratio:>9.3f}")
    
    print()
    
    # Sauvegarder résultats
    output_file = PROJECT_ROOT / 'SESSION_VALIDATION_ACTUELLE' / 'outputs' / 'analyse_relation_scores_surprises_impact.csv'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Préparer données pour CSV
    csv_data = []
    for result in all_results:
        csv_data.append({
            'date': result['date'],
            'core_type': result['core_type'],
            'country': result['country'],
            'n_core_events': result['n_core_events'],
            'core_score_db': result.get('core_score_db', None),
            'score_global_weighted_sum': result['scores_globaux']['weighted_sum']['score_global'],
            'score_global_weighted_avg': result['scores_globaux']['weighted_avg']['score_global'],
            'score_global_adjusted_sum': result['scores_globaux']['adjusted_sum']['score_global'],
            'surprise_net': result['surprise_net'],
            'surprise_abs': result['surprise_abs'],
            'impact_real': result.get('impact_real', None)
        })
    
    df_csv = pd.DataFrame(csv_data)
    df_csv.to_csv(output_file, index=False)
    
    print(f"💾 Résultats sauvegardés : {output_file}")
    print()
    
    print("="*100)
    print("ANALYSE TERMINÉE")
    print("="*100)

if __name__ == '__main__':
    analyze_multiple_dates()

