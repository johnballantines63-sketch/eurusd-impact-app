# REF-011 : Stratégie d'Intégration des Scores core_scores

**Date :** 2025-12-06  
**Objectif :** Définir une stratégie sécurisée pour intégrer les nouveaux scores avec possibilité de rollback

---

## 🎯 STRATÉGIE PROPOSÉE

### Phase 1 : Test Comparatif (Sans Modification du Pipeline)

**Objectif :** Comparer prédictions avec/sans nouveaux scores **sans modifier le pipeline actuel**

**Méthode :**
1. Créer un script de test qui :
   - Exécute le pipeline normalement (scores event_families)
   - Recalcule l'impact base avec scores core_scores
   - Compare les deux prédictions
2. Tester sur dates de validation connues
3. Analyser les différences

**Avantages :**
- ✅ Pas de risque de casser le pipeline actuel
- ✅ Comparaison directe avant/après
- ✅ Identification des cas problématiques

---

### Phase 2 : Critères de Validation

**Critères de succès :**

1. **Précision des prédictions**
   - MAE (Mean Absolute Error) ≤ MAE actuel
   - RMSE (Root Mean Square Error) ≤ RMSE actuel
   - Taux de prédictions acceptables (erreur < 20 pips) ≥ taux actuel

2. **Cohérence**
   - Pas de prédictions aberrantes (ex. > 500 pips)
   - Prédictions dans une plage raisonnable

3. **Amélioration attendue**
   - Meilleure précision pour noyaux durs spécifiques (CPI, NFP, JOBLESS_PCE)
   - Réduction des erreurs pour dates avec noyaux durs identifiés

**Seuil de décision :**
- ✅ **Intégrer** si : Amélioration ≥ 5% OU MAE ≤ MAE actuel
- ⚠️ **Analyser** si : Résultats similaires (différence < 5%)
- ❌ **Ne pas intégrer** si : Dégradation > 5%

---

### Phase 3 : Intégration Conditionnelle

**Si résultats satisfaisants :**

1. **Intégration avec flag de contrôle**
   ```python
   USE_CORE_SCORES = True  # Flag pour activer/désactiver
   
   if USE_CORE_SCORES:
       core_score = get_core_score_from_db(core_type, country)
       if core_score:
           base_score = core_score  # Utiliser score core_scores
       else:
           base_score = mean(event_families_scores)  # Fallback
   else:
       base_score = mean(event_families_scores)  # Comportement actuel
   ```

2. **Test sur dates de validation**
3. **Validation finale**

**Si résultats non satisfaisants :**

1. **Analyser les causes**
   - Pourquoi les nouveaux scores ne fonctionnent pas ?
   - Y a-t-il un biais dans le calcul des scores core_scores ?
   - Les scores sont-ils trop élevés/faibles ?

2. **Alternatives possibles :**
   - **Option A** : Utiliser scores core_scores comme **bonus** (addition) plutôt que remplacement
   - **Option B** : Utiliser scores core_scores uniquement pour certains types (ex. CPI, NFP)
   - **Option C** : Moyenne pondérée : `score_final = 0.7 × core_score + 0.3 × event_families_score`
   - **Option D** : Utiliser scores core_scores uniquement si sample_size ≥ 10 (plus robuste)

3. **Réévaluer la méthode de calcul des scores core_scores**
   - Vérifier la formule (50% avg + 50% p80)
   - Vérifier le facteur de robustesse
   - Comparer avec scores event_families

---

### Phase 4 : Rollback Plan

**Si intégration cause des problèmes :**

1. **Rollback immédiat**
   - Désactiver flag `USE_CORE_SCORES = False`
   - Pipeline revient au comportement actuel

2. **Analyse post-mortem**
   - Identifier les cas problématiques
   - Documenter les raisons de l'échec
   - Proposer corrections

3. **Réessayer avec corrections**
   - Appliquer alternatives (Option A, B, C, ou D)
   - Re-tester

---

## 📋 PLAN D'ACTION RECOMMANDÉ

### Étape 1 : Test Comparatif (Maintenant)

Créer script qui compare :
- Prédictions avec scores event_families (actuel)
- Prédictions avec scores core_scores (nouveau)
- Sur dates de validation connues

**Durée estimée :** 15-30 minutes

### Étape 2 : Analyse des Résultats

- Calculer métriques (MAE, RMSE, taux acceptables)
- Identifier cas problématiques
- Décider : Intégrer / Analyser / Ne pas intégrer

**Durée estimée :** 15-30 minutes

### Étape 3 : Décision

**Si satisfaisant :**
- Intégrer avec flag de contrôle
- Tester sur dates de validation
- Valider

**Si non satisfaisant :**
- Analyser causes
- Proposer alternatives
- Réessayer avec corrections

---

## 🔍 QUESTIONS À RÉSOUDRE AVANT INTÉGRATION

1. **Les scores core_scores sont-ils cohérents avec event_families ?**
   - Comparer scores pour mêmes événements
   - Identifier écarts significatifs

2. **Les scores core_scores sont-ils trop élevés/faibles ?**
   - Vérifier distribution
   - Comparer avec impacts réels observés

3. **Y a-t-il un biais dans le calcul ?**
   - Vérifier formule (50% avg + 50% p80)
   - Vérifier facteur de robustesse

---

## ✅ RECOMMANDATION

**Commencer par Phase 1 (Test Comparatif)** avant toute intégration.

Cela permet de :
- ✅ Évaluer l'impact sans risque
- ✅ Identifier les problèmes potentiels
- ✅ Décider en connaissance de cause

---

**Document créé le :** 2025-12-06  
**Dernière mise à jour :** 2025-12-06




