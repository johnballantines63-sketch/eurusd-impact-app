# SESSION 109 - CHECKLIST COMPLÈTE

**Date :** Session après Session 108  
**Type :** PARENTHÈSE MÉTHODOLOGIQUE - ANALYSE EXHAUSTIVE  
**Durée estimée :** 5-8h (possibilité découpage en 2 sessions)

---

## ✅ PHASE PRÉPARATION (30 min)

### Documentation Obligatoire

**À lire AVANT tout code :**

- [ ] **SESSION_109_PLAN.md** (plan 4 phases détaillé) ⭐⭐⭐
- [ ] **METHODOLOGIES_ALTERNATIVES.md** (catalogue 12 métriques + 8 corrélations) ⭐⭐⭐
- [ ] **MESSAGE_SESSION_108_TO_109.md** (handoff + contexte) ⭐⭐
- [ ] **SESSION_108_REPORT.md** (résultats Session 108) ⭐
- [ ] **PROJECT_STATE.md** (section Session 107-108) ⭐

**Résumé compris :**
- [ ] Questions André comprises (2 questions méthodologiques)
- [ ] Problème identifié (R² linéaire peut-être mauvais outil)
- [ ] Objectif session (tester 96 combinaisons)
- [ ] Critères succès (p < 0.05 significativité)

### Environnement Technique

**Installation librairies :**

```bash
# Vérifier installations
pip list | grep -E "scipy|ta|hurst|statsmodels|pygam|scikit-learn|dcor"

# Installer si manquant
pip install scipy
pip install ta  # Technical Analysis
pip install hurst
pip install statsmodels
pip install pygam
pip install scikit-learn
pip install dcor
```

- [ ] scipy installé (Pearson, Spearman, linregress)
- [ ] ta installé (ADX)
- [ ] hurst installé (Hurst Exponent)
- [ ] statsmodels installé (autocorrélation)
- [ ] pygam installé (GAM - optionnel)
- [ ] scikit-learn installé (Mutual Information)
- [ ] dcor installé (Distance Correlation - optionnel)

### Données Disponibles

**Vérifier présence fichiers :**

