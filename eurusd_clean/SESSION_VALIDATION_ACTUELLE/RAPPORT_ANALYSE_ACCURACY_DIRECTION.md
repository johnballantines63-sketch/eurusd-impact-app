# Rapport d'Analyse : Accuracy Directionnelle (48%)

**Date** : 2025-12-07  
**Objectif** : Comprendre pourquoi l'accuracy reste à 48% et proposer améliorations

---

## 📊 Résultats Actuels

### Accuracy Globale
- **48.0%** (24/50 corrects)
- **52.0%** d'erreurs (26/50)

### Répartition des Erreurs

| Type d'Erreur | Nombre | % des Erreurs |
|---------------|--------|---------------|
| **UP→DOWN** | 12 | 46.2% |
| **DOWN→UP** | 6 | 23.1% |
| **UP→UNKNOWN** | 6 | 23.1% |
| **DOWN→UNKNOWN** | 2 | 7.7% |

### Observations Clés

1. **Biais UP→DOWN** : 12 cas (46% des erreurs)
   - ⚠️ Le modèle prédit trop souvent DOWN quand c'est UP
   - Suggère un problème avec les familles "normales" (CPI, NFP, etc.)

2. **Surprise Moyenne** :
   - Direction correcte : **91.57%**
   - Direction incorrecte : **74.21%**
   - ✅ Les directions correctes ont une surprise plus élevée
   - ⚠️ Mais surprise élevée ne garantit pas direction correcte

3. **Cas UNKNOWN** : 8/50 (16%)
   - ⚠️ Trop élevé (16% des cas)
   - Principalement UP→UNKNOWN (6 cas)

---

## 🔍 Analyse des Problèmes

### Problème 1 : Biais UP→DOWN (12 cas)

**Symptôme** : Le modèle prédit DOWN alors que le mouvement réel est UP

**Causes Possibles** :
1. **Familles "normales" mal interprétées** :
   - CPI, NFP, etc. : surprise+ = GOOD for USD → EUR/USD DOWN
   - Mais peut-être que dans certains contextes, l'interprétation est inversée

2. **Pondération insuffisante** :
   - Les événements avec surprise positive (familles normales) dominent
   - Les événements avec surprise négative (ou familles inversées) sont sous-pondérés

3. **Surprise cluster faussée** :
   - Si plusieurs événements avec surprise positive, la somme est positive
   - Mais la direction devrait être DOWN (familles normales)
   - Le calcul actuel peut s'annuler incorrectement

### Problème 2 : Cas UNKNOWN (8 cas, 16%)

**Symptôme** : Le modèle ne peut pas prédire la direction (direction_sum = 0)

**Causes** :
1. **Tous événements avec surprise nulle** :
   - Après exclusion < 0.1%, il reste des événements avec surprise très faible
   - Ces événements retournent direction = 0 (neutre)
   - Somme = 0 → UNKNOWN

2. **Annulation parfaite** :
   - Événements UP et DOWN s'annulent exactement
   - Exemple : +1 (UP) + -1 (DOWN) = 0 → UNKNOWN

**Solution** : Fallback intelligent nécessaire

### Problème 3 : Surprise Élevée mais Direction Incorrecte

**Observation** : Surprise moyenne incorrecte = 74.21% (toujours élevée)

