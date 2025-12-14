"""
Base Pattern Detector V2 - SESSION 120 REFACTORING
==================================================

OBJECTIF: Refactorer détecteurs Session 119 avec approche mathématique Rev12

CHANGEMENTS MAJEURS vs Session 119:
1. ✅ Seuils adaptatifs ATR-based (plus de paramètres fixes)
2. ✅ Garde temporelle MIN_BARS_BEFORE_PULLBACK
3. ✅ Validation double (temps + amplitude ATR)
4. ✅ Extrema locaux adaptatifs (LOCAL_WIDTH de rev10)
5. ✅ Robustesse à différents régimes volatilité

MÉTHODOLOGIE:
- Baseline = close(event_time - 1 minute)
- ATR 14-périodes pour seuils dynamiques
- Extrema locaux avec LOCAL_WIDTH = 2 (validé Rev12)
- Post-processing sur extrema BRUTS (pas filtrés)
- Validation stricte (timestamps distincts, ratios valides)

RÉFÉRENCE:
- Rev12: MAE 4.5 pips (approche validée)
- Session 118: MAE 4.5 pips (convergence)
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict
from abc import ABC, abstractmethod

# Ajouter session119 au path pour imports
current_dir = Path(__file__).parent
scripts_dir = current_dir.parent
session119_dir = scripts_dir / 'session119'

if str(session119_dir) not in sys.path:
    sys.path.insert(0, str(session119_dir))

# Importer fonctions validées rev10 (approche mathématique)
from double_wave_detector_rev10 import (
    atr1m,                    # Calcul ATR 14-périodes
    to_pips,                  # Conversion prix → pips
    is_local_trough,          # Détection creux local (adaptatif)
    is_local_peak,            # Détection pic local (adaptatif)
    dynamic_thresholds,       # Seuils adaptatifs volatilité
    LOCAL_WIDTH,              # Width extrema locaux (=2)
    MAX_IDLE_BARS            # Stagnation maximum (=20)
)


# ============================================================================
# CONFIGURATION V2
# ============================================================================

# Garde temporelle (validée Rev12)
MIN_BARS_BEFORE_PULLBACK = 3  # Bars minimum entre peak et pullback

# ATR configuration
ATR_PERIOD = 14  # Période ATR standard

# Validation stricte
VALIDATE_TIMESTAMPS = True  # Vérifier timestamps distincts
VALIDATE_PULLBACK_RATIO = True  # Vérifier ratio < 100%

# Debug mode
DEBUG_MODE = False  # Activer pour logs détaillés


# ============================================================================
# BASE CLASS V2
# ============================================================================

class BasePatternDetectorV2(ABC):
    """
    Classe de base V2 - Approche mathématique adaptative
    
    DIFFÉRENCES vs V1 (Session 119):
    - Pas de min_variation_pips fixe → ATR-based
    - Pas de window fixe → LOCAL_WIDTH adaptatif
    - Garde temporelle obligatoire
    - Validation stricte (timestamps, ratios)
    """
    
    def __init__(
        self,
        local_width: int = LOCAL_WIDTH,
        min_bars_before_pullback: int = MIN_BARS_BEFORE_PULLBACK,
        max_idle_bars: int = MAX_IDLE_BARS,
        debug: bool = False
    ):
        """
        Args:
            local_width: Fenêtre extrema locaux (défaut 2 de rev10)
            min_bars_before_pullback: Garde temporelle (défaut 3)
            max_idle_bars: Stagnation max (défaut 20)
            debug: Mode debug logs
        """
        self.local_width = local_width
        self.min_bars_before_pullback = min_bars_before_pullback
        self.max_idle_bars = max_idle_bars
        self.debug = debug or DEBUG_MODE
    
    # ========================================================================
    # MÉTHODES ATR & SEUILS ADAPTATIFS
    # ========================================================================
    
    def calculate_atr(self, df: pd.DataFrame) -> pd.Series:
        """
        Calcule ATR 14-périodes (réutilise fonction rev10)
        
        Args:
            df: DataFrame avec colonnes OHLC
        
        Returns:
            Series ATR
        """
        return atr1m(df)
    
    def get_dynamic_thresholds(self, df: pd.DataFrame) -> Tuple[float, float, float]:
        """
        Calcule seuils adaptatifs selon volatilité (réutilise fonction rev10)
        
        Args:
            df: DataFrame avec ATR calculé
        
        Returns:
            Tuple (w1_min_dd, w2_min_dd, atr_k)
        """
        if 'ATR' not in df.columns:
            df = df.copy()
            df['ATR'] = self.calculate_atr(df)
        
        day_atr_median = float(df['ATR'].median()) if not df['ATR'].empty else 0.0
        atr0 = float(df['ATR'].iloc[0]) if not df['ATR'].empty else day_atr_median
        
        return dynamic_thresholds(day_atr_median, atr0)
    
    # ========================================================================
    # MÉTHODES EXTREMA ADAPTATIFS
    # ========================================================================
    
    def find_local_extrema_adaptive(
        self,
        df: pd.DataFrame,
        after_time: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Trouve extrema locaux avec LOCAL_WIDTH adaptatif (approche rev10)
        
        DIFFÉRENCE vs V1:
        - V1: window=3 FIXE
        - V2: LOCAL_WIDTH=2 adaptatif + validation ATR
        
        Args:
            df: DataFrame avec datetime, high, low
            after_time: Filtrer extrema après ce timestamp (optionnel)
        
        Returns:
            DataFrame extrema
        """
        extrema = []
        
        if after_time is not None:
            df = df[df['datetime'] > after_time].reset_index(drop=True)
        
        if df.empty:
            return pd.DataFrame(columns=['datetime', 'price', 'type', 'index'])
        
        highs = df['high'].values
        lows = df['low'].values
        
        # Détecter peaks (utilise is_local_peak de rev10)
        for i in range(self.local_width, len(df) - self.local_width):
            if is_local_peak(pd.Series(highs), i, self.local_width):
                extrema.append({
                    'datetime': df.iloc[i]['datetime'],
                    'price': highs[i],
                    'type': 'peak',
                    'index': i
                })
        
        # Détecter troughs (utilise is_local_trough de rev10)
        for i in range(self.local_width, len(df) - self.local_width):
            if is_local_trough(pd.Series(lows), i, self.local_width):
                extrema.append({
                    'datetime': df.iloc[i]['datetime'],
                    'price': lows[i],
                    'type': 'trough',
                    'index': i
                })
        
        # Trier par datetime
        if extrema:
            extrema_df = pd.DataFrame(extrema).sort_values('datetime').reset_index(drop=True)
            return extrema_df
        
        return pd.DataFrame(columns=['datetime', 'price', 'type', 'index'])
    
    def filter_significant_extrema_adaptive(
        self,
        extrema_df: pd.DataFrame,
        df_ohlc: pd.DataFrame,
        baseline_price: float
    ) -> pd.DataFrame:
        """
        Filtre extrema significatifs avec seuils ATR-based
        
        DIFFÉRENCE vs V1:
        - V1: min_variation_pips = 10 FIXE
        - V2: Seuil adaptatif selon ATR + amplitude depuis baseline
        
        Args:
            extrema_df: DataFrame extrema bruts
            df_ohlc: DataFrame OHLC avec ATR
            baseline_price: Prix baseline
        
        Returns:
            DataFrame extrema significatifs
        """
        if extrema_df.empty:
            return extrema_df
        
        # Calculer ATR si absent
        if 'ATR' not in df_ohlc.columns:
            df_ohlc = df_ohlc.copy()
            df_ohlc['ATR'] = self.calculate_atr(df_ohlc)
        
        atr_median = df_ohlc['ATR'].median()
        
        filtered = []
        
        for i in range(len(extrema_df)):
            curr = extrema_df.iloc[i]
            
            # Amplitude depuis baseline
            amplitude = abs(curr['price'] - baseline_price)
            amplitude_pips = to_pips(amplitude)
            
            # Seuil adaptatif: minimum 0.5x ATR ou 5 pips
            min_variation = max(atr_median * 0.5, 5.0 / 10000)
            
            # Garder si amplitude > seuil adaptatif
            if amplitude >= min_variation:
                filtered.append(curr)
        
        if filtered:
            return pd.DataFrame(filtered).reset_index(drop=True)
        
        return pd.DataFrame(columns=['datetime', 'price', 'type', 'index'])
    
    # ========================================================================
    # VALIDATION STRICTE
    # ========================================================================
    
    def validate_timestamps_distinct(
        self,
        peak_time: datetime,
        pullback_time: datetime
    ) -> bool:
        """
        Valide que peak et pullback ont timestamps distincts
        
        Args:
            peak_time: Timestamp peak
            pullback_time: Timestamp pullback
        
        Returns:
            bool: True si distincts
        """
        if not VALIDATE_TIMESTAMPS:
            return True
        
        distinct = peak_time != pullback_time
        
        if not distinct and self.debug:
            print(f"⚠️ VALIDATION ÉCHOUÉE: Peak et pullback même timestamp {peak_time}")
        
        return distinct
    
    def validate_temporal_guard(
        self,
        peak_time: datetime,
        current_time: datetime
    ) -> bool:
        """
        Valide garde temporelle (MIN_BARS_BEFORE_PULLBACK)
        
        Args:
            peak_time: Timestamp peak
            current_time: Timestamp actuel
        
        Returns:
            bool: True si garde respectée
        """
        minutes_elapsed = (current_time - peak_time).total_seconds() / 60.0
        
        valid = minutes_elapsed >= self.min_bars_before_pullback
        
        if not valid and self.debug:
            print(f"   Garde temporelle: {minutes_elapsed:.1f} min < {self.min_bars_before_pullback} min")
        
        return valid
    
    def validate_pullback_ratio(
        self,
        pullback_ratio: float,
        max_ratio: float = 1.0
    ) -> bool:
        """
        Valide que pullback ratio < 100% (pas de retombée sous baseline)
        
        Args:
            pullback_ratio: Ratio pullback
            max_ratio: Ratio maximum acceptable (défaut 1.0 = 100%)
        
        Returns:
            bool: True si valide
        """
        if not VALIDATE_PULLBACK_RATIO:
            return True
        
        valid = pullback_ratio < max_ratio
        
        if not valid and self.debug:
            print(f"⚠️ VALIDATION ÉCHOUÉE: Pullback ratio {pullback_ratio:.1%} > {max_ratio:.0%}")
        
        return valid
    
    def validate_amplitude_with_atr(
        self,
        amplitude: float,
        atr_current: float,
        min_atr_multiple: float = 0.4
    ) -> bool:
        """
        Valide amplitude minimum avec filtre ATR (approche rev10)
        
        Args:
            amplitude: Amplitude en prix
            atr_current: ATR actuel
            min_atr_multiple: Multiple minimum ATR (défaut 0.4 de rev10)
        
        Returns:
            bool: True si valide
        """
        min_amplitude = min_atr_multiple * atr_current
        
        valid = amplitude >= min_amplitude
        
        if not valid and self.debug:
            amp_pips = to_pips(amplitude)
            min_pips = to_pips(min_amplitude)
            print(f"   Amplitude {amp_pips:.1f} pips < {min_pips:.1f} pips (ATR filter)")
        
        return valid
    
    # ========================================================================
    # UTILITIES
    # ========================================================================
    
    def get_baseline_price(self, df_ohlc: pd.DataFrame, event_time: datetime) -> float:
        """
        Calcule baseline = close(event_time - 1 minute)
        
        Args:
            df_ohlc: DataFrame OHLC
            event_time: Timestamp events
        
        Returns:
            float: Prix baseline
        """
        baseline_time = event_time - timedelta(minutes=1)
        
        # Chercher close à baseline_time
        baseline_rows = df_ohlc[df_ohlc['datetime'] == baseline_time]
        
        if baseline_rows.empty:
            raise ValueError(f"Aucun prix trouvé pour baseline à {baseline_time}")
        
        return float(baseline_rows.iloc[0]['close'])
    
    def to_pips(self, price_diff: float) -> float:
        """
        Convertit différence de prix en pips
        
        Args:
            price_diff: Différence de prix
        
        Returns:
            float: Pips
        """
        return to_pips(price_diff)
    
    # ========================================================================
    # MÉTHODE ABSTRAITE
    # ========================================================================
    
    @abstractmethod
    def detect_pattern(
        self,
        df_ohlc: pd.DataFrame,
        event_time: datetime,
        baseline_price: Optional[float] = None
    ) -> Optional[Dict]:
        """
        Détecte le pattern spécifique
        
        Args:
            df_ohlc: DataFrame OHLC 1-min (avec datetime en colonne ou index)
            event_time: Timestamp events
            baseline_price: Prix baseline (calculé si None)
        
        Returns:
            Dict résultat ou None si pattern non détecté
        """
        pass


# ============================================================================
# UTILITIES PARTAGÉES
# ============================================================================

def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prépare DataFrame pour détection (datetime en colonne, tz-aware)
    
    Args:
        df: DataFrame brut
    
    Returns:
        DataFrame préparé
    """
    df = df.copy()
    
    # Assurer datetime en colonne
    if 'datetime' not in df.columns:
        if df.index.name == 'datetime' or isinstance(df.index, pd.DatetimeIndex):
            df = df.reset_index()
        else:
            raise ValueError("DataFrame doit avoir colonne ou index 'datetime'")
    
    # Assurer datetime tz-aware
    if df['datetime'].dt.tz is None:
        df['datetime'] = pd.to_datetime(df['datetime']).dt.tz_localize('Europe/Zurich')
    
    # Assurer OHLC
    required_cols = {'datetime', 'open', 'high', 'low', 'close'}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"DataFrame doit contenir colonnes: {required_cols}")
    
    return df.sort_values('datetime').reset_index(drop=True)


if __name__ == "__main__":
    print("BasePatternDetectorV2: Utiliser pour créer détecteurs spécifiques")
    print("Voir: single_wave_detectors_v2.py, zigzag_detector_v2.py")
