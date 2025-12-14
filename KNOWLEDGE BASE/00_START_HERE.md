# 🚀 START HERE - EUR/USD News Impact Calculator

**Point d'entrée unique** | **À lire en PREMIER** à chaque session

**Dernière mise à jour :** 21 octobre 2025 - Session 27  
**État projet :** ✅ event_impacts_v2 validé avec forecast corrigé (8,344 événements)  
**Prochaine étape :** Documenter Session 27 + Formule V4

---

## ⚡ DÉMARRAGE RAPIDE (5 MIN)

### 1️⃣ Lire les fichiers CRITIQUES (OBLIGATOIRE)

Ces fichiers contiennent l'info **certifiée** qui évite de refaire les mêmes erreurs :

| Fichier | Temps | Pourquoi |
|---------|-------|----------|
| [ERREURS_RECURRENTES.md](CRITIQUES/ERREURS_RECURRENTES.md) | 3 min | ⚠️  Éviter erreurs commises 6+ fois |
| [TABLES_DATABASE.md](CRITIQUES/TABLES_DATABASE.md) | 2 min | 📊 Structure DB certifiée |
| [FORMULES_CALCUL.md](CRITIQUES/FORMULES_CALCUL.md) | 2 min | 📐 Formules validées |
| [CAS_REFERENCE.md](CRITIQUES/CAS_REFERENCE.md) | 1 min | ✅ Validation obligatoire |

**⏱️ TOTAL : ~8 minutes** qui évitent 2h de debugging !

### 2️⃣ Lire la session actuelle

📅 [SESSION_27.md](SESSIONS/SESSION_27.md) - Session en cours

---

## 📚 DOCUMENTATION PAR THÈME

### 🔴 CRITIQUES (lire avant tout code)

```
KNOWLEDGE BASE/CRITIQUES/
├── ERREURS_RECURRENTES.md    ⚠️  Erreurs à ne JAMAIS refaire
├── TABLES_DATABASE.md         📊 Structure DB (certifiée)
├── FORMULES_CALCUL.md         📐 Formules validées
└── CAS_REFERENCE.md           ✅ Validation obligatoire
```

### 🟡 TECHNIQUES (lire si besoin)

```
KNOWLEDGE BASE/TECHNIQUES/
├── ARCHITECTURE_SYSTEME.md    🏗️  Vue d'ensemble
├── TIMEZONE_CONVERSION.md     🕐 Gestion fuseaux horaires
├── WORKFLOWS_STANDARD.md      🔄 Procédures standard
└── SOURCES_DONNEES.md         📥 APIs et imports
```

### 🟢 SESSIONS (historique)

```
KNOWLEDGE BASE/SESSIONS/
├── SESSION_27.md              📅 Session actuelle
├── SESSION_26.md              
└── SESSION_25.md              
```

---

## 🎯 ÉTAT ACTUEL DU PROJET

### Base de données ✅

```
warehouse.duckdb (205 MB)
├── events (58,449)              ✅ Données brutes + forecast corrigé
├── event_families (747)         ✅ Mappings validés
├── scores (991)                 ✅ Scores validés
├── prices_1m (1,114,260)        ✅ Dukascopy validé Session 25/26
└── event_impacts_v2 (8,344)     ✅ RECALCULÉ Session 27 avec forecast ⭐
```

**Backup :** `warehouse_BACKUP_SESSION26_before_clean.duckdb`

### Application Streamlit ✅

```
fx_impact_app/
├── app.py                       ✅ Fonctionne
├── modules/
│   ├── database.py              ✅ Compatible
│   ├── predictions.py           ⚠️  Formule V2 → migrer vers V4
│   └── calculations.py          ✅ OK
└── pages/
    ├── 1_Calendrier.py          ✅ OK
    └── 2_Planificateur.py       ✅ Audité Session 27
```

---

## 🚨 DÉCOUVERTES SESSION 27

### ✅ RÉSOLU

1. ✅ **Forecast vs Estimate** : EODHD utilise `estimate` pas `forecast`
2. ✅ **26,370 événements réparés** : estimate → forecast
3. ✅ **Planificateur audité** : Compatible avec nouvelles données
4. ✅ **event_impacts_v2 recalculé** : 8,344 événements (surprise > 30% vraie)
5. ✅ **11 septembre validé** : Inflation Rate MoM = 33.3% surprise

