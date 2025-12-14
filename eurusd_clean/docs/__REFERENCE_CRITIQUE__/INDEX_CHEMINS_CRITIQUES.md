# 🗺️ INDEX CHEMINS CRITIQUES - RÉFÉRENCE RAPIDE
**Mise à jour :** 04 novembre 2025 - Session 111  
**Usage :** Copier-coller rapide des chemins fichiers

---

## ✅ TOUS LES FICHIERS CRITIQUES SONT DANS CE RÉPERTOIRE !

**Chemin répertoire :**
```
eurusd_clean/docs/__REFERENCE_CRITIQUE__/
```

**TOUT est là ! Plus besoin de chercher ailleurs** 🎯

---

## 📚 FICHIERS DANS __REFERENCE_CRITIQUE__/ (20 fichiers)

### Documentation Principale
```
PROJECT_STATE_NEW.md                    # État global projet
MANDATORY_SESSION_RULES.md              # Règles sessions
FICHIERS_CRITIQUES_PROJET.md            # Liste complète détaillée
INDEX_CHEMINS_CRITIQUES.md              # Ce fichier
README.md                               # Point d'entrée principal
```

### Session 111 Actuelle
```
SESSION_111_ETAT_ACTUEL.md              # État session (Étape 1/4)
SESSION_111_PLAN_ACTION.md              # Plan 4 étapes
```

### Session 110
```
SESSION_110_RAPPORT_FINAL.md            # Rapport complet
SESSION_110_ETAT_PROBLEME_ARCHITECTURAL.md  # Problème identifié
SESSION_110_HANDOFF.md                  # Transition
```

### Guides Utilisateur
```
GUIDE_TIMEZONE_DEFINITIF.md             # Timezone (CRITIQUE !)
GUIDE_UTILISATEUR_PLANIFICATEUR.md      # Utilisation interface
DOUBLE_WAVE_GUIDE_UTILISATEUR.md        # Pattern Double Wave
DOUBLE_WAVE_MODEL.md                    # Modèle Double Wave
```

### Cas Référence
```
REFERENCE_CASE_11_SEPT_2025.md          # Cas GOLD STANDARD
```

### Erreurs & Anti-Patterns
```
ANTI_PATTERN_CRITIQUE.md                # Erreurs récurrentes
```

### Base de Données
```
DATABASE_SCHEMAS.md                     # Schémas tables
```

### Méthodologie Scientifique
```
PROJET_GESTION_SCIENTIFIQUE.md          # Méthodologie
PROJET_GESTION_SCIENTIFIQUE_COMPLEMENT.md
PROJET_GESTION_SCIENTIFIQUE_INTEGRE.md
```

---

## 🗂️ FICHIERS HORS __REFERENCE_CRITIQUE__ (code/données)

### 💾 Base de Données (NE PAS DÉPLACER)
```bash
# Chemin depuis __REFERENCE_CRITIQUE__/
../../../eurusd_clean/app/data/warehouse.duckdb  # 205 MB

# Chemin absolu
eurusd_clean/app/data/warehouse.duckdb
```

### 🧮 Formules Validées (code source)
```bash
# Depuis __REFERENCE_CRITIQUE__/
../../../fx_impact_app/src/formulas_validated.py
../../../fx_impact_app/src/cluster_impact_calculator.py

# Absolu
fx_impact_app/src/formulas_validated.py
fx_impact_app/src/cluster_impact_calculator.py
```

### 🖥️ Interface Planificateur (code source)
```bash
# Depuis __REFERENCE_CRITIQUE__/
../../../fx_impact_app/streamlit_app/pages/6_Planificateur_V27_AMPLIFICATION_DYNAMIQUE.py

# Absolu
fx_impact_app/streamlit_app/pages/6_Planificateur_V27_AMPLIFICATION_DYNAMIQUE.py
```

### 📊 Dataset CPI Validé
```bash
# Depuis __REFERENCE_CRITIQUE__/
../../../eurusd_clean/scripts/session99/real_impacts_TIMEZONE_FIX_FINAL.csv

# Absolu
eurusd_clean/scripts/session99/real_impacts_TIMEZONE_FIX_FINAL.csv
```

### 🔬 Scripts Validation
```bash
# Depuis __REFERENCE_CRITIQUE__/
../../../eurusd_clean/scripts/session84/validate_predictions_vs_reality.py
../../../eurusd_clean/scripts/sessionXX/test_4_formules_11sept.py
../../../eurusd_clean/scripts/session82/list_available_dates.py

# Absolu
eurusd_clean/scripts/session84/validate_predictions_vs_reality.py
eurusd_clean/scripts/sessionXX/test_4_formules_11sept.py
eurusd_clean/scripts/session82/list_available_dates.py
```

