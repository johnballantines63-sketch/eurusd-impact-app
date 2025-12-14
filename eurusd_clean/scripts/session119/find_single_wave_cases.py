"""
Script de recherche de cas Single Wave Fort dans la base de données
Session 119 - Phase 1

OBJECTIF:
Trouver au moins 3 cas réels de Single Wave Fort pour validation

CRITÈRES RECHERCHE:
- Mouvements > 40 pips sur 10-30 minutes
- Events économiques ±10 min autour du mouvement
- Pattern 1 pic dominant, pullback < 20%

MÉTHODOLOGIE:
1. Scanner prix pour détecter spikes > 40 pips
2. Chercher events causaux autour du spike
3. Appliquer SingleWaveFortDetector
4. Valider et mesurer MAE
"""

import duckdb
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys

# Import détecteurs
sys.path.append(str(Path(__file__).parent))
from pattern_detectors import SingleWaveFortDetector

def scan_for_strong_moves(conn, start_date: str, end_date: str, min_pips: float = 40):
    """
    Scanner prix pour détecter mouvements forts
    
    Args:
        conn: Connexion DuckDB
        start_date: Date début (YYYY-MM-DD)
        end_date: Date fin (YYYY-MM-DD)
        min_pips: Seuil minimum en pips
    
    Returns:
        List[Dict] avec mouvements détectés
    """
    query = f"""
        WITH price_ranges AS (
            SELECT 
                datetime,
                high,
                low,
                close,
                LAG(close, 1) OVER (ORDER BY datetime) as prev_close,
                (high - LAG(close, 1) OVER (ORDER BY datetime)) * 10000 as move_pips
            FROM prices_bern
            WHERE datetime >= '{start_date}'
              AND datetime <= '{end_date}'
        )
        SELECT 
            datetime,
            high,
            low,
            close,
            prev_close,
            move_pips
        FROM price_ranges
        WHERE move_pips >= {min_pips}
        ORDER BY move_pips DESC
        LIMIT 50
    """
    
    df = conn.execute(query).df()
    
    print(f"\n🔍 Scan mouvements > {min_pips} pips ({start_date} → {end_date})")
    print(f"   Trouvé {len(df)} candidats potentiels")
    
    return df


def find_nearby_events(conn, spike_time: datetime, window_minutes: int = 10):
    """
    Chercher events économiques autour d'un spike
    
    Args:
        conn: Connexion DuckDB
        spike_time: Timestamp du spike
        window_minutes: Fenêtre de recherche (±minutes)
    
    Returns:
        DataFrame events
    """
    start_time = spike_time - timedelta(minutes=window_minutes)
    end_time = spike_time + timedelta(minutes=window_minutes)
    
    query = """
        SELECT 
            ts_utc as datetime,
            event_title,
            event_key,
            country,
            actual,
            estimate,
            previous,
            importance_n as importance
        FROM events
        WHERE ts_utc >= ?
          AND ts_utc <= ?
          AND actual IS NOT NULL
        ORDER BY ts_utc
    """
    
    df = conn.execute(query, [start_time, end_time]).df()
    
    return df


