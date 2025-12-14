# 📊 RAPPORT VALIDATION FORMULE S115

**Session:** 118  
**Date:** 07 novembre 2025  
**Formule:** `calculate_double_wave_overlapping()`  
**Cas testés:** 13 Double Wave avec events causaux  

---

## 🎯 RÉSUMÉ EXÉCUTIF

### ⏳ VALIDATION EN COURS

Le script de validation `run_validation.py` est prêt à être exécuté pour tester la formule S115 sur les 13 cas Double Wave avec events causaux.

**Commande d'exécution:**
```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean
python scripts/session118/run_validation.py
```

---

## 📋 CAS À VALIDER (13 cas)

| # | Date | Impact Réel (pips) | Direction | Events | Pattern |
|---|------|-------------------|-----------|--------|---------|
| 1 | 2024-01-05 | 41.10 | bullish | 10 | ISM Services + Factory Orders |
| 2 | 2024-04-05 | 53.58 | bearish | 17 | CA Employment + US NFP |
| 3 | 2024-04-23 | 46.56 | bullish | 3 | US PMI Manufacturing |
| 4 | 2024-07-11 | 51.37 | bullish | 9 | US CPI + Jobless Claims |
| 5 | 2024-08-02 | 65.23 | bullish | 10 | US Manufacturing Payrolls (200%) |
| 6 | 2025-02-07 | 47.43 | bearish | 3 | RU Retail Sales |
| 7 | 2025-03-06 | 41.57 | bullish | 5 | ECB Interest Rate |
| 8 | 2025-04-03 | 40.76 | bearish | 3 | CA PMI Services |
| 9 | 2025-04-04 | 69.14 | bearish | 16 | CA Full Time Employment (513%) |
| 10 | 2025-04-10 | 80.97 | bullish | 1 | MX Monetary Policy |
| 11 | 2025-04-23 | 36.80 | bearish | 4 | US New Home Sales |
| 12 | 2025-07-03 | 66.19 | bearish | 15 | US Earnings + Trade Balance |
| 13 | 2025-09-11 | 60.67 | bullish | 10 | **US CPI + Jobless (référence)** |

**CAS EXCLUS (2 patterns techniques SANS events):**
- ❌ 2025-01-20 : 87.1 pips (SANS events causaux)
- ❌ 2025-07-16 : 101.6 pips (SANS events causaux)

---

## 🔬 MÉTHODOLOGIE VALIDATION

### **Étape 1: Extraction Impact Réel MT5**
```
Impact réel = |baseline_price - wave2_peak_price| × 10000
```

### **Étape 2: Filtrage Events par Cluster**
- **Wave 1 events**: Events dans fenêtre ±5 min autour de peak1_time
- **Wave 2 events**: Events dans fenêtre ±5 min autour de wave2_peak_time

### **Étape 3: Calcul Prédiction S115**

```python
# 1. Calculer impact Wave 1
wave1_result = calculate_cluster_impact(wave1_events, conn)

# 2. Calculer impact Wave 2
wave2_result = calculate_cluster_impact(wave2_events, conn)

# 3. Calculer pullback characteristics
pullback_result = calculate_pullback_characteristics(
    peak_impact=wave1_result['impact_pips'],
    peak_surprise=wave1_result['max_surprise'],
    num_events=wave1_result['num_events'],
    has_following_cluster=True,
    minutes_to_next_cluster=timing_delta_minutes
)

# 4. Calculer impact total (FORMULE S115)
total_result = calculate_double_wave_overlapping(
    wave1_cluster_result=wave1_result,
    wave2_cluster_result=wave2_result,
    pullback_characteristics=pullback_result,
    timing_delta_minutes=timing_delta_minutes,
    wave1_time=peak1_time,
    wave2_time=wave2_peak_time
)

predicted_impact = total_result['total_impact_pips']
```

### **Étape 4: Calcul MAE**
```
MAE = |predicted_impact - real_impact|
```

---

## 📈 CRITÈRES DE SUCCÈS

| Métrique | Objectif | Statut |
|----------|----------|--------|
| **MAE moyen** | < 5 pips | ⏳ En attente |
| **MAE médian** | < 5 pips | ⏳ En attente |
| **RMSE** | < 7 pips | ⏳ En attente |
| **R²** | > 0.85 | ⏳ En attente |
| **Outliers** (MAE>10) | < 3 cas | ⏳ En attente |
| **11 septembre** | MAE < 2 pips | ✅ Référence validée (0.29 pips S115) |

---

## 🔍 CAS D'ATTENTION PARTICULIÈRE

### **Cas #5 (02 août 2024) - Surprise Extrême**
- **Surprise Manufacturing Payrolls**: 200% !
- **Impact réel**: 65.23 pips
- **Attention**: Vérifier amplification facteur pour surprises > 100%

