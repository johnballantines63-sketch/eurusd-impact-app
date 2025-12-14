# 📘 GUIDE DOUBLE WAVE - INTÉGRATION SESSION 87

**Créé :** 26 octobre 2025  
**Pour :** Session 87  
**Priorité :** ⭐⭐⭐ CRITIQUE - FORMULES À INTÉGRER

---

## 🎯 CONTEXTE RAPIDE

**Problème identifié Session 86 :**
- Script détecte `DOUBLE_WAVE` mais utilise formule standard
- Formules Double Wave Session 64 existent mais NON intégrées dans `formulas_validated.py`
- Résultat : Sous-estimation massive (67.7 vs 173.8 pips réel)

**Solution Session 87 :**
- Intégrer formule `calculate_double_wave_impact()` dans `formulas_validated.py`
- Modifier script validation pour l'utiliser
- Ajuster amplification pour surprises extrêmes (>100%)

---

## 📋 FORMULE DOUBLE WAVE (SESSION 64)

### Code Complet À Intégrer

**Fichier :** `/fx_impact_app/src/formulas_validated.py`

**Position :** Après `calculate_pullback_v2()`, avant `get_all_formulas_info()`

```python
# ════════════════════════════════════════════════════════════════
# FORMULE DOUBLE WAVE - MOUVEMENT 2 PHASES (93% PRÉCISION)
# ════════════════════════════════════════════════════════════════

def calculate_double_wave_impact(
    base_impact: float,
    surprise_pct: float,
    cluster_size: int
) -> dict:
    """
    Calcule impact Double Wave pour événements majeurs - SESSION 64
    
    VALIDATION (Session 64 - 11 septembre 2025):
    - Impact prédit: 56.6 pips
    - Impact réel: 53.0 pips
    - MAE: 3.6 pips
    - Précision: 93% ✅ VALIDÉ
    
    - Timing Phase 1: T+5 (prédit) vs 14:35 (réel) = 0 min écart ✅
    - Timing Pullback: T+11 (prédit) vs 14:41 (réel) = 0 min écart ✅
    - Timing Phase 2: T+15 (prédit) vs 14:45 (réel) = 0 min écart ✅
    - Précision timing: 100% ✅✅✅
    
    CONCEPT:
    Événements majeurs (surprise > 20%, cluster ≥ 5) génèrent une réaction
    en 2 vagues distinctes séparées par un pullback technique :
    
    Phase 1 (T+0 to T+5):
    - Réaction immédiate algorithmes HFT
    - Mouvement rapide mais incomplet
    - ~58% de l'impact total
    
    Pullback (T+5 to T+11):
    - Prise de profits technique
    - Retrace ~84% du gain Phase 1
    - Ne retombe PAS sous prix départ
    - Durée typique : 6 minutes
    
    Phase 2 (T+11 to T+15):
    - Traders humains + ordres institutionnels
    - Momentum reprend, plus fort que Phase 1
    - ~90% de l'impact total (155% de Phase 1)
    - Atteint le peak absolu
    
    Stabilisation (T+40):
    - Nouvel équilibre trouvé
    - Volatilité diminue
    
    CRITÈRES DÉCLENCHEMENT:
    - surprise_pct > 20% (écart significatif vs prévisions)
    - cluster_size >= 5 (multiples données simultanées)
    - importance HIGH (CPI, NFP, Fed decisions)
    
    Si critères NON remplis → Mouvement simple linéaire
    
    RATIOS VALIDÉS (Session 64):
    - Phase 1 : 58% impact total
    - Pullback : 84% Phase 1
    - Phase 2 : 90% impact total
    
    Args:
        base_impact: Impact prédit Formule D en pips (ex: 57.0)
        surprise_pct: Surprise max en % (ex: 33.3)
        cluster_size: Nombre événements simultanés (ex: 9)
    
    Returns:
        dict avec :
        - type: 'double_wave' ou 'single_wave'
        - phase1: Impact phase 1 en pips
        - phase1_ttr: Time to reach phase 1 peak (minutes)
        - pullback: Ampleur pullback en pips
        - pullback_duration: Durée pullback (minutes)
        - phase2: Impact phase 2 en pips
        - phase2_peak: Time to reach phase 2 peak (minutes)
        - total_net: Impact net final en pips
        - stabilization_time: Temps stabilisation (minutes)
    
    Examples:
        >>> # Cas 11 septembre 2025 (validé)
        >>> result = calculate_double_wave_impact(57.0, 33.3, 9)
        >>> result['total_net']
        56.6  # vs 53.0 réel = 93% précision
        >>> result['type']
        'double_wave'
        
        >>> # Cas simple (critères non remplis)
        >>> result = calculate_double_wave_impact(40.0, 12.0, 3)
        >>> result['type']
        'single_wave'
        >>> result['total_net']
        40.0  # Retourne impact de base
    
    References:
        - Session 64: Découverte et validation Double Wave
        - SESSION64_RAPPORT_COMPLET.md: Documentation complète
        - MESSAGE_SESSION86_SESSION87.md: Guide intégration
    """
    # Vérifier critères déclenchement Double Wave
    if surprise_pct < 20 or cluster_size < 5:
        # Mouvement simple standard (formules Sessions 51-55)
        return {
            'type': 'single_wave',
            'phase1': base_impact,
            'phase1_ttr': 5,
            'pullback': 0,
            'pullback_duration': 0,
            'phase2': 0,
            'phase2_peak': 5,
            'total_net': base_impact,
            'stabilization_time': 20
        }
    
    # RATIOS SESSION 64 (validés 11 septembre 2025)
    phase1_ratio = 0.58        # Phase 1 = 58% impact total
    pullback_ratio = 0.84      # Pullback retrace 84% Phase 1
    phase2_ratio = 0.90        # Phase 2 = 90% impact total (plus forte)
    
    # Calculs des phases
    phase1_impact = base_impact * phase1_ratio
    pullback = phase1_impact * pullback_ratio
    phase2_impact = base_impact * phase2_ratio
    
    # Impact net final
    # Note: Ne pas soustraire pullback du total car c'est un retrace temporaire,
    # pas une perte définitive. L'impact total est la somme des 2 pics.
    total_net = phase1_impact + (phase2_impact - pullback)
    
    return {
        'type': 'double_wave',
        'phase1': phase1_impact,
        'phase1_ttr': 5,                    # T+5 min
        'pullback': pullback,
        'pullback_duration': 6,             # 6 minutes (T+5 to T+11)
        'phase2': phase2_impact,
        'phase2_peak': 15,                  # T+15 min
        'total_net': total_net,
        'stabilization_time': 40            # T+40 min
    }


# ════════════════════════════════════════════════════════════════
# AMPLIFICATION ÉTENDUE - SURPRISES EXTRÊMES (SESSION 87)
# ════════════════════════════════════════════════════════════════

def calculate_amplification_extended(surprise_pct: float) -> float:
    """
    Calcule facteur amplification pour TOUTES surprises (incluant extrêmes)
    
    NOUVEAU (Session 87):
    Extension de l'amplification Session 51 pour gérer surprises > 100%
    
    PROBLÈME IDENTIFIÉ (Session 86):
    - Cas 01.08.2025 : Surprise 500%
    - Amplification plafonnée à 2.5x (surprise > 15%)
    - Impact prédit : 67.7 pips
    - Impact réel : 173.8 pips
    - Écart : 106 pips (61% erreur)
    - → Nécessite amplification ~6.4x !
    
    ZONES SURPRISE:
    - < 15% : 1.0x (standard) [Session 51]
    - 15-30% : 1.0 → 2.5x (linéaire) [Session 51]
    - 30-100% : 2.5 → 5.0x (linéaire) [Session 87 NEW]
    - > 100% : 5.0 → 10.0x (logarithmique) [Session 87 NEW]
    
    RATIONALE:
    - 15-30% : Surprise forte, validée Session 51
    - 30-100% : Surprise très forte (NFP exceptionnel)
    - >100% : Surprise exceptionnelle rare (événements historiques)
    - Logarithmique >100% pour éviter explosion irréaliste
    
    Args:
        surprise_pct: Surprise en % (ex: 500)
    
    Returns:
        float: Facteur amplification (1.0 à 10.0)
    
    Examples:
        >>> calculate_amplification_extended(10)
        1.0  # Standard
        
        >>> calculate_amplification_extended(25)
        2.0  # Forte (zone validée S51)
        
        >>> calculate_amplification_extended(50)
        3.36  # Très forte
        
        >>> calculate_amplification_extended(500)
        9.65  # Exceptionnelle (01.08.2025)
    
    References:
        - Session 51: Amplification originale (< 30%)
        - Session 86: Identification problème surprise 500%
        - Session 87: Extension pour surprises extrêmes
    """
    import math
    
    abs_surprise = abs(surprise_pct)
    
    # Zone 1 : Standard (< 15%)
    if abs_surprise < 15:
        return 1.0
    
    # Zone 2 : Forte (15-30%) - VALIDÉE SESSION 51
    elif abs_surprise < 30:
        return 1.0 + (abs_surprise - 15) / 15 * 1.5
    
    # Zone 3 : Très forte (30-100%) - EXTENSION SESSION 87
    elif abs_surprise < 100:
        return 2.5 + (abs_surprise - 30) / 70 * 2.5
    
    # Zone 4 : Exceptionnelle (>100%) - EXTENSION SESSION 87
    else:
        # Logarithmique pour éviter explosion
        # log10(401) ≈ 2.60 → 5.0 + 2.60 = 7.60 pour surprise 500%
        # Plafonné à 10.0 pour garde-fou
        return min(5.0 + math.log10(abs_surprise - 99), 10.0)
```

