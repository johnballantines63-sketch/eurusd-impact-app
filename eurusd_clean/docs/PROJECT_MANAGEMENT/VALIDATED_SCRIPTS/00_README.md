# BACKUP ORGANISÉ - SCRIPTS VALIDÉS + DB

**Date création :** 10 November 2025 16:18:50  
**Version projet :** eurusd_clean  
**Auteur :** André Valentin

---

## 🎯 Objectif de ce Backup

Ce répertoire contient une **copie organisée** de tous les scripts validés et de la base de données du projet EUR/USD Impact Predictor.

**Important :** Les scripts originaux restent en place dans leur emplacement d'origine. Ce backup sert de :
1. **Sauvegarde de sécurité** (scripts + DB)
2. **Archive organisée** par fonction/étape
3. **Documentation** de l'état validé du projet

---

## 📂 Structure du Backup

```
VALIDATED_SCRIPTS/
├── 00_README.md                      (Ce fichier)
├── 01_FORMULES_GOLD_STANDARD/        Sessions 51-55 (>94% précision)
├── 02_DETECTION_INVERSION/           Sessions 102-107 (méthode validée)
├── 03_SCANNER_PATTERNS/              Session 117 (Rev7 + 42 patterns)
├── 04_DETECTEUR_DOUBLE_WAVE/         Session 118 (MAE 4.5 pips)
├── 05_VALIDATION_CAS_ECOLE/          Tests 11 septembre 2025
├── 06_MODULES_CORE/                  Production (src/core/)
├── 07_APPLICATION_STREAMLIT/         Interface utilisateur
├── 08_DATABASES/                     warehouse.duckdb (205 MB)
├── 09_DOCUMENTATION/                 Docs critiques
└── session125_amplification_universelle/  Session 125 (Fonction Universelle) ⭐
```

---

## 📋 Contenu Détaillé

### 01_FORMULES_GOLD_STANDARD
**Sessions 51-55 | Précision >94%**

- `formulas_validated.py` ⭐ : 4 formules validées
  - Ajustement Score Empirique (99.9% précision)
  - Impact Net - Formule D (98.6% précision) 🏆
  - Time To Reversal - TTR C (94.4% précision)
  - Pullback Logarithmique V2 (99.3% précision)

**Cas école :** 11 septembre 2025 - Précision globale >98%

---

### 02_DETECTION_INVERSION
**Sessions 102-107 | Méthode Validée**

Scripts clés :
- `s107_phase2e_cluster3_inversion_trend.py` ⭐ : Détection par séquence
- `s107_verify_trend_11sept.py` : Validation 11 sept (capte pic 9 sept 08:00)
- `s107_phase3_combined_calibration.py` : Calibration multi-clusters

**Validation :** Inversion 9 sept 08:00 (PEAK), durée 54.6h, R² 0.6376

---

### 03_SCANNER_PATTERNS
**Session 117 | 42 Patterns Détectés**

Scripts :
- `price_pattern_scanner_rev7_multimin.py` ⭐ : Scanner final (seuil 35 pips)
- `enrich_double_waves.py` : Enrichissement events causaux (13 cas)
- `analyze_enriched.py` : Analyse patterns
- `find_sept11.py` : Debug 11 septembre

Datasets :
- `patterns_detected.json` : 42 patterns (15 Double Wave)
- `double_waves_enriched.json` : 13 cas avec events causaux
- `plots_double_wave/` : 6 graphiques échantillon

**Découverte :** 87% Double Wave prédictibles (avec events), 13% techniques purs

---

### 04_DETECTEUR_DOUBLE_WAVE
**Session 118 | MAE 4.5 pips**

Scripts :
- `double_wave_detector.py` ⭐ : Détecteur algorithmique validé
- `run_validation_pro.py` : Validation production
- `verify_sept11_correct.py` : Vérification 11 sept

Résultats :
- `validation_results.json` : Validation multi-dates

**Validation 11 sept :** Impact détecté 51.7 pips vs 56.2 réel (MAE 4.5 pips)

---

### 05_VALIDATION_CAS_ECOLE
**Tests 11 Septembre 2025**

Scripts tests :
- `test_11sept_correct_methodology.py`
- `test_formulas_92xx_11sept.py`
- `validate_planificateur_migration.py`

**Cas référence :** 11 septembre 2025 = Gold Standard projet

---

### 06_MODULES_CORE
**Production (src/core/)**

9 modules production-ready :
- `formulas_validated.py` ⭐ : 4 formules gold standard
- `cluster_impact_calculator.py` : Calcul impact clusters
- `double_wave.py` : Pattern Double Wave
- `impact_measurement.py` : Mesure impact MT5 (v4.0)
- + 5 autres modules

**Status :** Tous modules en production

---

