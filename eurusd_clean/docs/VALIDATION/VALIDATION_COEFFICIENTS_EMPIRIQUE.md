# 📊 VALIDATION EMPIRIQUE DES COEFFICIENTS FORMULE D

**Date :** 2025-01-XX  
**Script :** `scripts/validate_coefficients_empirical.py`  
**Statut :** ✅ VALIDATION RÉUSSIE - Amélioration de 58.4%

---

## 🎯 OBJECTIF

Valider empiriquement les coefficients de la Formule D pour chaque `num_events` au lieu d'utiliser une interpolation linéaire non validée.

---

## 📊 RÉSULTATS

### **Amélioration globale**

| Métrique | Interpolation Linéaire | Coefficients Empiriques | Amélioration |
|----------|------------------------|--------------------------|--------------|
| **MAE** | 27.00 pips | **11.25 pips** | **+58.4%** ✅ |
| **Médiane erreur** | 23.38 pips | **5.87 pips** | **+74.9%** ✅ |

### **Coefficients calibrés**

| num_events | intercept | coefficient | R² | MAE | n_samples |
|------------|-----------|-------------|----|----|-----------|
| **1** | 25.43 | 0.3505 | 0.038 | 11.46 pips | 352 |
| **2** | 25.12 | 0.2658 | 0.037 | 10.23 pips | 290 |
| **3** | 26.60 | 0.2603 | 0.033 | 11.25 pips | 210 |
| **4** | 27.23 | 0.2788 | 0.049 | 11.74 pips | 153 |
| **5** | 21.54 | 0.4146 | 0.147 | 13.40 pips | 71 |
| **6** | 30.07 | 0.1427 | 0.015 | 13.16 pips | 68 |
| **7** | 17.03 | 0.5316 | 0.142 | 17.84 pips | 40 |
| **8** | 17.94 | 0.4695 | 0.117 | 14.56 pips | 25 |
| **9** | 7.58 | 0.5223 | 0.357 | 7.32 pips | 17 |
| **10** | 23.06 | 0.1240 | 0.097 | 5.15 pips | 5 |
| **11** | 87.32 | -1.0550 | 0.642 | 4.42 pips | 6 ⚠️ |
| **14** | 47.88 | -0.1395 | 0.085 | 3.52 pips | 3 ⚠️ |

⚠️ **Note :** n=11 et n=14 ont des coefficients négatifs, probablement dus au faible nombre de samples.

### **Comparaison par num_events**

| num_events | n_clusters | Interpolation MAE | Empirique MAE | Amélioration |
|------------|------------|------------------|---------------|--------------|
| **1** | 352 | 31.44 pips | **10.82 pips** | +65.6% |
| **2** | 290 | 29.23 pips | **10.03 pips** | +65.7% |
| **3** | 210 | 28.12 pips | **11.14 pips** | +60.4% |
| **4** | 153 | 26.02 pips | **11.71 pips** | +55.0% |
| **5** | 71 | 22.02 pips | **13.47 pips** | +38.8% |
| **6** | 68 | 15.85 pips | **11.72 pips** | +26.1% |
| **7** | 40 | 19.11 pips | **17.28 pips** | +9.6% |
| **8** | 25 | 14.90 pips | **14.43 pips** | +3.2% |
| **9** | 17 | 7.51 pips | 9.70 pips | -29.2% ⚠️ |
| **10** | 5 | 13.92 pips | **7.68 pips** | +44.8% |
| **11** | 6 | 11.34 pips | **9.10 pips** | +19.7% |
| **14** | 3 | 13.41 pips | **10.19 pips** | +24.0% |

---

## 🔍 OBSERVATIONS

### **1. Coefficients vs Interpolation actuelle**

**Interpolation actuelle :**
- n=1 : intercept=-7.08, coefficient=0.419
- n=2 : intercept=-10.47, coefficient=0.477
- n≥8 : intercept=0.0, coefficient=0.914

**Coefficients empiriques :**
- Intercepts **positifs** et plus élevés (17-27 pips)
- Coefficients **plus faibles** (0.14-0.53) sauf n=5, n=7, n=9
- Pas de progression linéaire évidente

### **2. Relation non-linéaire confirmée**

La relation entre `num_events` et les coefficients est **clairement non-linéaire** :
- n=1-4 : coefficients similaires (~0.26-0.35)
- n=5-7 : coefficients plus élevés (0.41-0.53)
- n=8-9 : coefficients modérés (0.47-0.52)
- n≥10 : coefficients variables (peu de samples)

