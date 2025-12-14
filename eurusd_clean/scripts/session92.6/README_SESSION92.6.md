# 📋 SESSION 92.6 - GRID SEARCH COMPLET 40 DATES

**Mission :** Exécuter Grid Search pour trouver amplifications optimales PAR TYPE (CPI, NFP, FOMC, ISM)

---

## 🎯 CONTEXTE

**Session 92.5 a validé :**
- ✅ Données Dukascopy = MT5 (écart 1-3 pips normal)
- ✅ Impact réel 11 sept : **51.0 pips** (pas 56.2!)
- ✅ **Amplification CPI optimale : 2.27** (MAE 0.1 pip, 99.8% précision)
- ✅ Grid Search Session 92.2 amp 2.2 était correcte (très proche 2.27)

**Amplifications attendues :**
- CPI  : ~2.27 (validé Session 92.5) ⭐⭐⭐⭐⭐
- NFP  : ~1.8-2.0 (Session 92.1) ⭐⭐⭐
- FOMC : ~0.8-1.0 (Session 92.1, 3 dates) ⭐
- ISM  : ~0.3-0.5 (Session 92.1, problématique) ⭐

---

## 📋 FICHIERS À LIRE (OBLIGATOIRE)

**AVANT de coder, lis dans cet ordre :**

1. **SESSION92.5_RAPPORT_COMPLET.md** (contexte complet)
2. **MESSAGE_SESSION92.5_SESSION92.6.md** (instructions mission)
3. **SESSION92.2_RAPPORT_COMPLET.md** (méthodologie Grid Search)

**Localisation :**
```
eurusd_clean/docs/
├── SESSION92.5_RAPPORT_COMPLET.md
├── MESSAGE_SESSION92.5_SESSION92.6.md
└── SESSION92.2_RAPPORT_COMPLET.md
```

---

## 🚀 EXÉCUTION SCRIPT

**André a déjà lancé :**
```bash
cd eurusd_clean/scripts/session92.6
python grid_search_amplification_by_type.py
```

**André fournira les résultats (output console + CSV)**

---

## ✅ CRITÈRES SUCCÈS

**CPI PRIORITAIRE :**
- Amplification trouvée entre 2.2 et 2.3 ✅
- Si divergence > 0.2 → investiguer

**MAE GLOBAL :**
- < 20 pips (vs 43.7 baseline) ✅
- Amélioration > 50%

**VALIDATION 11 SEPTEMBRE :**
- Tester chaque amplification trouvée
- CPI : MAE < 1 pip obligatoire
- Comparaison AVANT/APRÈS

---

## ⚠️ POINTS CRITIQUES

**1. ISM Problématique Attendue**
- Si MAE > 30 pips → Normal, documenter
- Ne pas bloquer sur ISM

**2. FOMC Faible Confiance**
- N = 3 dates seulement
- Si amp < 0.5 ou > 2.5 → Suspecter overfitting

**3. Validation Obligatoire**
- TOUJOURS tester sur 11 sept avant conclusions
- Comparer vs baseline V2.4

---

## 📊 BASELINE V2.4 (Référence)

**40 dates Session 91.2 :**
- MAE global : 43.7 pips
- CPI (10)  : MAE 13.7 pips
- NFP (10)  : MAE 36.9 pips
- FOMC (3)  : MAE 24.1 pips
- ISM (9)   : MAE 93.2 pips

**11 septembre 2025 (amp 2.5) :**
- Impact prédit : 56.3 pips
- Impact réel : 51.0 pips
- MAE : 5.3 pips

---

## 📁 FICHIERS DISPONIBLES

**Script Grid Search :**
```
session92.6/grid_search_amplification_by_type.py
```

**Données :**
```
session90/validation_results_planificateur_40dates.csv
fx_impact_app/data/warehouse.duckdb
```

**Validation Session 92.5 :**
```
session92.5_continuation/test_amplification_planificateur_reel.py
```

---

## 🎯 MISSION SESSION 92.6

**Phase 1 :** Analyser résultats Grid Search fournis par André

**Phase 2 :** Valider amplifications trouvées
- Tester sur 11 septembre
- Tester 5-10 dates variées
- Calculer MAE global projeté

**Phase 3 :** Comparaison vs Baseline
- Tableau AVANT/APRÈS
- Amélioration % par type
- Taux succès attendu

**Phase 4 :** Documentation
- Rapport complet Session 92.6
- Tableau amplifications finales
- Message transition Session 92.7

**Budget estimé :** 70-80k tokens restants (largement suffisant)

---

## 💡 RAPPELS MÉTHODOLOGIQUES

**Charte Scientifique :**
- Rigueur absolue (Article 1)
- Baseline sacrée (Article 3)
- Documentation = contrat (Article 4)
- Échecs documentés (Article 5)

**Tests obligatoires :**
- Validation 11 septembre
- Comparaison baseline
- MAE < 20 pips global

**Format rapport :**
- Sections structurées
- Tableaux comparatifs
- Preuves vérifiables
- Décisions justifiées

---

_README Session 92.6 - 28 octobre 2025_  
_"Grid Search complet 40 dates - Amplifications optimales par type"_
