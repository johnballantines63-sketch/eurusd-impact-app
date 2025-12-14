# 📬 MESSAGE SESSION 75 → SESSION 76

**Date :** 25 octobre 2025  
**Session actuelle :** 75 ✅ DIAGNOSTIC COMPLET  
**Prochaine session :** 76  
**Statut global :** Formules V1 inadaptées, ML nécessaire

---

## 🎯 RÉSUMÉ SESSIONS 74-75

### Mission vs Résultat

**Objectif initial :** Valider formules Sessions 51-55 sur dataset réel  
**Résultat :** ❌ ÉCHEC COMPLET - Formules inadaptées (overfitting 11 sept)  
**Tokens utilisés :** 95,000 / 190,000 (50%)

### Session 74 : Test Dataset Non Filtré

**Dataset :** 22 mouvements Session 73 (tous pays, toutes surprises)

**Résultats :**
```
MAE : 86.3 pips (critère : <30 pips)
% Erreur : 85.3% (critère : <35%)
Distribution : 0% cas < 35% (critère : 70%)
Biais : 100% sous-estimation
```

**Diagnostic :**
- 41% events "Unknown" (score DEFAULT)
- 45% surprises >100% (plafond formule 30%)
- 36% single events (formule calibrée clusters)

---

### Session 75 : Dataset Qualité + Re-test

**Scanner V2 créé avec filtres stricts :**
- Pays : US, EU uniquement
- Score DB : > 10 (events connus)
- Surprise : < 100% (cas normaux)
- Nb events : ≥ 3 (vrais clusters)
- Impact : ≥ 40 pips

**Dataset qualité : 7 mouvements**
- 7 jours distincts (100% diversité)
- Impact moyen : 86.0 pips
- Nb events moyen : 10.3
- Score moyen : 53.0
- Surprise moyenne : 25.5%

**Résultats re-test :**
```
MAE : 64.9 pips (-25% vs Session 74) ✅
% Erreur : 74.8% (-12% vs Session 74) ✅
Distribution : 0% cas < 35% ❌
Biais : 100% sous-estimation ❌
```

**Conclusion :**
- Filtrage améliore performances (+25%)
- MAIS toujours 100% échec
- Problème = Formules (pas dataset)

---

### Top 3 Découvertes Critiques

**1. Formules V1 = Overfitting 11 septembre 2025**

| Métrique | 11 Sept (Calibration) | Dataset Réel |
|----------|----------------------|--------------|
| Impact | 57 pips | **86 pips (+51%)** |
| Nb events | 9 | 10.3 (similaire) |
| Score | 85.1 | 53-117 (variable) |
| Surprise | 33% | 0-60% (variable) |

**Conclusion :** Formule calibrée sur 1 cas = 0% généralisation

---

**2. DB Problématique : event_title = NULL (85% cas)**

**Exemple dataset qualité :**
```
US:None | US:None | US:None | US:Interest Rate...
```

**Impact :**
- Events non identifiables
- Analyse patterns impossible
- Investigation nécessaire Session 76

---

**3. Sous-Estimation Systématique**

**Pattern 100% des cas (29/29) :**
- Impact prédit : 1-34 pips
- Impact réel : 58-176 pips
- Écart moyen : **+60 pips**

**Cause :** Coefficient formule D trop faible (0.477)

---

## 📁 FICHIERS DISPONIBLES SESSION 76

### Datasets Créés

```
fx_impact_app/scripts/session73/
├── dataset_session73.csv (40 lignes, 18 colonnes) - Non filtré
└── results_test_formulas_session73.csv (22 lignes) - Résultats S74

fx_impact_app/scripts/session75/
├── dataset_session75_filtered.csv (7 lignes, 18 colonnes) - Qualité ⭐
└── results_test_formulas_session75.csv (7 lignes) - Résultats S75
```

**Dataset recommandé pour Session 76 :**
- `dataset_session75_filtered.csv` : 7 mouvements qualité
- Ou créer dataset élargi 30-50 mouvements (Option A)

---

### Scripts Disponibles

```
fx_impact_app/scripts/session73/
├── 1_scanner_movements_DEDUP.py ✅ Scanner Session 73
├── 2_cross_with_events_FIXED.py ✅ Croisement events
└── 3_test_formulas.py ✅ Test formules

fx_impact_app/scripts/session75/
├── 1_scanner_movements_V3_FINAL.py ✅ Scanner V2 filtré
└── 2_test_formulas_quality.py ✅ Test qualité
```

