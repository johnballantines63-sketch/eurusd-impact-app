"""
Détecteurs de patterns EUR/USD - Session 119
Architecture modulaire basée sur extrema locaux

PATTERNS SUPPORTÉS:
- Single Wave Fort (1 pic > 40 pips, pullback < 20%)
- Single Wave Intermediate (1 pic 20-40 pips, pullback < 20%)
- Zig Zag (3+ pics, pullbacks < 20%)
- Double Wave (2 pics, pullback 20-80%) [hérité Session 118]

MÉTHODOLOGIE:
1. Baseline = close(event_time - 1 minute)
2. Extrema locaux (peaks & troughs)
3. Post-processing sur extrema BRUTS (pas filtrés)
4. Validation critères mathématiques stricts
"""

import duckdb
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict
from abc import ABC, abstractmethod
import sys
from pathlib import Path

# Import rev10 detector
sys.path.append(str(Path(__file__).parent))
try:
    from double_wave_detector_rev10 import detect_double_wave_on_df
    REV10_AVAILABLE = True
except ImportError:
    REV10_AVAILABLE = False
    print("Warning: double_wave_detector_rev10 not found. DoubleWaveDetectorRev10 disabled.")


class BasePatternDetector(ABC):
    """Classe de base pour tous les détecteurs de patterns"""
    
    def __init__(self, min_variation_pips: float = 10.0):
        """
        Args:
            min_variation_pips: Variation minimum pour considérer un extremum (défaut 10 pips)
        """
        self.min_variation_pips = min_variation_pips
        self.min_variation_price = min_variation_pips / 10000
    
    def find_local_extrema(self, df: pd.DataFrame, window: int = 3) -> pd.DataFrame:
        """
        Trouver tous les extrema locaux (maxima et minima)
        
        Args:
            df: DataFrame avec colonnes ['datetime', 'high', 'low']
            window: Fenêtre pour détection (défaut 3 = regarde ±3 minutes)
        
        Returns:
            DataFrame avec extrema marqués
        """
        extrema = []
        
        # Détecter maxima locaux (peaks)
        for i in range(window, len(df) - window):
            high_i = df.iloc[i]['high']
            
            # Vérifier si c'est un maximum local
            is_peak = all(high_i >= df.iloc[j]['high'] 
                         for j in range(i - window, i + window + 1) 
                         if j != i)
            
            if is_peak:
                extrema.append({
                    'datetime': df.iloc[i]['datetime'],
                    'price': high_i,
                    'type': 'peak',
                    'index': i
                })
        
        # Détecter minima locaux (troughs)
        for i in range(window, len(df) - window):
            low_i = df.iloc[i]['low']
            
            # Vérifier si c'est un minimum local
            is_trough = all(low_i <= df.iloc[j]['low'] 
                           for j in range(i - window, i + window + 1) 
                           if j != i)
            
            if is_trough:
                extrema.append({
                    'datetime': df.iloc[i]['datetime'],
                    'price': low_i,
                    'type': 'trough',
                    'index': i
                })
        
        # Trier par datetime
        extrema_df = pd.DataFrame(extrema).sort_values('datetime').reset_index(drop=True)
        
        return extrema_df
    
    def filter_significant_extrema(self, extrema_df: pd.DataFrame) -> pd.DataFrame:
        """
        Filtrer les extrema significatifs (variation > seuil)
        
        Args:
            extrema_df: DataFrame d'extrema
        
        Returns:
            DataFrame filtré
        """
        if extrema_df.empty:
            return extrema_df
        
        filtered = [extrema_df.iloc[0]]  # Garder le premier
        
        for i in range(1, len(extrema_df)):
            prev = filtered[-1]
            curr = extrema_df.iloc[i]
            
            # Calculer variation depuis dernier extremum significatif
            variation = abs(curr['price'] - prev['price'])
            
            # Garder seulement si variation > seuil ET type différent
            if variation >= self.min_variation_price and curr['type'] != prev['type']:
                filtered.append(curr)
        
        return pd.DataFrame(filtered).reset_index(drop=True)
    
    def get_events_from_db(self, conn, start_time, end_time):
        """
        Récupère events depuis DB avec enrichissement
        
        Args:
            conn: Connexion DuckDB
            start_time: Timestamp début
            end_time: Timestamp fin
        
        Returns:
            DataFrame events
        """
        query = """
            SELECT ts_utc as datetime, event_title, event_key,
                   country, actual, estimate, previous,
                   importance_n as importance
            FROM events
            WHERE ts_utc >= ? AND ts_utc <= ?
              AND actual IS NOT NULL
            ORDER BY ts_utc
        """
        df = conn.execute(query, [start_time, end_time]).df()
        
        # TODO: Enrichir avec latency_median + empirical_score si nécessaire
        
        return df
    
    def get_baseline_price(self, conn, event_time):
        """
        Calcul baseline = close de la minute AVANT events
        
        Args:
            conn: Connexion DuckDB
            event_time: Timestamp des events
        
        Returns:
            float: Prix close(t-1)
        """
        baseline_time = event_time - timedelta(minutes=1)
        query = f"""
            SELECT close FROM prices_bern
            WHERE datetime = '{baseline_time.strftime('%Y-%m-%d %H:%M:%S%z')}'
        """
        result = conn.execute(query).df()
        
        if result.empty:
            raise ValueError(f"Aucun prix trouvé pour baseline à {baseline_time}")
        
        return result['close'].values[0]
    
    @abstractmethod
    def detect_pattern(self, extrema_df, baseline_price, event_time) -> Optional[Dict]:
        """
        Détecte le pattern spécifique
        
        Args:
            extrema_df: DataFrame extrema (filtrés pour détection initiale)
            baseline_price: Prix baseline
            event_time: Timestamp events
        
        Returns:
            Dict résultat ou None si pattern non détecté
        """
        pass


