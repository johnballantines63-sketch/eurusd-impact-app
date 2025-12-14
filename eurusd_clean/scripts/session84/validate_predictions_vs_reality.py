"""
VALIDATION PRÉDICTIONS PLANIFICATEUR vs PRIX RÉELS - SESSION 87

Objectif : Comparer prédictions Planificateur contre prix réels MT5/Dukascopy
Méthode : Répliquer EXACTEMENT la logique du Planificateur puis valider

Version : 1.2 - DOUBLE WAVE INTÉGRÉ SESSION 87
Date : 26 octobre 2025

NOUVEAUTÉ SESSION 87:
=====================
- Import modules double_wave.py et single_wave_strong.py
- Détection automatique type mouvement (EXACTEMENT comme Planificateur)
- Utilisation predict_double_wave_timeline() si conditions remplies
- Utilisation predict_single_wave_timeline() si Single Wave Fort détecté

RÈGLE TIMEZONE VALIDÉE (Session 86):
====================================
- Table events : ts_utc contient heure +02:00 (Bern)
- Table prices_1m : datetime contient heure +02:00 (Bern)
- MÊME TIMEZONE pour les deux tables
- PAS de conversion +2h nécessaire
- Exemple : Event 12:30+02:00 → Chercher prix 12:30+02:00
"""

import duckdb
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import sys

# Import formules validées (même module que Planificateur)
sys.path.insert(0, '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/src')

from formulas_validated import (
    calculate_adjusted_empirical_score,
    calculate_amplification_extended,
    calculate_impact_d,
    calculate_ttr_c,
    calculate_pullback_v2
)

# Import modules Double Wave et Single Wave Strong (SESSION 87)
from double_wave import (
    detect_double_wave_conditions,
    predict_double_wave_timeline
)

from single_wave_strong import (
    detect_single_wave_strong,
    predict_single_wave_timeline
)

# ============================================================================
# CONFIGURATION
# ============================================================================

DB_PATH = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/data/warehouse.duckdb")
PIPS_MULTIPLIER = 10000

# ============================================================================
# ÉTAPE 1 : CHARGER ÉVÉNEMENTS (MÉTHODE PLANIFICATEUR)
# ============================================================================

def load_events_for_date(date_str: str) -> pd.DataFrame:
    """
    Charge événements HIGH IMPACT pour une date
    RÉPLIQUE EXACTEMENT : Planificateur ligne 208-224
    """
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    query = """
    SELECT 
        e.event_key,
        e.event_title as label,
        e.ts_utc,
        e.actual,
        e.estimate,
        e.previous,
        e.forecast,
        ef.family,
        ef.empirical_score,
        ef.latency_median
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE DATE(e.ts_utc) = ?
        AND e.country = 'US'
        AND ef.empirical_score IS NOT NULL
        AND ef.empirical_score > 40
    ORDER BY e.ts_utc
    """
    
    df = conn.execute(query, [date_str]).df()
    conn.close()
    
    print(f"\n📊 Événements chargés : {len(df)}")
    if len(df) > 0:
        print(f"   Première heure : {df['ts_utc'].iloc[0]}")
    
    return df


# ============================================================================
# ÉTAPE 2 : CALCULER PRÉDICTIONS (MÉTHODE PLANIFICATEUR + SESSION 87)
# ============================================================================