- [ ] `session107/cluster3_inversion_analysis.csv` (6 dates C#3)
- [ ] `session108/cluster1_inversion_analysis.csv` (11 dates C#1)
- [ ] `session108/calibration_inversion_17dates.csv` (17 dates complètes)
- [ ] Warehouse.duckdb accessible (pour extraction prix si besoin)

**Validation colonnes CSV :**
- [ ] Colonne `amp_optimal` présente (17 valeurs)
- [ ] Colonne `r2_inversion` présente (validation)
- [ ] Colonne `impact_real_pips` présente
- [ ] Pas de NaN critique

### Budget Session

- [ ] Tokens disponibles : ~190,000
- [ ] Objectif fin session : ~160,000 (30k pour documentation)
- [ ] Affichage tokens tous les 20k

---

## ✅ PHASE 1 : CALCUL MÉTRIQUES (2-3h)

### Script Creation

**Fichier :** `eurusd_clean/scripts/session109/phase1_compute_all_metrics.py`

**Structure minimale :**
- [ ] Imports (pandas, numpy, scipy, ta, hurst, statsmodels)
- [ ] Fonction load_trend_data(date, reversal_info)
- [ ] Fonction calculate_r2_linear(df_trend)
- [ ] Fonction calculate_r_pearson(df_trend)
- [ ] Fonction calculate_slope_pips_hour(df_trend)
- [ ] Fonction calculate_r2_poly(df_trend, deg=2)
- [ ] Fonction calculate_spearman(df_trend)
- [ ] Fonction calculate_adx(df_trend)
- [ ] Fonction calculate_volatility(df_trend)
- [ ] Fonction calculate_hurst(df_trend)
- [ ] Fonction calculate_autocorr(df_trend)
- [ ] Main loop 17 dates

### Métriques Implémentées

**A. Linéaires (4 métriques) :**

- [ ] **r2_linear** : R² régression linéaire (Session 108 existant)
- [ ] **r_pearson** : Corrélation Pearson avec signe ± (direction)
- [ ] **slope_pips_hour** : Pente en pips/heure (vitesse tendance)
- [ ] **duration_hours** : Durée tendance en heures (déjà dans CSV)

**B. Non-Linéaires (3 métriques) :**

- [ ] **r2_poly2** : R² polynomial degré 2 (parabole, U inversé)
- [ ] **r2_poly3** : R² polynomial degré 3 (cubique)
- [ ] **rho_spearman** : Spearman Rho au carré (monotone)

**C. Trading (3 métriques) :**

- [ ] **adx** : Average Directional Index (0-100, standard trading)
- [ ] **amplitude_pips** : Range pips (high-low, déjà dans CSV)
- [ ] **volatility_pips** : Écart-type prix en pips

**D. Avancées (2 métriques) :**

- [ ] **hurst** : Hurst Exponent (persistance, 0-1)
- [ ] **autocorr_lag1** : Autocorrélation lag 1 (mémoire série)

### Validation Phase 1

**Tests unitaires :**
- [ ] Test sur 1 date (ex: 2025-09-11)
- [ ] Vérifier r2_linear = Session 108 (validation)
- [ ] Vérifier ADX entre 0-100
- [ ] Vérifier Hurst entre 0-1
- [ ] Vérifier aucun NaN (sauf si métrique impossible)

**Exécution complète :**
- [ ] Exécuter sur 17 dates
- [ ] Temps exécution < 15 min
- [ ] Pas d'erreurs critiques

**Fichier généré :**
- [ ] `phase1_all_metrics_17dates.csv` créé
- [ ] 17 lignes (1 par date)
- [ ] 14 colonnes : date + amp_optimal + 12 métriques
- [ ] Colonnes : date, amp_optimal, r2_linear, r_pearson, slope_pips_hour, duration_hours, r2_poly2, r2_poly3, rho_spearman, adx, amplitude_pips, volatility_pips, hurst, autocorr_lag1
- [ ] Pas de NaN problématique
- [ ] Valeurs cohérentes (R² 0-1, ADX 0-100, etc.)

**Documentation Phase 1 :**
- [ ] Commentaires code (docstrings fonctions)
- [ ] Logging progression (print date par date)
- [ ] Note problèmes rencontrés (si erreurs)

---

## ✅ PHASE 2 : TEST CORRÉLATIONS (1-2h)

### Script Creation

**Fichier :** `eurusd_clean/scripts/session109/phase2_test_all_correlations.py`

**Structure minimale :**
- [ ] Load phase1_all_metrics_17dates.csv
- [ ] Liste métriques à tester (12)
- [ ] Fonction test_pearson(X, y)
- [ ] Fonction test_spearman(X, y)
- [ ] Fonction test_kendall(X, y)
- [ ] Fonction test_linear_regression(X, y)
- [ ] Fonction test_poly_regression(X, y, deg=2)
- [ ] Fonction test_distance_corr(X, y) - optionnel
- [ ] Fonction test_mutual_info(X, y) - optionnel
- [ ] Main loop 12 métriques × 8 tests

### Méthodes Corrélation Implémentées

**A. Corrélations Classiques (3 méthodes) :**

- [ ] **Pearson** : pearsonr(metric, amp_optimal) → r, p
- [ ] **Spearman** : spearmanr(metric, amp_optimal) → rho, p
- [ ] **Kendall** : kendalltau(metric, amp_optimal) → tau, p

**B. Régressions (3 méthodes) :**

- [ ] **Linéaire** : linregress(metric, amp_optimal) → r², p
- [ ] **Poly 2** : polyfit deg=2 → R² calculé manuellement
- [ ] **Poly 3** : polyfit deg=3 → R² calculé manuellement

**C. Avancées (2 méthodes - optionnel) :**

- [ ] **Distance Corr** : dcor.distance_correlation(metric, amp_optimal)
- [ ] **Mutual Info** : mutual_info_regression(metric, amp_optimal)

### Validation Phase 2

**Tests unitaires :**
- [ ] Test sur 1 métrique (ex: r2_linear)
- [ ] Vérifier Pearson r = Session 108 (validation)
- [ ] Vérifier p-values entre 0-1
- [ ] Vérifier corrélations entre -1 et +1

**Exécution complète :**
- [ ] Exécuter 96 tests (12 métriques × 8 corrélations)
- [ ] Temps exécution < 5 min
- [ ] Pas d'erreurs critiques

**Fichier généré :**
- [ ] `phase2_correlation_matrix_96.csv` créé
- [ ] 12 lignes (1 par métrique)
- [ ] 13 colonnes : metric + 12 résultats corrélation
- [ ] Colonnes : metric, pearson_r, pearson_p, spearman_rho, spearman_p, kendall_tau, kendall_p, linear_r2, linear_p, poly2_r2, poly3_r2, distance_corr, mutual_info
- [ ] P-values cohérentes (0-1)
- [ ] Corrélations cohérentes (-1 à +1)

**Analyse préliminaire :**
- [ ] Afficher TOP 5 métriques (par Spearman p-value)
- [ ] Identifier métriques p < 0.05 (significatives)
- [ ] Noter métriques prometteuses

**Documentation Phase 2 :**
- [ ] Logging progression
- [ ] Tableau récapitulatif console
- [ ] Note interprétations préliminaires

---

## ✅ PHASE 3 : SÉLECTION TOP 3 (30 min)

### Script Creation

**Fichier :** `eurusd_clean/scripts/session109/phase3_select_top3.py`

**Structure minimale :**
- [ ] Load phase2_correlation_matrix_96.csv
- [ ] Filtrer p < 0.05 (significatives)
- [ ] Trier par force corrélation (|r| ou R²)
- [ ] Calculer corrélation C#1 seul
- [ ] Calculer corrélation C#3 seul
- [ ] Vérifier cohérence (robustesse)
- [ ] Sélectionner Top 3

### Critères Sélection

**Ordre priorité :**

1. **Significativité statistique :**
   - [ ] Filtrer p < 0.05 au moins 1 méthode
   - [ ] Rejeter toutes p > 0.05

2. **Force corrélation :**
   - [ ] Calculer best_corr = max(|pearson_r|, |spearman_rho|)
   - [ ] Trier par best_corr décroissant
   - [ ] Sélectionner top 10

3. **Robustesse (C#1 vs C#3) :**
   - [ ] Pour chaque top 10 :
     - [ ] Calculer corr sur C#1 seul (11 dates)
     - [ ] Calculer corr sur C#3 seul (6 dates)
     - [ ] Vérifier cohérence signe (± même direction)
     - [ ] Vérifier magnitude similaire (pas écart 2x)

4. **Interprétabilité :**
   - [ ] Préférer métriques simples (ADX, Pente, Hurst)
   - [ ] vs complexes (Distance, MI) si performance égale

### Validation Phase 3

**Fichier généré :**
- [ ] `phase3_top3_combinations.txt` créé
- [ ] Top 3 identifiés avec :
  - [ ] Métrique utilisée
  - [ ] Méthode corrélation
  - [ ] Valeur corrélation (r ou rho)
  - [ ] P-value
  - [ ] R² (si régression)
  - [ ] Robustesse C#1 vs C#3

**Analyse qualitative :**
- [ ] Top 1 : Commentaire justification
- [ ] Top 2 : Commentaire justification
- [ ] Top 3 : Commentaire justification

**Documentation Phase 3 :**
- [ ] Tableau comparatif Top 10
- [ ] Graphique corrélations (optionnel)
- [ ] Justification sélection

---

## ✅ PHASE 4 : VALIDATION & DÉCISION (1-2h)

### Script Creation

**Fichier :** `eurusd_clean/scripts/session109/phase4_validate_decision.py`

**Structure minimale :**
- [ ] Load données Phases 1-3
- [ ] Pour Top 3 :
  - [ ] Générer scatter plot (metric vs amp_optimal)
  - [ ] Tracer ligne régression
  - [ ] Colorier C#1 vs C#3
  - [ ] Sauvegarder PNG
- [ ] Calculer amélioration vs baseline
- [ ] Décision finale

### Graphiques Validation

**Pour chaque Top 3 :**

- [ ] **Scatter plot** créé :
  - [ ] Points C#1 en rouge
  - [ ] Points C#3 en bleu
  - [ ] Ligne régression (si applicable)
  - [ ] Annotations r, p-value
  - [ ] Titre, axes, légende

- [ ] **Fichiers PNG** :
  - [ ] `validation_top1_[metric].png`
  - [ ] `validation_top2_[metric].png`
  - [ ] `validation_top3_[metric].png`

### Comparaison Baseline

**Si Top 1 significatif (p < 0.05) :**

- [ ] Calculer amp_predicted avec formule métrique
- [ ] Baseline par cluster :
  - [ ] C#1 : 1.45 (moyenne 11 dates)
  - [ ] C#3 : 2.55 (moyenne 6 dates)
- [ ] Calculer MAE formule dynamique
- [ ] Calculer MAE baseline cluster fixe
- [ ] Calculer amélioration % = (MAE_baseline - MAE_dynamic) / MAE_baseline × 100

**Critère décision :**
- [ ] Si amélioration > 20% → Adopter formule dynamique
- [ ] Si amélioration 10-20% → Gain marginal, à discuter
- [ ] Si amélioration < 10% → Rester cluster fixe

### Décision Finale

**Fichier :** `phase4_decision_finale.md`

**Contenu obligatoire :**
- [ ] **Meilleure combinaison** identifiée :
  - [ ] Métrique (ex: ADX, Hurst, etc.)
  - [ ] Méthode corrélation (ex: Spearman, Poly 2)
  - [ ] Performance (r, p-value, R²)
  - [ ] Amélioration vs baseline (%)
  
- [ ] **Décision** :
  - [ ] ✅ ADOPTER FORMULE DYNAMIQUE
  - [ ] ⚠️ GAIN MARGINAL (à discuter)
  - [ ] ❌ RETOUR CLUSTER FIXE
  
- [ ] **Justification** détaillée :
  - [ ] Arguments statistiques
  - [ ] Arguments pratiques
  - [ ] Arguments robustesse
  
- [ ] **Prochaine étape** Session 110 :
  - [ ] Implémentation formule (si adopté)
  - [ ] Baseline C#1 avec métrique (si adopté)
  - [ ] Ou amp par cluster fixe (si rejeté)

### Validation Phase 4

**Tests cohérence :**
- [ ] Graphiques cohérents avec statistiques
- [ ] Amélioration calculée correctement
- [ ] Décision justifiée par données

**Documentation :**
- [ ] Decision finale claire (1 page max)
- [ ] Graphiques explicites
- [ ] Arguments solides

---

## ✅ PHASE FINALISATION (1h)

### Documentation Complète

**Fichiers à créer :**

- [ ] **SESSION_109_REPORT.md** (rapport complet) :
  - [ ] Contexte et objectif
  - [ ] Méthodologie 4 phases
  - [ ] Résultats Phase 1 (12 métriques)
  - [ ] Résultats Phase 2 (96 tests)
  - [ ] Résultats Phase 3 (Top 3)
  - [ ] Résultats Phase 4 (Décision)
  - [ ] Conclusions
  - [ ] Leçons apprises

- [ ] **SESSION_109_SYNTHESE.md** (synthèse 1-2 pages) :
  - [ ] Question André → Réponse
  - [ ] Meilleure combinaison trouvée
  - [ ] Décision finale
  - [ ] Prochaine étape

- [ ] **MESSAGE_SESSION_109_TO_110.md** (handoff) :
  - [ ] Résumé exécutif
  - [ ] Fichiers générés
  - [ ] Décision finale
  - [ ] Instructions Session 110
  - [ ] Checklist démarrage

### Mise à Jour PROJECT_STATE

**Section SESSION 109 à ajouter :**
- [ ] Titre et date
- [ ] Objectif et résultat
- [ ] Réalisations clés
- [ ] Découvertes majeures
- [ ] Fichiers générés
- [ ] Décision finale
- [ ] Prochaine étape

**Vérifications :**
- [ ] Cohérence avec sessions précédentes
- [ ] Progression % mise à jour
- [ ] Liens vers fichiers corrects

### Sauvegarde et Archivage

**Fichiers générés à vérifier :**

- [ ] **Scripts** :
  - [ ] phase1_compute_all_metrics.py
  - [ ] phase2_test_all_correlations.py
  - [ ] phase3_select_top3.py
  - [ ] phase4_validate_decision.py
  - [ ] utils_metrics.py (si créé)

- [ ] **Données** :
  - [ ] phase1_all_metrics_17dates.csv
  - [ ] phase2_correlation_matrix_96.csv
  - [ ] phase3_top3_combinations.txt
  - [ ] phase4_decision_finale.md

- [ ] **Graphiques** :
  - [ ] validation_top1_*.png
  - [ ] validation_top2_*.png
  - [ ] validation_top3_*.png
  - [ ] correlation_matrix_heatmap.png (optionnel)

- [ ] **Documentation** :
  - [ ] SESSION_109_REPORT.md
  - [ ] SESSION_109_SYNTHESE.md
  - [ ] MESSAGE_SESSION_109_TO_110.md

**Backup :**
- [ ] Copie sécurité scripts/ avant modifications
- [ ] Copie sécurité docs/ avant mise à jour

---

## ⚠️ CRITÈRES QUALITÉ

### Rigueur Scientifique

- [ ] **Test exhaustif** : 96 combinaisons testées (pas de choix arbitraire)
- [ ] **Significativité** : Seuil p < 0.05 respecté strictement
- [ ] **Robustesse** : Validation sur C#1 ET C#3 séparément
- [ ] **Reproductibilité** : Tous scripts documentés et reproductibles
- [ ] **Transparence** : Succès ET échecs documentés

### Métriques Session

- [ ] **Tokens** : < 160,000 (30k réservés pour doc finale)
- [ ] **Durée** : 5-8h (1 session ou 2 sessions courtes)
- [ ] **Fichiers** : 4 scripts + 4 données + 3 docs minimum
- [ ] **Tests** : 96 combinaisons minimum (peut être plus)
- [ ] **Décision** : 1 décision claire documentée

### Critères Succès Session

**Scénario 1 : Métrique trouvée ✅**
- [ ] Au moins 1 combinaison p < 0.05
- [ ] Amélioration > 20% vs baseline
- [ ] Décision : Adopter formule dynamique
- [ ] Prochaine session : Implémentation

**Scénario 2 : Gain marginal ⚠️**
- [ ] Au moins 1 combinaison p < 0.05
- [ ] Amélioration 10-20% vs baseline
- [ ] Décision : À discuter avec André
- [ ] Prochaine session : TBD

**Scénario 3 : Rien trouvé ❌**
- [ ] Aucune combinaison p < 0.05
- [ ] Ou amélioration < 10%
- [ ] Décision : Retour amp par cluster
- [ ] Prochaine session : Baseline C#1 fixe
- [ ] **NOTE :** CE N'EST PAS UN ÉCHEC ! On a testé scientifiquement.

---

## 🚨 ERREURS À NE PAS COMMETTRE

### Erreurs Méthodologiques

- [ ] ❌ Tester seulement 3-4 métriques → ✅ Tester TOUTES (12)
- [ ] ❌ Accepter p = 0.06 comme "presque" → ✅ Rejeter si p > 0.05
- [ ] ❌ Ignorer validation C#1/C#3 → ✅ Tester robustesse
- [ ] ❌ Sur-interpréter R²=0.35 → ✅ R²=0.35 = modéré, pas excellent
- [ ] ❌ Ne pas comparer à baseline → ✅ Toujours calculer amélioration

### Erreurs Techniques

- [ ] ❌ Ne pas gérer NaN → ✅ Vérifier toutes métriques
- [ ] ❌ Division par zéro → ✅ Ajouter checks (if x != 0)
- [ ] ❌ Outliers extrêmes → ✅ Vérifier distributions
- [ ] ❌ Timezone incorrecte → ✅ Utiliser données Session 108 (validées)
- [ ] ❌ Overfitting (deg 4+) → ✅ Limiter à deg 3 maximum

### Erreurs Documentation

- [ ] ❌ Pas de rapport final → ✅ SESSION_109_REPORT.md obligatoire
- [ ] ❌ Décision floue → ✅ Décision CLAIRE (1 des 3 options)
- [ ] ❌ Pas de mise à jour PROJECT_STATE → ✅ Section 109 ajoutée
- [ ] ❌ Fichiers non sauvegardés → ✅ Backup + archivage

---

## 📞 EN CAS DE PROBLÈME

### Problèmes Fréquents

**1. Librairie manquante :**
```bash
# Erreur : ModuleNotFoundError: No module named 'xxx'
pip install xxx
```

**2. ADX returns NaN :**
```python
# Solution : window=14 nécessite 14+ points minimum
if len(df_trend) < 14:
    adx_value = np.nan  # Accepter NaN pour tendances courtes
```

**3. Hurst échoue :**
```python
# Solution : Hurst nécessite 100+ points
if len(df_trend) < 100:
    hurst_value = np.nan
```

**4. Distance Corr lente :**
```python
# Solution : dcor peut être lent, prévoir 5-10 min
# Optionnel si tokens limités
```

### Budget Tokens Dépassé

**Si > 160,000 tokens utilisés :**
- [ ] ARRÊTER immédiatement toute analyse
- [ ] Créer documentation minimale :
  - [ ] phase4_decision_finale.md (obligatoire)
  - [ ] Message handoff Session 110 (obligatoire)
  - [ ] Mise à jour PROJECT_STATE (obligatoire)
- [ ] Reporter documentation complète à Session 110

---

## 🏁 CHECKLIST FIN SESSION

### Avant de Terminer

**Vérifications finales :**
- [ ] Tous fichiers CSV générés et vérifiés
- [ ] Tous graphiques PNG créés
- [ ] Décision finale documentée et claire
- [ ] SESSION_109_REPORT.md complet
- [ ] PROJECT_STATE.md mis à jour
- [ ] MESSAGE_SESSION_109_TO_110.md créé
- [ ] Tokens utilisés : ______ / 190,000 (____%)

**Résultats clés documentés :**
- [ ] Nombre combinaisons significatives (p < 0.05) : ______
- [ ] Top 1 combinaison : [métrique] + [corrélation]
- [ ] Performance Top 1 : r = ______, p = ______
- [ ] Amélioration vs baseline : ______%
- [ ] Décision finale : [ADOPTER / MARGINAL / REJETER]

**Prochaine session :**
- [ ] Session 110 mission claire et documentée
- [ ] Fichiers nécessaires identifiés
- [ ] Instructions démarrage dans handoff

### Validation Qualité

**Scientifique :**
- [ ] 96 combinaisons testées (minimum 12 métriques × 8 corrélations)
- [ ] P-value < 0.05 respecté strictement
- [ ] Robustesse validée (C#1 et C#3 séparément)
- [ ] Transparence : Succès et échecs documentés

**Technique :**
- [ ] Code reproductible (scripts commentés)
- [ ] Pas d'erreurs critiques
- [ ] Données cohérentes (pas de NaN problématiques)
- [ ] Graphiques clairs et explicites

**Documentation :**
- [ ] Rapport complet (SESSION_109_REPORT.md)
- [ ] Synthèse claire (SESSION_109_SYNTHESE.md)
- [ ] Handoff détaillé (MESSAGE_SESSION_109_TO_110.md)
- [ ] PROJECT_STATE à jour

---

**🎉 SESSION 109 COMPLÈTE !**

**Ce qui a été accompli :**
1. ✅ Analyse exhaustive 96 combinaisons
2. ✅ Identification meilleurs outils mathématiques
3. ✅ Décision éclairée pour approche future
4. ✅ Documentation scientifique rigoureuse

**Ce qu'on sait maintenant :**
- ✅ Si relation métrique ↔ amp existe (ou non)
- ✅ Quelle métrique est meilleure (si existe)
- ✅ Quelle corrélation est meilleure (si existe)
- ✅ Quelle approche adopter : Dynamique vs Cluster fixe

**C'était une PARENTHÈSE méthodologique critique, pas une perte de temps.**

**Prochaine étape :** Session 110 avec les BONS outils identifiés !

---

**FIN SESSION_109_CHECKLIST.md**

*Document créé : 3 novembre 2025*  
*Checklist exhaustive : 4 phases + finalisation*  
*Rigueur scientifique garantie*
