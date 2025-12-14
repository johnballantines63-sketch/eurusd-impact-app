# REF-031 : Analyse Détaillée - Dates GENERIC

**Date :** 2025-12-06  
**Objectif :** Analyser en détail les dates GENERIC pour comprendre pourquoi les prédictions sont mauvaises

---

## 📊 RÉSULTATS

### Question 1 : Avec quel seuil Jaccard a-t-on trouvé des clusters identiques ?

**Réponse :** Les clusters trouvés ont des scores Jaccard **très élevés** (0.667 à 1.000), bien au-dessus du seuil 0.30.

| Date | Clusters Trouvés | Jaccard Min | Jaccard Max | Jaccard Moyen |
|------|------------------|-------------|-------------|---------------|
| 2024-02-13 | 24 | 0.667 | 1.000 | 0.833 |
| 2025-03-12 | 10 | 0.667 | 1.000 | 0.767 |
| 2024-11-08 | 32 | 0.833 | 1.000 | 0.969 |
| 2025-06-23 | 0 | - | - | - |
| 2025-04-10 | 0 | - | - | - |

**Conclusion :**
- ✅ Le seuil adaptatif (0.30) fonctionne : on trouve des clusters avec scores élevés
- ✅ Les clusters trouvés sont très similaires (Jaccard ≥ 0.667)
- ❌ **MAIS** les prédictions restent mauvaises malgré des clusters identiques

---

### Question 2 : Le début des mouvements correspond-il aux clusters ?

**Réponse :** ❌ **NON** - C'est le problème principal !

| Date | Début Mouvement | Anchor Time Cluster | Différence | Coïncidence |
|------|-----------------|---------------------|------------|-------------|
| 2025-03-12 | 15:40 | 12:00 | **220 minutes** | ❌ NON |
| 2024-11-08 | 17:02 | 16:00 | **62 minutes** | ❌ NON |
| 2025-04-10 | 15:39 | 11:15 | **264 minutes** | ❌ NON |
| 2024-02-13 | ? | 12:00 | ? | À vérifier |
| 2025-06-23 | ? | 12:45 | ? | À vérifier |

**Conclusion :**
- ❌ **Le cluster identifié ne correspond PAS au début du mouvement réel**
- ❌ Les événements du cluster sont à une heure différente du début du mouvement
- ❌ C'est pour ça que les prédictions sont mauvaises : on prédit pour le mauvais moment

---

## 🔍 ANALYSE DÉTAILLÉE

### 2025-03-12

**Cluster :**
- Anchor time : 12:00
- Clusters identiques : 10 (Jaccard 0.667-1.000)
- Événements : Car production (BR), Monetary policy (HU), etc.

**Mouvement réel :**
- Début : 15:40 (différence de 220 minutes)
- Événements à 15:40 : BOC Press Conference (CA), EIA Crude Oil (US), etc.

**Problème :** Le cluster à 12:00 n'est pas celui qui déclenche le mouvement à 15:40

### 2024-11-08

**Cluster :**
- Anchor time : 16:00
- Clusters identiques : 32 (Jaccard 0.833-1.000)
- Événements : ?

**Mouvement réel :**
- Début : 17:02 (différence de 62 minutes)
- Événements à 17:02 : Fed Bowman Speech (US)

**Problème :** Le cluster à 16:00 n'est pas celui qui déclenche le mouvement à 17:02

### 2025-04-10

**Cluster :**
- Anchor time : 11:15
- Clusters identiques : 0 (même avec seuil 0.30)

**Mouvement réel :**
- Début : 15:39 (différence de 264 minutes)
- Événements à 15:39 : Inflation (XK), Core Inflation (EG), Fed Logan Speech (US)

**Problème :** Le cluster à 11:15 n'est pas celui qui déclenche le mouvement à 15:39

---

## 💡 CAUSE RACINE

### Problème Identifié

**Les dates GENERIC ont des clusters d'événements qui ne correspondent PAS au début du mouvement réel.**

**Pourquoi ?**
1. **Événements multiples** : Plusieurs clusters d'événements dans la journée
2. **Sélection du mauvais cluster** : Le pipeline sélectionne un cluster (ex. 12:00) mais le mouvement commence plus tard (ex. 15:40)
3. **Événements non corrélés** : Les événements du cluster sélectionné ne sont pas ceux qui déclenchent le mouvement

**Impact :**
- Prédictions basées sur le mauvais cluster → Prédictions incorrectes
- Même avec clusters identiques, si c'est le mauvais cluster, la prédiction est fausse

---

## ✅ VALIDATION DE LA DÉCISION

### Pourquoi Exclure les Dates GENERIC ?

1. **Clusters identiques trouvés** ✅ (avec seuil adaptatif)
2. **MAIS clusters ne correspondent pas au mouvement** ❌
3. **Prédictions mauvaises** ❌ (erreur moyenne 86.1%)

**Conclusion :**
- Le problème n'est PAS le seuil Jaccard
- Le problème est la **sélection du mauvais cluster**
- Les dates GENERIC sont **non tradables** car on ne peut pas identifier correctement le cluster qui déclenche le mouvement

---

## 📋 RECOMMANDATIONS

### Court Terme

✅ **Exclure les dates GENERIC** (déjà fait)
- Les dates GENERIC sont non tradables
- Impossible de prédire avec précision

### Long Terme (Amélioration Future)

1. **Améliorer la sélection de cluster** :
   - Vérifier la coïncidence mouvement-cluster avant de sélectionner
   - Prioriser les clusters avec événements coïncidant avec le début du mouvement

2. **Détection multi-clusters** :
   - Identifier tous les clusters de la journée
   - Vérifier lequel correspond au mouvement réel
   - Utiliser celui-là pour la prédiction

3. **Validation post-détection** :
   - Après avoir identifié le cluster, vérifier s'il correspond au mouvement
   - Si non, essayer d'autres clusters ou exclure la date

---

**Document créé le :** 2025-12-06  
**Dernière mise à jour :** 2025-12-06