---

### Formules Validées (Sessions 51-55)

**Module :** `fx_impact_app/src/formulas_validated.py`

**Statut :** ❌ INADAPTÉES (overfitting 11 sept)

**Fonctions :**
```python
from src.formulas_validated import (
    calculate_adjusted_empirical_score,  # Ajustement surprise (plafond 30%)
    calculate_impact_d                   # Impact net (coef 0.477)
)
```

**Problèmes identifiés :**
- Coefficient 0.477 trop faible
- Plafond surprise 30% inadapté (réalité 0-60%)
- Facteur correction 0.758 trop conservateur

---

## 🎯 MISSION SESSION 76

### Priorité 1 : Dataset Élargi + ML (Recommandé) ⭐⭐⭐

**Objectif :** Créer dataset 30-50 mouvements pour ML robuste

**Approche :**

**Étape 1 : Scanner V3 Étendu** (~20k tokens)

Assouplir critères Session 75 :
```python
# Session 75 (strict)          → Session 76 (élargi)
COUNTRIES = ['US', 'EU']       → ['US', 'EU'] (identique)
SCORE_MIN = 10.0               → 5.0 (events connus)
SURPRISE_MAX = 100.0           → 200.0 (moins strict)
NB_EVENTS_MIN = 3              → 2 (clusters + single HIGH)
IMPACT_MIN = 40                → 30 pips
TOP_N_PER_YEAR = 30            → 50
YEARS = [2024, 2025]           → [2023, 2024, 2025]
```

**Résultat attendu :** 30-50 mouvements qualité

---

**Étape 2 : Régression ML Multi-Variables** (~30k tokens)

```python
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import cross_val_score
import numpy as np

# Variables prédicteurs
X = df[['score_ajuste', 'nb_events', 'surprise_max', 'coherence_famille']]

# Target
y = df['impact_reel_pips']

# Régression
model = LinearRegression()
model.fit(X, y)

# Métriques
r2 = model.score(X, y)
print(f"R² : {r2:.3f}")

# Validation croisée (5-fold)
scores = cross_val_score(model, X, y, cv=5, scoring='neg_mean_absolute_error')
mae_cv = -scores.mean()
print(f"MAE cross-val : {mae_cv:.1f} pips")

# Coefficients
print(f"Intercept : {model.intercept_:.2f}")
for i, col in enumerate(X.columns):
    print(f"{col} : {model.coef_[i]:.4f}")
```

**Métriques succès :**
- R² > 0.7 (bon) ou > 0.8 (excellent)
- MAE cross-val < 20 pips (excellent)
- Stabilité validation croisée (std < 5 pips)

---

**Étape 3 : Créer formulas_validated_v2.py** (~10k tokens)

```python
def calculate_impact_ml_v2(
    score_ajuste: float,
    nb_events: int,
    surprise_max: float,
    coherence_famille: float = 1.0
) -> float:
    """
    Formule ML V2.0 - Régression linéaire multi-variables
    
    Calibrée sur 30-50 mouvements (2023-2025)
    Validation croisée : MAE < 20 pips
    
    Args:
        score_ajuste: Score empirique ajusté par surprise
        nb_events: Nombre événements cluster
        surprise_max: Surprise maximum (%)
        coherence_famille: Ratio famille dominante
        
    Returns:
        Impact prédit (pips, valeur absolue)
    """
    # Coefficients régression ML
    intercept = X.XX  # À déterminer
    coef_score = X.XXXX
    coef_events = X.XXXX
    coef_surprise = X.XXXX
    coef_coherence = X.XXXX
    
    impact = (
        intercept +
        coef_score * score_ajuste +
        coef_events * nb_events +
        coef_surprise * surprise_max +
        coef_coherence * coherence_famille
    )
    
    return abs(impact)
```

---

**Étape 4 : Validation** (~10k tokens)

- Tester sur 7 mouvements Session 75
- Comparer V1 vs V2 (MAE, R²)
- Export results_ml_v2_session76.csv

**Budget total :** 70-80k tokens (suffisant avec 95k restants)

---

### Priorité 2 : Investiguer event_title NULL (Bloquant) ⭐⭐

**Problème :** 85% events affichés "None" dans dataset

**Investigation :**

