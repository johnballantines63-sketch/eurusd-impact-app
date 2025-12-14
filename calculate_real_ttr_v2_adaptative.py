"""
Version améliorée de calculate_real_ttr_for_phase() avec seuil adaptatif
À intégrer dans sequence_multi_event_timeline.py
"""

import pandas as pd
from typing import Dict

def calculate_real_ttr_for_phase_v2(
    phase: Dict, 
    real_prices_df: pd.DataFrame,
    max_lookback_minutes: int = 60,
    use_adaptive_threshold: bool = True
) -> float:
    """
    Calcule le TTR réel depuis les prix observés avec seuil adaptatif
    
    Version 2 - Améliorations :
    - Seuil adaptatif selon l'amplitude du mouvement
    - Meilleure gestion des mouvements faibles
    - Métadonnées enrichies pour analyse
    
    Args:
        phase: Dict de la phase (avec start, direction, impact_combined, etc.)
        real_prices_df: DataFrame avec colonnes 'time' et 'price'
        max_lookback_minutes: Durée max de recherche (60 min par défaut)
        use_adaptive_threshold: Activer le seuil adaptatif (True par défaut)
    
    Returns:
        float: TTR en minutes, ou TTR théorique si échec
    """
    
    if real_prices_df is None or len(real_prices_df) == 0:
        return phase.get('ttr_predicted', 30)
    
    try:
        # 1. Parser et normaliser le start_time
        start_time = pd.Timestamp(phase['start'])
        if hasattr(start_time, 'tz') and start_time.tz is not None:
            start_time = start_time.tz_localize(None)
        
        # 2. Normaliser les timestamps des prix
        real_prices_clean = real_prices_df.copy()
        if len(real_prices_clean) > 0:
            sample_time = real_prices_clean['time'].iloc[0]
            if hasattr(sample_time, 'tz') and sample_time.tz is not None:
                real_prices_clean['time'] = real_prices_clean['time'].dt.tz_localize(None)
        
        # 3. Filtrer les prix après start_time
        prices_after = real_prices_clean[real_prices_clean['time'] >= start_time].copy()
        
        if len(prices_after) == 0:
            return phase.get('ttr_predicted', 30)
        
        # 4. Limiter à max_lookback
        if len(prices_after) > max_lookback_minutes:
            prices_after = prices_after.iloc[:max_lookback_minutes]
        
        # 5. Prix de référence et direction
        ref_price = prices_after.iloc[0]['price']
        direction = phase.get('direction', 'UP')
        
        # 6. Trouver le peak
        if direction == 'DOWN':
            peak_idx = prices_after['price'].idxmin()
        else:
            peak_idx = prices_after['price'].idxmax()
        
        peak_price = prices_after.loc[peak_idx, 'price']
        peak_minutes = prices_after.index.get_loc(peak_idx)
        
        # 7. Calculer le mouvement en pips
        movement_pips = abs((peak_price - ref_price) * 10000)
        
        # 8. ✨ NOUVEAU : Seuil adaptatif selon le mouvement
        if use_adaptive_threshold:
            if movement_pips < 5:
                retracement_threshold = 0.10  # Très faible → seuil très bas
            elif movement_pips < 10:
                retracement_threshold = 0.15  # Faible → seuil bas
            elif movement_pips < 20:
                retracement_threshold = 0.20  # Moyen → seuil standard
            elif movement_pips < 30:
                retracement_threshold = 0.25  # Fort → seuil élevé
            else:
                retracement_threshold = 0.30  # Très fort → seuil maximal
        else:
            retracement_threshold = 0.30  # Seuil fixe par défaut
        
        # 9. Si mouvement trop faible (< 3 pips), ignorer
        if movement_pips < 3.0:
            phase['ttr_metadata'] = {
                'reason': 'movement_too_small',
                'movement_pips': movement_pips
            }
            return phase.get('ttr_predicted', 30)
        
        # 10. Chercher le retracement après le peak
        if peak_minutes < len(prices_after) - 1:
            for i in range(peak_minutes + 1, len(prices_after)):
                current_price = prices_after.iloc[i]['price']
                
                # Calculer retracement
                if direction == 'DOWN':
                    retracement_pips = (current_price - peak_price) * 10000
                else:
                    retracement_pips = (peak_price - current_price) * 10000
                
                retracement_pct = (retracement_pips / movement_pips * 100) if movement_pips > 0 else 0
                
                # Vérifier si retracement significatif
                if retracement_pips > movement_pips * retracement_threshold:
                    # ✨ Ajouter métadonnées pour analyse
                    phase['ttr_metadata'] = {
                        'movement_pips': movement_pips,
                        'threshold_used': retracement_threshold,
                        'peak_minutes': peak_minutes,
                        'retracement_pct': retracement_pct,
                        'reason': 'success'
                    }
                    return float(i)
        
        # 11. Pas de retracement trouvé → Fallback
        phase['ttr_metadata'] = {
            'movement_pips': movement_pips,
            'threshold_used': retracement_threshold,
            'peak_minutes': peak_minutes,
            'reason': 'no_retracement'
        }
        return phase.get('ttr_predicted', 30)
    
    except Exception as e:
        print(f"❌ Erreur calculate_real_ttr_for_phase_v2: {e}")
        phase['ttr_metadata'] = {'reason': 'error', 'error': str(e)}
        return phase.get('ttr_predicted', 30)


