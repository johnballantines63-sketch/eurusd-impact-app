# SECTIONS DÉTAILLÉES COMPLÉMENTAIRES

**Ce document contient les sections restantes détaillées à intégrer dans PROJET_GESTION_SCIENTIFIQUE.md**

---

## SECTION 3.3.3 COMPLÈTE

**M\u00e9triques d\u00e9j\u00e0 collect\u00e9es en 3.2** : surprise_max, surprise_avg, R2_72h, amplitude_24h, duration_minutes

**Objectif 3.3.3** : Vérifier que toutes les métriques nécessaires sont présentes pour la régression.

**Script de vérification** : `scripts/session105/verify_metrics_cluster3.py`

```python
#!/usr/bin/env python3
"""Vérification métriques contextuelles"""
import pandas as pd

df = pd.read_csv('cluster3_delta_amp.csv')

REQUIRED_METRICS = [
    'surprise_max', 'surprise_avg', 'R2_72h', 
    'amplitude_24h', 'duration_minutes', 'delta_amp'
]

print("VÉRIFICATION MÉTRIQUES")
for metric in REQUIRED_METRICS:
    assert metric in df.columns, f"{metric} manquante"
    assert not df[metric].isnull().any(), f"{metric} a valeurs nulles"
    print(f"✅ {metric}")

print("\n✅ Toutes métriques présentes et valides")
print("📋 Prêt pour Phase 3.4 (Modélisation)")
```

**Output** : Confirmation que dataset est prêt pour régression.

**Durée** : 5 minutes

---

## SECTIONS 3.4 DÉTAILLÉES (Modélisation)

### 3.4.1 Analyse corrélations - COMPLET

**Script** : `scripts/session105/analyze_correlations_cluster3.py`

```python
#!/usr/bin/env python3
"""Analyse corrélations Cluster #3"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv('cluster3_delta_amp.csv')

variables = ['surprise_max', 'surprise_avg', 'R2_72h', 'amplitude_24h', 'duration_minutes']
target = 'delta_amp'

print("CORRÉLATIONS AVEC delta_amp :")
for var in variables:
    corr = df[var].corr(df[target])
    sig = "***" if abs(corr) > 0.7 else "**" if abs(corr) > 0.4 else "*" if abs(corr) > 0.2 else ""
    print(f"  {var:20s} : r = {corr:+.3f} {sig}")

# Heatmap
corr_matrix = df[variables + [target]].corr()
plt.figure(figsize=(10, 8))
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, vmin=-1, vmax=1)
plt.title('Corrélations - Cluster #3')
plt.tight_layout()
plt.savefig('cluster3_correlations.png', dpi=150)

# Scatter plots
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
for idx, var in enumerate(variables):
    ax = axes[idx // 3, idx % 3]
    ax.scatter(df[var], df[target], alpha=0.7)
    ax.set_xlabel(var)
    ax.set_ylabel('delta_amp')
    corr = df[var].corr(df[target])
    ax.set_title(f'r = {corr:+.3f}')
    # Ligne tendance
    z = np.polyfit(df[var], df[target], 1)
    p = np.poly1d(z)
    ax.plot(df[var], p(df[var]), "r--", alpha=0.8)
    ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig('cluster3_scatter_plots.png', dpi=150)

print("\n✅ Graphiques sauvegardés")
```

**Interprétation** :
- |r| > 0.7 : Forte corrélation
- 0.4 < |r| < 0.7 : Modérée
- |r| < 0.4 : Faible

**Durée** : 15 minutes

---

### 3.4.2 Régression multiple - COMPLET

**Script** : `scripts/session105/regression_cluster3.py`

