# 📂 RÉPERTOIRE DE TRAVAIL - RÉFÉRENCE PERMANENTE

**Créé :** 27 octobre 2025 - Session 95  
**Objectif :** Documenter chemins absolus pour éviter recherches répétées  
**Statut :** Document de référence permanent

---

## 🎯 POURQUOI CE DOCUMENT

**Problème récurrent :** Sessions perdent temps à retrouver chemins corrects.

**Solution :** Documenter UNE FOIS les chemins absolus critiques.

**Utilisation :** Lire ce fichier EN PRIORITÉ au début de chaque session.

---

## 📍 RÉPERTOIRE RACINE PROJET

### Chemin Absolu

```
/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC
```

**Variable recommandée :**
```python
from pathlib import Path

# RACINE PROJET
PROJECT_ROOT = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC")

# Vérification existence
assert PROJECT_ROOT.exists(), f"Répertoire projet introuvable : {PROJECT_ROOT}"
```

---

## 📁 STRUCTURE PROJET PRINCIPALE

### Architecture Deux Répertoires

Le projet a **DEUX structures principales** :

#### 1. Structure Racine (Legacy - 400+ fichiers)
```
/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/
├── fx_impact_app/          # Application Streamlit LEGACY
│   ├── streamlit_app/
│   │   └── pages/
│   │       ├── copie 2.py  # Planificateur PRODUCTION (V2.4)
│   │       └── copie 3.py  # Planificateur BACKUP V2.4
│   ├── src/
│   │   └── formulas_validated.py  # Formules Sessions 51-55
│   └── data/
│       └── warehouse.duckdb  # Base de données (205 MB)
├── docs/                    # Documentation ancienne
├── scripts/                 # Scripts Python anciens
└── [400+ fichiers Python/MD]
```

#### 2. Structure Clean (Nouveau - Organisé)
```
/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/
├── app/
│   ├── core/               # Calculs et modèles
│   ├── services/           # Services métier
│   ├── utils/              # Utilitaires
│   └── data/
│       └── warehouse.duckdb  # Base données (COPIE ou LIEN)
├── docs/                   # Documentation Sessions 29+
│   ├── project_state_new.md     # ÉTAT PROJET OFFICIEL ⭐⭐⭐⭐⭐
│   ├── MANDATORY_SESSION_RULES.md  # RÈGLES OBLIGATOIRES ⭐⭐⭐⭐
│   ├── POSTMORTEM_SESSIONS_92.1-92.4.md  # ÉCHECS À ÉVITER ⭐⭐⭐
│   └── SESSION[N]_RAPPORT_COMPLET.md  # Rapports sessions
├── scripts/                # Scripts par session
│   ├── session92/
│   ├── session93/
│   ├── session94/
│   └── session95/
├── tests/                  # Tests unitaires
└── ui/                     # Interface utilisateur
```

---

## 🔑 FICHIERS CRITIQUES

### Documentation (À lire CHAQUE session)

| Fichier | Chemin Absolu | Priorité |
|---------|---------------|----------|
| **État Projet** | `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/project_state_new.md` | ⭐⭐⭐⭐⭐ |
| **Règles Obligatoires** | `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/MANDATORY_SESSION_RULES.md` | ⭐⭐⭐⭐ |
| **Post-Mortem Échecs** | `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/POSTMORTEM_SESSIONS_92.1-92.4.md` | ⭐⭐⭐ |

### Code Production

| Fichier | Chemin Absolu | Description |
|---------|---------------|-------------|
| **Planificateur V2.4** | `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/copie 2.py` | PRODUCTION - NE PAS MODIFIER directement |
| **Backup V2.4** | `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/copie 3.py` | SOURCE V2.4 - INTOUCHABLE |
| **Formules Validées** | `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/src/formulas_validated.py` | Sessions 51-55 - SACRÉES |

### Base de Données

| Fichier | Chemin Absolu | Taille | Tables Critiques |
|---------|---------------|--------|------------------|
| **Warehouse** | `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/data/warehouse.duckdb` | 205 MB | events, event_families, prices_1m, validation_events |

