# 📁 STRUCTURE PROJET - Vue d'Ensemble

**Créé :** Session 28 - 22 octobre 2025

---

## 🎯 Deux Projets Coexistent

```
/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/
│
├── [LEGACY]     fx_impact_app/ + 400+ fichiers    ❌ À NE PAS TOUCHER
│                (ancien projet chaotique)          (référence uniquement)
│
└── [NOUVEAU]    eurusd_clean/                     ✅ DÉVELOPPEMENT ICI
                 (structure propre professionnelle)
```

---

## ❌ STRUCTURE LEGACY (À NE PAS UTILISER)

**Répertoire racine chaotique :**
```
eurusd_news_impact_calculator_MPC/
├── fx_impact_app/
│   ├── src/                    # Modules production (à migrer)
│   ├── streamlit_app/          # UI Streamlit (à refactoriser)
│   └── data/
│       └── warehouse.duckdb    # Base de données (205 MB)
│
├── 400+ fichiers .py racine    ❌ Désorganisé
├── 50+ fichiers .backup        ❌ Pollution
├── Multiples versions          ❌ v85, v86, v87, v871...
├── RAPPORTS SESSIONS/          ❌ Documentation fragmentée
├── KNOWLEDGE BASE/             ❌ 10+ fichiers
└── Tests/                      ❌ Non organisés

PROBLÈMES :
- Code spaghetti (Planificateur 2,200 lignes)
- Imports circulaires
- Documentation fragmentée (10+ fichiers)
- Maintenance impossible
- Dette technique critique
```

---

## ✅ STRUCTURE CLEAN (NOUVEAU PROJET)

**Structure professionnelle dans `eurusd_clean/` :**

```
eurusd_clean/                           🏠 Racine projet clean
│
├── 📄 Fichiers Documentation Racine
│   ├── PROJECT_STATE.md                ⭐ FICHIER MAÎTRE (Source unique vérité)
│   ├── README.md                       📖 Guide démarrage rapide
│   ├── INSTALLATION.md                 🚀 Guide installation
│   ├── MESSAGE_SESSION_29.md           ✉️ Instructions prochaine session
│   ├── CHANGELOG.md                    📋 Historique versions
│   └── requirements.txt                📦 Dépendances Python
│
├── 📁 app/                             🎯 Application principale
│   ├── __init__.py                     ✅ Module Python
│   ├── config.py                       ⚙️ Configuration centralisée
│   │
│   ├── core/                           💎 Logique métier PURE
│   │   ├── __init__.py                 ✅ Créé
│   │   ├── models.py                   🚧 À créer (Event, Price, Family)
│   │   ├── calculations.py             🚧 À migrer (forecaster_mvp)
│   │   └── formulas.py                 🚧 À migrer (sequence_v87)
│   │
│   ├── services/                       🔧 Couche Services
│   │   ├── __init__.py                 ✅ Créé
│   │   ├── data_service.py             🚧 À créer (SEUL accès DB)
│   │   ├── prediction_service.py       🚧 À créer (Prédictions)
│   │   └── scoring_service.py          🚧 À créer (Scores)
│   │
│   ├── data/                           🗄️ Base de données
│   │   ├── README.md                   ✅ Documentation installation
│   │   └── warehouse.duckdb            🚧 À copier (205 MB)
│   │
│   └── utils/                          🛠️ Utilitaires
│       ├── __init__.py                 ✅ Créé
│       ├── db_utils.py                 🚧 À créer (Helpers DB)
│       └── date_utils.py               🚧 À créer (Helpers dates)
│
├── 📁 ui/                              🖥️ Interface Streamlit (SÉPARÉE!)
│   ├── Home.py                         🚧 À créer (~100 lignes)
│   │
│   ├── pages/                          📄 Pages Streamlit
│   │   ├── 1_Impact_Planner.py         🚧 À refactoriser (~200 lignes)
│   │   ├── 2_Calendrier.py             🚧 À refactoriser (~200 lignes)
│   │   ├── 3_Backtest.py               🚧 À refactoriser (~200 lignes)
│   │   ├── 4_Analyseur.py              🚧 À refactoriser (~200 lignes)
│   │   └── 5_Planificateur.py          🚧 À refactoriser (~250 lignes)
│   │
│   └── components/                     🧩 Composants réutilisables
│       ├── __init__.py                 🚧 À créer
│       ├── charts.py                   🚧 À créer (Graphiques Plotly)
│       ├── filters.py                  🚧 À créer (Filtres date/pays)
│       └── displays.py                 🚧 À créer (Affichage résultats)
│
├── 📁 scripts/                         🔧 Scripts administration
│   ├── migration/                      🔄 Migration legacy → clean
│   │   ├── setup_clean.py              ✅ Script installation
│   │   ├── analyze_current_usage.py    🚧 À créer Session 29
│   │   └── migrate_modules.py          🚧 À créer
│   │
│   ├── database/                       🗄️ Scripts gestion DB
│   │   ├── backup_db.py                🚧 À créer
│   │   ├── validate_schema.py          🚧 À créer
│   │   └── calculate_phase1.py         🚧 À créer (Phase 1 manquante)
│   │
│   ├── analysis/                       📊 Analyses ad-hoc
│   │   └── (scripts temporaires)
│   │
│   └── maintenance/                    🧹 Maintenance
│       ├── cleanup_old_backups.py      🚧 À créer
│       └── update_project_state.py     🚧 À créer
│
├── 📁 tests/                           ✅ Tests unitaires
│   ├── __init__.py                     🚧 À créer
│   ├── conftest.py                     🚧 À créer (Config pytest)
│   │
│   ├── test_core/                      🧪 Tests logique métier
│   │   ├── test_calculations.py        🚧 À créer
│   │   ├── test_formulas.py            🚧 À créer
│   │   └── test_models.py              🚧 À créer
│   │
│   ├── test_services/                  🧪 Tests services
│   │   ├── test_data_service.py        🚧 À créer
│   │   ├── test_prediction_service.py  🚧 À créer
│   │   └── test_scoring_service.py     🚧 À créer
│   │
│   └── test_integration/               🧪 Tests intégration
│       └── test_full_workflow.py       🚧 À créer
│
└── 📁 docs/                            📚 Documentation
    ├── archives/                       📦 Historique sessions legacy
    │   ├── sessions_01_10.md           🚧 À créer (résumé)
    │   ├── sessions_11_20.md           🚧 À créer
    │   └── sessions_21_27.md           🚧 À créer
    │
    ├── api/                            📖 Documentation technique
    │   ├── core_modules.md             🚧 À créer
    │   ├── services_api.md             🚧 À créer
    │   └── database_schema.md          🚧 À créer
    │
    └── guides/                         📘 Guides utilisateur
        ├── quickstart.md               🚧 À créer
        ├── trading_guide.md            🚧 À créer
        └── faq.md                      🚧 À créer
```