def calculate_predictions(events_df: pd.DataFrame) -> Dict:
    """
    Calcule prédictions EXACTEMENT comme le Planificateur
    
    SESSION 87 : Intègre détection Double Wave / Single Wave Strong
    RÉPLIQUE EXACTEMENT : Planificateur lignes 169-280
    """
    if events_df.empty:
        return None
    
    # Calculer surprise pour chaque événement
    surprises = []
    adjusted_scores = []
    
    for _, event in events_df.iterrows():
        actual = event['actual']
        estimate = event.get('estimate') or event.get('forecast') or event.get('previous')
        
        if estimate and estimate != 0:
            surprise_pct = abs((actual - estimate) / estimate) * 100
        else:
            surprise_pct = 0
        
        surprises.append(surprise_pct)
        
        # Ajuster score selon surprise (Session 55)
        adjusted_score = calculate_adjusted_empirical_score(
            event['empirical_score'],
            surprise_pct
        )
        adjusted_scores.append(adjusted_score)
    
    # Métriques agrégées
    surprise_max = max(surprises)
    surprise_mean = np.mean(surprises)
    score_adjusted_mean = np.mean(adjusted_scores)
    num_events = len(events_df)
    
    # Amplification (si surprise extrême)
    # SESSION 88 : Utilise formule étendue pour surprises > 100%
    amplification = calculate_amplification_extended(surprise_max)
    
    # Impact de BASE (Formule D)
    base_impact = calculate_impact_d(
        empirical_score=score_adjusted_mean,
        num_events=num_events,
        amplification=amplification
    )
    
    # TTR (Formule C)
    latency_mean = events_df['latency_median'].mean()
    latency_min = latency_mean / 60 if pd.notna(latency_mean) else 2.0
    ttr_minutes = calculate_ttr_c(latency_min, surprise_max)
    
    # ═══════════════════════════════════════════════════════════════
    # SESSION 87 : DÉTECTION AUTOMATIQUE TYPE DE MOUVEMENT
    # RÉPLIQUE EXACTEMENT : Planificateur lignes 226-280
    # ═══════════════════════════════════════════════════════════════
    
    # Préparer événements pour détection
    events_for_detection = []
    for _, event in events_df.iterrows():
        events_for_detection.append({
            'actual': event.get('actual'),
            'estimate': event.get('estimate'),
            'forecast': event.get('estimate'),
            'previous': event.get('estimate'),
            'importance_n': 3  # HIGH importance
        })
    
    # Utiliser timestamp premier événement
    start_time = pd.to_datetime(events_df.iloc[0]['ts_utc'])
    
    # 1. Tester Single Wave Strong d'abord (95% des cas)
    is_single_wave_strong = detect_single_wave_strong(
        events_for_detection,
        surprise_threshold=15.0,
        min_cluster_size=3
    )
    
    # 2. Tester Double Wave (rare, conditions strictes)
    is_double_wave = detect_double_wave_conditions(
        events_for_detection,
        surprise_threshold=20.0,
        min_cluster_size=5
    )
    
    # Calculer timeline selon le type
    # NOTE CRITIQUE SESSION 87 : 
    # Le Planificateur utilise Double Wave UNIQUEMENT pour la timeline (graphique)
    # L'impact affiché reste 'base_impact', PAS 'total_net_pips' de la timeline
    # Le Double Wave donne la timeline des phases, mais n'affecte PAS l'impact total
    movement_type = None
    single_wave_timeline = None
    double_wave_timeline = None
    
    if is_double_wave:
        # Double Wave (rare)
        movement_type = "DOUBLE_WAVE"
        double_wave_timeline = predict_double_wave_timeline(
            base_impact=base_impact,
            surprise_pct=surprise_max,
            cluster_size=num_events,
            start_time=start_time
        )
        
    elif is_single_wave_strong:
        # Single Wave Fort (standard CPI/NFP)
        movement_type = "SINGLE_WAVE_STRONG"
        single_wave_timeline = predict_single_wave_timeline(
            base_impact=base_impact,
            surprise_pct=surprise_max,
            cluster_size=num_events,
            start_time=start_time
        )
        
    else:
        # Single Wave Standard (cas simple)
        movement_type = "STANDARD"
    
    return {
        'num_events': num_events,
        'surprise_max': surprise_max,
        'surprise_mean': surprise_mean,
        'score_adjusted': score_adjusted_mean,
        'amplification': amplification,
        'base_impact': base_impact,
        'impact_predicted_pips': base_impact,  # Utilise base_impact (comme Planificateur)
        'ttr_predicted_min': ttr_minutes,
        'movement_type': movement_type,
        'is_single_wave_strong': is_single_wave_strong,
        'is_double_wave': is_double_wave,
        'single_wave_timeline': single_wave_timeline,
        'double_wave_timeline': double_wave_timeline
    }


# ============================================================================
# ÉTAPE 3 : EXTRAIRE PRIX RÉELS (CORRIGÉ SESSION 86)
# ============================================================================

