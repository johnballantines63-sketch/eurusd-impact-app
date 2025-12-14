# 📐 IMPACT_SPEC_V1 – Définition canonique de l'impact

**Version** : 1.0  
**Date** : 2025-12-11  
**Scope** : Toutes les fonctions de mesure d'impact de prix (historique, clusters, prédictions)

---

## 1. Objectif

Unifier la définition de l'**impact en pips** utilisée dans le projet pour :

- rendre cohérents :
  - les mesures historiques (`phase1_pips`, `impact_detecte`, etc.),
  - les caches de clusters (`impact_median`, `impact_mean`),
  - les métriques utilisées par les modèles de prédiction ;
- faciliter l'audit, la calibration et la comparaison entre événements.

---

## 2. Définition canonique

### 2.1. Variables

Soit :

- \( P_t \) : prix (bid/ask/mid, ici close ou high/low de la bougie) à l'instant \( t \)
- \( t_0 \) : timestamp de l'événement macro (NFP, CPI, etc.)
- \( \Delta t_{\text{lookback}} \) : fenêtre de lookback (minutes)
- \( \Delta t_{\text{horizon}} \) : fenêtre d'horizon (minutes) après l'événement
- \( \mathcal{W} = [t_0 - \Delta t_{\text{lookback}},\, t_0 + \Delta t_{\text{horizon}}] \)

### 2.2. Baseline

**Baseline canonique** : `event_open`

- On définit la bougie "événement" comme la **première bougie M1 dont l'horodatage est \(\ge t_0\)**.
- Si elle existe :

  \[
  P_{\text{baseline}} = \text{open de la première bougie M1 avec } datetime \ge t_0
  \]

- Sinon (cas rare) : fallback = **close de la dernière bougie avant \( t_0 \)**.

### 2.3. Horizon

- Horizon canonique :  
  \[
  \Delta t_{\text{lookback}} = 5\ \text{minutes}  
  \Delta t_{\text{horizon}} = 120\ \text{minutes}
  \]
- La fenêtre d'analyse \(\mathcal{W}\) est donc :

  \[
  \mathcal{W} = [t_0 - 5\text{ min},\, t_0 + 120\text{ min}]
  \]

En pratique, pour l'impact **phase 1**, on ne regarde que la partie \([t_0,\, t_0 + 120\text{ min}]\) pour le pic, mais on peut utiliser le lookback pour certaines analyses avancées (pré-move, etc.).

### 2.4. Direction et impact absolu

Dans la fenêtre \([t_0, t_0 + \Delta t_{\text{horizon}}]\), on définit :

- Pour chaque bougie \( i \) :

  - \( P_{\text{high}, i} \), \( P_{\text{low}, i} \)
  - \( \text{pips\_up}_i = (P_{\text{high}, i} - P_{\text{baseline}}) \times 10^4 \)
  - \( \text{pips\_down}_i = (P_{\text{baseline}} - P_{\text{low}, i}) \times 10^4 \)

- On définit :
  - \( \text{peak\_high} = \max_i \text{pips\_up}_i \)
  - \( \text{peak\_low} = \max_i \text{pips\_down}_i \)

- **Impact canonique (absolu)** :

  \[
  \text{impact\_pips} = \max(\text{peak\_high}, \text{peak\_low})
  \]

- **Direction** :

  \[
  \text{direction} = 
  \begin{cases}
  +1 & \text{si } \text{peak\_high} > \text{peak\_low} \\
  -1 & \text{sinon}
  \end{cases}
  \]

- **Impact signé (option)** :

  \[
  \text{impact\_signed\_pips} = \text{direction} \times \text{impact\_pips}
  \]

### 2.5. Temps au pic

On note \( t_{\text{peak}} \) l'instant de la bougie qui réalise l'impact canonique :

\[
\text{time\_to\_peak\_minutes} = \frac{t_{\text{peak}} - t_0}{60\text{ s}}
\]

---

## 3. Variantes autorisées

La fonction unifiée permettra de choisir :

- `baseline_method` :
  - `"event_open"` (défaut, canonique)
  - `"event_close"` (close dernière bougie avant \( t_0 \))
  - `"custom_price"` (prix fourni directement)
- `horizon_minutes` :
  - par défaut 120, mais configurable
- `min_pips` :
  - seuil minimal pour considérer l'événement comme "significatif" (ex : 15 ou 20 pips)

---

## 4. Invariants à respecter

1. **Baseline documentée** : chaque fonction qui retourne un impact doit préciser quelle baseline est utilisée.
2. **Horizon explicite** : la fenêtre en minutes doit être passée en paramètre ou clairement fixée.
3. **Unités** : tous les impacts sont en **pips** (pas en %).
4. **Direction séparée** : l'impact est renvoyé au moins en absolu, avec la direction comme champ séparé.

---

## 5. Migration

- `measure_impact_from_finnhub()` → sera refondu pour déléguer à `calculate_impact_unified` avec `baseline_method="event_open"`.
- `detect_pattern_type()` → pourra **en plus** calculer un impact unifié à partir de `event_timestamp`, pour comparer au "impact_detecte" historique.
- Les métriques de clusters (`impact_median`, `impact_mean`) seront recalculées, à terme, avec la métrique unifiée.

---
