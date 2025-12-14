# SESSION 124 - Scanner & Validation Multi-Dates

**Date :** 09 novembre 2025  
**Objectif :** Résoudre GAP #1 (Validation formules multi-dates)  
**Statut :** ✅ Scripts créés, prêt pour exécution

---

## 🎯 VUE D'ENSEMBLE

**Mission :** Valider formule S115 (Double Wave + Overlapping) sur 10-20 patterns historiques 2024-2025.

**Méthode :**
1. Scanner prix 2024-2025 avec Rev12 validé (MAE 4.5 pips)
2. Extraire événements causaux pour chaque pattern
3. Calculer impact prédit avec formule S115
4. Comparer vs amplitude réelle (MAE, R²)

**Critères succès :**
- ✅ MAE moyen < 5 pips
- ✅ R² > 0.90
- ✅ >80% cas MAE < 10 pips

---

## 📁 STRUCTURE

```
scripts/session124/
├── README.md                          ← CE FICHIER
│
├── 🔧 SCRIPTS EXÉCUTABLES
│   ├── run_validation_workflow.py    ← ORCHESTRATEUR (recommandé)
│   ├── test_scan_setup.py            ← Test environnement
│   ├── scan_with_rev12.py            ← Scanner 2024-2025
│   ├── validate_formulas_multidates.py ← Validation S115
│   └── analyze_results.py            ← Analyse & rapport
│
└── 📊 OUTPUTS (générés)
    ├── double_waves_rev12.json       ← Patterns détectés
    ├── double_waves_summary.csv      ← Résumé patterns
    ├── validation_results.json       ← Résultats validation
    └── VALIDATION_REPORT.md          ← Rapport final
```

---

## 🚀 EXÉCUTION RAPIDE (RECOMMANDÉ)

### **Option 1 : Workflow Automatique**

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean

# Activer venv
source .venv/bin/activate  # macOS/Linux
# OU
.venv\Scripts\activate     # Windows

# Exécuter workflow complet
python scripts/session124/run_validation_workflow.py
```

**Le workflow exécute automatiquement :**
1. ✅ Test environnement
2. ✅ Scanner 2024-2025 (~10-15 min)
3. ✅ Validation formules
4. ✅ Analyse résultats
5. ✅ Génération rapport

**Si déjà scanné précédemment :**
```bash
# Sauter scan, utiliser résultats existants
python scripts/session124/run_validation_workflow.py --skip-scan
```

---

## 🔧 EXÉCUTION MANUELLE (ÉTAPE PAR ÉTAPE)

### **Étape 1 : Test Setup** (2 minutes)

```bash
python scripts/session124/test_scan_setup.py
```

**Attendu :**
```
✅ OK - imports
✅ OK - db_access
✅ OK - reference_case
```

**Si échec :** Corriger environnement avant continuer.

---

### **Étape 2 : Scanner 2024-2025** (10-15 minutes)

```bash
# Scan complet
python scripts/session124/scan_with_rev12.py

# Scan avec debug (plus lent)
python scripts/session124/scan_with_rev12.py --debug

# Scan période spécifique
python scripts/session124/scan_with_rev12.py --period 2025-09-01:2025-09-30
```

**Résultats attendus :**
- `double_waves_rev12.json` : 10-20 patterns (comme Session 117)
- `double_waves_summary.csv` : Résumé statistiques

**Vérification rapide :**
```bash
# Compter patterns détectés
python -c "import json; f=open('scripts/session124/double_waves_rev12.json'); print(len(json.load(f)))"
```

---

### **Étape 3 : Validation Formules** (5 minutes)

```bash
python scripts/session124/validate_formulas_multidates.py
```

**Processus :**
1. Charge patterns détectés
2. Pour chaque pattern :
   - Extrait événements causaux (±10 min)
   - Calcule impact avec S115
   - Compare vs réel
3. Calcule statistiques (MAE, R²)

**Résultats :**
- `validation_results.json` : Résultats détaillés

**Affichage console :**
```
Patterns validés: 15/18
MAE:
  Moyenne: 4.2 pips
  Médiane: 3.8 pips
R²: 0.9234

