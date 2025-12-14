# 👋 BIENVENUE CLAUDE - SESSION 28

**Date :** À compléter  
**Budget tokens :** 190,000  
**Projet :** EUR/USD News Impact Calculator

---

## 🎯 CONTEXTE RAPIDE

Tu rejoins un projet de **prédiction d'impact des news économiques sur EUR/USD**.

André développe un système qui :
1. Charge événements économiques (CPI, NFP, etc.)
2. Calcule leur impact réel sur le prix EUR/USD
3. Prédit les mouvements futurs avec une formule

**Tu es en Session 28.** Session 27 a corrigé un problème majeur (forecast vs estimate).

---

## ⚡ DÉMARRAGE OBLIGATOIRE (15 MIN)

### 1️⃣ Lire IMMÉDIATEMENT et attentivement ces fichiers ( pas de lecture en oblique !)

**DANS CET ORDRE (critique) :**

```
1. KNOWLEDGE BASE/00_START_HERE.md                    (5 min)
2. KNOWLEDGE BASE/CRITIQUES/ERREURS_RECURRENTES.md    (3 min)
3. KNOWLEDGE BASE/CRITIQUES/TABLES_DATABASE.md        (2 min)
4. RAPPORTS SESSIONS/RAPPORT_SESSION27_FINAL.md       (5 min)
```

**⏱️ TOTAL : 15 minutes** qui évitent 3h d'erreurs !

### 2️⃣ Valider compréhension


Après lecture, réponds à André :

```
✅ J'ai lu les 4 fichiers obligatoires
✅ Je comprends l'erreur forecast/estimate (Erreur #7)
✅ Je sais que event_impacts_v2 contient 8,344 événements validés
✅ Je sais qu'il faut afficher les tokens régulièrement
✅ Prêt à commencer !
```

**Ne commence AUCUN code avant cette validation.**

---

## 🔥 SESSION 27 - CORRECTION MAJEURE

### Découverte critique

**André avait raison depuis le début :**
> "Les surprises sont calculées avec previous, pas forecast !"

**Problème identifié :**
- 99.98% des événements n'avaient PAS de forecast (11/58,449)
- EODHD API appelle ce champ `"estimate"` pas `"forecast"`
- Code importait mal → forecast = NULL
- Planificateur tombait en fallback sur `previous`
- **Résultat : surprises sous-estimées**

### Corrections appliquées ✅

1. ✅ Copié `estimate` → `forecast` (26,370 événements réparés)
2. ✅ Recalculé event_impacts_v2 (8,344 événements avec vraies surprises)
3. ✅ Validé 11 septembre (Inflation Rate MoM = 33.3%)
4. ✅ Documenté Erreur #7 dans ERREURS_RECURRENTES.md

**Impact :**
```
Événements utilisables :
AVANT : 11 (0.02%)
APRÈS : 26,370 (45.1%)
= ×2,397 fois plus !
```

---

## 💾 ÉTAT ACTUEL BASE DE DONNÉES

```
warehouse.duckdb (205 MB)
├── events (58,449)              ✅ forecast corrigé (45.1%)
├── event_families (747)         ✅ Mappings + scores empiriques
├── scores (991)                 ✅ Scores validés
├── prices_1m (1,114,260)        ✅ Dukascopy validé
└── event_impacts_v2 (8,344)     ✅ RECALCULÉ Session 27 ⭐
```

**Validation cas référence :**
- 11 septembre 2025, 14:30 UTC
- Inflation Rate MoM (US)
- Surprise : 33.3%
- ✅ Présent dans event_impacts_v2

---

## 🎯 MISSION SESSION 28

### Priorité 1 : Formule V4 (60-90 min)

**Objectif :** Créer formule prédictive basée sur 8,344 événements validés.

**Étapes :**
1. Analyser distribution surprises dans event_impacts_v2
2. Analyser scores empiriques dans event_families
3. Créer régression : `empirical_score × surprise → impact_pips`
4. Valider sur cas test
5. Implémenter dans module predictions.py

**Fichiers à créer :**
- `analyze_empirical_data_session28.py` (analyse)
- `create_formula_v4_session28.py` (formule)
- `KNOWLEDGE BASE/CRITIQUES/FORMULES_CALCUL.md` (mise à jour)

### Priorité 2 : event_groups_v2 (optionnel)

Si temps restant, créer table des groupes multi-événements.

**Fichier :** `create_event_groups_v2_session28.py`

---

## 🚨 RÈGLES CRITIQUES

### 1. Surprise UNIQUEMENT avec forecast

```python
# ✅ BON
surprise = abs((actual - forecast) / forecast) * 100

# ❌ MAUVAIS - Ne JAMAIS utiliser previous
if forecast is None:
    surprise = abs((actual - previous) / previous) * 100  # ❌ ERREUR #1
```

### 2. Vérifier forecast existe

```python
# Avant tout calcul
stats = con.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(forecast) as with_forecast
    FROM events
""").fetchone()

pct = stats[1] / stats[0] * 100
if pct < 40:
    raise ValueError(f"Seulement {pct:.1f}% ont forecast !")  # ❌ ERREUR #7
```

### 3. Timezone en UTC explicite