**Implication** :
- ⚠️ Même avec surprise élevée, la direction peut être incorrecte
- Suggère que la **magnitude de surprise** n'est pas le seul facteur
- Le **contexte** (familles, nombre d'événements, etc.) est important

---

## 💡 Améliorations Proposées

### Amélioration 1 : Seuil Surprise Plus Élevé

**Problème** : Seuil actuel 0.1% est trop bas

**Solution** : Tester seuils plus élevés
- **0.5%** : Exclut plus de bruit
- **1.0%** : Seulement surprises significatives
- **Adaptatif** : Seuil selon type d'événement

**Impact Attendu** :
- ✅ Réduit bruit dans calcul direction
- ✅ Améliore précision pour surprises significatives
- ⚠️ Peut augmenter cas UNKNOWN

### Amélioration 2 : Pondération Non-Linéaire

**Problème** : Pondération linéaire (`surprise × score`)

**Solution** : Pondération non-linéaire
- **surprise²** : Donne plus de poids aux grandes surprises
- **sqrt(surprise)** : Atténue les très grandes surprises
- **log(surprise + 1)** : Compresse l'échelle

**Impact Attendu** :
- ✅ Les grandes surprises dominent mieux
- ✅ Réduit influence des petites surprises
- ⚠️ Peut créer biais si une surprise est très grande

### Amélioration 3 : Surprise Cluster + Famille Dominante

**Problème** : Calcul direction événement par événement

**Solution** : Utiliser surprise cluster directement
```python
# 1. Calculer surprise cluster (somme vectorielle)
surprise_cluster = sum(surprises) / len(surprises)

# 2. Identifier famille dominante (plus grand score total)
dominant_family = max(family_scores, key=family_scores.get)

# 3. Utiliser surprise cluster avec famille dominante
direction = get_event_direction(dominant_family, surprise_cluster)
```

**Impact Attendu** :
- ✅ Plus cohérent avec calcul impact
- ✅ Prend en compte interaction entre événements
- ⚠️ Ignore autres familles (peut être un problème)

### Amélioration 4 : Fallback Intelligent pour UNKNOWN

**Problème** : 8 cas UNKNOWN (16%)

**Solution** : Stratégie de fallback
1. **Famille dominante** : Utiliser direction de la famille avec plus grand score
2. **Pattern historique** : Utiliser direction moyenne historique pour cette date
3. **Tendance pré-événement** : Utiliser direction du mouvement avant l'événement
4. **Majorité non-nulle** : Si quelques événements ont direction, utiliser majorité

**Impact Attendu** :
- ✅ Réduit cas UNKNOWN de 16% à < 5%
- ✅ Améliore accuracy globale
- ⚠️ Peut introduire erreurs si fallback incorrect

### Amélioration 5 : Correction Biais UP→DOWN

**Problème** : 12 cas UP→DOWN (46% des erreurs)

**Solution** : Analyser spécifiquement ces cas
1. **Vérifier familles impliquées** : Sont-elles toutes "normales" ?
2. **Vérifier signe surprise** : Sont-elles toutes positives ?
3. **Ajuster pondération** : Peut-être sous-pondérer certaines familles
4. **Contexte temporel** : Y a-t-il un pattern temporel ?

**Impact Attendu** :
- ✅ Réduit biais UP→DOWN
- ✅ Améliore accuracy globale significativement

---

## 🎯 Plan d'Action Prioritaire

### Phase 1 : Tests Rapides (Impact Immédiat)

1. ✅ **Tester seuil surprise 0.5%** (au lieu de 0.1%)
   - Impact : Réduit bruit, peut améliorer précision
   - Effort : Faible (changement 1 ligne)

2. ✅ **Tester pondération surprise²**
   - Impact : Donne plus de poids aux grandes surprises
   - Effort : Faible (changement 1 ligne)

3. ✅ **Implémenter fallback famille dominante**
   - Impact : Réduit UNKNOWN de 16% à ~8%
   - Effort : Moyen (nouvelle fonction)

### Phase 2 : Analyses Approfondies

4. ⏳ **Analyser cas UP→DOWN spécifiquement**
   - Identifier pattern commun
   - Ajuster pondération ou logique

5. ⏳ **Tester approche surprise cluster + famille dominante**
   - Comparer avec approche actuelle
   - Choisir meilleure approche

### Phase 3 : Optimisation

6. ⏳ **Optimiser paramètres** (seuil, pondération)
   - Grid search sur paramètres
   - Validation croisée

---

## 📊 Métriques de Succès

**Objectif** : Accuracy > 60%

**Cibles Intermédiaires** :
- ✅ Réduire UNKNOWN : 16% → < 10%
- ✅ Réduire biais UP→DOWN : 12 cas → < 8 cas
- ✅ Améliorer accuracy : 48% → > 55%

---

**Status** : 🔍 **Analyse complétée - Tests à effectuer**


