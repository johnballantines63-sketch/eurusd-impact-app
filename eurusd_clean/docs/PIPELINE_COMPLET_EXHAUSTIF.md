# Pipeline Complet - Description Exhaustive avec Chemins Conditionnels

**Date** : Documentation exhaustive  
**Objectif** : Décrire TOUTES les étapes et TOUS les chemins conditionnels du pipeline

---

## 🚀 MÉTHODE PRINCIPALE : `execute_complete_pipeline`

**Fichier** : `scripts/run_pipeline_complete.py`  
**Lignes** : 1922-2091

### Flux d'exécution

```
execute_complete_pipeline(date_str, window_minutes=30, support_threshold=0.8, jaccard_threshold=0.60, years_lookback=5)
│
├─> Étape 1 : Charger événements
│   └─> Si aucun événement → RETURN {success: False, error: "Aucun événement trouvé"}
│
├─> Étape 2 : Détecter clusters
│   └─> Si aucun cluster → RETURN {success: False, error: "Aucun cluster détecté"}
│
├─> Sélection cluster principal
│   ├─> Priorité 1 : Cluster US HIGH impact (empirical_score > 50) à 14:25-14:35
│   └─> Priorité 2 : Cluster le plus grand (max n_events)
│
├─> Étape 3 : Définir noyau dur
├─> Étape 4 : Rechercher clusters identiques
├─> Étape 5 : Calculer tendances
├─> Étape 6 : Calculer impacts base & amplifications
├─> Étape 7 : Analyser relation tendance → amplification
├─> Étape 8 : Appliquer cluster cible
│
└─> RETURN {success: True, final_prediction: {...}, results: {...}}
```

---

## 📋 ÉTAPE 1 : CHARGER ÉVÉNEMENTS

**Méthode** : `etape1_charger_evenements`  
**Lignes** : 108-174

### Paramètres
- `date_str` : Date au format 'YYYY-MM-DD'
- `countries` : Liste des pays (défaut: ['US', 'EU', 'DE'])

### Logique

```
Pour chaque pays dans ['US', 'EU', 'DE']:
│
├─> Déterminer seuil min_score:
│   ├─> Si country == 'DE' → min_score = 20.0
│   └─> Sinon (US/EU) → min_score = 29.0
│
├─> Charger événements avec load_high_impact_events:
│   ├─> db_path: self.db_path
│   ├─> target_date: date_str convertie en datetime
│   ├─> country: pays actuel
│   ├─> min_empirical_score: min_score (20.0 ou 29.0)
│   └─> verbose: False
│
├─> Si événements trouvés:
│   ├─> Ajouter colonne 'country' = pays actuel
│   ├─> Ajouter à all_events[]
│   └─> Log: "✅ X événements chargés (pays, seuil: X)"
│
└─> Si erreur → Log warning, continuer avec pays suivant

Si all_events vide:
└─> RETURN pd.DataFrame() vide

Sinon:
├─> Concaténer tous les événements
├─> Trier par ts_utc
└─> RETURN df_events
```

### Colonnes retournées
- `event_key`, `event_title`, `ts_utc`, `actual`, `estimate`, `forecast`, `previous`
- `country`, `importance_n`, `empirical_score`, `family`

---

## 📋 ÉTAPE 2 : DÉTECTER CLUSTERS

**Méthode** : `etape2_detecter_clusters`  
**Lignes** : 180-245

### Paramètres
- `df_events` : DataFrame des événements
- `window_minutes` : Fenêtre de groupement (défaut: 30)

### Logique

```
Si df_events vide:
└─> RETURN []

Sinon:
├─> Convertir ts_utc en datetime
├─> Initialiser processed_indices = set()
│
├─> Pour chaque événement (idx, row) dans df_events:
│   │
│   ├─> Si idx déjà dans processed_indices:
│   │   └─> CONTINUER (skip)
│   │
│   ├─> Définir fenêtre:
│   │   ├─> window_start = row['ts_utc']
│   │   └─> window_end = window_start + timedelta(minutes=window_minutes)
│   │
│   ├─> Trouver tous événements dans fenêtre:
│   │   ├─> mask = (ts_utc >= window_start) & (ts_utc < window_end)
│   │   └─> cluster_events = df_events[mask]
│   │
│   ├─> Si cluster_events non vide:
│   │   ├─> anchor_time = premier événement (cluster_events.iloc[0]['ts_utc'])
│   │   ├─> Créer cluster dict:
│   │   │   ├─> 'events': cluster_events
│   │   │   ├─> 'anchor_time': anchor_time
│   │   │   └─> 'n_events': len(cluster_events)
│   │   ├─> Ajouter à clusters[]
│   │   └─> Marquer tous les indices comme traités
│   │
│   └─> CONTINUER avec événement suivant
│
├─> Trier clusters par anchor_time
└─> RETURN clusters[]
```

### Résultat
Liste de clusters avec :
- `events` : DataFrame des événements du cluster
- `anchor_time` : Heure d'ancrage (premier événement)
- `n_events` : Nombre d'événements

---

## 📋 ÉTAPE 3 : DÉFINIR NOYAU DUR

**Méthode** : `etape3_definir_noyau_dur`  
**Lignes** : 251-375

### Paramètres
- `cluster` : Cluster avec events et anchor_time
- `support_threshold` : Seuil de support (défaut: 0.8)
- `years_lookback` : Années de lookback (non utilisé actuellement)

### Logique

```
cluster_events = cluster['events']
anchor_time = cluster['anchor_time']

Créer identifiants canoniques pour chaque événement:
├─> event_id = f"{event_key_normalized}_{country}_{importance}"
└─> event_keys_normalized[] = event_key en lowercase

Compter événements CPI et NFP:
├─> CPI_PATTERN = r'(?i)(cpi|consumer price|inflation rate|core inflation|harmonised inflation)'
├─> NFP_PATTERN = r'(?i)(non farm payrolls|nonfarm)'
├─> cpi_count = nombre d'event_keys correspondant à CPI_PATTERN
└─> nfp_count = nombre d'event_keys correspondant à NFP_PATTERN

DÉTERMINER TYPE NOYAU DUR:

SI cpi_count >= 2:
│   ├─> core_type = 'CPI'
│   ├─> Pour chaque événement:
│   │   ├─> Si event_key correspond à CPI_PATTERN:
│   │   │   ├─> Ajouter à core_events[]
│   │   │   └─> support_scores[event_id] = 1.0
│   │   └─> Sinon:
│   │       └─> support_scores[event_id] = 0.0
│   └─> Log: "Détection noyau dur CPI (X événements CPI)"

SINON SI nfp_count >= 1:
│   ├─> core_type = 'NFP'
│   ├─> Pour chaque événement:
│   │   ├─> Si event_key correspond à NFP_PATTERN:
│   │   │   ├─> Ajouter à core_events[]
│   │   │   └─> support_scores[event_id] = 1.0
│   │   └─> Sinon:
│   │       └─> support_scores[event_id] = 0.0
│   └─> Log: "Détection noyau dur NFP (X événements NFP)"

SINON (fallback):
│   ├─> core_type = 'GENERIC'
│   ├─> Tous les événements sont core:
│   │   ├─> core_events = event_ids.copy()
│   │   └─> support_scores[event_id] = 1.0 pour tous
│   └─> Log: "Aucun noyau dur pré-défini détecté, utilisation générique"

FILTRER PAR SEUIL:
├─> core_events_filtered = événements avec support >= support_threshold
└─> (Normalement tous >= 0.8 pour noyaux durs)

RETURN cluster_info:
├─> 'cluster': cluster original
├─> 'core_events': core_events_filtered
├─> 'n_core_events': len(core_events_filtered)
├─> 'n_total_events': n_total_events
├─> 'support_scores': support_scores
└─> 'core_type': core_type ('CPI', 'NFP', ou 'GENERIC')
```