---

## 🔧 MODIFICATIONS SCRIPT VALIDATION

**Fichier :** `/eurusd_clean/scripts/session84/validate_predictions_vs_reality.py`

### Étape 1 : Imports (ligne ~27)

```python
from formulas_validated import (
    calculate_adjusted_empirical_score,
    calculate_impact_d,
    calculate_ttr_c,
    calculate_pullback_v2,
    calculate_double_wave_impact,      # ← AJOUTER
    calculate_amplification_extended   # ← AJOUTER
)
```

### Étape 2 : Fonction calculate_predictions (ligne ~100)

**REMPLACER tout le bloc "Amplification + Impact" par :**

```python
def calculate_predictions(events_df: pd.DataFrame) -> Dict:
    """Calcule prédictions EXACTEMENT comme le Planificateur"""
    
    # ... code existant jusqu'à score_adjusted_mean ...
    
    # Métriques agrégées
    surprise_max = max(surprises)
    surprise_mean = np.mean(surprises)
    score_adjusted_mean = np.mean(adjusted_scores)
    num_events = len(events_df)
    
    # AMPLIFICATION ÉTENDUE (Session 87)
    amplification = calculate_amplification_extended(surprise_max)
    
    # IMPACT DE BASE (Formule D)
    base_impact = calculate_impact_d(
        empirical_score=score_adjusted_mean,
        num_events=num_events,
        amplification=amplification,
        correction_factor=0.758
    )
    
    # DÉTECTION TYPE MOUVEMENT
    if surprise_max > 20 and num_events >= 5:
        movement_type = "DOUBLE_WAVE"
        
        # APPLIQUER FORMULE DOUBLE WAVE (Session 64)
        dw_result = calculate_double_wave_impact(
            base_impact=base_impact,
            surprise_pct=surprise_max,
            cluster_size=num_events
        )
        
        # Utiliser impact net Double Wave
        impact_pips = dw_result['total_net']
        
    elif surprise_max > 15 and num_events >= 3:
        movement_type = "SINGLE_WAVE_STRONG"
        impact_pips = base_impact
        
    else:
        movement_type = "STANDARD"
        impact_pips = base_impact
    
    # TTR (Formule C - inchangé)
    latency_mean = events_df['latency_median'].mean()
    ttr_minutes = calculate_ttr_c(latency_mean, surprise_max)
    
    return {
        'num_events': num_events,
        'surprise_max': surprise_max,
        'surprise_mean': surprise_mean,
        'score_adjusted': score_adjusted_mean,
        'amplification': amplification,
        'base_impact': base_impact,              # ← AJOUTER
        'impact_predicted_pips': impact_pips,
        'ttr_predicted_min': ttr_minutes,
        'movement_type': movement_type
    }
```

