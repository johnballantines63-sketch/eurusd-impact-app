# 📁 ARCHITECTURE PROJET - EUR/USD News Impact Calculator

**Date création :** 21 octobre 2025  
**Session :** 26  
**Type :** Documentation technique permanente

---

## 🗂️ STRUCTURE RÉPERTOIRES

```
eurusd_news_impact_calculator_MPC/
├── fx_impact_app/                    # Application Streamlit principale
│   ├── data/                         # Données et base de données
│   │   ├── warehouse.duckdb          # Base de données principale ⭐
│   │   └── warehouse_BACKUP_*.duckdb # Backups datés
│   ├── modules/                      # Modules Python application
│   ├── pages/                        # Pages Streamlit
│   └── app.py                        # Point d'entrée Streamlit
│
├── KNOWLEDGE BASE/                   # Documentation sessions
│   ├── KNOWLEDGE_BASE.md             # Base principale
│   ├── KNOWLEDGE_BASE_UPDATE_SESSION*.md  # Mises à jour sessions
│   └── ARCHITECTURE_PROJET.md        # Ce fichier
│
├── RAPPORTS SESSIONS/                # Rapports détaillés sessions
│   ├── RAPPORT_SESSION*.md           # Rapports finaux
│   ├── REFERENCE_CASE_11_SEPT_2025.md  # Cas de validation
│   └── MESSAGE_POUR_CLAUDE_SESSION*.md # Instructions démarrage
│
├── backups/                          # Backups fichiers critiques
│   └── backup_v*_YYYYMMDD_HHMMSS.tar.gz
│
├── step*_*.py                        # Scripts reconstruction Session 26
├── *.py                              # Scripts utilitaires et corrections
└── *.csv                             # Données exportées

```

---

## 💾 BASE DE DONNÉES WAREHOUSE.DUCKDB

### Emplacement
```
fx_impact_app/data/warehouse.duckdb
```

### Taille actuelle
~205 MB (après nettoyage Session 26)

### Tables VALIDES (Session 26) ✅

**Tables de référence (ne pas modifier) :**

| Table | Lignes | Description | Source |
|-------|--------|-------------|--------|
| `events` | 58,449 | Événements bruts | EODHD API |
| `event_families` | 747 | Mappings événements → familles | Manuel Session 22 |
| `scores` | 991 | Scores empiriques | Calculs validés |
| `prices_1m` | 1,114,260 | Prix minute Dukascopy | **Dukascopy Session 25** ⭐ |
| `prices_5m` | 226,329 | Prix 5 minutes | Agrégation prices_1m |
| `prices_m15` | 77,057 | Prix 15 minutes | Agrégation prices_1m |
| `prices_m30` | 38,834 | Prix 30 minutes | Agrégation prices_1m |
| `prices_1h` | 19,563 | Prix 1 heure | Agrégation prices_1m |
| `prices_h4` | 4,843 | Prix 4 heures | Agrégation prices_1m |

**Tables calculées V2 (Session 26) :**

| Table | Lignes | Description | Source |
|-------|--------|-------------|--------|
| `event_impacts_v2` | ~16,335 | Impacts individuels surprise > 30% | **Dukascopy Session 26** |
| `event_groups_v2` | TBD | Groupes multi-événements | **Dukascopy Session 26** |

**Tables vues (read-only) :**
- `prices_*_v` : Vues sur tables prices_*
- `price_v` : Vue générale

---

## 📦 BACKUPS

### Backup Session 26 - Avant nettoyage

**Fichier :**
```
fx_impact_app/data/warehouse_BACKUP_SESSION26_before_clean.duckdb
```

**Date :** 21 octobre 2025  
**Taille :** 205.01 MB  
**Contenu :** Base complète AVANT suppression tables corrompues  
**Usage :** Rollback si problème pendant reconstruction

### Backups automatiques sessions précédentes

**Pattern :**
```
fx_impact_app/data/warehouse_BACKUP_SESSION[N]_*.duckdb
backups/backup_v*_YYYYMMDD_HHMMSS.tar.gz
```

**Conservation :** Garder backups des 3 dernières sessions majeures

---

## 📝 FICHIERS CRITIQUES

