"""
Module d'analyse de latence de réaction du marché EUR/USD aux annonces économiques
"""
import duckdb
from pathlib import Path
from typing import Dict, List, Optional
import statistics

class LatencyAnalyzer:
    """Analyse la latence de réaction du marché aux événements économiques"""
    
    def __init__(self, db_path: str = "fx_impact_app/data/warehouse.duckdb"):
        self.db_path = Path(db_path)
        self.conn = None
    
    def connect(self):
        if self.conn is None:
            self.conn = duckdb.connect(str(self.db_path))
    
    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def calculate_event_latency(self, event_time, event_key: str, 
                               threshold_pips: float = 5.0, max_minutes: int = 30) -> Dict:
        """Calcule les métriques de latence pour un événement spécifique"""
        self.connect()
        
        baseline_result = self.conn.execute("""
            SELECT close FROM prices_1m
            WHERE datetime <= ? - INTERVAL '1 minute'
            ORDER BY datetime DESC LIMIT 1
        """, [event_time]).fetchone()
        
        if not baseline_result:
            return {"error": "No baseline price"}
        
        baseline_price = baseline_result[0]
        
        post_prices = self.conn.execute(f"""
            SELECT datetime, close, high, low,
                   EXTRACT(EPOCH FROM (datetime - ?)) / 60.0 as minutes_after
            FROM prices_1m
            WHERE datetime > ? AND datetime <= ? + INTERVAL '{max_minutes} minutes'
            ORDER BY datetime
        """, [event_time, event_time, event_time]).fetchall()
        
        if not post_prices:
            return {"error": "No post-event data"}
        
        initial_reaction = None
        peak_movement = 0
        peak_time = 0
        direction = None
        
        for row in post_prices:
            minutes = row[4]
            close = row[1]
            movement = abs(close - baseline_price) * 10000
            
            if initial_reaction is None and movement >= threshold_pips:
                initial_reaction = minutes
                direction = 'up' if close > baseline_price else 'down'
            
            if movement > peak_movement:
                peak_movement = movement
                peak_time = minutes
        
        return {
            "event_key": event_key,
            "initial_reaction_minutes": initial_reaction,
            "peak_time_minutes": peak_time,
            "peak_movement_pips": round(peak_movement, 1),
            "direction": direction
        }
    
    def calculate_family_latency_stats(self, family_pattern: str, threshold_pips: float = 5.0,
                                      min_events: int = 10, lookback_days: int = 365) -> Dict:
        """Calcule les statistiques de latence moyennes pour une famille d'événements"""
        self.connect()
        
        events = self.conn.execute(f"""
            SELECT ts_utc, event_key, actual, previous
            FROM events
            WHERE event_key ILIKE '%{family_pattern}%'
                AND actual IS NOT NULL
                AND ts_utc >= CURRENT_DATE - INTERVAL '{lookback_days} days'
            ORDER BY ts_utc DESC
        """).fetchall()
        
        if len(events) < min_events:
            return {"error": f"Insufficient data: {len(events)} events (minimum {min_events})"}
        
        latencies = []
        peak_times = []
        peak_movements = []
        
        for event in events[:50]:
            result = self.calculate_event_latency(event[0], event[1], threshold_pips)
            
            if "error" not in result:
                if result["initial_reaction_minutes"] is not None:
                    latencies.append(result["initial_reaction_minutes"])
                if result["peak_time_minutes"] > 0:
                    peak_times.append(result["peak_time_minutes"])
                    peak_movements.append(result["peak_movement_pips"])
        
        stats = {
            "family": family_pattern,
            "events_analyzed": len(events),
            "events_with_reaction": len(latencies),
            "threshold_pips": threshold_pips
        }
        
        if latencies:
            stats["initial_reaction"] = {
                "mean_minutes": round(statistics.mean(latencies), 1),
                "median_minutes": round(statistics.median(latencies), 1),
                "min_minutes": round(min(latencies), 1),
                "max_minutes": round(max(latencies), 1)
            }
        
        if peak_times:
            stats["peak_timing"] = {
                "mean_minutes": round(statistics.mean(peak_times), 1),
                "mean_movement_pips": round(statistics.mean(peak_movements), 1)
            }
        
        return stats
    
    def predict_latency_for_event(self, event_key: str, surprise_magnitude: Optional[float] = None,
                                 threshold_pips: float = 5.0) -> Dict:
        """Prédit la latence attendue pour un événement futur"""
        self.connect()
        
        family_pattern = None
        families = ['cpi', 'nfp', 'gdp', 'pmi', 'unemployment', 'retail', 
                   'fomc', 'fed', 'jobless', 'inflation', 'confidence']
        
        for fam in families:
            if fam in event_key.lower():
                family_pattern = fam
                break
        
        if not family_pattern:
            family_pattern = '.*'
        
        stats = self.calculate_family_latency_stats(family_pattern, threshold_pips)
        
        if "error" in stats:
            return stats
        
        prediction = {
            "event_key": event_key,
            "family": family_pattern,
            "base_prediction": stats.get("initial_reaction", {}),
            "peak_prediction": stats.get("peak_timing", {})
        }
        
        if surprise_magnitude is not None and "initial_reaction" in stats:
            base_latency = stats["initial_reaction"]["mean_minutes"]
            adjustment_factor = max(0.5, 1 - (abs(surprise_magnitude) * 0.2))
            
            prediction["adjusted_prediction"] = {
                "latency_minutes": round(base_latency * adjustment_factor, 1),
                "note": "Latence réduite" if adjustment_factor < 1 else "Latence normale"
            }
        
        return prediction
    
    def get_all_families_latency_summary(self, threshold_pips: float = 5.0) -> List[Dict]:
        """Résumé des latences pour toutes les familles d'événements"""
        families = ['cpi', 'nfp', 'gdp', 'pmi', 'unemployment', 'retail', 
                   'fomc', 'fed', 'jobless', 'inflation', 'confidence']
        
        results = []
        for family in families:
            stats = self.calculate_family_latency_stats(family, threshold_pips, min_events=5)
            if "error" not in stats:
                results.append(stats)
        
        results.sort(key=lambda x: x.get("initial_reaction", {}).get("mean_minutes", 999))
        return results
