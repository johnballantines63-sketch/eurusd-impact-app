# Résumé Test Pipeline Complet - Formule Linéaire

**Date** : 2025-12-07  
**Script** : `test_pipeline_complet_linear.py`

---

## 📊 RÉSULTATS GLOBAUX

### Test Effectué
- **379 mouvements testés** (sur 1,147 disponibles)
- **101 dates uniques** testées
- **768 erreurs** (dates sans événements HIGH US dans DB)

### Performance Globale

| Méthode | MAE | Ratio médian | Corrélation |
|---------|-----|--------------|-------------|
| **Formule D (ancienne)** | 31.68 pips | 0.416 | 0.176 |
| **Formule Linéaire (nouvelle)** | 34.04 pips | 1.694 | 0.120 |

**Amélioration MAE globale** : -7.4% (légèrement pire)

---

## 📊 ANALYSE PAR CLASSE

### FORT (39 mouvements)
| Métrique | Formule D | Formule Linéaire | Amélioration |
|----------|-----------|------------------|--------------|
| **MAE** | 47.88 pips | **13.92 pips** | **+70.9%** ✅ |
| **Ratio médian** | - | 1.100 | ✅ Excellent |

### TRÈS_FORT (37 mouvements)
| Métrique | Formule D | Formule Linéaire | Amélioration |
|----------|-----------|------------------|--------------|
| **MAE** | 88.90 pips | **34.37 pips** | **+61.3%** ✅ |
| **Ratio médian** | - | 0.731 | ⚠️ Sous-estimation modérée |

### MOYEN (194 mouvements)
| Métrique | Formule D | Formule Linéaire | Amélioration |
|----------|-----------|------------------|--------------|
| **MAE** | 26.98 pips | 30.68 pips | -13.7% ⚠️ |
| **Ratio médian** | - | 1.581 | ⚠️ Surestimation |

### FAIBLE (109 mouvements)
| Métrique | Formule D | Formule Linéaire | Amélioration |
|----------|-----------|------------------|--------------|
| **MAE** | 14.81 pips | 47.10 pips | -218.1% ❌ |
| **Ratio médian** | - | 2.485 | ❌ Surestimation importante |

---

## 💡 OBSERVATIONS

### ✅ Points Positifs

1. **FORT** : Performance excellente (MAE 13.92 pips, ratio 1.100)
2. **TRÈS_FORT** : Amélioration significative (MAE 34.37 vs 88.90 pips)
3. **Meilleures prédictions** : Certaines prédictions sont très précises (erreur < 0.1 pips)

### ⚠️ Points d'Attention

1. **FAIBLE/MOYEN** : Surestimation importante
   - Ratio médian 2.485 pour FAIBLE (prédictions 2.5x trop élevées)
   - Ratio médian 1.581 pour MOYEN (prédictions 1.6x trop élevées)

2. **Corrélation faible** : 0.120 (vs 0.176 formule D)
   - Indique que la formule linéaire capture moins bien la variabilité

3. **Beaucoup d'erreurs** : 768 dates sans événements dans DB
   - Probablement événements non-US ou score < 40

---

## 🎯 RECOMMANDATIONS

### Option 1 : Utiliser Formule Linéaire pour FORT/TRÈS_FORT uniquement

```python
if movement_class in ['FORT', 'TRÈS_FORT']:
    impact = calculate_impact_linear(...)
else:
    impact = calculate_impact_d(...)  # Formule D pour FAIBLE/MOYEN
```

### Option 2 : Correction pour FAIBLE/MOYEN

Ajouter facteur correctif pour mouvements faibles :
```python
if predicted_impact < 40:  # Mouvement faible probable
    impact = predicted_impact * 0.6  # Réduire de 40%
```

### Option 3 : Formule Hybride

- Utiliser formule linéaire si `base_score >= 40` OU `n_events >= 10`
- Sinon utiliser formule D

---

## 📈 TOP PRÉDICTIONS

Meilleures prédictions (formule linéaire) :

| Date | Classe | Réel | Prédit | Erreur |
|------|--------|------|--------|--------|
| 2024-02-02 | TRÈS_FORT | 90.1 | 90.19 | 0.09 pips ✅ |
| 2025-06-11 | FORT | 74.7 | 74.61 | 0.09 pips ✅ |
| 2024-06-07 | TRÈS_FORT | 90.0 | 89.61 | 0.39 pips ✅ |

---

## 🔧 PROCHAINES ÉTAPES

1. ✅ Pipeline testé et fonctionnel
2. ⏳ Analyser pourquoi surestimation FAIBLE/MOYEN
3. ⏳ Implémenter formule hybride (linéaire pour forts, D pour faibles)
4. ⏳ Tester sur nouvelles dates

---

**Fichiers générés** :
- `test_pipeline_complet_linear_results.csv` : Détails tous les mouvements
- `test_pipeline_complet_linear_summary.csv` : Résumé global


