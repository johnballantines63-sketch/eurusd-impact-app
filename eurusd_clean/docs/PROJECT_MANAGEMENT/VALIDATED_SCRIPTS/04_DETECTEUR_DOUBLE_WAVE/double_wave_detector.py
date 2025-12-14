"""
Algorithme de détection Double Wave basé sur EXTREMA LOCAUX
Session 118 - Approche mathématique rigoureuse

ALGORITHME:
1. Détecter tous les extrema locaux (peaks & troughs)
2. Identifier pattern W : Trough → Peak → Trough → Peak
3. Valider avec critères mathématiques
4. Sélectionner le meilleur candidat
"""

import duckdb
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict

class DoubleWaveDetector:
    """Détecteur de patterns Double Wave basé sur extrema locaux"""
    
    def __init__(self, min_variation_pips: float = 15.0):
        """
        Args:
            min_variation_pips: Variation minimum pour considérer un extremum (défaut 15 pips)
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
    
    def identify_double_wave_pattern(
        self, 
        extrema_df: pd.DataFrame,
        event_time: Optional[datetime] = None,
        baseline_price: Optional[float] = None
    ) -> Optional[Dict]:
        """
        Identifier pattern Double Wave : Trough → Peak → Trough → Peak
        
        Args:
            extrema_df: DataFrame d'extrema filtrés
            event_time: Timestamp du/des events (optionnel)
            baseline_price: Prix baseline imposé (juste avant events)
        
        Returns:
            Dict avec pattern identifié ou None
        """
        if len(extrema_df) < 3:  # Need only 3: Peak → Trough → Peak (baseline fixé)
            return None
        
        best_pattern = None
        best_score = 0
        
        # Si baseline_price fourni, chercher pattern APRÈS les events
        if baseline_price and event_time:
            # Filtrer extrema APRÈS event_time
            extrema_after = extrema_df[extrema_df['datetime'] > event_time].reset_index(drop=True)
            
            if len(extrema_after) < 3:
                return None
            
            # Chercher pattern: Peak → Trough → Peak (baseline déjà fixé)
            for i in range(len(extrema_after) - 2):
                if (extrema_after.iloc[i]['type'] == 'peak' and
                    extrema_after.iloc[i+1]['type'] == 'trough' and
                    extrema_after.iloc[i+2]['type'] == 'peak'):
                    
                    # Créer baseline avec timestamp CORRECT (14:30)
                    baseline = {
                        'datetime': event_time,  # ← 14:30 (moment des events)
                        'price': baseline_price,
                        'type': 'trough'
                    }
                    
                    peak1 = extrema_after.iloc[i]
                    pullback = extrema_after.iloc[i+1]
                    wave2 = extrema_after.iloc[i+2]
                    
                    # Calculer métriques depuis baseline imposé
                    impact_total = (wave2['price'] - baseline_price) * 10000
                    impact_peak1 = (peak1['price'] - baseline_price) * 10000
                    pullback_pips = (peak1['price'] - pullback['price']) * 10000
                    
                    # Critères validation
                    extension_factor = wave2['price'] / peak1['price'] if peak1['price'] > 0 else 0
                    pullback_ratio = pullback_pips / impact_peak1 if impact_peak1 > 0 else 0
                    
                    # Valider
                    valid = (
                        impact_total > 30 and
                        extension_factor >= 0.95 and
                        extension_factor <= 2.0 and
                        pullback_ratio >= 0.15 and
                        pullback_ratio <= 0.85 and
                        wave2['price'] > baseline_price
                    )
                    
                    if not valid:
                        continue
                    
                    # Score qualité
                    score = 0
                    if 1.2 <= extension_factor <= 1.6:
                        score += 3
                    elif 1.0 <= extension_factor <= 2.0:
                        score += 1
                    
                    if 0.4 <= pullback_ratio <= 0.7:
                        score += 3
                    elif 0.2 <= pullback_ratio <= 0.8:
                        score += 1
                    
                    if impact_total > 50:
                        score += 2
                    elif impact_total > 40:
                        score += 1
                    
                    if score > best_score:
                        best_score = score
                        best_pattern = {
                            'baseline': baseline,
                            'peak1': peak1,
                            'pullback': pullback,
                            'wave2': wave2,
                            'impact_total_pips': float(impact_total),
                            'impact_peak1_pips': float(impact_peak1),
                            'pullback_pips': float(pullback_pips),
                            'pullback_ratio': float(pullback_ratio),
                            'extension_factor': float(extension_factor),
                            'quality_score': score
                        }
            
            return best_pattern
        
        # Sinon, mode original (chercher tous patterns possibles)
        for i in range(len(extrema_df) - 3):
            # Pattern W : Trough → Peak → Trough → Peak
            if (extrema_df.iloc[i]['type'] == 'trough' and
                extrema_df.iloc[i+1]['type'] == 'peak' and
                extrema_df.iloc[i+2]['type'] == 'trough' and
                extrema_df.iloc[i+3]['type'] == 'peak'):
                
                baseline = extrema_df.iloc[i]
                peak1 = extrema_df.iloc[i+1]
                pullback = extrema_df.iloc[i+2]
                wave2 = extrema_df.iloc[i+3]
                
                # Calculer métriques
                impact_total = (wave2['price'] - baseline['price']) * 10000
                impact_peak1 = (peak1['price'] - baseline['price']) * 10000
                pullback_pips = (peak1['price'] - pullback['price']) * 10000
                impact_wave2 = (wave2['price'] - baseline['price']) * 10000
                
                # Critères de validation
                extension_factor = wave2['price'] / peak1['price'] if peak1['price'] > 0 else 0
                pullback_ratio = pullback_pips / impact_peak1 if impact_peak1 > 0 else 0
                
                # Valider critères mathématiques
                valid = (
                    impact_total > 30 and  # Impact minimum 30 pips
                    extension_factor >= 0.95 and  # Wave2 au moins 95% de Peak1
                    extension_factor <= 2.0 and  # Wave2 max 2x Peak1
                    pullback_ratio >= 0.15 and  # Pullback au moins 15%
                    pullback_ratio <= 0.85 and  # Pullback max 85%
                    wave2['price'] > baseline['price']  # Continuation haussière
                )
                
                if not valid:
                    continue
                
                # Calculer score de qualité du pattern
                # Score basé sur: extension idéale, pullback équilibré, timing
                score = 0
                
                # Extension proche de 1.2-1.6x = idéal
                if 1.2 <= extension_factor <= 1.6:
                    score += 3
                elif 1.0 <= extension_factor <= 2.0:
                    score += 1
                
                # Pullback 40-70% = idéal
                if 0.4 <= pullback_ratio <= 0.7:
                    score += 3
                elif 0.2 <= pullback_ratio <= 0.8:
                    score += 1
                
                # Impact total significatif
                if impact_total > 50:
                    score += 2
                elif impact_total > 40:
                    score += 1
                
                # Si event_time fourni, bonus si baseline proche
                if event_time:
                    time_diff = abs((baseline['datetime'] - event_time).total_seconds() / 60)
                    if time_diff < 5:  # Baseline dans les 5 min avant event
                        score += 2
                
                # Garder le meilleur pattern
                if score > best_score:
                    best_score = score
                    best_pattern = {
                        'baseline': baseline,
                        'peak1': peak1,
                        'pullback': pullback,
                        'wave2': wave2,
                        'impact_total_pips': float(impact_total),
                        'impact_peak1_pips': float(impact_peak1),
                        'pullback_pips': float(pullback_pips),
                        'pullback_ratio': float(pullback_ratio),
                        'extension_factor': float(extension_factor),
                        'quality_score': score
                    }
        
        return best_pattern


def test_sept11():
    """Tester algorithme sur 11 septembre 2025"""
    
    print("=" * 80)
    print("🧪 TEST ALGORITHME EVENT-DRIVEN - 11 SEPTEMBRE 2025")
    print("=" * 80)
    
    # Connexion DB
    project_root = Path(__file__).parent.parent.parent
    warehouse_path = project_root / 'data' / 'warehouse.duckdb'
    conn = duckdb.connect(str(warehouse_path), read_only=True)
    
    # Timestamp des events (CPI + Jobless Claims)
    event_time = pd.to_datetime('2025-09-11 14:30:00+02:00')
    
    # ÉTAPE 0: Calculer BASELINE = close de 14:29 (prix juste avant events)
    print(f"\n🎯 ÉTAPE 0: Calcul BASELINE (close juste avant events)...")
    
    baseline_query = """
        SELECT close
        FROM prices_bern
        WHERE datetime = '2025-09-11 14:29:00+02:00'
    """
    
    baseline_result = conn.execute(baseline_query).df()
    if baseline_result.empty:
        print("   ❌ Impossible de trouver prix à 14:29")
        conn.close()
        return None
    
    baseline_price = baseline_result['close'].values[0]  # CLOSE de 14:29
    print(f"   ✅ Baseline (14:29 close): {baseline_price:.5f}")
    print(f"   📍 Events déclenchent à: {event_time.strftime('%H:%M:%S')}")
    
    # Récupérer prix APRÈS les events
    query = """
        SELECT 
            datetime,
            open,
            high,
            low,
            close
        FROM prices_bern
        WHERE datetime >= '2025-09-11 14:30:00'
          AND datetime <= '2025-09-11 15:30:00'
        ORDER BY datetime
    """
    
    df = conn.execute(query).df()
    print(f"\n📊 Chargé {len(df)} bougies 1-min APRÈS events (14:30-15:30)")
    
    # Créer détecteur
    detector = DoubleWaveDetector(min_variation_pips=10)
    
    # ÉTAPE 1: Détecter extrema locaux APRÈS events
    print(f"\n🔍 ÉTAPE 1: Détection extrema locaux APRÈS events...")
    extrema = detector.find_local_extrema(df, window=3)
    print(f"   Trouvé {len(extrema)} extrema bruts")
    
    # ÉTAPE 2: Filtrer extrema significatifs
    print(f"\n🔍 ÉTAPE 2: Filtrage extrema significatifs (> 10 pips)...")
    extrema_filtered = detector.filter_significant_extrema(extrema)
    print(f"   Conservé {len(extrema_filtered)} extrema significatifs")
    
    # Afficher TOUS les troughs bruts pour déboggage
    print(f"\n📊 DEBUG - Tous les troughs détectés (bruts):")
    troughs_all = extrema[extrema['type'] == 'trough']
    for i, trough in troughs_all.iterrows():
        variation_vs_baseline = (trough['price'] - baseline_price) * 10000
        print(f"   🔻 {trough['datetime'].strftime('%H:%M:%S')} - {trough['price']:.5f} [{variation_vs_baseline:+.1f} pips vs baseline]")
    
    # Afficher extrema
    print(f"\n📋 Extrema significatifs détectés APRÈS events:")
    for i, ext in extrema_filtered.iterrows():
        symbol = "🔺" if ext['type'] == 'peak' else "🔻"
        variation_vs_baseline = (ext['price'] - baseline_price) * 10000
        print(f"   {symbol} {ext['datetime'].strftime('%H:%M:%S')} - {ext['price']:.5f} ({ext['type']}) [{variation_vs_baseline:+.1f} pips vs baseline]")
    
    # ÉTAPE 3: Identifier pattern Double Wave avec BASELINE IMPOSÉ
    print(f"\n🔍 ÉTAPE 3: Identification pattern Double Wave (baseline imposé)...")
    pattern = detector.identify_double_wave_pattern(
        extrema_filtered, 
        event_time=event_time,
        baseline_price=baseline_price
    )
    
    # ÉTAPE 3.4: POST-PROCESSING - Trouver le VRAI pullback (minimum absolu)
    if pattern:
        print(f"\n🔍 ÉTAPE 3.4: Post-processing - Recherche pullback optimal (minimum absolu)...")
        
        peak1_time = pattern['peak1']['datetime']
        wave2_initial_time = pattern['wave2']['datetime']
        
        # Chercher TOUS les troughs bruts entre Peak1 et Wave2
        troughs_between = extrema[
            (extrema['type'] == 'trough') &
            (extrema['datetime'] > peak1_time) &
            (extrema['datetime'] < wave2_initial_time)
        ]
        
        if not troughs_between.empty:
            # Trouver le trough minimum (vrai pullback)
            true_pullback = troughs_between.loc[troughs_between['price'].idxmin()]
            
            current_pullback_price = pattern['pullback']['price']
            improvement = (current_pullback_price - true_pullback['price']) * 10000
            
            if improvement > 1:
                print(f"   📉 Pullback plus bas trouvé: {true_pullback['datetime'].strftime('%H:%M:%S')} - {true_pullback['price']:.5f}")
                print(f"   ✅ Pullback mis à jour: {current_pullback_price:.5f} → {true_pullback['price']:.5f} (-{improvement:.1f} pips)")
                
                pattern['pullback'] = true_pullback
                
                # Recalculer métriques
                peak1_price = pattern['peak1']['price']
                pullback_pips = (peak1_price - true_pullback['price']) * 10000
                impact_peak1 = (peak1_price - baseline_price) * 10000
                pattern['pullback_pips'] = float(pullback_pips)
                pattern['pullback_ratio'] = float(pullback_pips / impact_peak1) if impact_peak1 > 0 else 0
            else:
                print(f"   ✅ Pullback initial est déjà le minimum")
        else:
            print(f"   ℹ️ Aucun trough entre Peak1 et Wave2")
    
    # ÉTAPE 3.5: POST-PROCESSING - Chercher le VRAI Wave2 dans TOUS les extrema bruts
    if pattern:
        print(f"\n🔍 ÉTAPE 3.5: Post-processing - Recherche Wave2 optimal (extrema bruts)...")
        
        wave2_initial_time = pattern['wave2']['datetime']
        peak1_price = pattern['peak1']['price']
        
        # Chercher dans TOUS les extrema bruts (pas filtrés) APRÈS Wave2 initial
        remaining_extrema = extrema[extrema['datetime'] > wave2_initial_time]
        
        # Filtrer seulement les peaks (on cherche le Wave2 optimal)
        peaks_after = remaining_extrema[remaining_extrema['type'] == 'peak'].copy()
        
        if not peaks_after.empty:
            print(f"   🔍 Analyse de {len(peaks_after)} peaks après Wave2 initial...")
            
            # Trouver le peak maximum
            max_peak = peaks_after.loc[peaks_after['price'].idxmax()]
            max_peak_price = max_peak['price']
            max_peak_time = max_peak['datetime']
            
            improvement = (max_peak_price - pattern['wave2']['price']) * 10000
            
            if improvement > 1:
                print(f"   📈 Peak plus élevé trouvé: {max_peak_time.strftime('%H:%M:%S')} - {max_peak_price:.5f}")
                print(f"   ✅ Wave2 mis à jour: {pattern['wave2']['price']:.5f} → {max_peak_price:.5f} (+{improvement:.1f} pips)")
                
                pattern['wave2'] = {
                    'datetime': max_peak_time,
                    'price': max_peak_price,
                    'type': 'peak'
                }
                pattern['impact_total_pips'] = (max_peak_price - baseline_price) * 10000
                pattern['extension_factor'] = max_peak_price / peak1_price
            else:
                print(f"   ✅ Wave2 initial est déjà le peak maximum")
        else:
            print(f"   ℹ️ Pas de peak après Wave2, utilisé comme point final")
    
    if pattern:
        print(f"\n✅ PATTERN DOUBLE WAVE IDENTIFIÉ (score qualité: {pattern['quality_score']})")
        print(f"\n📊 POINTS CRITIQUES:")
        print(f"   Baseline:  {pattern['baseline']['datetime'].strftime('%H:%M:%S')} - {pattern['baseline']['price']:.5f} [IMPOSÉ]")
        print(f"   Peak1:     {pattern['peak1']['datetime'].strftime('%H:%M:%S')} - {pattern['peak1']['price']:.5f}")
        print(f"   Pullback:  {pattern['pullback']['datetime'].strftime('%H:%M:%S')} - {pattern['pullback']['price']:.5f}")
        print(f"   Wave2:     {pattern['wave2']['datetime'].strftime('%H:%M:%S')} - {pattern['wave2']['price']:.5f}")
        
        print(f"\n📊 MÉTRIQUES:")
        print(f"   Impact Total:      {pattern['impact_total_pips']:.2f} pips")
        print(f"   Impact Peak1:      {pattern['impact_peak1_pips']:.2f} pips")
        print(f"   Pullback:          {pattern['pullback_pips']:.2f} pips ({pattern['pullback_ratio']:.1%})")
        print(f"   Extension Factor:  {pattern['extension_factor']:.3f}x")
        
        print(f"\n🎯 VALIDATION SESSION 115:")
        print(f"   Impact détecté:    {pattern['impact_total_pips']:.2f} pips")
        print(f"   Référence S115:    56.2 pips")
        print(f"   Différence:        {abs(pattern['impact_total_pips'] - 56.2):.2f} pips")
        
        if abs(pattern['impact_total_pips'] - 56.2) < 2:
            print(f"   ✅ SUCCÈS - Cohérent avec référence !")
        elif abs(pattern['impact_total_pips'] - 56.2) < 5:
            print(f"   ⚠️ Acceptable - Écart {abs(pattern['impact_total_pips'] - 56.2):.2f} pips")
        else:
            print(f"   ❌ Écart significatif")
    else:
        print(f"\n❌ Aucun pattern Double Wave valide trouvé")
    
    conn.close()
    return pattern


if __name__ == '__main__':
    pattern = test_sept11()