### 07_APPLICATION_STREAMLIT
**Interface Utilisateur**

5 pages fonctionnelles :
- `Home.py` : Page accueil
- `pages/1_Calendrier_Trading.py` : Calendrier économique
- `pages/2_Planificateur_V2.py` ⭐ : Prédictions trading
- `pages/3_API_Status.py` : Status APIs
- `pages/4_Mise_a_jour_DB.py` : Import données

**Status :** Application 100% fonctionnelle

---

### 08_DATABASES
**Base de Données Principale**

- `warehouse.duckdb` (205 MB)
  - 58,449 événements économiques
  - 1,114,260 prix 1 minute EUR/USD
  - Vue prices_bern (timezone Bern +02:00)

- `database_info.json` : Métadonnées backup

**Période :** 2015-2025 (10 ans historique)

---

### 09_DOCUMENTATION
**Documentation Critique**

Documents clés :
- `PROJECT_STATE.md` : État actuel projet
- `SESSION_112_RAPPORT_FINAL.md` : Migration eurusd_clean
- `SESSION_113_RAPPORT_FINAL.md` : Validation cluster calculator
- `SOLUTION_DEFINITIVE_TIMEZONE.md` : Vue prices_bern
- `MASTER_PLAN.md` : Vision globale
- `VALIDATED_FORMULAS.md` : Synthèse formules

---

## 📊 Statistiques Backup

```
Scripts validés copiés   : ~30 scripts
Modules core             : 9 fichiers
Datasets                 : 5 fichiers JSON/CSV
Graphiques               : 6 échantillons
Base de données          : 205 MB
Documentation            : 6 documents critiques

Total taille backup      : ~210-220 MB
```

---

## ⚙️ Utilisation du Backup

### Restauration Scripts

Pour utiliser un script du backup :

```bash
# Copier script vers emplacement actif
cp 03_SCANNER_PATTERNS/price_pattern_scanner_rev7_multimin.py \
   ../scripts/session117/

# Ou exécuter directement depuis backup
cd 03_SCANNER_PATTERNS/
python3 price_pattern_scanner_rev7_multimin.py
```

### Restauration Base de Données

```bash
# Sauvegarder DB actuelle
mv ../data/warehouse.duckdb ../data/warehouse.duckdb.old

# Restaurer depuis backup
cp 08_DATABASES/warehouse.duckdb ../data/

# Vérifier intégrité
python3 -c "import duckdb; duckdb.connect('../data/warehouse.duckdb')"
```

---

## 🔗 Emplacements Originaux

**Scripts originaux restent dans :**
- `eurusd_clean/src/core/` : Modules production
- `eurusd_clean/scripts/session117/` : Scanner patterns
- `eurusd_clean/scripts/session118/` : Détecteur Double Wave
- `eurusd_clean/scripts/session107/` : Détection inversion
- `eurusd_clean/streamlit_app/` : Application interface

**Base de données originale :**
- `eurusd_clean/data/warehouse.duckdb`

**Documentation originale :**
- `eurusd_clean/docs/`

---

## ⚠️ Important

1. **Ce backup est READ-ONLY** : Ne pas modifier les fichiers ici
2. **Scripts originaux prioritaires** : Toujours utiliser versions originales pour développement
3. **Backup périodique** : Créer nouveau backup après chaque validation majeure
4. **Vérifier intégrité DB** : Tester connexion après restauration

---

### session125_amplification_universelle
**Session 125 | Fonction Universelle Validée** ⭐

Scripts pipeline :
- `find_matching_clusters.py` : Matching clusters identiques (29 CPI)
- `calculate_r2_trends.py` : Calcul R² tendances (window 240)
- `calibrate_amplification_function.py` : Calibration fonction
- `cross_validate_nfp_final.py` : Validation croisée (+88%)

**Fonction calibrée :**
```python
amp = 0.040833 + 0.050220×R² - 0.006553×R²²
```

**Validation :**
- 29 clusters CPI (calibration)
- 17 événements NFP (validation croisée)
- Amélioration : +88.3% MAE vs baseline
- **Décision : Fonction UNIVERSELLE** applicable à tous événements HIGH

**Voir :** `session125_amplification_universelle/README.md` pour documentation complète

---

## 📅 Historique Versions

| Date | Version | Description |
|------|---------|-------------|
| 2025-11-10 | 1.0 | Backup initial organisé (Sessions 51-118) |
| 2025-11-10 | 1.1 | Ajout Session 125 (Fonction Universelle) |

---

## 📞 Contact

**Auteur :** André Valentin  
**Projet :** EUR/USD News Impact Predictor  
**Sessions :** 51-125  
**Dernière mise à jour :** 10 November 2025

---

**🎯 Ce backup préserve l'état validé du projet à la date ci-dessus.**
