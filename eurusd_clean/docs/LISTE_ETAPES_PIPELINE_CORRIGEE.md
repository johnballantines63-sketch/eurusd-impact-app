# Liste des Étapes du Pipeline - Version Corrigée

## ⚠️ CORRECTIONS IMPORTANTES IDENTIFIÉES

### 1. ÉTAPE 2 : Fenêtre Temporelle APRÈS les Événements Déclencheurs
**❌ ERREUR ACTUELLE** : La fenêtre est définie avant les événements  
**✅ CORRECTION** : La fenêtre doit être définie APRÈS les événements déclencheurs du mouvement

### 2. TIMINGS PARFAITS MANQUANTS
**❌ PROBLÈME** : Les timings parfaits (T+5, T+11, T+15, T+40) ne sont pas utilisés  
**✅ SOLUTION** : Utiliser `predict_double_wave_timeline_s64()` pour Double Wave avec timings fixes validés (0.00 min erreur)

---

## 📋 LISTE DES 8 ÉTAPES (CORRIGÉE)

### ÉTAPE 1 : CHARGER ÉVÉNEMENTS
**Méthode** : `etape1_charger_evenements`

**Objectif** : Charger tous les événements économiques pour une date donnée depuis la base de données.

**Sources** :
- Table `events` (Finnhub)
- Filtrage par date et pays (US, EU, DE)
- Seuil `min_empirical_score` : 29.0 (US/EU), 20.0 (DE)

**Sortie** : DataFrame avec colonnes :
- `event_key`, `event_title`, `ts_utc`, `actual`, `estimate`, `forecast`, `previous`
- `country`, `importance_n`, `empirical_score`, `family`

**✅ VALIDATION** : Vérifier nombre d'événements chargés, présence des événements attendus

---

### ÉTAPE 2 : DÉTECTER CLUSTERS
**Méthode** : `etape2_detecter_clusters`

**Objectif** : Grouper les événements qui se produisent dans une fenêtre temporelle.

**⚠️ CORRECTION CRITIQUE** :
- **Fenêtre temporelle définie APRÈS les événements déclencheurs**
- Les événements déclencheurs sont ceux qui causent le mouvement
- La fenêtre capture les événements qui suivent le déclencheur principal

**Méthode** :
- Fenêtre glissante de 30 minutes par défaut
- **Anchor time** : Premier événement déclencheur (CPI/NFP typiquement)
- **Fenêtre** : [anchor_time, anchor_time + 30 min] pour capturer événements simultanés

**Paramètres** :
- `window_minutes` : 30 (défaut)

**Sortie** : Liste de clusters avec :
- `events` : DataFrame des événements du cluster
- `anchor_time` : Heure d'ancrage du cluster (premier événement déclencheur)
- `n_events` : Nombre d'événements

**✅ VALIDATION** : Vérifier que la fenêtre est bien APRÈS l'anchor_time, pas avant

---

### ÉTAPE 3 : DÉFINIR NOYAU DUR
**Méthode** : `etape3_definir_noyau_dur`

**Objectif** : Identifier les événements "core" qui apparaissent fréquemment ensemble dans l'historique.

