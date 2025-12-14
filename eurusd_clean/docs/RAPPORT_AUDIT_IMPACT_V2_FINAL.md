# 📊 RAPPORT FINAL – AUDIT & UNIFICATION DES DÉFINITIONS D'IMPACT

**Date** : 2025-12-11  
**Version** : V2 (refonte validée)

---

## 1. RÉSUMÉ EXÉCUTIF

### 1.1. Objectif

Unifier les différentes définitions d'**impact en pips** utilisées dans le projet et valider la nouvelle implémentation canonique basée sur **IMPACT_SPEC_V1**.

Trois définitions ont été comparées :

1. **impact_detecte_pips**  
   - Source : `detect_pattern_type()` (Planificateur)  
   - Baseline : segment détecté (logique de scan / cluster)  
   - Usage : UI Planificateur, patterns SINGLE_WAVE / DOUBLE_WAVE

2. **phase1_pips_legacy**  
   - Source : `measure_impact_from_finnhub(..., use_unified=False)`  
   - Logique historique interne (pré-refonte)  
   - Usage : `event_impacts_v2`, scripts historiques

3. **impact_unified_pips**  
   - Source : `measure_impact_from_finnhub(..., use_unified=True)`  
   - Implémentation canonique `calculate_impact_unified()` (IMPACT_SPEC_V1)  
   - Baseline = `event_open` (open première bougie événement)  
   - Horizon = 120 minutes après l'événement

### 1.2. Résultats clés

- ✅ **Refonte validée** :  
  `phase1_pips_legacy` et `impact_unified_pips` sont **strictement identiques**  
  → corrélation = 1.000, ratio = 1.0 (médiane, moyenne, min, max)

- 📈 **impact_detecte_pips vs phase1/impact_unified** (n = 98) :
  - Corrélation = **0.589** (modérée)
  - Ratio médian `impact_detecte_pips / phase1` = **0.77**
  - Ratio moyen ≈ **0.83** (écart-type ≈ 0.34)

### 1.3. Conclusions

1. La refonte de `measure_impact_from_finnhub()` via `calculate_impact_unified()` est **validée** :  
   la nouvelle version reproduit exactement l'ancienne logique (legacy).

2. L'**impact unifié** (`impact_unified_pips`) devient la **définition canonique** d'impact macro :
   - Baseline explicite : `event_open`
   - Horizon standardisé : 120 minutes
   - Une seule implémentation centrale : `src/core/impact_unified.py`

3. `impact_detecte_pips` et `impact_unified_pips` restent **différents mais corrélés** :  
   - Corrélation modérée (~0.59)  
   - `impact_detecte_pips` ≈ **77 %** de `impact_unified_pips` en médiane  
   → `impact_detecte_pips` est un **score de pattern** (mouvement détecté), pas la métrique canonique d'impact.

---

## 2. MÉTHODOLOGIE V2

### 2.1. Échantillon

- Source : table `events` (DuckDB)
- Filtre : événements **US Non-Farm Payrolls** (NFP)
- Période : 2020-01-01 → 2024-11-01
- Limite : 100 événements (NFP US)
- Lignes retenues pour l'audit V2 : événements avec **≥ 2 mesures disponibles**  
  → 98 événements analysés (comme dans V1)

### 2.2. Mesures calculées

Pour chaque événement NFP (`ts_utc`) :

1. **impact_detecte_pips (Planificateur)**  
   Via `detect_pattern_type()` chargé dynamiquement depuis  
   `streamlit_app/pages/5_Planificateur_V3.2_Formule_Lineaire.py` :

   - Chargement des prix m1 de la journée (`prices_finnhub_m1`)
   - Chargement des événements du jour via `load_events_for_date()`
   - Enrichissement surprises via `enrich_events_with_surprises()`
   - Appel de `detect_pattern_type()` avec :
     - `min_pips = 35.0`
     - `timezone = Europe/Zurich`
     - `cluster_anchor_time = event_ts (Bern time)`

   Extraction : `movement["impact_pips"]`.

2. **phase1_pips_legacy**  
   Via `measure_impact_from_finnhub(..., use_unified=False)` :

   - Chargement des prix via `get_finnhub_prices_at_event_time()`  
   - Baseline :
     - `open` de la première bougie avec `datetime >= event_timestamp`
     - Fallback : `close` dernière bougie avant l'événement
   - Horizon : 120 minutes après l'événement
   - Impact = max en valeur absolue des pips UP/DOWN
   - Résultat : `result["impact_pips"]`