---

## 📋 ÉTAPE 4 : RECHERCHER CLUSTERS IDENTIQUES

**Méthode** : `etape4_rechercher_clusters_identiques`  
**Lignes** : 381-537

### Paramètres
- `cluster_info` : Informations du cluster avec core_events
- `jaccard_threshold` : Seuil Jaccard initial (défaut: 0.60)
- `years_lookback` : Années de lookback (défaut: 5)
- `min_clusters_found` : Nombre minimum souhaité (défaut: 3)

### Logique

```
core_events_set = set(cluster_info['core_events'])
anchor_time = cluster_info['cluster']['anchor_time']

SI core_events_set vide:
└─> RETURN []

DÉFINIR PÉRIODE RECHERCHE:
├─> date_start = anchor_time - (years_lookback * 365 jours)
├─> date_end = anchor_time - 1 jour (exclure date cible)
└─> target_hour, target_minute = anchor_time.hour, anchor_time.minute

SEUILS ADAPTATIFS:
└─> jaccard_thresholds = [0.60, 0.55, 0.50]

all_candidates = []

POUR CHAQUE DATE dans [date_start → date_end]:
│   │
│   ├─> Charger événements historiques:
│   │   ├─> load_high_impact_events(date, country='US', min_empirical_score=29.0)
│   │   └─> Si vide → CONTINUER
│   │
│   ├─> Détecter clusters historiques:
│   │   └─> etape2_detecter_clusters(df_events_hist, window_minutes=30)
│   │
│   ├─> POUR CHAQUE cluster historique:
│   │   │
│   │   ├─> FILTRER PAR HEURE (±10 minutes):
│   │   │   ├─> time_diff_minutes = |(hist_hour*60 + hist_minute) - (target_hour*60 + target_minute)|
│   │   │   └─> Si time_diff_minutes > 10 → CONTINUER (skip)
│   │   │
│   │   ├─> Définir noyau dur pour cluster historique:
│   │   │   └─> etape3_definir_noyau_dur(cluster_hist, support_threshold=0.8)
│   │   │
│   │   ├─> SI core_events_hist vide:
│   │   │   └─> CONTINUER (skip)
│   │   │
│   │   ├─> CALCULER SIMILARITÉ JACCARD:
│   │   │   ├─> intersection = len(core_events_set & core_events_hist_set)
│   │   │   ├─> union = len(core_events_set | core_events_hist_set)
│   │   │   └─> jaccard_score = intersection / union
│   │   │
│   │   └─> Ajouter à all_candidates[] (même si < seuil initial)
│   │
│   └─> CONTINUER avec date suivante

APPLIQUER SEUIL ADAPTATIF:
├─> Pour chaque seuil dans [0.60, 0.55, 0.50]:
│   ├─> identical_clusters = candidats avec jaccard_score >= seuil
│   └─> SI len(identical_clusters) >= min_clusters_found:
│       └─> BREAK (utiliser ce seuil)
│
├─> Si aucun seuil ne donne assez de clusters:
│   └─> Utiliser seuil initial (0.60)
│
└─> Trier par jaccard_score décroissant

RETURN identical_clusters[]
```

### Résultat
Liste de clusters identiques avec :
- `date` : Date du cluster historique
- `jaccard_score` : Score de similarité (0.0-1.0)
- `core_events` : Événements du noyau dur historique
- `cluster` : Cluster historique complet
- `cluster_info` : Informations du noyau dur historique
- `anchor_time` : Heure d'ancrage historique

---

## 📋 ÉTAPE 5 : CALCULER TENDANCES

**Méthode** : `etape5_calculer_tendances_impacts`  
**Lignes** : 543-725

### Paramètres
- `identical_clusters` : Liste de clusters identiques
- `min_r2` : R² minimum requis (défaut: 0.15)
- `min_amplitude_pips` : Amplitude minimum (défaut: 15.0)

### Logique

```
SI identical_clusters vide:
└─> RETURN pd.DataFrame()

timeframes = ['H1']  # Peut être étendu à ['M1', 'M5', 'M15', 'M30', 'H1']
trends_data = []

POUR CHAQUE cluster dans identical_clusters:
│   │
│   ├─> cluster_date = cluster['date']
│   ├─> anchor_time = cluster['anchor_time']
│   │   └─> Convertir en datetime avec timezone Bern si nécessaire
│   │
│   ├─> best_trend = None
│   ├─> best_timeframe = None
│   │
│   ├─> POUR CHAQUE timeframe dans ['H1']:
│   │   │
│   │   ├─> Charger prix historiques:
│   │   │   ├─> table_name = 'prices_finnhub_h1' (données historiques)
│   │   │   ├─> lookback_days = 14
│   │   │   ├─> start_dt = anchor_time - 14 jours
│   │   │   ├─> end_dt = anchor_time + 6 jours
│   │   │   └─> Requête SQL pour prix dans cette fenêtre
│   │   │
│   │   ├─> SI pas assez de données (< 100 chandeliers):
│   │   │   └─> CONTINUER (skip timeframe)
│   │   │
│   │   ├─> Trouver index événement dans série de prix:
│   │   │   └─> event_time_idx = premier index où datetime >= anchor_time
│   │   │
│   │   ├─> SI event_time_idx None ou 0:
│   │   │   └─> CONTINUER (skip timeframe)
│   │   │
│   │   ├─> Détecter tendance avec detect_trend_by_inversion_s107:
│   │   │   ├─> prices: série de prix
│   │   │   ├─> event_time_idx: index événement
│   │   │   ├─> lookback_days: 14
│   │   │   ├─> segment_hours: 20 (pour H1)
│   │   │   ├─> min_r2_for_trend: min_r2 (0.15)
│   │   │   ├─> min_hours_before_event: 24
│   │   │   └─> timeframe: 'H1'
│   │   │
│   │   ├─> SI tendance détectée (trend_exists = True):
│   │   │   ├─> r2 = trend_result['r2']
│   │   │   ├─> amplitude = trend_result['amplitude_pips']
│   │   │   │
│   │   │   └─> SI r2 >= min_r2 ET amplitude >= min_amplitude_pips:
│   │   │       ├─> Candidat valide
│   │   │       └─> SI best_trend None OU r2 > best_trend['r2']:
│   │   │           ├─> best_trend = trend_result
│   │   │           └─> best_timeframe = timeframe
│   │   │
│   │   └─> CONTINUER avec timeframe suivant
│   │
│   ├─> AJOUTER RÉSULTAT:
│   │   │
│   │   ├─> SI best_trend trouvé:
│   │   │   ├─> trends_data.append({
│   │   │   │   ├─> 'trend_exists': True
│   │   │   │   ├─> 'r2': best_trend['r2']
│   │   │   │   ├─> 'amplitude_pips': best_trend['amplitude_pips']
│   │   │   │   ├─> 'duration_minutes': best_trend['duration_minutes']
│   │   │   │   ├─> 'duration_hours': best_trend['duration_hours']
│   │   │   │   ├─> 'direction': best_trend['direction'] ('UP' ou 'DOWN')
│   │   │   │   ├─> 'timeframe_used': best_timeframe
│   │   │   │   ├─> 'cluster_date': cluster_date
│   │   │   │   └─> 'slope_pips_per_hour': best_trend['slope_pips_per_hour']
│   │   │   └─> })
│   │   │
│   │   └─> SINON (pas de tendance valide):
│   │       ├─> trends_data.append({
│   │       │   ├─> 'trend_exists': False
│   │       │   ├─> 'r2': 0.0
│   │       │   ├─> 'amplitude_pips': 0.0
│   │       │   ├─> 'duration_minutes': 0
│   │       │   ├─> 'duration_hours': 0.0
│   │       │   ├─> 'direction': 'UNKNOWN'
│   │       │   ├─> 'timeframe_used': None
│   │       │   ├─> 'cluster_date': cluster_date
│   │       │   └─> 'slope_pips_per_hour': 0.0
│   │       └─> })
│   │
│   └─> CONTINUER avec cluster suivant

RETURN pd.DataFrame(trends_data)
```