**Méthode** :
- Analyse de fréquence sur 5 ans d'historique
- Calcul du support (fréquence d'apparition) pour chaque événement
- **Pour événements spécifiques** : Support dans clusters du même type (CPI/NFP)
- **Pour événements génériques** : Support dans TOUS les clusters
- Filtrage par seuil adaptatif :
  - Support >= 60% : core
  - OU (support >= 40% ET importance <= 2) : core
  - OU (support >= 20% ET générique récurrent) : core

**Paramètres** :
- `support_threshold` : 0.60 (60% de fréquence)
- `years_lookback` : 5 ans

**Sortie** : Cluster info avec :
- `core_events` : Liste des identifiants des événements du noyau dur
- `n_core_events` : Nombre d'événements core
- `n_total_events` : Nombre total d'événements
- `support_scores` : Scores de support pour chaque événement
- `core_type` : Type de noyau dur ('CPI', 'NFP', ou 'GENERIC')

**✅ VALIDATION** : Vérifier que les événements importants (Jobless Claims, etc.) sont inclus

---

### ÉTAPE 4 : RECHERCHER CLUSTERS IDENTIQUES
**Méthode** : `etape4_rechercher_clusters_identiques`

**Objectif** : Trouver des clusters historiques avec le même noyau dur pour utiliser leurs impacts réels.

**Méthode** :
- Similarité Jaccard entre noyaux durs
- Recherche sur 5 ans d'historique
- Filtrage par heure d'événement (±10 minutes)

**Paramètres** :
- `jaccard_threshold` : 0.60 (60% de similarité)
- `years_lookback` : 5 ans

**Calcul Jaccard** :
```
J(A, B) = |A ∩ B| / |A ∪ B|
```

**Sortie** : Liste de clusters identiques avec :
- `date` : Date du cluster historique
- `jaccard_similarity` : Score de similarité (0.0-1.0)
- `cluster` : Cluster historique complet
- `core_events` : Événements du noyau dur

**✅ VALIDATION** : Vérifier pourquoi 0 clusters trouvés (si applicable), scores Jaccard

---

### ÉTAPE 5 : CALCULER TENDANCES
**Méthode** : `etape5_calculer_tendances_impacts`

**Objectif** : Détecter et mesurer les tendances pré-événement pour chaque cluster identique.

**Méthode** : `detect_trend_by_inversion_s107` (multi-timeframe)

**Timeframes testées** : M1, M5, M15, M30, H1

**Critères de détection** :
- `min_hours_before_event` : 12 heures
- `min_duration_hours` : 6.0 heures (M30, H1) ou 8 heures (M1, M5, M15)
- `lookback_days` : 14 jours
- `min_r2` : 0.15
- `min_amplitude_pips` : 15.0

**Méthode de détection** : Validated Inversion (Session 107)
- Détection d'inversion majeure avant l'événement
- Régression linéaire sur la tendance
- Calcul de R², amplitude, durée

**Sortie** : DataFrame avec pour chaque cluster :
- `cluster_date` : Date du cluster
- `trend_exists` : Booléen
- `r2` : Coefficient de détermination
- `amplitude_pips` : Amplitude de la tendance
- `duration_hours` : Durée de la tendance
- `direction` : UP ou DOWN
- `timeframe_used` : Timeframe utilisée

**✅ VALIDATION** : Vérifier nombre de tendances détectées, R² moyen, amplitude moyenne

---

### ÉTAPE 6 : CALCULER IMPACTS BASE & AMPLIFICATIONS
**Méthode** : `etape6_calculer_impacts_base_amplifications`

**Objectif** : Calculer l'impact de base (formule) et l'amplification parfaite (réel/base) pour chaque cluster historique.

**Formule d'impact de base** : `calculate_impact_d`
- Somme des impacts individuels des événements
- Correction avec facteur empirique (0.758)
- Ajustements selon importance et scores

**Amplification parfaite** :
```
amplification_parfaite = impact_reel / impact_base
```

**Mesure d'impact réel** :
- Utilise détection de pattern réel (Double Wave detector)
- Détection du pic réel dans la fenêtre post-événement
- Direction UP ou DOWN selon le mouvement dominant

**Sortie** : DataFrame avec :
- `cluster_date` : Date du cluster
- `impact_base` : Impact calculé par formule
- `impact_reel` : Impact réel mesuré
- `amplification_parfaite` : Ratio réel/base

**✅ VALIDATION** : Vérifier nombre d'impacts calculés, impact moyen, amplification moyenne

---

### ÉTAPE 7 : ANALYSER RELATION TENDANCE → AMPLIFICATION
**Méthode** : `etape7_analyser_relation_tendance_amplification`

**Objectif** : Analyser la corrélation entre les métriques de tendance et l'amplification pour prédire l'amplification du cluster cible.

**Méthodes** :
1. **Corrélations** : R², durée, amplitude vs amplification
2. **Modèle linéaire** : Régression multivariée (si >= 5 clusters)
3. **Random Forest par date** : Si >= 5 clusters identiques
4. **Random Forest global** : Fallback si pas assez de clusters
5. **Moyenne historique** : Fallback final

**Features pour Random Forest** :
- `trend_r2` : R² de la tendance
- `trend_duration_h` : Durée en heures
- `trend_amplitude_pips` : Amplitude en pips
- `trend_direction_encoded` : Direction (1=UP, -1=DOWN)
- `max_surprise_pct` : Surprise maximale
- `mean_surprise_pct` : Surprise moyenne
- `num_events` : Nombre d'événements
- `mean_empirical_score` : Score empirique moyen
- `impact_base_pips` : Impact de base
- `pattern_impact_pips` : Impact du pattern (si disponible)

**Sortie** : Dict avec :
- `correlations` : Dict des corrélations
- `results_df` : DataFrame fusionné (trends + impacts)

**✅ VALIDATION** : Vérifier corrélations, modèle RF entraîné, features utilisées

---

### ÉTAPE 8 : APPLIQUER CLUSTER CIBLE
**Méthode** : `etape8_appliquer_cluster_cible`

**Objectif** : Appliquer toutes les analyses au cluster cible pour prédire l'impact final.

**Sous-étapes** :

#### 8.1 : Calcul de l'Impact de Base
- **Méthode standard** : Somme des impacts individuels × 0.758
- Utilise `calculate_impact_d` avec les événements du cluster cible

#### 8.2 : Détection de Tendance
- Utilise `detect_trend_by_inversion_s107` pour le cluster cible
- Même méthode que Étape 5
- Timeframe par défaut : M30

#### 8.3 : Prédiction d'Amplification
**Hiérarchie** :
1. **Random Forest par date** (si >= 5 clusters identiques)
2. **Random Forest global** (si modèle entraîné)
3. **Modèle linéaire** (si >= 5 clusters)
4. **Moyenne historique** (fallback)

#### 8.4 : Ajustements Support/Résistance
- Calcul distance aux niveaux S/R
- Ajustement selon proximité et type de breakout

#### 8.5 : Ajustements Patterns Finnhub
- Détection patterns Finnhub proches
- Ajustement selon validation/invalidation

#### 8.6 : Détection de Pattern de Prix
**⚠️ CRITIQUE : TIMINGS PARFAITS**

**Méthode** :
1. **Détecter conditions Double Wave** :
   - Surprise > 20% ET cluster >= 5 événements
   - Utilise `detect_double_wave_conditions()`

2. **Si Double Wave détecté** :
   - ✅ **UTILISER `predict_double_wave_timeline_s64()`**
   - ✅ **TIMINGS PARFAITS** : T+5, T+11, T+15, T+40 (0.00 min erreur)
   - ✅ **RATIOS SESSION 64** : Phase 1 (58%), Pullback (84%), Phase 2 (90%)
   - ✅ **Confidence 100%** car timings validés

3. **Si Single Wave Fort détecté** :
   - Utilise `predict_single_wave_timeline()` (Session 67)
   - Timings : T+8 (peak), T+15 (pullback), T+25 (stabilisation)

4. **Sinon** :
   - Détection pattern réelle avec `detect_for_date_duckdb_rev12()`
   - Timings détectés (peuvent avoir erreur)

**Timings Parfaits Double Wave (Session 64)** :
- **Phase 1 peak** : T+5 min → **0.00 min erreur** ✅
- **Creux pullback** : T+11 min → **0.00 min erreur** ✅
- **Phase 2 peak** : T+15 min → **0.00 min erreur** ✅
- **Stabilisation** : T+40 min → **0.00 min erreur** ✅

**Ratios Validés Session 64** :
- Phase 1 : 58% de l'impact total
- Pullback : 84% retrace de Phase 1
- Phase 2 : 90% de l'impact total

#### 8.7 : Stratégie Hybride Pattern/Formules
**Logique** :
- Comparaison `impact_formules` vs `pattern_impact`
- **Pour Double Wave** :
  - Si formules suspectes (amplification < 0.5x OU impact < pattern*0.3) → utiliser pattern
  - Sinon → utiliser formules
- **Pour Single Wave** :
  - Si écart < 10 pips → formules
  - Si écart >= 10 pips → pattern
- **Pour autres** :
  - Si écart < 10 pips → formules
  - Si écart >= 10 pips → pattern

#### 8.8 : Calcul du Target de Sortie
- Exit target = 80% de la prédiction finale
- Limite maximale 1.5x

**Sortie** : Dict final avec :
- `impact_base` : Impact de base calculé
- `amplification_predite` : Amplification prédite
- `prediction_finale` : Impact prédit final (en pips)
- `prediction_method` : Méthode utilisée ('formulas' ou 'pattern')
- `exit_target` : Target de sortie optimisé
- `pattern_type` : Type de pattern détecté
- `pattern_info` : Détails du pattern
- `timings_predicted` : Booléen (True si timings Session 64 utilisés)
- `pattern_wave1_peak_time` : T+5 min (si Double Wave)
- `pattern_pullback_low_time` : T+11 min (si Double Wave)
- `pattern_wave2_peak_time` : T+15 min (si Double Wave)
- `pattern_stabilization_time` : T+40 min (si Double Wave)
- `trend_exists` : Tendance détectée
- `trend_r2` : R² de la tendance
- `trend_direction` : Direction de la tendance
- `trend_amplitude_pips` : Amplitude de la tendance

**✅ VALIDATION** : Vérifier chaque sous-étape, logique de sélection finale, timings prédits

---

## 📄 RÉFÉRENCES DOCUMENTATION

### Documentation Principale
- `docs/PIPELINE_REFERENCE/PIPELINE_REFERENCE_COMPLETE.md` : Documentation complète de référence
- `docs/PIPELINE_COMPLET_EXHAUSTIF.md` : Description exhaustive avec chemins conditionnels
- `docs/VALIDATION_SESSION_2025_01_XX/INTEGRATION_TIMING_PARFAITS.md` : Intégration timings parfaits
- `docs/VALIDATION_SESSION_2025_01_XX/SCRIPTS_TIMING_PARFAITS.md` : Scripts avec timings parfaits
- `docs/SESSION64_RAPPORT_COMPLET.md` : Rapport Session 64 avec timings parfaits

### Fonctions Clés
- `src/core/double_wave.py` : `detect_double_wave_conditions()`, `predict_double_wave_timeline()`
- `scripts/run_pipeline_complete.py` : Toutes les méthodes `etape[1-8]_*`

---

## ⚠️ PROBLÈMES IDENTIFIÉS À VÉRIFIER

1. **Étape 2** : Vérifier que la fenêtre est bien APRÈS l'anchor_time
2. **Étape 8.6** : Vérifier que `predict_double_wave_timeline_s64()` est appelée pour Double Wave
3. **Étape 8.6** : Vérifier que les timings parfaits (T+5, T+11, T+15, T+40) sont utilisés
4. **Étape 8.7** : Vérifier la logique de sélection pattern vs formules pour Double Wave
5. **Étape 8.1** : Vérifier quelle méthode est utilisée (standard ou Session 88)

---

## ✅ PROCHAINES ÉTAPES

1. Exécuter pipeline étape par étape avec pause après chaque étape
2. Vérifier chaque résultat avant de passer à la suivante
3. Identifier où les timings parfaits sont perdus
4. Corriger les problèmes identifiés




