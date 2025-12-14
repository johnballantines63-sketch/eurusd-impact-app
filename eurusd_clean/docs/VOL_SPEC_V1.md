# 📊 VOL_SPEC_V1 – Spécification de la volatilité réalisée journalière EURUSD

**Date** : 2025-12-11  
**Version** : VOL_SPEC_V1  
**Scope** : mesure de volatilité journalière EURUSD pour validation prédictive

---

## 1. Objet

Définir la **mesure canonique de volatilité journalière EURUSD** pour :

- valider la prédictivité des scores d'impact des événements macro
- corréler `score_impact_v1` / `score_bucket_v1` avec la volatilité réalisée
- construire des modèles de prédiction de volatilité basés sur les news

**Version V1** : définition simple basée sur le range intraday.  
Les futures versions (V2+) pourront inclure :
- ATR (Average True Range)
- Realized variance
- Volatilité directionnelle (up vs down)

---

## 2. Source de données

**Table** : `prices_finnhub_m1`

**Caractéristiques** :
- Symbol : EURUSD (implicite dans la table)
- Granularité : M1 (1 minute)
- Timezone : Europe/Zurich (Bern time)
- Colonnes : `datetime`, `open`, `high`, `low`, `close`, `volume`

---

## 3. Définition VOL_SPEC_V1

### 3.1. Agrégations journalières

Pour chaque date (YYYY-MM-DD en timezone Europe/Zurich) :

**Extrêmes journaliers** :
- `day_open` : `open` de la première bougie M1 du jour (min(`datetime`) où DATE(`datetime`) = date)
- `day_close` : `close` de la dernière bougie M1 du jour (max(`datetime`) où DATE(`datetime`) = date)
- `day_high` : `MAX(high)` sur toutes les bougies M1 du jour
- `day_low` : `MIN(low)` sur toutes les bougies M1 du jour

### 3.2. Métriques de volatilité

**Range journalier (en pips)** :
```
range_pips = (day_high - day_low) × 10000
```

**Mouvement close-to-close (en pips)** :
```
close_to_close_pips = |day_close - day_open| × 10000
```

### 3.3. Métrique principale V1

**Volatilité journalière canonique** :
```
daily_volatility_pips_v1 = range_pips
```

**Justification** :
- Le range capture l'ampleur totale du mouvement intraday
- Plus robuste que close-to-close (peut masquer des retours en fin de journée)
- Standard dans l'industrie (utilisé pour calculer l'ATR, etc.)

---

## 4. Vue de données

**Nom** : `daily_eurusd_volatility_v1`

**Colonnes** :
- `date` : DATE (YYYY-MM-DD)
- `day_open` : DOUBLE (premier open du jour)
- `day_close` : DOUBLE (dernier close du jour)
- `day_high` : DOUBLE (high max du jour)
- `day_low` : DOUBLE (low min du jour)
- `range_pips` : DOUBLE (range journalier en pips)
- `close_to_close_pips` : DOUBLE (mouvement close-to-close en pips)
- `daily_volatility_pips_v1` : DOUBLE (métrique principale = range_pips)

**Création** : Script `scripts/create_daily_eurusd_volatility_v1.py`

---

## 5. Distribution attendue

**Ordres de grandeur typiques pour EURUSD** (à valider empiriquement) :

- **Jour calme** : range_pips < 30 pips
- **Jour normal** : 30–80 pips
- **Jour volatil** : 80–150 pips
- **Jour extrême** : > 150 pips

**Note** : Ces seuils seront calibrés après analyse de la distribution réelle dans `daily_eurusd_volatility_v1`.

---

## 6. Usage prévu

### 6.1. Validation prédictive

**Jointure** :
```sql
daily_eurusd_volatility_v1 d
JOIN daily_news_score_v1 n
    ON d.date = n.date
```

**Hypothèse à tester** :
- Plus le `daily_news_score_v1` est élevé, plus `daily_volatility_pips_v1` devrait être élevé.
- Les jours avec événements EXTREME devraient avoir une volatilité supérieure à la médiane.

### 6.2. Features de modèle

Utiliser `daily_volatility_pips_v1` comme :
- variable cible dans des modèles de régression
- métrique de performance pour évaluer la prédictivité des scores

---

## 7. Limitations V1

### 7.1. Range vs Realized Variance

Le range est sensible aux outliers (une bougie extrême peut gonfler le range).  
V2 pourra inclure des métriques plus robustes (médiane, percentiles, etc.).

### 7.2. Pas de prise en compte des gaps

Si le marché est fermé, le range ne capture pas les gaps d'ouverture.  
V2 pourra inclure `gap_pips = |open_day_N - close_day_N-1| × 10000`.

### 7.3. Timezone

La définition est basée sur le calendrier Europe/Zurich.  
Pour d'autres timezones (ex : session US), il faudra créer des versions spécifiques.

---

## 8. Roadmap VOL_SPEC_V2 (esquisse)

**Pistes** :
- ATR (Average True Range) sur fenêtre glissante
- Realized variance (somme des carrés des returns M1)
- Volatilité directionnelle (range_up vs range_down)
- Gaps inter-sessions
- Volatilité par session (Asian, European, US)

---

**Fin de VOL_SPEC_V1**
