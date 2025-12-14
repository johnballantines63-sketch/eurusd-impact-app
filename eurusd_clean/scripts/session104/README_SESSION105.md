# 📋 SESSION 105 - GUIDE DÉMARRAGE RAPIDE

**Date :** 31 octobre 2025  
**Mission :** Phase 1 - Validation Cluster #3 (6 dates CPI mensuel)

---

## ⚠️ PRIORITÉ ABSOLUE

**CORRIGER mesure impact 11.09 AVANT tout !**

```
Session 103 validé : 56.8 pips ✅
Script actuel      : 12.7 pips ❌
Écart              : 44.1 pips (77% erreur)
```

**Sans correction → Toutes les analyses invalides !**

---

## 📖 DOCUMENTATION À LIRE

**Ordre de lecture (30-45 min) :**

1. **MESSAGE_SESSION104_SESSION105.md** (15 min)
   - Récapitulatif Session 104
   - Méthodologie clusters
   - Plan Session 105

2. **METHODOLOGIE_VALIDATION_CLUSTERS.md** (15 min) ⚠️
   - **🚨 FICHIER CORRIGÉ - Lire attentivement !**
   - Principe : **Chaque cluster a SA PROPRE baseline**
   - Approche cluster par cluster
   - Plan 4 phases

3. **SESSION103_RAPPORT_COMPLET.md** (sections clés 15 min)
   - Méthode mesure impact correcte
   - Timestamps Session 92.5
   - Validation 11.09 = 56.8 pips

**⚠️ NE PAS LIRE :** `CORRECTION_BASELINE_PAR_CLUSTER.md` (note historique)

---

## 📂 FICHIERS DISPONIBLES

### Données

**Dataset complet :**
```
scripts/session104/dataset_44_dates_METHOD_SESSION92_5.csv
35 dates, clusters ≥8 events
⚠️ Impacts FAUX (à re-mesurer)
```

**Cluster #3 (6 dates) :**
```
scripts/session104/cluster3_cpi_6dates.csv  (à créer)
6 dates CPI mensuel
Référence : 2025-09-11
```

### Scripts Référence

**Mesure impact correcte :**
```
scripts/session102/measure_impact_FINAL_SESSION92_5_FIX.py
Méthode validée Session 103 : 56.8 pips ✅
```

**Formules validées :**
```
fx_impact_app/src/formulas_validated.py
- calculate_adjusted_empirical_score()
- calculate_impact_d()
- calculate_ttr_c()
```

---

## 🎯 ÉTAPES SESSION 105

### Étape 1 : CORRECTION CRITIQUE (⏱️ 1-2h)

**Objectif :** Reproduire 11.09 = 56.8 pips

**Actions :**
1. Créer `fix_measure_impact_11_09.py`
2. Copier logique EXACTE de Session 103
3. Tester sur 11.09
4. Valider : 56.8 ±2 pips
5. **Si échec → STOP, débugger avant continuer**

**Code référence Session 103 :**
```python
# Timestamps corrects
EVENT_TIME_DB = "12:30:00"  # Pour 14:30 Bern
query = f"WHERE datetime >= '2025-09-11 12:30:00+02:00'::TIMESTAMP"

# Prix départ = candle AVANT événement
prices_before = prices[prices['datetime'] < event_dt]
price_start = prices_before.iloc[-1]['close']

# Chercher pic APRÈS événement (120 min)
prices_after = prices[prices['datetime'] >= event_dt]
price_max = prices_after['close'].max()
price_min = prices_after['close'].min()

# Direction mouvement
if abs(price_max - price_start) > abs(price_min - price_start):
    impact = (price_max - price_start) * 10000  # UP
else:
    impact = (price_start - price_min) * 10000  # DOWN
```

---

### Étape 2 : Mesure 6 dates Cluster #3 (⏱️ 30 min)

**Objectif :** Impact réel pour les 6 dates

**Script :** `measure_cluster3_6dates.py`

```python
dates_cluster3 = [
    '2025-09-11',  # Doit être 56.8
    '2025-08-12',
    '2025-07-15',
    '2025-06-11',
    '2025-05-13',
    '2025-04-10'
]

for date in dates_cluster3:
    impact_real = measure_impact_corrected(date)
    # Utiliser méthode corrigée Étape 1
```