### Résultat
DataFrame avec colonnes :
- `trend_exists` : Booléen
- `r2` : Coefficient de détermination (0.0-1.0)
- `amplitude_pips` : Amplitude de la tendance (pips)
- `duration_minutes` : Durée (minutes)
- `duration_hours` : Durée (heures)
- `direction` : 'UP', 'DOWN', ou 'UNKNOWN'
- `timeframe_used` : Timeframe utilisée ('H1' ou None)
- `cluster_date` : Date du cluster
- `slope_pips_per_hour` : Pente (pips/heure)

---

## 📋 ÉTAPE 6 : CALCULER IMPACTS BASE & AMPLIFICATIONS

**Méthode** : `etape6_calculer_impacts_base_amplifications`  
**Lignes** : 728-865

### Paramètres
- `identical_clusters` : Liste de clusters identiques
- `trends_df` : DataFrame des tendances (pour alignement, non utilisé actuellement)

### Logique

```
SI identical_clusters vide:
└─> RETURN pd.DataFrame()

impacts_data = []

POUR CHAQUE cluster dans identical_clusters:
│   │
│   ├─> cluster_date = cluster['date']
│   ├─> anchor_time = cluster['anchor_time']
│   ├─> cluster_events_df = cluster['cluster']['events']
│   │   └─> Convertir anchor_time en datetime avec timezone Bern si nécessaire
│   │
│   ├─> === CALCUL IMPACT BASE ===
│   │   │
│   │   ├─> total_impact_base = 0.0
│   │   ├─> num_events = len(cluster_events_df)
│   │   │
│   │   ├─> POUR CHAQUE événement dans cluster_events_df:
│   │   │   │
│   │   │   ├─> base_score = event['empirical_score'] (défaut: 44.0)
│   │   │   ├─> actual = event['actual']
│   │   │   ├─> estimate = event['estimate'] OU event['forecast'] OU event['previous']
│   │   │   │
│   │   │   ├─> CALCULER SURPRISE:
│   │   │   │   ├─> SI actual ET estimate valides ET estimate != 0:
│   │   │   │   │   └─> surprise_pct = abs(actual - estimate) / abs(estimate) * 100
│   │   │   │   └─> SINON: surprise_pct = 0.0
│   │   │   │
│   │   │   ├─> AJUSTER SCORE SELON SURPRISE:
│   │   │   │   └─> adjusted_score = calculate_adjusted_empirical_score(
│   │   │   │       base_empirical_score=base_score,
│   │   │   │       surprise_pct=surprise_pct
│   │   │   │   )
│   │   │   │
│   │   │   ├─> CALCULER IMPACT INDIVIDUEL:
│   │   │   │   └─> impact_individuel = calculate_impact_d(
│   │   │   │       empirical_score=adjusted_score,
│   │   │   │       num_events=1,  # Impact individuel
│   │   │   │       amplification=1.0,  # Pas d'amplification ici
│   │   │   │       correction_factor=1.0  # Pas de correction vectorielle ici
│   │   │   │   )
│   │   │   │
│   │   │   └─> total_impact_base += impact_individuel
│   │   │
│   │   └─> APPLIQUER CORRECTION VECTORIELLE:
│   │       └─> SI num_events >= 2:
│   │           └─> total_impact_base = total_impact_base * 0.758
│   │
│   ├─> === MESURE IMPACT RÉEL ===
│   │   │
│   │   ├─> impact_reel = 0.0
│   │   ├─> direction = 0
│   │   │
│   │   ├─> ESSAYER measure_impact_from_finnhub:
│   │   │   ├─> db_path: self.db_path
│   │   │   ├─> event_timestamp: anchor_time
│   │   │   ├─> lookback_minutes: 5
│   │   │   ├─> lookahead_minutes: 120
│   │   │   └─> debug: False
│   │   │
│   │   ├─> SI impact_reel_result retourné:
│   │   │   ├─> impact_reel = impact_reel_result['impact_pips']
│   │   │   └─> direction = impact_reel_result['direction']
│   │   │
│   │   └─> SI erreur → Log warning, impact_reel reste 0.0
│   │
│   ├─> === CALCUL AMPLIFICATION PARFAITE ===
│   │   │
│   │   ├─> SI total_impact_base > 0:
│   │   │   └─> amplification_parfaite = impact_reel / total_impact_base
│   │   └─> SINON:
│   │       └─> amplification_parfaite = 1.0 si impact_reel == 0, sinon float('inf')
│   │
│   └─> impacts_data.append({
│       ├─> 'impact_base': total_impact_base
│       ├─> 'impact_reel': impact_reel
│       ├─> 'amplification_parfaite': amplification_parfaite
│       ├─> 'direction': direction (1=UP, -1=DOWN, 0=UNKNOWN)
│       ├─> 'cluster_date': cluster_date
│       └─> 'num_events': num_events
│   })

RETURN pd.DataFrame(impacts_data)
```

### Résultat
DataFrame avec colonnes :
- `impact_base` : Impact calculé par formule (pips)
- `impact_reel` : Impact réel mesuré (pips)
- `amplification_parfaite` : Ratio réel/base
- `direction` : Direction (1=UP, -1=DOWN, 0=UNKNOWN)
- `cluster_date` : Date du cluster
- `num_events` : Nombre d'événements

---

## 📋 ÉTAPE 7 : ANALYSER RELATION TENDANCE → AMPLIFICATION

**Méthode** : `etape7_analyser_relation_tendance_amplification`  
**Lignes** : 871-908

### Paramètres
- `trends_df` : DataFrame des tendances
- `impacts_df` : DataFrame des impacts

### Logique