---

## 🐍 TEMPLATES PYTHON

### Template Import Projet

```python
#!/usr/bin/env python3
"""
Script : mon_script.py
Session : [N]
Description : [Description]
"""

from pathlib import Path
import sys

# ═══════════════════════════════════════════════════════════
# CHEMINS ABSOLUS PROJET (NE PAS MODIFIER)
# ═══════════════════════════════════════════════════════════

PROJECT_ROOT = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC")
EURUSD_CLEAN = PROJECT_ROOT / "eurusd_clean"

# Vérifications existence
assert PROJECT_ROOT.exists(), f"❌ Projet introuvable : {PROJECT_ROOT}"
assert EURUSD_CLEAN.exists(), f"❌ eurusd_clean introuvable : {EURUSD_CLEAN}"

# Ajout chemins Python
sys.path.insert(0, str(PROJECT_ROOT / "fx_impact_app"))
sys.path.insert(0, str(EURUSD_CLEAN / "app"))

# ═══════════════════════════════════════════════════════════
# IMPORTS PROJET
# ═══════════════════════════════════════════════════════════

# Legacy
from src.formulas_validated import (
    calculate_adjusted_empirical_score,
    calculate_impact_d,
    calculate_ttr_c,
    calculate_pullback_v2
)

# Clean structure
from core.calculations import calculate_surprise
from services.prediction_service import PredictionService

# ═══════════════════════════════════════════════════════════
# BASE DE DONNÉES
# ═══════════════════════════════════════════════════════════

import duckdb

DB_PATH = PROJECT_ROOT / "fx_impact_app" / "data" / "warehouse.duckdb"
assert DB_PATH.exists(), f"❌ Base données introuvable : {DB_PATH}"

def get_connection(read_only=True):
    """Connexion base données avec gestion contexte"""
    return duckdb.connect(str(DB_PATH), read_only=read_only)

# ═══════════════════════════════════════════════════════════
# CODE PRINCIPAL
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(f"✅ Projet chargé : {PROJECT_ROOT}")
    print(f"✅ Base données : {DB_PATH}")
    
    # Ton code ici
    with get_connection() as conn:
        result = conn.execute("SELECT COUNT(*) FROM events").fetchone()
        print(f"✅ Events dans DB : {result[0]:,}")
```

### Template Chemins Fichiers

```python
from pathlib import Path

# RACINE
PROJECT_ROOT = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC")

# DOCUMENTATION
DOCS_DIR = PROJECT_ROOT / "eurusd_clean" / "docs"
PROJECT_STATE = DOCS_DIR / "project_state_new.md"
MANDATORY_RULES = DOCS_DIR / "MANDATORY_SESSION_RULES.md"
POSTMORTEM = DOCS_DIR / "POSTMORTEM_SESSIONS_92.1-92.4.md"

# RAPPORTS SESSIONS
SESSION_REPORT = DOCS_DIR / f"SESSION{session_num}_RAPPORT_COMPLET.md"
MESSAGE_TRANSITION = DOCS_DIR / f"MESSAGE_SESSION{session_num}_SESSION{session_num+1}.md"

# CODE PRODUCTION
STREAMLIT_PAGES = PROJECT_ROOT / "fx_impact_app" / "streamlit_app" / "pages"
PLANIFICATEUR_PROD = STREAMLIT_PAGES / "copie 2.py"
PLANIFICATEUR_BACKUP = STREAMLIT_PAGES / "copie 3.py"
FORMULAS_VALIDATED = PROJECT_ROOT / "fx_impact_app" / "src" / "formulas_validated.py"

# BASE DONNÉES
DB_PATH = PROJECT_ROOT / "fx_impact_app" / "data" / "warehouse.duckdb"

# SCRIPTS SESSION
SCRIPTS_DIR = PROJECT_ROOT / "eurusd_clean" / "scripts" / f"session{session_num}"
SCRIPTS_DIR.mkdir(exist_ok=True, parents=True)

# Vérifications
for path in [PROJECT_ROOT, DOCS_DIR, STREAMLIT_PAGES, DB_PATH]:
    assert path.exists(), f"❌ Chemin introuvable : {path}"

print("✅ Tous les chemins vérifiés")
```

