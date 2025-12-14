# 🔬 RAPPORT INVESTIGATION - RECHERCHE CLUSTERS SIMILAIRES

**Date :** 2025-11-16 19:09:02
**Cas référence :** 2025-09-11
**Composition :** 11 événements (US 14h30 + Current Account 14h45)

## 📊 Composition Référence

- Total événements : 11
- Uniques (raw) : 11
- Uniques (basic) : 11
- Uniques (variants) : 9

### Variantes Détectées

- `core inflation rate_mom` → `core inflation rate`
- `core inflation rate_yoy` → `core inflation rate`
- `inflation rate_mom` → `inflation rate`
- `inflation rate_yoy` → `inflation rate`
- `real earnings_mom` → `real earnings`

## 🎯 Meilleures Combinaisons

### Composition Complète (US 14h30 + Current Account 14h45)

| Période | Jaccard | Basic | Variants | Gain |
|---------|---------|-------|----------|------|
| 3 ans (Session 130) | 0.5 | 6 | 6 | +0 |
| 6 ans | 0.5 | 6 | 6 | +0 |
| 10 ans | 0.5 | 6 | 6 | +0 |
| 3 ans (Session 130) | 0.6 | 6 | 4 | -2 |
| 6 ans | 0.6 | 6 | 4 | -2 |
| 10 ans | 0.6 | 6 | 4 | -2 |
| 3 ans (Session 130) | 0.7 | 4 | 2 | -2 |
| 6 ans | 0.7 | 4 | 2 | -2 |
| 10 ans | 0.7 | 4 | 2 | -2 |
| 3 ans (Session 130) | 0.8 | 2 | 1 | -1 |
| 6 ans | 0.8 | 2 | 1 | -1 |
| 10 ans | 0.8 | 2 | 1 | -1 |

### Uniquement US 14h30 (sans Current Account)

| Période | Jaccard | Basic | Variants | Gain |
|---------|---------|-------|----------|------|
| 3 ans (Session 130) | 0.5 | 25 | 16 | -9 |
| 6 ans | 0.5 | 25 | 16 | -9 |
| 10 ans | 0.5 | 25 | 16 | -9 |
| 3 ans (Session 130) | 0.6 | 12 | 7 | -5 |
| 6 ans | 0.6 | 12 | 7 | -5 |
| 10 ans | 0.6 | 12 | 7 | -5 |
| 3 ans (Session 130) | 0.7 | 7 | 6 | -1 |
| 6 ans | 0.7 | 7 | 6 | -1 |
| 10 ans | 0.7 | 7 | 6 | -1 |
| 3 ans (Session 130) | 0.8 | 6 | 2 | -4 |
| 6 ans | 0.8 | 6 | 2 | -4 |
| 10 ans | 0.8 | 6 | 2 | -4 |

## 💡 Conclusions

**Meilleure combinaison (Composition complète) :**
- Période : 3 ans (Session 130)
- Seuil Jaccard : 0.5
- Clusters trouvés : 6
- Gain vs basic : +0

**Meilleure combinaison (Uniquement US) :**
- Période : 3 ans (Session 130)
- Seuil Jaccard : 0.5
- Clusters trouvés : 16
- Gain vs basic : -9

