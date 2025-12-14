# 📬 MESSAGE SESSION 76 → SESSION 77

**Date :** 25 octobre 2025  
**Session actuelle :** 76 ⚠️ DÉCOUVERTE CRITIQUE  
**Prochaine session :** 77  
**Statut global :** ML inadapté → Calibration Grid Search nécessaire

---

## 🎯 RÉSUMÉ SESSION 76

### Mission vs Résultat

**Objectif initial :** Créer formules ML V2.0 robustes sur dataset élargi  
**Résultat :** ❌ ML ÉCHEC - Erreur méthodologique critique identifiée  
**Tokens utilisés :** 87,000 / 190,000 (45.8%)

### Réalisations Session 76

**✅ Datasets créés :**
- Scanner V3 Standard : 20 mouvements (100% diversité)
- Scanner V3.1 Ultra : 27 mouvements (100% diversité) ⭐

**❌ ML tenté 2 fois - ÉCHEC :**
- Tentative 1 (20 obs) : R² -1.19 (NÉGATIF), MAE 23.1 pips
- Tentative 2 (27 obs) : R² NaN, MAE 18.8 pips, instabilité énorme (std 13 pips)

**🔥 DÉCOUVERTE CRITIQUE :**

**ML simple IGNORE formules validées Sessions 51-55 :**
- ❌ Somme vectorielle (impacts signés)
- ❌ Amplification surprise (zones 1-3)
- ❌ Facteur correction 0.758
- ❌ Direction événements (FAMILY_SENTIMENT)
- ❌ Distinction clusters vs single events

**Conséquence :** Modèle capture tendance moyenne (~19 pips MAE) mais ignore logique multi-événements → Instabilité catastrophique (erreurs 0.3-69 pips)

---

### Top 3 Découvertes Critiques

**1. ML Simple = Perte Structure Validée** 🔴

```python
# ❌ CE QUI A ÉTÉ FAIT (FAUX)
impact = intercept + coef_score × score + coef_events × nb_events + ...

# ✅ CE QUI DEVAIT ÊTRE FAIT (CORRECT)
# Formules Sessions 51-55 (98.6% précision 11 sept)
impact_brut = -10.47 + 0.477 × score_ajuste  # Multi-events
impact_signé = impact_brut × direction  # FAMILY_SENTIMENT
impact_total = SUM(impacts_signés)  # Somme vectorielle
impact_amplifié = impact_total × amplification(surprise)  # Zones 1-3
impact_final = |impact_amplifié| × 0.758  # Correction
```

**Impact :**
- ML réinvente formule → Ignore 5 composants validés
- Structure 98.6% précision abandonnée
- Coefficient surprise NÉGATIF (contre-intuitif) ignoré

---

**2. Dataset 27 obs = Limite Critique pour ML** 🟡

**Règle ML :** Minimum 10 observations par feature

| Config | Obs | Features | Ratio | Statut |
|--------|-----|----------|-------|--------|
| Idéal | 40+ | 4 | 10:1 | ✅ |
| **Actuel** | **27** | **4** | **6.75:1** | ❌ |

**Conséquence :**
- Overfitting inévitable (ratio < 10:1)
- R² NaN (variance nulle certains folds)
- Instabilité énorme (std 13 pips vs MAE 19 pips)

---

**3. Solution = Calibration, Pas ML From Scratch** ✅

**Approche correcte :**
- ✅ **GARDER structure Sessions 51-55** (validée 98.6%)
- ✅ **CALIBRER uniquement 4 coefficients** formule D sur 27 mouvements
- ✅ **Grid Search** : 29,700 combinaisons, Leave-One-Out CV
- ✅ **Conserver** amplification + correction + somme vectorielle

**Avantages :**
- Structure contrainte → Moins overfitting
- Interprétabilité haute (coefficients physiques)
- Validation robuste (LOO CV)

---

## 📁 FICHIERS DISPONIBLES SESSION 77

### Datasets Créés (Session 76)

```
fx_impact_app/scripts/session76/
├── dataset_session76_extended.csv (20 lignes) - V3 Standard
└── dataset_session76_ultra.csv (27 lignes) - V3.1 Ultra ⭐⭐⭐
```

