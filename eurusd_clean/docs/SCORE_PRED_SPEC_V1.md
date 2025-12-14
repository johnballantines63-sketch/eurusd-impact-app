# 🎯 SCORE_PRED_SPEC_V1 – Score prédictif ex-ante (no leakage)

**Date** : 2025-12-12  
**Version** : SCORE_PRED_SPEC_V1  
**Scope** : Score prédictif utilisable **AVANT** l'événement pour prédire la volatilité post-event

---

## ⚠️ ENCADRÉ : Ce document rend le modèle audit-proof (no leakage)

Cette spécification garantit qu'**aucune information post-release** n'est utilisée dans le calcul du score prédictif. Toutes les métriques basées sur les prix réalisés (`impact_unified_pips`, `score_impact_v1`, etc.) sont explicitement interdites.

**Pourquoi c'est crucial** :
- Un modèle qui utilise `impact_unified_pips` pour prédire la volatilité est **tautologique** (il prédit avec ce qu'il cherche à prédire).
- Un score vraiment prédictif doit être calculable **avant** que l'événement ne se produise.
- Cette spécification permet un **audit rigoureux** : toute violation des règles anti-leakage est immédiatement détectable.

---

## 1. Objectif

Définir un **score prédictif ex-ante** (`score_pred_v1`) qui :

- Est calculable **avant** la release de l'événement macro-économique
- Prédit la volatilité EURUSD post-event sans utiliser d'informations post-release
- Sert de base pour :
  - Modèles de prédiction de volatilité
  - Dashboards d'alerte "journée à risque"
  - Stratégies de trading pré-event

**Distinction clé** :
- `score_impact_v1` (SCORE_SPEC_V1) = score **rétrospectif** basé sur l'impact réalisé
- `score_pred_v1` (SCORE_PRED_SPEC_V1) = score **prédictif** basé uniquement sur des features ex-ante

---

## 2. Anti-leakage : métriques interdites

### 2.1. Métriques explicitement interdites

Les métriques suivantes **ne doivent jamais** être utilisées dans le calcul de `score_pred_v1` :

❌ **Métriques basées sur les prix post-release** :
- `impact_unified_pips` (IMPACT_SPEC_V1)
- `impact_unified_direction`
- `impact_unified_time_to_peak_minutes`
- `impact_unified_start_price`, `impact_unified_peak_price`
- Toute métrique dérivée de `prices_finnhub_m1` dans la fenêtre post-event

❌ **Scores rétrospectifs** :
- `score_impact_v1` (SCORE_SPEC_V1)
- `score_impact_signed_v1`
- `score_bucket_v1` (LOW/MEDIUM/HIGH/EXTREME)

❌ **Surprise réalisée** :
- `surprise_pct` (calculée à partir de `actual` vs `forecast`)
- `actual` (valeur réalisée, disponible seulement après release)

### 2.2. Règle générale

**Toute métrique calculée à partir de données disponibles uniquement APRÈS la release de l'événement est interdite.**

---

## 3. Inputs autorisés (disponibles avant release)

### 3.1. Métadonnées événement (toujours disponibles)

Depuis la table `events` :

- `ts_utc` : timestamp UTC de l'événement
- `country` : pays (US, EU, GB, JP, etc.)
- `event_key` : identifiant normalisé de l'événement (ex: "non farm payrolls")
- `event_title` : titre descriptif
- `importance_n` : importance (typiquement 1-5, parfois NULL)
- `forecast` : prévision consensuelle (disponible avant release)
- `previous` : valeur précédente (historique)
- `estimate` : estimation alternative (si disponible)

### 3.2. Features calendrier (dérivées de `ts_utc`)

Ces features sont calculables **avant** l'événement :

- `weekday` : jour de la semaine (0=Monday, 6=Sunday)
- `month` : mois (1-12)
- `hour_utc` : heure UTC (0-23)
- `is_month_end` : booléen (dernier jour ouvrable du mois)
- `is_quarter_end` : booléen (dernier jour ouvrable du trimestre)
- `is_year_end` : booléen (dernier jour ouvrable de l'année)
- `day_of_month` : jour du mois (1-31)

### 3.3. Features de session (optionnel)

Dérivées de `hour_utc` et `country` :

- `session_bucket` : session de trading dominante
  - `'ASIA'` : heures UTC 00:00-08:00
  - `'EU'` : heures UTC 08:00-16:00
  - `'US'` : heures UTC 13:00-21:00
  - `'OVERLAP'` : chevauchements (EU/US notamment)
  - `'LOW_LIQUIDITY'` : autres heures

### 3.4. Features historiques agrégées (priors empiriques)

Ces features seront calculées dans une **vue dédiée** (`event_priors_v1`, à créer) :

- `event_key_prior` : impact moyen historique de ce `event_key` (sur événements passés)
- `country_prior` : impact moyen historique de ce `country`
- `event_key_country_prior` : impact moyen historique de la combinaison (event_key, country)
- `importance_prior` : impact moyen historique par niveau d'importance

**Note** : Ces priors sont calculés sur des données **historiques uniquement** (pas sur l'événement courant), donc ils sont disponibles avant la release.

---

## 4. Formule V1 (simple, interprétable)

### 4.1. Formule de base

```text
score_pred_v1 = importance_weight * (importance_n / 5.0)
                + event_key_prior
                + country_prior
                + calendar_prior
```

Où :

- `importance_weight` : poids de l'importance (scalaire, à calibrer empiriquement)
- `importance_n / 5.0` : normalisation de l'importance sur [0.2, 1.0] (si importance_n ∈ [1, 5])
- `event_key_prior` : prior empirique pour ce type d'événement (moyenne historique de `impact_unified_pips` pour ce `event_key`)
- `country_prior` : prior empirique pour ce pays (moyenne historique de `impact_unified_pips` pour ce `country`)
- `calendar_prior` : contribution des features calendrier (à définir, ex: bonus pour month_end, quarter_end)

### 4.2. Composantes détaillées

**Importance weight** :
```text
importance_weight = α (scalaire calibré empiriquement)
```

**Event key prior** :
```text
event_key_prior = β_event_key * log(1 + avg_impact_event_key)
```
Où `avg_impact_event_key` = moyenne historique de `impact_unified_pips` pour ce `event_key` (sur événements passés uniquement).

**Country prior** :
```text
country_prior = β_country * log(1 + avg_impact_country)
```
Où `avg_impact_country` = moyenne historique de `impact_unified_pips` pour ce `country`.

**Calendar prior** :
```text
calendar_prior = β_month_end * is_month_end
                + β_quarter_end * is_quarter_end
                + β_session * session_bucket_factor
                + ...
```

### 4.3. Paramètres à calibrer empiriquement

Les coefficients `α`, `β_event_key`, `β_country`, `β_month_end`, etc. seront estimés via :

- Régression linéaire sur données historiques
- Validation temporelle (train sur 2022-2023, test sur 2024-2025)
- Regularisation (L1/L2) pour éviter le sur-apprentissage

**Note V1** : Pour la première version, on peut utiliser des valeurs simples :
- `importance_weight = 1.0`
- `β_event_key = 1.0`
- `β_country = 0.5`
- `calendar_prior = 0` (à activer en V2)

---

## 5. Sorties attendues

### 5.1. Colonnes principales

La vue `events_with_pred_score_v1` (à créer) exposera :

- `ts_utc` : timestamp de l'événement
- `country`, `event_key`, `event_title` : métadonnées
- `importance_n` : importance
- `score_pred_v1` : score prédictif ex-ante (DOUBLE, ≥ 0)

### 5.2. Composantes (optionnel)

Pour la traçabilité et le debugging, on peut exposer :

- `score_pred_importance_component` : contribution de l'importance
- `score_pred_event_key_component` : contribution du prior event_key
- `score_pred_country_component` : contribution du prior country
- `score_pred_calendar_component` : contribution des features calendrier

Ou, plus compact :
- `score_pred_components` : JSON ou struct contenant les composantes

---

## 6. Vue de priors empiriques (à créer)

### 6.1. Vue `event_priors_v1`

Cette vue agrège les impacts historiques pour calculer les priors :

```sql
CREATE OR REPLACE VIEW event_priors_v1 AS
SELECT
    event_key,
    country,
    COUNT(*) AS n_historical_events,
    AVG(impact_unified_pips) AS avg_impact_event_key,
    MEDIAN(impact_unified_pips) AS p50_impact_event_key,
    AVG(impact_unified_pips) AS avg_impact_country,
    -- ... autres agrégations
FROM events_with_canonical_impact_v1
WHERE ts_utc < CURRENT_DATE  -- ⚠️ IMPORTANT : uniquement historique
GROUP BY event_key, country;
```

**Règle critique** : Les priors sont calculés uniquement sur des événements **passés** (avant la date courante), pour éviter tout leakage temporel.

---

## 7. Roadmap V2

### 7.1. Intégration de la surprise (post-release update)

En V2, on pourra ajouter un **score prédictif mis à jour** après la release :

```text
score_pred_v2_post_release = score_pred_v1 + surprise_component
```

Où `surprise_component` utilise `surprise_pct` (disponible seulement après release).

**Distinction claire** :
- `score_pred_v1` = score ex-ante (avant release)
- `score_pred_v2_post_release` = score mis à jour (après release, avec surprise)

### 7.2. Calibration empirique avancée

- Régression avec regularisation (Lasso/Ridge)
- Validation croisée temporelle
- Features non-linéaires (interactions, transformations)

### 7.3. Validation temporelle stricte

- Train sur période A (ex: 2022-2023)
- Test sur période B (ex: 2024-2025)
- Mesure de la dérive temporelle (concept drift)

### 7.4. Features additionnelles

- Co-occurrence d'événements (plusieurs événements le même jour)
- Saisonnalité (patterns mensuels/trimestriels)
- Sentiment macro (si données disponibles ex-ante)

---

## 8. Usage recommandé

### 8.1. Ce qu'on fait AVEC `score_pred_v1`

✅ **Prédiction de volatilité** :
- Modèle : `volatility_predicted = f(score_pred_v1, autres_features)`
- Dashboard : alerte "journée à risque" si `score_pred_v1 > seuil`

✅ **Ranking d'événements futurs** :
- Trier les événements à venir par `score_pred_v1` décroissant
- Identifier les événements les plus susceptibles de générer de la volatilité

✅ **Stratégies de trading pré-event** :
- Préparer des positions si `score_pred_v1` élevé
- Ajuster le sizing selon le niveau de `score_pred_v1`

### 8.2. Ce qu'on NE fait PAS avec V1

❌ Ne pas comparer directement `score_pred_v1` avec `score_impact_v1` :
- `score_pred_v1` = prédiction ex-ante
- `score_impact_v1` = mesure rétrospective

❌ Ne pas utiliser `score_pred_v1` pour expliquer la volatilité réalisée sans validation :
- V1 est une première version, nécessite validation empirique
- La corrélation `score_pred_v1` vs `daily_volatility_pips_v1` doit être mesurée et documentée

---

## 9. TL;DR (résumé opérationnel)

- **`score_pred_v1`** = score prédictif ex-ante, calculable avant la release de l'événement
- **Anti-leakage strict** : aucune métrique post-release (`impact_unified_pips`, `score_impact_v1`, `surprise_pct`)
- **Inputs autorisés** : métadonnées événement, features calendrier, priors historiques
- **Formule V1** : combinaison linéaire de l'importance, priors event_key/country, features calendrier
- **Usage** : prédiction de volatilité, ranking d'événements futurs, stratégies pré-event
- **Roadmap V2** : intégration surprise post-release, calibration empirique, validation temporelle

---

**Fin de SCORE_PRED_SPEC_V1**

