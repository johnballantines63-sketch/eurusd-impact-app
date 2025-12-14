"""
PLANIFICATEUR V3 - CAS D'ÉCOLE 11 SEPTEMBRE 2025
=================================================

Objectif: Valider les 4 formules sur le cas de référence 11 septembre
Comparaison: Prédiction vs Réalité MT5

Date: 23 octobre 2025 - Session 57
Auteur: André Valentin avec Claude
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import duckdb

# Ajouter le chemin vers fx_impact_app/src
src_path = Path(__file__).parent / "fx_impact_app" / "src"
sys.path.insert(0, str(src_path))

from formulas_validated import (
    calculate_adjusted_empirical_score,
    calculate_impact_d,
    calculate_ttr_c,
    calculate_pullback_v2
)
from config import get_db_path


# ═══════════════════════════════════════════════════════════════
# DONNÉES DE RÉFÉRENCE MT5 (11 septembre 2025)
# ═══════════════════════════════════════════════════════════════

MT5_REFERENCE = {
    'prix_depart': 1.16816,  # 12:30 UTC (14:30 Berne)
    'prix_ttr_phase1': 1.17190,  # 12:35 UTC (TTR Phase 1)
    'prix_apres_pullback': 1.16919,  # 12:45 UTC (après pullback)
    'prix_stabilisation': 1.17378,  # 13:10 UTC (stabilisation)
    'phase1_impact': 37.4,  # pips
    'pullback_reel': 27.1,  # pips
    'phase2_impact': 45.9,  # pips
    'mouvement_net': 56.2  # pips
}


# ═══════════════════════════════════════════════════════════════
# ÉTAPE 1 : RÉCUPÉRATION DONNÉES 11 SEPTEMBRE
# ═══════════════════════════════════════════════════════════════

def get_events_11_sept():
    """
    Récupère les événements du 11 septembre 2025
    
    Returns:
        list: Liste d'événements avec leurs données
    """
    conn = duckdb.connect(str(get_db_path()), read_only=True)
    
    query = """
    SELECT 
        e.event_key,
        e.label as family,
        e.ts_utc,
        e.actual,
        e.estimate,
        e.previous,
        ef.empirical_score,
        ef.latency_median,
        ef.ttr_median
    FROM events e
    LEFT JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
    WHERE DATE(e.ts_utc) = '2025-09-11'
        AND e.country = 'US'
        AND ef.empirical_score IS NOT NULL
        AND ef.empirical_score > 40
    ORDER BY e.ts_utc
    """
    
    df = conn.execute(query).df()
    conn.close()
    
    if df.empty:
        print("❌ Aucun événement trouvé pour le 11 septembre 2025")
        return []
    
    events = []
    for _, row in df.iterrows():
        # Calculer surprise
        actual = row['actual']
        estimate = row['estimate']
        
        if actual is not None and estimate is not None and estimate != 0:
            surprise = actual - estimate
            surprise_pct = abs((actual - estimate) / estimate) * 100
        else:
            surprise = 0
            surprise_pct = 0
        
        event = {
            'event_key': row['event_key'],
            'family': row['family'],
            'ts_utc': row['ts_utc'],
            'actual': actual,
            'estimate': estimate,
            'previous': row['previous'],
            'empirical_score': row['empirical_score'],
            'surprise': surprise,
            'surprise_pct': surprise_pct,
            'latency_median': row['latency_median'] / 60 if row['latency_median'] else 2.0,  # Convertir en minutes
            'ttr_median': row['ttr_median'] / 60 if row['ttr_median'] else 10.0
        }
        
        events.append(event)
    
    return events


# ═══════════════════════════════════════════════════════════════
# ÉTAPE 2 : AGRÉGATION ÉVÉNEMENTS CPI (9 → 1)
# ═══════════════════════════════════════════════════════════════

def aggregate_cpi_events(events):
    """
    Agrège les 9 événements CPI en un seul événement représentatif
    
    Args:
        events: Liste des événements
    
    Returns:
        dict: Événement CPI agrégé
    """
    # Filtrer les CPI (14:30 heure locale Berne = 12:30 UTC)
    # ATTENTION: La colonne ts_utc contient en fait l'heure locale !
    cpi_events = [e for e in events if e['ts_utc'].hour == 14 and e['ts_utc'].minute == 30]
    
    if not cpi_events:
        print("⚠️ Aucun événement CPI trouvé à 14:30 (heure locale)")
        return None
    
    # IMPORTANT: Choisir l'événement avec la PLUS GRANDE SURPRISE
    # (pas le plus grand score, car les scores ne tiennent pas compte de la surprise)
    cpi_principal = max(cpi_events, key=lambda x: abs(x['surprise_pct']))
    
    print(f"\n📊 AGRÉGATION CPI:")
    print(f"   - {len(cpi_events)} événements CPI à 14:30 (heure locale)")
    print(f"   - Événement principal: {cpi_principal['family']}")
    print(f"   - Score base: {cpi_principal['empirical_score']:.1f}")
    print(f"   - Surprise: {cpi_principal['surprise_pct']:.1f}%")
    print(f"   - Actual: {cpi_principal.get('actual')}")
    print(f"   - Estimate: {cpi_principal.get('estimate')}")
    
    return {
        'family': f"{cpi_principal['family']} (agrégé)",
        'ts_utc': cpi_principal['ts_utc'],
        'empirical_score': cpi_principal['empirical_score'],
        'surprise_pct': cpi_principal['surprise_pct'],
        'latency_median': cpi_principal['latency_median'],
        'num_events': len(cpi_events)
    }


# ═══════════════════════════════════════════════════════════════
# ÉTAPE 3 : CALCUL PHASE 1 (CPI)
# ═══════════════════════════════════════════════════════════════

def calculate_phase_1(cpi_event, prix_depart):
    """
    Calcule Phase 1: Annonce CPI 12:30 UTC
    
    Args:
        cpi_event: Événement CPI agrégé
        prix_depart: Prix de départ
    
    Returns:
        dict: Résultats Phase 1
    """
    print(f"\n🚀 PHASE 1 - ANNONCE CPI (12:30 UTC)")
    print(f"   Prix départ: {prix_depart:.5f}")
    
    # 1. Ajustement score
    adjusted_score = calculate_adjusted_empirical_score(
        base_empirical_score=cpi_event['empirical_score'],
        surprise_pct=cpi_event['surprise_pct']
    )
    
    print(f"   Score base: {cpi_event['empirical_score']:.1f}")
    print(f"   Score ajusté: {adjusted_score:.1f}")
    
    # 2. Amplification dynamique
    if abs(cpi_event['surprise_pct']) > 30:
        amplification = 2.5
    elif abs(cpi_event['surprise_pct']) > 15:
        amplification = 2.0
    else:
        amplification = 1.5
    
    print(f"   Amplification: {amplification}x")
    
    # 3. Impact
    # IMPORTANT: Les événements CPI simultanés sont traités comme UN SEUL événement agrégé
    # Le score ajusté capture déjà l'effet de la surprise
    # On utilise num_events=1 pour éviter la double amplification
    impact_pips = calculate_impact_d(
        empirical_score=adjusted_score,
        num_events=1,  # ✅ Traité comme 1 événement agrégé
        amplification=amplification
    )
    
    print(f"   Impact prédit: {impact_pips:.1f} pips")
    print(f"   Impact MT5: {MT5_REFERENCE['phase1_impact']:.1f} pips")
    print(f"   Écart: {abs(impact_pips - MT5_REFERENCE['phase1_impact']):.1f} pips")
    
    # 4. TTR
    ttr_minutes = calculate_ttr_c(
        latency_minutes=cpi_event['latency_median'],
        surprise_pct=cpi_event['surprise_pct']
    )
    
    print(f"   TTR prédit: {ttr_minutes:.1f} min")
    print(f"   TTR réel: 5.0 min")
    
    # 5. Prix peak
    prix_peak = prix_depart + (impact_pips * 0.0001)
    print(f"   Prix peak prédit: {prix_peak:.5f}")
    print(f"   Prix peak MT5: {MT5_REFERENCE['prix_ttr_phase1']:.5f}")
    
    return {
        'impact_pips': impact_pips,
        'ttr_minutes': ttr_minutes,
        'prix_peak': prix_peak,
        'adjusted_score': adjusted_score,
        'amplification': amplification,
        'ts_peak': cpi_event['ts_utc'] + timedelta(minutes=ttr_minutes)
    }


# ═══════════════════════════════════════════════════════════════
# ÉTAPE 4 : CALCUL PULLBACK
# ═══════════════════════════════════════════════════════════════

def calculate_pullback_phase(phase1_result, event_phase2):
    """
    Calcule le pullback entre Phase 1 et Phase 2
    
    Args:
        phase1_result: Résultats Phase 1
        event_phase2: Événement Phase 2 (Compte Courant)
    
    Returns:
        dict: Résultats pullback
    """
    print(f"\n📉 PULLBACK (12:35 → 12:45 UTC)")
    
    # Calcul temps depuis peak Phase 1
    minutes_to_next = (event_phase2['ts_utc'] - phase1_result['ts_peak']).total_seconds() / 60
    
    print(f"   Temps depuis peak: {minutes_to_next:.1f} min")
    
    # Pullback
    pullback_pips = calculate_pullback_v2(
        phase1_impact=phase1_result['impact_pips'],
        minutes_since_peak=minutes_to_next,
        minutes_to_next_phase=minutes_to_next
    )
    
    print(f"   Pullback prédit: {pullback_pips:.1f} pips")
    print(f"   Pullback MT5: {MT5_REFERENCE['pullback_reel']:.1f} pips")
    print(f"   Écart: {abs(pullback_pips - MT5_REFERENCE['pullback_reel']):.1f} pips")
    
    # Prix après pullback
    prix_apres_pullback = phase1_result['prix_peak'] - (pullback_pips * 0.0001)
    print(f"   Prix après pullback: {prix_apres_pullback:.5f}")
    print(f"   Prix MT5: {MT5_REFERENCE['prix_apres_pullback']:.5f}")
    
    return {
        'pullback_pips': pullback_pips,
        'prix_apres_pullback': prix_apres_pullback,
        'minutes_to_next': minutes_to_next
    }


# ═══════════════════════════════════════════════════════════════
# ÉTAPE 5 : MÉTRIQUES DE VALIDATION
# ═══════════════════════════════════════════════════════════════

def calculate_validation_metrics(phase1, pullback):
    """
    Calcule les métriques de validation globales
    
    Args:
        phase1: Résultats Phase 1
        pullback: Résultats pullback
    
    Returns:
        dict: Métriques de validation
    """
    print(f"\n\n📊 MÉTRIQUES DE VALIDATION")
    print(f"="*60)
    
    # MAE Phase 1
    mae_impact_phase1 = abs(phase1['impact_pips'] - MT5_REFERENCE['phase1_impact'])
    precision_phase1 = (1 - mae_impact_phase1 / MT5_REFERENCE['phase1_impact']) * 100
    
    print(f"\n🚀 Phase 1 (Impact):")
    print(f"   Prédit: {phase1['impact_pips']:.1f} pips")
    print(f"   Réel: {MT5_REFERENCE['phase1_impact']:.1f} pips")
    print(f"   MAE: {mae_impact_phase1:.1f} pips")
    print(f"   Précision: {precision_phase1:.1f}%")
    
    # MAE Pullback
    mae_pullback = abs(pullback['pullback_pips'] - MT5_REFERENCE['pullback_reel'])
    precision_pullback = (1 - mae_pullback / MT5_REFERENCE['pullback_reel']) * 100
    
    print(f"\n📉 Pullback:")
    print(f"   Prédit: {pullback['pullback_pips']:.1f} pips")
    print(f"   Réel: {MT5_REFERENCE['pullback_reel']:.1f} pips")
    print(f"   MAE: {mae_pullback:.1f} pips")
    print(f"   Précision: {precision_pullback:.1f}%")
    
    # Global
    mae_global = (mae_impact_phase1 + mae_pullback) / 2
    precision_global = (precision_phase1 + precision_pullback) / 2
    
    print(f"\n🎯 GLOBAL:")
    print(f"   MAE moyenne: {mae_global:.1f} pips")
    print(f"   Précision moyenne: {precision_global:.1f}%")
    
    print(f"="*60)
    
    return {
        'mae_impact_phase1': mae_impact_phase1,
        'precision_phase1': precision_phase1,
        'mae_pullback': mae_pullback,
        'precision_pullback': precision_pullback,
        'mae_global': mae_global,
        'precision_global': precision_global
    }


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    """
    Fonction principale - Test cas d'école 11 septembre 2025
    """
    print("="*60)
    print("🎯 PLANIFICATEUR V3 - CAS D'ÉCOLE 11 SEPTEMBRE 2025")
    print("="*60)
    
    # 1. Récupérer événements
    print("\n📥 RÉCUPÉRATION ÉVÉNEMENTS...")
    events = get_events_11_sept()
    
    if not events:
        print("❌ Impossible de récupérer les événements")
        return
    
    print(f"✅ {len(events)} événements trouvés")
    
    # 2. Agréger CPI
    cpi_event = aggregate_cpi_events(events)
    
    if not cpi_event:
        print("❌ Impossible d'agréger les événements CPI")
        return
    
    # 3. Trouver événement Phase 2 (autres événements après CPI)
    # Chercher événements entre 14:30 et 15:30 (heure locale)
    events_phase2 = [e for e in events 
                     if e['ts_utc'].hour == 14 and e['ts_utc'].minute > 30]
    
    if not events_phase2:
        print("⚠️ Aucun événement trouvé après 14:30 (Phase 2)")
        event_phase2 = None
    else:
        # Prendre le premier événement après le CPI
        event_phase2 = min(events_phase2, key=lambda x: x['ts_utc'])
        print(f"\n📊 Événement Phase 2: {event_phase2['family']} ({event_phase2['ts_utc'].strftime('%H:%M')})")
    
    # 4. Calculer Phase 1
    phase1_result = calculate_phase_1(cpi_event, MT5_REFERENCE['prix_depart'])
    
    # 5. Calculer Pullback (si Phase 2 existe)
    if event_phase2:
        pullback_result = calculate_pullback_phase(phase1_result, event_phase2)
    else:
        print("\n⚠️ Phase 2 non trouvée, pullback non calculé")
        pullback_result = None
    
    # 6. Métriques de validation
    if pullback_result:
        metrics = calculate_validation_metrics(phase1_result, pullback_result)
    
    print(f"\n\n✅ TEST TERMINÉ")
    print(f"="*60)


if __name__ == "__main__":
    main()
