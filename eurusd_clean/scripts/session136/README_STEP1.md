# ÉTAPE 1 - SCAN PRICE MOVEMENTS
## Session 136 - Workflow LOO-CV DoubleWave_Overlap

**Date :** 14 novembre 2025  
**Auteur :** André Valentin avec Claude

---

## 🎯 OBJECTIF

Scanner `prices_bern` pour identifier tous les mouvements forts (≥40 pips) sur la période 2023-2025, **sans référence aux événements**.

Conforme au workflow exact `doublewave_loo_validation.mermaid`.

---

## 📋 FICHIERS

### **Scripts**
- `step1_scan_price_movements.py` : Script principal de scan
- `test_step1_scan_price_movements.py` : Tests de validation

### **Output**
- `step1_price_movements.csv` : Résultats du scan

---

## 🚀 UTILISATION

### **1. Exécuter le scan**

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session136

python step1_scan_price_movements.py
```

**Durée estimée :** 2-5 minutes (selon taille DB)

**Output attendu :**
```
================================================================================
ÉTAPE 1 : SCANNER MOUVEMENTS FORTS DANS PRICES_BERN
Session 136 - Workflow LOO-CV
================================================================================

📂 Connexion base de données...
   Chemin : .../warehouse.duckdb
   ✅ Table prices_bern trouvée

1️⃣ SCAN PRIX
   Période : 2023-01-01 00:00:00 → 2025-12-31 23:59:59
   Critère : Impact ≥ 40.0 pips
   Espacement minimum : 2h entre mouvements

📊 Chargement prix 2023-01-01 00:00:00 → 2025-12-31 23:59:59...
   ✅ 1,234,567 bougies chargées
   Première bougie : 2023-01-01 00:00:00+01:00
   Dernière bougie : 2025-12-31 23:59:00+01:00

🔍 Scanning mouvements ≥40.0 pips...
   Fenêtre observation: 60 min
   Baseline lookback: 10 min
   Progression: 25.0% (250,000/1,000,000) - 45 mouvements trouvés
   Progression: 50.0% (500,000/1,000,000) - 89 mouvements trouvés
   ...
   ✅ 127 mouvements ≥40.0 pips trouvés

2️⃣ STATISTIQUES
   Total mouvements : 127
   Impact moyen     : 58.3 pips
   Impact médian    : 52.1 pips
   Impact min       : 40.0 pips
   Impact max       : 156.8 pips
   Direction UP     : 64 (50.4%)
   Direction DOWN   : 63 (49.6%)

3️⃣ SAUVEGARDE
   💾 Fichier : .../step1_price_movements.csv
   📊 Lignes : 127

4️⃣ ÉCHANTILLON (10 premiers mouvements)
   Date/Heure           Impact  Direction  Peak (min)
   -------------------- ---------- ---------- ------------
   2023-01-12 14:30         56.2         UP         12.3
   2023-02-14 14:30         48.7         UP         18.5
   ...

✅ ÉTAPE 1 TERMINÉE
   Fichier prêt pour ÉTAPE 2 (matching clusters)

5️⃣ VALIDATION AUTOMATIQUE
   ✅ N≥10 mouvements → Objectif atteint !
```

---

### **2. Exécuter les tests**

```bash
python test_step1_scan_price_movements.py
```

**Output attendu :**
```
================================================================================
VALIDATION COMPLÈTE ÉTAPE 1 - SCAN PRICE MOVEMENTS
Session 136 - Tests rigoureux
================================================================================

================================================================================
TEST 1.1 : FICHIER OUTPUT EXISTE
================================================================================
✅ SUCCÈS : Fichier trouvé
   Chemin : .../step1_price_movements.csv

================================================================================
TEST 1.2 : STRUCTURE CSV CORRECTE
================================================================================
✅ SUCCÈS : Toutes les colonnes présentes
   Colonnes : ['datetime', 'impact_pips', 'direction', 'baseline_price', 'peak_price', 'peak_time', 'minutes_to_peak']
   Lignes : 127

[... autres tests ...]

================================================================================
RÉSUMÉ TESTS ÉTAPE 1
================================================================================
   ✅ SUCCÈS : 1.1 - Fichier output existe
   ✅ SUCCÈS : 1.2 - Structure CSV correcte
   ✅ SUCCÈS : 1.3 - Types données corrects
   ✅ SUCCÈS : 1.4 - Valeurs cohérentes
   ✅ SUCCÈS : 1.5 - Pas de doublons temporels
   ✅ SUCCÈS : 1.6 - Cas référence 11.09.2025
   ✅ SUCCÈS : 1.7 - Statistiques attendues

   Total : 7/7 tests passés

🎉 TOUS LES TESTS PASSENT - ÉTAPE 1 VALIDÉE
   Vous pouvez procéder à ÉTAPE 2 (matching clusters)
