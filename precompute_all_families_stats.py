#!/usr/bin/env python3
"""
Pré-calcule les stats (latence, TTR, MFE) pour TOUTES les familles
===============================================================

Ce script calcule une fois pour toutes les statistiques pour chaque famille
et les stocke dans la table event_families de la DB.

Résultat : Calculs instantanés (<5ms) pour tous les événements !

Usage:
    python3 precompute_all_families_stats.py

Durée: ~5-10 minutes (selon nombre de familles)
"""

import sys
from pathlib import Path
import duckdb

# Ajouter chemins nécessaires
project_root = Path(__file__).parent
src_path = project_root / "fx_impact_app" / "src"
sys.path.insert(0, str(src_path))

from config import get_db_path
from event_families import FAMILY_PATTERNS
from latency_analyzer import LatencyAnalyzer
from forecaster_mvp import ForecastEngine

def precompute_family_stats(family_name, pattern, db_path):
    """
    Calcule les stats pour une famille et retourne les données à stocker
    
    Returns:
        dict avec stats ou None si erreur
    """
    try:
        # 1. Calcul latence avec LatencyAnalyzer
        analyzer = LatencyAnalyzer(db_path)
        
        latency_stats = analyzer.calculate_family_latency_stats(
            family_pattern=pattern,
            threshold_pips=5.0,
            min_events=5,
            lookback_days=3 * 365  # 3 ans
        )
        
        analyzer.close()
        
        # Vérifier résultats
        if not latency_stats or not isinstance(latency_stats, dict):
            return None
            
        if latency_stats.get('events_analyzed', 0) == 0:
            return None
            
        if 'initial_reaction' not in latency_stats or not latency_stats['initial_reaction']:
            return None
        
        # 2. Calcul MFE avec ForecastEngine
        engine = ForecastEngine(db_path)
        
        mfe_stats = engine.calculate_family_stats(
            pattern,
            horizon_minutes=60,
            hist_years=3,
            countries=None
        )
        
        engine.close()
        
        # 3. Préparer données
        lat_median = latency_stats['initial_reaction']['median_minutes']
        
        stats = {
            'latency_median': lat_median,
            'latency_p20': latency_stats['initial_reaction'].get('p20_minutes', lat_median * 0.5),
            'latency_p80': latency_stats['initial_reaction'].get('p80_minutes', lat_median * 1.5),
            'ttr_median': lat_median * 1.5,  # TTR = Latence × 1.5
            'ttr_p20': lat_median * 1.0,
            'ttr_p80': lat_median * 2.0,
            'mfe_p80': mfe_stats.get('mfe_p80', 10.0),
            'n_events_latency': latency_stats['events_analyzed']
        }
        
        return stats
        
    except Exception as e:
        print(f"      ❌ Erreur: {e}")
        return None


def update_db_with_stats(conn, family_name, stats):
    """
    Met à jour la DB avec les stats calculées
    """
    update_query = f"""
    UPDATE event_families
    SET 
        latency_median = {stats['latency_median']},
        latency_p20 = {stats['latency_p20']},
        latency_p80 = {stats['latency_p80']},
        ttr_median = {stats['ttr_median']},
        ttr_p20 = {stats['ttr_p20']},
        ttr_p80 = {stats['ttr_p80']},
        mfe_p80 = {stats['mfe_p80']},
        n_events_latency = {stats['n_events_latency']}
    WHERE family = '{family_name}'
    """
    
    conn.execute(update_query)


def main():
    print("=" * 80)
    print("PRÉ-CALCUL STATS POUR TOUTES LES FAMILLES")
    print("=" * 80)
    print()
    print("Ce script va calculer et stocker les statistiques pour chaque famille.")
    print("Durée estimée : 5-10 minutes")
    print()
    
    db_path = get_db_path()
    print(f"📂 Base de données : {db_path}")
    print(f"📊 Nombre de familles : {len(FAMILY_PATTERNS)}")
    print()
    
    # Ouvrir connexion DB
    conn = duckdb.connect(db_path)
    
    # Compteurs
    total = len(FAMILY_PATTERNS)
    success = 0
    skipped = 0
    errors = 0
    
    print("-" * 80)
    print()
    
    # Traiter chaque famille
    for idx, (family_name, pattern) in enumerate(FAMILY_PATTERNS.items(), 1):
        print(f"[{idx}/{total}] 🔄 {family_name}...", end=" ", flush=True)
        
        # Calculer stats
        stats = precompute_family_stats(family_name, pattern, db_path)
        
        if stats is None:
            print("⚠️  SKIP (pas assez de données)")
            skipped += 1
            continue
        
        # Mettre à jour DB
        try:
            update_db_with_stats(conn, family_name, stats)
            print(f"✅ OK ({stats['n_events_latency']} événements | "
                  f"lat:{stats['latency_median']:.1f}min | "
                  f"ttr:{stats['ttr_median']:.1f}min | "
                  f"mfe:{stats['mfe_p80']:.1f}pips)")
            success += 1
        except Exception as e:
            print(f"❌ ERREUR mise à jour DB: {e}")
            errors += 1
    
    # Fermer connexion
    conn.close()
    
    # Résumé
    print()
    print("=" * 80)
    print("RÉSUMÉ")
    print("=" * 80)
    print(f"✅ Succès      : {success}/{total}")
    print(f"⚠️  Ignorées    : {skipped}/{total} (pas assez de données)")
    print(f"❌ Erreurs     : {errors}/{total}")
    print()
    
    if success > 0:
        print("🎉 PRÉ-CALCUL TERMINÉ !")
        print()
        print("📊 Les familles suivantes ont maintenant des calculs ultra-rapides :")
        
        # Lister familles mises à jour
        conn = duckdb.connect(db_path, read_only=True)
        query = """
        SELECT family, latency_median, ttr_median, mfe_p80, n_events_latency
        FROM event_families
        WHERE latency_median IS NOT NULL
        ORDER BY family
        """
        results = conn.execute(query).fetchall()
        conn.close()
        
        print()
        for row in results:
            family, lat, ttr, mfe, n = row
            print(f"   ⚡ {family:<35} | {lat:5.1f}min | {ttr:5.1f}min | {mfe:5.1f}pips | n={n}")
        
        print()
        print("💡 Redémarrez Streamlit pour voir les changements :")
        print("   cd fx_impact_app")
        print("   streamlit run streamlit_app/Home.py")
    else:
        print("⚠️  Aucune famille n'a pu être calculée.")
        print("   Vérifiez que la DB contient des données historiques.")
    
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
