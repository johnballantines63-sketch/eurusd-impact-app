# V8 - Ratios Recalibrés - Archive Production

**Date** : 2025-01-XX  
**Version** : V8 Final  
**N Multi-Wave** : 82 uniques  
**Tag Git** : `v8-historical-replay-final`

---

## Ratios Empiriques (Bootstrap N=82)

### Globaux

| Ratio | Médiane | Q25 | Q75 | CI80 | CI90 | Prior Session 64 | Écart |
|-------|---------|-----|-----|------|------|------------------|-------|
| **Leg1 / Total** | **39.1%** | 38.4% | 39.2% | [38.96%, 39.19%] | [38.84%, 39.19%] | 40% | **-1%** |
| **Leg2 / Total** | **60.9%** | 60.8% | 61.6% | [60.81%, 61.04%] | [60.81%, 61.10%] | 60% | **+1%** |

### Par Pattern Type

| Pattern | N | Leg1 Médiane | Leg2 Médiane | CI90 Leg1 | CI90 Leg2 |
|---------|---|--------------|--------------|-----------|-----------|
| **double_wave** | 11 | 38.7% | 61.3% | [38.42%, 39.19%] | [60.81%, 61.58%] |
| **zig_zag** | 71 | 39.2% | 60.8% | [38.95%, 39.19%] | [60.81%, 61.05%] |

### Par Cluster Type

| Cluster | N | Leg1 Médiane | Leg2 Médiane | CI90 Leg1 | CI90 Leg2 |
|---------|---|--------------|--------------|-----------|-----------|
| **CPI** | 19 | 39.2% | 60.8% | [38.72%, 39.19%] | [60.81%, 61.28%] |
| **CPI+Jobs** | 23 | 38.6% | 61.4% | [38.20%, 38.99%] | [61.01%, 61.80%] |
| **Jobs** | 40 | 39.2% | 60.8% | [39.01%, 39.19%] | [60.81%, 60.97%] |

---

## Décision Production

### Prior Final : **40/60** (Session 64)

**Justification** :
- Écart empirique vs prior : **1%** (< 10% seuil de changement)
- CI bootstrap serrés : ±0.3% (robustesse confirmée)
- Tous buckets "final" (N≥30) cohérents avec global : 39-40% / 60-61%
- Aucun bucket ne justifie override (drift <10% partout)

**Statut** : ✅ **CONFIRMÉ EMPIRIQUEMENT** sur horizon étendu (2022-2025)

---

## Buckets Stratifiés "Final" (N≥30)

| Bucket | N | Leg1 | Leg2 | Robustness |
|--------|---|------|------|------------|
| Jobs | 40 | 39.2% | 60.8% | final |
| zig_zag | 71 | 39.2% | 60.8% | final |
| low (strength) | 38 | 39.2% | 60.8% | final |
| DOWN | 40 | 39.2% | 60.8% | final |
| UP | 42 | 39.0% | 61.0% | final |

**Observation** : Cohérence universelle → Stratification informative, pas prescriptive.

---

## Source Données

- **Fichier** : `scripts/outputs/direction_router_test/ratios_recalibration.csv`
- **Période** : 2022-2025 (extension historique V8)
- **Méthode** : Bootstrap 1000×, CI 80-90%

---

**Version** : V8 Final  
**Status** : ✅ **ARCHIVÉ - PRODUCTION**