### **Cas #9 (04 avril 2025) - Surprise Record**
- **Surprise CA Full Time Employment**: 513% !!
- **Impact réel**: 69.14 pips
- **Attention**: Potentielle sous-estimation si surprise plafonnée

### **Cas #10 (10 avril 2025) - Single Event Fort**
- **Events**: 1 seul (MX Monetary Policy)
- **Impact réel**: 80.97 pips (le plus haut)
- **Extension factor**: 2.29x
- **Attention**: Vérifier si formule gère bien les single events forts

### **Cas #13 (11 septembre 2025) - Référence Validation**
- **Impact Session 115**: MAE 0.29 pips ✅
- **Impact Session 117**: MAE 4.5 pips (scanner seul)
- **Attendu**: Doit retrouver MAE ~0.3 pips avec formule complète

---

## 📊 HYPOTHÈSES DE RÉSULTATS

### **Scénario Optimiste (MAE < 3 pips)**
- Formule S115 réplique la précision du 11 septembre sur tous les cas
- Paramètres actuels (momentum 1.3-1.4, amplification 2.8) sont optimaux
- **Action**: Valider paramètres finaux, documenter, passer à intégration Planificateur

### **Scénario Nominal (MAE 3-5 pips)**
- Formule S115 atteint l'objectif avec légère marge
- Quelques outliers (2-3 cas) nécessitent attention
- **Action**: Analyser outliers, ajustements mineurs si patterns identifiés

### **Scénario Ajustements (MAE 5-8 pips)**
- Formule proche objectif mais nécessite calibration
- Patterns récurrents dans erreurs (ex: surprises extrêmes, single events)
- **Action**: Ajuster momentum_factor, amplification par type event, re-tester

### **Scénario Révision (MAE > 8 pips)**
- Formule sous-performe, révision méthodologique nécessaire
- Erreurs systématiques identifiées
- **Action**: Analyser causes profondes, revoir algorithme, grid search paramètres

---

## 🚀 PROCHAINES ÉTAPES

### **Immédiat (Session 118)**
1. ✅ Script validation créé (`run_validation.py`)
2. ⏳ Exécuter script: `python scripts/session118/run_validation.py`
3. ⏳ Analyser résultats (MAE par cas, statistiques globales)
4. ⏳ Identifier outliers et patterns
5. ⏳ Ajuster paramètres si nécessaire (momentum_factor, amplification)
6. ⏳ Re-valider après ajustements
7. ⏳ Documenter paramètres finaux validés

### **Court terme (Session 119)**
- Intégration Planificateur V2.9 avec formule S115 validée
- Tests interface Streamlit
- Guide utilisateur

### **Moyen terme (Sessions 120+)**
- Extension à autres patterns (Sequential, Cumulative)
- Validation multi-paires (EUR/GBP, GBP/USD)
- Backtesting exhaustif 2020-2025

---

## 📁 FICHIERS CRÉÉS

```
scripts/session118/
├── validate_formula_s115.py          # Script validation complet (classe)
├── run_validation.py                 # Script exécution simplifié ✅
├── validation_report_template.md    # Ce rapport (template)
└── [À GÉNÉRER]
    ├── validation_results.json       # Résultats détaillés
    ├── validation_results.csv        # Résultats CSV
    └── validation_plots/             # 3 graphiques PNG
        ├── predicted_vs_real.png
        ├── mae_distribution.png
        └── mae_by_date.png
```

---

## 📞 SUPPORT & DEBUG

### **Si Erreurs d'Exécution**
1. Vérifier connexion database: `warehouse.duckdb` accessible
2. Vérifier imports: modules `src.core.*` trouvables
3. Vérifier JSON: `double_waves_enriched.json` valide
4. Logs détaillés: traceback Python complet

### **Si MAE Anormalement Élevé**
1. Vérifier extraction impacts réels (baseline → wave2_peak)
2. Vérifier filtrage events (Wave1 vs Wave2)
3. Vérifier timestamps (timezone Bern +02:00 cohérent)
4. Comparer avec graphiques Session 117 (`plots_double_wave/`)

### **Si Outliers Nombreux**
1. Analyser pattern commun (surprises extrêmes, timing, direction)
2. Vérifier paramètres formule (momentum, amplification)
3. Considérer grid search calibration
4. Documenter limites formule

---

**Auteur:** André Valentin avec Claude  
**Session:** 118  
**Date:** 07 novembre 2025  
**Version:** 1.0 (Template - En attente exécution)

---

## ⏳ STATUT: EN ATTENTE EXÉCUTION

**Commande à lancer:**
```bash
python scripts/session118/run_validation.py
```

**Durée estimée:** 2-3 minutes  
**Tokens restants:** ~115k / 190k (60% disponible)