**Dataset recommandé Session 77 :**
- **`dataset_session76_ultra.csv` : 27 mouvements qualité**
- 100% diversité (27 jours distincts)
- Impact moyen : 74.2 pips
- Nb events moyen : 8.6
- Score moyen : 44.2
- Surprise moyenne : 59.3%

### Dataset Validation (Session 75)

```
fx_impact_app/scripts/session75/
└── dataset_session75_filtered.csv (7 lignes) - Qualité ⭐⭐
```

**Usage :** Validation finale formules V2 calibrées

### Formules Validées (Sessions 51-55)

**Module :** `fx_impact_app/src/formulas_validated.py`

**Statut :** ✅ STRUCTURE VALIDÉE (98.6% précision 11 sept)

**Fonctions :**
```python
from src.formulas_validated import (
    calculate_adjusted_empirical_score,  # Ajustement surprise
    calculate_impact_d                   # Impact net (coef à calibrer)
)
```

**Composants structure (à GARDER) :**
1. Score ajusté par surprise (Session 55)
2. Impact D : intercept + coef × score (Session 51)
3. Somme vectorielle (direction FAMILY_SENTIMENT)
4. Amplification surprise (zones 1-3)
5. Correction 0.758 (Session 11)

---

## 🎯 MISSION SESSION 77

### Objectif Principal ⭐⭐⭐

**CALIBRER coefficients formule D** (Sessions 51-55) sur dataset 27 mouvements via **Grid Search**

**GARDER structure validée, optimiser uniquement 4 coefficients**

---

### ÉTAPE 1 : Grid Search Calibration (~20-25k tokens)

**Script à créer :** `1_grid_search_calibration.py`

**Fonctions principales :**

```python
def reconstitute_event_cluster(movement_row, conn):
    """
    Reconstruit cluster événements pour 1 mouvement
    
    Query events dans fenêtre ±10 min autour mouvement
    Returns: Liste événements avec scores, surprises, familles
    """

def calculate_impact_with_params(
    events_cluster, 
    intercept_multi, coef_multi,
    intercept_single, coef_single
):
    """
    Calcule impact avec paramètres donnés
    
    APPLIQUE EXACTEMENT formules Sessions 51-55 :
    1. Score ajusté par surprise (Session 55)
    2. Impact D avec params donnés (Session 51)
    3. Somme vectorielle + direction (FAMILY_SENTIMENT)
    4. Amplification surprise (zones 1-3, Sessions 14-15)
    5. Correction 0.758 (Session 11)
    
    Args:
        events_cluster : Liste événements du cluster
        intercept_multi : Intercept multi-événements
        coef_multi : Coefficient multi-événements
        intercept_single : Intercept single event
        coef_single : Coefficient single event
    
    Returns:
        impact_final : Impact prédit (pips, valeur absolue)
    """

def grid_search_calibration(df_movements, conn, param_ranges):
    """
    Grid search exhaustif 29,700 combinaisons
    
    Pour chaque combinaison (intercept_multi, coef_multi, intercept_single, coef_single) :
        Pour chaque mouvement (Leave-One-Out CV, 27 iterations) :
            train_set = 26 mouvements
            test_set = 1 mouvement
            
            impact_pred = calculate_impact_with_params(test_set, params)
            impact_real = test_set['impact_pips']
            
            mae_fold = abs(impact_pred - impact_real)
        
        mae_cv = mean(mae_folds)
    
    Returns: Meilleurs paramètres (MAE CV minimum)
    """
```

**Configuration Grid :**
```python
param_ranges = {
    'intercept_multi': np.arange(-20, 1, 1),      # 20 valeurs
    'coef_multi': np.arange(0.30, 0.81, 0.05),    # 11 valeurs
    'intercept_single': np.arange(-15, 1, 1),     # 15 valeurs
    'coef_single': np.arange(0.30, 0.71, 0.05)    # 9 valeurs
}

# Total : 20 × 11 × 15 × 9 = 29,700 combinaisons
```