### Documentation permanente

| Fichier | Emplacement | Description |
|---------|-------------|-------------|
| `ARCHITECTURE_PROJET.md` | `KNOWLEDGE BASE/` | Ce fichier - Structure projet |
| `KNOWLEDGE_BASE.md` | `KNOWLEDGE BASE/` | Base de connaissances principale |
| `KNOWLEDGE_BASE_UPDATE_SESSION*.md` | `KNOWLEDGE BASE/` | Découvertes par session |

### Cas de validation

| Fichier | Emplacement | Description |
|---------|-------------|-------------|
| `REFERENCE_CASE_11_SEPT_2025.md` | `RAPPORTS SESSIONS/` | Cas référence validation 11 sept |

### Scripts Session 26 (reconstruction)

| Fichier | Description | Statut |
|---------|-------------|--------|
| `step1_backup_clean_session26.py` | Backup + Nettoyage | ✅ Validé |
| `step2_build_impacts_v2_session26.py` | Reconstruction event_impacts_v2 | 🔄 En cours |
| `step3_build_groups_v2_session26.py` | Reconstruction event_groups_v2 | ⏳ À créer |
| `step4_validate_v2_session26.py` | Validation complète | ⏳ À créer |

---

## 🔧 SCRIPTS UTILITAIRES

### Scripts de diagnostic

```
check_*.py                    # Vérification état base
analyze_*.py                  # Analyse données
diagnose_*.py                 # Diagnostic problèmes
inspect_*.py                  # Inspection structures
validate_*.py                 # Validation données
verify_*.py                   # Vérification résultats
```

### Scripts de correction

```
fix_*.py                      # Corrections bugs
apply_*.py                    # Application patches
clean_*.py                    # Nettoyage données
rebuild_*.py                  # Reconstruction tables
recalculate_*.py             # Recalcul métriques
```

### Scripts d'import

```
import_*.py                   # Import données externes
dukascopy_*.py               # Import Dukascopy spécifique
```

---

## 📊 DONNÉES EXPORTÉES

### CSV Session 26 (à créer)

| Fichier | Lignes | Description |
|---------|--------|-------------|
| `events_surprise30_v2_session26.csv` | ~16,335 | Export event_impacts_v2 |
| `event_groups_v2_session26.csv` | TBD | Export event_groups_v2 |

### CSV obsolètes (ne plus utiliser) ❌

```
events_extreme_surprise_dukascopy_session25.csv  # Données corrompues
extreme_cases_surprise30_session23.csv           # Anciennes sources
```

---

## 🎯 FICHIERS APPLICATION STREAMLIT

### Structure fx_impact_app/

```
fx_impact_app/
├── app.py                           # Point d'entrée principal
├── modules/
│   ├── database.py                  # Gestionnaire base de données
│   ├── predictions.py               # Formules prédiction
│   ├── calculations.py              # Calculs métriques
│   └── visualizations.py            # Graphiques
├── pages/
│   ├── 1_📅_Calendrier.py          # Page calendrier événements
│   ├── 2_📊_Planificateur.py       # Page planification trading
│   ├── 3_📈_Analyseur.py           # Page analyse impacts
│   └── 4_⚙️_Paramètres.py         # Page configuration
└── data/
    └── warehouse.duckdb             # Base de données
```

### Modules critiques

**`database.py`** : Connexion et requêtes DuckDB  
**`predictions.py`** : Formules V2 actuelles (à migrer vers V4)  
**`calculations.py`** : Calcul scores, surprise, impacts  

---

## 🔄 WORKFLOW DÉVELOPPEMENT

### 1. Démarrage nouvelle session

```bash
# Lire documentation
cat "KNOWLEDGE BASE/KNOWLEDGE_BASE_UPDATE_SESSION[dernière].md"
cat "RAPPORTS SESSIONS/MESSAGE_POUR_CLAUDE_SESSION[prochaine].md"

# Vérifier état base
python3 check_structure_quick.py
```

### 2. Backup avant modifications

```bash
# Backup manuel
cp fx_impact_app/data/warehouse.duckdb \
   fx_impact_app/data/warehouse_BACKUP_SESSION[N]_$(date +%Y%m%d).duckdb
```

