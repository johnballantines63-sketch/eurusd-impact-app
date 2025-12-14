# 📊 RAPPORT D'AUDIT COMPARATIF DES DÉFINITIONS D'IMPACT

**Date** : 2025-12-11  
**Script** : `scripts/compare_impact_definitions.py`  
**Échantillon** : 100 événements NFP US (2020-01-10 → 2024-11-01)  
**Événements analysés** : 98 (2 avec valeurs manquantes)

---

## 📋 TABLE DES MATIÈRES

1. [Résumé exécutif](#1-résumé-exécutif)
2. [Méthodologie](#2-méthodologie)
3. [Résultats statistiques](#3-résultats-statistiques)
4. [Analyse des cas extrêmes](#4-analyse-des-cas-extrêmes)
5. [Interprétation](#5-interprétation)
6. [Recommandations](#6-recommandations)
7. [Annexes](#7-annexes)

---

## 1. RÉSUMÉ EXÉCUTIF

### 1.1. Objectif

Comparer numériquement deux définitions d'impact utilisées dans le projet :
- **impact_detecte_pips** : Ce que retourne `detect_pattern_type()` → `movement['impact_pips']`
- **phase1_pips** : Ce que mesure `measure_impact_from_finnhub()` ou ce qui est stocké dans `event_impacts_v2`

### 1.2. Constat principal

**Les deux définitions sont statistiquement indépendantes** (corrélation Pearson = 0.048), confirmant l'incohérence identifiée dans la cartographie.

### 1.3. Résultats clés

| Métrique | Valeur | Interprétation |
|----------|--------|----------------|
| **Corrélation Pearson** | 0.048 | Quasi-indépendance statistique |
| **Ratio médian** | 1.03 | Similaire en médiane |
| **Ratio moyen** | 2.94 | Distribution très asymétrique |
| **Écart-type ratio** | 3.88 | Variabilité extrême |
| **IQR ratio** | 0.70 - 4.15 | 50% des ratios entre 0.70x et 4.15x |

### 1.4. Conclusion

Les deux définitions mesurent des concepts différents :
- **impact_detecte_pips** : Impact du mouvement détecté (baseline = segment détecté)
- **phase1_pips** : Impact depuis l'événement (baseline = open première bougie événement)

**Action requise** : Unification des définitions avec une fonction commune et une baseline explicite.

---

## 2. MÉTHODOLOGIE

### 2.1. Sélection de l'échantillon

**Critères** :
- Événements US NFP (Non-Farm Payrolls)
- Période : 2020-01-01 → 2024-11-01
- Limite : 100 événements (premier audit)

**Requête SQL** :
```sql
SELECT ts_utc, event_key, event_title, country, actual, estimate, previous
FROM events
WHERE country = 'US'
  AND DATE(ts_utc) >= '2020-01-01'
  AND DATE(ts_utc) <= '2024-11-01'
  AND (
      LOWER(event_key) LIKE '%nonfarm payrolls%'
      OR LOWER(event_key) LIKE '%non farm payrolls%'
      OR LOWER(event_title) LIKE '%nonfarm payrolls%'
      OR LOWER(event_title) LIKE '%employment situation%'
  )
ORDER BY ts_utc ASC
LIMIT 100
```

**Résultat** : 100 événements trouvés, 98 analysés avec succès.

### 2.2. Calcul de impact_detecte_pips

**Méthode** :
1. Charger les prix M1 du jour concerné (`prices_finnhub_m1`)
2. Charger les événements du jour via `load_events_for_date()`
3. Enrichir les événements via `enrich_events_with_surprises()`
4. Appeler `detect_pattern_type()` avec :
   - `min_pips = 35.0`
   - `timezone = 'Europe/Zurich'`
   - `cluster_anchor_time = timestamp de l'événement`
5. Extraire `movement['impact_pips']`

**Définition** :
- **Baseline** : `low` (UP) ou `high` (DOWN) du segment détecté par `scan_price_movements()`
- **Pic** : `high.max()` (UP) ou `low.min()` (DOWN) du même segment
- **Horizon** : Segment détecté (peut commencer avant l'événement)
- **Filtre** : `min_pips = 35.0` (seuil minimum)

**Référence** : `streamlit_app/pages/5_Planificateur_V3.2_Formule_Lineaire.py`, fonction `detect_pattern_type()` (lignes 2114-2412)

### 2.3. Calcul de phase1_pips

**Méthode** :
1. Essayer d'abord `event_impacts_v2` (si table existe)
2. Fallback : `measure_impact_from_finnhub()` avec :
   - `lookback_minutes = 5`
   - `lookahead_minutes = 120`
   - `event_timestamp = timestamp de l'événement`

**Définition** :
- **Baseline** : `open` de la première bougie M1 à l'événement ou après (`prices_at_event.iloc[0]['open']`)
- **Pic** : `high.max()` (UP) ou `low.min()` (DOWN) dans une fenêtre de 120 minutes après l'événement
- **Horizon** : 120 minutes après l'événement (fixe)
- **Filtre** : Aucun

**Référence** : `src/core/price_loader_finnhub.py`, fonction `measure_impact_from_finnhub()` (lignes 96-292)

### 2.4. Construction du DataFrame de comparaison

**Colonnes** :
- `event_ts` : Timestamp de l'événement
- `event_date` : Date de l'événement
- `event_title` : Titre de l'événement
- `impact_detecte_pips` : Impact détecté (via `detect_pattern_type()`)
- `phase1_pips` : Impact phase1 (via `measure_impact_from_finnhub()`)
- `diff_pips` : Différence absolue (`impact_detecte_pips - phase1_pips`)
- `ratio_detecte_sur_phase1` : Ratio (`impact_detecte_pips / phase1_pips`)

**Filtrage** :
- Exclure les lignes où l'une des deux valeurs est manquante
- Exclure les lignes où `phase1_pips <= 0` (pour calcul du ratio)

---

## 3. RÉSULTATS STATISTIQUES

### 3.1. Distribution des deux mesures

| Statistique | impact_detecte_pips | phase1_pips |
|-------------|---------------------|-------------|
| **Count** | 98.0 | 98.0 |
| **Mean** | 41.6 pips | 35.1 pips |
| **Std** | 18.1 pips | 31.8 pips |
| **Min** | 16.1 pips | 2.9 pips |
| **25%** | 27.8 pips | 11.5 pips |
| **50% (Médiane)** | 39.9 pips | 25.8 pips |
| **75%** | 51.3 pips | 47.9 pips |
| **Max** | 109.8 pips | 145.5 pips |

**Observations** :
- **impact_detecte_pips** : Distribution plus concentrée (std = 18.1), médiane proche de la moyenne
- **phase1_pips** : Distribution plus dispersée (std = 31.8), avec des valeurs extrêmes (max = 145.5 pips)
- **Médiane impact_detecte > Médiane phase1** : 39.9 vs 25.8 pips (+54%)

### 3.2. Corrélation

**Corrélation Pearson** : **0.048**

**Interprétation** :
- Corrélation quasi-nulle (< 0.1)
- Les deux mesures sont statistiquement indépendantes
- Aucune relation linéaire entre les deux définitions

**Matrice de corrélation** :
```
                     impact_detecte_pips  phase1_pips
impact_detecte_pips              1.00000      0.04785
phase1_pips                      0.04785      1.00000
```

### 3.3. Ratio impact_detecte / phase1_pips

| Statistique | Valeur |
|-------------|--------|
| **Count** | 98.0 |
| **Mean** | 2.94 |
| **Std** | 3.88 |
| **Min** | 0.27 |
| **25%** | 0.70 |
| **50% (Médiane)** | **1.03** |
| **75%** | 4.15 |
| **Max** | 21.41 |

**Observations** :
- **Médiane = 1.03** : En médiane, les deux mesures sont similaires
- **Moyenne = 2.94** : Distribution très asymétrique avec valeurs extrêmes
- **IQR = 0.70 - 4.15** : 50% des ratios entre 0.70x et 4.15x
- **Écart-type élevé** : 3.88 (variabilité extrême)

### 3.4. Différence absolue (impact_detecte - phase1_pips)

| Statistique | Valeur |
|-------------|--------|
| **Count** | 98.0 |
| **Mean** | +6.5 pips |
| **Std** | 35.8 pips |
| **Min** | -106.3 pips |
| **25%** | -15.5 pips |
| **50% (Médiane)** | **+0.8 pips** |
| **75%** | +32.4 pips |
| **Max** | +90.2 pips |

**Observations** :
- **Médiane = +0.8 pips** : Légèrement plus élevé en médiane
- **Moyenne = +6.5 pips** : Asymétrie vers les valeurs positives
- **Écart-type élevé** : 35.8 pips (grande variabilité)
- **Plage** : -106.3 à +90.2 pips (écarts importants dans les deux sens)

---

## 4. ANALYSE DES CAS EXTRÊMES

### 4.1. Top 10 événements (ratio le plus élevé)

**Cas où impact_detecte >> phase1_pips**

| Date | Événement | impact_detecte | phase1_pips | Ratio | Diff |
|------|-----------|----------------|-------------|-------|------|
| 2024-03-08 | Non Farm Payrolls | 62.1 | 2.9 | **21.41** | +59.2 |
| 2024-10-04 | Non Farm Payrolls | 65.4 | 4.4 | **14.86** | +61.0 |
| 2024-06-07 | Non Farm Payrolls | 66.4 | 7.5 | **8.85** | +58.9 |
| 2023-09-01 | Non Farm Payrolls | 39.0 | 5.2 | **7.50** | +33.8 |
| 2024-05-03 | Non Farm Payrolls | 60.8 | 9.2 | **6.61** | +51.6 |
| 2024-04-05 | Non Farm Payrolls | 41.7 | 7.5 | **5.56** | +34.2 |
| 2023-02-03 | Non Farm Payrolls | 109.8 | 19.6 | **5.60** | +90.2 |
| 2023-05-05 | Non Farm Payrolls | 41.6 | 7.8 | **5.33** | +33.8 |
| 2023-06-02 | Non Farm Payrolls | 30.2 | 6.0 | **5.03** | +24.2 |
| 2024-02-02 | Non Farm Payrolls | 58.5 | 14.0 | **4.18** | +44.5 |

**Analyse** :
- **Pattern commun** : `phase1_pips` très faible (< 10 pips dans 7 cas sur 10)
- **Hypothèse** : Le mouvement détecté commence **avant** l'événement, donc `impact_detecte` capture un mouvement plus large
- **Exemple 2024-03-08** : `impact_detecte = 62.1 pips` vs `phase1_pips = 2.9 pips` (ratio 21.41x)
  - Le mouvement détecté commence probablement avant 14:30
  - `phase1_pips` mesure seulement depuis 14:30, donc rate le début du mouvement

### 4.2. Bottom 10 événements (ratio le plus faible)

**Cas où phase1_pips >> impact_detecte**

| Date | Événement | impact_detecte | phase1_pips | Ratio | Diff |
|------|-----------|----------------|-------------|-------|------|
| 2022-11-04 | Non Farm Payrolls | 39.2 | 145.5 | **0.27** | -106.3 |
| 2022-11-04 | Nonfarm Payrolls Private | 39.2 | 145.5 | **0.27** | -106.3 |
| 2023-01-06 | Non Farm Payrolls | 37.5 | 103.7 | **0.36** | -66.2 |
| 2023-01-06 | Nonfarm Payrolls Private | 37.5 | 103.7 | **0.36** | -66.2 |
| 2021-02-05 | Non-Farm Payrolls | 18.1 | 49.0 | **0.37** | -30.9 |
| 2023-03-10 | Non Farm Payrolls | 39.9 | 100.1 | **0.40** | -60.2 |
| 2023-03-10 | Nonfarm Payrolls Private | 39.9 | 100.1 | **0.40** | -60.2 |
| 2020-05-08 | Non-Farm Payrolls | 16.4 | 35.3 | **0.46** | -18.9 |
| 2021-06-04 | Non-Farm Payrolls | 33.3 | 70.0 | **0.48** | -36.7 |
| 2022-03-04 | Non Farm Payrolls | 26.4 | 48.1 | **0.55** | -21.7 |

**Analyse** :
- **Pattern commun** : `phase1_pips` très élevé (> 48 pips dans 8 cas sur 10)
- **Hypothèse** : Le mouvement commence **après** l'événement, donc `phase1_pips` capture un mouvement plus large dans la fenêtre 120 min
- **Exemple 2022-11-04** : `impact_detecte = 39.2 pips` vs `phase1_pips = 145.5 pips` (ratio 0.27x)
  - Le mouvement détecté est probablement un mouvement partiel
  - `phase1_pips` mesure le pic maximum dans les 120 minutes, donc capture un mouvement plus large

### 4.3. Cas "normaux" (ratio proche de 1.0)

**Événements avec ratio entre 0.9 et 1.1** :

| Date | Événement | impact_detecte | phase1_pips | Ratio | Diff |
|------|-----------|----------------|-------------|-------|------|
| 2020-01-10 | Non-Farm Payrolls | 19.8 | 19.8 | **1.00** | 0.0 |
| 2020-04-03 | Non-Farm Payrolls | 26.0 | 25.7 | **1.01** | +0.3 |
| 2022-05-06 | Non Farm Payrolls | 26.6 | 25.4 | **1.05** | +1.2 |
| 2021-10-08 | Non-Farm Payrolls | 20.0 | 20.2 | **0.99** | -0.2 |
| 2021-11-05 | Non-Farm Payrolls | 23.7 | 25.6 | **0.93** | -1.9 |
| 2020-11-06 | Non-Farm Payrolls | 25.2 | 27.6 | **0.91** | -2.4 |

**Analyse** :
- **6 événements** sur 98 (6%) ont un ratio proche de 1.0
- Dans ces cas, les deux définitions donnent des résultats similaires
- **Hypothèse** : Le mouvement détecté commence à peu près au moment de l'événement

---

## 5. INTERPRÉTATION

### 5.1. Pourquoi la corrélation est si faible (0.048) ?

**Raison principale** : Différence de baseline

1. **impact_detecte_pips** :
   - Baseline = `low`/`high` du **segment détecté** (peut commencer avant l'événement)
   - Horizon = Segment détecté (variable)
   - Filtre = `min_pips = 35.0` (exclut les petits mouvements)

2. **phase1_pips** :
   - Baseline = `open` première bougie **à l'événement** (fixe)
   - Horizon = 120 minutes après événement (fixe)
   - Filtre = Aucun (capture tous les mouvements)

**Conséquence** :
- Si le mouvement commence **avant** l'événement → `impact_detecte` > `phase1_pips`
- Si le mouvement commence **après** l'événement → `phase1_pips` > `impact_detecte`
- Si le mouvement commence **à** l'événement → Les deux sont similaires

### 5.2. Pourquoi la distribution est si asymétrique ?

**Ratio médian = 1.03** mais **ratio moyen = 2.94**

**Explication** :
- La majorité des événements (médiane) ont des ratios proches de 1.0
- Mais quelques cas extrêmes tirent la moyenne vers le haut :
  - 2024-03-08 : ratio = 21.41
  - 2024-10-04 : ratio = 14.86
  - 2024-06-07 : ratio = 8.85

**Distribution** :
- 50% des ratios entre 0.70 et 4.15 (IQR)
- Quelques valeurs extrêmes (ratios > 10) tirent la moyenne vers le haut

### 5.3. Quelle définition est "meilleure" ?

**Réponse** : **Aucune n'est intrinsèquement meilleure**, elles mesurent des concepts différents :

- **impact_detecte_pips** :
  - ✅ Capture le mouvement réellement détecté (même s'il commence avant)
  - ✅ Filtre les petits mouvements (< 35 pips)
  - ❌ Baseline variable (dépend du segment détecté)
  - ❌ Peut manquer des mouvements qui commencent après l'événement

- **phase1_pips** :
  - ✅ Baseline fixe et reproductible (à l'événement)
  - ✅ Horizon fixe (120 min, standardisé)
  - ✅ Capture tous les mouvements (pas de filtre)
  - ❌ Peut rater le début du mouvement si il commence avant l'événement
  - ❌ Peut capturer des mouvements non liés à l'événement (dans les 120 min)

---

## 6. RECOMMANDATIONS

### 6.1. Unification des définitions

**Action prioritaire** : Créer une fonction commune avec paramètres configurables :

```python
def calculate_impact_unified(
    df_prices: pd.DataFrame,
    event_timestamp: pd.Timestamp,
    baseline_method: str = 'event_open',  # 'event_open', 'segment_low', 'segment_high', 'custom'
    horizon_minutes: int = 120,
    min_pips: Optional[float] = None,
    custom_baseline_price: Optional[float] = None
) -> Dict:
    """
    Calcule l'impact de manière unifiée.
    
    Args:
        baseline_method: 
            - 'event_open': open première bougie événement (comme phase1_pips)
            - 'segment_low': low segment détecté (comme impact détecté UP)
            - 'segment_high': high segment détecté (comme impact détecté DOWN)
            - 'custom': utiliser custom_baseline_price
        horizon_minutes: Fenêtre après événement
        min_pips: Seuil minimum (None = pas de filtre)
    """
    pass
```

### 6.2. Choix de la définition de référence

**Recommandation** : Utiliser **`event_open`** comme baseline par défaut pour :
- ✅ Reproductibilité (baseline fixe)
- ✅ Comparabilité (même baseline pour tous les événements)
- ✅ Standardisation (horizon fixe)

**Mais** : Garder la possibilité de calculer avec `segment_low`/`segment_high` pour des cas spécifiques.

### 6.3. Migration progressive

**Étape 1** : Créer la fonction unifiée (sans modifier le code existant)

**Étape 2** : Migrer `detect_pattern_type()` pour utiliser la fonction unifiée avec `baseline_method='segment_low'` ou `'segment_high'`

**Étape 3** : Migrer `measure_impact_from_finnhub()` pour utiliser la fonction unifiée avec `baseline_method='event_open'`

**Étape 4** : Mettre à jour le cache des clusters pour utiliser la définition unifiée

**Étape 5** : Documenter les différences et conversions possibles

### 6.4. Documentation

**Action** : Ajouter des commentaires explicites dans le code :

```python
# ⚠️ DÉFINITION IMPACT : "Impact détecté"
# Baseline: low/high du segment détecté (peut être avant événement)
# Horizon: Segment détecté par scan_price_movements()
# Usage: Affichage UI Planificateur, cache clusters
impact_pips = (peak_price - baseline_price) * 10000

# ⚠️ DÉFINITION IMPACT : phase1_pips
# Baseline: open première bougie événement (fixe à l'événement)
# Horizon: 120 minutes après événement (fixe)
# Usage: Table event_impacts_v2, historique événements individuels
phase1_pips = measure_impact_from_finnhub(...)['impact_pips']
```

---

## 7. ANNEXES

### 7.1. Liste complète des événements analysés

**Fichier** : Résultats complets disponibles dans la sortie du script `compare_impact_definitions.py`

**Résumé** :
- 98 événements avec les deux valeurs disponibles
- 2 événements avec valeurs manquantes :
  - 2020-02-07 : `impact_detecte` manquant
  - 2024-08-21 : `impact_detecte` manquant (événement de révision annuelle)

### 7.2. Distribution temporelle

**Période analysée** : 2020-01-10 → 2024-11-01

**Répartition** :
- 2020 : 12 événements
- 2021 : 11 événements
- 2022 : 12 événements
- 2023 : 12 événements
- 2024 : 11 événements

### 7.3. Commandes de reproduction

**Exécuter l'audit** :
```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean
python scripts/compare_impact_definitions.py
```

**Modifier l'échantillon** :
- Modifier `limit` dans `get_nfp_events()` (ligne ~70)
- Modifier `start_date` et `end_date` dans `main()` (ligne ~300)

### 7.4. Références

**Documents de cartographie** :
- `docs/CARTOGRAPHIE_IMPACT.md` : Cartographie complète des définitions d'impact
- `docs/RESUME_CARTOGRAPHIE_IMPACT_POUR_AUDIT.md` : Résumé pour audit/refonte

**Code source** :
- `scripts/compare_impact_definitions.py` : Script d'audit comparatif
- `streamlit_app/pages/5_Planificateur_V3.2_Formule_Lineaire.py` : Définition "Impact détecté"
- `src/core/price_loader_finnhub.py` : Définition `phase1_pips`

---

## 8. CONCLUSION

L'audit comparatif confirme l'incohérence identifiée dans la cartographie :
- **Corrélation quasi-nulle** (0.048) entre les deux définitions
- **Distribution très asymétrique** (ratio moyen = 2.94 vs médiane = 1.03)
- **Cas extrêmes fréquents** (ratios de 0.27 à 21.41)

**Action requise** : Unification des définitions avec une fonction commune et une baseline explicite.

**Prochaine étape** : Créer la fonction unifiée `calculate_impact_unified()` et migrer progressivement le code existant.

---

**Fin du rapport**