class SingleWaveFortDetector(BasePatternDetector):
    """
    Détecteur Single Wave Fort (1 pic > 40 pips, pullback < 20%)
    
    PATTERN:
    Baseline → Peak unique > 40 pips → Stabilisation
    
    CRITÈRES:
    - 1 pic dominant après events
    - Impact > 40 pips
    - Pullback < 20% du pic
    - Pas d'autre pic significatif après (> 90% du peak principal)
    """
    
    def detect_pattern(
        self, 
        extrema_df: pd.DataFrame,
        baseline_price: float,
        event_time: datetime,
        extrema_bruts: Optional[pd.DataFrame] = None
    ) -> Optional[Dict]:
        """
        Détecte pattern Single Wave Fort
        
        Args:
            extrema_df: DataFrame extrema filtrés
            baseline_price: Prix baseline (close t-1)
            event_time: Timestamp events
            extrema_bruts: DataFrame extrema NON filtrés (pour post-processing)
        
        Returns:
            Dict avec pattern ou None
        """
        # Filtrer extrema APRÈS event_time
        extrema_after = extrema_df[extrema_df['datetime'] > event_time].reset_index(drop=True)
        
        if extrema_after.empty:
            return None


class DoubleWaveDetectorRev10(BasePatternDetector):
    """
    Wrapper pour double_wave_detector_rev10.py
    Intégration du détecteur mathématique robuste dans architecture Session 119
    
    AVANTAGES REV10:
    - Approche mathématique pure (pas de fenêtres fixes)
    - Seuils adaptatifs (ATR-based)
    - Break-then-Trough rule (Wave2 doit casser Peak1)
    - Confidence score 0-100%
    - Baseline configurable
    
    NOTE: Nécessite DataFrame OHLC complet (pas juste extrema)
    """
    
    def __init__(self, baseline_mode: str = "prev_close_14_29", minutes_after_hint: int = 90):
        """
        Args:
            baseline_mode: Mode calcul baseline ('prev_close_14_29', 'low_14_30', etc.)
            minutes_after_hint: Horizon après 14:30 pour scanner (défaut 90 min)
        """
        super().__init__()
        if not REV10_AVAILABLE:
            raise ImportError("double_wave_detector_rev10 n'est pas disponible")
        self.baseline_mode = baseline_mode
        self.minutes_after_hint = minutes_after_hint
    
    def detect_pattern(
        self,
        extrema_df: pd.DataFrame,  # Non utilisé (rev10 travaille sur OHLC)
        baseline_price: float,     # Non utilisé (rev10 calcule lui-même)
        event_time: datetime,
        extrema_bruts: Optional[pd.DataFrame] = None,  # Non utilisé
        df_ohlc: Optional[pd.DataFrame] = None         # REQUIS pour rev10
    ) -> Optional[Dict]:
        """
        Détecte Double Wave avec rev10 (approche mathématique)
        
        Args:
            df_ohlc: DataFrame OHLC 1-min OBLIGATOIRE (index tz-aware)
                     Colonnes requises: open, high, low, close
            event_time: Timestamp des events (utilisé pour date_label)
            
        Returns:
            Dict format Session 119 ou None
        """
        if df_ohlc is None:
            raise ValueError("DoubleWaveDetectorRev10 nécessite DataFrame OHLC complet (df_ohlc parameter)")
        
        if df_ohlc.empty:
            return None
        
        # Vérifier colonnes OHLC
        required_cols = {'open', 'high', 'low', 'close'}
        if not required_cols.issubset(df_ohlc.columns):
            raise ValueError(f"df_ohlc doit contenir colonnes: {required_cols}")
        
        # Vérifier index tz-aware
        if df_ohlc.index.tz is None:
            raise ValueError("df_ohlc.index doit être tz-aware (utilisez pd.to_datetime(...).dt.tz_localize(...))")
        
        # Appeler rev10
        date_label = event_time.strftime('%Y-%m-%d')
        result_rev10 = detect_double_wave_on_df(
            df_ohlc,
            date_label=date_label,
            symbol="EURUSD",
            tz=str(df_ohlc.index.tz),
            baseline_mode=self.baseline_mode,
            minutes_after_hint=self.minutes_after_hint
        )
        
        if result_rev10 is None:
            return None
        
        # Convertir au format Session 119
        return self._convert_to_session119_format(result_rev10, event_time)
    
    def _convert_to_session119_format(self, rev10_result: Dict, event_time: datetime) -> Dict:
        """
        Convertit résultat rev10 vers format Session 119
        
        REV10 Format:
        {
            'peak1_time', 'peak1_price', 'wave1_amp_pips',
            'pullback1_time', 'pullback1_price', 'pullback1_ratio',
            'peak2_time', 'peak2_price', 'wave2_amp_pips',
            'pullback2_time', 'pullback2_price', 'pullback2_ratio',
            'baseline_time', 'baseline_price',
            'double_wave': bool, 'confidence': float
        }
        
        Session 119 Format:
        {
            'baseline': {...},
            'peak1': {...}, 'pullback': {...},
            'wave2': {...}, 'pullback2': {...},
            'impact_total_pips': float,
            'pattern_type': 'double_wave_rev10',
            'quality_score': int,
            'confidence': float,
            'extension_factor': float,
            'pullback_ratio': float
        }
        """
        # Parse timestamps
        baseline_time = pd.to_datetime(rev10_result['baseline_time'])
        peak1_time = pd.to_datetime(rev10_result['peak1_time'])
        pullback1_time = pd.to_datetime(rev10_result['pullback1_time'])
        peak2_time = pd.to_datetime(rev10_result['peak2_time'])
        
        # Calculer extension factor
        wave1_pips = rev10_result['wave1_amp_pips']
        wave2_pips = rev10_result['wave2_amp_pips']
        extension_factor = wave2_pips / wave1_pips if wave1_pips > 0 else 1.0
        
        # Convertir confidence 0-100 → quality_score 0-10
        quality_score = int(rev10_result['confidence'] / 10)
        
        return {
            # Structure points
            'baseline': {
                'datetime': baseline_time,
                'price': float(rev10_result['baseline_price']),
                'type': 'baseline'
            },
            'peak1': {
                'datetime': peak1_time,
                'price': float(rev10_result['peak1_price']),
                'type': 'peak'
            },
            'pullback': {
                'datetime': pullback1_time,
                'price': float(rev10_result['pullback1_price']),
                'type': 'trough'
            },
            'wave2': {
                'datetime': peak2_time,
                'price': float(rev10_result['peak2_price']),
                'type': 'peak'
            },
            
            # Métriques
            'impact_total_pips': float(wave2_pips),
            'impact_peak1_pips': float(wave1_pips),
            'pullback_pips': float(rev10_result['pullback1_ratio'] * wave1_pips),
            'pullback_ratio': float(rev10_result['pullback1_ratio']),
            'extension_factor': float(extension_factor),
            
            # Meta
            'pattern_type': 'double_wave_rev10',
            'quality_score': quality_score,
            'confidence': float(rev10_result['confidence']),
            'double_wave': bool(rev10_result['double_wave']),
            'direction': rev10_result.get('direction', 'bullish'),
            
            # Données brutes rev10 (pour debugging)
            'rev10_raw': rev10_result
        }
        
        # Trouver tous les peaks après events
        peaks_after = extrema_after[extrema_after['type'] == 'peak']
        
        if peaks_after.empty:
            return None
        
        # Trouver le peak maximum (plus haut prix)
        main_peak = peaks_after.loc[peaks_after['price'].idxmax()]
        main_peak_price = main_peak['price']
        
        # Calculer impact principal
        impact_pips = (main_peak_price - baseline_price) * 10000
        
        # Vérifier impact > 40 pips
        if impact_pips <= 40:
            return None
        
        # POST-PROCESSING: Chercher pullback dans extrema bruts APRÈS peak
        pullback_pips = 0
        pullback_point = None
        
        if extrema_bruts is not None:
            # Chercher troughs dans extrema bruts APRÈS le main peak
            troughs_after = extrema_bruts[
                (extrema_bruts['type'] == 'trough') &
                (extrema_bruts['datetime'] > main_peak['datetime'])
            ]
            
            if not troughs_after.empty:
                # Trouver le trough minimum (plus bas pullback)
                min_trough = troughs_after.loc[troughs_after['price'].idxmin()]
                pullback_pips = (main_peak_price - min_trough['price']) * 10000
                pullback_point = min_trough
        
        # Calculer pullback ratio
        pullback_ratio = pullback_pips / impact_pips if impact_pips > 0 else 0
        
        # Vérifier pullback < 20%
        if pullback_ratio >= 0.20:
            return None
        
        # Vérifier absence autre pic significatif après (> 90% du peak principal)
        # On cherche dans peaks_after s'il y a d'autres pics proches
        other_peaks = peaks_after[peaks_after['datetime'] != main_peak['datetime']]
        
        if not other_peaks.empty:
            max_other_peak = other_peaks['price'].max()
            ratio_other = max_other_peak / main_peak_price
            
            # Si un autre pic > 90% du pic principal, ce n'est pas Single Wave Fort
            if ratio_other > 0.90:
                return None
        
        # Pattern validé
        return {
            'baseline': {
                'datetime': event_time,
                'price': baseline_price,
                'type': 'baseline'
            },
            'peak': main_peak.to_dict(),
            'pullback': pullback_point.to_dict() if pullback_point is not None else None,
            'impact_pips': float(impact_pips),
            'pullback_pips': float(pullback_pips),
            'pullback_ratio': float(pullback_ratio),
            'pattern_type': 'single_wave_fort',
            'quality_score': self._calculate_quality_score(impact_pips, pullback_ratio)
        }
    
    def _calculate_quality_score(self, impact_pips: float, pullback_ratio: float) -> int:
        """
        Calcule score qualité du pattern (0-10)
        
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


class SingleWaveIntermediateDetector(BasePatternDetector):
    """
    Détecteur Single Wave Intermediate (1 pic 20-40 pips, pullback < 20%)
    
    PATTERN:
    Identique à Single Fort MAIS impact 20-40 pips
    
    CRITÈRES:
    - 1 pic dominant après events
    - Impact 20-40 pips (différence clé vs Fort)
    - Pullback < 20%
    - Pas d'autre pic significatif après
    """
    
    def detect_pattern(
        self, 
        extrema_df: pd.DataFrame,
        baseline_price: float,
        event_time: datetime,
        extrema_bruts: Optional[pd.DataFrame] = None
    ) -> Optional[Dict]:
        """
        Détecte pattern Single Wave Intermediate
        
        ALGORITHME: Identique à SingleWaveFortDetector
        DIFFÉRENCE: Filtre impact 20-40 pips (vs > 40 pips)
        """
        # Filtrer extrema APRÈS event_time
        extrema_after = extrema_df[extrema_df['datetime'] > event_time].reset_index(drop=True)
        
        if extrema_after.empty:
            return None
        
        # Trouver tous les peaks après events
        peaks_after = extrema_after[extrema_after['type'] == 'peak']
        
        if peaks_after.empty:
            return None
        
        # Trouver le peak maximum
        main_peak = peaks_after.loc[peaks_after['price'].idxmax()]
        main_peak_price = main_peak['price']
        
        # Calculer impact
        impact_pips = (main_peak_price - baseline_price) * 10000
        
        # Vérifier impact 20-40 pips (différence clé)
        if impact_pips < 20 or impact_pips > 40:
            return None
        
        # POST-PROCESSING: Chercher pullback dans extrema bruts
        pullback_pips = 0
        pullback_point = None
        
        if extrema_bruts is not None:
            troughs_after = extrema_bruts[
                (extrema_bruts['type'] == 'trough') &
                (extrema_bruts['datetime'] > main_peak['datetime'])
            ]
            
            if not troughs_after.empty:
                min_trough = troughs_after.loc[troughs_after['price'].idxmin()]
                pullback_pips = (main_peak_price - min_trough['price']) * 10000
                pullback_point = min_trough
        
        pullback_ratio = pullback_pips / impact_pips if impact_pips > 0 else 0
        
        # Vérifier pullback < 20%
        if pullback_ratio >= 0.20:
            return None
        
        # Vérifier absence autre pic significatif
        other_peaks = peaks_after[peaks_after['datetime'] != main_peak['datetime']]
        
        if not other_peaks.empty:
            max_other_peak = other_peaks['price'].max()
            ratio_other = max_other_peak / main_peak_price
            
            if ratio_other > 0.90:
                return None
        
        # Pattern validé
        return {
            'baseline': {
                'datetime': event_time,
                'price': baseline_price,
                'type': 'baseline'
            },
            'peak': main_peak.to_dict(),
            'pullback': pullback_point.to_dict() if pullback_point is not None else None,
            'impact_pips': float(impact_pips),
            'pullback_pips': float(pullback_pips),
            'pullback_ratio': float(pullback_ratio),
            'pattern_type': 'single_wave_intermediate',
            'quality_score': self._calculate_quality_score(impact_pips, pullback_ratio)
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


class ZigZagDetector(BasePatternDetector):
    """
    Détecteur Zig Zag (3+ pics, pullbacks < 60%)
    
    PATTERN:
    Montée en escalier avec 3+ pics successifs
    
    CRITÈRES:
    - Minimum 3 peaks détectés
    - Pullback < 60% entre chaque peak consécutif (calculé par rapport au segment LOCAL)
    - Peaks croissants (±10% tolérance pour tendance)
    - Impact = somme des amplitudes
    
    NOTE: Critère assoupli à 60% (vs 20% théorique) pour capturer patterns escalier modérés réels
    """
    
    def detect_pattern(
        self, 
        extrema_df: pd.DataFrame,
        baseline_price: float,
        event_time: datetime,
        extrema_bruts: Optional[pd.DataFrame] = None
    ) -> Optional[Dict]:
        """
        Détecte pattern Zig Zag (escalier)
        
        Args:
            extrema_df: DataFrame extrema filtrés
            baseline_price: Prix baseline (close t-1)
            event_time: Timestamp events
            extrema_bruts: DataFrame extrema NON filtrés (pour post-processing)
        
        Returns:
            Dict avec pattern ou None
        """
        # Filtrer extrema APRÈS event_time
        extrema_after = extrema_df[extrema_df['datetime'] > event_time].reset_index(drop=True)
        
        if extrema_after.empty:
            return None
        
        # Trouver tous les peaks après events
        peaks_after = extrema_after[extrema_after['type'] == 'peak'].copy()
        
        if len(peaks_after) < 3:
            return None  # Besoin minimum 3 peaks pour Zig Zag
        
        # Analyser séquence de peaks
        # Pour chaque paire consécutive de peaks, vérifier pullback < 60%
        valid_segments = []
        peaks_list = []
        troughs_list = []
        
        for i in range(len(peaks_after) - 1):
            peak1 = peaks_after.iloc[i]
            peak2 = peaks_after.iloc[i + 1]
            
            peak1_price = peak1['price']
            peak2_price = peak2['price']
            
            # POST-PROCESSING: Chercher le trough minimum ENTRE les deux peaks dans extrema bruts
            trough_price = None
            trough_point = None
            
            if extrema_bruts is not None:
                troughs_between = extrema_bruts[
                    (extrema_bruts['type'] == 'trough') &
                    (extrema_bruts['datetime'] > peak1['datetime']) &
                    (extrema_bruts['datetime'] < peak2['datetime'])
                ]
                
                if not troughs_between.empty:
                    min_trough = troughs_between.loc[troughs_between['price'].idxmin()]
                    trough_price = min_trough['price']
                    trough_point = min_trough
            
            # Si pas de trough trouvé, chercher dans extrema filtrés (fallback)
            if trough_price is None:
                troughs_between_filtered = extrema_after[
                    (extrema_after['type'] == 'trough') &
                    (extrema_after['datetime'] > peak1['datetime']) &
                    (extrema_after['datetime'] < peak2['datetime'])
                ]
                
                if troughs_between_filtered.empty:
                    continue  # Pas de trough entre les deux peaks, segment invalide
                
                min_trough = troughs_between_filtered.loc[troughs_between_filtered['price'].idxmin()]
                trough_price = min_trough['price']
                trough_point = min_trough
            
            # CORRECTION: Calculer amplitude segment LOCAL (pas depuis baseline globale)
            if i == 0:
                # Premier segment: depuis baseline
                segment_base_price = baseline_price
            else:
                # Segments suivants: depuis trough précédent
                prev_trough = troughs_list[-1] if troughs_list else None
                if prev_trough is not None:  # FIX: tester is not None pour pandas Series
                    segment_base_price = prev_trough['price']
                else:
                    segment_base_price = baseline_price
            
            # Amplitude du segment LOCAL
            segment_amplitude = (peak1_price - segment_base_price) * 10000
            
            # Pullback depuis Peak1 jusqu'au trough
            pullback_pips = (peak1_price - trough_price) * 10000
            
            # CRITIQUE: Pullback ratio calculé par rapport à l'amplitude du segment LOCAL
            pullback_ratio = pullback_pips / segment_amplitude if segment_amplitude > 0 else 0
            
            # Vérifier pullback < 60% (assoupli pour Zig Zag - patterns escalier modérés)
            if pullback_ratio >= 0.60:
                break  # Pullback trop fort, arrêter la séquence
            
            # Vérifier tendance continue (peak2 au moins ~90% de peak1, tolérance ±10%)
            ratio_peaks = peak2_price / peak1_price
            if ratio_peaks < 0.90 or ratio_peaks > 1.10:
                # Tendance rompue, mais on garde les segments valides jusqu'ici
                if len(valid_segments) >= 2:  # Si au moins 2 segments valides
                    break
                else:
                    continue
            
            # Segment valide
            valid_segments.append({
                'peak1': peak1.to_dict(),
                'peak2': peak2.to_dict(),
                'trough': trough_point.to_dict() if trough_point is not None else None,
                'amplitude': segment_amplitude,
                'pullback_pips': pullback_pips,
                'pullback_ratio': pullback_ratio
            })
            
            # Stocker peaks et troughs
            if i == 0:
                peaks_list.append(peak1)
            peaks_list.append(peak2)
            
            if trough_point is not None:
                troughs_list.append(trough_point)
        
        # Valider pattern: besoin minimum 2 segments valides (= 3 peaks)
        if len(valid_segments) < 2:
            return None
        
        # Calculer impact total = somme des amplitudes (pour info pattern)
        cumulative_amplitude = sum(seg['amplitude'] for seg in valid_segments)
        
        # Ajouter amplitude finale (dernier peak → peak final)
        last_peak = peaks_list[-1]
        last_trough = troughs_list[-1] if troughs_list else None
        
        if last_trough is not None:
            final_amplitude = (last_peak['price'] - last_trough['price']) * 10000
            cumulative_amplitude += final_amplitude
        
        # MÉTRIQUE PRINCIPALE: Impact net = peak maximum - baseline (pour validation MAE)
        max_peak = max(peaks_list, key=lambda p: p['price'] if isinstance(p, dict) else p['price'])
        max_peak_price = max_peak['price'] if isinstance(max_peak, dict) else max_peak['price']
        total_impact_pips = (max_peak_price - baseline_price) * 10000
        
        # Calculer pullback ratio moyen
        avg_pullback_ratio = np.mean([seg['pullback_ratio'] for seg in valid_segments])
        
        # Pattern validé
        return {
            'baseline': {
                'datetime': event_time,
                'price': baseline_price,
                'type': 'baseline'
            },
            'peaks': [p.to_dict() if hasattr(p, 'to_dict') else p for p in peaks_list],
            'troughs': [t.to_dict() if hasattr(t, 'to_dict') else t for t in troughs_list],
            'segments': valid_segments,
            'num_peaks': len(peaks_list),
            'num_segments': len(valid_segments),
            'total_impact_pips': float(total_impact_pips),  # Métrique principale (peak max - baseline)
            'cumulative_amplitude': float(cumulative_amplitude),  # Info: somme amplitudes segments
            'avg_pullback_ratio': float(avg_pullback_ratio),
            'pattern_type': 'zig_zag',
            'quality_score': self._calculate_quality_score(len(peaks_list), avg_pullback_ratio, total_impact_pips)
        }
    
    def _calculate_quality_score(self, num_peaks: int, avg_pullback_ratio: float, total_impact: float) -> int:
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
        
        # Pullback faible = meilleur
        if avg_pullback_ratio < 0.05:
            score += 3
        elif avg_pullback_ratio < 0.10:
            score += 2
        elif avg_pullback_ratio < 0.15:
            score += 1
        
        # Impact total
        if total_impact > 80:
            score += 3
        elif total_impact > 60:
            score += 2
        elif total_impact > 40:
            score += 1
        
        # Bonus si pattern très régulier (nombreux pics, faibles pullbacks)
        if num_peaks >= 4 and avg_pullback_ratio < 0.10:
            score += 1
        
        return min(score, 10)


class PatternClassifier:
    """
    Classifier automatique de patterns basé sur analyse extrema
    
    LOGIQUE:
    1. Compter peaks significatifs après events
    2. Analyser pullbacks entre peaks
    3. Décider type pattern selon critères
    4. Appliquer détecteur approprié
    
    PATTERNS SUPPORTÉS:
    - Single Wave Fort (1 pic > 40 pips)
    - Single Wave Intermediate (1 pic 20-40 pips)
    - Zig Zag (3+ pics, pullbacks < 60%)
    - Double Wave (2 pics, pullback 20-80%) [Session 118]
    """
    
    def __init__(self):
        """Initialise les détecteurs disponibles"""
        self.detectors = {
            'single_fort': SingleWaveFortDetector(),
            'single_intermediate': SingleWaveIntermediateDetector(),
            'zig_zag': ZigZagDetector()
            # 'double_wave': DoubleWaveDetector()  # TODO: importer depuis Session 118
        }
    
    def classify(self, extrema_df: pd.DataFrame, baseline_price: float, event_time: datetime) -> str:
        """
        Classifie le pattern basé sur analyse extrema
        
        Args:
            extrema_df: DataFrame extrema filtrés
            baseline_price: Prix baseline
            event_time: Timestamp events
        
        Returns:
            str: Type de pattern ('single_fort', 'single_intermediate', 'zig_zag', 'double_wave', 'unknown')
        """
        # Filtrer extrema APRÈS events
        extrema_after = extrema_df[extrema_df['datetime'] > event_time].reset_index(drop=True)
        
        if extrema_after.empty:
            return 'unknown'
        
        # Compter peaks significatifs
        peaks_after = extrema_after[extrema_after['type'] == 'peak']
        num_peaks = len(peaks_after)
        
        if num_peaks == 0:
            return 'unknown'
        
        # Calculer impact maximum
        max_peak = peaks_after.loc[peaks_after['price'].idxmax()]
        max_impact = (max_peak['price'] - baseline_price) * 10000
        
        # CAS 1: Un seul pic
        if num_peaks == 1:
            if max_impact > 40:
                return 'single_fort'
            elif max_impact >= 20:
                return 'single_intermediate'
            else:
                return 'unknown'  # Impact trop faible
        
        # CAS 2: Deux pics
        elif num_peaks == 2:
            # Analyser pullback entre les deux
            peak1 = peaks_after.iloc[0]
            peak2 = peaks_after.iloc[1]
            
            # Chercher trough entre les deux
            troughs_between = extrema_after[
                (extrema_after['type'] == 'trough') &
                (extrema_after['datetime'] > peak1['datetime']) &
                (extrema_after['datetime'] < peak2['datetime'])
            ]
            
            if not troughs_between.empty:
                min_trough = troughs_between.loc[troughs_between['price'].idxmin()]
                
                # Calculer pullback depuis peak1
                amplitude_peak1 = (peak1['price'] - baseline_price) * 10000
                pullback_pips = (peak1['price'] - min_trough['price']) * 10000
                pullback_ratio = pullback_pips / amplitude_peak1 if amplitude_peak1 > 0 else 0
                
                # Double Wave si pullback 20-80%
                if 0.20 <= pullback_ratio <= 0.80:
                    return 'double_wave'
            
            # Sinon, considérer comme Zig Zag (2 pics avec faibles pullbacks)
            return 'zig_zag'
        
        # CAS 3: Trois pics ou plus
        elif num_peaks >= 3:
            # Analyser premiers pullbacks pour décider
            # Si pullbacks < 60%, c'est probablement Zig Zag
            # Sinon, pourrait être pattern complexe non supporté
            
            valid_for_zigzag = True
            
            for i in range(min(2, num_peaks - 1)):  # Vérifier premiers 2 segments
                peak1 = peaks_after.iloc[i]
                peak2 = peaks_after.iloc[i + 1]
                
                # Chercher trough entre
                troughs_between = extrema_after[
                    (extrema_after['type'] == 'trough') &
                    (extrema_after['datetime'] > peak1['datetime']) &
                    (extrema_after['datetime'] < peak2['datetime'])
                ]
                
                if not troughs_between.empty:
                    min_trough = troughs_between.loc[troughs_between['price'].idxmin()]
                    
                    # Base segment LOCAL
                    if i == 0:
                        segment_base = baseline_price
                    else:
                        # Chercher trough précédent
                        prev_peak = peaks_after.iloc[i - 1]
                        troughs_prev = extrema_after[
                            (extrema_after['type'] == 'trough') &
                            (extrema_after['datetime'] > prev_peak['datetime']) &
                            (extrema_after['datetime'] < peak1['datetime'])
                        ]
                        if not troughs_prev.empty:
                            segment_base = troughs_prev.loc[troughs_prev['price'].idxmin()]['price']
                        else:
                            segment_base = baseline_price
                    
                    segment_amplitude = (peak1['price'] - segment_base) * 10000
                    pullback_pips = (peak1['price'] - min_trough['price']) * 10000
                    pullback_ratio = pullback_pips / segment_amplitude if segment_amplitude > 0 else 0
                    
                    # Si pullback > 60%, pas un bon Zig Zag
                    if pullback_ratio >= 0.60:
                        valid_for_zigzag = False
                        break
            
            if valid_for_zigzag:
                return 'zig_zag'
            else:
                return 'unknown'  # Pattern complexe non supporté
        
        return 'unknown'
    
    def detect_best_pattern(
        self, 
        extrema_df: pd.DataFrame,
        baseline_price: float,
        event_time: datetime,
        extrema_bruts: Optional[pd.DataFrame] = None
    ) -> Optional[Dict]:
        """
        Classifie pattern et applique détecteur approprié
        
        Args:
            extrema_df: DataFrame extrema filtrés
            baseline_price: Prix baseline
            event_time: Timestamp events
            extrema_bruts: DataFrame extrema bruts (pour post-processing)
        
        Returns:
            Dict résultat détection ou None
        """
        # Classifier pattern
        pattern_type = self.classify(extrema_df, baseline_price, event_time)
        
        if pattern_type == 'unknown':
            return None
        
        # Double Wave nécessite détecteur spécial (Session 118)
        if pattern_type == 'double_wave':
            # TODO: Implémenter appel DoubleWaveDetector
            return {
                'pattern_type': 'double_wave',
                'status': 'detected_but_not_implemented',
                'message': 'Double Wave détecté - utiliser DoubleWaveDetector Session 118'
            }
        
        # Appliquer détecteur approprié
        if pattern_type in self.detectors:
            detector = self.detectors[pattern_type]
            result = detector.detect_pattern(
                extrema_df,
                baseline_price,
                event_time,
                extrema_bruts=extrema_bruts
            )
            return result
        
        return None