### 3. Développement

```bash
# Scripts de diagnostic
python3 analyze_*.py

# Scripts de correction
python3 fix_*.py

# Validation
python3 validate_*.py
```

### 4. Documentation

```bash
# Mettre à jour Knowledge Base
vim "KNOWLEDGE BASE/KNOWLEDGE_BASE_UPDATE_SESSION[N].md"

# Créer rapport final
vim "RAPPORTS SESSIONS/RAPPORT_SESSION[N]_FINAL.md"
```

---

## 📌 CONVENTIONS NOMMAGE

### Scripts

```
[action]_[objet]_[détail]_session[N].py

Exemples :
- step1_backup_clean_session26.py
- build_event_impacts_v2_session26.py
- validate_reference_case_session25.py
```

### Tables base de données

```
[nom]_v[version]

Exemples :
- event_impacts_v2          # Version 2 (Session 26)
- event_groups_v2           # Version 2 (Session 26)
- prices_1m                 # Pas de version (stable)
```

### Fichiers documentation

```
[TYPE]_[SUJET]_SESSION[N].md

Exemples :
- KNOWLEDGE_BASE_UPDATE_SESSION26.md
- RAPPORT_SESSION25_FINAL.md
- MESSAGE_POUR_CLAUDE_SESSION26.md
```

### Backups

```
warehouse_BACKUP_SESSION[N]_[description].duckdb

Exemples :
- warehouse_BACKUP_SESSION26_before_clean.duckdb
- warehouse_BACKUP_SESSION25_after_dukascopy.duckdb
```

---

## 🚨 FICHIERS À NE JAMAIS SUPPRIMER

### Données critiques
- ✅ `fx_impact_app/data/warehouse.duckdb`
- ✅ Dernier backup `warehouse_BACKUP_SESSION*`

### Documentation
- ✅ `KNOWLEDGE BASE/KNOWLEDGE_BASE.md`
- ✅ `KNOWLEDGE BASE/ARCHITECTURE_PROJET.md`
- ✅ Tous fichiers `KNOWLEDGE_BASE_UPDATE_SESSION*.md`

### Application
- ✅ Tout le répertoire `fx_impact_app/`

---

## 🗑️ NETTOYAGE PÉRIODIQUE

### Fichiers à supprimer régulièrement

```bash
# Scripts de test temporaires
rm test_*.py

# CSV obsolètes (vérifier date)
rm *_session[N-3].csv  # Garder 3 dernières sessions

# Backups anciens (garder 3 derniers)
rm warehouse_BACKUP_SESSION[N-3]_*.duckdb
```

### Fichiers à archiver

```bash
# Créer archive session terminée
tar -czf backups/session_N_$(date +%Y%m%d).tar.gz \
    RAPPORTS\ SESSIONS/RAPPORT_SESSION[N]_*.md \
    step*_session[N].py \
    *_session[N].csv

# Supprimer fichiers archivés
rm step*_session[N].py
```

---

## 📈 ÉVOLUTION TAILLE BASE

| Session | Date | Taille | Tables | Événements |
|---------|------|--------|--------|------------|
| 23 | Oct 2025 | ~200 MB | 23 | 58,449 |
| 25 | Oct 2025 | ~205 MB | 23 | 58,449 |
| 26 (avant) | 21 Oct 2025 | 205 MB | 23 | 58,449 |
| 26 (après) | 21 Oct 2025 | ~205 MB | 20 | 58,449 |

---

## 🔗 LIENS UTILES

### Documentation externe
- Dukascopy API : https://www.dukascopy.com/swiss/english/marketwatch/historical/
- DuckDB Docs : https://duckdb.org/docs/
- Streamlit Docs : https://docs.streamlit.io/

### Repositories
- (À définir si Git utilisé)

---

## 📞 CONTACT / NOTES

**Développeur :** André  
**Assistant IA :** Claude (Anthropic)  
**Projet :** EUR/USD News Impact Calculator  
**Objectif :** Prédire impact événements économiques sur EUR/USD

---

**FIN ARCHITECTURE PROJET**

**Dernière mise à jour :** 21 octobre 2025 - Session 26  
**Prochaine révision :** Fin Session 26
