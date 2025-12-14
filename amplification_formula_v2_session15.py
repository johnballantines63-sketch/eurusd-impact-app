"""
FORMULE AMPLIFICATION V2 - Basée sur analyse Session 15

Changements vs v8.7.1 (Session 14) :
- Plafonnement surprises aberrantes (>30%)
- Amplification modérée uniquement (max ×2.5)
- Filtrage événements à faible score empirique

Rationale :
- Succès viennent de surprises MODÉRÉES (~7%), pas extrêmes
- Surprises >20% génèrent souvent impacts FAIBLES (aberrations)
- Zone optimale : 5-15% surprise, amplification ×1.5-2.5
"""

import numpy as np

def calculate_amplification_factor_v2(surprise_pct, empirical_score=None, country=None):
    """
    Calcule facteur d'amplification intelligent basé sur analyse Session 15
    
    Args:
        surprise_pct: Pourcentage de surprise de l'événement
        empirical_score: Score empirique (optionnel, pour filtrage)
        country: Pays de l'événement (optionnel, pour filtrage)
    
    Returns:
        float: Facteur d'amplification (1.0 à 2.5)
    
    Changements vs v1 :
    - Plafond surprise à 30% (aberrations exclues)
    - Amplification max réduite de ×10 à ×2.5
    - Zone linéaire réduite à 5-15%
    """
    
    surprise_abs = abs(surprise_pct)
    
    # FILTRAGE 1 : Surprises aberrantes (>30%) = plafonnées
    if surprise_abs > 30:
        surprise_abs = 30.0
    
    # FILTRAGE 2 : Score empirique trop faible = pas d'amplification
    if empirical_score is not None and empirical_score < 40:
        # Événements peu importants, même avec surprise
        return 1.0
    
    # ZONE 1 (0-5%) : Pas d'amplification
    if surprise_abs < 5.0:
        return 1.0
    
    # ZONE 2 (5-15%) : Amplification linéaire progressive
    # De ×1.0 (5%) à ×2.5 (15%)
    elif surprise_abs < 15.0:
        # Pente : (2.5 - 1.0) / (15 - 5) = 0.15
        return 1.0 + (surprise_abs - 5.0) * 0.15
    
    # ZONE 3 (>15%) : PLAFOND STRICT à ×2.5
    else:
        return 2.5

# ════════════════════════════════════════════════════════════════
# TESTS UNITAIRES
# ════════════════════════════════════════════════════════════════

def test_amplification_v2():
    """Tests de la nouvelle formule"""
    
    print("="*80)
    print("🧪 TESTS FORMULE AMPLIFICATION V2")
    print("="*80)
    
    # Test 1 : Pas de surprise
    factor = calculate_amplification_factor_v2(0)
    print(f"\n✅ Test 1 : Surprise 0% → Facteur ×{factor:.2f} (attendu: ×1.00)")
    assert factor == 1.0
    
    # Test 2 : Surprise modérée (zone optimale)
    factor = calculate_amplification_factor_v2(7.2)
    print(f"✅ Test 2 : Surprise 7.2% → Facteur ×{factor:.2f} (attendu: ~×1.33)")
    assert 1.30 <= factor <= 1.40
    
    # Test 3 : Surprise élevée mais raisonnable
    factor = calculate_amplification_factor_v2(15)
    print(f"✅ Test 3 : Surprise 15% → Facteur ×{factor:.2f} (attendu: ×2.50)")
    assert factor == 2.5
    
    # Test 4 : Surprise aberrante (plafonnée)
    factor = calculate_amplification_factor_v2(50)
    print(f"✅ Test 4 : Surprise 50% → Facteur ×{factor:.2f} (attendu: ×2.50 plafonné)")
    assert factor == 2.5
    
    # Test 5 : Surprise avec score faible (filtré)
    factor = calculate_amplification_factor_v2(20, empirical_score=30)
    print(f"✅ Test 5 : Surprise 20% + Score 30 → Facteur ×{factor:.2f} (attendu: ×1.00 filtré)")
    assert factor == 1.0
    
    # Test 6 : Surprise avec score élevé (amplifié)
    factor = calculate_amplification_factor_v2(10, empirical_score=70)
    print(f"✅ Test 6 : Surprise 10% + Score 70 → Facteur ×{factor:.2f} (attendu: ~×1.75)")
    assert 1.70 <= factor <= 1.80
    
    print("\n" + "="*80)
    print("✅ TOUS LES TESTS PASSENT !")
    print("="*80)

# ════════════════════════════════════════════════════════════════
# COMPARAISON V1 VS V2
# ════════════════════════════════════════════════════════════════

def compare_v1_v2():
    """Compare les deux versions de la formule"""
    
    print("\n" + "="*80)
    print("📊 COMPARAISON FORMULE V1 (Session 14) vs V2 (Session 15)")
    print("="*80)
    
    def calculate_amplification_factor_v1(surprise_pct):
        """Ancienne formule (Session 14)"""
        surprise_abs = abs(surprise_pct)
        if surprise_abs < 5.0:
            return 1.0
        elif surprise_abs < 10.0:
            return 1.0 + (surprise_abs - 5.0) * 0.4
        else:
            return 3.0 + np.log1p(surprise_abs - 10.0) * 2.0
    
    test_cases = [
        (0, "Pas de surprise"),
        (7.2, "Zone optimale (succès)"),
        (10, "Seuil zone 2"),
        (15, "Surprise modérée-élevée"),
        (20, "Surprise élevée"),
        (30, "Surprise très élevée"),
        (50, "Surprise aberrante (échecs)")
    ]
    
    print(f"\n{'Surprise':<10} {'Description':<30} {'V1 (vieux)':<15} {'V2 (nouveau)':<15} {'Changement':<15}")
    print("─" * 85)
    
    for surprise, desc in test_cases:
        v1 = calculate_amplification_factor_v1(surprise)
        v2 = calculate_amplification_factor_v2(surprise)
        diff = v2 - v1
        emoji = "🎯" if abs(diff) < 0.5 else ("📉" if diff < 0 else "📈")
        print(f"{surprise:<10} {desc:<30} ×{v1:<14.2f} ×{v2:<14.2f} {emoji} {diff:+.2f}")
    
    print("\n💡 IMPACT DES CHANGEMENTS :")
    print("   🎯 Surprises modérées (7-10%) : Légèrement réduites (plus conservateur)")
    print("   📉 Surprises élevées (15-50%) : FORTEMENT réduites (×10 → ×2.5)")
    print("   ✅ Résultat attendu : Moins d'over-amplification, meilleure précision")

# ════════════════════════════════════════════════════════════════
# EXÉCUTION
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    test_amplification_v2()
    compare_v1_v2()
    
    print("\n" + "="*80)
    print("📁 FORMULE V2 PRÊTE POUR INTÉGRATION")
    print("="*80)
    print("\nProchaine étape : Intégrer dans sequence_multi_event_timeline_v87.py")
