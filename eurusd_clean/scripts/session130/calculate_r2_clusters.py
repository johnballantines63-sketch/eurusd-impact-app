#!/usr/bin/env python3
"""
CALCULER R² CLUSTERS SIMILAIRES - SESSION 130 ÉTAPE 7
======================================================

Pour chaque cluster similaire, calculer R² tendance 7j avant.

Input : reference_cases_with_similar_clusters.json
Output : reference_cases_with_r2_clusters.json

Auteur : André Valentin avec Claude
Date : 12 novembre 2025 - Session 130
"""

import json
import duckdb
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List
import sys
import numpy as np
from sklearn.linear_model import LinearRegression

# Import utils timezone
sys.path.insert(0, str(Path(__file__).parent / '../session129'))
from utils_timezone import ensure_bern_time, TZ_BERN

# Chemins
DB_PATH = "data/warehouse.duckdb"
INPUT_FILE = Path(__file__).parent / "reference_cases_with_similar_clusters.json"
OUTPUT_FILE = Path(__file__).parent / "reference_cases_with_r2_clusters.json"


def calculate_r2_for_cluster(conn, cluster_time_str: str, lookback_hours: int = 168) -> float:
    """
    Calcule R² tendance linéaire 7j avant cluster.
    
    Returns:
        R² entre 0 et 1
    """
    # Parser cluster time
    cluster_time = ensure_bern_time(cluster_time_str)
    
    # Fenêtre prix
    start_time = cluster_time - timedelta(hours=lookback_hours)
    
    # Query prix
    query = """
    SELECT datetime, close
    FROM prices_bern
    WHERE datetime BETWEEN ? AND ?
    ORDER BY datetime
    """
    
    try:
        prices = conn.execute(query, [start_time, cluster_time]).fetchall()
        
        if len(prices) < 10:
            return 0.0
        
        # Régression linéaire
        closes = np.array([p[1] for p in prices])
        X = np.arange(len(closes)).reshape(-1, 1)
        y = closes
        
        model = LinearRegression()
        model.fit(X, y)
        
        r2 = model.score(X, y)
        
        return max(0.0, min(1.0, r2))
        
    except Exception as e:
        print(f"      ⚠️  Erreur calcul R² : {e}")
        return 0.0


def process_pattern_clusters(pattern: str, ref_case: Dict, conn) -> Dict:
    """
    Calcule R² pour tous clusters similaires d'un pattern.
    
    Returns:
        Dict enrichi avec R² pour chaque cluster
    """
    print(f"\n{'='*80}")
    print(f"Pattern : {pattern}")
    print(f"{'='*80}")
    
    similar_clusters = ref_case.get('similar_clusters', [])
    n_clusters = len(similar_clusters)
    
    print(f"Clusters similaires : {n_clusters}")
    
    if n_clusters == 0:
        print(f"   ⚠️  Aucun cluster à traiter")
        return ref_case
    
    print(f"\n📈 Calcul R² pour {n_clusters} clusters...")
    
    # Enrichir chaque cluster avec R²
    enriched_clusters = []
    r2_values = []
    
    for i, cluster in enumerate(similar_clusters, 1):
        cluster_time = cluster['cluster_time']
        date = cluster['date']
        
        # Calculer R²
        r2 = calculate_r2_for_cluster(conn, cluster_time, lookback_hours=168)
        r2_values.append(r2)
        
        # Enrichir cluster
        enriched_cluster = {
            **cluster,
            'r2_trend': r2
        }
        enriched_clusters.append(enriched_cluster)
        
        # Log progression
        if i % 10 == 0 or i == n_clusters:
            print(f"   Progression : {i}/{n_clusters} ({100*i/n_clusters:.0f}%)")
    
    # Statistiques R²
    if r2_values:
        avg_r2 = sum(r2_values) / len(r2_values)
        min_r2 = min(r2_values)
        max_r2 = max(r2_values)
        
        print(f"\n   📊 Statistiques R² :")
        print(f"      Moyenne : {avg_r2:.4f}")
        print(f"      Min : {min_r2:.4f}")
        print(f"      Max : {max_r2:.4f}")
        print(f"      Std : {np.std(r2_values):.4f}")
    
    # Top 5 R² élevés
    top5_r2 = sorted(enriched_clusters, key=lambda x: -x['r2_trend'])[:5]
    print(f"\n   Top 5 R² élevés :")
    for i, cluster in enumerate(top5_r2, 1):
        print(f"      {i}. {cluster['date']} - R²: {cluster['r2_trend']:.4f}")
    
    return {
        **ref_case,
        'similar_clusters': enriched_clusters,
        'r2_statistics': {
            'mean': avg_r2 if r2_values else 0.0,
            'min': min_r2 if r2_values else 0.0,
            'max': max_r2 if r2_values else 0.0,
            'std': float(np.std(r2_values)) if r2_values else 0.0,
            'count': len(r2_values)
        }
    }


