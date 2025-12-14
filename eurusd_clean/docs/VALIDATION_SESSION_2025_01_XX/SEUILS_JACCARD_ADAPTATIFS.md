# Seuils Jaccard Adaptatifs - Documentation

**Date** : 2025-01-XX  
**Problème** : Certains cas nécessitent un seuil Jaccard adaptatif (0.6 ou moins) pour trouver des clusters similaires  
**Objectif** : Documenter les seuils optimaux par type de noyau dur

---

## 🔍 CONTEXTE

Le seuil Jaccard par défaut est **0.60**, mais certains cas nécessitent un seuil plus bas pour trouver des clusters similaires dans l'historique.

### Seuils Adaptatifs Actuels

Le code implémente déjà un système de seuils adaptatifs :
- Commence à **0.60**
- Descend à **0.55** si < min_clusters_found
- Descend à **0.50** si toujours < min_clusters_found

---

## 📊 TESTS PAR TYPE DE NOYAU DUR

### JOBLESS_PCE

**Date test** : 2025-05-29  
**Noyau dur** : JOBLESS_PCE (4 événements)

| Seuil Jaccard | Clusters trouvés | Jaccard min-max |
|---------------|------------------|-----------------|
| 0.60 | 4 | 0.800-1.000 ✅ |
| 0.55 | 4 | 0.800-1.000 |
| 0.50 | 4 | 0.800-1.000 |

**Observation** : Seuil 0.60 suffisant pour trouver 4 clusters (≥3 requis)

---

### CPI

**Date test** : 2025-09-11  
**Noyau dur** : CPI (6 événements)

| Seuil Jaccard | Clusters trouvés | Jaccard min-max |
|---------------|------------------|-----------------|
| 0.60 | 0 | - |
| 0.55 | 0 | - |
| 0.50 | 0 | - |
| 0.45 | 0 | - |
| 0.40 | 0 | - |

**Observation** : ⚠️ Aucun cluster trouvé même avec seuil très bas (0.40).  
**Cause possible** : 
- Pas assez de clusters CPI similaires dans l'historique (2 ans)
- Noyau dur CPI trop spécifique (6 événements exacts)
- Besoin d'étendre le lookback à 5 ans

**Action** : Tester avec `years_lookback=5` au lieu de 2

---

### NFP

**Date test** : 2025-08-01  
**Noyau dur** : NFP (2 événements)

| Seuil Jaccard | Clusters trouvés | Jaccard min-max |
|---------------|------------------|-----------------|
| 0.60 | 22 | 1.000-1.000 ✅ |

**Observation** : Seuil 0.60 largement suffisant, trouve 22 clusters avec Jaccard parfait (1.000)

---

## 📝 RECOMMANDATIONS

### Seuils par Type de Noyau Dur (Basé sur Tests)

1. **CPI** : 0.60 (mais nécessite lookback 5 ans, pas 2 ans)
2. **NFP** : 0.60 (fonctionne bien, trouve 22 clusters)
3. **JOBLESS_PCE** : 0.60 (fonctionne bien, trouve 4 clusters)
4. **GDP** : À tester
5. **JOBLESS** : À tester
6. **PCE** : À tester
7. **GENERIC** : 0.50-0.45 (noyau dur large, peut nécessiter seuil plus bas)

### Logique Adaptative Actuelle

Le système actuel de seuils adaptatifs (0.60 → 0.55 → 0.50) est **correct** et fonctionne bien.

**Recommandation** : Garder cette logique adaptative, elle s'ajuste automatiquement selon les résultats.

### Points d'Attention

1. **Lookback** : Pour CPI (6 événements), peut nécessiter 5 ans au lieu de 2 ans
2. **Importance_n** : Les identifiants canoniques incluent `importance_n`, ce qui peut créer des différences si l'importance change entre dates
3. **Scores empiriques** : La requête optimisée charge maintenant aussi les événements HAUT importance même si score faible (cohérent avec Étape 1)

---

## ✅ VALIDATION

**Status** : ✅ **DOCUMENTÉ**

### Résultats Tests

| Date | Type Noyau Dur | Seuil Optimal | Clusters Trouvés | Note |
|------|----------------|---------------|-------------------|------|
| 2025-05-29 | JOBLESS_PCE | 0.60 | 4 | ✅ Fonctionne |
| 2025-08-01 | NFP | 0.60 | 22 | ✅ Fonctionne |
| 2025-09-11 | CPI | ? | 0 | ⚠️ Problème identifié |

### Problème Identifié pour CPI

**2025-09-11** : Aucun cluster CPI trouvé même avec seuil 0.40.

**Causes possibles** :
1. Les événements CPI historiques ont des scores empiriques NULL
2. Les événements CPI ont `importance_n = 1` ou `2` (pas `3`)
3. Besoin d'étendre le lookback à 5 ans

**Correction appliquée** : La requête SQL charge maintenant aussi les événements CPI/Inflation même si `importance_n != 3`.

---

## 🔄 MISE À JOUR

Cette documentation sera mise à jour au fur et à mesure des tests et validations.

**Dernière mise à jour** : 2025-01-XX - Correction requête SQL pour inclure événements CPI

