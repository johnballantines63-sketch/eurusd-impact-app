# 🧮 SCORE_SPEC_V1 – Spécification du score d'impact V1

**Date** : 2025-12-11  
**Version** : SCORE_SPEC_V1  
**Scope** : scoring d'événements macro individuels

---

## 1. Objet

Définir **précisément** la première version du score d'impact d'un événement macro-économique, basé sur :

- l'**impact canonique** en pips (`impact_unified_pips`)
- l'**importance** de l'événement (`importance_n`)
- la **surprise** relative (`surprise_pct`)

Cette spécification est utilisée pour :

- le **ranking** des événements
- la construction de **buckets** (FAIBLE / MOYEN / FORT / EXTRÊME)
- l'alimentation des **modèles et dashboards**.

**Version V1** : calibration interne, sans encore tenir compte de la volatilité réalisée.  
Les futures versions (V2+) pourront ajuster les paramètres après backtests.

---

## 2. Inputs & base de données

### 2.1. Vue canonique de base

**Source** : `events_with_canonical_impact_v1`

**Champs clés utilisés par SCORE_SPEC_V1** :

- `ts_utc`
- `country`
- `event_key`
- `event_title`
- `importance_n` (entier, typiquement 1–5)
- `surprise_pct` (surprise relative, en %)
- `impact_unified_pips` (magnitude canonique IMPACT_SPEC_V1)
- `impact_unified_direction` (+1 = UP, -1 = DOWN)
- `impact_unified_quality` (high / medium / low)

### 2.2. Vue scored (implémentation)

**Source** : `events_with_canonical_impact_scored_v1`

**Champs ajoutés par SCORE_SPEC_V1** :

- `impact_score_base`
- `importance_weight`
- `surprise_abs_capped`
- `surprise_factor`
- `score_impact_v1`
- `score_impact_signed_v1`

---

## 3. Formule du score V1

### 3.1. Étapes intermédiaires

Soit, pour un événement :

- `I = impact_unified_pips` (pips, **≥ 0**)
- `imp = COALESCE(importance_n, 1)` (importance brute, défaut = 1 si NULL)
- `S = COALESCE(surprise_pct, 0.0)` (surprise en pourcentage, peut être négatif)

On calcule :

**1. Base impact (log)**  
   Compression des extrêmes par un log naturel :

   ```
   impact_score_base = ln(1 + I)
   ```

**2. Poids d'importance**

   Importance normalisée sur [0.2, 1.0] :

   ```
   importance_weight = imp / 5.0
   ```

   - `imp = 1` → `weight = 0.2`
   - `imp = 5` → `weight = 1.0`

**3. Surprise cappée & facteur multiplicatif**

   ```
   surprise_abs_capped = min(|S|, 5.0)
   surprise_factor = 1.0 + 0.1 * surprise_abs_capped
   ```

   Donc :
   - `|S| = 0%` → `factor = 1.0`
   - `|S| = 2%` → `factor = 1.2`
   - `|S| ≥ 5%` → `factor = 1.5` (cap à 5%)

### 3.2. Score scalaire (sans signe)

**Score final scalaire (magnitude uniquement)** :

```
score_impact_v1 =
    ln(1 + I)
  * (imp / 5.0)
  * (1.0 + 0.1 * min(|S|, 5.0))
```

**En SQL (DuckDB)**, tel qu'implémenté dans `events_with_canonical_impact_scored_v1` :

```sql
ln(1.0 + v.impact_unified_pips)
    * (COALESCE(v.importance_n, 1)::DOUBLE / 5.0)
    * (1.0 + 0.1 * LEAST(ABS(COALESCE(v.surprise_pct, 0.0)), 5.0))
AS score_impact_v1
```

### 3.3. Score signé

**Score signé** en fonction de la direction de l'impact :

```
score_impact_signed_v1 =
    + score_impact_v1  si impact_unified_direction = +1
    - score_impact_v1  si impact_unified_direction = -1
    NULL               sinon
```

**Implémentation SQL** :

```sql
CASE
    WHEN v.impact_unified_direction = 1 THEN
        ln(1.0 + v.impact_unified_pips)
            * (COALESCE(v.importance_n, 1)::DOUBLE / 5.0)
            * (1.0 + 0.1 * LEAST(ABS(COALESCE(v.surprise_pct, 0.0)), 5.0))
    WHEN v.impact_unified_direction = -1 THEN
        - ln(1.0 + v.impact_unified_pips)
            * (COALESCE(v.importance_n, 1)::DOUBLE / 5.0)
            * (1.0 + 0.1 * LEAST(ABS(COALESCE(v.surprise_pct, 0.0)), 5.0))
    ELSE NULL
END AS score_impact_signed_v1
```

---

## 4. Distribution observée (V1)

Sur l'historique backfillé au 2025-12-11 :

- **Min** ≈ 0.477
- **P25** ≈ 1.812
- **P50 (médiane)** ≈ 2.326
- **P75** ≈ 2.845
- **Max** ≈ 4.719
- **Moyenne** ≈ 2.324