3. **impact_unified_pips (canonique)**  
   Via `measure_impact_from_finnhub(..., use_unified=True)` qui appelle :

   ```python
   unified_result = calculate_impact_unified(
       df_prices=df_prices,
       event_timestamp=event_timestamp,
       baseline_method="event_open",
       horizon_minutes=lookahead_minutes,  # 120
       lookback_minutes=lookback_minutes,  # 5
       min_pips=None,                      # pas de filtre
       timezone_str="Europe/Zurich",
       debug=debug,
   )
   ```

   Extraction : `unified_result.impact_pips`.

### 2.3. Script d'audit V2

**Fichier** : `scripts/compare_impact_definitions_v2.py`

**Fonctionnalités** :
- Import dynamique du Planificateur
- Appels successifs :
  - `calculate_impact_detecte(...)`
  - `measure_phase1(..., use_unified=False)`
  - `measure_phase1(..., use_unified=True)`
- Construction d'un DataFrame avec :
  - `impact_detecte_pips`
  - `phase1_pips_legacy`
  - `impact_unified_pips`
- Stats pair à pair :
  - `impact_detecte_pips` vs `phase1_pips_legacy`
  - `impact_detecte_pips` vs `impact_unified_pips`
  - `phase1_pips_legacy` vs `impact_unified_pips`

---

## 3. VALIDATION DE LA REFONTE (LEGACY vs UNIFIED)

### 3.1. Résultat principal

**Comparaison** : `phase1_pips_legacy` vs `impact_unified_pips`

- **Corrélation Pearson** : **1.000**
- **Ratio** `impact_unified_pips / phase1_pips_legacy` :
  - Médiane : **1.0**
  - Moyenne : **1.0**
  - Min : **1.0**
  - Max : **1.0**

**Conclusion** :  
L'implémentation canonique `calculate_impact_unified()` reproduit exactement la logique historique de `measure_impact_from_finnhub()`.

**On peut donc** :
- Considérer `phase1_pips_legacy` comme un alias historique de `impact_unified_pips`
- Migrer progressivement tout le code vers `impact_unified_pips` sans risque de rupture de métrique.

---

## 4. COMPARAISON IMPACT_DÉTECTÉ vs PHASE1/UNIFIED

### 4.1. impact_detecte_pips vs phase1_pips_legacy

**Taille échantillon** : n = 98

- **Corrélation Pearson** : **0.589** (corrélation modérée)
- **Ratio** `impact_detecte_pips / phase1_pips_legacy` :
  - Médiane : **0.77**
  - Moyenne : **~0.83**
  - Écart-type : **~0.34**

### 4.2. impact_detecte_pips vs impact_unified_pips

Sans surprise, mêmes chiffres (legacy = unified) :

- **Corrélation Pearson** : **0.589**
- **Ratio médian** : **0.77**
- **Ratio moyen** : **~0.83**

### 4.3. Interprétation

**Corrélation modérée (~0.59)**  
→ Les deux mesures sont liées, mais ne capturent pas la même chose :

- `impact_unified_pips` : impact macro standardisé depuis `event_open` (baseline fixe)
- `impact_detecte_pips` : impact du mouvement détecté (segment de prix, baseline segment)

**Biais systématique (~0.77)**  
→ En médiane, `impact_detecte_pips` ≈ 77 % de `impact_unified_pips`

**Causes probables** :
- Filtre `min_pips = 35` dans `detect_pattern_type()`  
  → exclut les petits mouvements, tronque certains segments
- Baseline de `detect_pattern_type()` = extrémité du segment détecté (`low`/`high`),  
  qui peut être postérieure à la baseline canonique `event_open`.

**Conclusion opérationnelle** :

- `impact_unified_pips` doit être utilisé comme **référence canonique** pour :
  - scoring d'événements
  - stats historiques
  - stockage dans la DB (`event_impacts_vX`)

- `impact_detecte_pips` reste utile comme **métrique locale de pattern** :
  - pour décrire le mouvement du cluster
  - pour l'UI du Planificateur
  - mais **pas** comme métrique macro standard de comparaison entre événements.

---

## 5. DÉFINITION CANONIQUE RETENUE

### 5.1. Spécification IMPACT_SPEC_V1 (rappel)

