"""
Scoring Engine - Calcul du score composite 0-100
"""

import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class ScoringWeights:
    impact: float = 0.40
    persistence: float = 0.30
    reliability: float = 0.20
    importance: float = 0.10

class ScoringEngine:
    def __init__(self, weights: Optional[ScoringWeights] = None):
        self.weights = weights or ScoringWeights()
        self.impact_max_pips = 100.0
        self.latency_optimal_min = 5.0
        self.latency_max_min = 60.0
        self.ttr_optimal_min = 60.0
        self.ttr_min_acceptable = 15.0
        self.min_events_reliable = 10
    
    def calculate_score(self, stats: Dict, importance: int = 2) -> Dict:
        if stats['n_events'] == 0:
            return self._empty_score()
        
        impact_score = self._normalize_impact(stats['mfe_p80'])
        latency_score = self._normalize_latency(stats['latency_median'])
        ttr_score = self._normalize_ttr(stats['ttr_median'])
        persistence_score = (latency_score + ttr_score) / 2
        reliability_score = self._normalize_reliability(stats['n_events'])
        importance_score = (importance - 1) / 2
        
        composite_score = (
            self.weights.impact * impact_score +
            self.weights.persistence * persistence_score +
            self.weights.reliability * reliability_score +
            self.weights.importance * importance_score
        )
        
        final_score = composite_score * 100
        
        directional_bias = max(stats['p_up'], stats['p_down'])
        if directional_bias < 0.6:
            final_score *= 0.85
        
        return {
            'score': round(final_score, 1),
            'grade': self._score_to_grade(final_score),
            'components': {
                'impact': round(impact_score * 100, 1),
                'persistence': round(persistence_score * 100, 1),
                'reliability': round(reliability_score * 100, 1),
                'importance': round(importance_score * 100, 1)
            },
            'metrics': {
                'mfe_p80': stats['mfe_p80'],
                'latency_median': stats['latency_median'],
                'ttr_median': stats['ttr_median'],
                'n_events': stats['n_events'],
                'p_up': stats['p_up']
            },
            'tradability': self._assess_tradability(final_score, stats)
        }
    
    def _normalize_impact(self, mfe_p80):
        k = 0.05
        x0 = self.impact_max_pips / 2
        return min(1 / (1 + np.exp(-k * (mfe_p80 - x0))), 1.0)
    
    def _normalize_latency(self, latency_median):
        if latency_median <= self.latency_optimal_min:
            return 1.0
        elif latency_median >= self.latency_max_min:
            return 0.2
        else:
            return 1.0 - 0.8 * ((latency_median - self.latency_optimal_min) /
                                (self.latency_max_min - self.latency_optimal_min))
    
    def _normalize_ttr(self, ttr_median):
        if ttr_median >= self.ttr_optimal_min:
            return 1.0
        elif ttr_median <= self.ttr_min_acceptable:
            return 0.3
        else:
            return 0.3 + 0.7 * ((ttr_median - self.ttr_min_acceptable) /
                                (self.ttr_optimal_min - self.ttr_min_acceptable))
    
    def _normalize_reliability(self, n_events):
        if n_events >= self.min_events_reliable:
            return min(1.0, n_events / 20)
        else:
            return n_events / self.min_events_reliable * 0.5
    
    def _score_to_grade(self, score):
        if score >= 85: return 'A+'
        elif score >= 75: return 'A'
        elif score >= 65: return 'B+'
        elif score >= 55: return 'B'
        elif score >= 45: return 'C+'
        elif score >= 35: return 'C'
        else: return 'D'
    
    def _assess_tradability(self, score, stats):
        has_impact = stats['mfe_p80'] >= 15.0
        has_direction = max(stats['p_up'], stats['p_down']) >= 0.65
        has_persistence = stats['ttr_median'] >= 20.0
        is_reliable = stats['n_events'] >= 5
        
        if score >= 75 and all([has_impact, has_direction, has_persistence, is_reliable]):
            return 'EXCELLENT'
        elif score >= 60 and has_impact and has_direction:
            return 'GOOD'
        elif score >= 45 and has_impact:
            return 'FAIR'
        elif score >= 30:
            return 'POOR'
        else:
            return 'AVOID'
    
    def _empty_score(self):
        return {
            'score': 0.0, 'grade': 'N/A',
            'components': {'impact': 0.0, 'persistence': 0.0, 'reliability': 0.0, 'importance': 0.0},
            'metrics': {'mfe_p80': 0.0, 'latency_median': 0.0, 'ttr_median': 0.0, 'n_events': 0, 'p_up': 0.0},
            'tradability': 'N/A'
        }
    
    def batch_score(self, stats_dict, importance_map=None):
        if importance_map is None:
            importance_map = {}
        results = []
        for family_name, stats in stats_dict.items():
            importance = importance_map.get(family_name, 2)
            score_result = self.calculate_score(stats, importance)
            score_result['family'] = family_name
            results.append(score_result)
        results.sort(key=lambda x: x['score'], reverse=True)
        return results
    
    def format_for_export(self, scored_results):
        export_rows = []
        for result in scored_results:
            row = {
                'Family': result['family'],
                'Score': result['score'],
                'Grade': result['grade'],
                'Tradability': result['tradability'],
                'Impact_P80_Pips': result['metrics']['mfe_p80'],
                'Latency_Min': result['metrics']['latency_median'],
                'TTR_Min': result['metrics']['ttr_median'],
                'N_Events': result['metrics']['n_events'],
                'P_Up': result['metrics']['p_up']
            }
            export_rows.append(row)
        return export_rows