### **3. Qualité de la régression**

- **R² faibles** (0.015-0.642) : La relation linéaire score → impact explique peu de variance
- **MAE empirique** : 5-18 pips selon num_events
- **Meilleur R²** : n=9 (0.357), n=11 (0.642) mais peu de samples

---

## ✅ RECOMMANDATIONS

### **1. Utiliser coefficients empiriques**

✅ **Recommandation principale :** Utiliser les coefficients empiriques calibrés au lieu de l'interpolation linéaire.

**Raison :** Amélioration de **58.4%** sur l'ensemble des clusters.

### **2. Stratégie d'implémentation**

**Pour num_events avec suffisamment de samples (n≥3) :**
- Utiliser coefficients empiriques directement

**Pour num_events avec peu de samples (n=10, 11, 14) :**
- Utiliser coefficients empiriques mais avec prudence
- Considérer interpolation entre valeurs proches si nécessaire

**Pour num_events sans samples (n=12, 13, 15+) :**
- Interpolation entre n=11 et n=14 (si disponible)
- Ou utiliser formule n≥8 comme fallback

### **3. Mise à jour Formule D**

**Nouvelle structure proposée :**

```python
def calculate_impact_d_empirical(
    empirical_score: float,
    num_events: int = 1,
    amplification: float = 1.0,
    correction_factor: float = 0.758
) -> float:
    """
    Formule D avec coefficients empiriques validés.
    """
    n = int(num_events)
    
    # Coefficients empiriques (validation 2025-01-XX)
    COEFFICIENTS = {
        1: {'intercept': 25.43, 'coefficient': 0.3505},
        2: {'intercept': 25.12, 'coefficient': 0.2658},
        3: {'intercept': 26.60, 'coefficient': 0.2603},
        4: {'intercept': 27.23, 'coefficient': 0.2788},
        5: {'intercept': 21.54, 'coefficient': 0.4146},
        6: {'intercept': 30.07, 'coefficient': 0.1427},
        7: {'intercept': 17.03, 'coefficient': 0.5316},
        8: {'intercept': 17.94, 'coefficient': 0.4695},
        9: {'intercept': 7.58, 'coefficient': 0.5223},
        10: {'intercept': 23.06, 'coefficient': 0.1240},
        11: {'intercept': 87.32, 'coefficient': -1.0550},  # ⚠️ Peu de samples
        14: {'intercept': 47.88, 'coefficient': -0.1395},  # ⚠️ Peu de samples
    }
    
    if n in COEFFICIENTS:
        coeffs = COEFFICIENTS[n]
    elif n < 1:
        coeffs = COEFFICIENTS[1]
    elif n > 14:
        # Fallback : utiliser n=8 ou n=9
        coeffs = COEFFICIENTS[8]
    else:
        # Interpolation entre valeurs proches
        # TODO : Implémenter interpolation intelligente
        coeffs = COEFFICIENTS[8]  # Fallback temporaire
    
    intercept = coeffs['intercept']
    coefficient = coeffs['coefficient']
    
    # Calcul impact brut
    impact_brut = intercept + (coefficient * empirical_score)
    
    # Appliquer amplification
    impact_amplifie = abs(impact_brut) * amplification
    
    # Appliquer correction vectorielle
    impact_final = impact_amplifie * correction_factor
    
    return impact_final
```

### **4. Limitations**

⚠️ **Points d'attention :**
1. **R² faibles** : La relation linéaire explique peu de variance (0.015-0.642)
2. **Peu de samples** pour n≥10 : Coefficients moins fiables
3. **Coefficients négatifs** pour n=11, n=14 : Peut indiquer relation non-linéaire
4. **Validation nécessaire** : Tester sur nouveaux cas pour confirmer

### **5. Prochaines étapes**

1. ✅ **Validation réussie** : Coefficients empiriques validés
2. ⏳ **Implémentation** : Mettre à jour `calculate_impact_d` avec coefficients empiriques
3. ⏳ **Tests** : Valider sur cas de test (11.09.2025, 01.08.2025)
4. ⏳ **Documentation** : Mettre à jour documentation Formule D

---

## 📈 CONCLUSION

La validation empirique confirme que **l'interpolation linéaire est insuffisante** et que les **coefficients empiriques améliorent significativement** la précision (+58.4%).

**Action requise :** Mettre à jour la Formule D avec les coefficients empiriques validés.

