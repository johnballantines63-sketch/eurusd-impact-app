# REF-032 : Investigation 2025-04-10 - Événements 13:30 Non Détectés

**Date :** 2025-12-06  
**Problème :** Pourquoi les événements US à 13:30 (impact HAUT) et le mouvement à 14:00 ne sont pas détectés ?

---

## 📊 RÉSULTATS INVESTIGATION

### 1. Événements à 13:30

**Constats :**
- ✅ **3 événements à 13:30** trouvés dans la DB
- ❌ **Aucun événement US HIGH (importance_n=3)** à 13:30
- ⚠️ Les événements à 13:30 ne sont pas tous US HIGH

**Événements à 13:30 :**
- Non listés comme US HIGH dans la DB
- Probablement importance_n=1 ou 2, ou pas d'importance_n=3

### 2. Événements à 14:30

**Constats :**
- ✅ **Cluster détecté à 14:30** avec 9 événements
- ✅ **Événements US HIGH** dans ce cluster :
  - `continuing jobless claims` (US, imp=3)
  - `jobless claims 4week average` (US, imp=3)

### 3. Cluster Sélectionné

**Problème identifié :**

| Cluster | Anchor Time | Événements | Type | Sélectionné ? |
|--------|-------------|------------|------|---------------|
| Cluster 1 | **11:15** | 1 événement (ECB Tuominen Speech, EU, imp=3) | GENERIC | ✅ **OUI** |
| Cluster 2 | **14:30** | 9 événements (US HIGH) | GENERIC | ❌ NON |

**Le cluster à 11:15 est sélectionné au lieu de celui à 14:30 !**

### 4. Mouvement Réel

**Constats :**
- ✅ **Mouvement détecté** : 57.10 pips (UP)
- ✅ **Début mouvement** : 13:30-14:00
- ✅ **Pic** : 14:39

**Coïncidence :**
- ❌ **Anchor time cluster sélectionné** : 11:15
- ✅ **Début mouvement réel** : 13:30-14:00
- ❌ **Différence** : ~2h15-2h45

---

## 🔍 CAUSE RACINE

### Problème 1 : Sélection du Mauvais Cluster

**Pourquoi le cluster à 11:15 est sélectionné ?**

La logique de sélection du cluster principal utilise le **score de qualité composite** :
- `score_qualite = importance_n × score_empirique` (moyenne)

**Hypothèse :**
- Cluster 11:15 : 1 événement EU HIGH (imp=3) avec score empirique élevé → score_qualite élevé
- Cluster 14:30 : 9 événements US HIGH mais peut-être scores empiriques plus faibles → score_qualite plus faible

**Le problème :** La logique ne priorise pas assez les événements US HIGH qui coïncident avec le mouvement réel.

### Problème 2 : Événements à 13:30 Non US HIGH

**Pourquoi les événements à 13:30 ne sont pas détectés comme US HIGH ?**

- Les événements à 13:30 dans la DB ne sont pas marqués comme `importance_n=3`
- Ou ils n'ont pas de `empirical_score > 40.0`
- Donc ils ne passent pas le filtre de l'Étape 1 (`min_empirical_score=40.0`)

---

## 💡 SOLUTIONS PROPOSÉES

### Solution 1 : Améliorer la Sélection de Cluster

**Principe :** Prioriser les clusters avec événements US HIGH qui coïncident avec le mouvement réel

**Implémentation :**
1. Détecter le début du mouvement réel (comme dans REF-027)
2. Vérifier la coïncidence mouvement-cluster (±15 min)
3. Bonus pour clusters avec coïncidence dans le score de qualité

**Avantages :**
- Sélectionne le bon cluster (celui qui déclenche le mouvement)
- Améliore les prédictions pour GENERIC

### Solution 2 : Vérifier Événements à 13:30

**Principe :** Vérifier pourquoi les événements à 13:30 ne sont pas US HIGH

**Actions :**
1. Vérifier dans la DB les événements à 13:30
2. Vérifier leur `importance_n` et `empirical_score`
3. Si ce sont des événements importants (CPI, NFP, etc.), corriger la DB

---

## ✅ VALIDATION

### Pourquoi 2025-04-10 est GENERIC ?

**Réponse :** Le cluster sélectionné (11:15, ECB Speech) ne correspond pas au mouvement réel (13:30-14:00, US Jobless Claims).

**Conclusion :**
- Le problème n'est pas les événements à 13:30 (ils existent mais ne sont pas US HIGH)
- Le problème est la **sélection du mauvais cluster** (11:15 au lieu de 14:30)
- Même si on sélectionnait le cluster à 14:30, il faudrait vérifier s'il correspond au mouvement à 13:30-14:00

---

**Document créé le :** 2025-12-06  
**Dernière mise à jour :** 2025-12-06