**Top scores** :  
NFP US du 2025-08-01, avec :
- `impact_unified_pips` ≈ 188.4
- `importance_n` = 3
- surprise forte (cappée à 5%)
- `score_impact_v1` ≈ 4.719 (score max observé)

---

## 5. Buckets SCORE_SPEC_V1

### 5.1. Seuils retenus

Seuils basés sur la distribution globale :

- **P50** = 2.326
- **P75** = 2.845
- **P90** = 3.286

**Buckets V1** :

- **LOW** : `score_impact_v1 < 2.326`
- **MEDIUM** : `2.326 ≤ score_impact_v1 < 2.845`
- **HIGH** : `2.845 ≤ score_impact_v1 < 3.286`
- **EXTREME** : `score_impact_v1 ≥ 3.286`

### 5.2. Statistiques par bucket (observées)

Sur l'historique analysé :

| Bucket | % des événements | Score moyen | Impact moyen (pips) | Impact médian (pips) | Max (pips) |
|--------|------------------|-------------|---------------------|----------------------|------------|
| LOW | ~49.9 % | 1.721 | 18.8 | 12.9 | 188.4 |
| MEDIUM | ~24.9 % | 2.578 | 23.8 | 17.6 | 106.4 |
| HIGH | ~15.2 % | 3.041 | 29.6 | 27.9 | 188.4 |
| EXTREME | ~9.9 % | 3.619 | 57.8 | 50.6 | 188.4 |

**Lecture** :

- Les buckets sont équilibrés (~50 / 25 / 15 / 10).
- L'impact moyen/médian augmente de façon monotone de LOW → EXTREME.
- Le bucket EXTREME correspond à des événements avec impact typiquement > 50 pips.

---

## 6. Cas particuliers & outliers

### 6.1. Gros impact en LOW : comportement attendu

**Analyse ciblée** :  
Événements avec :
- `score_impact_v1 < 2.326` (bucket LOW)
- `impact_unified_pips ≥ 120`

**Résultat** : 8 événements, dont :
- NFP / Unemployment Rate (2025-08-01)
- Fed press conference (2022-11-02)

**Caractéristiques typiques** :
- `impact_unified_pips` ≈ 123–188 pips
- `importance_n` = 1
- `surprise_pct` parfois très élevée (mais cappée à 5% dans la formule)
- `score_impact_v1` ≈ 1.4–1.6 → classés en LOW

**Explication** :

Pour un NFP 188.4 pips avec importance 1 :
- `ln(1 + 188.4)` ≈ 5.24
- `importance` = 1/5 = 0.2
- `surprise_factor` (cap 5%) ≈ 1.5

**score** ≈ 5.24 × 0.2 × 1.5 ≈ 1.57 → bucket LOW

---

➡️ **Ce comportement est cohérent avec la définition V1** :

Le score est conçu comme : **Impact × Importance × Surprise**

Si la base considère `importance_n = 1`, l'événement est structurellement dévalorisé, même avec un gros impact en pips.

Le score reflète donc la combinaison des trois dimensions, pas uniquement l'impact brut.

### 6.2. Position officielle

Ces cas ne sont **pas** considérés comme des bugs, mais comme des effets assumés de la formule SCORE_SPEC_V1.

Si la base d'`importance_n` est jugée peu fiable sur certains events (ex : NFP mal taggés importance 1), la correction doit se faire :
- soit en corrigeant `importance_n` dans la DB,
- soit, dans une future version du score (V2), en ajoutant des garde-fous spécifiques (par ex. seuil minimal de bucket en fonction de `impact_unified_pips`).

---

## 7. Usage recommandé

### 7.1. Ce qu'on fait AVEC SCORE_SPEC_V1

- **Ranking d'événements** :
  - par `score_impact_v1` (magnitude)
  - ou `score_impact_signed_v1` (direction UP/DOWN)

- **Filtrage** :
  - ne garder que les buckets HIGH et EXTREME pour certains use cases

- **Feature de modèle** :
  - utiliser le score comme feature synthétique dans les modèles de prédiction de volatilité / mouvement

### 7.2. Ce qu'on NE fait PAS avec V1

- **Ne pas considérer SCORE_SPEC_V1 comme définitif** :
  - V1 ne tient pas encore compte de la volatilité réalisée (mouvement réel après l'événement).

- **Ne pas recalibrer "à la main" les seuils** sans passer par un processus empirique :
  - tests sur plusieurs années
  - corrélation avec la performance des stratégies

---

## 8. Roadmap SCORE_SPEC_V2 (esquisse)

**Pistes pour une future version** :

### Calibration sur volatilité réalisée
- Corréler `score_impact_v1` avec la volatilité / move réel.
- Ajuster les poids (importance, surprise) pour maximiser la corrélation.

### Garde-fous sur les gros impacts
- Par ex. : imposer que `impact_unified_pips ≥ 120` → bucket ≥ HIGH,
  si et seulement si les backtests le justifient.

### Différenciation par type d'événement
- Exemples : NFP, CPI, FOMC peuvent avoir des profils différents.

### Spécification SCORE_SPEC_V2
- Nouveau doc dédié, en conservant SCORE_SPEC_V1 comme référence historique.

---

**Fin de SCORE_SPEC_V1**