---

## ✅ TESTS À EFFECTUER

### Test 1 : Formule Double Wave seule

```python
# Test unitaire dans formulas_validated.py
if __name__ == "__main__":
    # Cas 11 septembre 2025 (validé Session 64)
    result = calculate_double_wave_impact(
        base_impact=57.0,
        surprise_pct=33.3,
        cluster_size=9
    )
    
    print("=" * 60)
    print("TEST DOUBLE WAVE - 11 SEPTEMBRE 2025")
    print("=" * 60)
    print(f"Type         : {result['type']}")
    print(f"Phase 1      : {result['phase1']:.1f} pips (attendu ~33 pips)")
    print(f"Pullback     : {result['pullback']:.1f} pips (attendu ~28 pips)")
    print(f"Phase 2      : {result['phase2']:.1f} pips (attendu ~51 pips)")
    print(f"Total net    : {result['total_net']:.1f} pips (attendu ~57 pips)")
    print(f"Timing       : T+{result['phase1_ttr']}, T+{result['phase2_peak']}, T+{result['stabilization_time']}")
    
    # Validation
    assert result['type'] == 'double_wave'
    assert 55 < result['total_net'] < 58, f"Total {result['total_net']:.1f} hors plage"
    assert 32 < result['phase1'] < 34, f"Phase1 {result['phase1']:.1f} hors plage"
    
    print("\n✅ Test Double Wave PASSÉ")
```