def main():
    """Fonction principale"""
    
    print("=" * 80)
    print("CALCULER R² CLUSTERS SIMILAIRES - ÉTAPE 7")
    print("=" * 80)
    
    # Charger données
    print(f"\n📂 Chargement : {INPUT_FILE}")
    
    if not INPUT_FILE.exists():
        print(f"❌ Fichier introuvable : {INPUT_FILE}")
        return 1
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    reference_cases = data['reference_cases']
    print(f"✅ {len(reference_cases)} cas référence chargés")
    
    # Total clusters à traiter
    total_clusters = sum(
        len(case.get('similar_clusters', [])) 
        for case in reference_cases.values()
    )
    print(f"📊 Total clusters à traiter : {total_clusters}")
    
    if total_clusters == 0:
        print(f"\n⚠️  Aucun cluster similaire trouvé")
        print(f"   Vérifier Étape 6 (find_similar_clusters.py)")
        return 1
    
    # Connexion DB
    print(f"\n🔗 Connexion DB...")
    conn = duckdb.connect(DB_PATH, read_only=True)
    print(f"✅ Connecté")
    
    # Traiter chaque pattern
    enriched_cases = {}
    
    for pattern, ref_case in reference_cases.items():
        try:
            enriched = process_pattern_clusters(pattern, ref_case, conn)
            enriched_cases[pattern] = enriched
        except Exception as e:
            print(f"\n❌ ERREUR traitement {pattern} : {e}")
            import traceback
            traceback.print_exc()
            enriched_cases[pattern] = {
                **ref_case,
                'error': str(e)
            }
    
    conn.close()
    
    # Résumé
    print(f"\n{'='*80}")
    print("RÉSUMÉ R² CLUSTERS")
    print("=" * 80)
    
    print(f"\n| {'Pattern':<30s} | {'N Clusters':<11s} | {'R² Moyen':<10s} | {'R² Min':<8s} | {'R² Max':<8s} |")
    print(f"|{'-'*32}|{'-'*13}|{'-'*12}|{'-'*10}|{'-'*10}|")
    
    for pattern, case in enriched_cases.items():
        stats = case.get('r2_statistics', {})
        n = stats.get('count', 0)
        mean_r2 = stats.get('mean', 0.0)
        min_r2 = stats.get('min', 0.0)
        max_r2 = stats.get('max', 0.0)
        
        print(f"| {pattern:<30s} | {n:>11d} | {mean_r2:>10.4f} | {min_r2:>8.4f} | {max_r2:>8.4f} |")
    
    # Sauvegarde
    print(f"\n{'='*80}")
    print("SAUVEGARDE RÉSULTATS")
    print("=" * 80)
    
    output = {
        'metadata': {
            **data['metadata'],
            'r2_calculated': datetime.now().isoformat(),
            'lookback_hours': 168
        },
        'reference_cases': enriched_cases,
        'validated_cases': data.get('validated_cases', {})
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ R² clusters sauvegardés : {OUTPUT_FILE}")
    print(f"   Taille : {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")
    
    print(f"\n{'='*80}")
    print("✅ ÉTAPE 7 TERMINÉE")
    print("=" * 80)
    
    print(f"\n🎯 PHASE 3 COMPLÉTÉE !")
    print(f"   Fichiers créés :")
    print(f"   - reference_cases_with_similar_clusters.json")
    print(f"   - reference_cases_with_r2_clusters.json")
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ ERREUR : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
