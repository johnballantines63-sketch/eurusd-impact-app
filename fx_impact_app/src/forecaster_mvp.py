"""
Forecaster MVP - Version enrichie avec Latence et TTR
Calcule les statistiques d'impact pour chaque famille d'événements
"""

import duckdb
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class ForecastEngine:
    """Moteur de calcul des statistiques d'impact des événements macro"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = duckdb.connect(db_path, read_only=False)
    
    def calculate_family_stats(
        self,
        family_pattern: str,
        horizon_minutes: int = 30,
        hist_years: int = 3,
        countries: Optional[List[str]] = None,
        timeframe: str = '1m'
    ) -> Dict:
        """Calcule toutes les stats pour une famille d'événements"""
        
        if countries is None:
            countries = ['US']
        
        cutoff_date = datetime.utcnow() - timedelta(days=hist_years * 365)
        country_filter = "', '".join(countries)
        
        # CORRECTION: Utiliser ~ au lieu de REGEXP pour DuckDB
        query_events = f"""
        SELECT ts_utc, event_key, country, importance_n
        FROM events
        WHERE ts_utc >= '{cutoff_date.strftime('%Y-%m-%d')}'
          AND country IN ('{country_filter}')
          AND event_key ~ '{family_pattern}'
        ORDER BY ts_utc
        """
        
        events_df = self.conn.execute(query_events).fetchdf()
        
        if len(events_df) == 0:
            return self._empty_stats(family_pattern)
        
        all_impacts = []
        all_latencies = []
        all_ttrs = []
        directions = []
        
        for _, event in events_df.iterrows():
            stats = self._calculate_single_event_stats(
                event['ts_utc'], horizon_minutes, timeframe
            )
            
            if stats is not None:
                all_impacts.append(stats['mfe'])
                all_latencies.append(stats['latency'])
                all_ttrs.append(stats['ttr'])
                directions.append(stats['direction'])
        
        if len(all_impacts) == 0:
            return self._empty_stats(family_pattern)
        
        all_impacts = np.array(all_impacts)
        all_latencies = np.array(all_latencies)
        all_ttrs = np.array(all_ttrs)
        directions = np.array(directions)
        
        return {
            'family': family_pattern,
            'n_events': len(all_impacts),
            'horizon_min': horizon_minutes,
            'p_up': float(np.mean(directions > 0)),
            'p_down': float(np.mean(directions < 0)),
            'mfe_median': float(np.median(all_impacts)),
            'mfe_p80': float(np.percentile(all_impacts, 80)),
            'mfe_p90': float(np.percentile(all_impacts, 90)),
            'mfe_mean': float(np.mean(all_impacts)),
            'mfe_std': float(np.std(all_impacts)),
            'latency_median': float(np.median(all_latencies)),
            'latency_p20': float(np.percentile(all_latencies, 20)),
            'latency_p80': float(np.percentile(all_latencies, 80)),
            'latency_mean': float(np.mean(all_latencies)),
            'ttr_median': float(np.median(all_ttrs)),
            'ttr_p20': float(np.percentile(all_ttrs, 20)),
            'ttr_p80': float(np.percentile(all_ttrs, 80)),
            'ttr_mean': float(np.mean(all_ttrs)),
            'timeframe': timeframe,
            'countries': countries,
            'hist_years': hist_years
        }
    
    def _calculate_single_event_stats(self, event_ts, horizon_minutes, timeframe):
        """Calcule MFE, latence et TTR pour un événement unique"""
        
        # Normaliser event_ts (enlever timezone info si présente)
        import pandas as pd
        if hasattr(event_ts, 'tz_localize'):
            event_ts_naive = event_ts.tz_localize(None) if event_ts.tzinfo else event_ts
        else:
            event_ts_naive = pd.Timestamp(event_ts).tz_localize(None) if pd.Timestamp(event_ts).tzinfo else pd.Timestamp(event_ts)
        
        query_ref = f"""
        SELECT close as ref_price
        FROM prices_{timeframe}_v
        WHERE ts_utc < '{event_ts_naive}'
        ORDER BY ts_utc DESC
        LIMIT 1
        """
        
        ref_result = self.conn.execute(query_ref).fetchdf()
        if len(ref_result) == 0:
            return None
        
        ref_price = ref_result['ref_price'].iloc[0]
        end_ts_naive = event_ts_naive + timedelta(minutes=horizon_minutes)
        
        query_prices = f"""
        SELECT ts_utc, close, (close - {ref_price}) * 10000 as pips
        FROM prices_{timeframe}_v
        WHERE ts_utc >= '{event_ts_naive}' AND ts_utc <= '{end_ts_naive}'
        ORDER BY ts_utc
        """
        
        prices_df = self.conn.execute(query_prices).fetchdf()
        
        if len(prices_df) < 3:
            return None
        
        # Normaliser les timestamps du DataFrame
        prices_df['ts_utc'] = pd.to_datetime(prices_df['ts_utc']).dt.tz_localize(None)
        
        pips = prices_df['pips'].values
        mfe = float(np.max(np.abs(pips)))
        direction = 1 if np.sum(pips > 0) > np.sum(pips < 0) else -1
        
        # Latence
        latency_minutes = 0
        for idx, pip_val in enumerate(pips):
            if abs(pip_val) >= 5.0:
                time_diff = prices_df['ts_utc'].iloc[idx] - event_ts_naive
                latency_minutes = time_diff.total_seconds() / 60
                break
        if latency_minutes == 0:
            latency_minutes = horizon_minutes
        
        # TTR
        ttr_minutes = horizon_minutes
        peak_idx = np.argmax(np.abs(pips))
        peak_value = pips[peak_idx]
        reversal_threshold = abs(peak_value) * 0.5
        
        for idx in range(peak_idx + 1, len(pips)):
            if abs(pips[idx]) < reversal_threshold and np.sign(pips[idx]) != np.sign(peak_value):
                time_diff = prices_df['ts_utc'].iloc[idx] - event_ts_naive
                ttr_minutes = time_diff.total_seconds() / 60
                break
        
        return {
            'mfe': mfe,
            'latency': latency_minutes,
            'ttr': ttr_minutes,
            'direction': direction
        }
    
    def _empty_stats(self, family_pattern):
        """Retourne un dict de stats vides"""
        return {
            'family': family_pattern, 'n_events': 0, 'horizon_min': 0,
            'p_up': 0.0, 'p_down': 0.0,
            'mfe_median': 0.0, 'mfe_p80': 0.0, 'mfe_p90': 0.0, 'mfe_mean': 0.0, 'mfe_std': 0.0,
            'latency_median': 0.0, 'latency_p20': 0.0, 'latency_p80': 0.0, 'latency_mean': 0.0,
            'ttr_median': 0.0, 'ttr_p20': 0.0, 'ttr_p80': 0.0, 'ttr_mean': 0.0
        }
    
    def calculate_multiple_families(self, family_patterns, horizon_minutes=30, hist_years=3, countries=None):
        """Calcule les stats pour plusieurs familles"""
        results = {}
        for family_name, pattern in family_patterns.items():
            results[family_name] = self.calculate_family_stats(
                pattern, horizon_minutes, hist_years, countries
            )
        return results
    
    def close(self):
        """Ferme la connexion"""
        if self.conn:
            self.conn.close()
