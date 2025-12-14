# Chaîne de vues : events_with_ts_local_v1

**Date :** 2025-12-13  
**Objectif :** Documenter la chaîne complète de vues jusqu'à la table source

---

## 🔗 Chaîne Complète

```
events_with_ts_local_v1
    ↓
events_with_canonical_impact_scored_bucketed_v1
    ↓
events_with_canonical_impact_scored_v1
    ↓
events_with_canonical_impact_v1
    ↓
events (TABLE) + event_impacts_v2 (probablement)
```

---

## 📋 Détails par Vue

### 1. events_with_ts_local_v1

**Source :** `events_with_canonical_impact_scored_bucketed_v1`

**Transformation :**
- Alias `ts_utc AS ts_local` pour clarifier la sémantique
- Conserve toutes les colonnes de la vue source

**Note importante :** 
- `ts_utc` dans la table `events` est en fait en Europe/Zurich (voir TIMEZONE_NOTE.md)
- `ts_local` = alias pour clarifier cette sémantique

---

### 2. events_with_canonical_impact_scored_bucketed_v1

**Source :** `events_with_canonical_impact_scored_v1`

**Transformation :**
- Ajoute `score_bucket_v1` basé sur `score_impact_v1`:
  - `score_impact_v1 < 2.326` → `'LOW'`
  - `score_impact_v1 < 2.845` → `'MEDIUM'`
  - `score_impact_v1 < 3.286` → `'HIGH'`
  - Sinon → `'EXTREME'`

---

### 3. events_with_canonical_impact_scored_v1

**Source :** `events_with_canonical_impact_v1`

**Transformation :**
- Calcule `score_impact_v1` :
  - `impact_score_base = ln(1 + impact_unified_pips)`
  - `importance_weight = importance_n / 5.0`
  - `surprise_abs_capped = min(abs(surprise_pct), 5.0)`
  - `surprise_factor = 1 + 0.1 * surprise_abs_capped`
  - `score_impact_v1 = impact_score_base * importance_weight * surprise_factor`
- Calcule `score_impact_signed_v1` (avec direction)

---

### 4. events_with_canonical_impact_v1

**Source :** `events` (TABLE) + `event_impacts_v2` (probablement)

**Transformation :**
- Joint `events` avec `event_impacts_v2` pour ajouter:
  - `surprise_pct`
  - `impact_unified_pips`
  - `impact_unified_direction`
  - `impact_unified_time_to_peak_minutes`
  - `impact_unified_start_price`
  - `impact_unified_peak_price`
  - `impact_unified_quality`

---

## 🗄️ Tables Sources Finales

### Table principale : `events`

**Lignes :** 150,219  
**Colonnes principales :**
- `ts_utc` (TIMESTAMP WITH TIME ZONE) — ⚠️ En fait Europe/Zurich
- `country`
- `event_key`
- `event_title`
- `importance_n`
- `actual`
- `previous`
- `estimate`
- `forecast`
- ...

### Table secondaire : `event_impacts_v2`

**Lignes :** 8,344  
**Usage :** Jointure avec `events` pour ajouter les impacts calculés

---

## ⚠️ Notes Importantes

1. **Timezone :** `ts_utc` dans `events` est en fait en Europe/Zurich, pas UTC
2. **Alias `ts_local` :** Utilisé dans `events_with_ts_local_v1` pour clarifier
3. **Chaine de vues :** 4 niveaux de vues avant d'atteindre les tables

---

**Document créé le :** 2025-12-13

