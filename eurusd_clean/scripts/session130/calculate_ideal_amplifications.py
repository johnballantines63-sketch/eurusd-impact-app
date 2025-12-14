#!/usr/bin/env python3
"""
CALCULER AMPLIFICATIONS IDÉALES - SESSION 130 ÉTAPE 4
======================================================

Pour chaque cas référence, calculer amplification qui prédit exactement l'impact.

FORMULE (Session 115 validée) :
    impact = score × amp × sqrt(n)
    
    Donc : amp_ideal = impact / (score × sqrt(n))

Input : reference_cases.json
Output : reference_cases_with_amplifications.json (enrichi)

Auteur : André Valentin avec Claude
Date : 12 novembre 2025 - Session 130
"""

import json
import duckdb
from pathlib import Path
from datetime import datetime, timedelta
import math
from typing import Dict, List, Optional
import sys

# Import utils timezone
sys.path.insert(0, str(Path(__file__).parent / '../session129'))
from utils_timezone import ensure_bern_time, get_price_window, TZ_BERN

# Chemins
DB_PATH = "data/warehouse.duckdb"
INPUT_FILE = Path(__file__).parent / "reference_cases.json"
OUTPUT_FILE = Path(__file__).parent / "reference_cases_with_amplifications.json"


def load_empirical_scores(conn) -> Dict[str, float]:
    """
    Charge scores empiriques depuis event_families table.
    
    Returns:
        Dict {event_key: score}
    """
    query = """
    SELECT event_key, empirical_score
    FROM event_families
    WHERE empirical_score IS NOT NULL
    """
    
    results = conn.execute(query).fetchall()
    
    scores = {}
    for event_key, score in results:
        scores[event_key.lower().strip()] = float(score)
    
    return scores


def get_event_score(event_key: str, scores_dict: Dict[str, float]) -> Optional[float]:
    """
    Récupère score pour un event_key.
    
    Essaie plusieurs variantes pour matcher.
    """
    event_key_clean = event_key.lower().strip()
    
    # Essai direct
    if event_key_clean in scores_dict:
        return scores_dict[event_key_clean]
    
    # Essai sans suffixes variantes (_mom, _yoy, etc.)
    suffixes = ['_mom', '_yoy', '_qoq', ' mom', ' yoy', ' qoq']
    for suffix in suffixes:
        if event_key_clean.endswith(suffix):
            base_key = event_key_clean[:-len(suffix)]
            if base_key in scores_dict:
                return scores_dict[base_key]
    
    return None


def calculate_cluster_scores(events: List[Dict], scores_dict: Dict[str, float]) -> tuple:
    """
    Calcule score total et compte événements d'un cluster.
    
    Returns:
        (total_score, n_events_with_score, events_details)
    """
    total_score = 0.0
    n_valid = 0
    details = []
    
    for event in events:
        event_key = event['event_key']
        score = get_event_score(event_key, scores_dict)
        
        if score is not None:
            total_score += score
            n_valid += 1
            details.append({
                'event_key': event_key,
                'score': score,
                'country': event.get('country', 'N/A'),
                'importance': event.get('importance', 'N/A')
            })
        else:
            details.append({
                'event_key': event_key,
                'score': None,
                'country': event.get('country', 'N/A'),
                'importance': event.get('importance', 'N/A'),
                'warning': 'Score non trouvé'
            })
    
    return total_score, n_valid, details


def calculate_r2_trend(conn, peak_time_str: str, lookback_hours: int = 168) -> float:
    """
    Calcule R² tendance linéaire sur période pré-événement.
    
    Args:
        peak_time_str: Timestamp peak (ISO format)
        lookback_hours: Heures avant événement (défaut 7 jours)
        
    Returns:
        R² entre 0 et 1
    """
    from sklearn.linear_model import LinearRegression
    import numpy as np
    
    # Parser peak time
    peak_time = ensure_bern_time(peak_time_str)
    
    # Fenêtre prix
    start_time = peak_time - timedelta(hours=lookback_hours)
    
    # Query prix
    query = """
    SELECT datetime, close
    FROM prices_bern
    WHERE datetime BETWEEN ? AND ?
    ORDER BY datetime
    """
    
    prices = conn.execute(query, [start_time, peak_time]).fetchall()
    
    if len(prices) < 10:
        return 0.0
    
    # Régression linéaire
    closes = np.array([p[1] for p in prices])
    X = np.arange(len(closes)).reshape(-1, 1)
    y = closes
    
    model = LinearRegression()
    model.fit(X, y)
    
    r2 = model.score(X, y)
    
    return max(0.0, min(1.0, r2))