```

---

## 📊 FORMAT OUTPUT

**Fichier :** `step1_price_movements.csv`

**Colonnes :**
- `datetime` : Début du mouvement (ISO format string)
- `impact_pips` : Ampleur du mouvement en pips (float)
- `direction` : Direction (`'UP'` ou `'DOWN'`)
- `baseline_price` : Prix de référence (moyenne 10 min avant)
- `peak_price` : Prix au pic (max high pour UP, min low pour DOWN)
- `peak_time` : Datetime du pic (ISO format string)
- `minutes_to_peak` : Durée jusqu'au pic en minutes (float)

**Exemple :**
```csv
datetime,impact_pips,direction,baseline_price,peak_price,peak_time,minutes_to_peak
2025-09-11 14:30:00+02:00,56.2,UP,1.1045,1.1107,2025-09-11 14:42:00+02:00,12.0
2025-09-18 14:30:00+02:00,48.7,UP,1.1123,1.1172,2025-09-18 14:48:00+02:00,18.0
```

---

## ⚙️ PARAMÈTRES AJUSTABLES

**Dans `step1_scan_price_movements.py` :**

```python
# Période scan
PERIOD_START = "2023-01-01 00:00:00"  # Début
PERIOD_END = "2025-12-31 23:59:59"    # Fin

# Critères mouvements
MIN_IMPACT_PIPS = 40.0                # Impact minimum (pips)
WINDOW_MINUTES = 60                   # Fenêtre observation peak
BASELINE_LOOKBACK = 10                # Minutes pour baseline
MIN_HOURS_BETWEEN_MOVEMENTS = 2       # Espacement minimum
```

**Si trop peu de mouvements :**
- Réduire `MIN_IMPACT_PIPS` (ex: 30 pips)
- Réduire `MIN_HOURS_BETWEEN_MOVEMENTS` (ex: 1h)
- Étendre `PERIOD_START` (ex: 2022 ou 2021)

**Si trop de mouvements :**
- Augmenter `MIN_IMPACT_PIPS` (ex: 50 pips)
- Augmenter `MIN_HOURS_BETWEEN_MOVEMENTS` (ex: 3h)

---

## ✅ CRITÈRES VALIDATION

### **Automatiques (tests)**
- ✅ Fichier CSV généré
- ✅ Structure conforme (7 colonnes)
- ✅ Types corrects (float, string, datetime)
- ✅ Valeurs cohérentes (impact ≥40, peak_time > datetime)
- ✅ Pas de doublons (<2h entre mouvements)
- ✅ Cas référence 11.09.2025 détecté
- ✅ Statistiques raisonnables

### **Manuels**
- ✅ N≥10 mouvements (optimal pour LOO-CV)
- ✅ N≥3 mouvements (minimum pour workflow)
- ✅ Distribution directions équilibrée (~40-60%)

---

## 🔍 ANALYSE RÉSULTATS

### **Vérifier distribution temporelle**

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('step1_price_movements.csv')
df['datetime'] = pd.to_datetime(df['datetime'])

# Distribution par année
df['year'] = df['datetime'].dt.year
print(df['year'].value_counts().sort_index())

# Distribution par mois
df['month'] = df['datetime'].dt.month
print(df['month'].value_counts().sort_index())
```

### **Visualiser impacts**

```python
# Histogramme impacts
plt.figure(figsize=(10, 6))
plt.hist(df['impact_pips'], bins=20, edgecolor='black')
plt.xlabel('Impact (pips)')
plt.ylabel('Fréquence')
plt.title('Distribution Impacts Mouvements')
plt.savefig('step1_impact_distribution.png')
```

---

## ⚠️ PROBLÈMES CONNUS

### **1. Aucun mouvement trouvé**

**Cause :** Critères trop stricts ou période sans données

**Solution :**
1. Vérifier table `prices_bern` contient données 2023-2025
2. Réduire `MIN_IMPACT_PIPS` à 30 pips
3. Vérifier timezone prix (doit être Europe/Zurich)

### **2. Trop de mouvements (>500)**

**Cause :** Critères trop permissifs ou bruit marché

**Solution :**
1. Augmenter `MIN_IMPACT_PIPS` à 50 pips
2. Augmenter `MIN_HOURS_BETWEEN_MOVEMENTS` à 3-4h
3. Vérifier pas de gaps/erreurs dans prix

### **3. Cas référence 11.09.2025 non détecté**

**Cause :** Dates prix décalées ou mouvement < 40 pips

**Solution :**
1. Vérifier table `prices_bern` contient 11.09.2025
2. Réduire temporairement `MIN_IMPACT_PIPS` pour debug
3. Vérifier timezone +02:00 (Bern)

---

## 📋 PROCHAINES ÉTAPES

**Si tests passent :**

1. ✅ Procéder à **ÉTAPE 2** : `step2_match_clusters.py`
   - Matcher mouvements → événements clusters
   - Définir signatures clusters

2. Lire `step1_price_movements.csv` comme input

**Si tests échouent :**

1. ❌ Analyser logs tests
2. Ajuster paramètres `step1_scan_price_movements.py`
3. Ré-exécuter scan + tests
4. Ne PAS passer à ÉTAPE 2 avant validation complète

---

## 📊 MÉTRIQUES SESSION 136

**Tokens utilisés :** ~76k / 190k (40%)

**Fichiers créés :**
- `step1_scan_price_movements.py` (239 lignes)
- `test_step1_scan_price_movements.py` (445 lignes)
- `README_STEP1.md` (ce fichier)

**Durée implémentation :** ~15 min

---

**Statut :** ✅ ÉTAPE 1 IMPLÉMENTÉE - EN ATTENTE EXÉCUTION ET VALIDATION
