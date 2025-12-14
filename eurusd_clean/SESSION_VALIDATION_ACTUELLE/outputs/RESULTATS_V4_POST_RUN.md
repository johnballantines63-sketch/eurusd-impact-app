# 📊 RÉSULTATS POST-RUN V4

**Date** : 2025-12-08  
**Script** : `build_v2_scores_composite.py` (avec patch V4)

---

## ✅ CHECK A : ÉVÉNEMENTS MAJEURS REVENUS

### Événements trouvés avec weights non-nuls

| Event Key | Horizon | Weight | |Weight| | n_events |
|-----------|---------|--------|---------|----------|
| **Unemployment_surp_neg** | 4h | -0.339463 | 0.339463 | 109 |
| **Unemployment_surp_pos** | 4h | +0.329460 | 0.329460 | 51 |
| **PMI_surp_neg** | 1j | -0.243656 | 0.243656 | 569 |
| **Unemployment_surp_neg** | 1j | -0.227377 | 0.227377 | 109 |
| **Employment Change_surp_neg** | 4h | -0.131512 | 0.131512 | 33 |
| **ISM_surp_neg** | 1j | +0.107625 | 0.107625 | 129 |
| **NFP_surp_neg** | 4h | +0.095506 | 0.095506 | 51 |
| **NFP_surp_neg** | 1j | -0.078048 | 0.078048 | 51 |
| **NFP_surp_pos** | 1h | - | - | 65 |
| **Consumer Confidence_surp_pos** | 1h | -0.104725 | 0.104725 | 116 |
| **Consumer_surp_pos** | 4h | -0.103968 | 0.103968 | 98 |
| **ISM_surp_pos** | 1h | -0.070153 | 0.070153 | 122 |

**✅ SUCCÈS** : Tous les événements majeurs sont revenus avec des weights significatifs et n_events ≥ 20 !

---

## ⚠️ CHECK B : DISTRIBUTION S (NEUTRES)

### Statistiques

| Métrique | Valeur |
|----------|--------|
| **Médiane |S|** | 0.0063 (très proche de 0) |
| **Moyenne |S|** | 0.0070 |
| **Écart-type** | 0.1102 |
| **% |S| < 0.02** | 32.0% |
| **% |S| < 0.05** | 54.0% |
| **% |S| < 0.10** | **76.0%** ⚠️ |

**❌ ÉCHEC** : 76% des scores sont neutres (objectif < 35%)

---

## ⚠️ CHECK C : DIRECTIONNEL

### Résultats à θ=0.0

| Métrique | Valeur | Objectif | Status |
|----------|--------|----------|--------|
| **Accuracy** | 51.2% | > 52% | ⚠️ Légèrement en dessous |
| **Coverage** | 86.0% | 70-80% | ✅ Bon |
| **Balanced Accuracy** | 49.7% | > 50% | ⚠️ Légèrement en dessous |
| **F1 Macro** | 49.4% | > 50% | ⚠️ Légèrement en dessous |
| **Corrélation S ↔ direction** | 0.0072 | > 0.05 | ❌ Très faible |

### Comparaison avec avant V4

| Métrique | Avant V4 | Après V4 | Évolution |
|----------|----------|----------|-----------|
| **Accuracy** | 46.2% | 51.2% | ✅ +5.0% |
| **Coverage** | 78.0% | 86.0% | ✅ +8.0% |
| **Corrélation** | -0.0024 | 0.0072 | ✅ Amélioration |

**⚠️ RÉSULTAT INTERMÉDIAIRE** :
- Légère amélioration de l'accuracy (+5%) et coverage (+8%)
- Mais corrélation toujours très faible (0.0072) et 76% de neutres

---

## 🔍 TOP 20 ALPHA WEIGHTS (par |weight|)

| Horizon | Event Key | Weight |
|---------|-----------|--------|
| 4h | Trade Balance_surp_pos | +0.376765 |
| 4h | Unemployment_surp_neg | -0.339463 |
| 4h | Unemployment_surp_pos | +0.329460 |
| 4h | Trade Balance_surp_neg | +0.264193 |
| 4h | PPI_surp_neg | +0.263575 |
| 1j | PMI_surp_neg | -0.243656 |
| 4h | Confidence_surp_pos | +0.239949 |
| 1j | Business Confidence_surp_pos | -0.239204 |
| 1j | Business Confidence_surp_neg | -0.234998 |
| 1j | Unemployment_surp_neg | -0.227377 |
| 4h | Manufacturing_surp_pos | -0.218514 |
| 4h | PPI_surp_pos | +0.215568 |
| 1j | GDP_surp_pos | +0.211597 |
| 1j | PPI_surp_neg | +0.205032 |
| 1j | Building Permits_surp_neg | +0.186634 |
| 1j | Industrial Production_surp_pos | +0.168216 |
| 4h | Michigan_Current_Conditions_surp_neg | +0.164669 |
| 1j | Durable Goods_surp_pos | -0.142757 |
| 4h | Monthly_Budget_Statement_surp_neg | +0.139750 |
| 4h | Building Permits_surp_neg | +0.132494 |

---

## 📋 DIAGNOSTIC

### Problèmes identifiés

1. **76% de scores neutres** : Le signal reste trop faible
   - Les alphas majeurs sont revenus, mais leurs contributions s'annulent peut-être
   - "Other" domine toujours (61% des événements dans le dataset)

2. **Corrélation très faible** (0.0072) : Le signal directionnel est encore noyé
   - Amélioration par rapport à -0.0024, mais toujours insuffisant

3. **Accuracy ~51%** : Légèrement au-dessus du hasard, mais pas assez pour être prédictif

### Causes probables

**CAS 2 : Alphas reviennent mais direction stagne**
- "Other" (61% des événements) écrase encore tout
- Contributions des alphas majeurs s'annulent
- Besoin de splitter "Other" ou exclusion temporaire du training

---

## 💡 RECOMMANDATION

**Prochaine action** : Splitter "Other" ou exclusion temporaire
1. Identifier les sous-catégories de "Other" (Bills, EIA, Secondary)
2. Créer des familles séparées ou exclure du training
3. Recalculer alpha weights sans "Other" ou avec "Other" splité

**Alternative** : Optimiser θ avec les données actuelles
- θ optimal pourrait améliorer légèrement l'accuracy
- Mais le problème fondamental (76% neutres, corrélation faible) restera

