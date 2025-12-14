# 📊 Rapport Test Complet - Détecteur Delta Rapide

**Date :** 2025-11-27 22:56:45

## 📈 Statistiques Globales

- **Total cas testés :** 17
- **Delta rapide détecté :** 6 (35.3%)
- **Delta rapide NON détecté :** 11 (64.7%)

## ✅ Cas avec Delta Rapide Détecté

| Date | Delta (pips) | Direction | Fenêtre (min) | Impact réel (pips) | Pattern |
|------|--------------|-----------|---------------|-------------------|---------|
| 2024-06-12 | 62.9 | UP | 28.0 | 77.2 | DOUBLE_WAVE |
| 2024-07-11 | 52.0 | UP | 21.0 | 52.0 | DOUBLE_WAVE |
| 2025-08-12 | 47.7 | UP | 20.0 | 62.7 | DOUBLE_WAVE |
| 2025-06-11 | 40.2 | UP | 17.0 | 55.3 | DOUBLE_WAVE |
| 2024-09-11 | 39.6 | DOWN | 16.0 | 39.4 | DOUBLE_WAVE |
| 2025-09-11 | 36.9 | UP | 30.0 | 60.7 | DOUBLE_WAVE |

## ⚠️  Cas avec Impact Élevé mais Pas de Delta Rapide

Ces cas ont un impact réel élevé (≥50 pips) mais pas de delta rapide détecté dans les 15-30 min.

| Date | Impact réel (pips) | Raison | Pattern |
|------|-------------------|--------|---------|
| 2024-11-13 | 72.2 | delta_too_small | DOUBLE_WAVE |
| 2024-01-11 | 58.0 | delta_too_small | DOUBLE_WAVE |
| 2025-01-15 | 52.1 | delta_too_small | DOUBLE_WAVE |

## 💡 Recommandations

1. **Cas détectés :** Le détecteur fonctionne correctement pour les mouvements forts immédiats
2. **Cas non détectés avec impact élevé :** Vérifier si ces cas sont des mouvements progressifs ou des faux positifs
3. **Ajustements possibles :**
   - Ajuster le seuil `min_delta_pips` si nécessaire
   - Ajuster la fenêtre `window_min`/`window_max` si nécessaire
