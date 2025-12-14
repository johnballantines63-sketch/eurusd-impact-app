"""
Single Wave Detectors V2 - SESSION 120 REFACTORING
===================================================

DÉTECTEURS:
1. SingleWaveFortDetectorV2 (impact > 40 pips, pullback < 20%)
2. SingleWaveIntermediateDetectorV2 (impact 20-40 pips, pullback < 20%)

AMÉLIORATIONS vs V1 (Session 119):
✅ Seuils adaptatifs ATR-based (plus de 10 pips fixes)
✅ Garde temporelle MIN_BARS_BEFORE_PULLBACK = 3
✅ Validation double (temps + amplitude ATR)
✅ Extrema locaux adaptatifs (LOCAL_WIDTH = 2)
✅ Validation stricte timestamps + ratios

MÉTHODOLOGIE:
- Baseline = close(event_time - 1 minute)
- Chercher peak maximum après events
- Valider impact selon catégorie (Fort > 40, Intermediate 20-40)
- Post-processing extrema bruts pour pullback
- Validation stricte (garde temporelle, ratio < 100%)
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, Dict

# Import base V2
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from base_pattern_detector_v2 import (
    BasePatternDetectorV2,
    prepare_dataframe
)


class SingleWaveFortDetectorV2(BasePatternDetectorV2):
    """
    Détecteur Single Wave Fort V2 - Approche mathématique adaptative
    
    PATTERN:
    Baseline → Peak unique > 40 pips → Stabilisation
    
    CRITÈRES:
    - 1 pic dominant après events
    - Impact > 40 pips
    - Pullback < 20% du pic
    - Pas d'autre pic significatif (> 90% du peak principal)
    - Garde temporelle respectée
    - Validation ATR
    """
    
    def __init__(
        self,
        min_impact_pips: float = 40.0,
        max_pullback_ratio: float = 0.20,
        min_peak_dominance: float = 0.90,
        **kwargs
    ):
        """
        Args:
            min_impact_pips: Impact minimum (défaut 40 pips)
            max_pullback_ratio: Pullback maximum (défaut 20%)
            min_peak_dominance: Ratio minimum autre pic vs principal (défaut 90%)
            **kwargs: Arguments BasePatternDetectorV2
        """
        super().__init__(**kwargs)
        self.min_impact_pips = min_impact_pips
        self.max_pullback_ratio = max_pullback_ratio
        self.min_peak_dominance = min_peak_dominance
    
    def detect_pattern(
        self,
        df_ohlc: pd.DataFrame,
        event_time: datetime,
        baseline_price: Optional[float] = None
    ) -> Optional[Dict]:
        """
        Détecte pattern Single Wave Fort avec approche mathématique
        
        Args:
            df_ohlc: DataFrame OHLC 1-min
            event_time: Timestamp events
            baseline_price: Prix baseline (calculé si None)
        
        Returns:
            Dict résultat ou None
        """
        # Préparer données
        df = prepare_dataframe(df_ohlc)
        
        # Calculer baseline si non fourni
        if baseline_price is None:
            baseline_price = self.get_baseline_price(df, event_time)
        
        # Calculer ATR
        df['ATR'] = self.calculate_atr(df)
        
        # Filtrer données APRÈS event
        df_after = df[df['datetime'] > event_time].copy()
        
        if df_after.empty:
            if self.debug:
                print("❌ Aucune donnée après event_time")
            return None
        
        if self.debug:
            print(f"\n{'='*80}")
            print(f"🔍 SINGLE WAVE FORT V2 - {event_time.strftime('%Y-%m-%d')}")
            print(f"{'='*80}")
            print(f"Baseline: {event_time - pd.Timedelta(minutes=1)} @ {baseline_price:.5f}")
        
        # Trouver extrema adaptatifs
        extrema_df = self.find_local_extrema_adaptive(df, after_time=event_time)
        
        if extrema_df.empty:
            if self.debug:
                print("❌ Aucun extrema détecté")
            return None
        
        # Filtrer peaks
        peaks = extrema_df[extrema_df['type'] == 'peak'].copy()
        
        if peaks.empty:
            if self.debug:
                print("❌ Aucun peak détecté")
            return None
        
        # Trouver peak maximum
        main_peak_idx = peaks['price'].idxmax()
        main_peak = peaks.loc[main_peak_idx]
        main_peak_price = main_peak['price']
        main_peak_time = main_peak['datetime']
        
        # Calculer impact
        impact = main_peak_price - baseline_price
        impact_pips = self.to_pips(impact)
        
        if self.debug:
            print(f"\n📊 ANALYSE PEAK PRINCIPAL:")
            print(f"   Time: {main_peak_time.strftime('%H:%M:%S')}")
            print(f"   Price: {main_peak_price:.5f}")
            print(f"   Impact: {impact_pips:.1f} pips")
        
        # CRITÈRE 1: Impact > 40 pips
        if impact_pips <= self.min_impact_pips:
            if self.debug:
                print(f"❌ Impact {impact_pips:.1f} pips <= {self.min_impact_pips} pips")
            return None
        
        # CRITÈRE 2: Vérifier absence autre pic dominant (> 90%)
        other_peaks = peaks[peaks.index != main_peak_idx]
        
        if not other_peaks.empty:
            max_other_price = other_peaks['price'].max()
            dominance_ratio = max_other_price / main_peak_price
            
            if dominance_ratio > self.min_peak_dominance:
                if self.debug:
                    print(f"❌ Autre pic {dominance_ratio:.1%} > {self.min_peak_dominance:.0%} (pas Single Wave)")
                return None
        
        # CRITÈRE 3: Chercher pullback APRÈS peak avec garde temporelle
        troughs_after = extrema_df[
            (extrema_df['type'] == 'trough') &
            (extrema_df['datetime'] > main_peak_time)
        ].copy()
        
        pullback_pips = 0
        pullback_ratio = 0
        pullback_point = None
        
        if not troughs_after.empty:
            # Chercher trough avec garde temporelle
            for idx, trough in troughs_after.iterrows():
                trough_time = trough['datetime']
                
                # Valider garde temporelle
                if not self.validate_temporal_guard(main_peak_time, trough_time):
                    continue
                
                # Calculer pullback
                trough_price = trough['price']
                pb_pips = self.to_pips(main_peak_price - trough_price)
                pb_ratio = pb_pips / impact_pips if impact_pips > 0 else 0
                
                # Garder pullback maximum (creux minimum)
                if pb_pips > pullback_pips:
                    pullback_pips = pb_pips
                    pullback_ratio = pb_ratio
                    pullback_point = trough
                    
                    if self.debug:
                        print(f"   Pullback candidat: {trough_time.strftime('%H:%M:%S')} → {pb_ratio:.1%}")
        
        if self.debug and pullback_point is not None:
            print(f"\n📊 PULLBACK TROUVÉ:")
            print(f"   Time: {pullback_point['datetime'].strftime('%H:%M:%S')}")
            print(f"   Price: {pullback_point['price']:.5f}")
            print(f"   Amplitude: {pullback_pips:.1f} pips ({pullback_ratio:.1%})")
        
        # CRITÈRE 4: Pullback < 20%
        if pullback_ratio >= self.max_pullback_ratio:
            if self.debug:
                print(f"❌ Pullback {pullback_ratio:.1%} >= {self.max_pullback_ratio:.0%}")
            return None
        
        # CRITÈRE 5: Valider pullback ratio < 100%
        if not self.validate_pullback_ratio(pullback_ratio):
            return None
        
        # CRITÈRE 6: Valider timestamps distincts
        if pullback_point is not None:
            if not self.validate_timestamps_distinct(main_peak_time, pullback_point['datetime']):
                return None
        
        # Pattern validé
        quality_score = self._calculate_quality_score(impact_pips, pullback_ratio)
        
        if self.debug:
            print(f"\n✅ SINGLE WAVE FORT DÉTECTÉ")
            print(f"   Impact: {impact_pips:.1f} pips")
            print(f"   Pullback: {pullback_ratio:.1%}")
            print(f"   Qualité: {quality_score}/10")
            print(f"{'='*80}\n")
        
        return {
            'baseline': {
                'datetime': event_time - pd.Timedelta(minutes=1),
                'price': baseline_price,
                'type': 'baseline'
            },
            'peak': {
                'datetime': main_peak_time,
                'price': main_peak_price,
                'type': 'peak'
            },
            'pullback': {
                'datetime': pullback_point['datetime'] if pullback_point is not None else None,
                'price': pullback_point['price'] if pullback_point is not None else None,
                'type': 'trough'
            } if pullback_point is not None else None,
            'impact_pips': float(impact_pips),
            'pullback_pips': float(pullback_pips),
            'pullback_ratio': float(pullback_ratio),
            'pattern_type': 'single_wave_fort_v2',
            'quality_score': quality_score,
            'version': 'v2',
            'method': 'adaptive_atr_based'
        }
    
    def _calculate_quality_score(self, impact_pips: float, pullback_ratio: float) -> int:
        """
        Calcule score qualité (0-10)
        
        Args:
            impact_pips: Impact en pips
            pullback_ratio: Ratio pullback
        
        Returns:
            int: Score 0-10
        """
        score = 0
        
        # Impact fort = meilleur
        if impact_pips > 80:
            score += 4
        elif impact_pips > 60:
            score += 3
        elif impact_pips > 50:
            score += 2
        elif impact_pips > 40:
            score += 1
        
        # Pullback faible = meilleur
        if pullback_ratio < 0.05:
            score += 4
        elif pullback_ratio < 0.10:
            score += 3
        elif pullback_ratio < 0.15:
            score += 2
        elif pullback_ratio < 0.20:
            score += 1
        
        # Bonus si très fort impact ET très faible pullback
        if impact_pips > 70 and pullback_ratio < 0.10:
            score += 2
        
        return min(score, 10)


class SingleWaveIntermediateDetectorV2(BasePatternDetectorV2):
    """
    Détecteur Single Wave Intermediate V2 - Approche mathématique adaptative
    
    PATTERN:
    Identique à Single Fort MAIS impact 20-40 pips
    
    CRITÈRES:
    - 1 pic dominant après events
    - Impact 20-40 pips (différence clé vs Fort)
    - Pullback < 20%
    - Garde temporelle respectée
    - Validation ATR
    """
    
    def __init__(
        self,
        min_impact_pips: float = 20.0,
        max_impact_pips: float = 40.0,
        max_pullback_ratio: float = 0.20,
        min_peak_dominance: float = 0.90,
        **kwargs
    ):
        """
        Args:
            min_impact_pips: Impact minimum (défaut 20 pips)
            max_impact_pips: Impact maximum (défaut 40 pips)
            max_pullback_ratio: Pullback maximum (défaut 20%)
            min_peak_dominance: Ratio minimum autre pic (défaut 90%)
            **kwargs: Arguments BasePatternDetectorV2
        """
        super().__init__(**kwargs)
        self.min_impact_pips = min_impact_pips
        self.max_impact_pips = max_impact_pips
        self.max_pullback_ratio = max_pullback_ratio
        self.min_peak_dominance = min_peak_dominance
    
    def detect_pattern(
        self,
        df_ohlc: pd.DataFrame,
        event_time: datetime,
        baseline_price: Optional[float] = None
    ) -> Optional[Dict]:
        """
        Détecte pattern Single Wave Intermediate avec approche mathématique
        
        ALGORITHME: Identique à SingleWaveFortDetectorV2
        DIFFÉRENCE: Filtre impact 20-40 pips (vs > 40 pips)
        """
        # Préparer données
        df = prepare_dataframe(df_ohlc)
        
        if baseline_price is None:
            baseline_price = self.get_baseline_price(df, event_time)
        
        df['ATR'] = self.calculate_atr(df)
        df_after = df[df['datetime'] > event_time].copy()
        
        if df_after.empty:
            return None
        
        if self.debug:
            print(f"\n{'='*80}")
            print(f"🔍 SINGLE WAVE INTERMEDIATE V2 - {event_time.strftime('%Y-%m-%d')}")
            print(f"{'='*80}")
        
        # Trouver extrema
        extrema_df = self.find_local_extrema_adaptive(df, after_time=event_time)
        
        if extrema_df.empty:
            return None
        
        peaks = extrema_df[extrema_df['type'] == 'peak'].copy()
        
        if peaks.empty:
            return None
        
        # Peak maximum
        main_peak = peaks.loc[peaks['price'].idxmax()]
        main_peak_price = main_peak['price']
        main_peak_time = main_peak['datetime']
        
        # Impact
        impact_pips = self.to_pips(main_peak_price - baseline_price)
        
        if self.debug:
            print(f"   Peak: {main_peak_time.strftime('%H:%M:%S')} → {impact_pips:.1f} pips")
        
        # CRITÈRE 1: Impact 20-40 pips
        if impact_pips < self.min_impact_pips or impact_pips > self.max_impact_pips:
            if self.debug:
                print(f"❌ Impact {impact_pips:.1f} hors range [{self.min_impact_pips}-{self.max_impact_pips}] pips")
            return None
        
        # Vérifier dominance
        other_peaks = peaks[peaks['datetime'] != main_peak_time]
        if not other_peaks.empty:
            max_other = other_peaks['price'].max()
            if max_other / main_peak_price > self.min_peak_dominance:
                return None
        
        # Chercher pullback avec garde temporelle
        troughs_after = extrema_df[
            (extrema_df['type'] == 'trough') &
            (extrema_df['datetime'] > main_peak_time)
        ].copy()
        
        pullback_pips = 0
        pullback_ratio = 0
        pullback_point = None
        
        if not troughs_after.empty:
            for idx, trough in troughs_after.iterrows():
                if not self.validate_temporal_guard(main_peak_time, trough['datetime']):
                    continue
                
                pb_pips = self.to_pips(main_peak_price - trough['price'])
                pb_ratio = pb_pips / impact_pips
                
                if pb_pips > pullback_pips:
                    pullback_pips = pb_pips
                    pullback_ratio = pb_ratio
                    pullback_point = trough
        
        # Valider pullback < 20%
        if pullback_ratio >= self.max_pullback_ratio:
            return None
        
        if not self.validate_pullback_ratio(pullback_ratio):
            return None
        
        if pullback_point is not None:
            if not self.validate_timestamps_distinct(main_peak_time, pullback_point['datetime']):
                return None
        
        quality_score = self._calculate_quality_score(impact_pips, pullback_ratio)
        
        if self.debug:
            print(f"✅ SINGLE WAVE INTERMEDIATE DÉTECTÉ")
            print(f"   Impact: {impact_pips:.1f} pips, Pullback: {pullback_ratio:.1%}")
            print(f"{'='*80}\n")
        
        return {
            'baseline': {
                'datetime': event_time - pd.Timedelta(minutes=1),
                'price': baseline_price,
                'type': 'baseline'
            },
            'peak': {
                'datetime': main_peak_time,
                'price': main_peak_price,
                'type': 'peak'
            },
            'pullback': {
                'datetime': pullback_point['datetime'] if pullback_point is not None else None,
                'price': pullback_point['price'] if pullback_point is not None else None,
                'type': 'trough'
            } if pullback_point is not None else None,
            'impact_pips': float(impact_pips),
            'pullback_pips': float(pullback_pips),
            'pullback_ratio': float(pullback_ratio),
            'pattern_type': 'single_wave_intermediate_v2',
            'quality_score': quality_score,
            'version': 'v2',
            'method': 'adaptive_atr_based'
        }
    
    def _calculate_quality_score(self, impact_pips: float, pullback_ratio: float) -> int:
        """Calcule score qualité (adapté pour impacts plus faibles)"""
        score = 0
        
        # Impact dans range cible
        if 30 <= impact_pips <= 40:
            score += 4
        elif 25 <= impact_pips < 30:
            score += 3
        elif 20 <= impact_pips < 25:
            score += 2
        
        # Pullback faible
        if pullback_ratio < 0.05:
            score += 4
        elif pullback_ratio < 0.10:
            score += 3
        elif pullback_ratio < 0.15:
            score += 2
        elif pullback_ratio < 0.20:
            score += 1
        
        # Bonus si impact optimal ET faible pullback
        if 35 <= impact_pips <= 40 and pullback_ratio < 0.10:
            score += 2
        
        return min(score, 10)


if __name__ == "__main__":
    print("SingleWaveDetectorsV2: Utiliser test_detectors_v2_validation.py pour tests")