```
SI trends_df vide OU impacts_df vide:
└─> RETURN {
    'correlations': {},
    'results_df': pd.DataFrame()
}

FUSIONNER LES DONNÉES:
├─> SI 'cluster_date' présent dans les deux DataFrames:
│   └─> results_df = trends_df.merge(impacts_df, on='cluster_date', how='outer', suffixes=('', '_impact'))
└─> SINON:
    └─> results_df = pd.concat([trends_df, impacts_df], axis=1)

CALCULER CORRÉLATIONS:
├─> correlations = {}
└─> SI 'r2' ET 'amplification_parfaite' dans results_df.columns:
    └─> correlations['r2_vs_amplification'] = results_df['r2'].corr(results_df['amplification_parfaite'])

RETURN {
    'correlations': correlations,
    'results_df': results_df
}
```

### Résultat
Dict avec :
- `correlations` : Dict des corrélations calculées
- `results_df` : DataFrame fusionné avec toutes les colonnes de trends_df et impacts_df

---

## 📋 ÉTAPE 8 : APPLIQUER CLUSTER CIBLE

**Méthode** : `etape8_appliquer_cluster_cible`  
**Lignes** : 914-1916

### Paramètres
- `cluster_info` : Informations du cluster cible
- `analysis_results` : Résultats de l'analyse (étape 7)
- `identical_clusters` : Clusters identiques trouvés

### Sous-étapes

---

### 8.1 : CALCUL DE L'IMPACT DE BASE

**Lignes** : 971-1019

```
cluster_events = cluster_info['cluster']['events']
anchor_time = cluster_info['cluster']['anchor_time']

Ajuster anchor_time si événement US HIGH impact à 14:25-14:35:
├─> us_high_impact_events = cluster_events[(country=='US') & (empirical_score>50)]
└─> SI trouvé ET heure 14:25-14:35:
    └─> anchor_time = cpi_anchor_time (premier événement US HIGH impact)

CALCULER IMPACT BASE (Méthode Session 88):
├─> num_events = len(cluster_events)
│
├─> Score base moyen:
│   ├─> base_scores = cluster_events['empirical_score'].dropna()
│   ├─> SI base_scores vide:
│   │   └─> score_base_avg = 44.0 (défaut)
│   └─> SINON:
│       └─> score_base_avg = base_scores.mean()
│
├─> Surprise maximale:
│   ├─> max_surprise_pct = 0.0
│   └─> POUR CHAQUE événement:
│       ├─> actual = event['actual']
│       ├─> estimate = event['estimate'] OU 'forecast' OU 'previous'
│       └─> SI actual ET estimate valides ET estimate != 0:
│           └─> surprise_pct = abs(actual - estimate) / abs(estimate) * 100
│           └─> max_surprise_pct = max(max_surprise_pct, surprise_pct)
│
├─> Score ajusté moyen:
│   └─> score_adjusted_mean = calculate_adjusted_empirical_score(
│       base_empirical_score=score_base_avg,
│       surprise_pct=max_surprise_pct
│   )
│
└─> Impact de base:
    └─> impact_base = calculate_impact_d(
        empirical_score=score_adjusted_mean,
        num_events=num_events,
        amplification=1.0,
        correction_factor=0.758  # Correction vectorielle
    )
```

---

### 8.2 : DÉTECTION DE TENDANCE

**Lignes** : 1021-1080

```
trend_exists = False
trend_r2 = 0.0
trend_direction = 'UNKNOWN'
trend_amplitude_pips = 0.0

ESSAYER détection tendance:
├─> Charger prix M30:
│   ├─> table_name = 'prices_finnhub_m30'
│   ├─> lookback_days = 14
│   ├─> start_dt = anchor_time - 14 jours
│   ├─> end_dt = anchor_time + 6 jours
│   └─> Requête SQL pour prix dans cette fenêtre
│
├─> SI pas assez de données (< 100 chandeliers):
│   └─> SKIP (trend_exists reste False)
│
├─> Trouver index événement:
│   └─> event_time_idx = premier index où datetime >= anchor_time
│
├─> SI event_time_idx None ou 0:
│   └─> SKIP (trend_exists reste False)
│
├─> Détecter tendance:
│   └─> trend_result = detect_trend_by_inversion_s107(
│       prices=prices_series,
│       event_time_idx=event_time_idx,
│       lookback_days=14,
│       segment_hours=12,
│       min_r2_for_trend=0.15,
│       min_hours_before_event=12,
│       timeframe='M30'
│   )
│
└─> SI trend_result['trend_exists'] = True:
    ├─> trend_exists = True
    ├─> trend_r2 = trend_result['r2']
    ├─> trend_direction = trend_result['direction']
    └─> trend_amplitude_pips = trend_result['amplitude_pips']

SI erreur → Log warning, trend_exists reste False
```

---

### 8.3 : PRÉDICTION D'AMPLIFICATION

**Lignes** : 1082-1195

```
amplification_predite = 1.0
amplification_method = 'default'

results_df = analysis_results.get('results_df') si analysis_results existe, sinon None
num_clusters = len(identical_clusters) si identical_clusters existe, sinon 0

Calculer surprise maximale (déjà fait en 8.1, réutiliser max_surprise_pct)

HIÉRARCHIE D'AMPLIFICATION:

0. FORMULE SESSION 88 (priorité maximale):
│   ├─> SI max_surprise_pct > 100:
│   │   ├─> ESSAYER calculate_amplification_extended(max_surprise_pct)
│   │   ├─> SI succès:
│   │   │   ├─> amplification_predite = résultat
│   │   │   ├─> amplification_method = 'session88_extended'
│   │   │   └─> Log: "✅ Amplification (Session 88): X.XXXx"
│   │   └─> SI erreur → Log warning, continuer
│   └─> SINON (surprise <= 100%):
│       └─> CONTINUER à étape suivante

1. RANDOM FOREST (si >= 5 clusters identiques ET Session 88 non utilisée):
│   ├─> SI amplification_method == 'default' ET num_clusters >= 5 ET results_df non None:
│   │   ├─> ESSAYER train_rf_from_identical_clusters:
│   │   │   ├─> identical_clusters: identical_clusters
│   │   │   ├─> results_df: results_df
│   │   │   ├─> executor: self
│   │   │   └─> min_clusters: 5
│   │   │
│   │   ├─> SI rf_result non None:
│   │   │   ├─> rf_model, scaler, feature_names = rf_result
│   │   │   │
│   │   │   ├─> Extraire features pour cluster cible:
│   │   │   │   └─> features_target = extract_features_for_rf(
│   │   │   │       cluster_events=cluster_events,
│   │   │   │       trend_r2=trend_r2,
│   │   │   │       trend_direction=trend_direction,
│   │   │   │       trend_amplitude_pips=trend_amplitude_pips,
│   │   │   │       num_events=num_events
│   │   │   │   )
│   │   │   │
│   │   │   ├─> Prédire amplification:
│   │   │   │   └─> amplification_predite = predict_amplification_with_rf(
│   │   │   │       rf_model=rf_model,
│   │   │   │       scaler=scaler,
│   │   │   │       feature_names=feature_names,
│   │   │   │       features=features_target
│   │   │   │   )
│   │   │   │
│   │   │   ├─> amplification_method = 'random_forest'
│   │   │   └─> Log: "✅ Amplification prédite (Random Forest): X.XXXx"
│   │   │
│   │   └─> SINON (RF ne peut pas être entraîné):
│   │       ├─> SI 'amplification_parfaite' dans results_df.columns:
│   │       │   ├─> amplification_predite = results_df['amplification_parfaite'].mean()
│   │       │   ├─> amplification_method = 'rf_fallback_mean'
│   │       │   └─> Log: "ℹ️ RF non disponible, utilisation moyenne: X.XXXx"
│   │       └─> SI erreur → Log warning, continuer
│   │
│   └─> SINON (conditions non remplies):
│       └─> CONTINUER à étape suivante

2. MODÈLE LINÉAIRE R² (si tendance détectée ET Session 88/RF non utilisés):
│   ├─> SI amplification_method == 'default' ET trend_exists ET trend_r2 > 0:
│   │   ├─> ESSAYER predict_amplification_from_r2:
│   │   │   ├─> r2_trend: trend_r2
│   │   │   └─> calibration_mode: 'linear'
│   │   │
│   │   ├─> SI succès:
│   │   │   ├─> amplification_predite = résultat
│   │   │   ├─> amplification_method = 'linear_r2'
│   │   │   └─> Log: "✅ Amplification prédite (linéaire R²): X.XXXx"
│   │   └─> SI erreur → Log warning, continuer
│   │
│   └─> SINON (conditions non remplies):
│       └─> CONTINUER à étape suivante

3. MOYENNE HISTORIQUE (dernier fallback):
│   ├─> SI amplification_method == 'default' ET results_df non None:
│   │   ├─> SI 'amplification_parfaite' dans results_df.columns:
│   │   │   ├─> amplification_predite = results_df['amplification_parfaite'].mean()
│   │   │   ├─> amplification_method = 'mean_historical'
│   │   │   └─> Log: "ℹ️ Amplification (moyenne historique): X.XXXx"
│   │   └─> SINON:
│   │       └─> amplification_predite reste 1.0 (défaut)
│   │
│   └─> SINON (results_df None):
│       └─> amplification_predite reste 1.0 (défaut)
```