**Output :** `cluster3_impacts_corrected.csv`

---

### Étape 3 : Calcul amp_optimal (⏱️ 1h)

**Objectif :** amp optimal pour chaque date

**Script :** `calculate_amp_optimal_cluster3.py`

```python
from scipy.optimize import minimize_scalar
from formulas_validated import calculate_impact_d

for date in dates_cluster3:
    # Charger événements
    events = load_events_cluster3(date)
    score_adj = calculate_adjusted_score(events)
    
    # Optimiser amp
    def error(amp):
        pred = calculate_impact_d(score_adj, 11, amp, 0.758)
        return abs(pred - impact_real)
    
    result = minimize_scalar(error, bounds=(0.5, 5.0))
    amp_opt = result.x
    
    # Delta vs baseline
    delta_amp = (amp_opt - 2.5) / 2.5
```

**Output :** `cluster3_amp_optimal.csv`

---

### Étape 4 : Métriques (⏱️ 1h)

**Objectif :** Collecter surprise, R², amplitude, durée

**Script :** `collect_metrics_cluster3.py`

```python
for date in dates_cluster3:
    metrics = {
        'surprise_max': max_surprise(events),
        'surprise_avg': avg_surprise(events),
        'R2_72h': calculate_r2_window(date, 72),
        'amplitude': price_amplitude(date),
        'duration': time_to_reversal(date)
    }
```

**Output :** `cluster3_metrics.csv`

---

### Étape 5 : Régression (⏱️ 30 min)

**Objectif :** Modèle delta_amp = f(surprise, R², amplitude)

**Script :** `regression_cluster3.py`

```python
from sklearn.linear_model import LinearRegression

X = df[['surprise_max', 'R2_72h', 'amplitude', 'duration']]
y = df['delta_amp']

model = LinearRegression().fit(X, y)

print(f"Coefficients : {model.coef_}")
print(f"R² score : {model.score(X, y)}")
```

---

### Étape 6 : Validation (⏱️ 30 min)

**Objectif :** Leave-One-Out validation

**Script :** `validate_cluster3_loo.py`

```python
from sklearn.model_selection import LeaveOneOut

mae_scores = []
for train_idx, test_idx in LeaveOneOut().split(df):
    train_data = df.iloc[train_idx]
    test_data = df.iloc[test_idx]
    
    model = train_model(train_data)
    mae = evaluate(model, test_data)
    mae_scores.append(mae)

mae_final = np.mean(mae_scores)
print(f"MAE Leave-One-Out : {mae_final:.2f} pips")

# Comparer baseline
baseline_mae = calculate_baseline_mae(df, amp=2.5)
print(f"MAE Baseline 2.5 : {baseline_mae:.2f} pips")

if mae_final < baseline_mae:
    print("✅ Formule améliore baseline")
else:
    print("✅ Baseline 2.5 suffisante")
```

---

## ⏱️ DURÉE ESTIMÉE SESSION 105

**Total : 4-6 heures**
- Correction mesure : 1-2h
- Mesure 6 dates : 30 min
- Calcul amp_optimal : 1h
- Métriques : 1h
- Régression : 30 min
- Validation : 30 min
- Documentation : 30-60 min

---

## ✅ CRITÈRES SUCCÈS

**Session 105 réussie si :**

1. ✅ 11.09 mesuré = 56.8 ±2 pips
2. ✅ 6 dates Cluster #3 mesurées correctement
3. ✅ amp_optimal calculé pour chaque date
4. ✅ Régression complétée (R² > 0.5)
5. ✅ Validation Leave-One-Out
6. ✅ Décision claire : formule ou baseline 2.5

---

## 🚨 POINTS CRITIQUES

**1. Ne PAS sauter Étape 1 :**
```
Sans correction 11.09 = 56.8 pips
→ Toutes analyses FAUSSES
→ Perte de temps
```

**2. Timestamps DB :**
```
14:30 Bern = 12:30:00+02:00 dans DB
Référence Session 92.5 TOUJOURS
```

**3. Méthode mesure :**
```
Prix départ = candle AVANT événement
Pic = max/min dans 120 min APRÈS
Direction = plus grand mouvement
```

---

**Bonne chance ! 🚀**

*Guide créé : 31 octobre 2025 - Session 104*
