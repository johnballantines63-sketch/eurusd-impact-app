# MESSAGE SESSION 87 → SESSION 88

**Date :** 26 octobre 2025  
**Session 87 :** ✅ Double Wave intégré  
**Session 88 :** Ajuster amplification + Tests multi-dates

---

## 🎯 MISSION SESSION 88

**Objectif :** Ajuster amplification pour surprises extrêmes + Valider 4 dates

**Budget :** 190,000 tokens

---

## 📚 LECTURE OBLIGATOIRE

1. `MANDATORY_SESSION_RULES.md`
2. `project_state_new.md` 
3. `SESSION87_RAPPORT.md` (ce rapport)
4. `MESSAGE_SESSION86_SESSION87.md`

---

## ✅ ACQUIS SESSION 87

1. Double Wave intégré dans script validation
2. Découverte : Planificateur utilise Double Wave pour timeline SEULEMENT
3. Correction : Script utilise `base_impact` (comme Planificateur)
4. Problème identifié : Amplification 2.5x insuffisant surprise 500%

---

## 🚀 PLAN SESSION 88

### ÉTAPE 1 : Fonction Amplification Étendue (20k tokens)

**Fichier :** `formulas_validated.py`

```python
def calculate_amplification_extended(surprise_pct: float) -> float:
    """
    Zones : 0-15%, 15-30% (S51), 30-100%, >100%
    """
    abs_surprise = abs(surprise_pct)
    
    if abs_surprise < 15:
        return 1.0
    elif abs_surprise < 30:
        return 1.0 + (abs_surprise - 15) / 15 * 1.5  # S51 validé
    elif abs_surprise < 100:
        return 2.5 + (abs_surprise - 30) / 70 * 2.5
    else:
        import math
        return min(5.0 + math.log10(abs_surprise - 99), 10.0)
```

### ÉTAPE 2 : Modifier Script (10k tokens)

Ligne 125 :
```python
# AVANT
amplification = min(surprise_max / 10, 2.5)

# APRÈS  
amplification = calculate_amplification_extended(surprise_max)
```

### ÉTAPE 3 : Test 01.08.2025 (10k tokens)

Attendu :
- Surprise 500% → Amplification ~9.7x
- Impact ~150-180 pips
- MAE < 30 pips ✅

### ÉTAPE 4 : Tests 3 autres dates (40k tokens)

- 17.09.2025
- 05.09.2025  
- 10.12.2025

### ÉTAPE 5 : Documentation (20k tokens)

- Rapport final
- Message Session 89

---

## 📝 FICHIERS CLÉS

**Script validation :**
`/eurusd_clean/scripts/session84/validate_predictions_vs_reality.py` v1.2

**Formules :**
`/fx_impact_app/src/formulas_validated.py`

---

**Tokens Session 87 :** 132,000 / 190,000 (69%)  
**GO Session 88 !** 🚀
