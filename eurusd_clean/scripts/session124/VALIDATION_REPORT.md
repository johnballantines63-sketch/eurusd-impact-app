# VALIDATION REPORT - SESSION 124

**Date :** 09 November 2025 23:12
**Objectif :** Résoudre GAP #1 (Validation formules multi-dates)

---

## 🎯 RÉSUMÉ EXÉCUTIF

⚠️  **GAP #1 PARTIEL** - Certains critères non atteints

- **Patterns validés :** 107
- **MAE moyen :** 11.57 pips (objectif < 5 pips)
- **R² :** -0.2601 (objectif > 0.90)
- **Distribution :** 58.9% cas MAE < 10 pips (objectif > 80%)

---

## 📊 STATISTIQUES DÉTAILLÉES

### MAE (Mean Absolute Error)

| Métrique | Valeur |
|----------|--------|
| Moyenne | 11.57 pips |
| Médiane | 6.39 pips |
| Écart-type | 15.17 pips |
| Minimum | 0.00 pips |
| Maximum | 75.69 pips |

### Distribution MAE

| Catégorie | Nombre | Pourcentage |
|-----------|--------|-------------|
| < 5 pips | 50 | 46.7% |
| < 10 pips | 63 | 58.9% |
| < 20 pips | 85 | - |
| ≥ 20 pips | 22 | - |

### R² (Coefficient de détermination)

**R² = -0.2601**

❌ **Insuffisant** - Formule explique <80% variance

---

## 🏆 TOP 5 MEILLEURS CAS

| Rang | Date | MAE (pips) | Réel (pips) | Prédit (pips) | Events |
|------|------|------------|-------------|---------------|--------|
| 1 | 2024-01-12 | 0.00 | 33.7 | 33.7 | 6 |
| 2 | 2024-01-25 | 0.00 | 9.9 | 9.9 | 28 |
| 3 | 2024-02-08 | 0.00 | 18.4 | 18.4 | 4 |
| 4 | 2024-02-20 | 0.00 | 16.0 | 16.0 | 6 |
| 5 | 2024-02-22 | 0.00 | 36.5 | 36.5 | 8 |

---

## ⚠️  TOP 5 PIRES CAS

| Rang | Date | MAE (pips) | Réel (pips) | Prédit (pips) | Events |
|------|------|------------|-------------|---------------|--------|
| 1 | 2025-01-06 | 75.69 | 82.9 | 7.2 | 1 |
| 2 | 2025-05-29 | 70.71 | 73.8 | 3.1 | 2 |
| 3 | 2025-03-05 | 60.34 | 70.2 | 9.9 | 3 |
| 4 | 2025-06-05 | 55.99 | 63.2 | 7.2 | 15 |
| 5 | 2025-02-13 | 43.99 | 51.2 | 7.2 | 1 |

### Analyse Pires Cas

- **5 cas avec événements** mais MAE élevé
  → Nécessite investigation approfondie

---

## 🔍 OUTLIERS (MAE ≥ 20 pips)

**22 outliers identifiés**

| Date | MAE (pips) | Réel (pips) | Prédit (pips) | Events W1/W2 | Timing |
|------|------------|-------------|---------------|--------------|--------|
| 2025-01-06 | 75.69 | 82.9 | 7.2 | 0/1 | 31 min |
| 2025-05-29 | 70.71 | 73.8 | 3.1 | 0/2 | 81 min |
| 2025-03-05 | 60.34 | 70.2 | 9.9 | 1/2 | 69 min |
| 2025-06-05 | 55.99 | 63.2 | 7.2 | 14/1 | 59 min |
| 2025-02-13 | 43.99 | 51.2 | 7.2 | 0/1 | 99 min |
| 2025-09-11 | 37.92 | 51.7 | 13.8 | 10/2 | 34 min |
| 2024-11-15 | 35.93 | 61.8 | 25.9 | 13/6 | 82 min |
| 2024-09-26 | 34.91 | 38.0 | 3.1 | 0/5 | 87 min |
| 2025-04-10 | 32.99 | 40.2 | 7.2 | 0/1 | 101 min |
| 2024-10-30 | 30.51 | 33.6 | 3.1 | 0/2 | 36 min |
| 2025-09-25 | 30.33 | 56.2 | 25.9 | 2/2 | 72 min |
| 2024-01-11 | 30.29 | 57.5 | 27.2 | 9/1 | 35 min |
| 2024-10-17 | 29.63 | 55.5 | 25.9 | 1/5 | 49 min |
| 2024-04-05 | 28.63 | 54.5 | 25.9 | 17/3 | 41 min |
| 2024-10-29 | 27.41 | 30.5 | 3.1 | 0/3 | 24 min |
| 2024-04-11 | 27.01 | 30.1 | 3.1 | 12/2 | 55 min |
| 2025-05-22 | 26.61 | 29.7 | 3.1 | 0/2 | 67 min |
| 2024-04-18 | 23.51 | 26.6 | 3.1 | 9/2 | 73 min |
| 2025-08-12 | 23.39 | 50.6 | 27.2 | 8/1 | 14 min |
| 2024-05-14 | 22.61 | 25.7 | 3.1 | 1/2 | 36 min |
| 2025-10-28 | 21.57 | 4.3 | 25.9 | 0/4 | 23 min |
| 2025-07-02 | 20.41 | 23.5 | 3.1 | 0/2 | 26 min |

---

## 📈 CORRÉLATIONS

| Variable | Corrélation avec MAE |
|----------|----------------------|
| Nombre events total | -0.074 |
| Timing delta (min) | 0.243 |
| Amplitude réelle | 0.640 |

### MAE moyen par type pattern

- **Overlapping** (timing < 30 min): 5.74 pips
- **Sequential** (timing ≥ 30 min): 14.92 pips

---

## ✅ CRITÈRES SUCCÈS

| Critère | Objectif | Atteint | Résultat |
|---------|----------|---------|----------|
| MAE moyen | < 5 pips | ❌ | 11.57 pips |
| R² | > 0.90 | ❌ | -0.2601 |
| Distribution | >80% MAE < 10 pips | ❌ | 58.9% |

---

## 💡 RECOMMANDATIONS

### ⚠️  Ajustements Nécessaires

1. **MAE moyen > 5 pips** - Ajuster paramètres:
   - Amplification (actuellement 2.8)
   - Momentum factor (actuellement 1.3)

2. **R² < 0.90** - Améliorer modèle:
   - Considérer variables additionnelles
   - Affiner détection clusters

3. **Distribution insuffisante** - Investiguer outliers:
   - Analyser cas MAE > 20 pips
   - Identifier patterns non couverts

---

**Rapport généré :** 09 November 2025 23:12
**Session :** 124
**Auteur :** André Valentin avec Claude