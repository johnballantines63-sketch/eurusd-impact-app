# 📊 MISE À JOUR PROJECT_STATE - SESSION 92.1 (CORRECTION)

**À ajouter/remplacer dans project_state_new.md**

---

## 🎯 SESSION 92.1 : ANALYSE AMPLIFICATIONS - ERREUR MÉTHODOLOGIQUE CORRIGÉE (27 octobre 2025)

### Mission et Résultat

**Objectif :** Analyser validation 40 dates (Session 91.2) pour calculer amplifications optimales PAR TYPE

**Résultat :** ⚠️ ANALYSE COMPLÉTÉE mais **ERREUR MÉTHODOLOGIQUE DÉTECTÉE ET CORRIGÉE**

### Contexte Session 91.2

**Problème identifié :**
- MAE global : 43.7 pips (cible < 30) ❌
- Amplification fixe 2.5 inadaptée à variabilité par type
- ISM catastrophique : MAE 93 pips, 6 outliers

**Hypothèse André validée :**
> "l'amplification ne sera pas la même pour tous les events"

### Approche Session 92.1 (SIMPLIFIÉE - INCORRECTE)

**Méthode utilisée :**
```python
# ❌ SIMPLIFIÉ (ne respecte pas méthodologie Planificateur)
ratio = impact_réel_moyen / impact_prédit_moyen
amplification_optimale = 2.5 × ratio
```

**Résultats obtenus (NON VALIDÉS) :**

| Type | Amp Optimale* | MAE Projeté* | Statut |
|------|---------------|--------------|--------|
| CPI | 2.08 | 2.3p | ⚠️ À valider S92.2 |
| NFP | 1.84 | 9.8p | ⚠️ À valider S92.2 |
| FOMC | 0.85 | 15.9p | ⚠️ À valider S92.2 |
| ISM | 0.34 | 80.5p | ⚠️ À valider S92.2 |

*Ces valeurs sont des **ESTIMATIONS GROSSIÈRES**, pas des calibrations validées !

### 🚨 Erreur Méthodologique Identifiée

**Ce qui manquait dans Session 92.1 :**

1. ❌ Pas d'utilisation de `calculate_adjusted_empirical_score()` (Session 55)
2. ❌ Pas d'utilisation de `calculate_impact_d()` (Session 51)
3. ❌ Pas de réplication exacte logique Planificateur lignes 189-277
4. ❌ Simplification excessive (ratio simple vs chaîne complète)

**Règle violée :** "RÈGLE CRITIQUE VALIDATION" (project_state_new.md, Sessions 74-84)
> Pour TOUTE validation prix réels, RÉPLIQUER EXACTEMENT le Planificateur, ne pas créer nouvelles formules

### Correction Appliquée

**Session 92.2 DOIT :**

1. ✅ Lire `formulas_validated.py` (Sessions 51-55)
2. ✅ Lire Planificateur V2.4 lignes 189-277
3. ✅ RÉPLIQUER exactement la méthodologie :
   ```python
   # ✅ CORRECT (réplication Planificateur)
   adjusted_score = calculate_adjusted_empirical_score(base_score, surprise)
   impact_predicted = calculate_impact_d(adjusted_score, num_events, amplification)
   ```
4. ✅ Grid search amplifications par type (0.5 → 3.0, pas 0.1)
5. ✅ Trouver amplification minimisant MAE avec méthodologie COMPLÈTE

### Leçon Critique

**Session 92.1 = Avertissement méthodologique**

**Erreur récurrente projet (Sessions 74-76, maintenant 92.1) :**
- Tenter simplifications au lieu de réplications
- Ignorer formules validées Sessions 51-55
- Court-circuiter méthodologie éprouvée

**Rappel MANDATORY_SESSION_RULES.md :**
> Les formules Sessions 51-55 ont 94-99% précision. Les réutiliser, pas les remplacer.

### Fichiers Créés Session 92.1