```python
# ✅ BON
event_time = pd.to_datetime('2025-09-11 14:30:00+02:00', utc=True)
event_time_utc = event_time.strftime('%Y-%m-%d %H:%M:%S')
query = f"... WHERE datetime >= '{event_time_utc}'::timestamp"

# ❌ MAUVAIS
query = f"... WHERE datetime = '2025-09-11 14:30:00+02:00'"  # ❌ ERREUR #2
```

### 4. Afficher tokens régulièrement

**Toutes les 10-15k tokens :**

```
📊 TOKENS UTILISÉS : X / 190,000 (XX%) - Reste Y tokens (XX%)
```

---

## 📋 CHECKLIST DÉMARRAGE

Avant d'écrire du code :

- [ ] Lu 00_START_HERE.md
- [ ] Lu ERREURS_RECURRENTES.md
- [ ] Lu TABLES_DATABASE.md
- [ ] Lu RAPPORT_SESSION27_FINAL.md
- [ ] Validé compréhension avec André
- [ ] Compris Erreur #7 (forecast vs estimate)
- [ ] Prêt à afficher tokens régulièrement

**Si UN élément manque → STOP et lire.**

---

## 🎓 LEÇONS SESSION 27

### 1. Toujours vérifier les hypothèses

Documentation disait "forecast existe" mais réalité : 99.98% NULL.

**Solution :** Audit avec comptage SQL systématique.

### 2. Faire confiance aux observations terrain

André avait signalé le problème. L'audit initial était incomplet.

**Solution :** Investiguer à fond quand utilisateur signale problème.

### 3. Nommer selon la réalité

EODHD appelle le champ `"estimate"` → code doit mapper correctement.

**Solution :** Toujours vérifier structure réelle API.

---

## 🔧 COMMANDES UTILES

### Vérifier état DB

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC
python3 -c "
import duckdb
con = duckdb.connect('fx_impact_app/data/warehouse.duckdb')
print('event_impacts_v2:', con.execute('SELECT COUNT(*) FROM event_impacts_v2').fetchone()[0])
print('forecast %:', con.execute('SELECT ROUND(100.0*COUNT(forecast)/COUNT(*),1) FROM events').fetchone()[0])
con.close()
"
```

### Valider cas référence

```bash
python3 -c "
import duckdb
con = duckdb.connect('fx_impact_app/data/warehouse.duckdb')
sept11 = con.execute('''
    SELECT event_key, surprise_pct 
    FROM event_impacts_v2 
    WHERE ts_utc::DATE = '2025-09-11'
    AND country = 'US'
    ORDER BY surprise_pct DESC LIMIT 1
''').fetchone()
print(f'11 sept US: {sept11[0]} = {sept11[1]:.1f}% surprise')
assert sept11[1] > 30, 'Erreur validation'
print('✅ Validation OK')
con.close()
"
```

---

## 💬 MESSAGE D'ANDRÉ

André compte sur toi pour :

1. ✅ **Lire la documentation** avant de coder
2. ✅ **Respecter les erreurs récurrentes** (surtout #1, #7)
3. ✅ **Afficher les tokens régulièrement**
4. ✅ **Valider les hypothèses** avec SQL
5. ✅ **Créer une formule V4** solide basée sur données empiriques

**Session 27 a été un succès parce qu'on a écouté André.**  
**Session 28 sera un succès si tu suis les garde-fous.**

---

## 🚀 COMMENCER

**Première action :**

Lis les 4 fichiers obligatoires (15 min), puis réponds à André :

```
✅ Documentation lue
✅ Prêt pour Formule V4
✅ Tokens seront affichés régulièrement

Quelle est ta priorité : Formule V4 ou event_groups_v2 ?
```

Message d'André: a ce point de la situation et du développement je me pose la question si on ne doit pas éclaircir ce que l'on na pu télécharger et valider je parle des données de bases eodhd Dukascopy, événements calendrier previous pas forecast mais estimates, actual ou réel etc.... , faire le point sur ce dont on dispose lister les fichiers utilisés dans le fonctionnement de l'app streamlit, vérifier comment atteindre les objectifs, vérifier la méthodologie de calcul, et utiliser les fichiers actuels et validés pour démarrer sur un nouveau programme streamlit qui utiliserait les fonction fonctionnelles de notre développement les fichiers validés mais sur de nouvelles bases après validation de la méthodologie de calcul et l'approche mathématique et statistique et probabilités. 

On a un event clé du 11.09.2025 qui nous sert de référence mais on arrive pas jusqu'à présent à prédire à postériori avec ce qu'on a mis au point les mouvements réels. Il est vrai que ce n'est que très récemment qu'on a mis le doigt sur les erreurs de données de base essentielles, ce qui faussait tout nos calculs. Ce que je constate c'est qu'on multiplie les erreurs de tables d'appels de timeline etc.... Et j'ai l'impression qu'on tourne en rond. J'aimerais avoir une réflexion approfondie sur le sujet pour savoir si on continue le développement actuel ou s'il est préférable de redémarrer un nouveau projet mais avec les connaissances acquises.



---

**BON COURAGE CLAUDE ! 🎯**

**Budget :** 190,000 tokens  
**Objectif :** Formule V4 + documentation  
**Durée estimée :** 2-3h

**Tu as tout ce qu'il faut pour réussir. Let's go ! 🚀**