### 🎯 PROCHAINES ÉTAPES

1. Documenter Session 27 complètement
2. Créer formule V4 basée sur données empiriques
3. Créer event_groups_v2 (multi-événements)

---

## 🔧 COMMANDES RAPIDES

### Vérifier état base de données

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC
python3 -c "
import duckdb
con = duckdb.connect('fx_impact_app/data/warehouse.duckdb')
print('Tables:', con.execute('SHOW TABLES').df()['name'].tolist())
print('event_impacts_v2:', con.execute('SELECT COUNT(*) FROM event_impacts_v2').fetchone()[0])
con.close()
"
```

### Valider forecast correction

```bash
python3 -c "
import duckdb
con = duckdb.connect('fx_impact_app/data/warehouse.duckdb')
stats = con.execute('''
    SELECT 
        COUNT(*) as total,
        COUNT(forecast) as with_forecast,
        ROUND(100.0 * COUNT(forecast) / COUNT(*), 1) as pct
    FROM events
''').fetchone()
print(f'Forecast: {stats[1]:,}/{stats[0]:,} ({stats[2]}%)')
con.close()
"
```

### Lancer application

```bash
cd fx_impact_app
streamlit run app.py
```

---

## 📋 CHECKLIST DÉMARRAGE SESSION

Avant d'écrire du code :

- [ ] Lu `ERREURS_RECURRENTES.md`
- [ ] Lu `TABLES_DATABASE.md`
- [ ] Lu `FORMULES_CALCUL.md`
- [ ] Vérifié cas référence 11 septembre
- [ ] Compris état actuel (SESSION_XX.md)
- [ ] Backup DB si modifications prévues

**Si UN élément manque → STOP et lire.**

---

## 🤖 POUR CLAUDE (Assistant IA)

### Au démarrage

1. Lire ce fichier en entier
2. Lire les 4 fichiers CRITIQUES/
3. Lire SESSION_actuelle.md
4. Valider compréhension avec André

### Pendant la session

- **📊 AFFICHER TOKENS RÉGULIÈREMENT** : Indiquer tokens utilisés/restants toutes les 10-15k tokens
- Mettre à jour ce fichier si découverte majeure
- Ajouter erreur dans ERREURS_RECURRENTES.md si récurrente
- Documenter changements DB dans TABLES_DATABASE.md

### Format affichage tokens

```
📊 TOKENS UTILISÉS : X / 190,000 (XX%) - Reste Y tokens (XX%)
```

### Checkpoint automatique (115k tokens)

```markdown
## [TIMESTAMP] - Checkpoint automatique

**Tokens utilisés :** 115,000 / 190,000 (60.5%)

**État :**
- [Liste actions effectuées]
- [Actions en cours]
- [Prochaines étapes]

**Fichiers mis à jour :**
- [Liste]

**Prochaine session :**
- [Actions à reprendre]
```

### En fin de session

1. Créer rapport SESSION_XX.md
2. Mettre à jour état projet dans ce fichier
3. Archiver si nécessaire

---

## 📞 CONTACT

**Développeur :** André  
**Assistant IA :** Claude (Anthropic)  
**Projet :** EUR/USD News Impact Calculator  
**Objectif :** Prédire impact événements économiques sur EUR/USD

---

## 🔄 HISTORIQUE MISES À JOUR

| Date | Session | Changement |
|------|---------|------------|
| 21 oct 2025 | 27 | Correction forecast/estimate + audit planificateur |
| 21 oct 2025 | 26 | Création structure documentation + event_impacts_v2 |
| 20 oct 2025 | 25 | Validation Dukascopy + correction timezone |

---

**📌 RAPPEL : Ce fichier est le POINT D'ENTRÉE UNIQUE.**

Si tu ne sais pas par où commencer → C'est ici.  
Si tu as un doute → Relis les fichiers CRITIQUES/.  
Si tu découvres une erreur récurrente → Ajoute-la dans ERREURS_RECURRENTES.md.

**Bonne session ! 🚀**
