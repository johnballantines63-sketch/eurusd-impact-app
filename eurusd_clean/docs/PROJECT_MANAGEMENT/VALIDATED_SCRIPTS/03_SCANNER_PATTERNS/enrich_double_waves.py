"""
Enrichissement Double Wave avec events causaux
Session 117 - Phase 2

Mapper chaque Double Wave → events économiques dans fenêtre temporelle

Auteur: André Valentin avec Claude
Date: 06 novembre 2025
"""

import json
import duckdb
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict
import pandas as pd


class DoubleWaveEnricher:
    """Enrichit les Double Wave avec events causaux"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        """Connexion DB"""
        self.conn = duckdb.connect(self.db_path, read_only=True)
        print(f"✅ Connecté à {self.db_path}")
    
    def disconnect(self):
        """Fermeture connexion"""
        if self.conn:
            self.conn.close()
            print("✅ Connexion fermée")
    
    def get_events_around_time(
        self, 
        target_time: datetime, 
        window_minutes: int = 10
    ) -> pd.DataFrame:
        """
        Récupère events autour d'un timestamp
        
        Args:
            target_time: Timestamp cible (peak1)
            window_minutes: Fenêtre ±N minutes
        
        Returns:
            DataFrame avec events
        """
        start_time = target_time - timedelta(minutes=window_minutes)
        end_time = target_time + timedelta(minutes=window_minutes)
        
        query = """
        SELECT 
            e.ts_utc as datetime,
            e.event_title,
            e.event_key,
            e.country,
            e.actual,
            e.estimate,
            e.previous,
            e.importance_n as importance,
            ef.empirical_score,
            ef.latency_median
        FROM events e
        LEFT JOIN event_families ef 
            ON e.event_key = ef.event_key 
            AND e.country = ef.country
        WHERE e.ts_utc >= ?
            AND e.ts_utc <= ?
        ORDER BY e.ts_utc
        """
        
        df = self.conn.execute(query, [start_time, end_time]).fetchdf()
        
        return df
    
    def calculate_surprise(self, actual, estimate, previous=None) -> float:
        """
        Calcule surprise en %
        
        Args:
            actual: Valeur réelle
            estimate: Valeur estimée (ou previous si estimate NULL)
            previous: Valeur précédente (fallback)
        
        Returns:
            Surprise en % (ou 0 si non calculable)
        """
        # Utiliser estimate, sinon previous
        reference = estimate if estimate is not None else previous
        
        if reference is None or actual is None:
            return 0.0
        
        if reference == 0:
            return 0.0
        
        surprise_pct = abs((actual - reference) / reference) * 100
        
        return round(surprise_pct, 2)
    
    def enrich_double_wave(self, dw: Dict) -> Dict:
        """
        Enrichit un Double Wave avec events causaux
        
        Args:
            dw: Dict Double Wave du scan
        
        Returns:
            Dict enrichi avec events
        """
        # Parser peak1_time
        peak_time_str = dw['peak1_time']
        if isinstance(peak_time_str, str):
            peak_time = datetime.fromisoformat(peak_time_str)
        else:
            peak_time = peak_time_str
        
        print(f"\n🔍 Enrichissement : {peak_time.date()} {peak_time.strftime('%H:%M')}")
        
        # Récupérer events ±10 min
        events_df = self.get_events_around_time(peak_time, window_minutes=10)
        
        if events_df.empty:
            print(f"   ⚠️  Aucun event trouvé dans fenêtre ±10 min")
            dw['events'] = []
            dw['num_events'] = 0
            dw['max_surprise'] = 0.0
            dw['events_summary'] = "Aucun event"
            return dw
        
        print(f"   ✅ {len(events_df)} events trouvés")
        
        # Calculer surprises
        events_enriched = []
        for _, row in events_df.iterrows():
            surprise = self.calculate_surprise(
                row['actual'], 
                row['estimate'], 
                row['previous']
            )
            
            event_data = {
                'datetime': row['datetime'].isoformat() if hasattr(row['datetime'], 'isoformat') else str(row['datetime']),
                'event_title': row['event_title'],
                'event_key': row['event_key'],
                'country': row['country'],
                'actual': float(row['actual']) if row['actual'] is not None else None,
                'estimate': float(row['estimate']) if row['estimate'] is not None else None,
                'previous': float(row['previous']) if row['previous'] is not None else None,
                'surprise_pct': surprise,
                'importance': int(row['importance']) if row['importance'] is not None else 0,
                'empirical_score': float(row['empirical_score']) if row['empirical_score'] is not None else 0.0
            }
            
            events_enriched.append(event_data)
        
        # Trier par surprise décroissante
        events_enriched.sort(key=lambda e: e['surprise_pct'], reverse=True)
        
        # Statistiques
        surprises = [e['surprise_pct'] for e in events_enriched]
        max_surprise = max(surprises) if surprises else 0.0
        avg_surprise = sum(surprises) / len(surprises) if surprises else 0.0
        
        # Top 3 events par surprise
        top3_events = events_enriched[:3]
        events_summary = " | ".join([
            f"{e['country']} {e['event_key']} ({e['surprise_pct']:.1f}%)"
            for e in top3_events
        ])
        
        # Enrichir Double Wave
        dw['events'] = events_enriched
        dw['num_events'] = len(events_enriched)
        dw['max_surprise'] = max_surprise
        dw['avg_surprise'] = round(avg_surprise, 2)
        dw['events_summary'] = events_summary
        
        print(f"   📊 Max surprise : {max_surprise:.1f}%")
        print(f"   📋 Top events : {events_summary}")
        
        return dw
    
    def enrich_all_double_waves(
        self, 
        patterns: List[Dict]
    ) -> List[Dict]:
        """
        Enrichit tous les Double Wave d'un dataset
        
        Args:
            patterns: Liste patterns du scan
        
        Returns:
            Liste patterns enrichis
        """
        print("=" * 70)
        print("🚀 ENRICHISSEMENT DOUBLE WAVE AVEC EVENTS")
        print("=" * 70)
        
        # Filtrer Double Wave
        double_waves = [p for p in patterns if p['pattern'] == 'double_wave']
        
        print(f"\n📊 {len(double_waves)} Double Wave à enrichir")
        
        # Enrichir chaque Double Wave
        enriched = []
        for i, dw in enumerate(double_waves, 1):
            print(f"\n--- Double Wave {i}/{len(double_waves)} ---")
            dw_enriched = self.enrich_double_wave(dw)
            enriched.append(dw_enriched)
        
        print("\n" + "=" * 70)
        print(f"✅ {len(enriched)} Double Wave enrichis")
        print("=" * 70)
        
        return enriched
    
    def export_enriched(
        self, 
        enriched_dw: List[Dict], 
        output_file: str = "double_waves_enriched.json"
    ):
        """
        Exporte Double Wave enrichis en JSON
        
        Args:
            enriched_dw: Liste Double Wave enrichis
            output_file: Nom fichier output
        """
        output_path = Path(__file__).parent / output_file
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(enriched_dw, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Double Wave enrichis exportés : {output_path}")
        
        # Statistiques
        print(f"\n📊 STATISTIQUES ENRICHISSEMENT :")
        
        total_events = sum(dw['num_events'] for dw in enriched_dw)
        avg_events = total_events / len(enriched_dw) if enriched_dw else 0
        
        max_surprises = [dw['max_surprise'] for dw in enriched_dw]
        avg_max_surprise = sum(max_surprises) / len(max_surprises) if max_surprises else 0
        
        print(f"   Total events trouvés : {total_events}")
        print(f"   Moyenne events/DW : {avg_events:.1f}")
        print(f"   Max surprise moyen : {avg_max_surprise:.1f}%")
        print(f"   Range max surprise : {min(max_surprises):.1f}% - {max(max_surprises):.1f}%")
        
        # Compter DW sans events
        no_events = sum(1 for dw in enriched_dw if dw['num_events'] == 0)
        if no_events > 0:
            print(f"\n   ⚠️  {no_events} Double Wave SANS events détectés")
            print(f"      → Patterns techniques purs (pas d'events causaux)")


def main():
    """Fonction principale"""
    print("=" * 70)
    print("🚀 ENRICHISSEMENT DOUBLE WAVE - SESSION 117")
    print("=" * 70)
    
    # Chemins
    db_path = "/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb"
    patterns_file = Path(__file__).parent / "patterns_detected.json"
    
    # Vérifier fichier patterns
    if not patterns_file.exists():
        print(f"❌ Fichier patterns non trouvé : {patterns_file}")
        return
    
    # Charger patterns
    print(f"\n📥 Chargement patterns depuis : {patterns_file.name}")
    with open(patterns_file, 'r', encoding='utf-8') as f:
        patterns = json.load(f)
    
    print(f"✅ {len(patterns)} patterns chargés")
    
    # Initialiser enricher
    enricher = DoubleWaveEnricher(db_path)
    
    try:
        # Connexion
        enricher.connect()
        
        # Enrichir Double Wave
        enriched_dw = enricher.enrich_all_double_waves(patterns)
        
        # Exporter
        enricher.export_enriched(enriched_dw, "double_waves_enriched.json")
        
    finally:
        # Fermer connexion
        enricher.disconnect()
    
    print("\n✅ ENRICHISSEMENT TERMINÉ")


if __name__ == "__main__":
    main()