# ═══════════════════════════════════════════════════════════════
# FONCTION COMPLÉMENTAIRE : TTR THÉORIQUE AMÉLIORÉ
# ═══════════════════════════════════════════════════════════════

def calculate_improved_ttr_theoretical(
    impact_pips: float, 
    surprise_pct: float = 0, 
    base_ttr: float = 35
) -> float:
    """
    Calcule un TTR théorique plus réaliste
    
    Basé sur les résultats du backtest :
    - Mouvements faibles (< 10 pips) : TTR court (~20 min)
    - Mouvements moyens (10-30 pips) : TTR moyen (~35 min)
    - Mouvements forts (> 30 pips) : TTR long (~50 min)
    
    Args:
        impact_pips: Impact prédit en pips
        surprise_pct: Surprise en % (optionnel)
        base_ttr: TTR de base (35 min par défaut)
    
    Returns:
        float: TTR théorique en minutes
    """
    
    # Ajustement selon l'impact
    if impact_pips < 10:
        impact_factor = 0.6  # Mouvements faibles → TTR court
    elif impact_pips < 20:
        impact_factor = 0.8
    elif impact_pips < 30:
        impact_factor = 1.0
    elif impact_pips < 50:
        impact_factor = 1.2
    else:
        impact_factor = 1.5  # Mouvements très forts → TTR long
    
    # Ajustement selon la surprise (optionnel)
    if surprise_pct > 0:
        surprise_factor = min(surprise_pct / 50.0, 0.5)  # Max +50%
    else:
        surprise_factor = 0
    
    ttr_theoretical = base_ttr * impact_factor * (1.0 + surprise_factor)
    
    return ttr_theoretical


# ═══════════════════════════════════════════════════════════════
# INSTRUCTIONS D'INTÉGRATION
# ═══════════════════════════════════════════════════════════════

"""
COMMENT INTÉGRER DANS sequence_multi_event_timeline.py :

1. Remplacer l'ancienne fonction par calculate_real_ttr_for_phase_v2()

2. Dans sequence_multi_event_timeline(), modifier :

   AVANT :
   ttr_real = calculate_real_ttr_for_phase(phase, real_prices_df)
   
   APRÈS :
   ttr_real = calculate_real_ttr_for_phase_v2(
       phase, 
       real_prices_df,
       use_adaptive_threshold=True  # Activer seuil adaptatif
   )

3. Utiliser calculate_improved_ttr_theoretical() pour le TTR initial :

   AVANT :
   phase['ttr_predicted'] = max(evt['ttr_median'] for evt in phase['events'])
   
   APRÈS :
   impact_combined = abs(phase['impact_combined'])
   phase['ttr_predicted'] = calculate_improved_ttr_theoretical(impact_combined)

4. Afficher le seuil utilisé dans les notes (optionnel) :

   if 'ttr_metadata' in phase:
       metadata = phase['ttr_metadata']
       note += f"\\n🔧 Seuil: {metadata.get('threshold_used', 0.30)*100:.0f}%, "
       note += f"Mouvement: {metadata.get('movement_pips', 0):.1f} pips"

RÉSULTAT ATTENDU :
- MAE devrait passer de 11.9 à < 10 min
- Couverture devrait augmenter de 100% à ~110% (plus de retracements détectés)
- Précision sur mouvements faibles améliorée
"""
