# Synthèse Finale V7 — Version Copier-Coller

## V7 — État Final Production

**Triggers scannés** : 153 (sur 565 dates)

**Multi-wave** : 35 lignes → **9 uniques (5.9% des triggers)**
- 2 double_wave uniques
- 7 zig_zag uniques

**Double-wave validés visuellement** (retrace ≥30%, leg2 étend, nouveau extrême)
→ Reproductibles au recalcul.

**Ratios Leg1/Leg2 empiriques (uniques)** : 39.2% / 60.8%
- vs Session 64 : 40% / 60%
- **Écart 0.8%** → Prior conservé

**TURN_PIPS adaptatif** implémenté et loggé (`turn_pips_used`)
- Distribution observée : toujours 8.0 (floor)
- Explication : `impact_total_pips_used` (38.9-48.7 pips) < 53.3 pips (seuil pour sortir du floor)
- Adaptatif non "testé" en conditions variées faute d'historique pré-2024.

**Conclusion** : Code propre, métriques cohérentes, ratios validés → **Production ready**.

---

## Audit 9 Multi-Waves Uniques

### Par Cluster Type

| Cluster Type | N | Patterns | Directions | Strength (median) |
|--------------|---|----------|------------|-------------------|
| **CPI** | 5 | 4 zig_zag, 1 double_wave | 4 DOWN, 1 UP | 1.90 |
| **Jobs** | 3 | 2 zig_zag, 1 double_wave | 2 UP, 1 DOWN | 1.35 |
| **CPI+Jobs** | 1 | 1 zig_zag | 1 DOWN | 2.34 |

### Par Pattern Type

| Pattern | N | Cluster Types | Directions | Strength (median) |
|---------|---|---------------|------------|-------------------|
| **Double-wave** | 2 | CPI: 1, Jobs: 1 | DOWN: 1, UP: 1 | 1.61 |
| **Zig-zag** | 7 | CPI: 4, Jobs: 2, CPI+Jobs: 1 | DOWN: 5, UP: 2 | 1.51 |

### Observations

- **CPI majoritaire** : 5/9 cas (55%)
- **Direction DOWN dominante** : 6/9 cas (67%)
- **Strength modéré** : Median 1.51 (pas de très gros triggers)
- **Double-wave équilibré** : 1 CPI, 1 Jobs (pas de biais cluster)

---

## Recommandations V8 (Stratification)

### Buckets Strength (si N augmente)

- **Low** : |z| < 1.5 (actuellement 3 cas)
- **Medium** : 1.5 ≤ |z| < 2.0 (actuellement 4 cas)
- **High** : |z| ≥ 2.0 (actuellement 2 cas)

### Buckets Cluster Type

- **CPI** : N=5 (suffisant pour stats)
- **Jobs** : N=3 (limite, attendre N≥5)
- **CPI+Jobs** : N=1 (insuffisant)

### Buckets Pattern

- **Double-wave** : N=2 (insuffisant, attendre N≥5)
- **Zig-zag** : N=7 (suffisant pour stats)

---

**Version** : V7
**Date** : 2025-01-XX
**Status** : ✅ **PRODUCTION READY**

