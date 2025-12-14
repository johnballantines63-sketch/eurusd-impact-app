# 📁 RÉPERTOIRE RÉFÉRENCE CRITIQUE
**Créé :** 04 novembre 2025 - Session 111  
**Objectif :** Centraliser TOUS les fichiers essentiels du projet

---

## 🎯 COMMENCER ICI !

**Si vous démarrez une nouvelle session, lisez dans cet ordre :**

1. **`README.md`** (ce fichier) - 2 min ⭐⭐⭐
2. **`METHODES_VALIDEES.md`** - 10 min ⭐⭐⭐⭐⭐ **DOCUMENT EDISON**
3. **`PROJECT_STATE_NEW.md`** - 15 min ⭐⭐⭐
4. **`MANDATORY_SESSION_RULES.md`** - 5 min ⭐⭐⭐
5. **`SESSION_111_ETAT_ACTUEL.md`** - 5 min (si Session 111 en cours) ⭐⭐⭐

**Total : 37 min maximum**

---

## 📂 CONTENU COMPLET DE CE RÉPERTOIRE

### 📚 Documentation Principale (5 fichiers)

```
PROJECT_STATE_NEW.md                    ⭐⭐⭐ État global projet (source vérité)
MANDATORY_SESSION_RULES.md              ⭐⭐⭐ Règles sessions obligatoires
FICHIERS_CRITIQUES_PROJET.md            ⭐⭐  Liste complète + descriptions
INDEX_CHEMINS_CRITIQUES.md              ⭐⭐  Chemins rapides copier-coller
README.md                               ⭐⭐⭐ Ce fichier
```

### 📊 Session 111 Actuelle (2 fichiers)

```
SESSION_111_ETAT_ACTUEL.md              ⭐⭐⭐ État session (Étape 1/4 done)
SESSION_111_PLAN_ACTION.md              ⭐⭐  Plan détaillé 4 étapes
```

### 📝 Session 110 (3 fichiers)

```
SESSION_110_RAPPORT_FINAL.md            ⭐⭐  Rapport complet Session 110
SESSION_110_ETAT_PROBLEME_ARCHITECTURAL.md ⭐⭐ Problème pattern matching
SESSION_110_HANDOFF.md                  ⭐    Transition 110→111
```

### 🎓 Guides Utilisateur (4 fichiers)

```
GUIDE_TIMEZONE_DEFINITIF.md             ⭐⭐⭐ CRITIQUE pour dates/prix
GUIDE_UTILISATEUR_PLANIFICATEUR.md      ⭐⭐  Utilisation Planificateur
DOUBLE_WAVE_GUIDE_UTILISATEUR.md        ⭐    Pattern Double Wave
DOUBLE_WAVE_MODEL.md                    ⭐    Modèle Double Wave
```

### 📊 Cas Référence (1 fichier)

```
REFERENCE_CASE_11_SEPT_2025.md          ⭐⭐⭐ Cas GOLD STANDARD
```

### 🚨 Erreurs & Anti-Patterns (1 fichier)

```
ANTI_PATTERN_CRITIQUE.md                ⭐⭐  Erreurs à éviter
```

### 💾 Base de Données (1 fichier)

```
DATABASE_SCHEMAS.md                     ⭐⭐  Schémas tables DuckDB
```

### 🔬 Méthodologie Scientifique (3 fichiers)

```
PROJET_GESTION_SCIENTIFIQUE.md          ⭐⭐  Méthodologie projet
PROJET_GESTION_SCIENTIFIQUE_COMPLEMENT.md ⭐  Complément
PROJET_GESTION_SCIENTIFIQUE_INTEGRE.md  ⭐    Version intégrée
```

---

**TOTAL : 20 FICHIERS CRITIQUES** ✅

**Tous les autres (280+) restent dans `/docs/` pour recherches historiques**

---

## 🗺️ FICHIERS HORS DE CE RÉPERTOIRE

### 💾 Base de Données (NON déplacée)
```
../../../eurusd_clean/app/data/warehouse.duckdb  ⚠️ 205 MB
```

### 🧮 Formules Validées (NON déplacées - code source)
```
../../../fx_impact_app/src/formulas_validated.py           ⭐⭐⭐ Formules S51-55
../../../fx_impact_app/src/cluster_impact_calculator.py    ⭐⭐⭐ Module S111
```

### 🖥️ Interface Planificateur (NON déplacée - code source)
```
../../../fx_impact_app/streamlit_app/pages/6_Planificateur_V27_AMPLIFICATION_DYNAMIQUE.py
```

### 📊 Dataset CPI Validé (NON déplacé - résultats)
```
../../../eurusd_clean/scripts/session99/real_impacts_TIMEZONE_FIX_FINAL.csv
```

### 🔬 Scripts Validation (NON déplacés - scripts)
```
../../../eurusd_clean/scripts/session84/validate_predictions_vs_reality.py
../../../eurusd_clean/scripts/sessionXX/test_4_formules_11sept.py
../../../eurusd_clean/scripts/session82/list_available_dates.py
```

---

## 🚀 NAVIGATION RAPIDE PAR SITUATION

### 📖 Je démarre une nouvelle session
```
Lire : README.md (2 min)
    → PROJECT_STATE_NEW.md (15 min)
    → MANDATORY_SESSION_RULES.md (5 min)
    → Rapport session précédente (10 min)
```

### 🔄 Je reprends Session 111
```
Lire : SESSION_111_ETAT_ACTUEL.md (5 min)
    → SESSION_111_PLAN_ACTION.md (5 min)
    → Vérifier token usage
    → GO !
```