def process_reference_case(pattern: str, ref_case: Dict, scores_dict: Dict, conn) -> Dict:
    """
    Traite un cas référence pour calculer amplification idéale.
    
    Returns:
        Dict enrichi avec amp_ideal, total_score, n_events, r2_trend
    """
    print(f"\n{'='*80}")
    print(f"Pattern : {pattern}")
    print(f"{'='*80}")
    print(f"Date : {ref_case['date']}")
    print(f"Impact réel : {ref_case['impact_real']:.2f} pips")
    print(f"Events : {ref_case['n_events']}")
    
    # Calculer scores cluster
    events = ref_case['events']
    total_score, n_valid, details = calculate_cluster_scores(events, scores_dict)
    
    print(f"\n📊 Scores événements :")
    print(f"   Total score : {total_score:.2f}")
    print(f"   Events avec score : {n_valid}/{len(events)}")
    
    if n_valid > 0:
        print(f"\n   Détails events :")
        for i, detail in enumerate(details, 1):
            score = detail['score']
            if score is not None:
                print(f"      {i}. {detail['event_key']:<40s} : {score:>6.2f} ({detail['importance']})")
            else:
                print(f"      {i}. {detail['event_key']:<40s} : {'N/A':>6s} ⚠️")
    
    if total_score == 0 or n_valid == 0:
        print(f"\n⚠️  ATTENTION : Score total nul, impossible calculer amp_ideal")
        return {
            **ref_case,
            'total_score': 0.0,
            'n_events_with_score': 0,
            'amp_ideal': None,
            'r2_trend': None,
            'events_details': details,
            'warning': 'Score total nul'
        }
    
    # Calculer amp_ideal
    sqrt_n = math.sqrt(n_valid)
    amp_ideal = ref_case['impact_real'] / (total_score * sqrt_n)
    
    print(f"\n🎯 Calcul amplification idéale :")
    print(f"   Formule : amp = impact / (score × sqrt(n))")
    print(f"   amp_ideal = {ref_case['impact_real']:.2f} / ({total_score:.2f} × {sqrt_n:.4f})")
    print(f"   amp_ideal = {amp_ideal:.6f}")
    
    # Calculer R² tendance
    print(f"\n📈 Calcul R² tendance (7j avant)...")
    r2_trend = calculate_r2_trend(conn, ref_case['peak_time'], lookback_hours=168)
    print(f"   R² = {r2_trend:.4f}")
    
    # Validation
    impact_predicted = total_score * amp_ideal * sqrt_n
    mae = abs(impact_predicted - ref_case['impact_real'])
    
    print(f"\n✅ Validation :")
    print(f"   Impact prédit : {impact_predicted:.2f} pips")
    print(f"   Impact réel : {ref_case['impact_real']:.2f} pips")
    print(f"   MAE : {mae:.4f} pips")
    
    if mae < 0.01:
        print(f"   🎉 PARFAIT (MAE < 0.01 pips)")
    elif mae < 1.0:
        print(f"   ✅ EXCELLENT (MAE < 1 pips)")
    else:
        print(f"   ⚠️  Erreur résiduelle présente")
    
    return {
        **ref_case,
        'total_score': total_score,
        'n_events_with_score': n_valid,
        'amp_ideal': amp_ideal,
        'r2_trend': r2_trend,
        'events_details': details,
        'validation': {
            'impact_predicted': impact_predicted,
            'mae': mae
        }
    }


