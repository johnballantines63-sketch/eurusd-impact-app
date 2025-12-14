# 📊 RÉSULTATS PHASE D (D1 + D2)

**Date** : 2025-12-09  
**Script** : `build_v2_scores_composite.py` (avec D1 + D2)

---

## ✅ CHECK A : ÉVÉNEMENTS MAJEURS

### Status : ✅ Maintenus

- **51 lignes** d'événements majeurs présents dans `alpha_weights.csv`
- NFP, Unemployment, Employment, ISM, PMI, Consumer : tous présents avec weights non-nuls

### Sous-familles Other (D2)

**⚠️ Problème détecté** : Seulement **Secondary** apparaît dans les alpha_weights

- `Secondary_surp_neg`: weight=-0.012046
- `Secondary_surp_pos`: weight=-0.003210
- **Bills et EIA absents** des alpha_weights

**Cause probable** : Bills et EIA n'ont pas assez d'occurrences avec `surprise_z` calculé (filtrés avant le split car estimate NaN ou < 10 occurrences pour z-score)

---

## ⚠️ CHECK B : DISTRIBUTION S (NEUTRES)

### Résultats

| Métrique | Valeur | Objectif | Status |
|----------|--------|----------|--------|
| **% |S| < 0.1** | **82.0%** | < 35% | ❌ **DÉGRADATION** |
| Médiane |S| | ~0.006 | - | ⚠️ |

**❌ ÉCHEC** : 82% de neutres (vs 76% avant D1/D2) → **Dégradation de 6 points**

---

## ⚠️ CHECK C : DIRECTIONNEL (θ=0.0)

### Résultats

| Métrique | Valeur | Objectif | Status |
|----------|--------|----------|--------|
| **Accuracy** | 51.2% | > 52% | ⚠️ Légèrement en dessous |
| **Coverage** | 86.0% | 70-80% | ✅ Bon |
| **Corrélation S ↔ direction** | **-0.0005** | > 0.05 | ❌ Très faible |

### Comparaison avec avant D1/D2

| Métrique | Avant D1/D2 | Après D1/D2 | Évolution |
|----------|-------------|-------------|-----------|
| **Accuracy** | 51.2% | 51.2% | = (identique) |
| **Coverage** | 86.0% | 86.0% | = (identique) |
| **Corrélation** | 0.0072 | -0.0005 | ⚠️ Légère dégradation |
| **% neutres** | 76.0% | 82.0% | ❌ **+6% (pire)** |

---

## 📊 TOP 20 ALPHA WEIGHTS

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

## 🔍 DIAGNOSTIC

### D1 : Exclusion temporaire

**Résultat** : 899 événements exclus (sur 1,183,432)

**Problème** : C'est très peu ! On s'attendait à exclure ~60% (tous les Other/Bills/EIA/Secondary). Cela suggère que :
- La plupart des événements Other sont déjà filtrés avant (estimate NaN ou pas assez d'occurrences)
- Ou le filtrage par `event_key.startswith()` ne capture pas tous les cas

### D2 : Split Other

**Résultat** : Split détecté dans le log (995 événements Secondary), mais **Bills et EIA absents** des alpha_weights

**Cause probable** :
- Bills et EIA n'ont pas assez d'événements avec `surprise_z` calculé (< 10 occurrences ou estimate NaN)
- Le split fonctionne, mais ces sous-familles sont éliminées lors du calcul des scores empiriques (MIN_EVENTS_FOR_SCORE=20)

---

## 💡 CONCLUSION

### CAS 3 : D1/D2 n'ont pas amélioré les résultats

**Observations** :
- ✅ Les événements majeurs restent présents
- ❌ **82% de neutres** (vs 76% avant) → **Dégradation**
- ❌ Corrélation toujours très faible (-0.0005 vs 0.0072 avant)
- ⚠️ Accuracy identique (51.2%)

**Causes probables** :
1. **Bills et EIA éliminés** : Pas assez d'occurrences pour passer MIN_EVENTS_FOR_SCORE=20
2. **D1 trop faible** : Seulement 899 exclus (0.08%) au lieu des milliers attendus
3. **Secondary domine encore** : Avec weight très faible (-0.012/-0.003), mais peut-être présent dans beaucoup de timestamps

### Prochaines étapes recommandées

1. **Vérifier pourquoi Bills/EIA sont absents** :
   - Combien d'occurrences avec `surprise_z` calculé ?
   - Sont-ils éliminés par MIN_EVENTS_FOR_SCORE=20 ?

2. **Exclure Secondary aussi** (pas seulement Bills/EIA) :
   - Secondary a des weights très faibles et peut encore noyer le signal
   - Tester l'exclusion complète de toutes les sous-familles Other

3. **Alternative** : Augmenter MIN_EVENTS_FOR_SCORE temporairement pour voir si ça améliore les résultats (contre-intuitif mais peut filtrer le bruit)