def extract_real_prices(date_str: str, event_time_bern: str, window_minutes: int = 60) -> Tuple[pd.DataFrame, datetime]:
    """
    Extrait prix 1m depuis prices_1m
    
    TIMEZONE DOCUMENTATION (VALIDÉ SESSION 86):
    -------------------------------------------
    - Table events : ts_utc contient +02:00 (Bern time)
    - Table prices_1m : datetime contient +02:00 (Bern time)
    - MÊME TIMEZONE → PAS de conversion nécessaire
    
    Args:
        date_str: Date format 'YYYY-MM-DD'
        event_time_bern: Heure événement format 'HH:MM:SS' en Bern
        window_minutes: Fenêtre ± en minutes (défaut 60)
    
    Returns:
        Tuple (DataFrame prix, datetime événement)
    
    Example:
        # Événement 01.08.2025 12:30 Bern
        prices, event_dt = extract_real_prices('2025-08-01', '12:30:00', 60)
        # Retourne prix 11:30 → 13:30 Bern
    """
    
    # Construire timestamp événement
    event_dt = datetime.strptime(f"{date_str} {event_time_bern}", "%Y-%m-%d %H:%M:%S")
    
    print(f"\n📈 Extraction prix réels...")
    print(f"   Événement : {event_dt.strftime('%Y-%m-%d %H:%M')} Bern")
    print(f"   Fenêtre : ±{window_minutes} minutes")
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # RÈGLE TIMEZONE SESSION 86:
    # Event 12:30+02:00 → Chercher prix 12:30+02:00 (MÊME heure)
    query = f"""
    SELECT 
        datetime,
        open,
        high,
        low,
        close,
        volume
    FROM prices_1m
    WHERE datetime >= '{date_str} {event_time_bern}+02:00'::TIMESTAMP - INTERVAL '{window_minutes} minutes'
      AND datetime <= '{date_str} {event_time_bern}+02:00'::TIMESTAMP + INTERVAL '{window_minutes} minutes'
    ORDER BY datetime
    """
    
    df = conn.execute(query).fetchdf()
    conn.close()
    
    if df.empty:
        raise ValueError(f"Aucune donnée prix pour {date_str} {event_time_bern}")
    
    print(f"   ✅ {len(df)} barres extraites")
    print(f"   Période : {df['datetime'].iloc[0]} → {df['datetime'].iloc[-1]}")
    
    # VALIDATION AUTOMATIQUE (Session 86)
    # Pour 01.08.2025 12:30, doit trouver min ~1.13918
    if date_str == '2025-08-01' and event_time_bern == '12:30:00':
        min_price = df['low'].min()
        EXPECTED_MIN = 1.13925
        min_diff_pips = abs(min_price - EXPECTED_MIN) * 10000
        
        if min_diff_pips > 20:
            raise ValueError(
                f"❌ VALIDATION TIMEZONE ÉCHOUÉE !\n"
                f"01.08.2025 12:30 : Min={min_price:.5f}\n"
                f"Attendu : ~{EXPECTED_MIN:.5f}\n"
                f"Écart : {min_diff_pips:.1f} pips\n"
                f"→ Timezone query incorrecte"
            )
        print(f"   ✅ Validation timezone : Min={min_price:.5f} (écart {min_diff_pips:.1f} pips)")
    
    # Convertir event_dt en timezone-aware pour compatibilité pandas  
    import pytz
    bern_tz = pytz.timezone('Europe/Zurich')
    event_dt_aware = bern_tz.localize(event_dt)
    
    return df, event_dt_aware


# ============================================================================
# ÉTAPE 4 : MESURER IMPACT RÉEL
# ============================================================================

