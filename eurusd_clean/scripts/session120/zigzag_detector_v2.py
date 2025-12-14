"""
ZigZag Detector V2 - SESSION 120 REFACTORING
=============================================

PATTERN:
Montée en escalier avec 3+ pics successifs

AMÉLIORATIONS vs V1 (Session 119):
✅ Seuils adaptatifs ATR-based (plus de 10 pips fixes)
✅ Garde temporelle MIN_BARS_BEFORE_PULLBACK = 3
✅ Validation double (temps + amplitude ATR)
✅ Extrema locaux adaptatifs (LOCAL_WIDTH = 2)
✅ Pullback calculé par segment LOCAL (pas global)

CRITÈRES:
- Minimum 3 peaks détectés
- Pullback < 60% entre chaque peak consécutif (segment LOCAL)
- Peaks croissants (±10% tolérance tendance)
- Garde temporelle respectée
- Impact net = peak maximum - baseline

MÉTHODOLOGIE:
- Baseline = close(event_time - 1 minute)
- Scanner peaks successifs après events
- Valider pullback entre chaque paire (avec garde temporelle)
- Calculer amplitude segment LOCAL (pas depuis baseline globale)
- Impact total = somme amplitudes segments (info)
- Impact net = peak max - baseline (métrique principale validation)
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, Dict, List

# Import base V2
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from base_pattern_detector_v2 import (
    BasePatternDetectorV2,
    prepare_dataframe
)


class ZigZagDetectorV2(BasePatternDetectorV2):
    """
    Détecteur Zig Zag V2 - Approche mathématique adaptative
    
    PATTERN:
    Baseline → Peak1 → Trough1 → Peak2 → Trough2 → Peak3+ → Stabilisation
    
    CRITÈRES STRICTS:
    - Minimum 3 peaks (= 2 segments validés)
    - Pullback < 60% par segment (assoupli vs 20% théorique)
    - Garde temporelle respectée (MIN_BARS entre peak et trough)
    - Validation ATR (amplitudes significatives)
    - Tendance continue (peaks ±10% tolérance)
    
    MÉTRIQUE PRINCIPALE:
    - Impact net = peak maximum - baseline (pour validation MAE)
    - Impact cumulé = somme amplitudes segments (info pattern)
    """
    
    def __init__(
        self,
        min_peaks: int = 3,
        max_pullback_ratio: float = 0.60,  # Assoupli pour Zig Zag réels
        min_trend_ratio: float = 0.90,      # Tolérance tendance ±10%
        max_trend_ratio: float = 1.10,
        **kwargs
    ):
        """
        Args:
            min_peaks: Nombre minimum peaks (défaut 3)
            max_pullback_ratio: Pullback maximum par segment (défaut 60%)
            min_trend_ratio: Ratio minimum peak suivant vs précédent (défaut 90%)
            max_trend_ratio: Ratio maximum peak suivant vs précédent (défaut 110%)
            **kwargs: Arguments BasePatternDetectorV2
        """
        super().__init__(**kwargs)
        self.min_peaks = min_peaks
        self.max_pullback_ratio = max_pullback_ratio
        self.min_trend_ratio = min_trend_ratio
        self.max_trend_ratio = max_trend_ratio
    
    def detect_pattern(
        self,
        df_ohlc: pd.DataFrame,
        event_time: datetime,
        baseline_price: Optional[float] = None
    ) -> Optional[Dict]:
        """
        Détecte pattern Zig Zag avec approche mathématique
        
        Args:
            df_ohlc: DataFrame OHLC 1-min
            event_time: Timestamp events
            baseline_price: Prix baseline (calculé si None)
        
        Returns:
            Dict résultat ou None
        """
        # Préparer données
        df = prepare_dataframe(df_ohlc)
        
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
            print(f"🔍 ZIG ZAG V2 - {event_time.strftime('%Y-%m-%d')}")
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
        
        if len(peaks) < self.min_peaks:
            if self.debug:
                print(f"❌ Seulement {len(peaks)} peaks < {self.min_peaks} minimum")
            return None
        
        if self.debug:
            print(f"\n📊 ANALYSE SÉQUENCE ZIG ZAG:")
            print(f"   Peaks détectés: {len(peaks)}")
        
        # Analyser séquence de segments (peak → trough → peak)
        valid_segments = []
        peaks_list = []
        troughs_list = []
        
        segment_base_price = baseline_price  # Base du premier segment
        
        for i in range(len(peaks) - 1):
            peak1 = peaks.iloc[i]
            peak2 = peaks.iloc[i + 1]
            
            peak1_price = peak1['price']
            peak1_time = peak1['datetime']
            peak2_price = peak2['price']
            peak2_time = peak2['datetime']
            
            if self.debug:
                print(f"\n   Segment {i+1}: Peak1 @ {peak1_time.strftime('%H:%M')} → Peak2 @ {peak2_time.strftime('%H:%M')}")
            
            # CHERCHER TROUGH ENTRE LES DEUX PEAKS (avec garde temporelle)
            troughs_between = extrema_df[
                (extrema_df['type'] == 'trough') &
                (extrema_df['datetime'] > peak1_time) &
                (extrema_df['datetime'] < peak2_time)
            ].copy()
            
            if troughs_between.empty:
                if self.debug:
                    print(f"      ❌ Pas de trough entre peaks")
                break  # Pas de trough, arrêter séquence
            
            # Chercher trough avec garde temporelle
            valid_trough = None
            
            for idx, trough_candidate in troughs_between.iterrows():
                trough_time = trough_candidate['datetime']
                
                # Valider garde temporelle depuis Peak1
                if not self.validate_temporal_guard(peak1_time, trough_time):
                    continue
                
                # Valider garde temporelle jusqu'à Peak2
                if not self.validate_temporal_guard(trough_time, peak2_time):
                    continue
                
                # Trough valide trouvé (prendre le plus bas)
                if valid_trough is None or trough_candidate['price'] < valid_trough['price']:
                    valid_trough = trough_candidate
            
            if valid_trough is None:
                if self.debug:
                    print(f"      ❌ Aucun trough avec garde temporelle valide")
                break
            
            trough_price = valid_trough['price']
            trough_time = valid_trough['datetime']
            
            # CALCULER AMPLITUDE SEGMENT LOCAL (correction majeure vs V1)
            # Premier segment: depuis baseline
            # Segments suivants: depuis trough précédent
            segment_amplitude = self.to_pips(peak1_price - segment_base_price)
            
            # Pullback depuis Peak1 jusqu'au trough
            pullback_pips = self.to_pips(peak1_price - trough_price)
            
            # CRITIQUE: Pullback ratio par rapport à amplitude segment LOCAL
            pullback_ratio = pullback_pips / segment_amplitude if segment_amplitude > 0 else 0
            
            if self.debug:
                print(f"      Trough @ {trough_time.strftime('%H:%M')} (garde temporelle OK)")
                print(f"      Amplitude segment: {segment_amplitude:.1f} pips")
                print(f"      Pullback: {pullback_pips:.1f} pips ({pullback_ratio:.1%})")
            
            # VALIDATION 1: Pullback < 60% (assoupli pour Zig Zag)
            if pullback_ratio >= self.max_pullback_ratio:
                if self.debug:
                    print(f"      ❌ Pullback {pullback_ratio:.1%} >= {self.max_pullback_ratio:.0%}")
                break  # Pullback trop fort, arrêter séquence
            
            # VALIDATION 2: Pullback < 100% (pas de retombée sous base segment)
            if not self.validate_pullback_ratio(pullback_ratio):
                break
            
            # VALIDATION 3: Tendance continue (peak2 environ même niveau que peak1)
            ratio_peaks = peak2_price / peak1_price
            
            if ratio_peaks < self.min_trend_ratio or ratio_peaks > self.max_trend_ratio:
                if self.debug:
                    print(f"      ⚠️ Tendance rompue: Peak2/Peak1 = {ratio_peaks:.2f}")
                # Tendance rompue, mais on garde segments valides jusqu'ici
                if len(valid_segments) >= (self.min_peaks - 1):  # Au moins 2 segments = 3 peaks
                    break
                else:
                    continue
            
            # Segment valide
            valid_segments.append({
                'segment_num': i + 1,
                'peak1': {
                    'datetime': peak1_time,
                    'price': peak1_price
                },
                'peak2': {
                    'datetime': peak2_time,
                    'price': peak2_price
                },
                'trough': {
                    'datetime': trough_time,
                    'price': trough_price
                },
                'segment_base_price': segment_base_price,
                'amplitude': segment_amplitude,
                'pullback_pips': pullback_pips,
                'pullback_ratio': pullback_ratio
            })
            
            # Stocker peaks et troughs
            if i == 0:
                peaks_list.append(peak1)
            peaks_list.append(peak2)
            troughs_list.append(valid_trough)
            
            # Base du prochain segment = trough actuel
            segment_base_price = trough_price
            
            if self.debug:
                print(f"      ✅ Segment {i+1} validé")
        
        # VALIDATION PATTERN: Besoin minimum 2 segments (= 3 peaks)
        if len(valid_segments) < (self.min_peaks - 1):
            if self.debug:
                print(f"\n❌ Seulement {len(valid_segments)} segments < {self.min_peaks-1} minimum")
            return None
        
        if self.debug:
            print(f"\n✅ {len(valid_segments)} segments validés ({len(peaks_list)} peaks)")
        
        # CALCULER MÉTRIQUES
        
        # Impact cumulé = somme amplitudes segments (info pattern)
        cumulative_amplitude = sum(seg['amplitude'] for seg in valid_segments)
        
        # Amplitude finale (dernier trough → dernier peak)
        last_peak = peaks_list[-1]
        last_trough = troughs_list[-1] if troughs_list else None
        
        if last_trough is not None:
            final_segment_base = last_trough['price']
            final_amplitude = self.to_pips(last_peak['price'] - final_segment_base)
            cumulative_amplitude += final_amplitude
        
        # MÉTRIQUE PRINCIPALE: Impact net = peak maximum - baseline (validation MAE)
        max_peak = max(peaks_list, key=lambda p: p['price'])
        max_peak_price = max_peak['price']
        total_impact_pips = self.to_pips(max_peak_price - baseline_price)
        
        # Pullback ratio moyen
        avg_pullback_ratio = np.mean([seg['pullback_ratio'] for seg in valid_segments])
        
        # Quality score
        quality_score = self._calculate_quality_score(
            len(peaks_list),
            avg_pullback_ratio,
            total_impact_pips
        )
        
        if self.debug:
            print(f"\n📊 MÉTRIQUES FINALES:")
            print(f"   Impact net (peak max - baseline): {total_impact_pips:.1f} pips")
            print(f"   Impact cumulé (somme segments): {cumulative_amplitude:.1f} pips")
            print(f"   Pullback moyen: {avg_pullback_ratio:.1%}")
            print(f"   Quality score: {quality_score}/10")
            print(f"{'='*80}\n")
        
        # Pattern validé
        return {
            'baseline': {
                'datetime': event_time - pd.Timedelta(minutes=1),
                'price': baseline_price,
                'type': 'baseline'
            },
            'peaks': [
                {
                    'datetime': p['datetime'],
                    'price': p['price'],
                    'type': 'peak'
                } for p in peaks_list
            ],
            'troughs': [
                {
                    'datetime': t['datetime'],
                    'price': t['price'],
                    'type': 'trough'
                } for t in troughs_list
            ],
            'segments': valid_segments,
            'num_peaks': len(peaks_list),
            'num_segments': len(valid_segments),
            'total_impact_pips': float(total_impact_pips),       # Métrique principale (validation)
            'cumulative_amplitude': float(cumulative_amplitude),  # Info pattern
            'avg_pullback_ratio': float(avg_pullback_ratio),
            'pattern_type': 'zig_zag_v2',
            'quality_score': quality_score,
            'version': 'v2',
            'method': 'adaptive_atr_based'
        }
    
    def _calculate_quality_score(
        self,
        num_peaks: int,
        avg_pullback_ratio: float,
        total_impact: float
    ) -> int:
        """
        Calcule score qualité du pattern Zig Zag (0-10)
        
        Args:
            num_peaks: Nombre de peaks
            avg_pullback_ratio: Pullback ratio moyen
            total_impact: Impact total en pips
        
        Returns:
            int: Score 0-10
        """
        score = 0
        
        # Nombre de peaks (plus = mieux)
        if num_peaks >= 5:
            score += 3
        elif num_peaks >= 4:
            score += 2
        elif num_peaks >= 3:
            score += 1
        
        # Pullback faible = meilleur (pattern régulier)
        if avg_pullback_ratio < 0.10:
            score += 3
        elif avg_pullback_ratio < 0.20:
            score += 2
        elif avg_pullback_ratio < 0.40:
            score += 1
        
        # Impact total net
        if total_impact > 80:
            score += 3
        elif total_impact > 60:
            score += 2
        elif total_impact > 40:
            score += 1
        
        # Bonus si pattern très régulier (nombreux pics, faibles pullbacks)
        if num_peaks >= 4 and avg_pullback_ratio < 0.20:
            score += 1
        
        return min(score, 10)


if __name__ == "__main__":
    print("ZigZagDetectorV2: Utiliser test_detectors_v2_validation.py pour tests")