**Validation Leave-One-Out :**
- 27 iterations (1 mouvement test, 26 train)
- Métrique : MAE (Mean Absolute Error)
- Objectif : MAE CV < 30 pips (amélioration 50% vs S75 : 64.9 → 30)

**Outputs :**
- `calibration_results_session77.txt` (meilleurs params + métriques)
- `calibration_grid_analysis.csv` (top 100 combinaisons)

**Durée estimée :** 2-3 minutes (29,700 × 27 = 800k calculs)

---

### ÉTAPE 2 : Test 11 Septembre (~5-8k tokens)

**Vérifier pas de régression vs V1 original**

```python
# Charger événements 11 septembre
events_11sept = load_validation_events()

# V1 original (Session 51)
impact_v1 = calculate_impact_d(
    events_11sept,
    intercept_multi=-10.47,
    coef_multi=0.477,
    intercept_single=-7.08,
    coef_single=0.419
)

# V2 calibré
impact_v2 = calculate_impact_d(
    events_11sept,
    intercept_multi=CALIBRATED_MULTI,
    coef_multi=CALIBRATED_COEF_MULTI,
    intercept_single=CALIBRATED_SINGLE,
    coef_single=CALIBRATED_COEF_SINGLE
)

# Impact réel MT5
impact_real = 53 pips

# Comparaison
MAE_v1 = abs(impact_v1 - impact_real)  # ~4 pips (7%)
MAE_v2 = abs(impact_v2 - impact_real)  # ? pips
```

**Critère succès :** MAE_v2 < 10 pips (acceptable, < 20%)

**Si MAE_v2 > 10 pips :** Formules calibrées dégradent cas référence → Ajuster grid search

---

### ÉTAPE 3 : Validation Session 75 (~8-10k tokens)

**Test sur 7 mouvements qualité Session 75**

```python
# Charger dataset S75
df_s75 = pd.read_csv('dataset_session75_filtered.csv')

# Calculer avec V1 original
impacts_v1 = []
for i, row in df_s75.iterrows():
    events = reconstitute_event_cluster(row, conn)
    impact = calculate_impact_with_params(
        events,
        intercept_multi=-10.47,
        coef_multi=0.477,
        intercept_single=-7.08,
        coef_single=0.419
    )
    impacts_v1.append(impact)

mae_v1 = mean_absolute_error(df_s75['impact_pips'], impacts_v1)

# Calculer avec V2 calibré
impacts_v2 = []
for i, row in df_s75.iterrows():
    events = reconstitute_event_cluster(row, conn)
    impact = calculate_impact_with_params(
        events,
        intercept_multi=CALIBRATED_MULTI,
        coef_multi=CALIBRATED_COEF_MULTI,
        intercept_single=CALIBRATED_SINGLE,
        coef_single=CALIBRATED_COEF_SINGLE
    )
    impacts_v2.append(impact)

mae_v2 = mean_absolute_error(df_s75['impact_pips'], impacts_v2)

# Comparaison
print(f"MAE V1 : {mae_v1:.1f} pips")
print(f"MAE V2 : {mae_v2:.1f} pips")
print(f"Amélioration : {(mae_v1 - mae_v2) / mae_v1 * 100:.1f}%")
```

**Critères succès :**
- MAE_v2 < 32 pips (amélioration 50% vs S75 : 64.9 → 32)
- MAE_v2 < MAE_v1 (amélioration vs V1)

---

### ÉTAPE 4 : Module formulas_validated_v2.py (~8-10k tokens)

**Fichier à créer :** `fx_impact_app/src/formulas_validated_v2.py`