def main():
    """Fonction principale"""
    
    print("=" * 80)
    print("CALCULER AMPLIFICATIONS IDÉALES - ÉTAPE 4")
    print("=" * 80)
    
    # Charger cas référence
    print(f"\n📂 Chargement : {INPUT_FILE}")
    
    if not INPUT_FILE.exists():
        print(f"❌ Fichier introuvable : {INPUT_FILE}")
        return 1
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    reference_cases = data['reference_cases']
    print(f"✅ {len(reference_cases)} cas référence chargés")
    
    # Connexion DB
    print(f"\n🔗 Connexion DB...")
    conn = duckdb.connect(DB_PATH, read_only=True)
    print(f"✅ Connecté")
    
    # Charger scores empiriques
    print(f"\n📊 Chargement scores empiriques...")
    scores_dict = load_empirical_scores(conn)
    print(f"✅ {len(scores_dict)} scores chargés")
    
    # Traiter chaque cas référence
    enriched_cases = {}
    
    for pattern, ref_case in reference_cases.items():
        try:
            enriched = process_reference_case(pattern, ref_case, scores_dict, conn)
            enriched_cases[pattern] = enriched
        except Exception as e:
            print(f"\n❌ ERREUR traitement {pattern} : {e}")
            import traceback
            traceback.print_exc()
            enriched_cases[pattern] = {
                **ref_case,
                'error': str(e)
            }
    
    conn.close()
    
    # Résumé
    print(f"\n" + "=" * 80)
    print("RÉSUMÉ AMPLIFICATIONS")
    print("=" * 80)
    
    print(f"\n| {'Pattern':<30s} | {'Date':<12s} | {'Amp Idéale':<12s} | {'R²':<8s} | {'Statut':<10s} |")
    print(f"|{'-'*32}|{'-'*14}|{'-'*14}|{'-'*10}|{'-'*12}|")
    
    for pattern, case in enriched_cases.items():
        amp = case.get('amp_ideal')
        r2 = case.get('r2_trend')
        
        amp_str = f"{amp:.6f}" if amp is not None else "N/A"
        r2_str = f"{r2:.4f}" if r2 is not None else "N/A"
        
        if 'error' in case:
            statut = "❌ Erreur"
        elif amp is None:
            statut = "⚠️ No score"
        else:
            statut = "✅ OK"
        
        print(f"| {pattern:<30s} | {case['date']:<12s} | {amp_str:<12s} | {r2_str:<8s} | {statut:<10s} |")
    
    # Sauvegarde
    print(f"\n" + "=" * 80)
    print("SAUVEGARDE RÉSULTATS")
    print("=" * 80)
    
    output = {
        'metadata': {
            **data['metadata'],
            'amplifications_calculated': datetime.now().isoformat(),
            'lookback_hours_r2': 168
        },
        'reference_cases': enriched_cases,
        'validated_cases': data.get('validated_cases', {})
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Amplifications sauvegardées : {OUTPUT_FILE}")
    print(f"   Taille : {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")
    
    # Validation 11 septembre
    print(f"\n" + "=" * 80)
    print("VALIDATION 11 SEPTEMBRE")
    print("=" * 80)
    
    if 'DoubleWave_Overlap' in enriched_cases:
        dw = enriched_cases['DoubleWave_Overlap']
        if dw['date'] == '2025-09-11':
            print(f"\n✅ 11 septembre traité")
            print(f"   Amp idéale : {dw.get('amp_ideal', 'N/A')}")
            print(f"   R² tendance : {dw.get('r2_trend', 'N/A')}")
            print(f"   Score total : {dw.get('total_score', 'N/A')}")
            
            # Comparer avec Session 115
            ref_amp_s115 = 2.049  # Référence Session 115
            if dw.get('amp_ideal'):
                diff_pct = 100 * abs(dw['amp_ideal'] - ref_amp_s115) / ref_amp_s115
                print(f"\n   Comparaison Session 115 :")
                print(f"   Amp S115 : {ref_amp_s115}")
                print(f"   Amp S130 : {dw['amp_ideal']:.6f}")
                print(f"   Différence : {diff_pct:.1f}%")
                
                if diff_pct < 10:
                    print(f"   ✅ Cohérence excellente (< 10%)")
                elif diff_pct < 25:
                    print(f"   ✅ Cohérence bonne (< 25%)")
                else:
                    print(f"   ⚠️  Différence significative (> 25%)")
    
    print(f"\n" + "=" * 80)
    print("✅ ÉTAPE 4 TERMINÉE")
    print("=" * 80)
    
    print(f"\n🎯 PROCHAINE ÉTAPE : Établir table référence (Étape 5)")
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ ERREUR : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