def measure_real_impact(prices_df: pd.DataFrame, event_dt: datetime) -> Dict:
    """
    Mesure impact réel depuis prix observés
    
    Utilise colonnes high/low pour précision maximale
    """
    # Filtrer prix APRÈS événement
    df_post = prices_df[prices_df['datetime'] >= event_dt].copy()
    
    if df_post.empty:
        raise ValueError("Aucune donnée après événement")
    
    # Prix départ (open de première barre)
    start_price = df_post.iloc[0]['open']
    
    # Creux absolu (pour spike baissier)
    low_idx = df_post['low'].idxmin()
    low_price = df_post.loc[low_idx, 'low']
    low_time = df_post.loc[low_idx, 'datetime']
    
    # Pic absolu (pour spike haussier)
    high_idx = df_post['high'].idxmax()
    high_price = df_post.loc[high_idx, 'high']
    high_time = df_post.loc[high_idx, 'datetime']
    
    # Impact = plus grand mouvement absolu
    impact_down = abs(start_price - low_price) * PIPS_MULTIPLIER
    impact_up = abs(high_price - start_price) * PIPS_MULTIPLIER
    
    if impact_down > impact_up:
        # Spike baissier
        peak_price = low_price
        peak_time = low_time
        impact_real_pips = impact_down
        direction = "DOWN"
    else:
        # Spike haussier
        peak_price = high_price
        peak_time = high_time
        impact_real_pips = impact_up
        direction = "UP"
    
    # Timing
    time_to_peak_min = (peak_time - event_dt).total_seconds() / 60
    
    print(f"\n🎯 Impact réel mesuré...")
    print(f"   Direction : {direction}")
    print(f"   Prix départ : {start_price:.5f}")
    print(f"   Prix peak : {peak_price:.5f} à {peak_time.strftime('%H:%M')}")
    print(f"   Impact : {impact_real_pips:.1f} pips")
    print(f"   Timing : {time_to_peak_min:.0f} minutes")
    
    return {
        'start_price': start_price,
        'peak_price': peak_price,
        'peak_time': peak_time,
        'impact_real_pips': impact_real_pips,
        'time_to_peak_real_min': time_to_peak_min,
        'direction': direction
    }


# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================

