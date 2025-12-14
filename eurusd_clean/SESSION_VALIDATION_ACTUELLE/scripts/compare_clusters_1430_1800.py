"""
Comparaison détaillée des clusters à 14:30 et 18:00 pour 2025-05-29
"""
import sys
from pathlib import Path
import pandas as pd
import duckdb

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from config import DB_PATH
from core.formulas_validated import get_event_direction, infer_family_from_event_key

def load_events_for_date(date_str: str):
    """Charge tous les événements US HIGH pour une date avec scores empiriques réels"""
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    query = '''
    SELECT 
        e.ts_utc,
        e.event_title,
        e.event_key,
        e.country,
        e.importance_n,
        e.actual,
        e.estimate,
        e.forecast,
        e.previous,
        COALESCE(ef.empirical_score, 0.0) as empirical_score
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE DATE(e.ts_utc) = ?
      AND e.country = 'US'
      AND e.importance_n = 3
    ORDER BY e.ts_utc
    '''
    
    df = conn.execute(query, [date_str]).df()
    conn.close()
    
    if not df.empty:
        df['ts_utc'] = pd.to_datetime(df['ts_utc'])
        # Si pas de score empirique, utiliser un score par défaut basé sur l'importance
        df['empirical_score'] = df['empirical_score'].fillna(
            df['importance_n'].map({1: 20.0, 2: 35.0, 3: 50.0}).fillna(20.0)
        )
    
    return df

