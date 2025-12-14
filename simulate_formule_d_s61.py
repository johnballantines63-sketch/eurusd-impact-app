"""
SIMULATION FORMULE D - Comprendre la logique exacte
Session 61 - Résolution Problème #7
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "fx_impact_app"))
sys.path.insert(0, str(project_root / "fx_impact_app" / "src"))

import duckdb
from fx_impact_app.src.config import get_db_path

# Dictionnaire sentiment
FAMILY_SENTIMENT = {
    'GDP': 1, 'GDP_Growth_Rate': 1, 'GDP_Sales': 1,
    'PMI': 1, 'PMI_Composite': 1, 'PMI_Manufacturing': 1, 'PMI_Services': 1,
    'CPI': 1, 'CPI_Core': 1, 'PPI': 1,
    'Unemployment_Rate': -1, 'Jobless_Claims': -1,
    'NFP': 1, 'Payrolls': 1,
    'Retail_Sales': 1, 'Consumer_Confidence': 1,
    'Industrial_Production': 1, 'Inflation_Rate': 1,
    'Interest_Rate': 1, 'Trade_Balance': 1, 'Current_Account': 1,
}

def get_event_direction(family: str, surprise: float) -> int:
    """Détermine direction selon surprise et sentiment"""
    if abs(surprise) < 0.01:
        return 1
    sentiment = FAMILY_SENTIMENT.get(family, 1)
    if surprise > 0:
        return sentiment
    else:
        return -sentiment

def simulate_formule_d():
    """Simule Formule D avec scores validation_events"""
    
    print("\n" + "="*80)
    print("🧪 SIMULATION FORMULE D - COMPRENDRE LA LOGIQUE")
    print("="*80 + "\n")
    
    # Charger événements
    db_path = get_db_path()
    conn = duckdb.connect(str(db_path))
    
    query = """
    SELECT 
        family,
        surprise,
        surprise_pct,
        empirical_score
    FROM validation_events
    WHERE event_date = '2025-09-11'
    ORDER BY family
    """
    
    events = conn.execute(query).fetchall()
    conn.close()
    
    print(f"📊 {len(events)} événements chargés\n")
    
    # Calculer contributions individuelles
    contributions = []
    surprises_pct = []
    
    print(f"{'Family':<25} {'Score':>8} {'Surp%':>8} {'Impact':>10} {'Dir':>5} {'Contrib':>10}")
    print("-"*80)
    
    for family, surprise, surprise_pct, score in events:
        surprises_pct.append(abs(surprise_pct))
        
        # Formule C (multi-events)
        impact_abs = -10.47 + 0.477 * score
        
        # Direction
        direction = get_event_direction(family, surprise)
        
        # Contribution vectorielle
        contribution = impact_abs * direction
        contributions.append(contribution)
        
        print(f"{family:<25} {score:>8.1f} {surprise_pct:>7.1f}% {impact_abs:>10.1f} "
              f"{'+1' if direction > 0 else '-1':>5} {contribution:>+10.1f}")
    
    print("-"*80)
    
    # Somme vectorielle
    impact_brut = sum(contributions)
    print(f"{'IMPACT BRUT':<25} {'':<8} {'':<8} {'':<10} {'':<5} {impact_brut:>+10.1f}\n")
    
    # Amplification
    max_surprise_pct = max(surprises_pct)
    if max_surprise_pct <= 5:
        amplification_factor = 1.0
    elif max_surprise_pct <= 15:
        amplification_factor = 1.0 + (max_surprise_pct - 5) / 10 * 1.5
    else:
        amplification_factor = 2.5
    
    impact_amplifie = abs(impact_brut) * amplification_factor
    
    # Correction
    impact_final_abs = impact_amplifie * 0.758
    direction_finale = 1 if impact_brut >= 0 else -1
    impact_final = impact_final_abs * direction_finale
    
    print("📊 CALCUL FINAL:")
    print("-"*80)
    print(f"Impact brut              : {impact_brut:>+10.1f} pips")
    print(f"Surprise max             : {max_surprise_pct:>10.1f}%")
    print(f"Amplification            : {amplification_factor:>10.2f}x")
    print(f"Impact amplifié (abs)    : {impact_amplifie:>10.1f} pips")
    print(f"Facteur correction       : {0.758:>10.3f}")
    print(f"Impact final (abs)       : {impact_final_abs:>10.1f} pips")
    print(f"Direction                : {'UP (+1)' if direction_finale > 0 else 'DOWN (-1)':>10}")
    print(f"IMPACT FINAL             : {impact_final:>+10.1f} pips")
    print("="*80)
    
    print(f"\n🎯 Impact réel MT5       : +56.2 pips")
    print(f"📊 Impact prédit         : {impact_final:+.1f} pips")
    print(f"📊 Écart                 : {abs(impact_final - 56.2):.1f} pips")
    
    if abs(impact_final - 56.2) < 5:
        print(f"✅ EXCELLENT ! (MAE < 5 pips)\n")
    elif abs(impact_final - 56.2) < 10:
        print(f"⚠️  ACCEPTABLE (MAE < 10 pips)\n")
    else:
        print(f"❌ PROBLÈME ! (MAE > 10 pips)\n")
    
    return {
        'impact_brut': impact_brut,
        'amplification': amplification_factor,
        'impact_final': impact_final,
        'contributions': contributions,
        'scores': [score for _, _, _, score in events]
    }

if __name__ == "__main__":
    result = simulate_formule_d()
    
    # Diagnostiquer les scores
    avg_score = sum(result['scores']) / len(result['scores'])
    print("\n" + "="*80)
    print("🔍 DIAGNOSTIC SCORES:")
    print("="*80)
    print(f"Score moyen : {avg_score:.1f}")
    print(f"Min score   : {min(result['scores']):.1f}")
    print(f"Max score   : {max(result['scores']):.1f}")
    
    if avg_score > 60:
        print(f"\n⚠️  SCORES SEMBLENT AJUSTÉS ({avg_score:.1f} >> 44.8)")
        print("    validation_events contient scores pré-ajustés")
    else:
        print(f"\n✅ SCORES SEMBLENT BRUTS ({avg_score:.1f} ≈ 44.8)")
        print("    validation_events contient scores bruts")
    
    print("="*80 + "\n")