```python
#!/usr/bin/env python3
"""Régression multiple Cluster #3"""
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error
from scipy import stats

df = pd.read_csv('cluster3_delta_amp.csv')

# Variables
X = df[['surprise_max', 'R2_72h', 'amplitude_24h', 'duration_minutes']]
y = df['delta_amp']

# Régression
model = LinearRegression()
model.fit(X, y)

# Coefficients
coeffs = {
    'alpha (surprise)': model.coef_[0],
    'beta (R2)': model.coef_[1],
    'gamma (amplitude)': model.coef_[2],
    'delta (duration)': model.coef_[3],
    'intercept': model.intercept_
}

print("COEFFICIENTS RÉGRESSION :")
for name, value in coeffs.items():
    print(f"  {name:25s} : {value:+.6f}")

# Métriques
y_pred = model.predict(X)
r2 = r2_score(y, y_pred)
mae = mean_absolute_error(y, y_pred)

print(f"\nMÉTRIQUES :")
print(f"  R² : {r2:.3f}")
print(f"  MAE : {mae:.4f}")

# Tests significativité
n, p = len(X), X.shape[1]
dof = n - p - 1
residuals = y - y_pred
mse = np.sum(residuals**2) / dof

print(f"\nSIGNIFICATIVITÉ (test t) :")
for i, name in enumerate(['alpha', 'beta', 'gamma', 'delta']):
    se = np.sqrt(mse * np.linalg.inv(X.T.dot(X))[i, i])
    t_stat = model.coef_[i] / se
    p_value = 2 * (1 - stats.t.cdf(abs(t_stat), dof))
    sig = "***" if p_value < 0.001 else "**" if p_value < 0.01 else "*" if p_value < 0.05 else ""
    print(f"  {name:10s} : t={t_stat:+.3f}, p={p_value:.4f} {sig}")

# Sauvegarde
import json
results = {
    'coefficients': {k: float(v) for k, v in coeffs.items()},
    'metrics': {'R2': float(r2), 'MAE': float(mae)},
    'n_samples': int(n)
}
with open('cluster3_regression_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\n✅ Résultats sauvegardés")
```

**Durée** : 15 minutes

---

### 3.4.3 Formule amp dynamique - COMPLET

**Formule générique** :

```python
# scripts/session105/formule_cluster3.py

def amp_dynamic_cluster3(surprise, R2, amplitude, duration):
    """
    Calcule amp dynamique pour Cluster #3 (CPI)
    
    Paramètres (issus de régression 3.4.2) :
    - surprise : surprise_max (ratio)
    - R2 : R²_72h (0-1)
    - amplitude : amplitude_24h
    - duration : duration_minutes
    
    Retourne : amp optimisé
    """
    # Baseline Cluster #3
    baseline = 2.5
    
    # Coefficients (à remplacer par valeurs réelles de 3.4.2)
    alpha = 0.150   # surprise
    beta = -0.080   # R²
    gamma = 0.020   # amplitude
    delta = -0.010  # duration
    
    # Correction
    correction = (
        alpha * surprise +
        beta * R2 +
        gamma * amplitude +
        delta * duration
    )
    
    # Amp final
    amp = baseline * (1 + correction)
    
    # Contraintes sécurité
    amp = np.clip(amp, 0.5, 5.0)
    
    return amp
```

**Sauvegarde dans module production** :
- `fx_impact_app/src/formulas_cluster3.py`

**Tests unitaires** :
```python
# tests/test_formulas_cluster3.py

def test_amp_cluster3_baseline():
    # Contexte neutre = baseline
    amp = amp_dynamic_cluster3(0, 0, 0, 0)
    assert amp == pytest.approx(2.5, 0.01)

def test_amp_cluster3_constraints():
    # Contraintes respectées
    amp_high = amp_dynamic_cluster3(1, 1, 100, 200)
    assert 0.5 <= amp_high <= 5.0
```

**Durée** : 20 minutes

---

### 3.4.4 Validation Leave-One-Out - COMPLET

**Script** : `scripts/session105/validate_cluster3_loo.py`