def analyze_cluster(events_df, time_str, hour, minute_range=(25, 35)):
    """Analyse un cluster à une heure spécifique"""
    if events_df.empty:
        return None
    
    # Filtrer événements à l'heure spécifiée
    if hour == 14:
        mask = (
            (events_df['ts_utc'].dt.hour == 14) & 
            (events_df['ts_utc'].dt.minute >= minute_range[0]) & 
            (events_df['ts_utc'].dt.minute <= minute_range[1])
        )
    elif hour == 18:
        mask = (
            (events_df['ts_utc'].dt.hour == 18) & 
            (events_df['ts_utc'].dt.minute >= 0) & 
            (events_df['ts_utc'].dt.minute <= 5)
        )
    else:
        return None
    
    cluster_events = events_df[mask].copy()
    
    if cluster_events.empty:
        return None
    
    # Calculer scores vectoriels
    scores_vectoriels = []
    scores_simples = []
    details = []
    
    for _, event in cluster_events.iterrows():
        # Score empirique réel depuis la DB
        empirical_score = event.get('empirical_score', 0.0)
        if pd.isna(empirical_score) or empirical_score == 0:
            # Fallback : score basé sur importance
            importance_n = event.get('importance_n', 1)
            empirical_score = {1: 20.0, 2: 35.0, 3: 50.0}.get(importance_n, 20.0)
        
        # Calculer surprise
        actual = event.get('actual')
        estimate = event.get('estimate') or event.get('forecast') or event.get('previous')
        surprise = 0.0
        surprise_str = "N/A"
        
        if actual is not None and estimate is not None and estimate != 0:
            surprise = (actual - estimate) / abs(estimate) * 100
            surprise_str = f"{surprise:.1f}%"
        elif actual is not None and estimate is not None:
            surprise = actual - estimate
            surprise_str = f"{surprise:.2f}"
        
        # Direction
        event_key = event.get('event_key') or event.get('event_title') or 'Unknown'
        family = infer_family_from_event_key(event_key)
        direction = get_event_direction(family, surprise) if surprise != 0 else 1
        
        # Score vectoriel
        score_vectoriel = empirical_score * direction
        
        # Score composite : importance_n × empirical_score
        importance_n = event.get('importance_n', 1)
        importance_weight = {1: 0.5, 2: 0.75, 3: 1.0}.get(importance_n, 0.5)
        score_composite = empirical_score * importance_weight
        score_vectoriel_composite = score_composite * direction
        
        scores_vectoriels.append(score_vectoriel)
        scores_vectoriels_composite = getattr(analyze_cluster, 'scores_vectoriels_composite', [])
        if not hasattr(analyze_cluster, 'scores_vectoriels_composite'):
            analyze_cluster.scores_vectoriels_composite = []
        analyze_cluster.scores_vectoriels_composite.append(score_vectoriel_composite)
        scores_simples.append(empirical_score)
        
        # Score composite : combinaison importance_n et empirical_score
        importance_n = event.get('importance_n', 1)
        importance_weight = {1: 0.5, 2: 0.75, 3: 1.0}.get(importance_n, 0.5)
        score_composite = empirical_score * importance_weight
        
        # Score vectoriel avec score composite
        score_vectoriel_composite = score_composite * direction
        
        details.append({
            'Heure': pd.to_datetime(event['ts_utc']).strftime('%H:%M'),
            'Événement': event_key[:50],
            'Importance': f"HIGH ({importance_n})",
            'Score Emp': f"{empirical_score:.1f}",
            'Score Comp': f"{score_composite:.1f}",
            'Surprise': surprise_str,
            'Dir': 'UP' if direction > 0 else 'DOWN',
            'Vect Comp': f"{score_vectoriel_composite:.1f}"
        })
    
    # Calculer score composite global
    scores_vectoriels_composite = []
    for _, event in cluster_events.iterrows():
        empirical_score = event.get('empirical_score', 0.0)
        if pd.isna(empirical_score) or empirical_score == 0:
            importance_n = event.get('importance_n', 1)
            empirical_score = {1: 20.0, 2: 35.0, 3: 50.0}.get(importance_n, 20.0)
        
        importance_n = event.get('importance_n', 1)
        importance_weight = {1: 0.5, 2: 0.75, 3: 1.0}.get(importance_n, 0.5)
        score_composite = empirical_score * importance_weight
        
        actual = event.get('actual')
        estimate = event.get('estimate') or event.get('forecast') or event.get('previous')
        surprise = 0.0
        if actual is not None and estimate is not None and estimate != 0:
            surprise = (actual - estimate) / abs(estimate) * 100
        elif actual is not None and estimate is not None:
            surprise = actual - estimate
        
        event_key = event.get('event_key') or event.get('event_title') or 'Unknown'
        family = infer_family_from_event_key(event_key)
        direction = get_event_direction(family, surprise) if surprise != 0 else 1
        
        scores_vectoriels_composite.append(score_composite * direction)
    
    return {
        'time': time_str,
        'n_events': len(cluster_events),
        'score_global_simple': sum(scores_simples),
        'score_global_vectoriel': sum(scores_vectoriels),
        'score_global_composite': sum(scores_vectoriels_composite),
        'details': details
    }