---

## 📊 Légende Statuts

| Symbole | Signification |
|---------|---------------|
| ✅ | Créé et fonctionnel |
| 🚧 | À créer/migrer |
| ⚙️ | Configuration |
| 💎 | Logique métier pure |
| 🔧 | Services |
| 🖥️ | Interface utilisateur |
| 🗄️ | Base de données |
| 🧪 | Tests |
| 📚 | Documentation |

---

## 🎯 Principes Architecture

### 1. Séparation Responsabilités

```
app/core/          → Logique métier pure (calculs, formules)
                    Pas de DB, pas de UI, testable isolément

app/services/      → Accès données et orchestration
                    Interface entre core et DB/API

ui/                → Interface utilisateur uniquement
                    Appelle services, n'accède jamais DB direct
```

### 2. Isolation Modules

```python
# ✅ CORRECT
from app.services.data_service import DataService
from app.core.calculations import calculate_impact

data = DataService()
events = data.get_events(...)
impact = calculate_impact(events)

# ❌ INCORRECT
import duckdb
conn = duckdb.connect(...)  # Accès DB direct depuis UI
```

### 3. Tests Systématiques

```
Chaque module app/core/     → Test unitaire tests/test_core/
Chaque service app/services/ → Test unitaire tests/test_services/
Workflow complet            → Test intégration tests/test_integration/
```

---

## 📋 Progression Migration

**Session 28 :** 10% complété
- ✅ Structure créée
- ✅ Documentation de base
- ✅ Scripts installation
- 🚧 Modules à migrer

**Session 29 :** Cible 30-40%
- 🚧 Inventaire modules legacy
- 🚧 Migration 2-3 modules core
- 🚧 Premiers tests unitaires

**Sessions 30-32 :** Cible 100%
- 🚧 Migration services
- 🚧 Refactorisation UI
- 🚧 Tests complets
- 🚧 Documentation

---

## 🧹 Nettoyage Futur

**Quand eurusd_clean/ sera opérationnel :**

```bash
# Supprimer tout le legacy
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC

# Backup si besoin
tar -czf legacy_backup_$(date +%Y%m%d).tar.gz \
    fx_impact_app/ \
    RAPPORTS\ SESSIONS/ \
    "KNOWLEDGE BASE/" \
    *.py *.md

# Supprimer legacy
rm -rf fx_impact_app/
rm -rf "RAPPORTS SESSIONS/"
rm -rf "KNOWLEDGE BASE/"
rm -rf .venv/ venv/ __pycache__/
rm *.py *.md *.sh

# Garder uniquement eurusd_clean/
# Optionnel : renommer
mv eurusd_clean eurusd_impact_calculator
```

**Résultat :** Structure propre, professionnelle, maintenable

---

## ✅ Avantages Structure Clean

| Aspect | Legacy | Clean |
|--------|--------|-------|
| Organisation | Chaotique (400+ fichiers) | Structurée (50 fichiers) |
| Maintenance | Impossible | Facile |
| Tests | 0% couverture | Objectif 80% |
| Documentation | Fragmentée (10+ fichiers) | Unique (PROJECT_STATE.md) |
| Déploiement | Impossible | Simple (1 dossier) |
| Onboarding | 2-3 heures | 15 minutes |

---

**Créé :** Session 28  
**Statut :** Structure créée, migration en cours  
**Fichier maître :** PROJECT_STATE.md (Section 2 mise à jour)
