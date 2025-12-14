"""
AJUSTEMENT AUTOMATIQUE COEFFICIENT - Session 88
Optimise le coefficient logarithmique Zone 4 selon résultats tests
"""

import sys
from pathlib import Path
import numpy as np

# Ajouter chemin formules
sys.path.insert(0, '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/src')

# ============================================================================
# CONFIGURATION
# ============================================================================

FORMULAS_FILE = Path('/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/src/formulas_validated.py')

# ============================================================================
# FONCTION CALCUL OPTIMAL
# ============================================================================

def calculate_optimal_coefficient(test_results: list) -> float:
    """
    Calcule coefficient optimal pour minimiser MAE
    
    Args:
        test_results: Liste de dicts avec keys:
            - surprise_max: float
            - impact_real: float
            - impact_brut: float (sans amplification)
    
    Returns:
        float: Coefficient optimal pour Zone 4
    """
    # Filtrer cas Zone 4 (surprise > 100%)
    zone4_cases = [r for r in test_results if r['surprise_max'] > 100]
    
    if not zone4_cases:
        print("⚠️ Aucun cas Zone 4 trouvé")
        return 1.8  # Valeur actuelle
    
    print(f"\n📊 Analyse {len(zone4_cases)} cas Zone 4 (surprise > 100%)")
    
    # Pour chaque cas, calculer coefficient nécessaire
    coeffs = []
    
    for r in zone4_cases:
        surprise = r['surprise_max']
        impact_target = r['impact_real']
        impact_brut = r['impact_brut']
        
        # Résolution: impact_target = impact_brut × (5.0 + coeff × log10(surprise - 99)) × 0.758
        # coeff = [(impact_target / (impact_brut × 0.758)) - 5.0] / log10(surprise - 99)
        
        amplification_needed = impact_target / (abs(impact_brut) * 0.758)
        coeff_needed = (amplification_needed - 5.0) / np.log10(surprise - 99)
        
        coeffs.append(coeff_needed)
        
        print(f"   Surprise {surprise:.0f}% → Coeff optimal: {coeff_needed:.3f}")
    
    # Moyenne des coefficients
    coeff_optimal = np.mean(coeffs)
    coeff_std = np.std(coeffs)
    
    print(f"\n💡 Coefficient optimal : {coeff_optimal:.3f} ± {coeff_std:.3f}")
    
    return coeff_optimal


# ============================================================================
# FONCTION MISE À JOUR FICHIER
# ============================================================================