---

## 📂 STRUCTURE PROJET COMPLÈTE

```
eurusd_news_impact_calculator_MPC/
├── eurusd_clean/
│   ├── app/
│   │   └── data/
│   │       └── warehouse.duckdb              ⚠️ 205 MB
│   ├── docs/
│   │   ├── __REFERENCE_CRITIQUE__/          ⭐ 20 FICHIERS CRITIQUES
│   │   │   ├── README.md
│   │   │   ├── PROJECT_STATE_NEW.md
│   │   │   ├── MANDATORY_SESSION_RULES.md
│   │   │   ├── SESSION_111_*.md (2)
│   │   │   ├── SESSION_110_*.md (3)
│   │   │   ├── GUIDE_*.md (4)
│   │   │   ├── REFERENCE_CASE_*.md (1)
│   │   │   ├── ANTI_PATTERN_*.md (1)
│   │   │   ├── DATABASE_*.md (1)
│   │   │   ├── PROJET_GESTION_*.md (3)
│   │   │   └── INDEX_*.md + FICHIERS_*.md (2)
│   │   └── (280+ fichiers historiques)      📁 Archives
│   └── scripts/
│       └── sessionXXX/                      🔬 Scripts par session
│
└── fx_impact_app/
    ├── src/
    │   ├── formulas_validated.py            🧮 Formules S51-55
    │   └── cluster_impact_calculator.py     🧮 Module S111
    └── streamlit_app/
        └── pages/
            └── 6_Planificateur_V27_*.py     🖥️ Interface
```

---

## 🎯 COMMANDES UTILES

```bash
# Aller dans répertoire critique
cd eurusd_clean/docs/__REFERENCE_CRITIQUE__

# Lister fichiers critiques
ls -la

# Lancer Planificateur (depuis __REFERENCE_CRITIQUE__/)
cd ../../../fx_impact_app/streamlit_app
streamlit run streamlit_app.py

# Tester formules validées
cd ../../../eurusd_clean/scripts/sessionXX
python test_4_formules_11sept.py

# Scanner dates disponibles
cd ../../../eurusd_clean/scripts/session82
python list_available_dates.py

# Valider prédictions
cd ../../../eurusd_clean/scripts/session84
python validate_predictions_vs_reality.py
```

---

## 📋 CHECKLIST RAPIDE

### Début session
- [ ] `README.md`
- [ ] `PROJECT_STATE_NEW.md`
- [ ] `MANDATORY_SESSION_RULES.md`
- [ ] Rapport session précédente

### Avant coder
- [ ] `formulas_validated.py` (réutiliser)
- [ ] `GUIDE_TIMEZONE_DEFINITIF.md` (si dates/prix)
- [ ] `DATABASE_SCHEMAS.md` (si requêtes DB)

### Fin session
- [ ] Créer rapport session
- [ ] Mettre à jour `PROJECT_STATE_NEW.md`
- [ ] Mettre à jour `SESSION_XXX_ETAT_ACTUEL.md`

---

## 💡 AVANTAGE : CHEMINS SIMPLES

### Avant (fichiers éparpillés)
```bash
# Complexe
../../docs/PROJECT_STATE_NEW.md
../../docs/MANDATORY_SESSION_RULES.md
../../docs/SESSION_110_RAPPORT_FINAL.md
```

### Après (tous dans __REFERENCE_CRITIQUE__/)
```bash
# Simple
PROJECT_STATE_NEW.md
MANDATORY_SESSION_RULES.md
SESSION_110_RAPPORT_FINAL.md
```

**Même répertoire = Chemins simples = Moins d'erreurs** 🎯

---

## 🔗 NAVIGATION DEPUIS __REFERENCE_CRITIQUE__/

```bash
# Vers racine projet
cd ../../../../

# Vers docs/ (archives historiques)
cd ..

# Vers app/data/ (DuckDB)
cd ../../app/data/

# Vers fx_impact_app/src/ (code formules)
cd ../../../fx_impact_app/src/

# Vers scripts/session111/
cd ../../scripts/session111/
```

---

## 🎓 RÉSUMÉ (TL;DR)

**20 fichiers critiques** → Dans `__REFERENCE_CRITIQUE__/`  
**Code source** → Dans `fx_impact_app/src/`  
**Base données** → Dans `app/data/`  
**Scripts** → Dans `scripts/sessionXXX/`  
**Archives** → Dans `docs/` (280+ fichiers)

**Tout est organisé. Rien à chercher.** ✅

---

**Dernière mise à jour :** 04 novembre 2025 - Session 111  
**Version :** 2.0 (Chemins simplifiés, tout centralisé)