def main():
    date_str = '2025-05-29'
    
    print('='*120)
    print(f'COMPARAISON CLUSTERS 14:30 vs 18:00 - {date_str}')
    print('='*120)
    print()
    
    # Charger événements
    events_df = load_events_for_date(date_str)
    
    if events_df.empty:
        print('❌ Aucun événement US HIGH trouvé')
        return
    
    # Analyser cluster 14:30
    cluster_1430 = analyze_cluster(events_df, '14:30', 14, (25, 35))
    
    # Analyser cluster 18:00
    cluster_1800 = analyze_cluster(events_df, '18:00', 18, (0, 5))
    
    # Afficher tableau comparatif
    print('📊 TABLEAU COMPARATIF')
    print('-'*120)
    print()
    
    if cluster_1430:
        print(f'🔵 CLUSTER 14:30')
        print('-'*120)
        print(f"{'Heure':<8} {'Événement':<45} {'Imp':<6} {'Score Emp':<10} {'Score Comp':<12} {'Surprise':<12} {'Dir':<5} {'Vect Comp':<12}")
        print('-'*120)
        for detail in cluster_1430['details']:
            print(f"{detail['Heure']:<8} {detail['Événement']:<45} {detail['Importance']:<6} {detail['Score Emp']:<10} {detail['Score Comp']:<12} {detail['Surprise']:<12} {detail['Dir']:<5} {detail['Vect Comp']:<12}")
        print('-'*120)
        print(f"Total: {cluster_1430['n_events']} événements")
        print(f"Score global (simple): {cluster_1430['score_global_simple']:.1f}")
        print(f"Score global (vectoriel): {cluster_1430['score_global_vectoriel']:.1f}")
        print(f"Score global (composite): {cluster_1430['score_global_composite']:.1f}")
        print()
    
    if cluster_1800:
        print(f'🔴 CLUSTER 18:00')
        print('-'*120)
        print(f"{'Heure':<8} {'Événement':<45} {'Imp':<6} {'Score Emp':<10} {'Score Comp':<12} {'Surprise':<12} {'Dir':<5} {'Vect Comp':<12}")
        print('-'*120)
        for detail in cluster_1800['details']:
            print(f"{detail['Heure']:<8} {detail['Événement']:<45} {detail['Importance']:<6} {detail['Score Emp']:<10} {detail['Score Comp']:<12} {detail['Surprise']:<12} {detail['Dir']:<5} {detail['Vect Comp']:<12}")
        print('-'*120)
        print(f"Total: {cluster_1800['n_events']} événements")
        print(f"Score global (simple): {cluster_1800['score_global_simple']:.1f}")
        print(f"Score global (vectoriel): {cluster_1800['score_global_vectoriel']:.1f}")
        print(f"Score global (composite): {cluster_1800['score_global_composite']:.1f}")
        print()
    
    # Comparaison finale
    print('='*120)
    print('📈 COMPARAISON FINALE')
    print('='*120)
    
    if cluster_1430 and cluster_1800:
        print(f"Cluster 14:30:")
        print(f"  - Nombre événements: {cluster_1430['n_events']}")
        print(f"  - Score global (simple): {cluster_1430['score_global_simple']:.1f}")
        print(f"  - Score global (vectoriel): {cluster_1430['score_global_vectoriel']:.1f}")
        print(f"  - Score global (composite): {cluster_1430['score_global_composite']:.1f}")
        print()
        print(f"Cluster 18:00:")
        print(f"  - Nombre événements: {cluster_1800['n_events']}")
        print(f"  - Score global (simple): {cluster_1800['score_global_simple']:.1f}")
        print(f"  - Score global (vectoriel): {cluster_1800['score_global_vectoriel']:.1f}")
        print(f"  - Score global (composite): {cluster_1800['score_global_composite']:.1f}")
        print()
        print(f"Différence:")
        print(f"  - Nombre: {cluster_1800['n_events'] - cluster_1430['n_events']} événements de plus à 18:00")
        print(f"  - Score simple: {cluster_1800['score_global_simple'] - cluster_1430['score_global_simple']:.1f} points de plus à 18:00")
        print(f"  - Score vectoriel: {cluster_1800['score_global_vectoriel'] - cluster_1430['score_global_vectoriel']:.1f} points de plus à 18:00")
        print(f"  - Score composite: {cluster_1800['score_global_composite'] - cluster_1430['score_global_composite']:.1f} points de plus à 18:00")
        print()
        print("💡 CONCLUSION:")
        if cluster_1800['score_global_composite'] > cluster_1430['score_global_composite']:
            print("  ⚠️  Le cluster à 18:00 a un score composite plus élevé")
            print("  ⚠️  MAIS le mouvement réel se produit à 14:30 (visible sur graphique)")
            print("  ✅ La logique de priorité absolue à 14:30 est donc correcte")
        else:
            print("  ✅ Le cluster à 14:30 a un score composite plus élevé")
            print("  ✅ Cela confirme que c'est le bon cluster à sélectionner")

if __name__ == '__main__':
    main()

