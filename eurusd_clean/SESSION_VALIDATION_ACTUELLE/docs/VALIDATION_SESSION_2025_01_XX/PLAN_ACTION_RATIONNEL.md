# Plan d'Action Rationnel - Suite des Corrections

**Date** : 2025-01-XX  
**Objectif** : Continuer les corrections de manière rationnelle et validée

---

## ✅ ÉTAT ACTUEL

### Corrections Validées
- ✅ Étape 6 : Calcul Impacts Base & Amplifications
- ✅ Étape 8.1 : Calcul Impact Base (cluster cible)
- ✅ Étape 8.2 : Détection Tendance Réelle

### Code Actuel Étape 8.3
**Ligne 1085-1091** : Simplifié (moyenne simple)
```python
amplification_predite = 1.0
if identical_clusters and analysis_results.get('results_df') is not None:
    results_df = analysis_results['results_df']
    if 'amplification_parfaite' in results_df.columns:
        amplification_predite = results_df['amplification_parfaite'].mean()
```

### Ce qui est Documenté pour Étape 8.3
**Hiérarchie attendue** :
1. Random Forest par date (si >= 5 clusters identiques)
2. Random Forest global (fallback)
3. Modèle linéaire (fallback)
4. Moyenne des amplifications historiques (dernier fallback)

---

## 🔍 DIAGNOSTIC

### Modules Manquants
- ❌ `src/core/amplification_random_forest.py` (RF global)
- ❌ `src/core/amplification_random_forest_per_date.py` (RF par date)

### Options

#### Option A : Créer les Modules RF Complets
**Avantages** :
- ✅ Conforme à la documentation complète
- ✅ Meilleure précision prédictive
- ✅ Utilise toute la puissance du ML

**Inconvénients** :
- ⏱️ Temps de développement important
- 🧪 Nécessite validation et tests
- 📊 Nécessite données d'entraînement

#### Option B : Implémenter Hiérarchie Simplifiée (Sans RF)
**Avantages** :
- ✅ Rapide à implémenter
- ✅ Utilise modèles linéaires (plus simple)
- ✅ Peut être validé rapidement

**Inconvénients** :
- ⚠️ Moins précis que RF
- ⚠️ Ne correspond pas exactement à la documentation

#### Option C : Implémenter Hiérarchie avec Fallback RF
**Avantages** :
- ✅ Hiérarchie complète implémentée
- ✅ Fallback vers moyenne si RF indisponible
- ✅ Peut être amélioré plus tard avec RF réel

**Inconvénients** :
- ⚠️ RF sera un placeholder pour l'instant

---

## 🎯 DÉCISION RATIONNELLE

### Approche Recommandée : **Option C (Hiérarchie avec Fallback)**

**Raisonnement** :
1. ✅ Respecte la structure documentée
2. ✅ Permet validation immédiate de la logique
3. ✅ Peut être amélioré progressivement
4. ✅ Ne bloque pas les autres corrections

**Plan d'Implémentation** :

#### Phase 1 : Hiérarchie Structure (Sans RF Réel)
1. Implémenter la hiérarchie complète
2. RF par date → placeholder retournant moyenne
3. RF global → placeholder retournant moyenne
4. Modèle linéaire → implémenter réellement
5. Moyenne → déjà implémentée

#### Phase 2 : Validation
1. Tester avec clusters identiques
2. Vérifier que la hiérarchie fonctionne
3. Valider les fallbacks

#### Phase 3 : Amélioration Future (Optionnel)
1. Créer modules RF réels
2. Remplacer placeholders
3. Entraîner modèles

---

## 📋 PLAN D'ACTION IMMÉDIAT

### Prochaine Étape : Étape 8.3

**Objectif** : Implémenter hiérarchie complète avec fallbacks

**Tâches** :
1. [ ] Créer fonction `predict_amplification_hierarchical()`
2. [ ] Implémenter RF par date (placeholder → moyenne si >= 5 clusters)
3. [ ] Implémenter RF global (placeholder → moyenne)
4. [ ] Implémenter modèle linéaire réel
5. [ ] Tester hiérarchie
6. [ ] Valider avec test spécifique

**Critères de Succès** :
- ✅ Hiérarchie respectée (RF date → RF global → linéaire → moyenne)
- ✅ Fallbacks fonctionnent correctement
- ✅ Test passe avec validation

---

## 🔄 ORDRE DES CORRECTIONS RESTANTES

1. **Étape 8.3** : Prédiction Amplification (hiérarchie)
2. **Étape 8.4-8.5** : Ajustements Support/Résistance + Finnhub
3. **Étape 8.6** : Détection Pattern Réelle
4. **Étape 8.7** : Stratégie Hybride Pattern/Formules
5. **Étape 8.8** : Calcul Target de Sortie

**Règle** : Une correction à la fois, avec validation avant de passer à la suivante.

---

## 📊 STATUT

| Étape | Statut | Priorité | Complexité |
|-------|--------|-----------|------------|
| 8.3 | ⏳ À faire | Critique | Moyenne |
| 8.4-8.5 | ⏳ À faire | Important | Moyenne |
| 8.6 | ⏳ À faire | Critique | Élevée |
| 8.7 | ⏳ À faire | Critique | Moyenne |
| 8.8 | ⏳ À vérifier | Moyenne | Faible |

---

**Prochaine Action** : Implémenter Étape 8.3 avec hiérarchie complète