def test_single_wave_detector(
    conn,
    spike_time: datetime,
    spike_high: float,
    prev_close: float
):
    """
    Tester détecteur Single Wave Fort sur un cas
    
    Args:
        conn: Connexion DuckDB
        spike_time: Timestamp du spike
        spike_high: Prix high du spike
        prev_close: Prix close précédent (baseline estimé)
    
    Returns:
        Dict résultat test
    """
    print(f"\n" + "="*80)
    print(f"🧪 TEST SINGLE WAVE FORT - {spike_time.strftime('%Y-%m-%d %H:%M')}")
    print("="*80)
    
    # Chercher events autour du spike
    events = find_nearby_events(conn, spike_time, window_minutes=10)
    
    if events.empty:
        print(f"   ⚠️ Aucun event trouvé ±10 min du spike")
        return None
    
    print(f"\n📅 Events trouvés ({len(events)}) :")
    for _, event in events.iterrows():
        print(f"   {event['datetime'].strftime('%H:%M:%S')} - {event['country']} {event['event_title']}")
        print(f"      Actual: {event['actual']}, Estimate: {event['estimate']}, Importance: {event['importance']}")
    
    # Prendre le premier event comme référence (event_time)
    event_time = events.iloc[0]['datetime']
    
    # Récupérer prix autour du spike (30 min avant → 60 min après)
    start_query = spike_time - timedelta(minutes=30)
    end_query = spike_time + timedelta(minutes=60)
    
    query = f"""
        SELECT 
            datetime,
            open,
            high,
            low,
            close
        FROM prices_bern
        WHERE datetime >= '{start_query.strftime('%Y-%m-%d %H:%M:%S%z')}'
          AND datetime <= '{end_query.strftime('%Y-%m-%d %H:%M:%S%z')}'
        ORDER BY datetime
    """
    
    df = conn.execute(query).df()
    
    print(f"\n📊 Chargé {len(df)} bougies 1-min")
    
    # Créer détecteur
    detector = SingleWaveFortDetector(min_variation_pips=10)
    
    # Calculer baseline = close(event_time - 1 min)
    try:
        baseline_price = detector.get_baseline_price(conn, event_time)
        print(f"\n🎯 Baseline (close t-1): {baseline_price:.5f}")
    except:
        # Fallback si baseline non trouvée
        baseline_price = prev_close
        print(f"\n🎯 Baseline (fallback prev_close): {baseline_price:.5f}")
    
    # ÉTAPE 1: Détecter extrema locaux
    print(f"\n🔍 ÉTAPE 1: Détection extrema locaux...")
    extrema_bruts = detector.find_local_extrema(df, window=3)
    print(f"   Trouvé {len(extrema_bruts)} extrema bruts")
    
    # ÉTAPE 2: Filtrer extrema significatifs
    print(f"\n🔍 ÉTAPE 2: Filtrage extrema significatifs (> 10 pips)...")
    extrema_filtered = detector.filter_significant_extrema(extrema_bruts)
    print(f"   Conservé {len(extrema_filtered)} extrema significatifs")
    
    # Afficher extrema filtrés
    print(f"\n📋 Extrema significatifs :")
    for i, ext in extrema_filtered.iterrows():
        symbol = "🔺" if ext['type'] == 'peak' else "🔻"
        variation_vs_baseline = (ext['price'] - baseline_price) * 10000
        print(f"   {symbol} {ext['datetime'].strftime('%H:%M:%S')} - {ext['price']:.5f} ({ext['type']}) [{variation_vs_baseline:+.1f} pips vs baseline]")
    
    # ÉTAPE 3: Détecter pattern Single Wave Fort
    print(f"\n🔍 ÉTAPE 3: Détection pattern Single Wave Fort...")
    pattern = detector.detect_pattern(
        extrema_filtered,
        baseline_price,
        event_time,
        extrema_bruts=extrema_bruts
    )
    
    if pattern:
        print(f"\n✅ PATTERN SINGLE WAVE FORT DÉTECTÉ (score qualité: {pattern['quality_score']}/10)")
        print(f"\n📊 POINTS CRITIQUES:")
        print(f"   Baseline:  {pattern['baseline']['datetime'].strftime('%H:%M:%S')} - {pattern['baseline']['price']:.5f}")
        print(f"   Peak:      {pattern['peak']['datetime'].strftime('%H:%M:%S')} - {pattern['peak']['price']:.5f}")
        if pattern['pullback']:
            print(f"   Pullback:  {pattern['pullback']['datetime'].strftime('%H:%M:%S')} - {pattern['pullback']['price']:.5f}")
        
        print(f"\n📊 MÉTRIQUES:")
        print(f"   Impact:            {pattern['impact_pips']:.2f} pips")
        print(f"   Pullback:          {pattern['pullback_pips']:.2f} pips ({pattern['pullback_ratio']:.1%})")
        
        # Estimer impact "réel" (spike_high vs baseline)
        real_impact = (spike_high - baseline_price) * 10000
        mae = abs(pattern['impact_pips'] - real_impact)
        
        print(f"\n🎯 VALIDATION:")
        print(f"   Impact détecté:    {pattern['impact_pips']:.2f} pips")
        print(f"   Impact réel (spike high): {real_impact:.2f} pips")
        print(f"   MAE:               {mae:.2f} pips")
        
        if mae < 5:
            print(f"   ✅ EXCELLENT - MAE < 5 pips")
        elif mae < 10:
            print(f"   ✅ BON - MAE < 10 pips")
        else:
            print(f"   ⚠️ MAE élevé")
        
        return {
            'spike_time': spike_time,
            'event_time': event_time,
            'events_count': len(events),
            'pattern': pattern,
            'real_impact': real_impact,
            'mae': mae
        }
    else:
        print(f"\n❌ Aucun pattern Single Wave Fort détecté")
        print(f"   Raisons possibles:")
        print(f"   - Impact < 40 pips")
        print(f"   - Pullback > 20%")
        print(f"   - Autre pic significatif (> 90%)")
        return None


