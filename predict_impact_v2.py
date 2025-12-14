"""
Script de pré-calcul des statistiques de latence/TTR/impact
À exécuter UNE FOIS pour accélérer le Planificateur Multi-Événements

Usage:
    python precompute_family_stats.py
"""

import sys
from pathlib import Path

# Setup paths
sys.path.insert(0, str(Path(__file__).parent / "fx_impact_app" / "src"))

import duckdb
from latency_analyzer import LatencyAnalyzer
from forecaster_mvp import ForecastEngine
from event_families import FAMILY_PATTERNS

DB_PATH = "fx_impact_app/data/warehouse.duckdb"

def precompute_all_families():
    """Pré-calcule et stocke les stats pour toutes les familles"""
    
    conn = duckdb.connect(DB_PATH)
    
    # 1. Ajouter colonnes si elles n'existent pas
    print("📋 Vérification structure table event_families...")
    try:
        conn.execute("ALTER TABLE event_families ADD COLUMN IF NOT EXISTS latency_median DOUBLE")
        conn.execute("ALTER TABLE event_families ADD COLUMN IF NOT EXISTS latency_p20 DOUBLE")
        conn.execute("ALTER TABLE event_families ADD COLUMN IF NOT EXISTS latency_p80 DOUBLE")
        conn.execute("ALTER TABLE event_families ADD COLUMN IF NOT EXISTS ttr_median DOUBLE")
        conn.execute("ALTER TABLE event_families ADD COLUMN IF NOT EXISTS ttr_p20 DOUBLE")
        conn.execute("ALTER TABLE event_families ADD COLUMN IF NOT EXISTS ttr_p80 DOUBLE")
        conn.execute("ALTER TABLE event_families ADD COLUMN IF NOT EXISTS mfe_p80 DOUBLE")
        conn.execute("ALTER TABLE event_families ADD COLUMN IF NOT EXISTS n_events_latency INTEGER")
        print("✅ Structure table mise à jour")
    except Exception as e:
        print(f"⚠️ Colonnes déjà existantes ou erreur: {e}")
    
    # 2. Récupérer toutes les familles uniques
    families_query = "SELECT DISTINCT family FROM event_families WHERE family IS NOT NULL"
    families = conn.execute(families_query).fetchall()
    families = [f[0] for f in families]
    
    print(f"\n🔍 {len(families)} familles trouvées dans event_families")
    
    # 3. Calculer stats pour chaque famille
    analyzer = LatencyAnalyzer(DB_PATH)
    engine = ForecastEngine(DB_PATH)
    
    success_count = 0
    error_count = 0
    
    for i, family in enumerate(families, 1):
        print(f"\n[{i}/{len(families)}] 📊 Traitement famille: {family}")
        
        # Trouver pattern correspondant
        pattern = FAMILY_PATTERNS.get(family, '')
        if not pattern:
            print(f"  ⚠️ Pattern non trouvé, skip")
            error_count += 1
            continue
        
        try:
            # Calculer stats latence
            latency_stats = analyzer.calculate_family_latency_stats(
                family_pattern=pattern,
                threshold_pips=5.0,
                min_events=5,
                lookback_days=1095
            )
            
            if latency_stats['events_analyzed'] == 0:
                print(f"  ⚠️ Aucun événement historique, skip")
                error_count += 1
                continue
            
            # Calculer stats MFE
            mfe_stats = engine.calculate_family_stats(
                pattern,
                horizon_minutes=60,
                hist_years=3,
                countries=None
            )
            
            # Préparer données
            latency_median = latency_stats['initial_reaction']['median_minutes']
            latency_p20 = latency_stats['initial_reaction'].get('p20_minutes', latency_median * 0.5)
            latency_p80 = latency_stats['initial_reaction'].get('p80_minutes', latency_median * 1.5)
            
            ttr_median = latency_median * 2
            ttr_p20 = latency_median * 1.5
            ttr_p80 = latency_median * 3
            
            mfe_p80 = mfe_stats.get('mfe_p80', 10.0)
            n_events = latency_stats['events_analyzed']
            
            # Mise à jour DB
            conn.execute("""
                UPDATE event_families
                SET latency_median = ?,
                    latency_p20 = ?,
                    latency_p80 = ?,
                    ttr_median = ?,
                    ttr_p20 = ?,
                    ttr_p80 = ?,
                    mfe_p80 = ?,
                    n_events_latency = ?
                WHERE family = ?
            """, [
                latency_median, latency_p20, latency_p80,
                ttr_median, ttr_p20, ttr_p80,
                mfe_p80, n_events, family
            ])
            
            print(f"  ✅ Latence: {latency_median:.1f} min, TTR: {ttr_median:.1f} min, MFE: {mfe_p80:.1f} pips ({n_events} événements)")
            success_count += 1
            
        except Exception as e:
            print(f"  ❌ Erreur: {e}")
            error_count += 1
    
    analyzer.close()
    engine.close()
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"✅ PRÉ-CALCUL TERMINÉ")
    print(f"{'='*60}")
    print(f"✅ Succès: {success_count} familles")
    print(f"❌ Erreurs: {error_count} familles")
    print(f"\n💡 Les stats sont maintenant stockées dans event_families")
    print(f"💡 Modifier predict_impact() pour lire depuis la DB au lieu de calculer")


if __name__ == "__main__":
    print("🚀 Démarrage pré-calcul statistiques familles...")
    print("⏱️  Durée estimée: 5-10 minutes\n")
    precompute_all_families()
