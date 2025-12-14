# Liste des Étapes du Pipeline - Selon Documentation de Référence

## Vue d'ensemble
Pipeline en **8 étapes** pour prédire l'impact des événements économiques sur EUR/USD.

---

## ÉTAPE 1 : CHARGER ÉVÉNEMENTS
**Méthode** : `etape1_charger_evenements`

**Objectif** : Charger tous les événements économiques pour une date donnée depuis la base de données.

**Sources** :
- Table `events` (Finnhub)
- Filtrage par date et pays (US, EU, DE)
- Seuil `min_empirical_score` : 29.0 (US/EU), 20.0 (DE)

**Sortie** : DataFrame avec colonnes :
- `event_key`, `event_title`, `ts_utc`, `actual`, `estimate`, `forecast`, `previous`
- `country`, `importance_n`, `empirical_score`, `family`

**Validation attendue** :
- Nombre d'événements chargés
- Présence des événements CPI/NFP attendus
- Colonnes requises présentes

---

## ÉTAPE 2 : DÉTECTER CLUSTERS
**Méthode** : `etape2_detecter_clusters`

**Objectif** : Grouper les événements qui se produisent dans une fenêtre temporelle.

**Méthode** :
- Fenêtre glissante de 30 minutes par défaut
- Groupement par heure d'ancrage (anchor_time)
- Calcul du nombre d'événements par cluster

**Paramètres** :
- `window_minutes` : 30 (défaut)

**Sortie** : Liste de clusters avec :
- `events` : DataFrame des événements du cluster
- `anchor_time` : Heure d'ancrage du cluster (premier événement)
- `n_events` : Nombre d'événements

**Validation attendue** :
- Nombre de clusters détectés
- Événements dans chaque cluster
- Anchor time de chaque cluster

---

## ÉTAPE 3 : DÉFINIR NOYAU DUR
**Méthode** : `etape3_definir_noyau_dur`

**Objectif** : Identifier les événements "core" qui apparaissent fréquemment ensemble dans l'historique.

**Méthode** :
- Analyse de fréquence sur 5 ans d'historique
- Calcul du support (fréquence d'apparition) pour chaque événement
- Filtrage par seuil de support (0.60 par défaut)
- Support de noyaux durs pré-définis (CPI, NFP)

**Paramètres** :
- `support_threshold` : 0.60 (60% de fréquence)
- `years_lookback` : 5 ans

**Logique adaptative** :
- Support >= 60% : core
- OU (support >= 40% ET importance <= 2) : core
- OU (support >= 20% ET générique récurrent) : core

**Sortie** : Cluster info avec :
- `core_events` : Liste des identifiants des événements du noyau dur
- `n_core_events` : Nombre d'événements core
- `n_total_events` : Nombre total d'événements
- `support_scores` : Scores de support pour chaque événement
- `core_type` : Type de noyau dur ('CPI', 'NFP', ou 'GENERIC')

**Validation attendue** :
- Type de noyau dur détecté (CPI/NFP/GENERIC)
- Nombre d'événements core vs total
- Support de chaque événement
- Événements inclus/exclus

---

## ÉTAPE 4 : RECHERCHER CLUSTERS IDENTIQUES
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

**Validation attendue** :
- Nombre de clusters identiques trouvés
- Scores Jaccard des clusters trouvés
- Dates des clusters historiques
- Si 0 clusters : raison possible

---

## ÉTAPE 5 : CALCULER TENDANCES
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

**Validation attendue** :
- Nombre de tendances détectées
- R² moyen des tendances
- Amplitude moyenne
- Direction des tendances

---

## ÉTAPE 6 : CALCULER IMPACTS BASE & AMPLIFICATIONS
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

**Validation attendue** :
- Nombre d'impacts calculés
- Impact de base moyen
- Impact réel moyen
- Amplification parfaite moyenne

---

## ÉTAPE 7 : ANALYSER RELATION TENDANCE → AMPLIFICATION
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

**Sortie** : Dict avec :
- `correlations` : Dict des corrélations
- `results_df` : DataFrame fusionné (trends + impacts)

**Validation attendue** :
- Corrélations calculées
- Modèle RF entraîné (si applicable)
- Features utilisées
- Résultats DataFrame

---

## ÉTAPE 8 : APPLIQUER CLUSTER CIBLE
**Méthode** : `etape8_appliquer_cluster_cible`

**Objectif** : Appliquer toutes les analyses au cluster cible pour prédire l'impact final.

**Sous-étapes** :

### 8.1 : Calcul de l'Impact de Base
- Méthode standard : Somme des impacts individuels × 0.758
- OU Méthode Session 88 : Score moyen ajusté avec surprise MAX

### 8.2 : Détection de Tendance
- Utilise `detect_trend_by_inversion_s107` pour le cluster cible
- Même méthode que Étape 5

### 8.3 : Prédiction d'Amplification
**Hiérarchie** :
1. Random Forest par date (si >= 5 clusters identiques)
2. Random Forest global (si modèle entraîné)
3. Modèle linéaire (si >= 5 clusters)
4. Moyenne historique (fallback)

### 8.4 : Ajustements Support/Résistance
- Calcul distance aux niveaux S/R
- Ajustement selon proximité

### 8.5 : Ajustements Patterns Finnhub
- Détection patterns Finnhub proches
- Ajustement selon validation/invalidation

### 8.6 : Détection de Pattern de Prix
- Détection Double Wave / Single Wave
- Utilise `detect_for_date_duckdb_rev12`
- Calcul impact du pattern détecté

### 8.7 : Stratégie Hybride Pattern/Formules
- Comparaison `impact_formules` vs `pattern_impact`
- Choix selon écart et type de pattern

### 8.8 : Calcul du Target de Sortie
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
- `trend_exists` : Tendance détectée
- `trend_r2` : R² de la tendance
- `trend_direction` : Direction de la tendance
- `trend_amplitude_pips` : Amplitude de la tendance

**Validation attendue** :
- Impact de base
- Amplification prédite et méthode utilisée
- Pattern détecté et son impact
- Prédiction finale et méthode
- Exit target

---

## Points de Validation Critiques

1. **Étape 1** : Vérifier que tous les événements attendus sont chargés
2. **Étape 2** : Vérifier que le cluster principal est correctement identifié
3. **Étape 3** : Vérifier que le noyau dur inclut les événements importants
4. **Étape 4** : Vérifier pourquoi 0 clusters identiques (si applicable)
5. **Étape 5** : Vérifier que les tendances sont détectées correctement
6. **Étape 6** : Vérifier que les impacts réels sont mesurés correctement
7. **Étape 7** : Vérifier que l'amplification est prédite correctement
8. **Étape 8** : Vérifier chaque sous-étape et la logique de sélection finale




