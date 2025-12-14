# 📊 Schémas Base de Données - warehouse.duckdb

**Date :** Session 30  
**Source :** fx_impact_app/data/warehouse.duckdb

---

## Table : events (58,449 lignes)

**Clé primaire :** event_key + country + ts_utc (composite)

| Colonne | Type | Description |
|---------|------|-------------|
| ts_utc | TIMESTAMP WITH TIME ZONE | Date/heure événement |
| country | VARCHAR | Pays (US, EU, GB) |
| event_title | VARCHAR | Titre événement |
| event_key | VARCHAR | Clé unique événement |
| importance_n | BIGINT | Importance 1-3 |
| actual | DOUBLE | Valeur réelle |
| previous | DOUBLE | Valeur précédente |
| estimate | DOUBLE | Estimation consensus |
| forecast | DOUBLE | Prévision |
| unit | VARCHAR | Unité (%, K, etc.) |
| type | VARCHAR | Type |
| label | VARCHAR | Label |
| comparison | VARCHAR | Comparaison |
| period | VARCHAR | Période |
| change | DOUBLE | Changement |
| change_percentage | DOUBLE | Changement % |
| event_type | VARCHAR | Type événement |

---

## Table : event_families (747 lignes)

**Clé primaire :** event_key + country

| Colonne | Type | Description |
|---------|------|-------------|
| event_key | VARCHAR | Clé événement |
| country | VARCHAR | Pays |
| family | VARCHAR | Famille (ex: "CPI") |
| empirical_score | DOUBLE | Score empirique |
| avg_movement_pips | DOUBLE | Mouvement moyen pips |
| sample_size | INTEGER | Taille échantillon |
| latency_median | DOUBLE | Latence médiane |
| latency_p20 | DOUBLE | Latence P20 |
| latency_p80 | DOUBLE | Latence P80 |
| ttr_median | DOUBLE | TTR médian |
| ttr_p20 | DOUBLE | TTR P20 |
| ttr_p80 | DOUBLE | TTR P80 |
| mfe_p80 | DOUBLE | MFE P80 |
| n_events_latency | INTEGER | Nombre événements |

**⚠️ IMPORTANT :** Pas de colonnes `importance`, `sensitivity`, `unit`, `description`

---

## Table : prices_1m (1,114,260 lignes)

**Clé primaire :** datetime (ou timestamp)

| Colonne | Type | Description |
|---------|------|-------------|
| datetime | TIMESTAMP WITH TIME ZONE | Date/heure (principal) |
| timestamp | BIGINT | Unix timestamp |
| gmtoffset | BIGINT | Décalage GMT |
| open | DOUBLE | Prix ouverture |
| high | DOUBLE | Prix haut |
| low | DOUBLE | Prix bas |
| close | DOUBLE | Prix clôture |
| volume | BIGINT | Volume |

**⚠️ IMPORTANT :** Utiliser `datetime` comme colonne principale, pas `ts_utc`

---

## Table : event_impacts_v2 (8,344 lignes)

**Clé primaire :** ts_utc + event_key + country (composite)

| Colonne | Type | Description |
|---------|------|-------------|
| ts_utc | TIMESTAMP WITH TIME ZONE | Date/heure événement |
| event_key | VARCHAR | Clé événement |
| event_title | VARCHAR | Titre |
| country | VARCHAR | Pays |
| actual | DOUBLE | Valeur réelle |
| forecast | DOUBLE | Prévision |
| previous | DOUBLE | Valeur précédente |
| surprise_pct | DOUBLE | Surprise % |
| importance | BIGINT | Importance |
| phase1_pips | DOUBLE | Impact Phase 1 pips |
| ttr_minutes | INTEGER | Time-to-revert minutes |
| direction | VARCHAR | Direction (up/down) |
| start_price | DOUBLE | Prix départ |
| ttr_price | DOUBLE | Prix retour |
| source | VARCHAR | Source calcul |
| created_at | TIMESTAMP WITH TIME ZONE | Date création |

**⚠️ IMPORTANT :** Pas de colonne `time_group`, utiliser `ts_utc` directement

---

## Jointures Critiques

### events ↔ event_families

```sql
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
```

**TOUJOURS joindre sur event_key ET country !**

### events ↔ event_impacts_v2

```sql
LEFT JOIN event_impacts_v2 ei
    ON e.event_key = ei.event_key
    AND e.country = ei.country
    AND e.ts_utc = ei.ts_utc
```

---

## Erreurs Courantes à Éviter

1. ❌ `e.event_id` → N'EXISTE PAS
2. ❌ `e.importance` → Utiliser `e.importance_n`
3. ❌ `ef.importance` → N'EXISTE PAS dans event_families
4. ❌ `ef.sensitivity` → N'EXISTE PAS
5. ❌ `ef.unit` → N'EXISTE PAS
6. ❌ `ef.description` → N'EXISTE PAS
7. ❌ `p.ts_utc` → Utiliser `p.datetime` pour prices_1m
8. ❌ `ei.time_group` → N'EXISTE PAS, utiliser `ei.ts_utc`

---

**Dernière mise à jour :** Session 30 - 22 octobre 2025