```python
#!/usr/bin/env python3
"""Validation Leave-One-Out Cluster #3"""
import pandas as pd
import numpy as np
from sklearn.model_selection import LeaveOneOut
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "fx_impact_app" / "src"))
from formulas_validated import calculate_impact_d

df = pd.read_csv('cluster3_delta_amp.csv')

BASELINE = 2.5
CORRECTION = 0.758

loo = LeaveOneOut()
errors_loo = []
errors_baseline = []
dates_test = []

print("VALIDATION LEAVE-ONE-OUT")
print("="*60)

for train_idx, test_idx in loo.split(df):
    train = df.iloc[train_idx]
    test = df.iloc[test_idx]
    
    # Entraîner modèle
    X_train = train[['surprise_max', 'R2_72h', 'amplitude_24h', 'duration_minutes']]
    y_train = train['delta_amp']
    
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    # Prédire
    X_test = test[['surprise_max', 'R2_72h', 'amplitude_24h', 'duration_minutes']]
    delta_pred = model.predict(X_test)[0]
    
    # Amp prédit formule
    amp_pred_formula = BASELINE * (1 + delta_pred)
    
    # Impact prédit formule
    impact_pred_formula = calculate_impact_d(
        test['score_adjusted'].values[0],
        11,
        amp_pred_formula,
        CORRECTION
    )
    
    # Impact prédit baseline
    impact_pred_baseline = calculate_impact_d(
        test['score_adjusted'].values[0],
        11,
        BASELINE,
        CORRECTION
    )
    
    # Impact réel
    impact_real = test['impact_real_pips'].values[0]
    
    # Erreurs
    error_formula = abs(impact_pred_formula - impact_real)
    error_baseline = abs(impact_pred_baseline - impact_real)
    
    errors_loo.append(error_formula)
    errors_baseline.append(error_baseline)
    dates_test.append(test['date'].values[0])
    
    print(f"{test['date'].values[0]} :")
    print(f"  Réel: {impact_real:.1f} | Baseline: {impact_pred_baseline:.1f} ({error_baseline:.1f}) | Formule: {impact_pred_formula:.1f} ({error_formula:.1f})")

# MAE moyens
mae_loo = np.mean(errors_loo)
mae_baseline = np.mean(errors_baseline)
improvement = mae_baseline - mae_loo
improvement_pct = (improvement / mae_baseline) * 100

print("\n" + "="*60)
print("RÉSULTATS LEAVE-ONE-OUT :")
print(f"  MAE Formule dynamique : {mae_loo:.2f} pips")
print(f"  MAE Baseline (2.5)    : {mae_baseline:.2f} pips")
print(f"  Amélioration          : {improvement:.2f} pips ({improvement_pct:.1f}%)")

# Graphique
fig, ax = plt.subplots(figsize=(10, 6))
x = np.arange(len(dates_test))
ax.bar(x - 0.2, errors_baseline, 0.4, label='Baseline 2.5', alpha=0.8)
ax.bar(x + 0.2, errors_loo, 0.4, label='Formule dynamique', alpha=0.8)
ax.set_xlabel('Date')
ax.set_ylabel('Erreur absolue (pips)')
ax.set_title('Erreurs Leave-One-Out - Cluster #3')
ax.set_xticks(x)
ax.set_xticklabels(dates_test, rotation=45, ha='right')
ax.legend()
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('cluster3_loo_results.png', dpi=150)

# Sauvegarde résultats
results = {
    'mae_formule': float(mae_loo),
    'mae_baseline': float(mae_baseline),
    'improvement_pips': float(improvement),
    'improvement_pct': float(improvement_pct),
    'dates': dates_test,
    'errors_formule': [float(e) for e in errors_loo],
    'errors_baseline': [float(e) for e in errors_baseline]
}

import json
with open('cluster3_loo_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\n✅ Résultats sauvegardés")
```

**Dur\u00e9e** : 20 minutes

---

## SECTION 3.5 D\u00c9TAILL\u00c9E (Décision)

### 3.5.1-3.5.3 Décision Cluster #3 - COMPLET

**Script décision** : `scripts/session105/decision_cluster3.py`

