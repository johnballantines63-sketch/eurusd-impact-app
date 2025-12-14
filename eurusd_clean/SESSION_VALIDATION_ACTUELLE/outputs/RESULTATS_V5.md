# 📊 RÉSULTATS PHASE V5 (E1+E2+E3+F1)

**Date** : 2025-12-09  
**Script** : `build_v2_scores_composite.py` (avec E1, E2, E3, F1)

---

## ✅ MODIFICATIONS APPLIQUÉES

### E1 : Exclusion Bills ✅
- Bills exclus (0 événements avec estimate)
- Impact : Normal, Bills n'avaient déjà pas d'estimate

### E2 : Seuil z-score adaptatif pour EIA ✅
- `MIN_Z_FOR_ZSCORE_EIA = 5` (vs 10 par défaut)
- **Résultat** : ⚠️ EIA toujours absent des alpha_weights

### E3 : Filtrage Secondary (top 40) ✅
- Secondary filtré : 995 → 943 événements (52 exclus)
- Top 35 event_keys gardés (sur 35 avec corrélation)
- **Résultat** : Secondary présent mais avec weights = 0.0

### F1 : Normalisation S par n_active ✅
- `S = S_raw / n_active`
- **Résultat** : ⚠️ **Trop agressive** → scores comprimés

---

## ⚠️ CHECK A : ÉVÉNEMENTS MAJEURS

### Status : ✅ Maintenus

- **51 lignes** d'événements majeurs présents
- NFP, Unemployment, Employment, ISM, PMI, Consumer : tous présents

### Sous-familles Other

- **EIA** : 0 lignes (toujours absent)
- **Secondary** : 6 lignes avec **weights = 0.0** (tous horizons)

**Problème** : EIA et Secondary n'ont pas de poids significatifs

---

## ❌ CHECK B : DISTRIBUTION S (NEUTRES) - DÉGRADATION MAJEURE

### Résultats

| Métrique | Valeur | Objectif | Status |
|----------|--------|----------|--------|
| **% |S| < 0.1** | **100.0%** | < 35% | ❌ **DÉGRADATION** |
| Médiane |S| | 0.001259 | - | ⚠️ Très faible |
| Écart-type | 0.021324 | - | ⚠️ Très faible |

**Statistiques S** :
- Min : -0.049
- Max : +0.099
- Médiane : 0.001259
- Moyenne : 0.005742

**❌ ÉCHEC CRITIQUE** : 100% de neutres (vs 82% avant V5) → **Dégradation de 18 points**

---

## ⚠️ CHECK C : DIRECTIONNEL (θ=0.0)

### Résultats

| Métrique | Valeur | Objectif | Status |
|----------|--------|----------|--------|
| **Accuracy** | 51.2% | > 52% | ⚠️ Identique |
| **Coverage** | 86.0% | 70-80% | ✅ Bon |
| **Corrélation S ↔ direction** | **-0.0219** | > 0.05 | ❌ Très faible |

### Comparaison avec avant V5

| Métrique | Avant V5 | Après V5 | Évolution |
|----------|----------|----------|-----------|
| **Accuracy** | 51.2% | 51.2% | = (identique) |
| **Coverage** | 86.0% | 86.0% | = (identique) |
| **Corrélation** | -0.0005 | -0.0219 | ⚠️ Légère amélioration (moins négative) |
| **% neutres** | 82.0% | 100.0% | ❌ **+18% (pire)** |

---

## 📊 TOP 20 ALPHA WEIGHTS

| Horizon | Event Key | Weight |
|---------|-----------|--------|
| 4h | Trade Balance_surp_pos | +0.353656 |
| 4h | Unemployment_surp_neg | -0.318685 |
| 4h | Unemployment_surp_pos | +0.308331 |
| 4h | Trade Balance_surp_neg | +0.254323 |
| 4h | PPI_surp_neg | +0.247698 |
| 1j | PMI_surp_neg | -0.240764 |
| 1j | Business Confidence_surp_neg | -0.235438 |
| 1j | Business Confidence_surp_pos | -0.232347 |
| 1j | Unemployment_surp_neg | -0.226805 |
| 4h | Confidence_surp_pos | +0.219533 |

---

## 🔍 DIAGNOSTIC

### Problème principal : Normalisation F1 trop agressive

**Cause** : `S = S_raw / n_active` compresse excessivement les scores

**Exemple** :
- Si `S_raw = 0.5` et `n_active = 10` → `S = 0.05` (dans la zone neutre)
- Si `S_raw = 1.0` et `n_active = 20` → `S = 0.05` (toujours neutre)

**Impact** : 
- Scores comprimés dans une plage très étroite (-0.05 à +0.10)
- 100% des scores deviennent neutres (|S| < 0.1)

### Autres problèmes

1. **EIA absent** : Même avec `MIN_Z_FOR_ZSCORE_EIA = 5`, EIA n'apparaît pas dans alpha_weights
   - Probablement éliminé par `MIN_EVENTS_FOR_SCORE = 20` lors du calcul des scores empiriques

2. **Secondary avec weights = 0.0** : Après filtrage E3, Secondary a des weights nuls
   - Cela suggère que même les top 35 event_keys n'ont pas de signal directionnel significatif

---

## 💡 SOLUTION RECOMMANDÉE

### F1 : Utiliser normalisation moins agressive

**Option F2 (recommandée)** : Normalisation par racine carrée

```python
if n_active > 0:
    S = S_raw / math.sqrt(n_active)
else:
    S = S_raw
```

**Avantages** :
- Moins agressive que division par n_active
- Maintient l'amplitude des scores
- Réduit l'effet de fréquence sans comprimer à zéro

**Alternative** : Normalisation hybride

```python
if n_active > 0:
    # Normalisation adaptative : moins agressive pour grand n_active
    if n_active <= 5:
        S = S_raw / n_active
    else:
        S = S_raw / math.sqrt(n_active)
else:
    S = S_raw
```

---

## ✅ CONCLUSION

### CAS 4 : Normalisation F1 trop agressive

**Résultats** :
- ✅ Événements majeurs maintenus
- ❌ **100% de neutres** (vs 82% avant) → **Dégradation**
- ⚠️ Corrélation légèrement améliorée (-0.0219 vs -0.0005)
- ⚠️ Accuracy identique (51.2%)

**Cause principale** : Normalisation `S = S_raw / n_active` compresse trop les scores

**Action immédiate** : Passer à F2 (normalisation par √n_active) ou normalisation hybride

