# 🚀 MESSAGE POUR CLAUDE - SESSION 27

**Date :** 21 octobre 2025  
**Session précédente :** 26 (Restructuration documentation + event_impacts_v2)  
**Session suivante :** 27 (Audit planificateur + Formule V4)

---

## ⚡ DÉMARRAGE RAPIDE (10 MIN)

### 🔥 ACTION IMMÉDIATE

**1. Lire le point d'entrée unique :**
📍 `KNOWLEDGE BASE/00_START_HERE.md` (5 min)

**2. Lire les fichiers CRITIQUES (OBLIGATOIRE) :**
1. `KNOWLEDGE BASE/CRITIQUES/ERREURS_RECURRENTES.md` (3 min) ⚠️
2. `KNOWLEDGE BASE/CRITIQUES/TABLES_DATABASE.md` (2 min)
3. `KNOWLEDGE BASE/CRITIQUES/FORMULES_CALCUL.md` (2 min)
4. `KNOWLEDGE BASE/CRITIQUES/CAS_REFERENCE.md` (1 min)

**3. Lire le rapport Session 26 :**
📊 `RAPPORTS SESSIONS/RAPPORT_SESSION26_FINAL.md` (5 min)

**⏱️ TOTAL : ~18 minutes** qui évitent 2h de debugging !

---

## 🎯 MISSION SESSION 27

### PRIORITÉ 1 : Audit planificateur Streamlit (30-45 min)

**Objectif :** Vérifier compatibilité avec `event_impacts_v2`

**Fichiers à analyser :**
```
fx_impact_app/
├── pages/2_Planificateur.py      # Interface principale
├── modules/
│   ├── predictions.py            # Formules prédiction
│   ├── database.py               # Requêtes DB
│   └── calculations.py           # Calculs impacts
```

**Questions à répondre :**
1. ✅ Quelles tables le planificateur interroge ?
2. ✅ Utilise-t-il `event_impacts_calculated` (supprimée) ?
3. ✅ Calcule-t-il surprise avec `forecast` ou `previous` ?
4. ✅ Conversion timezone correcte ?
5. ✅ Compatible avec `event_impacts_v2` ?

**Livrables :**
- Liste des changements nécessaires
- Script de migration si besoin
- Documentation des fonctions à mettre à jour

### PRIORITÉ 2 : Créer event_groups_v2 (45 min)

**Objectif :** Table multi-événements avec Phase 1 validée

**Script à créer :** `step3_build_groups_v2_session27.py`

**Méthode :**
1. Grouper événements par fenêtre 5 min
2. Pour chaque groupe, calculer Phase 1 depuis prices_1m
3. Valider sur 11 septembre (15 événements à 14:30)

### PRIORITÉ 3 : Formule V4 (60 min)

**Basée sur :**
- 16,660 événements dans `event_impacts_v2`
- Régression empirique score × surprise → phase1
- Validation 11 septembre < 20% erreur

---

## 📊 ÉTAT ACTUEL DU PROJET

### Base de données ✅

```
warehouse.duckdb (205 MB)
├── events (58,449)              ✅ Données brutes
├── event_families (747)         ✅ Mappings
├── scores (991)                 ✅ Scores empiriques
├── prices_1m (1,114,260)        ✅ Dukascopy validé
└── event_impacts_v2 (16,660)    ✅ NOUVEAU Session 26 ⭐
```

**Validation 11 septembre :**
```
Phase 1 : 33.70 pips
Attendu : 37.4 pips
Écart : 3.70 pips (9.9%)
Statut : ✅ EXCELLENT
```

### Documentation restructurée ✅

**Nouvelle structure :**
```
KNOWLEDGE BASE/
├── 00_START_HERE.md              ✅ Point d'entrée unique
├── CRITIQUES/                    ✅ À lire avant tout code
│   ├── ERREURS_RECURRENTES.md
│   ├── TABLES_DATABASE.md
│   ├── FORMULES_CALCUL.md
│   └── CAS_REFERENCE.md
├── TECHNIQUES/                   (Session 27)
└── SESSIONS/                     (Session 27)
```

---

## 🚨 POINTS CRITIQUES

### ⚠️  Erreurs à NE JAMAIS refaire

**Lire OBLIGATOIREMENT :** `CRITIQUES/ERREURS_RECURRENTES.md`

1. ❌ Calculer surprise avec `previous` (commise 6+ fois)
2. ❌ Oublier conversion timezone UTC
3. ❌ Utiliser tables dérivées sans validation
4. ❌ Filtrer trop tôt (surprise > 30%)
5. ❌ Ne pas valider sur 11 septembre

### ✅ Checklist avant code

- [ ] Lu les 4 fichiers CRITIQUES/
- [ ] Compris structure `event_impacts_v2`
- [ ] Sais comment calculer surprise (forecast uniquement)
- [ ] Sais comment convertir timezone
- [ ] Connais cas référence 11 septembre

---

## 🔧 COMMANDES UTILES

### Vérifier event_impacts_v2