CRITÈRES SUCCÈS:
✅ MAE moyen < 5 pips
✅ R² > 0.90
✅ >80% MAE < 10 pips
```

---

### **Étape 4 : Analyse Résultats** (2 minutes)

```bash
python scripts/session124/analyze_results.py
```

**Génère :**
- `VALIDATION_REPORT.md` : Rapport complet Markdown

**Contenu rapport :**
- Résumé exécutif (GAP #1 résolu ?)
- Statistiques détaillées
- Top 5 meilleurs/pires cas
- Outliers (MAE > 20 pips)
- Corrélations
- Recommandations

---

## 📊 INTERPRÉTATION RÉSULTATS

### **Critères Succès**

| Critère | Objectif | Signification |
|---------|----------|---------------|
| **MAE moyen** | < 5 pips | Précision globale formule |
| **R²** | > 0.90 | Qualité prédiction (variance expliquée) |
| **Distribution** | >80% < 10 pips | Robustesse (peu d'outliers) |

### **Scénarios Possibles**

#### ✅ **Tous critères atteints**
→ GAP #1 RÉSOLU  
→ Formule S115 production-ready  
→ Session 125: Intégrer Planificateur V2.9

#### ⚠️  **MAE moyen légèrement > 5 pips (5-7 pips)**
→ Acceptable si R² > 0.90  
→ Analyser outliers  
→ Ajuster paramètres si nécessaire

#### ❌ **MAE moyen > 7 pips OU R² < 0.85**
→ Investigation approfondie requise  
→ Vérifier :
  - Événements causaux correctement extraits ?
  - Paramètres amplification (2.8) optimaux ?
  - Patterns sans événements exclus ?

---

## 🐛 DÉPANNAGE

### **Erreur : DB non trouvée**
```bash
# Vérifier path
ls -lh data/warehouse.duckdb

# Devrait afficher : ~205 MB
```

### **Erreur : Import Rev12 échoue**
```bash
# Vérifier Rev12 existe
ls scripts/session120/double_wave_detector_rev12.py
```

### **Scan détecte 0 patterns**
Causes possibles :
1. DB vide ou corrompue → Restaurer backup
2. Paramètres Rev12 trop stricts → Ajuster seuils
3. Timezone incorrecte → Vérifier config

### **Validation trouve 0 événements**
Causes possibles :
1. Table `economic_events` vide → Vérifier DB
2. Fenêtre temporelle trop étroite → Élargir ±10 → ±20 min
3. Filtres importance trop stricts → Inclure LOW importance

### **MAE très élevé (>20 pips)**
Investiguer :
1. Patterns sans événements → Patterns techniques purs (non prédictibles)
2. Surprises extrêmes → Formule saturée (plafond ?)
3. Overlapping mal détecté → Vérifier timing_delta

---

## 📈 MÉTRIQUES ATTENDUES (ESTIMATION)

Basé sur Session 117 et validation 11 septembre :

| Métrique | Estimation |
|----------|------------|
| Patterns détectés | 10-20 |
| Patterns validables | 70-85% (10-17) |
| MAE moyen | 4-6 pips |
| MAE médian | 3-5 pips |
| R² | 0.88-0.94 |
| < 5 pips | 50-65% |
| < 10 pips | 80-90% |

**Note :** Estimations basées sur 1 cas validé (11 sept). Résultats réels peuvent varier.

---

## 🎯 APRÈS SESSION 124

### **Si GAP #1 résolu (critères atteints)**

**Session 125 :** Planificateur V2.9
- Intégrer formule S115
- Intégrer Rev12 pour détection automatique
- Interface utilisateur
- Tests end-to-end

### **Si ajustements nécessaires**

**Session 125 :** Optimisation
- Ajuster paramètres (amplification, momentum_factor)
- Analyser outliers en détail
- Tester variantes formule
- Re-valider

---

## 📚 RÉFÉRENCES

### **Documentation**
- `MASTER_PLAN.md` : Vision projet, GAP #1
- `SESSION_124_HANDOFF.md` : Instructions session
- `SESSION_120_RAPPORT.md` : Validation Rev12

### **Code Validé**
- `scripts/session120/double_wave_detector_rev12.py` : Rev12 (MAE 4.5 pips)
- `src/core/cluster_impact_calculator.py` : Formule S115

### **Cas Référence**
- **11 septembre 2025** : Double Wave validé
  - Wave1: 33.7 pips
  - Wave2: 51.7 pips
  - Total: 85.4 pips (vs 56.2 MT5)
  - MAE Rev12: 4.5 pips

---

## ⚡ COMMANDES RAPIDES

```bash
# Workflow complet
python scripts/session124/run_validation_workflow.py

# Test seulement
python scripts/session124/test_scan_setup.py

# Scan seulement
python scripts/session124/scan_with_rev12.py

# Validation seulement (après scan)
python scripts/session124/validate_formulas_multidates.py

# Analyse seulement (après validation)
python scripts/session124/analyze_results.py

# Workflow sans re-scanner
python scripts/session124/run_validation_workflow.py --skip-scan

# Scan période spécifique
python scripts/session124/scan_with_rev12.py --period 2025-01-01:2025-01-31

# Scan avec debug
python scripts/session124/scan_with_rev12.py --debug
```

---

## 📞 SUPPORT

**Si problème persistant :**
1. Vérifier logs console (messages d'erreur)
2. Vérifier tokens session (< 105k pour doc)
3. Consulter `MASTER_PLAN.md` section GAP #1
4. Consulter `SESSION_123_HANDOFF.md` (leçons)

---

**Auteur :** André Valentin avec Claude  
**Session :** 124  
**Date :** 09 novembre 2025  
**Tokens utilisés :** ~80k / 190k (scripts créés, docs, README)