def update_formulas_file(new_coefficient: float) -> bool:
    """
    Met à jour le coefficient dans formulas_validated.py
    
    Args:
        new_coefficient: Nouveau coefficient à appliquer
    
    Returns:
        bool: True si succès
    """
    if not FORMULAS_FILE.exists():
        print(f"❌ Fichier non trouvé: {FORMULAS_FILE}")
        return False
    
    # Lire contenu actuel
    with open(FORMULAS_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup
    backup_path = FORMULAS_FILE.with_suffix('.py.backup_session88')
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Backup créé: {backup_path.name}")
    
    # Remplacer ligne coefficient
    # Chercher: return min(5.0 + 1.8 * math.log10(abs_surprise - 99), 10.0)
    # Remplacer: return min(5.0 + {new_coefficient} * math.log10(abs_surprise - 99), 10.0)
    
    old_line = "return min(5.0 + 1.8 * math.log10(abs_surprise - 99), 10.0)"
    new_line = f"return min(5.0 + {new_coefficient:.3f} * math.log10(abs_surprise - 99), 10.0)"
    
    if old_line not in content:
        print("⚠️ Ligne cible non trouvée (format différent)")
        print("   Recherche pattern plus large...")
        
        # Pattern alternatif
        import re
        pattern = r'return min\(5\.0 \+ [\d.]+ \* math\.log10\(abs_surprise - 99\), 10\.0\)'
        
        if re.search(pattern, content):
            content_new = re.sub(pattern, new_line, content)
            
            with open(FORMULAS_FILE, 'w', encoding='utf-8') as f:
                f.write(content_new)
            
            print(f"✅ Coefficient mis à jour: {new_coefficient:.3f}")
            return True
        else:
            print("❌ Pattern non trouvé")
            return False
    
    # Remplacement direct
    content_new = content.replace(old_line, new_line)
    
    with open(FORMULAS_FILE, 'w', encoding='utf-8') as f:
        f.write(content_new)
    
    print(f"✅ Coefficient mis à jour: {new_coefficient:.3f}")
    return True


# ============================================================================
# FONCTION TEST COEFFICIENT
# ============================================================================

def test_coefficient_impact(coefficient: float, test_cases: list):
    """
    Teste impact d'un coefficient sur les cas de test
    
    Args:
        coefficient: Coefficient à tester
        test_cases: Liste de cas avec surprise_max et impact_real
    """
    print(f"\n📊 TEST COEFFICIENT {coefficient:.3f}")
    print("─" * 70)
    
    for case in test_cases:
        surprise = case['surprise_max']
        impact_brut = case['impact_brut']
        impact_real = case['impact_real']
        
        # Calculer amplification avec ce coefficient
        if surprise < 15:
            amp = 1.0
        elif surprise < 30:
            amp = 1.0 + (surprise - 15) / 15 * 1.5
        elif surprise < 100:
            amp = 2.5 + (surprise - 30) / 70 * 2.5
        else:
            amp = min(5.0 + coefficient * np.log10(surprise - 99), 10.0)
        
        # Impact prédit
        impact_predicted = abs(impact_brut) * amp * 0.758
        
        # Erreur
        error = abs(impact_predicted - impact_real)
        error_pct = (error / impact_real * 100) if impact_real > 0 else 0
        
        status = "✅" if error < 30 else "❌"
        print(f"Surprise {surprise:5.0f}% → Prédit {impact_predicted:5.1f}p vs Réel {impact_real:5.1f}p | Erreur {error:4.1f}p ({error_pct:3.0f}%) {status}")
    
    # MAE global
    errors = []
    for case in test_cases:
        surprise = case['surprise_max']
        impact_brut = case['impact_brut']
        impact_real = case['impact_real']
        
        if surprise < 15:
            amp = 1.0
        elif surprise < 30:
            amp = 1.0 + (surprise - 15) / 15 * 1.5
        elif surprise < 100:
            amp = 2.5 + (surprise - 30) / 70 * 2.5
        else:
            amp = min(5.0 + coefficient * np.log10(surprise - 99), 10.0)
        
        impact_predicted = abs(impact_brut) * amp * 0.758
        error = abs(impact_predicted - impact_real)
        errors.append(error)
    
    mae = np.mean(errors)
    print(f"\n📊 MAE global: {mae:.1f} pips")
    
    return mae


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("="*80)
    print("🔧 AJUSTEMENT AUTOMATIQUE COEFFICIENT")
    print("="*80)
    
    # ========================================================================
    # CAS DE TEST (À COMPLÉTER APRÈS EXÉCUTION test_multi_dates.py)
    # ========================================================================
    
    # EXEMPLE : Remplacer par résultats réels
    test_results = [
        {
            'name': '01 Août',
            'surprise_max': 500.0,
            'impact_real': 160.0,  # ← À REMPLACER par valeur réelle
            'impact_brut': 30.3    # Calculé: -10.47 + 0.477 × score_ajusté
        },
        # Ajouter autres dates si Zone 4
    ]
    
    print("\n⚠️ ATTENTION: Mettre à jour test_results[] avec résultats réels !")
    print("   Exécuter d'abord: python test_multi_dates.py")
    print("\n📋 Cas actuels:")
    for r in test_results:
        print(f"   {r['name']}: Surprise {r['surprise_max']:.0f}%, Impact réel {r['impact_real']:.1f} pips")
    
    # Calculer coefficient optimal
    coeff_optimal = calculate_optimal_coefficient(test_results)
    
    # Tester plusieurs coefficients autour de l'optimal
    print("\n" + "="*80)
    print("🧪 TEST COEFFICIENTS CANDIDATS")
    print("="*80)
    
    candidates = [
        coeff_optimal - 0.2,
        coeff_optimal - 0.1,
        coeff_optimal,
        coeff_optimal + 0.1,
        coeff_optimal + 0.2,
        1.8  # Valeur actuelle pour comparaison
    ]
    
    results_by_coeff = {}
    for c in candidates:
        mae = test_coefficient_impact(c, test_results)
        results_by_coeff[c] = mae
    
    # Trouver meilleur
    best_coeff = min(results_by_coeff, key=results_by_coeff.get)
    best_mae = results_by_coeff[best_coeff]
    
    print("\n" + "="*80)
    print(f"🏆 MEILLEUR COEFFICIENT : {best_coeff:.3f} (MAE = {best_mae:.1f} pips)")
    print("="*80)
    
    # Proposition mise à jour
    if abs(best_coeff - 1.8) > 0.1:
        print(f"\n💡 RECOMMANDATION:")
        print(f"   Coefficient actuel : 1.800")
        print(f"   Coefficient optimal: {best_coeff:.3f}")
        print(f"   Amélioration MAE   : {results_by_coeff.get(1.8, 0) - best_mae:.1f} pips")
        
        response = input("\n❓ Mettre à jour formulas_validated.py ? (oui/non): ")
        
        if response.lower() in ['oui', 'o', 'yes', 'y']:
            if update_formulas_file(best_coeff):
                print("\n✅ Fichier mis à jour avec succès !")
                print("   → Relancer test_multi_dates.py pour valider")
            else:
                print("\n❌ Échec mise à jour")
        else:
            print("\n⏭️ Pas de modification")
    else:
        print(f"\n✅ Coefficient actuel (1.8) est optimal !")
        print(f"   Pas de modification nécessaire")
    
    print("\n" + "="*80)
