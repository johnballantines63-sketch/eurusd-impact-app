# 📊 PROJECT STATE - EUR/USD News Impact Calculator

**Dernière mise à jour :** 24 octobre 2025 (Session 60 - Reconstruction complète)  
**Source de vérité unique** - Ne PAS créer de fichiers PROJECT_STATE_UPDATE_*

---

## 📑 TABLE DES MATIÈRES

1. [État Actuel du Projet](#1-état-actuel-du-projet)
2. [Architecture Système](#2-architecture-système)
3. [Formules Validées](#3-formules-validées)
4. [Base de Données](#4-base-de-données)
5. [Scripts et Outils](#5-scripts-et-outils)
6. [Erreurs Récurrentes](#6-erreurs-récurrentes)
7. [Historique Sessions](#7-historique-sessions)
8. [Problèmes Connus](#8-problèmes-connus)
9. [Prochaines Étapes](#9-prochaines-étapes)

---

## 1. ÉTAT ACTUEL DU PROJET

### Progression Globale : **89%**

| Composant | Status | Progression |
|-----------|--------|-------------|
| **Core (app/core/)** | ✅ Complet | 100% |
| **Services (app/services/)** | ✅ Complet | 100% |
| **Utils (app/utils/)** | ✅ Complet | 100% |
| **Formules Validées** | ✅ Validées | 100% |
| **Planificateur Validation** | ⏳ En cours | 85% |
| **Interface UI** | ⏳ À faire | 0% |

### Dernières Sessions

| Session | Date | Mission | Résultat | Tokens |
|---------|------|---------|----------|--------|
| **S51** | 23/10 | Tests 4 formules | ✅ Formule D validée (98.6%) | 82k |
| **S52** | 23/10 | Validation TTR | ✅ Formule C créée (94.4%) | 71k |
| **S55** | 23/10 | Validation complète | ✅ Ajustement score (99.9%) | 96k |
| **S58** | 23/10 | Script validation | ✅ Bug identifié | 107k |
| **S59** | 23/10 | Correction bug | ❌ Échec méthodologique | 96k |
| **S60** | 24/10 | Reconstruction docs | ⏳ En cours | - |

---

## 2. ARCHITECTURE SYSTÈME

### Structure eurusd_clean/

```
eurusd_clean/
├── app/
│   ├── config.py                    ✅ Configuration centralisée
│   ├── core/                        ✅ Logique métier
│   │   ├── calculations.py          ✅ Calculs impacts
│   │   └── models.py                ✅ Modèles données
│   ├── services/                    ✅ Couche services
│   │   ├── data_service.py          ✅ Interface DB unique
│   │   ├── prediction_service.py    ✅ Prédictions impacts
│   │   └── scoring_service.py       ✅ Calcul scores
│   └── utils/                       ✅ Utilitaires
│       ├── time_windows.py          ✅ Groupement temporel
│       ├── backtest.py              ✅ Validation rétroactive
│       ├── fibonacci.py             ✅ Niveaux Fibonacci
│       ├── visualization.py         ✅ Graphiques Plotly
│       └── scoring.py               ✅ Score tradabilité
├── ui/                              ⏳ Interface (à faire)
├── tests/                           ✅ Tests unitaires
└── docs/                            ✅ Documentation

### Scripts Validation (Racine)

```
eurusd_news_impact_calculator_MPC/
├── test_4_formules_11sept.py        ⭐⭐⭐ Validation 4 formules
├── formulas_validated.py            ⭐⭐⭐ Module formules validées
├── validate_ttr_11sept.py           ✅ Validation TTR
├── validate_pullback_11sept.py      ✅ Validation Pullback
└── planificateur_11sept_FINAL.py    ⏳ Script validation (bug)
```

---

## 3. FORMULES VALIDÉES

### 📐 Formule D - Impact Multi-Événements (98.6%)

**Source :** `sequence_multi_event_timeline_v87.py`  
**Validation :** Session 51  
**MAE :** 0.8 pips sur cas 11 septembre 2025

**Architecture complète :**
```python
def formule_d_timeline_v87(events):
    # 1. Ajuster scores selon surprise
    adjusted_scores = [
        calculate_adjusted_empirical_score(e.empirical_score, e.surprise_pct)
        for e in events
    ]
    
    # 2. Calcul impacts individuels (Formule C base)
    impacts = [
        -10.47 + 0.477 * score  # Multi-événements
        for score in adjusted_scores
    ]
    
    # 3. Application direction avec sentiment
    contributions = [
        impact * get_event_direction(e.family, e.surprise)
        for impact, e in zip(impacts, events)
    ]
    
    # 4. Somme vectorielle
    impact_brut = sum(contributions)
    
    # 5. Amplification selon surprise max
    max_surprise = max(abs(e.surprise_pct) for e in events)
    if max_surprise <= 5:
        amplification = 1.0
    elif max_surprise <= 15:
        amplification = 1.0 + (max_surprise - 5) / 10 * 1.5
    else:
        amplification = 2.5  # Plafond
    
    # 6. Correction empirique
    impact_final = abs(impact_brut) * amplification * 0.758
    
    return impact_final * (1 if impact_brut >= 0 else -1)
```

**Exemple validation (11 septembre 2025) :**
- Impact prédit : +57.0 pips
- Impact réel MT5 : +56.2 pips
- MAE : 0.8 pips ✅

### 🔧 Ajustement Score (99.9%)

**Source :** `formulas_validated.py` v1.1  
**Création :** Session 55  
**MAE :** 0.1 sur cas 11 septembre

**Formule :**
```python
def calculate_adjusted_empirical_score(base_score, surprise_pct):
    abs_surprise = abs(surprise_pct)
    
    if abs_surprise < 5:
        factor = 1.0
    elif abs_surprise < 15:
        factor = 1.0 + (abs_surprise - 5) / 10 * 0.5  # 1.0 → 1.5
    elif abs_surprise < 30:
        factor = 1.5 + (abs_surprise - 15) / 15 * 0.4  # 1.5 → 1.9
    else:
        factor = 1.9  # Plafond
    
    return base_score * factor
```

**Pourquoi nécessaire :** Scores DB calculés sur historique moyen ne tiennent PAS compte de la surprise actuelle.

### ⏱️ Formule TTR C (94.4%)

**Source :** `formulas_validated.py` v1.0  
**Création :** Session 52  
**MAE :** 0.3 minutes

**Formule :**
```python
def calculate_ttr_c(latency_minutes, surprise_pct):
    abs_surprise = abs(surprise_pct)
    
    if abs_surprise < 10:
        multiplier = 3.0  # Mouvement lent
    elif abs_surprise < 30:
        multiplier = 2.5  # Mouvement normal
    else:
        multiplier = 2.0  # Mouvement rapide
    
    return latency_minutes * multiplier
```

**Logique :** Plus la surprise est forte, plus le marché atteint son pic rapidement.

### 📉 Formule Pullback V2 (99.3%)

**Source :** `formulas_validated.py` v1.0  
**Validation :** Session 53  
**MAE :** 0.2 pips

**Formule :**
```python
def calculate_pullback_v2(phase1_impact, minutes_since_peak, minutes_to_next):
    if minutes_to_next <= 0:
        ratio = 0.725  # Ratio empirique standard
    else:
        decay = min(1.0, minutes_since_peak / 30.0)
        ratio = 0.725 * (1 - 0.3 * decay)
    
    return phase1_impact * ratio
```

---

## 4. BASE DE DONNÉES

### Structure warehouse.duckdb

**Localisation :** `fx_impact_app/data/warehouse.duckdb`  
**Taille :** ~205 MB  
**Tables principales :**

```sql
-- Table événements (58,449 événements)
events (
    id, event_key, event_title, country, 
    importance_n, actual, forecast, estimate, previous,
    ts_utc, datetime, source
)

-- Table familles (scores pré-calculés)
event_families (
    family, country, event_key,
    empirical_score,     -- Score 0-100
    avg_movement_pips,   -- Mouvement moyen
    mfe_p80,            -- 80e percentile mouvement
    latency_median,     -- Latence médiane
    ttr_median,         -- TTR médian
    n_events            -- Nombre événements
)

-- Table validation (11 événements 11 septembre)
validation_events (
    id, event_date, event_time, event_datetime,
    family, country,
    actual, forecast, estimate, previous,
    surprise, surprise_pct,
    predicted_pips, direction,
    latency_median, ttr_median, empirical_score,
    source, notes
)

-- Table prix minute (1,114,260 lignes)
prices_1m (
    datetime,  -- ⚠️ Utiliser cette colonne (pas timestamp)
    open, high, low, close, volume
)
```

### Paramètres Critiques

**threshold_pips :** 2.0 (modifié Session 52)  
- ❌ Avant : 5.0 → TTR irréaliste (0.2 min)
- ✅ Après : 2.0 → TTR réaliste (18.9 min pour CPI)

### Cas de Référence : 11 Septembre 2025

**11 événements dédupliqués dans validation_events :**

**12:30 UTC (14:30 CEST) - 9 événements US :**
- Continuing Jobless Claims (score 85, surprise +11.9%)
- Initial Jobless Claims (score 85, surprise +2.2%)
- 4-Week Average Jobless (score 85, surprise 0%)
- Core CPI MoM (score 85, surprise +50% ⭐)
- CPI Index (score 85, surprise -0.03%)
- CPI Final (score 85, surprise 0%)
- CPI MoM (score 85, surprise 0%)
- CPI YoY (score 85, surprise -3.8%)
- Core CPI YoY (score 85, surprise 0%)

**12:45 UTC - 2 événements EUR :**
- ECB Press Conference
- Current Account (DE)

**Impact réel MT5 :**
- Annonce : 12:30:00 → 1.16816
- Pic (TTR) : 12:35:00 → 1.17190 (+37.4 pips)
- Après pullback : 12:45:00 → 1.16919
- **Impact net : +56.2 pips**

---

## 5. SCRIPTS ET OUTILS

### Scripts de Test Validés

| Script | Description | Validation |
|--------|-------------|------------|
| **test_4_formules_11sept.py** | Compare 4 formules sur 11 sept | ⭐⭐⭐ GOLD |
| **validate_ttr_11sept.py** | Validation TTR (Formule C) | ✅ S52 |
| **validate_pullback_11sept.py** | Validation Pullback V2 | ✅ S53 |
| **test_planificateur_v2_final.py** | Validation pipeline complet | ✅ S55 |

### Scripts de Diagnostic

| Script | Utilité | Création |
|--------|---------|----------|
| `check_db_dates.py` | Plage dates DB | S36 |
| `check_prices_structure.py` | Structure table prices_1m | S36 |
| `diagnostic_heures_events.py` | Vérif heures événements | S58 |
| `explore_db.py` | Exploration structure DB | S52 |

### Modules Core

| Module | Description | Tests |
|--------|-------------|-------|
| `formulas_validated.py` v1.1 | **4 formules validées** | ✅ |
| `app/services/data_service.py` | Interface DB unique | ✅ |
| `app/services/prediction_service.py` | Prédictions impacts | ✅ |
| `app/services/scoring_service.py` | Calcul scores | ✅ |

---

## 6. ERREURS RÉCURRENTES

### ❌ ERREUR #1 : Colonne event_name N'EXISTE PAS

```sql
-- ❌ INCORRECT
SELECT ef.event_name FROM event_families ef

-- ✅ CORRECT
SELECT e.event_title FROM events e
```

### ❌ ERREUR #2 : Forecast Souvent NULL

```python
# ❌ INCORRECT
forecast = event['forecast']  # Souvent NULL !

# ✅ CORRECT
forecast = event.get('estimate') or event.get('forecast') or event.get('previous')
```

### ❌ ERREUR #3 : Jointure Sans Country

```sql
-- ❌ INCORRECT
LEFT JOIN event_families ef ON e.event_key = ef.event_key

-- ✅ CORRECT  
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
```

### ❌ ERREUR #4 : Colonne timestamp au lieu de datetime

```python
# ❌ INCORRECT (colonne NULL dans prices_1m)
SELECT timestamp FROM prices_1m

# ✅ CORRECT
SELECT datetime FROM prices_1m
```

### ❌ ERREUR #5 : Config.db_path vs Config.get_db_path()

```python
# ❌ INCORRECT (attribut n'existe pas)
config = Config()
db_path = config.db_path

# ✅ CORRECT (méthode)
config = Config()
db_path = config.get_db_path()
```

### ❌ ERREUR #6 : Connexion Directe DB (Éviter)

```python
# ❌ INCORRECT (violation architecture)
conn = duckdb.connect('warehouse.duckdb')

# ✅ CORRECT (injection DataService)
from app.services.data_service import DataService
data_service = DataService(config.get_db_path())
```

### ❌ ERREUR #7 : Double Ajustement Score

**⚠️ PROBLÈME CRITIQUE NON RÉSOLU (Session 59)**

**Situation :**
- `validation_events` contient scores = 85.0
- Question : scores bruts (44.8) ou déjà ajustés (85.0) ?
- `test_4_formules_11sept.py` donne 57 pips (correct)

**Investigation nécessaire Session 60 :**
1. Lire `test_4_formules_11sept.py` ligne 83-104 et 250-330
2. Identifier quelle table il utilise vraiment
3. Vérifier s'il appelle `calculate_adjusted_empirical_score()`
4. Copier la logique EXACTE qui fonctionne

---

## 7. HISTORIQUE SESSIONS

### Sessions Clés (Succès)

| Session | Réalisation | Impact |
|---------|-------------|--------|
| **S28** | Création structure eurusd_clean/ | Foundation |
| **S29-32** | Migration core + services | Architecture |
| **S33-34** | Création utils/ | Outils |
| **S51** | Validation Formule D (98.6%) | ⭐⭐⭐ |
| **S52** | Création Formule TTR C (94.4%) | ⭐⭐⭐ |
| **S53** | Validation Pullback V2 (99.3%) | ⭐⭐⭐ |
| **S55** | Ajustement score (99.9%) | ⭐⭐⭐ |

### Sessions Problématiques (Échecs)

| Session | Problème | Leçon |
|---------|----------|-------|
| **S49** | N'a pas lu docs | Lire AVANT agir |
| **S57** | Réinvente au lieu de copier | Utiliser l'existant |
| **S59** | Répète erreur S57 | **LIRE ATTENTIVEMENT** |

### Pattern de Succès (S51-52-53-55)

✅ Lire documentation COMPLÈTE en premier (40k tokens)  
✅ Afficher tokens régulièrement  
✅ TESTER avant conclure  
✅ Documenter au fur et à mesure  
✅ Arrêter à 110k pour documentation finale  

---

## 8. PROBLÈMES CONNUS

### 🚨 Problème #7 : Double Ajustement Score (CRITIQUE)

**Status :** ⏳ Non résolu  
**Impact :** Bloque validation planificateur  
**Découvert :** Session 58  
**Échec correction :** Session 59

**Symptômes :**
- Script calcule 152.5 pips au lieu de 57 pips
- `validation_events` contient scores = 85.0
- Incertitude : bruts ou ajustés ?

**Solution Session 60 :**
1. ✅ Lire `test_4_formules_11sept.py` (fonctionne, donne 57 pips)
2. ✅ Identifier table utilisée (validation_events ou events+event_families)
3. ✅ Vérifier appel `calculate_adjusted_empirical_score()`
4. ✅ Copier logique EXACTE
5. ✅ Tester et valider

**Ne PAS :**
- ❌ Deviner quelle table utiliser
- ❌ Créer 5 versions de scripts
- ❌ Réinventer au lieu de copier

### ⚠️ Problème #6 : Confusion PROJECT_STATE

**Status :** ✅ RÉSOLU Session 59  
**Solution :** Unification en un seul fichier

**Règle établie :**
- ✅ Mettre à jour PROJECT_STATE.md directement
- ❌ NE PLUS créer PROJECT_STATE_UPDATE_SXX.md

### ⚠️ Problème #5 : TTR Surestimé

**Status :** ✅ RÉSOLU Session 52

**Cause :**
- threshold_pips = 5.0 → TTR 0.2 min ❌
- Formules A & B inadaptées

**Solution :**
- threshold_pips → 2.0 ✅
- Formule TTR C créée (94.4%) ✅

---

## 9. PROCHAINES ÉTAPES

### Session 60 : Résolution Problème #7 (PRIORITÉ)

**Mission SIMPLE et CLAIRE :**

**Étape 1 : Tester test_4_formules_11sept.py (5k tokens)**
```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC
python test_4_formules_11sept.py
```

Observer :
- ✅ Quel résultat pour Formule D ? (attendu : ~57 pips)
- ✅ Quels scores utilise-t-il ?
- ✅ Quelle table : validation_events ou events+event_families ?

**Étape 2 : Lire le code (15k tokens)**

Lignes critiques :
- Ligne 83-104 : load_11sept_events() - Quelle requête SQL EXACTE ?
- Ligne 250-330 : test_formule_d_vectorielle() - Utilise empirical_score TEL QUEL ?
- Ligne 431 : Quelle table vraiment ?

**Étape 3 : Copier la logique (30k tokens)**

Créer UN SEUL script : `planificateur_11sept_CORRECT.py`
- ✅ Même requête SQL
- ✅ Même table
- ✅ Même traitement scores
- ✅ Même logique Formule D

**Étape 4 : Valider (20k tokens)**

Critère succès : Impact ~57 pips (±5 pips)

**Étape 5 : Documenter (20k tokens)**

Total estimé : **90k tokens**

### Session 61+ : Interface Streamlit

Une fois Problème #7 résolu :
- Créer interface Streamlit propre
- Intégrer formules validées
- Tests bout-en-bout
- Documentation utilisateur

---

## 📚 RÉFÉRENCES RAPIDES

### Fichiers Critiques

```
eurusd_clean/
├── PROJECT_STATE.md                 ⭐⭐⭐ Ce fichier
├── docs/
│   ├── SESSION59_RAPPORT_FINAL.md   ⭐⭐⭐ Erreurs S59
│   ├── SESSION58_RAPPORT_FINAL.md   ⭐⭐⭐ Bug identifié
│   ├── SESSION55_RAPPORT_FINAL.md   ⭐⭐⭐ Ajustement score
│   ├── SESSION52_RAPPORT_FINAL.md   ⭐⭐ TTR C
│   └── SESSION51_RAPPORT_FINAL.md   ⭐⭐⭐ Formule D

/eurusd_news_impact_calculator_MPC/
├── test_4_formules_11sept.py        ⭐⭐⭐ SCRIPT QUI FONCTIONNE !
└── formulas_validated.py            ⭐⭐⭐ Module formules
```

### Commandes Utiles

```bash
# Tester formule D
python test_4_formules_11sept.py

# Lancer Streamlit (legacy)
cd fx_impact_app
streamlit run streamlit_app/Home.py

# Diagnostic DB
python check_db_dates.py
python check_prices_structure.py
```

---

## 🎯 RÈGLES ABSOLUES

### Pour TOUTES les Sessions Futures

**DO ✅**
1. Lire PROJECT_STATE.md EN PREMIER
2. Lire rapports sessions précédentes COMPLÈTEMENT
3. TESTER ce qui existe avant créer
4. Afficher tokens régulièrement
5. Arrêter à 110k pour documentation
6. Documenter honnêtement succès ET échecs

**DON'T ❌**
1. Sauter directement au code sans lire
2. Créer 5 versions d'un même script
3. Réinventer au lieu de copier l'existant
4. Ignorer scripts qui fonctionnent déjà
5. Créer PROJECT_STATE_UPDATE_* (mettre à jour ce fichier)
6. Deviner quand on peut TESTER

### Méthodologie Validée (S51-52-53-55)

```
1. Lecture documentation (40k tokens)
   └─> PROJECT_STATE + rapports précédents
   
2. Tests existant (10k tokens)
   └─> Ce qui fonctionne déjà
   
3. Implémentation ciblée (30k tokens)
   └─> Copier/adapter, pas réinventer
   
4. Validation immédiate (10k tokens)
   └─> Tester chaque étape
   
5. Documentation continue (20k tokens)
   └─> Au fur et à mesure
```

**Total : 110k tokens pour session productive**

---

## 🏆 RÉALISATIONS MAJEURES

- ✅ **4 formules validées** (Impact D, Ajustement, TTR C, Pullback V2)
- ✅ **Architecture modulaire** (core, services, utils)
- ✅ **98.6% précision** sur cas référence 11 septembre
- ✅ **Documentation exhaustive** (60+ rapports de session)
- ✅ **Méthodologie éprouvée** (pattern de succès défini)

---

## 📞 SUPPORT

**En cas de problème :**
1. Relire PROJECT_STATE.md (ce fichier)
2. Consulter rapports sessions récentes
3. Vérifier ERREURS_RÉCURRENTES (section 6)
4. Tester scripts qui fonctionnent
5. Documenter problème clairement

**Fichiers de référence :**
- PROJECT_STATE.md
- SESSION59_RAPPORT_FINAL.md (erreurs méthodologiques)
- SESSION58_RAPPORT_FINAL.md (bug double ajustement)
- SESSION55_RAPPORT_FINAL.md (ajustement score)
- SESSION51_RAPPORT_FINAL.md (formule D)

---

*Dernière reconstruction : 24 octobre 2025 - Session 60*  
*Base de connaissance : Sessions 28-59*  
*Prochaine mise à jour : Session 60 (résolution Problème #7)*
