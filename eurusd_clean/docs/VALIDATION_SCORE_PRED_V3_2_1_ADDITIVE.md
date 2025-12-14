# VALIDATION SCORE PRÉDICTIF V3.2.1 ADDITIVE — BASELINE STABLE

**Version :** V3.2.1 (Additive)  
**Date validation :** 2025-12-12  
**Statut :** ✅ BASELINE FIGÉE — PRODUCTION

---

## 1. OBJECTIF

Valider **V3.2.1 Additive** comme baseline de production pour la prédiction ex-ante du risque de volatilité EURUSD, en ajoutant une **densité informationnelle macro US** au modèle V3.1.

---

## 2. DÉCISIONS FIGÉES

### 2.1 Héritage

- Score news ex-ante (V1/V2.1)
- Release group + TOP2
- Régime de volatilité ex-ante (lag 1 jour)
- Modèle Ridge (alpha = 0.1)

**Référence :** `docs/VALIDATION_SCORE_PRED_V3_1_BASELINE.md`

---

### 2.2 Nouvelle Feature (V3.2.1)

**Feature :**
```text
n_us_events_day = COUNT(events WHERE country = 'US' AND DATE(ts_local) = date)
```

**Utilisation :**
```text
log1p(n_us_events_day)
```

**Nature :** additive (pas d'interaction)

**Garantie no-leakage :**
- Donnée strictement calendrier
- Calculée à partir de `events_with_ts_local_v1`
- Aucune dépendance à la volatilité future

---

## 3. MODÈLE

**Type :** Ridge Regression

**Target :** `log1p(daily_volatility_pips)`

**Nombre de features :** 18

**Vue dataset :** `daily_pred_score_v3_2_dataset_v1`

**Featureset retenu :** **V3.2.1 Additive** (V3.1 S3_full + log1p(n_us_events_day))

**Modèle :** Ridge regression avec alpha=0.1 (hérité V3.1).

**Target :** `log1p(daily_volatility_pips_v1)`

---

## 4. VALIDATION WALK-FORWARD

### 4.1 Résultats Globaux

| Modèle | Spearman moyen |
|--------|----------------|
| V3.1 baseline | 0.3158 |
| **V3.2.1 additive** | **0.3581** |

**Delta :** +0.0423

### 4.2 Résultats par Cutoff

| Cutoff | V3.1 | V3.2.1 | Delta |
|--------|------|--------|-------|
| 2023-01-01 | 0.2186 | 0.2999 | +0.0813 |
| 2023-07-01 | 0.3601 | 0.3802 | +0.0201 |
| 2024-01-01 | 0.3400 | 0.3710 | +0.0310 |
| 2024-07-01 | 0.3443 | 0.3814 | +0.0371 |

---

## 5. COMPARAISON AVEC INTERACTIONS

| Variante | Spearman | Statut |
|----------|----------|--------|
| **V3.2.1 additive** | **0.3581** | ✅ **Retenu** |
| V3.2.2 interactions | 0.3420 | ❌ Non retenu |

**Conclusion :** L'effet de densité est additif, pas conditionnel.

**Référence :** `docs/ANALYSE_V3_2_2_INTERACTIONS.md`

---

## 6. GUARDRAILS

V3.2.1 Additive est validé comme baseline de production.

**Points clés :**
- ✅ Signal robuste
- ✅ Gain significatif (+0.0423)
- ✅ Interprétable
- ✅ Ex-ante strict
- ✅ Guardrails complets
- ✅ Objectif >0.35 atteint (0.3581)

---

## 8. NEXT STEPS

**Script :** `scripts/check_v3_2_guardrail.py`

**Vérifications :**
- COUNT(*) cohérent V3.1 / V3.2
- Couverture dates complète
- 0 NULL sur colonnes critiques
- `n_us_events_day >= 0`
- Cohérence avec `events_with_ts_local_v1`
- Ex-ante structurel validé

**Résultat :** ✅ PASSED

**Référence SQL :** `docs/GUARDRAIL_V3_2_SQL_REFERENCE.md`

---

## 7. CONCLUSION

- **V3.3 :** Densité multi-pays
- **V3.4 :** Interactions ciblées si justifiées
- **V4 :** Modèles non-linéaires si nécessaire

---

**Document créé le :** 2025-12-12  
**Dernière mise à jour :** 2025-12-12  
**Version :** V3.2.1 (BASELINE FIGÉE — PRODUCTION)