---

### 8.4 : AJUSTEMENTS SUPPORT/RÉSISTANCE

**Lignes** : 1197-1328

```
sr_adjustment = 0.0  # Ajustement en pourcentage

SI trend_exists ET trend_direction != 'UNKNOWN':
│   │
│   ├─> ESSAYER calculer ajustement S/R:
│   │   │
│   │   ├─> Charger prix M30:
│   │   │   ├─> table_name = 'prices_finnhub_m30'
│   │   │   ├─> start_dt = anchor_time - 7 jours
│   │   │   ├─> end_dt = anchor_time + 1 jour
│   │   │   └─> Requête SQL pour prix
│   │   │
│   │   ├─> SI pas assez de données (< 20 chandeliers):
│   │   │   └─> SKIP (sr_adjustment reste 0.0)
│   │   │
│   │   ├─> Calculer ATR (Average True Range):
│   │   │   ├─> hl = high - low
│   │   │   ├─> hc = abs(high - close.shift())
│   │   │   ├─> lc = abs(low - close.shift())
│   │   │   ├─> tr = max(hl, hc, lc)
│   │   │   └─> atr = tr.rolling(window=14).mean()
│   │   │
│   │   ├─> atr_median = atr.median()
│   │   │
│   │   ├─> SI atr_median > 0:
│   │   │   │
│   │   │   ├─> Prix actuel:
│   │   │   │   └─> current_price = prix à anchor_time (ou dernier prix disponible)
│   │   │   │
│   │   │   ├─> Support/Résistance (24h avant événement):
│   │   │   │   ├─> window_start = anchor_time - 24 heures
│   │   │   │   ├─> window_end = anchor_time
│   │   │   │   ├─> df_window = prix dans [window_start, window_end)
│   │   │   │   ├─> support_level = df_window['low'].min()
│   │   │   │   └─> resistance_level = df_window['high'].max()
│   │   │   │
│   │   │   ├─> Direction cluster:
│   │   │   │   └─> cluster_direction = 1 si trend_direction == 'UP', -1 si 'DOWN', 0 sinon
│   │   │   │
│   │   │   ├─> SI cluster_direction > 0 (Cluster haussier):
│   │   │   │   │
│   │   │   │   ├─> Distance à résistance:
│   │   │   │   │   ├─> distance_to_resistance = (resistance_level - current_price) * 10000 (pips)
│   │   │   │   │   └─> distance_normalized = distance_to_resistance / (atr_median * 10000)
│   │   │   │   │
│   │   │   │   ├─> Breakout détecté:
│   │   │   │   │   └─> is_breakout = current_price > resistance_level
│   │   │   │   │
│   │   │   │   ├─> SI is_breakout:
│   │   │   │   │   ├─> SI distance_normalized < 0.15:
│   │   │   │   │   │   └─> sr_adjustment = 0.15  # +15%
│   │   │   │   │   └─> SINON SI distance_normalized < 0.40:
│   │   │   │   │       └─> sr_adjustment = 0.05  # +5%
│   │   │   │   │
│   │   │   │   └─> SINON (pas de breakout):
│   │   │   │       ├─> SI distance_normalized < 0.10:
│   │   │   │       │   └─> sr_adjustment = -0.30  # -30%
│   │   │   │       ├─> SINON SI distance_normalized < 0.20:
│   │   │   │       │   └─> sr_adjustment = -0.10  # -10%
│   │   │   │       └─> SINON SI distance_normalized > 1.40:
│   │   │   │           └─> sr_adjustment = 0.15  # +15%
│   │   │   │
│   │   │   └─> SINON SI cluster_direction < 0 (Cluster baissier):
│   │   │       │
│   │   │       ├─> Distance à support:
│   │   │       │   ├─> distance_to_support = (current_price - support_level) * 10000 (pips)
│   │   │       │   └─> distance_normalized = distance_to_support / (atr_median * 10000)
│   │   │       │
│   │   │       ├─> Breakout détecté:
│   │   │       │   └─> is_breakout = current_price < support_level
│   │   │       │
│   │   │       ├─> SI is_breakout:
│   │   │       │   ├─> SI distance_normalized < 0.15:
│   │   │       │   │   └─> sr_adjustment = 0.15  # +15%
│   │   │       │   └─> SINON SI distance_normalized < 0.40:
│   │   │       │       └─> sr_adjustment = 0.05  # +5%
│   │   │       │
│   │   │       └─> SINON (pas de breakout):
│   │   │           ├─> SI distance_normalized < 0.10:
│   │   │           │   └─> sr_adjustment = -0.30  # -30%
│   │   │           ├─> SINON SI distance_normalized < 0.20:
│   │   │           │   └─> sr_adjustment = -0.10  # -10%
│   │   │           └─> SINON SI distance_normalized > 1.40:
│   │   │               └─> sr_adjustment = 0.15  # +15%
│   │   │
│   │   └─> SI sr_adjustment != 0:
│   │       └─> Log: "ℹ️ Ajustement S/R: ±X.X%"
│   │
│   └─> SI erreur → Log warning, sr_adjustment reste 0.0

SINON (pas de tendance):
└─> sr_adjustment reste 0.0
```

---

### 8.5 : AJUSTEMENTS PATTERNS FINNHUB

**Lignes** : 1330-1365