**Définition canonique (macro impact)** :

- **Baseline** : `event_open`
  → `open` de la première bougie M1 avec `datetime >= event_timestamp`
  → fallback : `close` de la dernière bougie avant l'événement

- **Horizon** : `horizon_minutes = 120`
  → fenêtre de 120 minutes après l'événement

- **Impact** :
  - `pips_high = (high.max() - baseline_price) * 10000`
  - `pips_low = (baseline_price - low.min()) * 10000`
  - `impact_pips = max(pips_high, pips_low)`
  - `direction = +1` si `pips_high > pips_low`, sinon `-1`

**Implémentation** : `calculate_impact_unified()`  
**Fichier** : `src/core/impact_unified.py`  
**Résultat** : `ImpactResult`

### 5.2. Décision

**Décision finale** :

✅ La métrique canonique d'impact du projet est désormais  
`impact_unified_pips` = résultat de `calculate_impact_unified()` (IMPACT_SPEC_V1),  
exposée via `measure_impact_from_finnhub(..., use_unified=True)`.

**Conséquences** :
- `phase1_pips_legacy` = alias historique de `impact_unified_pips`
- Toute nouvelle fonctionnalité doit utiliser uniquement `impact_unified_pips` comme référence.

---

## 6. PLAN DE MIGRATION

### 6.1. Code déjà refondu

**Module canonique**  
**Fichier** : `src/core/impact_unified.py`

Contient :
- `ImpactResult` (dataclass)
- `calculate_impact_unified(...)`

**measure_impact_from_finnhub()**  
**Fichier** : `src/core/price_loader_finnhub.py`

- Paramètre : `use_unified: bool = True` (défaut)
- Nouveau flux :
  - `use_unified=True` → utilise `calculate_impact_unified()`
  - `use_unified=False` → utilise l'ancienne logique (legacy)

**Planificateur (impact unifié affiché en beta)**  
**Fichier** : `streamlit_app/pages/5_Planificateur_V3.2_Formule_Lineaire.py`

Ajout :
- Import `from core.impact_unified import calculate_impact_unified`
- Calcul `impact_unified_pips` dans `detect_pattern_type()` (et variantes DOUBLE_WAVE)
- Affichage UI :
  - Colonne 1 : **Impact détecté**
  - Colonne 2 : **Impact unifié (beta)** (baseline=event_open, horizon=120min)

**Guide de test**  
**Fichier** : `docs/GUIDE_TEST_IMPACT_UNIFIE.md`

- Cas de test recommandés (NFP propres, cas extrêmes)
- Checklist UI & cohérence

### 6.2. Étapes restantes

**Remplacer `phase1_pips` par `impact_unified_pips` dans la DB**

Soit :
- Nouvelle colonne `impact_unified_pips` dans `event_impacts_v2` / v3
Soit :
- Nouvelle table normalisée pour les impacts canoniques

**Documenter clairement le mapping** `phase1_pips_legacy` ≡ `impact_unified_pips`.

**Mettre à jour la cartographie**

- `CARTOGRAPHIE_IMPACT.md`
- `RESUME_CARTOGRAPHIE_IMPACT_POUR_AUDIT.md`
- `IMPACT_SPEC_V1.md` (déjà créé, à pointer comme référence unique)

**Communiquer les invariants**

- Baseline = `event_open`
- Horizon = 120 minutes
- Une seule fonction canonique : `calculate_impact_unified`
- `impact_detecte_pips` = métrique locale de pattern (UI), non canonique.

---

## 7. CONCLUSION

L'audit V2 confirme :

✅ **La refonte de `measure_impact_from_finnhub()` est correcte** :  
`phase1_pips_legacy` et `impact_unified_pips` sont identiques (corrélation = 1.000).

📈 **La relation entre `impact_detecte_pips` et la métrique canonique est** :
- Corrélation modérée (~0.59)
- Biais médian : `impact_detecte_pips` ≈ 0.77 × `impact_unified_pips`

🧭 **`impact_unified_pips` est désormais la boussole officielle du projet** pour mesurer l'impact macro d'un événement.

Les prochaines évolutions (scoring, ranking, dashboards, optimisation) doivent toutes se baser sur cette définition canonique, en gardant `impact_detecte_pips` comme outil complémentaire pour l'analyse fine des patterns de prix.

---

**Fin du rapport**