---

## 🔍 COMMANDES FILESYSTEM CLAUDE

### Lecture Fichiers

```python
# Lire documentation (utiliser head pour aperçu)
filesystem:read_text_file(
    path="/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/project_state_new.md",
    head=50  # Premiers 50 lignes
)

# Lire code complet
filesystem:read_text_file(
    path="/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/copie 3.py"
)
```

### Écriture Fichiers

```python
# Créer rapport session
filesystem:write_file(
    path="/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/SESSION95_RAPPORT_COMPLET.md",
    content="# Rapport Session 95\n\n..."
)

# Créer script session
filesystem:write_file(
    path="/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session95/mon_script.py",
    content="#!/usr/bin/env python3\n# Script Session 95\n"
)
```

### Navigation

```python
# Lister contenu répertoire
filesystem:list_directory(
    path="/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs"
)

# Arbre répertoire
filesystem:directory_tree(
    path="/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts"
)
```

---

## 🚨 ERREURS FRÉQUENTES À ÉVITER

### ❌ ERREUR #1 : Chemins Relatifs Ambigus

**Mauvais :**
```python
DB_PATH = Path("fx_impact_app/data/warehouse.duckdb")  # Relatif à quoi ?
```

**Correct :**
```python
PROJECT_ROOT = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC")
DB_PATH = PROJECT_ROOT / "fx_impact_app" / "data" / "warehouse.duckdb"
```

### ❌ ERREUR #2 : Confusion eurusd_clean vs Racine

**Mauvais :**
```python
# Où est ce fichier exactement ?
docs_path = "docs/project_state_new.md"
```

**Correct :**
```python
# eurusd_clean/docs/ ou racine/docs/ ?
EURUSD_CLEAN_DOCS = PROJECT_ROOT / "eurusd_clean" / "docs" / "project_state_new.md"
ROOT_DOCS = PROJECT_ROOT / "docs"
```

### ❌ ERREUR #3 : Oublier Vérification Existence

**Mauvais :**
```python
DB_PATH = Path("/some/path/warehouse.duckdb")
conn = duckdb.connect(str(DB_PATH))  # Crash si fichier absent
```

**Correct :**
```python
DB_PATH = PROJECT_ROOT / "fx_impact_app" / "data" / "warehouse.duckdb"
assert DB_PATH.exists(), f"❌ Base données introuvable : {DB_PATH}"
conn = duckdb.connect(str(DB_PATH))
```

### ❌ ERREUR #4 : Hardcoder Numéro Session

**Mauvais :**
```python
report_path = "eurusd_clean/docs/SESSION95_RAPPORT_COMPLET.md"
```

**Correct :**
```python
session_num = 95  # Variable au début du script
REPORT_PATH = DOCS_DIR / f"SESSION{session_num}_RAPPORT_COMPLET.md"
```

---

## ✅ CHECKLIST DÉMARRAGE SESSION

### Avant Tout Code

- [ ] Lire ce fichier (`REPERTOIRE_TRAVAIL_REFERENCE.md`)
- [ ] Vérifier PROJECT_ROOT existe
- [ ] Vérifier DB_PATH existe
- [ ] Créer répertoire session si nécessaire
- [ ] Tester imports projet fonctionnent

### Template Vérification Rapide

```python
from pathlib import Path

# Chemins critiques
PROJECT_ROOT = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC")
DB_PATH = PROJECT_ROOT / "fx_impact_app" / "data" / "warehouse.duckdb"
DOCS_DIR = PROJECT_ROOT / "eurusd_clean" / "docs"

# Vérifications
checks = {
    "Projet": PROJECT_ROOT.exists(),
    "Base données": DB_PATH.exists(),
    "Documentation": DOCS_DIR.exists()
}

for item, ok in checks.items():
    status = "✅" if ok else "❌"
    print(f"{status} {item}")

assert all(checks.values()), "❌ Chemins manquants détectés"
print("\n✅ Tous les chemins vérifiés - Prêt à coder !")
```