```
finnhub_adjustment = 0.0  # Ajustement en pourcentage

ESSAYER charger patterns Finnhub:
├─> finnhub_patterns = load_finnhub_patterns(
│   ├─> date: anchor_time
│   ├─> db_path: self.db_path
│   └─> lookback_days: 7
│   )
│
├─> SI finnhub_patterns non vide:
│   │
│   ├─> Trouver patterns proches de anchor_time:
│   │   └─> patterns_near = find_patterns_near_time(
│   │       ├─> patterns: finnhub_patterns
│   │       ├─> target_time: anchor_time
│   │       └─> window_minutes: 60
│   │   )
│   │
│   ├─> SI patterns_near non vide:
│   │   │
│   │   ├─> Déterminer direction prédiction:
│   │   │   └─> prediction_direction = trend_direction si trend_exists, sinon 'UNKNOWN'
│   │   │
│   │   ├─> validating_patterns = 0
│   │   ├─> invalidating_patterns = 0
│   │   │
│   │   ├─> POUR CHAQUE pattern dans patterns_near:
│   │   │   │
│   │   │   ├─> pattern_dir = get_pattern_direction(pattern['pattern_type'])
│   │   │   ├─> pattern_strength = pattern['status'] == 'mature'
│   │   │   │
│   │   │   ├─> SI pattern_strength:
│   │   │   │   │
│   │   │   │   ├─> SI direction cohérente (prediction_direction == pattern_dir):
│   │   │   │   │   └─> validating_patterns += 1
│   │   │   │   │
│   │   │   │   └─> SINON (direction opposée):
│   │   │   │       └─> invalidating_patterns += 1
│   │   │   │
│   │   │   └─> CONTINUER avec pattern suivant
│   │   │
│   │   ├─> APPLIQUER MULTIPLICATEURS:
│   │   │   ├─> SI validating_patterns > 0:
│   │   │   │   └─> finnhub_adjustment = min(0.10, validating_patterns * 0.05)  # Max +10%
│   │   │   └─> SI invalidating_patterns > 0:
│   │   │       └─> finnhub_adjustment = max(-0.10, -invalidating_patterns * 0.05)  # Min -10%
│   │   │
│   │   └─> SI finnhub_adjustment != 0:
│   │       └─> Log: "ℹ️ Ajustement Finnhub: ±X.X%"
│   │
│   └─> SINON (pas de patterns proches):
│       └─> finnhub_adjustment reste 0.0
│
└─> SI erreur → Log warning, finnhub_adjustment reste 0.0

CALCULER FACTEUR D'AJUSTEMENT TOTAL:
└─> adjustment_factor = 1.0 + sr_adjustment + finnhub_adjustment
    └─> Limiter entre 0.5 et 2.0: adjustment_factor = max(0.5, min(2.0, adjustment_factor))
```

---

### 8.6 : DÉTECTION DE PATTERN DE PRIX

**Lignes** : 1367-1835