**Script diagnostic** (~15k tokens) :
```python
import duckdb

conn = duckdb.connect('warehouse.duckdb', read_only=True)

# Cas 1 : 2024-12-18 17:59 (FOMC Minutes)
query = """
SELECT 
    event_key,
    event_title,
    country,
    ts_utc
FROM events
WHERE ts_utc BETWEEN '2024-12-18 17:49:00' AND '2024-12-18 18:09:00'
  AND country = 'US'
ORDER BY ts_utc
"""

df = conn.execute(query).fetchdf()
print(df)

# Vérifier si event_title NULL ou autre
print(f"\nNull count: {df['event_title'].isna().sum()}")
```

**Si event_title = NULL :**
- Utiliser event_key comme fallback
- Créer mapping event_key → event_name manuel

**Budget :** 20-30k tokens

---

### Priorité 3 : ML Simple (7 cas) ⭐

**Si temps/tokens limités :**

Régression sur 7 cas qualité Session 75 uniquement.

**Avantages :** Rapide (30k tokens)  
**Inconvénients :** Risque overfitting

**Recommandation :** Préférer Priorité 1 (dataset élargi)

---

## ⚠️ POINTS D'ATTENTION SESSION 76

### Attention #1 : Taille Dataset Minimale

**Pour ML robuste :**
- Minimum : 20-30 observations
- Idéal : 40-50 observations
- Variables prédicteurs : 4 max (ratio 10:1)

**Dataset Session 75 :**
- 7 observations ❌ INSUFFISANT
- Besoin dataset élargi

**Solution :** Scanner V3 étendu (Priorité 1, Étape 1)

---

### Attention #2 : Validation Croisée Obligatoire

**Avec dataset 30-50 :**
- ✅ Utiliser cross-validation 5-fold
- ✅ Vérifier stabilité MAE (std < 5 pips)
- ❌ NE PAS valider sur training set uniquement

**Exemple :**
```python
from sklearn.model_selection import cross_val_score

scores = cross_val_score(model, X, y, cv=5, scoring='neg_mean_absolute_error')
mae_mean = -scores.mean()
mae_std = scores.std()

print(f"MAE : {mae_mean:.1f} ± {mae_std:.1f} pips")

# Critère : std < 5 pips (stable)
if mae_std < 5:
    print("✅ Modèle stable")
```

---

### Attention #3 : event_title NULL

**Impact si non résolu :**
- Analyse patterns impossible
- Events non identifiables
- Documentation limitée

**Recommandation :**
- Investigation Priorité 2 AVANT ML
- Ou accepter limitation + documenter

---

## 🎓 LEÇONS SESSIONS 74-75 POUR SESSION 76

### Ce qui a bien fonctionné ✅

1. **Filtrage dataset améliore performances**
   - Session 74 (non filtré) : MAE 86.3 pips
   - Session 75 (qualité) : MAE 64.9 pips
   - Amélioration : -25%

2. **Diagnostic méthodique révèle problème fondamental**
   - 2 datasets testés (22 + 7 mouvements)
   - Pattern 100% sous-estimation
   - Conclusion : Formules V1 inadaptées (pas dataset)

3. **Scripts réutilisables créés**
   - Scanner V2 filtré (420 lignes)
   - Test formules qualité (340 lignes)
   - Prêts pour Session 76

### À appliquer Session 76 ✅

1. **Dataset 30-50 minimum pour ML**
   - 7 cas insuffisants (risque overfitting)
   - Scanner V3 étendu nécessaire

2. **Validation croisée obligatoire**
   - Ne pas répéter erreur Sessions 51-55
   - Cross-validation 5-fold
   - Vérifier stabilité

3. **Investiguer event_title NULL**
   - Bloque analyse patterns
   - Script diagnostic simple
   - 15-20k tokens

---

## 📞 MESSAGE TYPE SESSION 76

