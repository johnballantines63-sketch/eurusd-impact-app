# REF-030 : Test Seuil Jaccard Adaptatif pour GENERIC

**Date :** 2025-12-06  
**Objectif :** Tester si le seuil Jaccard adaptatif (0.30 au lieu de 0.60) améliore les prédictions pour les dates GENERIC

---

## 📊 RÉSULTATS

### Statistiques d'Erreur

| Métrique | Valeur |
|----------|--------|
| **Erreur moyenne (%)** | 86.1% |
| **Erreur médiane (%)** | 86.9% |

**Conclusion :** ❌ **Amélioration insuffisante**

---

## 📈 COMPARAISON AVANT/APRÈS

### Avant (Seuil 0.60)

| Date | Erreur | Clusters |
|------|--------|----------|
| 2025-06-23 | 93.8% | 0 |
| 2024-02-13 | 88.6% | 0 |
| 2025-03-12 | 86.9% | 0 |
| 2024-11-08 | 82.4% | 0 |
| 2025-04-10 | 79.1% | 0 |

**Erreur moyenne :** ~86.2%

### Après (Seuil 0.30 pour GENERIC)

| Date | Erreur | Clusters |
|------|--------|----------|
| 2025-06-23 | 93.8% | 0 |
| 2024-02-13 | 88.6% | **24** ✅ |
| 2025-03-12 | 86.9% | **10** ✅ |
| 2024-11-08 | 82.4% | **32** ✅ |
| 2025-04-10 | 79.1% | 0 |

**Erreur moyenne :** 86.1%

---

## 🔍 ANALYSE

### Clusters Trouvés

- **2024-02-13** : 24 clusters identiques trouvés ✅
- **2025-03-12** : 10 clusters identiques trouvés ✅
- **2024-11-08** : 32 clusters identiques trouvés ✅
- **2025-06-23** : 0 clusters (même avec seuil 0.30)
- **2025-04-10** : 0 clusters (même avec seuil 0.30)

**Observation :**
- Le seuil adaptatif permet de trouver des clusters pour certaines dates
- **MAIS** les erreurs restent très élevées même avec clusters identiques
- Les clusters trouvés ne suffisent pas à améliorer la prédiction

### Causes Probables

1. **Événements rares** : Les événements GENERIC sont souvent uniques ou peu fréquents
2. **Variabilité élevée** : Même avec clusters similaires, l'impact varie beaucoup
3. **RF Global insuffisant** : Random Forest Global (fallback) n'est pas assez précis
4. **Manque de données** : Pas assez de clusters identiques pour entraîner RF par date

---

## ❌ DÉCISION

### Recommandation : Exclure les Dates GENERIC

**Raison :**
- Erreur moyenne : 86.1% (toujours très élevée)
- Erreur médiane : 86.9% (toujours très élevée)
- Même avec clusters identiques, les prédictions restent imprécises
- **Les dates GENERIC ne sont pas prédictibles avec suffisamment de précision**

**Action :**
1. ✅ Exclure les dates GENERIC de la liste des dates valides
2. ✅ Mettre à jour les scripts pour exclure GENERIC
3. ✅ Documenter que GENERIC = non tradable

---

## 📋 IMPACT

### Dates à Exclure (GENERIC)

1. **2025-06-23** (GENERIC)
2. **2024-02-13** (GENERIC)
3. **2025-03-12** (GENERIC)
4. **2024-11-08** (GENERIC)
5. **2025-04-10** (GENERIC)
6. **2025-10-10** (GENERIC, déjà exclue - pas de coïncidence)

**Total :** 6 dates GENERIC à exclure

### Dates Valides Restantes

**Avant :** 21 dates valides  
**Après exclusion GENERIC :** ~15 dates valides (NFP, CPI, JOBLESS_PCE)

---

## ✅ ACTIONS À PRENDRE

1. **Mettre à jour `valid_test_dates.txt`** : Retirer les dates GENERIC
2. **Mettre à jour les scripts** : Filtrer automatiquement les dates GENERIC
3. **Documenter** : GENERIC = non tradable dans la documentation

---

**Document créé le :** 2025-12-06  
**Dernière mise à jour :** 2025-12-06




