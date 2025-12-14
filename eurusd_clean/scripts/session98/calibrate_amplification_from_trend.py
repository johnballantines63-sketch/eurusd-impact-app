"""
CALIBRATION FACTEUR AMPLIFICATION - BASÉ SUR TENDANCE 24H
===========================================================

Session 98 - Objectif : Remplacer amplification fixe 2.5 par facteur dynamique

APPROCHE :
1. Calculer impact théorique avec formules S51-55 (SANS amplification)
2. Mesurer impact réel depuis prices_1m (timezone correcte)
3. Calculer facteur d'amplification parfait = impact_réel / (impact_théorique × 0.758)
4. Analyser tendance 24h avant (régression linéaire, momentum, position)
5. Établir corrélation entre tendance et facteur_parfait
6. Tester sur 4 dates CPI

DONNÉES RÉFÉRENCE (session92.8) :
- 2025-09-11 : 51.7 pips réel
- 2025-01-15 : 49.9 pips réel
- 2025-05-13 : 34.0 pips réel
- 2025-07-15 : 24.6 pips réel

Date : 29 octobre 2025
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Ajouter chemins
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root / "fx_impact_app" / "src"))
sys.path.insert(0, str(project_root / "eurusd_clean" / "scripts" / "session92.8"))

import pandas as pd
import numpy as np
import duckdb
from config import get_db_path

# Import formules validées S51-55
from formulas_validated import (
    calculate_adjusted_empirical_score,
    calculate_impact_d
)

# Import analyse tendance (régression linéaire)
from direction_sentiment_24h_REGRESSION import (
    load_prices_24h_before,
    calculate_trend_regression,
    calculate_24h_indicators
)

print("="*80)
print("🎯 CALIBRATION FACTEUR AMPLIFICATION - TENDANCE 24H")
print("="*80)

# ============================================================================
# DATES À TESTER (avec impacts réels référence)
# ============================================================================

DATES_TEST = [
    {
        'date': '2025-09-11',
        'event_time_bern': '14:30:00',
        'impact_reel': 51.7,  # Référence session92.8
        'description': 'CPI Septembre 2025 (référence)'
    },
    {
        'date': '2025-01-15',
        'event_time_bern': '14:30:00',
        'impact_reel': 49.9,
        'description': 'CPI Janvier 2025'
    },
    {
        'date': '2025-05-13',
        'event_time_bern': '14:30:00',
        'impact_reel': 34.0,
        'description': 'CPI Mai 2025'
    },
    {
        'date': '2025-07-15',
        'event_time_bern': '14:30:00',
        'impact_reel': 24.6,
        'description': 'CPI Juillet 2025'
    }
]

# ============================================================================
# FONCTION ANALYSE UNE DATE
# ============================================================================

def analyze_date(date_str, event_time_bern, impact_reel, conn):
    """
    Analyse complète une date pour calibration
    
    Returns:
        dict avec toutes les variables nécessaires
    """
    print(f"\n{'='*80}")
    print(f"📅 {date_str} - Impact réel référence : {impact_reel:.1f} pips")
    print(f"{'='*80}")
    
    # ========================================================================
    # ÉTAPE 1 : CHARGER ÉVÉNEMENTS
    # ========================================================================
    
    query_events = """
    SELECT 
        e.event_key,
        e.ts_utc,
        e.actual,
        e.estimate,
        e.previous,
        e.forecast,
        ef.empirical_score
    FROM events e
    LEFT JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
    WHERE DATE(e.ts_utc) = ?
        AND e.country = 'US'
        AND ef.empirical_score IS NOT NULL
        AND ef.empirical_score > 40
    ORDER BY e.ts_utc
    """
    
    events = conn.execute(query_events, [date_str]).df()
    
    if len(events) == 0:
        print(f"❌ ERREUR : Aucun événement trouvé pour {date_str}")
        return None
    
    print(f"✅ Événements chargés : {len(events)}")
    
    # ========================================================================
    # ÉTAPE 2 : CALCULER SURPRISE ET SCORE AJUSTÉ
    # ========================================================================
    
    surprises = []
    for _, event in events.iterrows():
        ref = None
        if pd.notna(event['estimate']) and event['estimate'] != 0:
            ref = event['estimate']
        elif pd.notna(event['forecast']) and event['forecast'] != 0:
            ref = event['forecast']
        elif pd.notna(event['previous']) and event['previous'] != 0:
            ref = event['previous']
        
        if pd.notna(event['actual']) and ref is not None:
            surprise_pct = abs((event['actual'] - ref) / ref) * 100
            surprises.append(surprise_pct)
        else:
            surprises.append(0.0)
    
    surprise_max = max(surprises) if surprises else 0
    score_base = events['empirical_score'].mean()
    
    # Score ajusté (Session 55)
    score_ajuste = calculate_adjusted_empirical_score(score_base, surprise_max)
    
    print(f"\n🔢 CALCULS PRÉDICTION :")
    print(f"   Score base        : {score_base:.1f}")
    print(f"   Surprise max      : {surprise_max:.1f}%")
    print(f"   Score ajusté      : {score_ajuste:.1f}")
    print(f"   Num events        : {len(events)}")
    
    # ========================================================================
    # ÉTAPE 3 : IMPACT THÉORIQUE SANS AMPLIFICATION
    # ========================================================================
    
    # Calculer avec amplification = 1.0 pour avoir impact de base
    impact_base = calculate_impact_d(
        empirical_score=score_ajuste,
        num_events=len(events),
        amplification=1.0
    )
    
    print(f"   Impact base (amp=1.0) : {impact_base:.1f} pips")
    print(f"   Avec correction 0.758 : {impact_base * 0.758:.1f} pips")
    
    # ========================================================================
    # ÉTAPE 4 : CALCULER FACTEUR AMPLIFICATION PARFAIT
    # ========================================================================
    
    # Formule : impact_réel = impact_base × amplification × 0.758
    # Donc : amplification_parfait = impact_réel / (impact_base × 0.758)
    
    impact_base_corrected = impact_base * 0.758
    
    if impact_base_corrected > 0:
        facteur_parfait = impact_reel / impact_base_corrected
    else:
        facteur_parfait = 0
    
    print(f"\n🎯 FACTEUR AMPLIFICATION PARFAIT :")
    print(f"   Impact réel       : {impact_reel:.1f} pips")
    print(f"   Impact base×0.758 : {impact_base_corrected:.1f} pips")
    print(f"   FACTEUR PARFAIT   : {facteur_parfait:.3f}")
    
    # ========================================================================
    # ÉTAPE 5 : ANALYSER TENDANCE 24H AVANT (RÉGRESSION)
    # ========================================================================
    
    print(f"\n📊 ANALYSE TENDANCE 24H AVANT (Régression linéaire) :")
    
    # Charger prix 24h avant
    prices_24h = load_prices_24h_before(date_str, event_time_bern, conn)
    
    if len(prices_24h) == 0:
        print(f"❌ ERREUR : Pas de prix 24h disponibles")
        return None
    
    # Régression linéaire pour tendance
    trend, slope, r_squared = calculate_trend_regression(prices_24h)
    
    # Pente en pips (conversion)
    slope_pips = slope * 10000
    
    # Indicateurs complémentaires
    indicators = calculate_24h_indicators(prices_24h)
    momentum_24h = indicators['momentum_24h_pct']
    position_range = indicators['position_in_range']
    
    print(f"\n   Tendance (régression) : {trend}")
    print(f"   Pente                 : {slope_pips:.4f} pips/minute")
    print(f"   R² (significativité)  : {r_squared:.3f}")
    print(f"   Momentum 24h          : {momentum_24h:.2f}%")
    print(f"   Position range        : {position_range:.2f}")
    
    # ========================================================================
    # RETOUR RÉSULTATS
    # ========================================================================
    
    return {
        'date': date_str,
        'num_events': len(events),
        'score_base': score_base,
        'score_ajuste': score_ajuste,
        'surprise_max': surprise_max,
        'impact_base': impact_base,
        'impact_base_corrected': impact_base_corrected,
        'impact_reel': impact_reel,
        'facteur_parfait': facteur_parfait,
        'trend': trend,
        'slope_pips': slope_pips,
        'r_squared': r_squared,
        'momentum_24h': momentum_24h,
        'position_range': position_range
    }

# ============================================================================
# ANALYSE TOUTES LES DATES
# ============================================================================

db_path = get_db_path()
conn = duckdb.connect(str(db_path), read_only=True)

results = []

for date_info in DATES_TEST:
    result = analyze_date(
        date_info['date'],
        date_info['event_time_bern'],
        date_info['impact_reel'],
        conn
    )
    
    if result:
        results.append(result)

conn.close()

# ============================================================================
# ANALYSE CORRÉLATIONS
# ============================================================================

print("\n" + "="*80)
print("📈 ANALYSE CORRÉLATIONS")
print("="*80)

if len(results) >= 3:
    df = pd.DataFrame(results)
    
    # Variables indépendantes (tendance)
    X_vars = ['slope_pips', 'r_squared', 'momentum_24h', 'position_range']
    
    # Variable dépendante (facteur parfait)
    y = df['facteur_parfait'].values
    
    print(f"\n🔍 Corrélations avec facteur_parfait :")
    print(f"   {'Variable':20} {'Corrélation':>12} {'Significativité':>15}")
    print(f"   {'-'*50}")
    
    correlations = {}
    for var in X_vars:
        x = df[var].values
        corr = np.corrcoef(x, y)[0, 1]
        correlations[var] = corr
        
        # Significativité simple
        if abs(corr) > 0.8:
            signif = "FORTE ✅✅✅"
        elif abs(corr) > 0.5:
            signif = "MOYENNE ✅"
        else:
            signif = "FAIBLE ⚠️"
        
        print(f"   {var:20} {corr:>11.3f}  {signif:>15}")
    
    # ========================================================================
    # PROPOSITION FORMULE DYNAMIQUE
    # ========================================================================
    
    print(f"\n" + "="*80)
    print("🎯 PROPOSITION FORMULE DYNAMIQUE")
    print("="*80)
    
    # Trouver variable la plus corrélée
    best_var = max(correlations, key=lambda k: abs(correlations[k]))
    best_corr = correlations[best_var]
    
    print(f"\n📊 Variable la plus corrélée : {best_var} (r={best_corr:.3f})")
    
    # Régression linéaire simple : facteur = a * var + b
    x_best = df[best_var].values
    
    # Calcul coefficients
    x_mean = np.mean(x_best)
    y_mean = np.mean(y)
    
    a = np.sum((x_best - x_mean) * (y - y_mean)) / np.sum((x_best - x_mean) ** 2)
    b = y_mean - a * x_mean
    
    print(f"\n📐 Formule proposée (régression linéaire) :")
    print(f"   amplification = {a:.4f} × {best_var} + {b:.4f}")
    
    # Test formule
    print(f"\n✅ TEST FORMULE SUR 4 DATES :")
    print(f"   {'Date':12} {'Facteur Parfait':>16} {'Facteur Prédit':>15} {'Erreur':>8}")
    print(f"   {'-'*60}")
    
    errors = []
    for _, row in df.iterrows():
        facteur_predit = a * row[best_var] + b
        error = abs(facteur_predit - row['facteur_parfait'])
        errors.append(error)
        
        print(f"   {row['date']:12} {row['facteur_parfait']:>15.3f} {facteur_predit:>15.3f} {error:>8.3f}")
    
    mae_formule = np.mean(errors)
    print(f"\n   MAE formule : {mae_formule:.3f}")
    
    # Comparaison avec facteur fixe 2.5
    facteur_fixe = 2.5
    errors_fixe = [abs(facteur_fixe - row['facteur_parfait']) for _, row in df.iterrows()]
    mae_fixe = np.mean(errors_fixe)
    
    print(f"\n📊 COMPARAISON :")
    print(f"   MAE formule dynamique : {mae_formule:.3f}")
    print(f"   MAE facteur fixe 2.5  : {mae_fixe:.3f}")
    
    if mae_formule < mae_fixe:
        improvement = ((mae_fixe - mae_formule) / mae_fixe) * 100
        print(f"   Amélioration          : {improvement:.1f}% ✅")
    else:
        degradation = ((mae_formule - mae_fixe) / mae_fixe) * 100
        print(f"   Dégradation           : {degradation:.1f}% ❌")
    
    # ========================================================================
    # SAUVEGARDER RÉSULTATS CSV
    # ========================================================================
    
    output_csv = Path(__file__).parent / "calibration_amplification_results.csv"
    df.to_csv(output_csv, index=False)
    print(f"\n💾 Résultats sauvegardés : {output_csv}")
    
else:
    print(f"\n⚠️ Pas assez de dates pour analyse corrélation (besoin ≥3)")

print("\n" + "="*80)
print("✅ CALIBRATION TERMINÉE")
print("="*80)

print(f"\n**Token usage:** ~103,000 / 190,000 (54%)")