```python
"""
FORMULES VALIDÉES V2.0 - SESSION 77
====================================

Calibration coefficients formule D sur 27 mouvements (2023-2025)

Structure identique Sessions 51-55 :
- Score ajusté par surprise (Session 55)
- Impact D (Session 51) avec coefficients calibrés
- Somme vectorielle + direction (FAMILY_SENTIMENT)
- Amplification surprise (zones 1-3, Sessions 14-15)
- Correction 0.758 (Session 11)

Validation :
- Dataset 27 mouvements : MAE X.X pips (LOO CV)
- 11 septembre 2025 : MAE X.X pips
- Session 75 (7 mouvements) : MAE X.X pips

Date : 25 octobre 2025
Session : 77
"""

# ════════════════════════════════════════════════════════════════
# COEFFICIENTS CALIBRÉS
# ════════════════════════════════════════════════════════════════

# Multi-événements (nb_events ≥ 2)
INTERCEPT_MULTI_V2 = -X.XX  # À déterminer Grid Search
COEF_MULTI_V2 = 0.XXX

# Single event (nb_events = 1)
INTERCEPT_SINGLE_V2 = -X.XX  # À déterminer Grid Search
COEF_SINGLE_V2 = 0.XXX

# Coefficients V1 (référence Sessions 51-55)
INTERCEPT_MULTI_V1 = -10.47
COEF_MULTI_V1 = 0.477
INTERCEPT_SINGLE_V1 = -7.08
COEF_SINGLE_V1 = 0.419


# ════════════════════════════════════════════════════════════════
# FONCTIONS
# ════════════════════════════════════════════════════════════════

def calculate_impact_v2(
    events_cluster: List[Dict],
    apply_correction: bool = True,
    version: str = 'v2'
) -> float:
    """
    Formule V2.0 - Coefficients calibrés sur 27 mouvements
    
    Structure IDENTIQUE Sessions 51-55 :
    1. Score ajusté par surprise
    2. Impact D avec coefficients calibrés
    3. Somme vectorielle (direction)
    4. Amplification surprise (zones 1-3)
    5. Correction 0.758
    
    Args:
        events_cluster : Liste événements du cluster
        apply_correction : Appliquer facteur 0.758
        version : 'v1' (Sessions 51-55) ou 'v2' (calibré)
    
    Returns:
        impact_final : Impact prédit (pips, valeur absolue)
    
    Examples:
        >>> events = [
        ...     {'score': 44.8, 'surprise': 33.3, 'family': 'CPI', 'nb_events': 9}
        ... ]
        >>> impact = calculate_impact_v2(events, version='v2')
        >>> print(f"{impact:.1f} pips")
    """
```

---

### ÉTAPE 5 : Documentation (~8-10k tokens)

- `SESSION77_RAPPORT_COMPLET.md`
- `MESSAGE_SESSION77_SESSION78.md`
- Update `project_state_new.md` (section Session 77)

---

## ⚠️ POINTS D'ATTENTION SESSION 77

### Attention #1 : Appliquer EXACTEMENT Formules Sessions 51-55

**CRITIQUE :** Session 76 a échoué car ML simple ignorait :
- ❌ Somme vectorielle
- ❌ Amplification surprise
- ❌ Correction 0.758
- ❌ Direction FAMILY_SENTIMENT

**Solution Session 77 :**
```python
# ✅ STRUCTURE COMPLÈTE À RESPECTER

# 1. Score ajusté (Session 55)
score_ajuste = calculate_adjusted_empirical_score(score_base, surprise)

# 2. Impact D avec params
if nb_events >= 2:
    impact_brut = intercept_multi + coef_multi × score_ajuste
else:
    impact_brut = intercept_single + coef_single × score_ajuste

# 3. Somme vectorielle
impact_signé = impact_brut × FAMILY_SENTIMENT[famille]
impact_total = SUM(impacts_signés)

# 4. Amplification surprise
if score_ajuste >= 40 and surprise >= 5:
    if surprise < 5:
        amplification = 1.0
    elif surprise < 15:
        amplification = 1.0 + (surprise - 5) / 10 × 1.5
    else:
        amplification = 2.5  # Plafond
else:
    amplification = 1.0

impact_amplifié = impact_total × amplification

# 5. Correction
impact_final = abs(impact_amplifié) × 0.758
```

---

### Attention #2 : Vérifier Path Dataset

**Erreur Session 76 Tentative 1 :** Chargé V3 (20 obs) au lieu V3.1 (27 obs)