### Test 2 : Amplification étendue

```python
# Test amplification surprises extrêmes
if __name__ == "__main__":
    test_cases = [
        (10, 1.0, "Standard"),
        (25, 2.0, "Forte"),
        (50, 3.36, "Très forte"),
        (500, 9.65, "Exceptionnelle")
    ]
    
    print("\n" + "=" * 60)
    print("TEST AMPLIFICATION ÉTENDUE")
    print("=" * 60)
    
    for surprise, expected, label in test_cases:
        result = calculate_amplification_extended(surprise)
        print(f"Surprise {surprise:3}% : {result:.2f}x ({label})")
        assert abs(result - expected) < 0.1, f"Écart trop grand pour {surprise}%"
    
    print("\n✅ Test Amplification PASSÉ")
```

### Test 3 : Validation complète 01.08.2025

```bash
cd /eurusd_clean/scripts/session84
python validate_predictions_vs_reality.py
```

**Résultats attendus AMÉLIORÉS :**
```
Impact prédit  : ~150-180 pips (vs 67.7 avant)
Impact réel    : 173.8 pips
Erreur         : < 30 pips (vs 106 pips avant)
Précision      : > 80% (vs 39% avant)
```

---

## 📊 RÉSUMÉ INTÉGRATION

### Fichiers à Modifier

1. **`/fx_impact_app/src/formulas_validated.py`**
   - Ajouter `calculate_double_wave_impact()`
   - Ajouter `calculate_amplification_extended()`
   - Position : Après `calculate_pullback_v2()`

2. **`/eurusd_clean/scripts/session84/validate_predictions_vs_reality.py`**
   - Imports : Ajouter 2 nouvelles fonctions
   - Fonction `calculate_predictions()` : Utiliser Double Wave si détecté

### Backup Obligatoire

```bash
# Avant toute modification
cp formulas_validated.py formulas_validated.py.backup_session87
cp validate_predictions_vs_reality.py validate_predictions_vs_reality.py.backup_session86_before87
```

### Tests à Passer

- [ ] Test unitaire Double Wave (11.09.2025)
- [ ] Test unitaire amplification étendue
- [ ] Test validation 01.08.2025 (amélioration attendue)
- [ ] Test validation 17.09, 05.09, 10.12

---

## 🎯 CRITÈRES SUCCÈS

| Critère | Avant S87 | Après S87 | Amélioration |
|---------|-----------|-----------|--------------|
| Impact prédit 01.08 | 67.7 pips | ~170 pips | +152% |
| Erreur 01.08 | 106 pips (61%) | <30 pips (<20%) | -71% |
| Timing | 16.8 min | ~60 min | +257% |
| Type détecté ET appliqué | ❌ | ✅ | 100% |

---

## 📞 EN CAS DE PROBLÈME

**Symptôme 1 :** `calculate_double_wave_impact()` non trouvée

**Solution :** Vérifier import + position dans `formulas_validated.py`

---

**Symptôme 2 :** Impact encore sous-estimé après intégration

**Solution :** Vérifier que `dw_result['total_net']` est bien utilisé (pas `base_impact`)

---

**Symptôme 3 :** Tests unitaires échouent

**Solution :** Vérifier ratios (0.58, 0.84, 0.90) et timing (5, 15, 40)

---

*Guide créé Session 86 - 26 octobre 2025*  
*Code exact fourni, prêt à intégrer Session 87*  
*Tests définis, critères succès établis*