```
pattern_type = 'NONE'
pattern_info = {
    'pattern_type': 'NONE',
    'direction': 'UNKNOWN',
    'confidence': 0.0,
    'wave1_pips': 0.0,
    'wave2_pips': 0.0,
    'pullback_pips': 0.0,
    'baseline_price': None,
    'wave2_peak_pips_absolute': 0.0,
    'timings_predicted': False,
    'wave1_peak_time': None,
    'pullback_low_time': None,
    'wave2_peak_time': None,
    'stabilization_time': None
}

DÉTECTER CLUSTERS MULTIPLES:
├─> Charger tous événements de la date:
│   └─> all_events_date = etape1_charger_evenements(date_str)
│
├─> Détecter clusters:
│   └─> clusters_temporels_all = etape2_detecter_clusters(all_events_date, window_minutes=30)
│
├─> has_multiple_clusters = len(clusters_temporels_all) > 1
└─> cluster2_time = None (si cluster suivant trouvé)

DÉTECTER PATTERN RÉEL DANS PRIX:
├─> ESSAYER detect_for_date_duckdb_rev12:
│   ├─> db_path: self.db_path
│   ├─> table: 'prices_finnhub_m1'
│   ├─> date: anchor_time (datetime naive)
│   ├─> tz: 'Europe/Zurich'
│   ├─> baseline_mode: 'prev_close_14_29'
│   ├─> minutes_after_hint: 120
│   ├─> trading_window: True
│   └─> debug: False
│
├─> pattern_real_result = résultat (peut être None)
│
└─> SI pattern_real_result:
    ├─> SI pattern_real_result['double_wave'] = True:
    │   └─> Log: "✅ Pattern réel détecté : DOUBLE_WAVE"
    └─> SINON:
        └─> Log: "ℹ️ Pattern réel détecté : SINGLE_WAVE"

DÉTECTER CONDITIONS DOUBLE WAVE (ÉVÉNEMENTS):
├─> ESSAYER detect_double_wave_conditions:
│   ├─> events: liste des événements du cluster
│   └─> Retourne: is_double_wave_events (booléen)
│
└─> SI erreur → is_double_wave_events = False

DÉTERMINER TYPE PATTERN:

SI pattern_real_result ET pattern_real_result['double_wave'] = True:
│   ├─> Pattern réel = Double Wave confirmé
│   └─> is_double_wave = True
│
SINON SI pattern_real_result (mais double_wave = False):
│   ├─> pattern_real_is_single = True
│   │
│   ├─> SI is_double_wave_events:
│   │   ├─> Exception : Pattern réel = Single Wave mais critères événements = Double Wave
│   │   ├─> is_single_wave_strong = True
│   │   └─> is_double_wave = False
│   │
│   └─> SINON:
│       └─> is_single_wave_strong = True
│
SINON (pattern_real_result = None):
│   ├─> pattern_real_is_single = True (pas de Double Wave détecté = Single Wave probable)
│   │
│   ├─> SI is_double_wave_events:
│   │   ├─> Pattern réel pas détecté mais critères remplis → Utiliser Double Wave
│   │   └─> is_double_wave = True
│   │
│   └─> SINON:
│       └─> is_single_wave_strong = True

PRÉDICTION PATTERN:

SI is_double_wave:
│   │
│   ├─> DOUBLE WAVE - Utiliser predict_double_wave_timeline_s64:
│   │   │
│   │   ├─> base_impact_for_timeline = impact_base * amplification_predite
│   │   │
│   │   ├─> timeline = predict_double_wave_timeline_s64(
│   │   │   ├─> base_impact: base_impact_for_timeline
│   │   │   ├─> surprise_pct: max_surprise_pct
│   │   │   ├─> cluster_size: num_events
│   │   │   └─> start_time: anchor_time
│   │   │   )
│   │   │
│   │   ├─> Extraire timings prédits:
│   │   │   ├─> wave1_peak_time_predicted = timeline['phase1']['time'] (T+5 min)
│   │   │   ├─> pullback_low_time_predicted = timeline['pullback']['time'] (T+11 min)
│   │   │   ├─> wave2_peak_time_predicted = timeline['phase2']['time'] (T+15 min)
│   │   │   └─> stabilization_time_predicted = timeline['stabilization']['time'] (T+40 min)
│   │   │
│   │   ├─> Extraire amplitudes prédites:
│   │   │   ├─> wave1_pips_predicted = timeline['phase1']['impact_pips']
│   │   │   ├─> pullback_pips_predicted = timeline['pullback']['retrace_pips']
│   │   │   └─> wave2_pips_predicted = timeline['phase2']['impact_pips']
│   │   │
│   │   ├─> wave2_peak_pips_absolute = wave2_pips_predicted (Pic absolu = Phase 2)
│   │   │
│   │   ├─> pattern_type = 'DOUBLE_WAVE'
│   │   ├─> pattern_direction = 'UP' (par défaut) ou 'DOWN' (si trend_direction == 'DOWN')
│   │   │
│   │   └─> pattern_info = {
│   │       ├─> 'pattern_type': 'DOUBLE_WAVE'
│   │       ├─> 'direction': pattern_direction
│   │       ├─> 'confidence': 100.0
│   │       ├─> 'wave1_pips': wave1_pips_predicted
│   │       ├─> 'wave2_pips': wave2_pips_predicted
│   │       ├─> 'pullback_pips': abs(pullback_pips_predicted)
│   │       ├─> 'baseline_price': None
│   │       ├─> 'wave2_peak_pips_absolute': wave2_peak_pips_absolute
│   │       ├─> 'timings_predicted': True
│   │       ├─> 'wave1_peak_time': wave1_peak_time_predicted
│   │       ├─> 'pullback_low_time': pullback_low_time_predicted
│   │       ├─> 'wave2_peak_time': wave2_peak_time_predicted
│   │       ├─> 'stabilization_time': stabilization_time_predicted
│   │       └─> 'timeline': timeline
│   │   }
│   │
│   └─> Log: "✅ Double Wave détecté - Timings prédits (Session 64, 0.00 min erreur)"

SINON SI is_single_wave_strong:
│   │
│   ├─> SINGLE WAVE FORT - Utiliser predict_single_wave_timeline:
│   │   │
│   │   ├─> base_impact_for_timeline_single = impact_base * amplification_predite
│   │   │
│   │   ├─> single_wave_timeline = predict_single_wave_timeline(
│   │   │   ├─> base_impact: base_impact_for_timeline_single
│   │   │   ├─> surprise_pct: max_surprise_pct
│   │   │   ├─> cluster_size: num_events
│   │   │   └─> start_time: anchor_time
│   │   │   )
│   │   │
│   │   ├─> Extraire timings prédits:
│   │   │   ├─> peak_time_predicted = single_wave_timeline['peak']['time'] (T+8 min)
│   │   │   ├─> pullback_time_predicted = single_wave_timeline['pullback']['time'] (T+15 min)
│   │   │   └─> stabilization_time_predicted = single_wave_timeline['stabilization_time'] (T+25 min)
│   │   │
│   │   ├─> Extraire amplitudes prédites:
│   │   │   ├─> peak_pips_predicted = single_wave_timeline['peak']['impact_pips']
│   │   │   └─> pullback_pips_predicted = single_wave_timeline['pullback']['retrace_pips']
│   │   │
│   │   ├─> pattern_type = 'SINGLE_WAVE_STRONG'
│   │   ├─> pattern_direction = 'UP' (par défaut) ou 'DOWN' (si trend_direction == 'DOWN')
│   │   │
│   │   ├─> pattern_info = {
│   │   │   ├─> 'pattern_type': 'SINGLE_WAVE_STRONG'
│   │   │   ├─> 'direction': pattern_direction
│   │   │   ├─> 'confidence': 100.0
│   │   │   ├─> 'wave1_pips': peak_pips_predicted
│   │   │   ├─> 'wave2_pips': 0.0
│   │   │   ├─> 'pullback_pips': abs(pullback_pips_predicted)
│   │   │   ├─> 'baseline_price': None
│   │   │   ├─> 'wave2_peak_pips_absolute': peak_pips_predicted
│   │   │   ├─> 'timings_predicted': True
│   │   │   ├─> 'wave1_peak_time': peak_time_predicted
│   │   │   ├─> 'pullback_low_time': pullback_time_predicted
│   │   │   ├─> 'wave2_peak_time': None
│   │   │   ├─> 'stabilization_time': stabilization_time_predicted
│   │   │   └─> 'timeline': single_wave_timeline
│   │   }
│   │   │
│   │   ├─> CORRECTION : Utiliser pattern réel détecté pour l'impact (si disponible)
│   │   │   ├─> SI pattern_real_result ET pattern_real_result['double_wave'] = False:
│   │   │   │   ├─> wave1_pips_real = pattern_real_result['wave1_amp_pips']
│   │   │   │   └─> SI wave1_pips_real > 0:
│   │   │   │       ├─> pattern_info['wave2_peak_pips_absolute'] = wave1_pips_real
│   │   │   │       ├─> pattern_info['wave1_pips'] = wave1_pips_real
│   │   │   │       └─> Log: "✅ Pattern réel utilisé : Impact réel X.XX pips"
│   │   │   └─> (Sinon garder pattern prédit)
│   │   │
│   │   └─> Log: "✅ Single Wave Fort détecté - Timings prédits (Session 67)"
│   │
│   └─> SI erreur → Log warning, is_single_wave_strong = False

SINON (fallback - pas Double Wave ni Single Wave Fort):
│   │
│   └─> ESSAYER détection pattern réelle:
│       ├─> pattern_result = detect_for_date_duckdb_rev12(...)
│       │
│       ├─> SI pattern_result:
│       │   ├─> pattern_type = 'DOUBLE_WAVE' si double_wave=True, sinon 'SINGLE_WAVE'
│       │   ├─> pattern_direction = 'UP' ou 'DOWN' depuis pattern_result['direction']
│       │   ├─> baseline_price = pattern_result['baseline_price']
│       │   ├─> wave1_pips = pattern_result['wave1_amp_pips']
│       │   ├─> wave2_pips = pattern_result['wave2_amp_pips']
│       │   ├─> pullback_pips = abs(pattern_result['pullback1_ratio'] * wave1_pips)
│       │   ├─> wave2_peak_pips_absolute = wave2_pips
│       │   │
│       │   └─> pattern_info = {
│       │       ├─> 'pattern_type': pattern_type
│       │       ├─> 'direction': pattern_direction
│       │       ├─> 'confidence': pattern_result['confidence']
│       │       ├─> 'wave1_pips': wave1_pips
│       │       ├─> 'wave2_pips': wave2_pips
│       │       ├─> 'pullback_pips': pullback_pips
│       │       ├─> 'baseline_price': baseline_price
│       │       ├─> 'wave2_peak_pips_absolute': wave2_peak_pips_absolute
│       │       ├─> 'timings_predicted': False
│       │       ├─> 'wave1_peak_time': pattern_result['peak1_time']
│       │       └─> 'wave2_peak_time': pattern_result['peak2_time']
│       │   }
│       │
│       └─> Log: "✅ Pattern détecté: X (Y), confiance: Z%"
```

---

### 8.7 : STRATÉGIE HYBRIDE PATTERN/FORMULES

**Lignes** : 1837-1879