```
Bonjour Claude,

Nouvelle session 76 - FORMULES ML V2.0

AVANT TOUT :
1. Lis MANDATORY_SESSION_RULES.md (v2.1)
2. Lis project_state_new.md
3. Lis SESSION74_SESSION75_RAPPORT_COMPLET.md
4. Lis MESSAGE_SESSION75_SESSION76.md (ce fichier)

Indique régulièrement les tokens utilisés

CONTEXTE SESSIONS 74-75 :
- Mission : Valider formules V1 (Sessions 51-55)
- Session 74 : ❌ MAE 86.3 pips (22 mouvements)
- Session 75 : ❌ MAE 64.9 pips (7 mouvements qualité)
- Diagnostic : Formules V1 = overfitting 11 sept
- Conclusion : ML nécessaire avec dataset élargi

MISSION SESSION 76 :
Priorité 1 : Dataset Élargi + ML Robuste

Étape 1 : Scanner V3 étendu
- Assouplir critères Session 75
- Score > 5 (vs 10), Surprise < 200% (vs 100%)
- Nb events ≥ 2 (vs 3), Impact ≥ 30 (vs 40)
- Top 50 par année, 2023-2025
- Résultat attendu : 30-50 mouvements

Étape 2 : Régression ML multi-variables
- Variables : score_ajuste, nb_events, surprise_max, coherence_famille
- Target : impact_reel_pips
- Validation croisée 5-fold
- Métriques : R² > 0.7, MAE < 20 pips

Étape 3 : Créer formulas_validated_v2.py
- Fonction calculate_impact_ml_v2()
- Coefficients régression ML

Étape 4 : Validation
- Tester sur 7 mouvements Session 75
- Comparer V1 vs V2

SCRIPTS DISPONIBLES :
- fx_impact_app/scripts/session75/1_scanner_movements_V3_FINAL.py
  (base pour Scanner V3 étendu)
- fx_impact_app/scripts/session75/2_test_formulas_quality.py
  (base pour validation)

DATASETS DISPONIBLES :
- dataset_session75_filtered.csv (7 mouvements qualité)
- results_test_formulas_session75.csv (résultats V1)

CRITÈRES SUCCÈS :
- Dataset : 30-50 mouvements
- R² > 0.7 (bon) ou > 0.8 (excellent)
- MAE cross-val < 20 pips
- Amélioration vs V1 : > 50% (MAE < 32 pips)

POINTS D'ATTENTION :
- Validation croisée obligatoire (éviter overfitting)
- event_title NULL (85% cas) - investiguer si temps
- Taille dataset minimum : 20-30 observations

BUDGET TOKENS : 95k disponibles (suffisant)

GO après validation compréhension !
```

---

## ✅ CHECKLIST SESSION 76

### Phase 1 : Lecture (20k tokens)
- [ ] MANDATORY_SESSION_RULES.md (v2.1) lu
- [ ] project_state_new.md lu
- [ ] SESSION74_SESSION75_RAPPORT_COMPLET.md lu
- [ ] MESSAGE_SESSION75_SESSION76.md lu (ce fichier)
- [ ] Validation mission avec utilisateur

### Phase 2 : Scanner V3 Étendu (20k tokens)
- [ ] Script scanner V3 créé (critères assouplis)
- [ ] Exécution scanner
- [ ] Dataset 30-50 mouvements obtenu
- [ ] Validation qualité dataset

### Phase 3 : Régression ML (30k tokens)
- [ ] Script ML créé (LinearRegression)
- [ ] Variables prédicteurs sélectionnées
- [ ] Régression entraînée
- [ ] Validation croisée 5-fold
- [ ] Métriques R² / MAE calculées
- [ ] Coefficients extraits

### Phase 4 : Formulas V2 (10k tokens)
- [ ] Module formulas_validated_v2.py créé
- [ ] Fonction calculate_impact_ml_v2()
- [ ] Documentation complète
- [ ] Tests unitaires

### Phase 5 : Validation (10k tokens)
- [ ] Test sur 7 mouvements Session 75
- [ ] Comparaison V1 vs V2
- [ ] Export results CSV

### Phase 6 : Documentation (15k tokens)
- [ ] SESSION76_RAPPORT_COMPLET.md
- [ ] MESSAGE_SESSION76_SESSION77.md
- [ ] project_state_new.md mis à jour

---

## 🎯 OBJECTIF FINAL

**Sessions 74-75 :** ❌ Formules V1 inadaptées (overfitting)  
**Session 76 :** ✅ Formules ML V2.0 robustes  
**Session 77+ :** Intégration production Planificateur

**Vision :** ML multi-variables validé sur 30-50 cas → Généralisation robuste

---

*Prêt pour Session 76 - Formules ML V2.0 !* 🚀

**SESSION 75 → SESSION 76**  
**Date :** 25 octobre 2025  
**Tokens Sessions 74-75 :** 95,000 / 190,000  
**Budget Session 76 :** ~95k disponibles  
**Priorité :** Scanner V3 étendu (30-50 mouvements) + ML robuste
