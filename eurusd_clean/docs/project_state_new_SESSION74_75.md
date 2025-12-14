## 🔧 SESSIONS 74-75 : DIAGNOSTIC FORMULES V1 (25 octobre 2025)

### Objectif

**Mission Sessions 74-75 :** Valider formules Sessions 51-55 sur dataset réel  
**Résultat :** ❌ ÉCHEC COMPLET - Formules inadaptées (overfitting 11 sept)  
**Tokens :** 95,000 / 190,000 (50%)

---

### Session 74 : Test Dataset Non Filtré

**Dataset :** 22 mouvements Session 73 (tous pays, toutes surprises)

**Script créé :** `3_test_formulas.py` (570 lignes)
- Application formules V1 (calculate_adjusted_empirical_score + calculate_impact_d)
- Calcul écarts prédit vs réel
- Statistiques MAE / % erreur / Distribution
- Analyse 4 patterns problématiques

**Résultats :**

| Métrique | Résultat | Critère | Status |
|----------|----------|---------|--------|
| **MAE** | **86.3 pips** | < 30 pips | ❌ **4.3x pire** |
| **% Erreur** | **85.3%** | < 35% | ❌ **2.4x pire** |
| **Distribution** | **0% cas < 35%** | 70% cas < 30% | ❌ **0% réussite** |
| **Biais** | **100% sous-estimation** | - | ❌ Systématique |

**Diagnostic 3 problèmes :**
1. **41% events "Unknown"** (TR, JP, MX) → Score DEFAULT 10.0 → Erreur 98%
2. **45% surprises >100%** → Plafond formule 30% → Erreur 98%
3. **36% single events** → Formule calibrée clusters → Erreur 98%

---

### Session 75 : Dataset Qualité + Re-test

**Scanner V2 créé avec filtres stricts :**

| Critère | Valeur | Raison |
|---------|--------|--------|
| Pays | US, EU | 80% volume trading |
| Score DB | > 10 | Events connus (pas Unknown) |
| Surprise | < 100% | Cas normaux (pas extrêmes) |
| Nb events | ≥ 3 | Vrais clusters |
| Impact | ≥ 40 pips | Mouvements significatifs |

**Corrections appliquées :**
- ❌ `importance_n >= 3` → Colonne cassée (toujours = 1)
- ❌ `importance = 'High'` → Colonne n'existe pas
- ✅ `score_moyen > 10` → Solution finale

**Scripts créés :**
- `1_scanner_movements_V3_FINAL.py` (420 lignes) - Scanner V2 filtré
- `2_test_formulas_quality.py` (340 lignes) - Test qualité

**Dataset qualité : 7 mouvements**
- 7 jours distincts (100% diversité)
- Impact moyen : 86.0 pips
- Nb events moyen : 10.3 (vrais clusters)
- Score moyen : 53.0 (events connus)
- Surprise moyenne : 25.5% (réaliste)

**Résultats re-test :**

| Métrique | Session 74 | Session 75 | Amélioration |
|----------|------------|------------|--------------|
| **MAE** | 86.3 pips | **64.9 pips** | ✅ **-25%** |
| **% Erreur** | 85.3% | **74.8%** | ✅ **-12%** |
| **Cas < 35%** | 0/22 (0%) | 0/7 (0%) | ❌ **0%** |
| **Biais** | 100% sous-estim. | 100% sous-estim. | ❌ Systématique |

---

### Diagnostic Final

**Formules Sessions 51-55 = OVERFITTING sur 11 septembre 2025 :**

| Métrique | 11 Sept (Calibration) | Dataset Réel |
|----------|----------------------|--------------|
| **Impact** | **57 pips** | **86 pips (+51%)** ❌ |
| Nb events | 9 | 10.3 (similaire) ✅ |
| Score | 85.1 | 53-117 (variable) |
| Surprise | 33% | 0-60% (variable) |

**Problèmes formule D :**
```python
# Coefficient trop faible
impact_brut = -10.47 + 0.477 × score  # 0.477 inadapté

# Facteur correction trop conservateur
impact_final = |impact_brut| × 0.758  # 0.758 inadapté

# Plafond surprise trop bas
if surprise >= 30%: facteur = 1.9  # Réalité : 0-60%
```

**Conclusion :**
- Formules calibrées sur **1 seul cas**
- **0% généralisation** sur dataset réel
- **ML nécessaire** avec dataset 30-50 mouvements

---

### Découverte Critique : event_title NULL

**Problème :** 85% events affichés "None" dans dataset qualité

**Exemple :**
```
US:None | US:None | US:None | US:Interest Rate...
```

**Impact :**
- Events non identifiables
- Analyse patterns impossible
- Investigation nécessaire Session 76

---

### Fichiers Sessions 74-75

**Scripts créés :**
```
fx_impact_app/scripts/session73/
└── 3_test_formulas.py (570 lignes) ✅ Session 74

fx_impact_app/scripts/session75/
├── 1_scanner_movements_V3_FINAL.py (420 lignes) ✅ FINAL
└── 2_test_formulas_quality.py (340 lignes) ✅ FINAL
```

**Outputs créés :**
```
fx_impact_app/scripts/session73/
└── results_test_formulas_session73.csv (22 lignes)

fx_impact_app/scripts/session75/
├── dataset_session75_filtered.csv (7 lignes) ⭐ Qualité
└── results_test_formulas_session75.csv (7 lignes)
```

**Documentation créée :**
```
eurusd_clean/docs/
├── SESSION74_SESSION75_RAPPORT_COMPLET.md ✅
└── MESSAGE_SESSION75_SESSION76.md ✅
```

---

### Prochaines Étapes (Session 76)

**Mission :** Formules ML V2.0 robustes

**Priorité 1 : Dataset Élargi (30-50 mouvements)**

Assouplir critères Session 75 :
- Score > 10 → **Score > 5**
- Surprise < 100% → **Surprise < 200%**
- Nb events ≥ 3 → **Nb events ≥ 2**
- Impact ≥ 40 → **Impact ≥ 30 pips**
- Top 30 → **Top 50 par année**
- 2024-2025 → **2023-2025**

**Priorité 2 : Régression ML Multi-Variables**

```python
X = [score_ajuste, nb_events, surprise_max, coherence_famille]
y = impact_reel_pips

model = LinearRegression()
model.fit(X, y)

# Validation croisée 5-fold
scores = cross_val_score(model, X, y, cv=5)
```

**Critères succès :**
- Dataset : 30-50 mouvements ✅
- R² > 0.7 (bon) ou > 0.8 (excellent) ✅
- MAE cross-val < 20 pips ✅
- Amélioration vs V1 : > 50% (MAE < 32 pips) ✅

**Budget estimé :** 70-80k tokens (95k disponibles)

---

**Progression :** 93% → 94% (diagnostic complet formules)

---