**Solution :**
```python
# ✅ VÉRIFIER AVANT EXÉCUTION
INPUT_PATH = SCRIPT_DIR / "dataset_session76_ultra.csv"  # CORRECT

if not INPUT_PATH.exists():
    print(f"❌ Dataset non trouvé : {INPUT_PATH}")
    return 1

df = pd.read_csv(INPUT_PATH)
print(f"✅ {len(df)} mouvements chargés")

# Vérifier nombre attendu
if len(df) != 27:
    print(f"⚠️  ATTENTION : {len(df)} mouvements au lieu de 27")
```

---

### Attention #3 : Grid Search = Long (2-3 min)

**29,700 combinaisons × 27 iterations LOO = 800,000 calculs**

**Optimisations :**
```python
# 1. Progress bar
from tqdm import tqdm

for params in tqdm(param_combinations, desc="Grid Search"):
    ...

# 2. Parallélisation (optionnel)
from joblib import Parallel, delayed

results = Parallel(n_jobs=-1)(
    delayed(test_params)(params) for params in param_combinations
)

# 3. Early stopping (optionnel)
if mae_cv < 15:  # Excellent
    print(f"✅ MAE {mae_cv:.1f} pips < 15 - STOP")
    break
```

---

### Attention #4 : Coefficient Contre-Intuitif = Red Flag

**Expérience Session 76 :**
```
surprise_max : -0.1743  # NÉGATIF ❌
```

**Interprétation :** Plus surprise augmente → Impact diminue (FAUX)

**Action Session 77 :**
```python
# Après Grid Search, vérifier coefficients
if coef_multi < 0 or coef_single < 0:
    print(f"⚠️  RED FLAG : Coefficient négatif détecté")
    print(f"   coef_multi : {coef_multi:.4f}")
    print(f"   coef_single : {coef_single:.4f}")
    print(f"   → STOP et investiguer")
```

**Coefficients attendus (physiquement cohérents) :**
- `coef_multi` : 0.3-0.8 (positif)
- `coef_single` : 0.3-0.7 (positif)
- `intercept_multi` : -20 à 0 (négatif ou faible positif)
- `intercept_single` : -15 à 0 (négatif ou faible positif)

---

## 🎓 LEÇONS SESSION 76 POUR SESSION 77

### Ce qui a bien fonctionné ✅

1. **Datasets qualité créés**
   - 27 mouvements, 100% diversité
   - Vrais clusters (8.6 events moyens)
   - Réutilisables Session 77

2. **Méthodologie validation**
   - Leave-One-Out adaptée à 27 observations
   - Plus stable que K-Fold

3. **Diagnostic méthodique**
   - 2 tentatives ML testées
   - Erreur méthodologique identifiée clairement

### À appliquer Session 77 ✅

1. **Structure validée = Non négociable**
   - Formules Sessions 51-55 = 98.6% précision
   - GARDER somme vectorielle, amplification, correction
   - CALIBRER uniquement coefficients (4 params)

2. **Grid Search exhaustif**
   - 29,700 combinaisons
   - Validation rigoureuse LOO
   - Éviter overfitting (structure contrainte)

3. **Validation double**
   - 11 septembre : Pas de régression (MAE < 10 pips)
   - Session 75 : Amélioration (MAE < 32 pips)

4. **Coefficients physiquement cohérents**
   - Positifs (score/surprise → impact augmente)
   - Interceptes négatifs/faibles (seuil activation)

---

## 📞 MESSAGE TYPE SESSION 77