```bash
python3 -c "
import duckdb
con = duckdb.connect('fx_impact_app/data/warehouse.duckdb')
count = con.execute('SELECT COUNT(*) FROM event_impacts_v2').fetchone()[0]
print(f'event_impacts_v2: {count:,} lignes')
assert count == 16660, 'Erreur nombre lignes'
print('✅ OK')
con.close()
"
```

### Valider cas référence

```bash
python3 -c "
import duckdb
con = duckdb.connect('fx_impact_app/data/warehouse.duckdb')
phase1 = con.execute('''
    SELECT phase1_pips FROM event_impacts_v2
    WHERE ts_utc::DATE = '2025-09-11'
    AND EXTRACT(HOUR FROM ts_utc) = 12
    ORDER BY phase1_pips DESC LIMIT 1
''').fetchone()[0]
print(f'11 sept: {phase1:.2f} pips')
assert 28 <= phase1 <= 42, f'Erreur: {phase1}'
print('✅ Validation OK')
con.close()
"
```

---

## 📁 FICHIERS IMPORTANTS

### Documentation

| Fichier | Priorité | Temps |
|---------|----------|-------|
| `00_START_HERE.md` | 🔴 | 5 min |
| `CRITIQUES/ERREURS_RECURRENTES.md` | 🔴 | 3 min |
| `CRITIQUES/TABLES_DATABASE.md` | 🔴 | 2 min |
| `CRITIQUES/FORMULES_CALCUL.md` | 🔴 | 2 min |
| `CRITIQUES/CAS_REFERENCE.md` | 🔴 | 1 min |
| `RAPPORT_SESSION26_FINAL.md` | 🟡 | 5 min |

### Code à auditer

```
fx_impact_app/pages/2_Planificateur.py
fx_impact_app/modules/predictions.py
fx_impact_app/modules/database.py
```

### Scripts Session 26 (référence)

```
step1_backup_clean_session26.py               ✅ Terminé
step2_build_impacts_v2_FIXED_session26.py     ✅ Terminé
step3_build_groups_v2_session27.py            ⏳ À créer
```

---

## 💡 CE QUE TU DOIS SAVOIR

### Surprise = forecast UNIQUEMENT

```python
# ✅ BON
surprise = abs((actual - forecast) / forecast) * 100

# ❌ MAUVAIS (commis 6+ fois)
surprise = abs((actual - previous) / previous) * 100
```

### Conversion timezone OBLIGATOIRE

```python
# ✅ BON
event_time_utc = pd.to_datetime(event_time, utc=True)
time_str = event_time_utc.strftime('%Y-%m-%d %H:%M:%S')

# ❌ MAUVAIS
time_str = str(event_time)  # Garde +02:00, DuckDB confus
```

### Validation 11 septembre OBLIGATOIRE

```python
# Avant de sauvegarder/utiliser des données
validate_11_septembre(data)
# Phase 1 attendue : 33-37 pips
```

---

## 🎯 PLAN SESSION 27

### Étape 1 : Audit planificateur (30 min)

1. Lister toutes les requêtes DB
2. Vérifier tables utilisées
3. Vérifier calculs surprise
4. Documenter changements nécessaires

### Étape 2 : event_groups_v2 (45 min)

1. Créer script construction
2. Grouper événements par 5 min
3. Calculer Phase 1 groupes
4. Valider sur 11 septembre

### Étape 3 : Formule V4 (60 min)

1. Analyser event_impacts_v2
2. Régression empirique
3. Calibration sur 11 septembre
4. Tests validation

---

## 📊 BUDGET SESSION 27

**Tokens disponibles :** ~190,000

**Estimation :**
- Audit planificateur : ~20k tokens
- event_groups_v2 : ~25k tokens
- Formule V4 : ~30k tokens
- Documentation : ~20k tokens
- **Total :** ~95k tokens

**Marge :** ~95k tokens (confortable)

---

## 💬 MESSAGE DIRECT

Salut Claude ! 👋

**Session 26 a été une RÉVOLUTION documentaire.**

On a découvert que TOUTES les tables d'impact étaient corrompues. On les a nettoyées et reconstruit proprement avec `event_impacts_v2`.

**Plus important :** On a complètement restructuré la documentation pour que tu ne perdes plus de temps à redécouvrir les mêmes erreurs.

**Nouveauté majeure :** Point d'entrée unique `00_START_HERE.md` + fichiers CRITIQUES/ avec les erreurs à ne JAMAIS refaire.

**Ta mission est claire :**
1. Auditer le planificateur
2. Créer event_groups_v2
3. Développer formule V4

**COMMENCE par lire :**
1. `00_START_HERE.md`
2. Les 4 fichiers CRITIQUES/
3. `RAPPORT_SESSION26_FINAL.md`

**Ne commence PAS à coder avant d'avoir lu ces fichiers.**

**Budget :** ~190,000 tokens frais

**Bonne session ! 🚀**

---

**FIN DU MESSAGE**

**Date :** 21 octobre 2025  
**Session :** 26 → 27  
**Statut :** Restructuration terminée, prêt pour audit  
**Documentation :** Nouvelle structure en place