```python
#!/usr/bin/env python3
"""Décision finale Cluster #3"""
import json

with open('cluster3_loo_results.json') as f:
    loo = json.load(f)

mae_formule = loo['mae_formule']
mae_baseline = loo['mae_baseline']
improvement = loo['improvement_pips']

print("="*80)
print("D\u00c9CISION CLUSTER #3")
print("="*80)

print(f"\nMAE Formule  : {mae_formule:.2f} pips")
print(f"MAE Baseline : {mae_baseline:.2f} pips")
print(f"Am\u00e9lioration : {improvement:.2f} pips\n")

# Critères décision
if improvement >= 5:
    decision = "A"
    action = "ADOPTER formule dynamique"
    justif = f"Am\u00e9lioration significative ({improvement:.1f} pips ≥ 5 pips)"
elif 1 <= improvement < 5:
    decision = "B/C"
    action = "ÉVALUER rapport bénéfice/complexité"
    justif = f"Am\u00e9lioration marginale ({improvement:.1f} pips)"
else:
    decision = "B"
    action = "MAINTENIR baseline 2.5"
    justif = f"Pas d'amélioration ({improvement:.1f} pips < 1 pip)"

print(f"DÉCISION : Scénario {decision}")
print(f"ACTION   : {action}")
print(f"JUSTIF   : {justif}")

# Sauvegarde
with open('CLUSTER3_DECISION.txt', 'w') as f:
    f.write(f"DÉCISION CLUSTER #3 : {action}\n")
    f.write(f"Am\u00e9lioration : {improvement:.2f} pips\n")
    f.write(f"Justification : {justif}\n")

print("\n✅ Décision documentée")
```

**Rapport final** : `docs/CLUSTER3_VALIDATION_REPORT.md`

**Template rapport** :

```markdown
# CLUSTER #3 (CPI) - RAPPORT VALIDATION

## RÉSUMÉ EXÉCUTIF
- **Décision** : [Adopter formule / Maintenir baseline]
- **Amélioration** : X.X pips
- **Recommandation** : [Action]

## DONNÉES
- 6 dates validées (2025-04 à 2025-09)
- Baseline : 2.5
- Composition : 11 événements CPI

## RÉSULTATS RÉGRESSION
- R² : 0.XXX
- Coefficients : α, β, γ, δ
- Variables significatives : [liste]

## VALIDATION LEAVE-ONE-OUT
- MAE baseline : XX.X pips
- MAE formule : XX.X pips
- Amélioration : X.X pips (XX%)

## DÉCISION
[Justification détaillée]

## FORMULE FINALE (si adoptée)
```python
amp_cluster3 = 2.5 × (1 + α×surprise + β×R² + γ×amplitude + δ×duration)
```

## PROCHAINES ÉTAPES
- Phase 2 : Cluster #1 (Manufacturing)
- Phase 3 : Cluster #2 (NFP)
```

**Durée Section 3.5** : 1 heure

---

## PARTIE 4 COMPLÈTE - CLUSTER #1 (Manufacturing)

**Méthodologie** : **IDENTIQUE À PARTIE 3** mais adaptée pour :
- 11 dates (au lieu de 6)
- 8 événements (au lieu de 11)
- Baseline à établir (pas de référence connue)

### 4.1 Établissement baseline

**4.1.1-4.1.3** : Même approche que 3.1.2-3.1.3
- Sélectionner date référence parmi les 11
- Mesurer impact réel (méthode 3.1.1)
- Calculer amp_optimal → **baseline_cluster1**

**Script** : `scripts/session106/establish_baseline_cluster1.py`

```python
# Analyser 11 dates disponibles
dates = ['2025-10-01', '2025-09-02', ..., '2024-09-03']

# Sélectionner date médiane + récente
ref_date = '2025-06-02'  # Exemple

# Mesurer + optimiser
impact_real = measure_impact_corrected(ref_date)
amp_optimal_ref = optimize_amp(score, 8, impact_real)  # 8 events!

baseline_cluster1 = amp_optimal_ref
print(f"Baseline Cluster #1 : {baseline_cluster1:.3f}")
```

### 4.2-4.4 Validation

**Scripts** :
- `measure_cluster1_11dates.py` (comme 3.2)
- `calculate_amp_optimal_cluster1.py` (comme 3.3)
- `regression_cluster1.py` (comme 3.4)
- `validate_cluster1_loo.py` (comme 3.4.4)
- `decision_cluster1.py` (comme 3.5)

**Particularité** : Delta vs **baseline_cluster1** (pas 2.5!)

```python
df['delta_amp'] = (df['amp_optimal'] - baseline_cluster1) / baseline_cluster1
```

**Durée Partie 4** : Session 106 (~4-5 heures)

---