```
Bonjour Claude,

Nouvelle session 77 - CALIBRATION GRID SEARCH FORMULES VALIDÉES

AVANT TOUT :
1. Lis MANDATORY_SESSION_RULES.md (v2.1)
2. Lis project_state_new.md (section Session 76)
3. Lis SESSION76_RAPPORT_COMPLET.md
4. Lis MESSAGE_SESSION76_SESSION77.md (ce fichier)

Indique régulièrement les tokens utilisés

CONTEXTE SESSION 76 :
- Mission : Créer formules ML V2.0 robustes
- Résultat : ❌ ML ÉCHEC (R² NaN, instabilité énorme)
- Découverte : ML simple IGNORE formules validées Sessions 51-55
- Conclusion : Calibration Grid Search nécessaire

MISSION SESSION 77 :
Calibrer coefficients formule D (Sessions 51-55) sur dataset 27 mouvements

Étape 1 : Grid Search Calibration
- Appliquer EXACTEMENT formules Sessions 51-55
  (somme vectorielle + amplification + correction 0.758)
- Optimiser 4 coefficients : intercept/coef × (multi/single)
- 29,700 combinaisons, Leave-One-Out CV
- Objectif : MAE CV < 30 pips

Étape 2 : Test 11 septembre
- Vérifier pas de régression vs V1
- Critère : MAE < 10 pips

Étape 3 : Validation Session 75
- Tester sur 7 mouvements qualité
- Critère : MAE < 32 pips (amélioration 50%)

Étape 4 : Module formulas_validated_v2.py
- Fonction calculate_impact_v2()
- Coefficients calibrés
- Structure identique Sessions 51-55

Étape 5 : Documentation

FICHIERS DISPONIBLES :
- dataset_session76_ultra.csv (27 mouvements) ⭐⭐⭐
- dataset_session75_filtered.csv (7 mouvements validation)
- formulas_validated.py (structure Sessions 51-55)

CRITÈRES SUCCÈS :
- MAE CV dataset 27 : < 30 pips
- MAE 11 septembre : < 10 pips (pas régression)
- MAE Session 75 : < 32 pips (amélioration 50%)

POINTS CRITIQUES :
- APPLIQUER EXACTEMENT formules Sessions 51-55
- Vérifier path dataset (27 mouvements)
- Grid Search = 2-3 min (normal)
- Coefficients contre-intuitifs = red flag → STOP

BUDGET TOKENS : ~105k limite (suffisant pour tout)

GO après validation compréhension !
```

---

## ✅ CHECKLIST SESSION 77

### Phase 1 : Lecture (30-35k tokens)
- [ ] MANDATORY_SESSION_RULES.md lu
- [ ] project_state_new.md lu (section Session 76)
- [ ] SESSION76_RAPPORT_COMPLET.md lu
- [ ] MESSAGE_SESSION76_SESSION77.md lu (ce fichier)
- [ ] Validation mission avec utilisateur

### Phase 2 : Grid Search (~20-25k tokens)
- [ ] Script 1_grid_search_calibration.py créé
- [ ] Dataset V3.1 Ultra chargé (27 mouvements)
- [ ] Formules Sessions 51-55 appliquées correctement
- [ ] Grid Search exécuté (29,700 combinaisons)
- [ ] Meilleurs paramètres identifiés
- [ ] Coefficients physiquement cohérents vérifiés

### Phase 3 : Validation (~13-18k tokens)
- [ ] Test 11 septembre : MAE < 10 pips ✅
- [ ] Test Session 75 : MAE < 32 pips ✅
- [ ] Comparaison V1 vs V2 documentée

### Phase 4 : Module V2 (~8-10k tokens)
- [ ] formulas_validated_v2.py créé
- [ ] Fonction calculate_impact_v2()
- [ ] Documentation complète
- [ ] Tests unitaires

### Phase 5 : Documentation (~8-10k tokens)
- [ ] SESSION77_RAPPORT_COMPLET.md
- [ ] MESSAGE_SESSION77_SESSION78.md
- [ ] project_state_new.md mis à jour

---

## 🎯 OBJECTIF FINAL

**Session 76 :** ❌ ML simple inadapté (ignore structure validée)  
**Session 77 :** ✅ Calibration Grid Search (garde structure, optimise coefficients)  
**Session 78+ :** Intégration production Planificateur V2.5

**Vision :** Formules V2.0 calibrées sur 27 mouvements → Généralisation robuste

---

*Prêt pour Session 77 - Calibration Grid Search Formules Validées !* 🚀

**SESSION 76 → SESSION 77**  
**Date :** 25 octobre 2025  
**Tokens Session 76 :** 87,000 / 190,000  
**Budget Session 77 :** ~105k limite  
**Priorité :** Grid Search exhaustif + Validation double (11 sept + S75)