```
eurusd_clean/scripts/session92.1/
├── analyze_amplifications_by_type.py (approche simplifiée)
├── ANALYSE_AMPLIFICATIONS_RESULTATS.md (résultats non validés)
└── [6 autres fichiers documentation]

eurusd_clean/docs/
├── SESSION92.1_RAPPORT_COMPLET.md
├── MESSAGE_SESSION92.1_SESSION92.2.md (obsolète)
├── MESSAGE_SESSION92.1_SESSION92.2_CORRECTED.md (⭐ à utiliser)
└── UPDATE_PROJECT_STATE_SESSION92.1.md
```

### Status Session 92.1

⚠️ **RÉSULTATS INDICATIFS UNIQUEMENT - À REVALIDER Session 92.2**

**Acquis :**
- Hypothèse André confirmée (amplification varie par type)
- Ordre de grandeur amplifications identifié
- Problème ISM confirmé

**À corriger Session 92.2 :**
- Méthodologie complète (réplication Planificateur)
- Validation avec formules Sessions 51-55
- Grid search rigoureux

### Prochaine Session 92.2

**Mission :** Calibration CORRECTE avec réplication exacte Planificateur

**Méthode obligatoire :**
1. Charger événements (query SQL identique Planificateur)
2. Pour chaque type, tester amplifications 0.5 → 3.0
3. Calculer impact avec `calculate_adjusted_empirical_score()` + `calculate_impact_d()`
4. Trouver amplification minimisant MAE
5. Valider cohérence avec estimations Session 92.1 (±20%)

**Budget :** 90k tokens

**Objectif :** MAE < 30 pips avec amplifications VALIDÉES

---

## 📚 RÈGLE CRITIQUE VALIDATION (Rappel)

**ÉTABLIE après Sessions 74-84, RÉAFFIRMÉE Session 92.1**

### Méthodologie Obligatoire Validation

Pour TOUTE validation prix réels, vous DEVEZ :

1. **Lire** Planificateur V2.4 complet (lignes 189-277 minimum)
2. **Identifier** formules utilisées (Sessions 51-55)
3. **RÉPLIQUER** exactement même logique (pas simplifier)
4. **Utiliser** `formulas_validated.py` :
   - `calculate_adjusted_empirical_score()` (Session 55)
   - `calculate_impact_d()` (Session 51)
5. **Comparer** prédictions vs réalité
6. **Analyser** écarts avec méthodologie validée

### ❌ Ce Qu'il NE Faut JAMAIS Faire

```python
# ❌ INTERDIT : Simplification
ratio = impact_real / impact_predicted
amp_optimal = 2.5 * ratio

# ❌ INTERDIT : Nouvelle formule
impact_new = train_regression(prices, events)

# ❌ INTERDIT : Court-circuiter formules validées
impact = simple_calculation(score)
```

### ✅ Ce Qu'il FAUT TOUJOURS Faire

```python
# ✅ CORRECT : Réplication exacte
from formulas_validated import (
    calculate_adjusted_empirical_score,
    calculate_impact_d
)

adjusted_score = calculate_adjusted_empirical_score(base_score, surprise)
impact_predicted = calculate_impact_d(adjusted_score, num_events, amplification)
```

### Pourquoi Cette Règle Est Critique

**Raisons :**
1. **Cohérence** : Utilisateurs utilisent Planificateur, pas nouveau système
2. **Validation** : On valide existant, pas ce qui pourrait exister
3. **Précision** : Formules S51-55 = 94-99% (déjà excellentes)
4. **Évite overfitting** : Nouvelles formules sur petits datasets = overfitting garanti

**Exemples échecs :**
- **Sessions 74-76** : ML depuis prix → overfitting sévère (MAE 30+ min)
- **Session 92.1** : Ratio simple → estimations non validées

**Exemples succès :**
- **Sessions 84-91** : Réplication Planificateur → validations réussies
- **Formules S51-55** : Précision 94-99% maintenue

---

**Progression projet :** 94% → 94% (Session 92.1 corrigée, pas de progression réelle)

---

_Mise à jour project_state_new.md - Session 92.1 CORRIGÉE - 27 octobre 2025_