---

## 📊 CHEMINS PAR TYPE

### Documentation

```
/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/
├── project_state_new.md                     # État projet officiel
├── MANDATORY_SESSION_RULES.md               # Règles obligatoires
├── POSTMORTEM_SESSIONS_92.1-92.4.md        # Échecs à éviter
├── SESSION[N]_RAPPORT_COMPLET.md           # Rapports sessions
├── MESSAGE_SESSION[N]_SESSION[N+1].md      # Transitions
└── [Autres docs]
```

### Code Production

```
/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/
├── streamlit_app/
│   └── pages/
│       ├── copie 2.py          # PRODUCTION V2.4
│       └── copie 3.py          # BACKUP V2.4
└── src/
    └── formulas_validated.py   # Formules S51-55
```

### Scripts Sessions

```
/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/
├── session92/
│   ├── amplification_wrapper.py
│   └── formulas_hybrid_empirical.py
├── session93/
├── session94/
│   ├── integrate_addon_planificateur.py
│   └── test_wrapper_validation.py
└── session95/
    └── [Scripts Session 95]
```

### Base Données

```
/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/data/
└── warehouse.duckdb            # 205 MB, 58,449+ events
```

---

## 🎓 BONNES PRATIQUES

### 1. Toujours Utiliser Chemins Absolus

```python
# ✅ BON
PROJECT_ROOT = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC")
fichier = PROJECT_ROOT / "eurusd_clean" / "docs" / "mon_fichier.md"

# ❌ MAUVAIS
fichier = "eurusd_clean/docs/mon_fichier.md"  # Relatif à quoi ?
```

### 2. Vérifier Existence Avant Utilisation

```python
# ✅ BON
fichier = PROJECT_ROOT / "data" / "important.csv"
if not fichier.exists():
    raise FileNotFoundError(f"Fichier introuvable : {fichier}")

# ❌ MAUVAIS
df = pd.read_csv(fichier)  # Crash si absent
```

### 3. Créer Répertoires Si Nécessaire

```python
# ✅ BON
scripts_dir = PROJECT_ROOT / "eurusd_clean" / "scripts" / f"session{num}"
scripts_dir.mkdir(exist_ok=True, parents=True)

# ❌ MAUVAIS
fichier = scripts_dir / "script.py"  # Crash si répertoire absent
```

### 4. Utiliser Variables au Lieu de Hardcoder

```python
# ✅ BON
session_num = 95
REPORT = DOCS_DIR / f"SESSION{session_num}_RAPPORT_COMPLET.md"

# ❌ MAUVAIS
REPORT = DOCS_DIR / "SESSION95_RAPPORT_COMPLET.md"
```

---

## 🔄 MISE À JOUR DOCUMENT

**Ce document doit être mis à jour si :**
- Structure projet change
- Nouveaux répertoires critiques ajoutés
- Chemins absolus modifiés
- Migration projet vers nouveau Mac/utilisateur

**Procédure mise à jour :**
1. Modifier ce fichier
2. Ajouter note en bas avec date + raison
3. Référencer dans `project_state_new.md`

---

## 📝 HISTORIQUE MODIFICATIONS

| Date | Session | Modification | Raison |
|------|---------|--------------|--------|
| 27 oct 2025 | 95 | Création document | Éviter recherches répétées chemins |

---

**FIN DOCUMENTATION RÉPERTOIRE TRAVAIL**

**Ce fichier est une RÉFÉRENCE PERMANENTE à consulter au début de CHAQUE session.**

**Gain temps estimé : 5-10 minutes par session évitées en recherches chemins.**

---

*Créé : 27 octobre 2025 - Session 95*  
*Dernière mise à jour : 27 octobre 2025*  
*Maintenu par : Claude + André*
