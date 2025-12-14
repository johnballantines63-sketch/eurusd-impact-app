# PRODUCTION V3.2.1 — Guide d'Utilisation

**Version :** V3.2.1 (Additive)  
**Date :** 2025-12-12  
**Statut :** Production-ready

---

## 1. OVERVIEW

Le système V3.2.1 est un modèle de prédiction ex-ante du risque de volatilité EURUSD basé sur :
- Score news (V2.1)
- Features calendrier (8)
- Features régime de volatilité ex-ante (8)
- Densité informationnelle US (1)

**Modèle :** Ridge Regression (alpha=0.1)  
**Target :** `log1p(daily_volatility_pips)`  
**Features :** 18

---

## 2. PIPELINE PRODUCTION

### 2.1 Entraînement (Génération Artefact)

**Script :** `scripts/train_v3_2_1_additive_model_v1.py`

**Usage :**
```bash
# Entraîner sur données jusqu'à 2024-07-01
python3 scripts/train_v3_2_1_additive_model_v1.py --cutoff 2024-07-01

# Entraîner avec alpha personnalisé
python3 scripts/train_v3_2_1_additive_model_v1.py --cutoff 2024-07-01 --alpha 0.1

# Spécifier un chemin de sortie
python3 scripts/train_v3_2_1_additive_model_v1.py --cutoff 2024-07-01 --output models/my_model.json
```

**Output :** Artefact JSON dans `models/v3_2_1_additive_ridge_alpha0_1.json`

**Structure artefact :**
```json
{
  "version": "V3.2.1",
  "model_type": "ridge",
  "alpha": 0.1,
  "intercept": 3.124734,
  "coef": [0.288712, ...],
  "features": ["log1p_score_v2_1", "dow", ...],
  "training_cutoff": "2024-07-01",
  "n_train": 370,
  "date_range": {
    "min": "2022-09-21",
    "max": "2024-07-01"
  }
}
```

### 2.2 Application (Prédiction)

**Script :** `scripts/apply_v3_2_1_additive_model_v1.py`

**Usage :**
```bash
# Appliquer sur toutes les dates disponibles
python3 scripts/apply_v3_2_1_additive_model_v1.py

# Appliquer sur une plage de dates
python3 scripts/apply_v3_2_1_additive_model_v1.py --from 2024-01-01 --to 2024-12-31

# Test avec limite (debug)
python3 scripts/apply_v3_2_1_additive_model_v1.py --limit 10

# Dry-run (pas d'écriture DB)
python3 scripts/apply_v3_2_1_additive_model_v1.py --dry-run
```

**Input :** Vue DuckDB `daily_pred_score_v3_2_dataset_v1`  
**Output :** Table DuckDB `daily_risk_signal_v3_2_1`

**Colonnes output :**
- `date` : Date de prédiction
- `pred_log_vol` : Prédiction log(vol+1)
- `pred_vol_pips` : Prédiction volatilité (pips)
- `model_version` : "V3.2.1"

---

## 3. VÉRIFICATIONS PRÉ-APPLICATION

### 3.1 Guardrails

**Vérifier l'intégrité des données :**
```bash
python3 scripts/check_v3_2_guardrail.py
```

**Résultat attendu :** ✅ PASSED

### 3.2 Vérification Artefact

**Vérifier que l'artefact existe et est valide :**
```bash
python3 -c "
import json
from pathlib import Path
artifact = json.load(open('models/v3_2_1_additive_ridge_alpha0_1.json'))
assert artifact['version'] == 'V3.2.1'
assert artifact['model_type'] == 'ridge'
assert len(artifact['coef']) == 18
print('✅ Artefact valide')
"
```

---

## 4. WORKFLOW RECOMMANDÉ

### 4.1 Initialisation (Première Utilisation)

1. **Vérifier les vues nécessaires :**
   ```bash
   python3 scripts/check_v3_2_guardrail.py
   ```

2. **Entraîner le modèle :**
   ```bash
   python3 scripts/train_v3_2_1_additive_model_v1.py --cutoff 2024-07-01
   ```

3. **Tester l'application (dry-run) :**
   ```bash
   python3 scripts/apply_v3_2_1_additive_model_v1.py --dry-run --limit 10
   ```