```
impact_formules = impact_base * amplification_predite * adjustment_factor

DÉTERMINER PATTERN IMPACT:
├─> SI pattern_info['wave2_peak_pips_absolute'] > 0:
│   └─> pattern_impact = pattern_info['wave2_peak_pips_absolute']
├─> SINON SI pattern_info['wave2_pips'] > 0:
│   └─> pattern_impact = pattern_info['wave2_pips']
└─> SINON:
    └─> pattern_impact = 0.0

ecart_absolu = abs(pattern_impact - impact_formules) si pattern_impact > 0, sinon 0

STRATÉGIE SELON PATTERN TYPE:

SI pattern_type == 'SINGLE_WAVE_STRONG' OU pattern_type == 'SINGLE_WAVE':
│   │
│   ├─> Single Wave : Stratégie hybride activée
│   │
│   ├─> SI ecart_absolu < 10 OU pattern_impact == 0:
│   │   ├─> prediction_finale = impact_formules
│   │   ├─> prediction_method = 'formulas'
│   │   └─> Log: "✅ Stratégie: Formules (Single Wave, écart: X.X pips < 10)"
│   │
│   └─> SINON (ecart_absolu >= 10):
│       ├─> prediction_finale = pattern_impact
│       ├─> prediction_method = 'pattern'
│       └─> Log: "✅ Stratégie: Pattern (Single Wave, écart: X.X pips >= 10)"

SINON SI pattern_type == 'DOUBLE_WAVE':
│   │
│   ├─> Double Wave : Toujours utiliser formules (stratégie hybride désactivée)
│   │
│   ├─> prediction_finale = impact_formules
│   ├─> prediction_method = 'formulas'
│   └─> Log: "✅ Stratégie: Formules (Double Wave, stratégie hybride désactivée)"

SINON (Autres patterns: NONE, etc.):
│   │
│   ├─> Stratégie hybride standard
│   │
│   ├─> SI ecart_absolu < 10 OU pattern_impact == 0:
│   │   ├─> prediction_finale = impact_formules
│   │   ├─> prediction_method = 'formulas'
│   │   └─> Log: "✅ Stratégie: Formules (écart: X.X pips < 10)"
│   │
│   └─> SINON (ecart_absolu >= 10):
│       ├─> prediction_finale = pattern_impact
│       ├─> prediction_method = 'pattern'
│       └─> Log: "✅ Stratégie: Pattern (écart: X.X pips >= 10)"
```

---

### 8.8 : CALCUL DU TARGET DE SORTIE

**Lignes** : 1881-1892

```
exit_target = prediction_finale * 0.80

Limiter (formule documentée mais peu claire):
└─> exit_target = max(prediction_finale * 0.80, min(prediction_finale * 1.5, exit_target))
    └─> (En pratique = prediction_finale * 0.80 car toujours < 1.5x)
```

---

### RETOUR FINAL

**Lignes** : 1894-1916

```
RETURN final_prediction = {
    'impact_base': impact_base,
    'amplification_predite': amplification_predite,
    'prediction_finale': prediction_finale,
    'prediction_method': prediction_method,
    'exit_target': exit_target,
    'exit_strategy': '80% du prédit',
    'pattern_type': pattern_type,
    'pattern_info': pattern_info,
    'trend_exists': trend_exists,
    'trend_r2': trend_r2,
    'trend_direction': trend_direction,
    'trend_amplitude_pips': trend_amplitude_pips,
    'baseline_price': pattern_info.get('baseline_price'),
    'pattern_wave1_peak_time': pattern_info.get('wave1_peak_time'),
    'pattern_pullback_low_time': pattern_info.get('pullback_low_time'),
    'pattern_wave2_peak_time': pattern_info.get('wave2_peak_time'),
    'pattern_stabilization_time': pattern_info.get('stabilization_time'),
    'timings_predicted': pattern_info.get('timings_predicted', False)
}
```

---

## 🔍 POINTS CRITIQUES À VÉRIFIER

### 1. Ordre d'exécution des étapes
✅ Correct : 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8

### 2. Utilisation des résultats entre étapes
- ✅ Étape 3 utilise résultat étape 2 (cluster)
- ✅ Étape 4 utilise résultat étape 3 (cluster_info avec core_events)
- ✅ Étape 5 utilise résultat étape 4 (identical_clusters)
- ✅ Étape 6 utilise résultat étape 4 (identical_clusters) et étape 5 (trends_df pour alignement)
- ✅ Étape 7 fusionne résultats étape 5 (trends_df) et étape 6 (impacts_df)
- ✅ Étape 8 utilise résultats étape 3 (cluster_info), étape 4 (identical_clusters), étape 7 (analysis_results)

### 3. Calcul impact base dans étape 6 vs étape 8
⚠️ **DIFFÉRENCE IMPORTANTE** :
- **Étape 6** : Somme des impacts individuels avec correction vectorielle 0.758
- **Étape 8** : Méthode Session 88 (score moyen ajusté avec surprise MAX)

### 4. Amplification idéale dans Random Forest
✅ Utilise `impact_base` et `impact_reel` de l'étape 6 (via `results_df`)
✅ Calcul : `amplification_ideale = impact_real / (impact_base * adjustment_factor)`

### 5. Pattern réel vs Pattern prédit
⚠️ **CORRECTION APPLIQUÉE** :
- Pour Single Wave : Utilise pattern réel détecté (183.3 pips) si disponible
- Sinon : Utilise pattern prédit (223.18 pips)

---

## 📊 FLUX DE DONNÉES COMPLET

```
date_str
│
├─> Étape 1: df_events (tous événements date)
│   └─> Seuil: 29.0 (US/EU), 20.0 (DE)
│
├─> Étape 2: clusters[] (groupés par fenêtre 30 min)
│   └─> Sélection: Cluster US HIGH impact à 14:30 OU plus grand
│
├─> Étape 3: cluster_info (avec core_events, core_type)
│   └─> Type: CPI (si >=2 CPI), NFP (si >=1 NFP), GENERIC (sinon)
│
├─> Étape 4: identical_clusters[] (clusters historiques similaires)
│   └─> Jaccard >= 0.60 (adaptatif jusqu'à 0.50)
│
├─> Étape 5: trends_df (tendances pour chaque cluster historique)
│   └─> Timeframe: H1, détection avec detect_trend_by_inversion_s107
│
├─> Étape 6: impacts_df (impacts base/réel/amplification pour chaque cluster)
│   ├─> impact_base: Somme impacts individuels × 0.758
│   ├─> impact_reel: measure_impact_from_finnhub (M1)
│   └─> amplification_parfaite: impact_reel / impact_base
│
├─> Étape 7: analysis_results (fusion trends_df + impacts_df)
│   ├─> results_df: DataFrame fusionné par cluster_date
│   └─> correlations: Corrélations calculées
│
└─> Étape 8: final_prediction (prédiction pour cluster cible)
    ├─> 8.1: impact_base (Session 88) ← cluster_events uniquement
    ├─> 8.2: trend (M30) ← cluster cible uniquement
    ├─> 8.3: amplification_predite (hiérarchie) ← results_df + identical_clusters
    ├─> 8.4: sr_adjustment ← trend + prix M30
    ├─> 8.5: finnhub_adjustment ← patterns Finnhub
    ├─> 8.6: pattern_info ← pattern réel OU prédit
    ├─> 8.7: prediction_finale ← stratégie hybride
    └─> 8.8: exit_target ← 80% de prediction_finale
```

---

_Date création : Documentation exhaustive pipeline_  
_Status : ✅ Documentation complète avec tous les chemins conditionnels_