## PARTIE 5 COMPLÈTE - CLUSTER #2 (NFP)

**Méthodologie** : **IDENTIQUE À PARTIE 3/4** mais pour :
- 7 dates
- 12 événements
- Baseline à établir

**Scripts session 107** :
- `establish_baseline_cluster2.py`
- `measure_cluster2_7dates.py`
- `calculate_amp_optimal_cluster2.py`
- `regression_cluster2.py`
- `validate_cluster2_loo.py`
- `decision_cluster2.py`

**Durée Partie 5** : Session 107 (~4-5 heures)

---

## PARTIE 6 COMPLÈTE - SYNTHÈSE & PRODUCTION

### 6.1 Comparaison inter-clusters

**Script** : `scripts/session108/compare_clusters.py`

```python
#!/usr/bin/env python3
"""Comparaison inter-clusters"""
import json

# Charger résultats 3 clusters
with open('cluster3_decision.json') as f:
    c3 = json.load(f)
with open('cluster1_decision.json') as f:
    c1 = json.load(f)
with open('cluster2_decision.json') as f:
    c2 = json.load(f)

print("COMPARAISON INTER-CLUSTERS")
print("="*80)

clusters = {
    'Cluster #3 (CPI)': c3,
    'Cluster #2 (NFP)': c2,
    'Cluster #1 (Mfg)': c1
}

for name, data in clusters.items():
    print(f"\n{name} :")
    print(f"  Baseline        : {data['baseline']}")
    print(f"  MAE baseline    : {data['mae_baseline']:.2f} pips")
    print(f"  MAE formule     : {data['mae_formule']:.2f} pips")
    print(f"  Amélioration    : {data['improvement']:.2f} pips")
    print(f"  Décision        : {data['decision']}")
```

**Analyse** :
- Quelle relation baseline vs composition ?
- Formule dynamique utile pour quels clusters ?
- Patterns communs dans coefficients ?

### 6.2 Décision globale

**Scénarios** :

**A - Formules dynamiques** : Si amélioration moyenne ≥ 3 pips
**B - Baselines spécifiques** : Si amélioration 1-3 pips
**C - Baseline universelle 2.5** : Si pas d'amélioration

### 6.3 Intégration Planificateur

**Module** : `fx_impact_app/src/cluster_detection.py`

```python
def detect_cluster_type(events):
    """Détecte cluster par signature événements"""
    event_keys_set = frozenset(sorted([e.event_key for e in events]))
    
    # Signatures
    if event_keys_set == CLUSTER3_SIGNATURE:
        return "CLUSTER_3_CPI", 1.0
    elif event_keys_set == CLUSTER2_SIGNATURE:
        return "CLUSTER_2_NFP", 1.0
    elif event_keys_set == CLUSTER1_SIGNATURE:
        return "CLUSTER_1_MFG", 1.0
    else:
        return "UNKNOWN", 0.0
```

**Module** : `fx_impact_app/src/amp_optimization.py`

```python
def calculate_amp_optimized(events, context, strategy="baseline"):
    cluster, conf = detect_cluster_type(events)
    
    if strategy == "baseline":
        baselines = {
            "CLUSTER_3_CPI": 2.5,
            "CLUSTER_2_NFP": baseline_cluster2,
            "CLUSTER_1_MFG": baseline_cluster1
        }
        return baselines.get(cluster, 2.5)
    
    elif strategy == "dynamic":
        if cluster == "CLUSTER_3_CPI":
            return amp_dynamic_cluster3(context)
        elif cluster == "CLUSTER_2_NFP":
            return amp_dynamic_cluster2(context)
        elif cluster == "CLUSTER_1_MFG":
            return amp_dynamic_cluster1(context)
        else:
            return 2.5
```

**Tests** : `tests/test_cluster_detection.py`

### 6.4 Documentation finale

**Guides** :
- `USER_GUIDE_PLANIFICATEUR_V2.7.md`
- `TECHNICAL_DOCUMENTATION_V2.7.md`
- `API_REFERENCE_V2.7.md`

**Durée Partie 6** : Session 108-109 (~6-8 heures)

---

**FIN DU COMPLÉMENT**