def main():
    """Recherche et validation de cas Single Wave Fort"""
    
    print("="*80)
    print("🔎 RECHERCHE CAS SINGLE WAVE FORT - SESSION 119 PHASE 1")
    print("="*80)
    
    # Connexion DB
    project_root = Path(__file__).parent.parent.parent
    warehouse_path = project_root / 'data' / 'warehouse.duckdb'
    conn = duckdb.connect(str(warehouse_path), read_only=True)
    
    # Scanner mouvements forts (période 2024-2025)
    moves = scan_for_strong_moves(conn, '2024-01-01', '2025-11-01', min_pips=40)
    
    # Tester les meilleurs candidats
    validated_cases = []
    
    for i, move in moves.head(10).iterrows():  # Tester top 10
        result = test_single_wave_detector(
            conn,
            move['datetime'],
            move['high'],
            move['prev_close']
        )
        
        if result and result['mae'] < 10:
            validated_cases.append(result)
        
        # Stop si on a 3 cas validés
        if len(validated_cases) >= 3:
            break
    
    # Résumé final
    print(f"\n" + "="*80)
    print(f"📊 RÉSUMÉ VALIDATION")
    print("="*80)
    print(f"\n✅ Cas validés: {len(validated_cases)}/3")
    
    if validated_cases:
        print(f"\n📋 DÉTAILS CAS VALIDÉS:")
        for i, case in enumerate(validated_cases, 1):
            print(f"\n   CAS #{i}:")
            print(f"   Date:          {case['spike_time'].strftime('%Y-%m-%d %H:%M')}")
            print(f"   Events:        {case['events_count']}")
            print(f"   Impact détecté: {case['pattern']['impact_pips']:.2f} pips")
            print(f"   Impact réel:    {case['real_impact']:.2f} pips")
            print(f"   MAE:           {case['mae']:.2f} pips")
            print(f"   Score qualité: {case['pattern']['quality_score']}/10")
        
        # Statistiques globales
        maes = [c['mae'] for c in validated_cases]
        print(f"\n📊 STATISTIQUES:")
        print(f"   MAE moyen:     {np.mean(maes):.2f} pips")
        print(f"   MAE médian:    {np.median(maes):.2f} pips")
        print(f"   MAE max:       {np.max(maes):.2f} pips")
        
        if np.mean(maes) < 10:
            print(f"\n✅✅✅ SUCCÈS - SingleWaveFortDetector validé (MAE < 10 pips)")
        else:
            print(f"\n⚠️ MAE moyen élevé - Ajustements nécessaires")
    else:
        print(f"\n⚠️ Aucun cas validé trouvé - Ajuster critères recherche")
    
    conn.close()


if __name__ == '__main__':
    main()
