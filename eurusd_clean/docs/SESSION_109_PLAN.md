# SESSION 109 - ANALYSE EXHAUSTIVE MÉTRIQUES & CORRÉLATIONS

**Date prévue :** Session après Session 108  
**Type :** PARENTHÈSE MÉTHODOLOGIQUE  
**Objectif :** Identifier MEILLEURS outils mathématiques avant application

---

## 🎯 CONTEXTE

### État Post-Session 108

**Acquis :**
- ✅ 17 dates testées (6 C#3 + 11 C#1)
- ✅ Méthode Inversion validée (100% détection)
- ✅ Mesure impact fiable (Session 106)
- ✅ amp_optimal calculé pour 17 dates
- ❌ R² linéaire ne prédit pas amp (r=+0.084, p=0.75)

**Questions André (3 nov 2025) :**

**Question 1 :**
> "Est-ce que la formule servant à établir les caractéristiques des tendances est la seule existant mathématiquement parlant ou existe-t-il d'autres variantes ?"

**Réponse :** NON. R² linéaire n'est qu'UNE méthode parmi 10+ alternatives.

**Question 2 :**
> "Est-ce que la formule servant à calculer la corrélation entre la tendance et l'établissement du calcul du facteur d'amplification est unique ou en existe-t-il d'autres potentiellement plus pertinentes mais que nous n'avons pas testées ?"

**Réponse :** NON. Pearson linéaire n'est qu'UNE méthode parmi 8+ alternatives.

### Constat Critique

**On a peut-être utilisé les MAUVAIS outils mathématiques !**

**Exemple :**
- R² linéaire = 0.08 (faible)
- MAIS ADX = 60 (fort) → Tendance forte non-linéaire !
- MAIS Spearman = +0.45 (modéré) → Relation monotone courbe !

**→ Risque : passer à côté d'une vraie relation par mauvais choix d'outils**

### Décision Méthodologique

**André (3 nov 2025) :**
> "Ne devrait-on pas plutôt faire l'analyse exhaustive avant de tester au petit bonheur la chance une méthode parmi d'autres ?"

**✅ APPROUVÉ**

**Ordre rigoureux :**
1. ✅ Identifier tous instruments mesure disponibles
2. ✅ Tester tous systématiquement
3. ✅ Sélectionner MEILLEURS
4. ✅ PUIS les utiliser pour baseline C#1 et suite

**vs mauvaise approche :**
1. ❌ Choisir R² au hasard
2. ❌ Tout faire avec
3. ❌ Découvrir qu'ADX était mieux
4. ❌ Tout refaire

---

## 🎯 OBJECTIF SESSION 109

### Objectif Principal

**Identifier LA meilleure combinaison :**
- **Métrique tendance** : Parmi 12 candidates
- **Méthode corrélation** : Parmi 8 candidates
- **→ 96 combinaisons à tester**

### Critères Succès

**Scénario 1 : Jackpot ✅✅✅**
```
Métrique X + Corrélation Y : r > 0.6, p < 0.01
→ Excellente relation trouvée !
→ Implémentation prioritaire Session 110
```

**Scénario 2 : Modéré ✅**
```
Métrique Z + Corrélation W : r = 0.4-0.6, p < 0.05
→ Relation significative mais modérée
→ À comparer avec amp par cluster
```

**Scénario 3 : Rien ❌**
```
Toutes combinaisons : p > 0.05
→ AUCUNE variable ne prédit amp
→ Confirme Session 108
→ Retour amp par cluster fixe
→ MAIS on SAIT qu'on a tout testé !
```

### Ce Qu'On Va Savoir Après

**Questions résolues :**
- ✅ Existe-t-il UNE métrique tendance qui prédit amp ?
- ✅ Quelle est la MEILLEURE méthode corrélation ?
- ✅ Y a-t-il relation non-linéaire (U inversé, exponentielle) ?
- ✅ Faut-il retourner à amp par cluster fixe ?

**Décision éclairée :**
- Si métrique trouvée → Session 110 : Implémentation
- Si rien → Session 110 : Amp par cluster (Option A)

---

## 📋 PLAN DÉTAILLÉ SESSION 109

### Phase 1 : Calcul Métriques Tendance (2-3h)

#### Objectif
Calculer 12 métriques différentes caractérisant la tendance pour les 17 dates.

#### Métriques à Calculer

**A. Linéaires (4 métriques)**

1. **R² linéaire** (actuel)
```python
from scipy.stats import linregress
slope, intercept, r_value, p_value, std_err = linregress(X, y)
r2_linear = r_value ** 2
```

2. **R Pearson** (avec signe ±)
```python
r_pearson = r_value  # -1 à +1
# Garde info direction (UP/DOWN)
```

3. **Pente** (pips/heure)
```python
slope_pips_per_hour = slope * 10000 * 3600
# Vitesse tendance
```

4. **Durée tendance** (heures)
```python
duration_hours = (query_dt - reversal_datetime).total_seconds() / 3600
# Déjà calculé Session 107-108
```

**B. Non-Linéaires (3 métriques)**

5. **R² polynomial degré 2**
```python
coeffs = np.polyfit(X, y, deg=2)
y_pred = np.polyval(coeffs, X)
ss_res = np.sum((y - y_pred)**2)
ss_tot = np.sum((y - np.mean(y))**2)
r2_poly2 = 1 - (ss_res / ss_tot)
```

6. **R² polynomial degré 3**
```python
coeffs = np.polyfit(X, y, deg=3)
# Idem calcul R²
```

7. **Spearman Rho** (rank correlation)
```python
from scipy.stats import spearmanr
rho, p_value = spearmanr(X, y)
rho_squared = rho ** 2
# Corrélation rang (monotone, pas forcément linéaire)
```

**C. Trading Standard (3 métriques)**

8. **ADX (Average Directional Index)**
```python
from ta.trend import ADXIndicator
df_trend['adx'] = ADXIndicator(
    df_trend['high'], 
    df_trend['low'], 
    df_trend['close'], 
    window=14
).adx()
adx_value = df_trend['adx'].iloc[-1]  # 0-100
# Standard trading : ADX > 25 = tendance forte
```

9. **Amplitude tendance** (pips)
```python
amplitude_pips = (df_trend['high'].max() - df_trend['low'].min()) * 10000
# Déjà calculé Session 107-108
```

10. **Volatilité tendance** (std pips)
```python
volatility_pips = df_trend['close'].std() * 10000
# Écart-type prix
```

**D. Statistiques Avancées (2 métriques)**

11. **Hurst Exponent** (persistance)
```python
from hurst import compute_Hc
H, c, data = compute_Hc(df_trend['close'].values)
# H < 0.5 : Mean-reverting
# H = 0.5 : Random walk
# H > 0.5 : Trending (persistent)
```

12. **Autocorrélation Lag 1**
```python
from statsmodels.tsa.stattools import acf
autocorr_lag1 = acf(df_trend['close'].values, nlags=1, fft=False)[1]
# Mesure mémoire série temporelle
# Proche 1 : forte persistance
# Proche 0 : pas de mémoire
```

#### Script à Créer

**Fichier :** `eurusd_clean/scripts/session109/phase1_compute_all_metrics.py`

**Structure :**
```python
#!/usr/bin/env python3
"""
SESSION 109 - PHASE 1 : CALCUL MÉTRIQUES TENDANCE
==================================================
Calculer 12 métriques caractérisant tendance pour 17 dates
"""

# 1. Charger données Session 108
df_c3 = pd.read_csv('../session107/cluster3_inversion_analysis.csv')
df_c1 = pd.read_csv('../session108/cluster1_inversion_analysis.csv')

# 2. Pour chaque date
results = []
for date in all_dates:
    # Récupérer données tendance (prix depuis inversion)
    df_trend = get_trend_data(date)
    
    # Calculer 12 métriques
    metrics = {
        'date': date,
        'r2_linear': calculate_r2_linear(df_trend),
        'r_pearson': calculate_r_pearson(df_trend),
        'slope_pips_hour': calculate_slope(df_trend),
        'duration_hours': ...,  # Déjà dans CSV
        'r2_poly2': calculate_r2_poly(df_trend, deg=2),
        'r2_poly3': calculate_r2_poly(df_trend, deg=3),
        'rho_spearman': calculate_spearman(df_trend),
        'adx': calculate_adx(df_trend),
        'amplitude_pips': ...,  # Déjà dans CSV
        'volatility_pips': calculate_volatility(df_trend),
        'hurst': calculate_hurst(df_trend),
        'autocorr_lag1': calculate_autocorr(df_trend)
    }
    results.append(metrics)

# 3. Sauvegarder
df_metrics = pd.DataFrame(results)
df_metrics.to_csv('phase1_all_metrics_17dates.csv', index=False)
```

#### Résultat Phase 1

**Fichier généré :** `phase1_all_metrics_17dates.csv`

**Structure :**
```csv
date,r2_linear,r_pearson,slope_pips_hour,...,hurst,autocorr_lag1
2025-09-11,0.6376,+0.7985,+12.5,...,0.68,0.85
2025-08-12,0.4288,-0.6549,-8.3,...,0.55,0.72
...
(17 lignes × 14 colonnes : date + amp_optimal + 12 métriques)
```

#### Validation Phase 1

**Tests :**
1. ✅ 17 lignes (toutes dates)
2. ✅ 14 colonnes (date + amp_optimal + 12 métriques)
3. ✅ Pas de NaN (sauf si métrique impossible)
4. ✅ Valeurs cohérentes (R² entre 0-1, ADX entre 0-100, etc.)
5. ✅ Reproduction r2_linear Session 108 (validation)

---

### Phase 2 : Test Corrélations (1-2h)

#### Objectif
Tester 8 méthodes corrélation pour chaque des 12 métriques vs amp_optimal.

#### Méthodes Corrélation à Tester

**A. Corrélations Classiques (3 méthodes)**

1. **Pearson** (linéaire)
```python
from scipy.stats import pearsonr
r_p, p_p = pearsonr(metric_values, amp_optimal)
```

2. **Spearman** (monotone)
```python
from scipy.stats import spearmanr
rho_s, p_s = spearmanr(metric_values, amp_optimal)
```

3. **Kendall Tau** (robuste)
```python
from scipy.stats import kendalltau
tau_k, p_k = kendalltau(metric_values, amp_optimal)
```

**B. Régressions (3 méthodes)**

4. **Linéaire** (y = ax + b)
```python
from scipy.stats import linregress
slope, intercept, r, p, std_err = linregress(metric_values, amp_optimal)
r2_linear = r ** 2
```

5. **Polynomiale deg 2** (y = ax² + bx + c)
```python
coeffs = np.polyfit(metric_values, amp_optimal, deg=2)
y_pred = np.polyval(coeffs, metric_values)
r2_poly2 = 1 - (np.sum((amp_optimal - y_pred)**2) / 
                 np.sum((amp_optimal - np.mean(amp_optimal))**2))
```

6. **Polynomiale deg 3** (y = ax³ + bx² + cx + d)
```python
# Idem deg 2
```

**C. Métriques Avancées (2 méthodes)**

7. **Distance Correlation**
```python
from scipy.spatial.distance import pdist, squareform
# Capte dépendances non-linéaires complexes
# Implémentation : dcor library
```

8. **Mutual Information**
```python
from sklearn.metrics import mutual_info_score
from sklearn.feature_selection import mutual_info_regression
mi = mutual_info_regression(
    metric_values.reshape(-1, 1), 
    amp_optimal
)[0]
```

#### Script à Créer

**Fichier :** `eurusd_clean/scripts/session109/phase2_test_all_correlations.py`

**Structure :**
```python
#!/usr/bin/env python3
"""
SESSION 109 - PHASE 2 : TEST CORRÉLATIONS
==========================================
Tester 8 méthodes corrélation pour 12 métriques vs amp_optimal
→ 96 combinaisons
"""

# 1. Charger métriques Phase 1
df = pd.read_csv('phase1_all_metrics_17dates.csv')

# 2. Liste métriques à tester
metrics = [
    'r2_linear', 'r_pearson', 'slope_pips_hour', 'duration_hours',
    'r2_poly2', 'r2_poly3', 'rho_spearman',
    'adx', 'amplitude_pips', 'volatility_pips',
    'hurst', 'autocorr_lag1'
]

# 3. Pour chaque métrique
results = []
for metric in metrics:
    X = df[metric].values
    y = df['amp_optimal'].values
    
    # Test 8 corrélations
    result = {
        'metric': metric,
        # Classiques
        'pearson_r': pearsonr(X, y)[0],
        'pearson_p': pearsonr(X, y)[1],
        'spearman_rho': spearmanr(X, y)[0],
        'spearman_p': spearmanr(X, y)[1],
        'kendall_tau': kendalltau(X, y)[0],
        'kendall_p': kendalltau(X, y)[1],
        # Régressions
        'linear_r2': linregress(X, y).rvalue**2,
        'linear_p': linregress(X, y).pvalue,
        'poly2_r2': calculate_poly_r2(X, y, deg=2),
        'poly3_r2': calculate_poly_r2(X, y, deg=3),
        # Avancées
        'distance_corr': calculate_distance_corr(X, y),
        'mutual_info': mutual_info_regression(X.reshape(-1,1), y)[0]
    }
    results.append(result)

# 4. Sauvegarder
df_results = pd.DataFrame(results)
df_results.to_csv('phase2_correlation_matrix_96.csv', index=False)

# 5. Trier par performance
df_sorted = df_results.sort_values('spearman_p').head(10)
print("\nTOP 10 COMBINAISONS (par p-value Spearman) :")
print(df_sorted[['metric', 'spearman_rho', 'spearman_p']])
```

#### Résultat Phase 2

**Fichier généré :** `phase2_correlation_matrix_96.csv`

**Structure :**
```csv
metric,pearson_r,pearson_p,spearman_rho,spearman_p,...
r2_linear,+0.084,0.7487,+0.125,0.6234,...
r_pearson,+0.105,0.6832,...
adx,+0.456,0.0623,...
hurst,+0.523,0.0301,...
...
(12 lignes × 13 colonnes)
```

#### Validation Phase 2

**Tests :**
1. ✅ 12 lignes (toutes métriques)
2. ✅ 13 colonnes (metric + 12 résultats corrélation)
3. ✅ P-values entre 0-1
4. ✅ Corrélations entre -1 et +1
5. ✅ Reproduction Pearson r=+0.084 pour r2_linear (validation)

---

### Phase 3 : Identification Top 3 (30min)

#### Objectif
Sélectionner les 3 meilleures combinaisons selon critères rigoureux.

#### Critères Sélection

**Ordre priorité :**

1. **P-value < 0.05** (significativité statistique)
   - Élimine combinaisons non significatives
   
2. **|r| ou R² maximal** (force relation)
   - Parmi significatives, prendre plus forte
   
3. **Robustesse** (performant C#1 ET C#3)
   - Calculer corrélation sur C#1 seul
   - Calculer corrélation sur C#3 seul
   - Vérifier cohérence
   
4. **Interprétabilité** (compréhensible)
   - Préférer métriques interprétables (ADX, Pente)
   - vs complexes (Distance Corr, MI)

#### Script à Créer

**Fichier :** `eurusd_clean/scripts/session109/phase3_select_top3.py`

**Structure :**
```python
#!/usr/bin/env python3
"""
SESSION 109 - PHASE 3 : SÉLECTION TOP 3
========================================
Identifier 3 meilleures combinaisons
"""

# 1. Charger résultats Phase 2
df = pd.read_csv('phase2_correlation_matrix_96.csv')

# 2. Filtrer significatives (p < 0.05)
significant = df[
    (df['pearson_p'] < 0.05) |
    (df['spearman_p'] < 0.05) |
    (df['linear_p'] < 0.05)
]

print(f"Combinaisons significatives : {len(significant)}/12")

# 3. Trier par force (R² ou |rho|)
df['best_corr'] = df[['pearson_r', 'spearman_rho']].abs().max(axis=1)
top10 = df.sort_values('best_corr', ascending=False).head(10)

# 4. Test robustesse (C#1 vs C#3)
for idx, row in top10.iterrows():
    metric = row['metric']
    
    # Corrélation sur C#1 seulement
    corr_c1 = spearmanr(df_c1[metric], df_c1['amp_optimal'])[0]
    
    # Corrélation sur C#3 seulement
    corr_c3 = spearmanr(df_c3[metric], df_c3['amp_optimal'])[0]
    
    print(f"{metric}: Global={row['spearman_rho']:.3f}, "
          f"C#1={corr_c1:.3f}, C#3={corr_c3:.3f}")

# 5. Sélection finale Top 3
print("\n" + "="*80)
print("TOP 3 COMBINAISONS FINALES :")
print("="*80)
for i, (idx, row) in enumerate(top10.head(3).iterrows(), 1):
    print(f"\n{i}. {row['metric']}")
    print(f"   Spearman rho : {row['spearman_rho']:+.3f}")
    print(f"   P-value      : {row['spearman_p']:.4f}")
    print(f"   Linéaire R²  : {row['linear_r2']:.4f}")
    print(f"   Poly 2 R²    : {row['poly2_r2']:.4f}")
```

#### Résultat Phase 3

**Fichier généré :** `phase3_top3_combinations.txt`

**Contenu exemple :**
```
TOP 3 COMBINAISONS FINALES :

1. hurst + Spearman
   Spearman rho : +0.523
   P-value      : 0.0301
   Linéaire R²  : 0.2734
   Poly 2 R²    : 0.3456
   Robustesse   : C#1=+0.489, C#3=+0.556
   
2. adx + Spearman
   Spearman rho : +0.456
   P-value      : 0.0623
   Linéaire R²  : 0.2078
   Poly 2 R²    : 0.2891
   Robustesse   : C#1=+0.423, C#3=+0.478
   
3. autocorr_lag1 + Polynomial 2
   Spearman rho : +0.389
   P-value      : 0.1123
   Poly 2 R²    : 0.3201
   Robustesse   : C#1=+0.356, C#3=+0.412
```

---

### Phase 4 : Validation & Décision (1-2h)

#### Objectif
Valider Top 3 et décider quelle méthode utiliser pour suite.

#### Tests Validation

**A. Graphiques Scatter**
```python
import matplotlib.pyplot as plt

for metric in top3:
    plt.figure(figsize=(10, 6))
    plt.scatter(df[metric], df['amp_optimal'], 
                c=['blue']*6 + ['red']*11,  # C#3 bleu, C#1 rouge
                alpha=0.6)
    plt.xlabel(metric)
    plt.ylabel('amp_optimal')
    plt.title(f'{metric} vs amp_optimal')
    
    # Ligne régression
    plot_regression_line(df[metric], df['amp_optimal'])
    
    plt.savefig(f'validation_{metric}.png')
```

**B. Comparaison Baseline**

Si Top 1 significatif (p < 0.05) :
```python
# Formule dynamique
amp_predicted = calculate_amp_from_metric(metric_value)

# vs Baseline par cluster
amp_baseline_c1 = 1.5
amp_baseline_c3 = 2.5

# Calculer MAE
mae_dynamic = mean_absolute_error(amp_optimal, amp_predicted)
mae_baseline = mean_absolute_error(amp_optimal, amp_baseline_cluster)

improvement = (mae_baseline - mae_dynamic) / mae_baseline * 100
print(f"Amélioration : {improvement:+.1f}%")
```

#### Décision Finale

**Critères décision :**

**SI Top 1 avec p < 0.05 ET amélioration > 20% :**
```
✅ ADOPTER FORMULE DYNAMIQUE
→ Session 110 : Implémentation formule
→ Calculer baseline C#1 avec cette métrique
```

**SI Top 1 avec p < 0.05 MAIS amélioration < 20% :**
```
⚠️ GAIN MARGINAL
→ Comparer complexité vs gain
→ Peut-être rester amp par cluster fixe
```

**SI Aucune p < 0.05 :**
```
❌ AUCUNE RELATION SIGNIFICATIVE
→ Confirme Session 108
→ Retour amp par cluster fixe (Option A)
→ MAIS on SAIT qu'on a tout testé !
```

#### Résultat Phase 4

**Fichier généré :** `phase4_decision_finale.md`

**Contenu :**
```markdown
# DÉCISION FINALE SESSION 109

## Meilleure Combinaison

**Métrique :** [hurst / adx / autre]
**Corrélation :** [Spearman / Polynomial / autre]
**Performance :**
- Rho / R² : X.XXX
- P-value : 0.0XXX
- Amélioration vs baseline : +XX%

## Décision

[✅ ADOPTER / ⚠️ GAIN MARGINAL / ❌ RETOUR CLUSTER FIXE]

## Justification

[Explication détaillée]

## Prochaine Étape

Session 110 : [Implémentation formule / Baseline C#1 / Amp par cluster]
```

---

## 📊 RÉSULTATS ATTENDUS

### Scénario 1 : Jackpot ✅✅✅

**Exemple :**
```
MEILLEURE : ADX + Spearman
- Rho : +0.68
- P-value : 0.003
- Amélioration : +45%

→ Formule : amp = f(ADX) significative
→ Implémentation prioritaire Session 110
```

### Scénario 2 : Modéré ✅

**Exemple :**
```
MEILLEURE : Hurst + Polynomial 2
- R² : 0.35
- P-value : 0.04
- Amélioration : +15%

→ Relation faible mais significative
→ À comparer avec amp par cluster
```

### Scénario 3 : Rien ❌

**Exemple :**
```
MEILLEURE : Autocorr + Spearman
- Rho : +0.18
- P-value : 0.48
- Pas d'amélioration

→ Aucune variable ne prédit amp
→ Retour amp par cluster fixe
→ Mais on a tout testé !
```

---

## 📂 FICHIERS GÉNÉRÉS SESSION 109

### Scripts

```
eurusd_clean/scripts/session109/
├── phase1_compute_all_metrics.py      ← Calcul 12 métriques
├── phase2_test_all_correlations.py    ← Test 96 combinaisons
├── phase3_select_top3.py              ← Sélection Top 3
├── phase4_validate_decision.py        ← Validation & décision
└── utils_metrics.py                   ← Fonctions utilitaires
```

### Données

```
eurusd_clean/scripts/session109/
├── phase1_all_metrics_17dates.csv           ← 12 métriques × 17 dates
├── phase2_correlation_matrix_96.csv         ← 96 combinaisons
├── phase3_top3_combinations.txt             ← Top 3
├── phase4_decision_finale.md                ← Décision
└── graphs/
    ├── validation_hurst.png
    ├── validation_adx.png
    └── correlation_matrix_heatmap.png
```

### Documentation

```
eurusd_clean/docs/
├── SESSION_109_REPORT.md              ← Rapport session (à créer fin)
└── session_reports/
    └── SESSION_109_SYNTHESE.md        ← Synthèse (à créer fin)
```

---

## ⏱️ TEMPS ESTIMÉ

| Phase | Activité | Temps |
|-------|----------|-------|
| **Phase 1** | Calcul métriques | 2-3h |
| **Phase 2** | Test corrélations | 1-2h |
| **Phase 3** | Sélection Top 3 | 30min |
| **Phase 4** | Validation & décision | 1-2h |
| **Documentation** | Rapports fin session | 1h |
| **TOTAL** | **Session complète** | **5-8h** |

**Possibilité découpage :**
- **Session 109a (4h) :** Phases 1-2 (calculs automatisés)
- **Session 109b (3h) :** Phases 3-4 + Documentation

---

## 🎯 CHECKLIST SESSION 109

### Avant Démarrage

- [ ] Lire SESSION_109_PLAN.md (ce fichier)
- [ ] Lire METHODOLOGIES_ALTERNATIVES.md (catalogue complet)
- [ ] Lire MESSAGE_SESSION_108_TO_109.md (handoff)
- [ ] Vérifier données Session 108 disponibles
- [ ] Budget tokens : ~190,000 disponibles

### Phase 1 (Métriques)

- [ ] Créer phase1_compute_all_metrics.py
- [ ] Implémenter 12 métriques
- [ ] Tester sur 1 date validation
- [ ] Exécuter sur 17 dates
- [ ] Vérifier phase1_all_metrics_17dates.csv
- [ ] Valider reproduction r2_linear Session 108

### Phase 2 (Corrélations)

- [ ] Créer phase2_test_all_correlations.py
- [ ] Implémenter 8 méthodes corrélation
- [ ] Exécuter 96 combinaisons
- [ ] Vérifier phase2_correlation_matrix_96.csv
- [ ] Valider reproduction Pearson r=+0.084 pour r2_linear

### Phase 3 (Top 3)

- [ ] Créer phase3_select_top3.py
- [ ] Filtrer p < 0.05
- [ ] Trier par force corrélation
- [ ] Tester robustesse (C#1 vs C#3)
- [ ] Générer phase3_top3_combinations.txt

### Phase 4 (Validation)

- [ ] Créer phase4_validate_decision.py
- [ ] Générer graphiques scatter
- [ ] Calculer amélioration vs baseline
- [ ] Prendre décision finale
- [ ] Documenter phase4_decision_finale.md

### Fin Session

- [ ] Créer SESSION_109_REPORT.md
- [ ] Créer SESSION_109_SYNTHESE.md
- [ ] Mettre à jour PROJECT_STATE.md
- [ ] Créer MESSAGE_SESSION_109_TO_110.md
- [ ] Sauvegarder tous fichiers générés

---

## 💡 PRINCIPES MÉTHODOLOGIQUES

### Rigueur Scientifique

1. **Test systématique** : 96 combinaisons, pas de choix arbitraire
2. **Significativité** : P-value < 0.05 obligatoire
3. **Robustesse** : Validation sur sous-groupes (C#1, C#3)
4. **Reproductibilité** : Tous scripts documentés
5. **Transparence** : Documenter succès ET échecs

### Si Rien Trouvé

**Ce n'est PAS un échec :**
- ✅ On a testé scientifiquement
- ✅ On SAIT que rien ne marche
- ✅ On retourne à amp par cluster en connaissance de cause
- ✅ Pas de "et si on avait essayé X ?"

### Documentation Continue

- Afficher tokens régulièrement
- Documenter au fur et à mesure
- Arrêter à 160k tokens pour documenter fin
- Ne pas attendre fin pour écrire rapports

---

## 🚨 ERREURS À ÉVITER

### Pièges Méthodologiques

1. ❌ **Ne tester que quelques métriques** : Tester TOUTES
2. ❌ **Accepter p > 0.05** : Exiger significativité
3. ❌ **Ignorer robustesse** : Valider sur C#1 ET C#3
4. ❌ **Over-interpréter** : R²=0.35 ≠ "excellent"
5. ❌ **Oublier baseline** : Toujours comparer avec amp par cluster

### Pièges Techniques

1. ❌ **Outliers non gérés** : Vérifier métriques robustes
2. ❌ **Division par zéro** : Gérer cas limites
3. ❌ **NaN propagation** : Vérifier toutes valeurs
4. ❌ **Timezone errors** : Utiliser données Session 108 (validées)
5. ❌ **Overfitting** : N=17 petit, méfiance formules complexes

---

## 📞 SUPPORT DOCUMENTATION

### Fichiers Référence

**À lire AVANT Session 109 :**
1. SESSION_109_PLAN.md (ce fichier)
2. METHODOLOGIES_ALTERNATIVES.md
3. MESSAGE_SESSION_108_TO_109.md
4. SESSION_108_REPORT.md
5. PROJECT_STATE.md

**Données Session 108 :**
1. `session107/cluster3_inversion_analysis.csv` (6 dates C#3)
2. `session108/cluster1_inversion_analysis.csv` (11 dates C#1)
3. `session108/calibration_inversion_17dates.csv` (comparaisons)

---

## 🏁 APRÈS SESSION 109

### Si Métrique Trouvée

**Session 110 :**
- Implémentation formule amp = f(métrique)
- Baseline C#1 avec meilleure métrique
- Tests sur 17 dates
- Validation robustesse
- Intégration Planificateur

### Si Rien Trouvé

**Session 110 :**
- Retour Option A (amp par cluster fixe)
- Baseline C#1 = 1.5 (moyenne 11 dates)
- Tests comparatifs
- Intégration Planificateur
- **Décision éclairée : on a tout testé**

---

**FIN SESSION_109_PLAN.md**

*Document créé : 3 novembre 2025*  
*Parenthèse méthodologique critique*  
*96 combinaisons à tester - Rigueur scientifique*
