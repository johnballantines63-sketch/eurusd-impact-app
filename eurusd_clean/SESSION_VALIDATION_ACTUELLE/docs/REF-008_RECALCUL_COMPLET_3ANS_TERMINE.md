# REF-008 : Recalcul Complet Scores Noyaux Durs - 3 Ans

**Date :** 2025-12-06  
**Période :** 2023-01-01 à 2025-12-06  
**Statut :** ✅ **TERMINÉ AVEC SUCCÈS**

---

## 📊 RÉSULTATS GLOBAUX

### Statistiques

- **Période analysée :** 2023-01-01 à 2025-12-06 (~1095 jours)
- **Mouvements forts détectés :** 457
- **Dates avec noyaux durs identifiés :** 351
- **Types de noyaux durs calculés :** 8
- **Scores mis à jour dans DB :** 8

---

## 🎯 SCORES CALCULÉS PAR TYPE NOYAU DUR

| Core Type | Country | Score | Avg Impact | P80 Impact | Sample Size | Distribution |
|-----------|---------|-------|------------|------------|-------------|--------------|
| **NFP** | US | **80.13** | 65.82 pips | 94.44 pips | 43 | DOWN: 23, UP: 20 |
| **CPI** | US | **75.06** | 59.83 pips | 90.28 pips | 32 | UP: 21, DOWN: 11 |
| **JOBLESS_PCE** | US | **53.51** | 47.16 pips | 59.86 pips | 20 | DOWN: 13, UP: 7 |
| **JOBLESS** | US | **51.80** | 44.87 pips | 58.72 pips | 54 | DOWN: 28, UP: 26 |
| **GENERIC** | US | **44.92** | 38.94 pips | 50.90 pips | 166 | UP: 92, DOWN: 74 |
| **CPI** | DE | **43.71** | 44.51 pips | 52.62 pips | 13 | DOWN: 7, UP: 6 |
| **PCE** | US | **38.21** | 36.92 pips | 47.98 pips | 14 | UP: 8, DOWN: 6 |
| **GENERIC** | DE | **25.53** | 33.87 pips | 39.06 pips | 4 | UP: 3, DOWN: 1 |

---

## 📈 ANALYSE DES RÉSULTATS

### Top 3 Noyaux Durs par Score

1. **NFP (US) : 80.13**
   - 43 occurrences sur 3 ans
   - Impact moyen : 65.82 pips
   - Impact P80 : 94.44 pips
   - Distribution équilibrée (23 DOWN, 20 UP)

2. **CPI (US) : 75.06**
   - 32 occurrences sur 3 ans
   - Impact moyen : 59.83 pips
   - Impact P80 : 90.28 pips
   - Biais haussier (21 UP, 11 DOWN)

3. **JOBLESS_PCE (US) : 53.51**
   - 20 occurrences sur 3 ans
   - Impact moyen : 47.16 pips
   - Impact P80 : 59.86 pips
   - Biais baissier (13 DOWN, 7 UP)

### Observations

- **NFP et CPI US** sont les noyaux durs les plus impactants (scores > 75)
- **JOBLESS_PCE** et **JOBLESS** ont des scores similaires (~51-53)
- **GENERIC US** représente le plus grand nombre d'occurrences (166)
- **CPI DE** a un score proche de GENERIC US (43.71 vs 44.92)
- **PCE** seul a un score plus faible (38.21)

---

## ✅ VALIDATION

### Points Validés

1. ✅ **Méthode d'identification** : Fonctionne correctement
2. ✅ **Filtrage événements sans estimate** : Discours Fed, etc. exclus
3. ✅ **Détection mouvements forts** : 457 mouvements ≥ 20 pips
4. ✅ **Identification noyaux durs** : 351 dates avec noyaux durs identifiés
5. ✅ **Calcul scores** : 8 types de noyaux durs avec scores calculés
6. ✅ **Sauvegarde DB** : Table `core_scores` mise à jour

### Cohérence avec Tests Préliminaires

- **2025-05-29 (JOBLESS_PCE)** : Score test = 62.58, Score final = 53.51
  - Différence due à l'agrégation sur 20 occurrences (vs 1 seule date)
  - Score final plus robuste (moyenne sur échantillon)

- **2025-09-11 (CPI)** : Score test = 43.68, Score final US = 75.06
  - Différence due à l'agrégation sur 32 occurrences (vs 1 seule date)
  - Score final plus robuste (moyenne sur échantillon)

---

## 📋 FICHIERS GÉNÉRÉS

1. **CSV Résultats :**
   - `SESSION_VALIDATION_ACTUELLE/outputs/core_scores_historical_2023-01-01_2025-12-06.csv`

2. **Log Complet :**
   - `SESSION_VALIDATION_ACTUELLE/outputs/recalcul_complet_3ans.log`

3. **Table DB :**
   - `core_scores` (8 lignes mises à jour)

---

## 🎯 UTILISATION

Les scores calculés sont maintenant disponibles dans la table `core_scores` et peuvent être utilisés dans le pipeline pour :

1. **Améliorer la prédiction d'impact** : Utiliser scores spécifiques par type de noyau dur
2. **Affiner la sélection de clusters** : Prioriser clusters avec noyaux durs à score élevé
3. **Optimiser l'amplification** : Ajuster selon le type de noyau dur détecté

---

## 📝 PROCHAINES ÉTAPES

1. ✅ Recalcul terminé
2. ⏳ Intégrer scores dans pipeline (Étape 3 : Définir Noyau Dur)
3. ⏳ Tester prédictions avec nouveaux scores
4. ⏳ Comparer performances avant/après

---

**Document créé le :** 2025-12-06  
**Dernière mise à jour :** 2025-12-06