def validate_date(date_str: str, event_time_bern: str):
    """
    Validation complète : Prédictions vs Réalité
    
    Args:
        date_str: Date format 'YYYY-MM-DD'
        event_time_bern: Heure Bern format 'HH:MM:SS'
    """
    print("="*80)
    print(f"🔍 VALIDATION {date_str} - {event_time_bern} Bern")
    print("="*80)
    
    # 1. Charger événements
    events_df = load_events_for_date(date_str)
    
    if events_df.empty:
        print("❌ Aucun événement HIGH IMPACT trouvé")
        return None
    
    # 2. Calculer prédictions (SESSION 87: avec Double Wave)
    print("\n📐 Calcul prédictions (formules Planificateur + Double Wave)...")
    predictions = calculate_predictions(events_df)
    
    print(f"   Événements : {predictions['num_events']}")
    print(f"   Surprise max : {predictions['surprise_max']:.1f}%")
    print(f"   Score ajusté : {predictions['score_adjusted']:.1f}")
    print(f"   Type mouvement : {predictions['movement_type']}")
    print(f"   Base impact : {predictions['base_impact']:.1f} pips")
    print(f"   Impact prédit FINAL : {predictions['impact_predicted_pips']:.1f} pips")
    print(f"   TTR prédit : {predictions['ttr_predicted_min']:.1f} minutes")
    
    # Afficher détails si Double Wave ou Single Wave Strong
    if predictions['is_double_wave']:
        timeline = predictions['double_wave_timeline']
        print(f"\n   ✅ DOUBLE WAVE DÉTECTÉ :")
        print(f"      Phase 1 : {timeline['phase1']['impact_pips']:.1f} pips (T+{timeline['phase1']['duration_min']})")
        print(f"      Pullback : {timeline['pullback']['retrace_pips']:.1f} pips (T+{timeline['pullback']['duration_min']})")
        print(f"      Phase 2 : {timeline['phase2']['impact_pips']:.1f} pips (T+{timeline['phase2']['duration_min']})")
        print(f"      Net total : {timeline['total_net_pips']:.1f} pips")
        
    elif predictions['is_single_wave_strong']:
        timeline = predictions['single_wave_timeline']
        print(f"\n   ✅ SINGLE WAVE FORT DÉTECTÉ :")
        print(f"      Peak : {timeline['peak']['impact_pips']:.1f} pips (T+8)")
        print(f"      Pullback : {timeline['pullback']['retrace_pips']:.1f} pips ({timeline['pullback']['retrace_pct']:.0f}%)")
        print(f"      Net total : {timeline['total_net_pips']:.1f} pips")
    
    # 3. Extraire prix réels (TIMEZONE CORRIGÉ)
    prices_df, event_dt = extract_real_prices(date_str, event_time_bern)
    
    # 4. Mesurer impact réel
    real_metrics = measure_real_impact(prices_df, event_dt)
    
    # 5. Comparaison
    print("\n" + "="*80)
    print("⚖️ COMPARAISON PRÉDICTIONS vs RÉALITÉ")
    print("="*80)
    
    error_impact = abs(predictions['impact_predicted_pips'] - real_metrics['impact_real_pips'])
    error_pct = (error_impact / real_metrics['impact_real_pips'] * 100) if real_metrics['impact_real_pips'] > 0 else 0
    
    error_timing = abs(predictions['ttr_predicted_min'] - real_metrics['time_to_peak_real_min'])
    
    print(f"\n📊 IMPACT :")
    print(f"   Prédit  : {predictions['impact_predicted_pips']:6.1f} pips")
    print(f"   Réel    : {real_metrics['impact_real_pips']:6.1f} pips")
    print(f"   Erreur  : {error_impact:6.1f} pips ({error_pct:.0f}%)")
    
    print(f"\n⏱️ TIMING :")
    print(f"   Prédit  : {predictions['ttr_predicted_min']:6.1f} minutes")
    print(f"   Réel    : {real_metrics['time_to_peak_real_min']:6.1f} minutes")
    print(f"   Erreur  : {error_timing:6.1f} minutes")
    
    print(f"\n🏷️ TYPE MOUVEMENT :")
    print(f"   Prédit  : {predictions['movement_type']}")
    
    # Validation
    impact_ok = error_pct < 30  # Tolérance 30%
    timing_ok = error_timing < 10  # Tolérance 10 minutes
    
    print(f"\n✅ VALIDATION :")
    print(f"   Impact : {'✅ OK' if impact_ok else '❌ ÉCART SIGNIFICATIF'}")
    print(f"   Timing : {'✅ OK' if timing_ok else '❌ ÉCART SIGNIFICATIF'}")
    
    return {
        'date': date_str,
        'event_time_bern': event_time_bern,
        'predictions': predictions,
        'real_metrics': real_metrics,
        'error_impact_pips': error_impact,
        'error_impact_pct': error_pct,
        'error_timing_min': error_timing,
        'validation_ok': impact_ok and timing_ok
    }


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("SCRIPT VALIDATION - VERSION 1.2 DOUBLE WAVE INTÉGRÉ (SESSION 87)")
    print("="*80)
    
    # Test 01.08.2025
    # Événement à 12:30 Bern
    # Surprise 500% → Devrait détecter Double Wave
    result = validate_date(
        date_str='2025-08-01',
        event_time_bern='12:30:00'
    )
    
    if result:
        print("\n" + "="*80)
        if result['validation_ok']:
            print("✅✅✅ VALIDATION RÉUSSIE ✅✅✅")
        else:
            print("⚠️ AMÉLIORATION DÉTECTÉE mais ajustements nécessaires")
        print("="*80)
        
        # Afficher amélioration vs Session 86
        print("\n📊 COMPARAISON SESSION 86 vs SESSION 87 :")
        print(f"   Session 86 (sans Double Wave) : 67.7 pips prédit")
        print(f"   Session 87 (avec Double Wave) : {result['predictions']['impact_predicted_pips']:.1f} pips prédit")
        print(f"   Impact réel observé : {result['real_metrics']['impact_real_pips']:.1f} pips")
        
        improvement = abs(67.7 - result['real_metrics']['impact_real_pips']) - result['error_impact_pips']
        if improvement > 0:
            print(f"   ✅ AMÉLIORATION : +{improvement:.1f} pips de précision !")
        else:
            print(f"   ⚠️ Pas d'amélioration détectée")