4. **Appliquer sur toutes les dates :**
   ```bash
   python3 scripts/apply_v3_2_1_additive_model_v1.py
   ```

### 4.2 Mise à Jour Périodique (Ré-entraînement)

**Fréquence recommandée :** Mensuelle ou trimestrielle

1. **Choisir un nouveau cutoff :**
   ```bash
   # Exemple : entraîner sur données jusqu'à fin décembre 2024
   python3 scripts/train_v3_2_1_additive_model_v1.py --cutoff 2024-12-31
   ```

2. **Valider le nouveau modèle :**
   ```bash
   # Comparer avec modèle précédent (walk-forward)
   python3 scripts/analyze_v3_2_density_walkforward_v1.py --cutoffs "2024-07-01,2024-10-01,2024-12-31"
   ```

3. **Appliquer le nouveau modèle :**
   ```bash
   python3 scripts/apply_v3_2_1_additive_model_v1.py
   ```

### 4.3 Application Quotidienne

**Pour prédire le risque du jour suivant :**

```bash
# Prédire pour demain (date du jour + 1)
python3 scripts/apply_v3_2_1_additive_model_v1.py --from $(date -v+1d +%Y-%m-%d) --to $(date -v+1d +%Y-%m-%d)
```

**Ou pour une date spécifique :**
```bash
python3 scripts/apply_v3_2_1_additive_model_v1.py --from 2024-12-13 --to 2024-12-13
```

---

## 5. REQUÊTES SQL UTILES

### 5.1 Consulter les Prédictions

```sql
-- Dernières prédictions
SELECT
    date,
    pred_vol_pips,
    pred_log_vol,
    model_version
FROM daily_risk_signal_v3_2_1
ORDER BY date DESC
LIMIT 10;
```

### 5.2 Comparer Prédiction vs Réalité

```sql
-- Prédiction vs volatilité observée
SELECT
    s.date,
    s.pred_vol_pips AS pred,
    v.daily_volatility_pips_v1 AS actual,
    ABS(s.pred_vol_pips - v.daily_volatility_pips_v1) AS error
FROM daily_risk_signal_v3_2_1 s
JOIN daily_eurusd_volatility_v1 v ON s.date = v.date
ORDER BY s.date DESC
LIMIT 20;
```

### 5.3 Top Risques Prédits

```sql
-- Top 20 journées à risque (prédiction)
SELECT
    date,
    pred_vol_pips,
    pred_log_vol
FROM daily_risk_signal_v3_2_1
ORDER BY pred_vol_pips DESC
LIMIT 20;
```

---

## 6. DÉPANNAGE

### 6.1 Erreur "Model artifact not found"

**Solution :** Entraîner le modèle d'abord :
```bash
python3 scripts/train_v3_2_1_additive_model_v1.py --cutoff 2024-07-01
```

### 6.2 Erreur "Missing columns in input view"

**Solution :** Vérifier que toutes les vues V3.2 sont créées :
```bash
python3 scripts/create_daily_pred_score_v3_2_dataset_v1_view.py
```

### 6.3 Erreur "Invariant check failed"

**Solution :** Exécuter le guardrail pour diagnostiquer :
```bash
python3 scripts/check_v3_2_guardrail.py
```

### 6.4 Lock DuckDB

**Solution :** Attendre quelques secondes et réessayer. Le script gère automatiquement les retries.

---

## 7. PERFORMANCE ATTENDUE

**Métriques walk-forward (cutoff 2024-07-01) :**
- Spearman : 0.3581 (objectif >0.35 ✅)
- Gain vs V3.1 : +0.0423

**Stabilité temporelle :**
- Min : 0.2999
- Max : 0.3814
- Écart : ~0.08 (excellent)

---

## 8. RÉFÉRENCES

- **Validation :** `docs/VALIDATION_SCORE_PRED_V3_2_1_ADDITIVE.md`
- **Guardrails SQL :** `docs/GUARDRAIL_V3_2_SQL_REFERENCE.md`
- **Analyse interactions :** `docs/ANALYSE_V3_2_2_INTERACTIONS.md`

---

**Document créé le :** 2025-12-12  
**Version :** V3.2.1 (Production)