### 🧮 Je veux calculer un impact
```
Code : ../../../fx_impact_app/src/formulas_validated.py
    → calculate_impact_d()
Valider : REFERENCE_CASE_11_SEPT_2025.md
```

### 📊 Je veux comprendre les clusters
```
Lire : SESSION_110_RAPPORT_FINAL.md (observations MT5)
    → SESSION_110_ETAT_PROBLEME_ARCHITECTURAL.md (problème)
Code : ../../../fx_impact_app/src/cluster_impact_calculator.py
```

### 🧪 Je veux tester sur une nouvelle date
```
Script : ../../../eurusd_clean/scripts/session84/validate_predictions_vs_reality.py
Dataset : ../../../eurusd_clean/scripts/session99/real_impacts_TIMEZONE_FIX_FINAL.csv
Guide : GUIDE_TIMEZONE_DEFINITIF.md
```

### 🖥️ Je veux modifier le Planificateur
```
Problème : SESSION_110_ETAT_PROBLEME_ARCHITECTURAL.md
Code nouveau : ../../../fx_impact_app/src/cluster_impact_calculator.py
Code existant : ../../../fx_impact_app/streamlit_app/pages/6_Planificateur_V27_*.py
```

### 🚨 Je veux comprendre une erreur
```
Lire : PROJECT_STATE_NEW.md → Section "Erreurs Récurrentes"
    → ANTI_PATTERN_CRITIQUE.md
    → DATABASE_SCHEMAS.md (si erreur DB)
```

---

## 📋 CHECKLIST DÉMARRAGE SESSION

**OBLIGATOIRE au début de TOUTE session :**

- [ ] Lire `README.md` (ce fichier - 2 min)
- [ ] Lire `PROJECT_STATE_NEW.md` (état global - 15 min)
- [ ] Lire `MANDATORY_SESSION_RULES.md` (règles - 5 min)
- [ ] Lire rapport session précédente (10 min)
- [ ] Vérifier token budget (105k préférence André, 190k max)
- [ ] Résumer compréhension mission
- [ ] Obtenir confirmation GO utilisateur

**Si UNE case non cochée → NE PAS coder !**

---

## 🎯 AVANTAGES DE CETTE ORGANISATION

### Avant
```
❌ 300+ fichiers mélangés dans /docs/
❌ Chercher 10-15 min pour trouver le bon fichier
❌ Risque de lire fichiers obsolètes
❌ Chemins relatifs complexes (../../..)
```

### Après
```
✅ 20 fichiers ESSENTIELS dans __REFERENCE_CRITIQUE__/
✅ 280 fichiers HISTORIQUES dans /docs/ (recherches)
✅ Trouver fichier critique : < 1 min
✅ Chemins simples (même répertoire)
✅ Impossible de se tromper
```

---

## 💡 PHILOSOPHIE

> **"Si tu ne sais pas où commencer, commence par __REFERENCE_CRITIQUE__/README.md"**

**Principe :**
- **TOUT ce qui est critique** → Dans __REFERENCE_CRITIQUE__/
- **Historique/archives** → Reste dans /docs/ (accessible mais pas prioritaire)
- **Code source** → Reste dans fx_impact_app/src/ (où il doit être)
- **Base données** → Reste dans app/data/ (où elle doit être)

**Un seul endroit pour l'essentiel = Efficacité maximale** 🎯

---

## 📞 MAINTENANCE

### Quand ajouter un fichier ici
- Nouveau guide critique créé
- Nouvelle session majeure terminée
- Nouveau fichier règles/méthodologie

### Quand NE PAS ajouter
- Rapports sessions anciennes (< Session 100)
- Fichiers temporaires/brouillons
- Code source (reste dans src/)
- Données/résultats (reste dans scripts/)

### Règle d'or
> **Maximum 25-30 fichiers** dans __REFERENCE_CRITIQUE__/
> 
> Si plus → Archiver les moins critiques dans /docs/

---

## 🔗 STRUCTURE PROJET COMPLÈTE

```
eurusd_news_impact_calculator_MPC/
├── eurusd_clean/
│   ├── app/
│   │   └── data/
│   │       └── warehouse.duckdb              ⚠️ 205 MB (NE PAS TOUCHER)
│   ├── docs/
│   │   ├── __REFERENCE_CRITIQUE__/          ⭐⭐⭐ VOUS ÊTES ICI (20 fichiers)
│   │   └── (280+ fichiers historiques)      (pour recherches)
│   └── scripts/
│       └── sessionXXX/                      (scripts par session)
│
└── fx_impact_app/
    ├── src/
    │   ├── formulas_validated.py            ⭐⭐⭐ Formules S51-55
    │   └── cluster_impact_calculator.py     ⭐⭐⭐ Module S111
    └── streamlit_app/
        └── pages/
            └── 6_Planificateur_V27_*.py     ⭐⭐⭐ Interface
```

---

## 🎓 RÉSUMÉ ULTRA-RAPIDE (TL;DR)

**Pour démarrer une session :**
1. Ouvrir `__REFERENCE_CRITIQUE__/`
2. Lire `README.md` (2 min)
3. Lire `PROJECT_STATE_NEW.md` (15 min)
4. Lire `MANDATORY_SESSION_RULES.md` (5 min)
5. GO ! 🚀

**Tout est dans ce répertoire. Rien à chercher ailleurs.**

---

**Dernière mise à jour :** 04 novembre 2025 - Session 111  
**Version :** 2.0 (TOUS les fichiers critiques centralisés)  
**Maintenance :** Maintenir 20-30 fichiers max
