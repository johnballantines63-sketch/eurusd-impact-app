# 📁 SESSION 92.8 - DIRECTION_SENTIMENT 24H + TIMEZONE

**Dates :** Sessions 92.5-92.10 (25-29 octobre 2025)  
**Objectif :** Améliorer prédictions impact avec analyse contexte marché 24h avant événement

---

## 🎯 OBJECTIF GÉNÉRAL

**Formule actuelle V2 (Session 92.7) :**
```python
Impact = Base_Impact × direction_factor × 0.758
```
- MAE : 7.0 pips (4 dates CPI)
- Amélioration baseline : +50%

**Formule proposée Combined (Sessions 92.8-92.10) :**
```python
Impact = Base_Impact × combined_factor × 0.758
combined_factor = direction_factor × (1 + direction_sentiment × 0.1)
```
- direction_factor : Surprise nette (V2)
- direction_sentiment : Contexte marché 24h (-1 à +1)

**Hypothèse :** Ajouter contexte marché améliore précision

---

## 📊 HISTORIQUE SESSIONS

### Session 92.5 : Validation Données Dukascopy
- Comparaison MT5 vs Dukascopy (identiques)
- Validation timezone : events et prices = +02:00
- Cas référence 11.09.2025 établi

### Session 92.6 : Calibration Amplifications
- Test amplifications 2.0-3.0 par pas 0.1
- Résultat : 2.5 optimal (MAE 9.6 pips)

### Session 92.7 : Surprise Nette (V2)
- Formule direction_factor selon surprise
- MAE : 7.0 pips (4 dates CPI) ✅
- Amélioration +27% vs amplification fixe

### Session 92.8 : Direction_sentiment (Échec Logique)
- Tentative distance pic = direction tendance
- MAE : 10.1 pips ❌
- Erreur logique identifiée

### Session 92.9 : Correction Logique (Échec Timezone)
- Fonction `determine_trend_from_peak()` correcte
- Erreur timezone : timestamps +2h décalés
- MAE : 9.7 pips ❌

### Session 92.10 : Corrections Timezone (PRÊT)
- Règle timezone appliquée correctement
- Module `direction_sentiment_24h_FIXED_TIMEZONE.py`
- Scripts tests complets créés
- **EN ATTENTE EXÉCUTION**

---

## 📁 FICHIERS PRINCIPAUX

### Modules Core

**`direction_sentiment_24h_FIXED_TIMEZONE.py`** (480 lignes) ✅
- Fonction `load_prices_24h_before()` - Timestamps corrects
- Fonction `find_last_absolute_peak()` - Identifie pic HIGH/LOW 24h
- Fonction `calculate_24h_indicators()` - Momentum, volatilité, position
- Fonction `determine_trend_from_peak()` - BAISSIER/HAUSSIER/NEUTRE
- Fonction `calculate_direction_sentiment()` - Score -1 à +1
- Fonction `calculate_combined_factor()` - Combine surprise + sentiment

**Fichier backup :**
- `direction_sentiment_24h.py.backup_session92.9_avant_correction`

---

### Scripts Tests

**`execute_test_FIXED_TIMEZONE.py`** (330 lignes) ✅ **PRINCIPAL**
- Teste 4 dates CPI (09-11, 01-15, 05-13, 07-15)
- Calcule Baseline, V2, Combined pour chaque date
- Génère CSV complet avec 19 colonnes
- Affiche métriques MAE + régressions
- Verdict automatique avec décision

**Commande :**
```bash
python3 execute_test_FIXED_TIMEZONE.py
```

**Output :**
- Console : Analyse détaillée chaque date
- CSV : `resultats_combined_FIXED_TIMEZONE.csv`

---

**`analyze_results_auto.py`** (350 lignes) ✅
- Analyse automatique CSV généré
- Métriques détaillées par date
- Comparaisons MAE
- Détection logique inversée
- Recommandations

**Commande :**
```bash
python3 analyze_results_auto.py
```

**Requis :** CSV `resultats_combined_FIXED_TIMEZONE.csv` déjà généré

---

**`test_formule_INVERSE.py`** (400 lignes) ✅
- Test formule inversée si Combined échoue
- `combined = direction_factor × (1 - sentiment × 0.1)`
- Même 4 dates CPI
- Génère CSV séparé

**Commande :**
```bash
# À utiliser UNIQUEMENT si Combined échoue
python3 test_formule_INVERSE.py
```

**Output :**
- Console : Analyse inversée
- CSV : `resultats_combined_INVERSE.csv`

---

### Scripts Validation (Legacy)

**Fichiers Session 92.9 (timestamps faux) :**
- `execute_test_complet.py.backup_session92.9_avant_correction`
- `direction_sentiment_24h.py.backup_session92.9_avant_correction`

**Fichiers Session 92.5 (référence timezone) :**
- `replicate_session92.5_CORRECT.py` - Query SQL correcte
- `replication_session92.5_CORRECT.csv` - 71 lignes référence

---

## 🔬 MÉTHODOLOGIE

### Analyse 24h Avant Événement

**Principe :**
```
T-24h → T0 (événement)
    ↓
Identifier pic absolu (HIGH ou LOW)
    ↓
Analyser tendance depuis pic
    ↓
Calculer direction_sentiment
    ↓
Combiner avec surprise nette
```

**Exemple concret 11.09.2025 :**
```
10.09 17h08 : PIC HIGH à 1.17289
    ↓ BAISSE 21 HEURES ↓
11.09 14h30 : Prix 1.16880 (-40.9 pips)
    ↓
Marché BAISSIER détecté
    ↓
Direction_sentiment = -0.4
    ↓
CPI surprise +33.6% (positive)
    ↓
REVERSAL HAUSSIER attendu → Impact +51.7 pips ✅
```

### Calcul Direction_Sentiment

**Composantes :**
1. **Trend** : BAISSIER/HAUSSIER/NEUTRE (depuis pic)
2. **Momentum 24h** : % variation prix
3. **Position range** : Où se situe prix dans range 24h (0-1)

**Formule :**
```python
# Base depuis trend
if trend == 'HAUSSIER': base = +0.5
if trend == 'BAISSIER': base = -0.5
if trend == 'NEUTRE':   base = 0.0

# Ajustements
momentum_adj = momentum_24h_pct / 100 × 0.3  # Max ±0.3
position_adj = +0.2 si position > 0.8 else -0.2 si < 0.2 else 0.0

# Combinaison
direction_sentiment = base + momentum_adj + position_adj
direction_sentiment = clamp(direction_sentiment, -1.0, +1.0)
```

### Formule Combined_factor

**Actuelle (à tester) :**
```python
combined_factor = direction_factor × (1 + direction_sentiment × 0.1)
```

**Exemple :**
- Surprise +33% → direction_factor = 1.05
- Sentiment -0.4 (baissier)
- combined = 1.05 × (1 + (-0.4) × 0.1) = 1.05 × 0.96 = 1.008

**Problème potentiel :** Atténue au lieu d'amplifier (reversal)

**Inversée (à tester si échec) :**
```python
combined_factor = direction_factor × (1 - direction_sentiment × 0.1)
```

**Exemple inversé :**
- Surprise +33% → direction_factor = 1.05
- Sentiment -0.4 (baissier)
- combined = 1.05 × (1 - (-0.4) × 0.1) = 1.05 × 1.04 = 1.092

---

## 📊 RÉSULTATS CSV

### Structure `resultats_combined_FIXED_TIMEZONE.csv`

**19 colonnes :**
```
date                    : Date CPI (YYYY-MM-DD)
surprise_net            : Surprise nette en %
impact_reel             : Impact réel mesuré (pips)
num_events              : Nombre événements HIGH cluster
score_ajuste            : Score empirique ajusté
direction_sentiment     : -1.0 à +1.0
peak_type               : HIGH ou LOW
distance_peak_pips      : Distance du pic (pips)
hours_since_peak        : Temps écoulé depuis pic (heures)
momentum_24h            : Momentum 24h (%)
position_range          : Position dans range (0-1)
atr_24h                 : Volatilité 24h (pips)
trend                   : BAISSIER/HAUSSIER/NEUTRE
impact_baseline         : Prédiction Baseline (pips)
impact_v2               : Prédiction V2 (pips)
impact_combined         : Prédiction Combined (pips)
erreur_baseline         : |Baseline - Réel| (pips)
erreur_v2               : |V2 - Réel| (pips)
erreur_combined         : |Combined - Réel| (pips)
```

### Exemples Attendus

**11.09.2025 (Reversal haussier) :**
```csv
2025-09-11,+33.6,51.7,9,85.1,-0.4,HIGH,-40.9,21.0,-0.5,0.25,12.3,BAISSIER,47.0,49.0,47.0,4.7,2.7,4.7
```

**05.13.2025 (Surprise extrême négative) :**
```csv
2025-05-13,-108.5,34.0,7,70.2,+0.4,LOW,+35.2,18.5,+0.3,0.70,15.8,HAUSSIER,56.0,39.0,41.0,22.0,5.0,7.0
```

---

## 🎯 OBJECTIFS & DÉCISIONS

### Objectifs Session 92.10

1. **MAE Combined < 5 pips** (strict)
2. **0 régressions vs Baseline**
3. **MAE Combined < MAE V2 (8.5 pips)**

### Décisions Possibles

**Si MAE < 5 pips ✅**
→ SUCCÈS COMPLET → Test Combined 40 dates (Session 92.11)

**Si MAE 5-8 pips ⚠️**
→ SUCCÈS PARTIEL → Tester formule inversée OU 10-15 dates supplémentaires

**Si MAE > 8.5 pips ❌**
→ ÉCHEC → Tester formule inversée OU Accepter V2 → Test V2 40 dates

### Critères Logique Inversée

**Inversée détectée si ≥2 dates montrent :**
- Reversal haussier : Surprise+ / Sentiment- / Combined atténue ❌
- Reversal baissier : Surprise- / Sentiment+ / Combined amplifie ❌

**Action :** Exécuter `test_formule_INVERSE.py`

---

## 📋 USAGE RAPIDE

### Test Complet 4 Dates

```bash
# 1. Aller dans répertoire
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session92.8

# 2. Lancer test principal (2-3 min)
python3 execute_test_FIXED_TIMEZONE.py

# 3. Analyser résultats automatiquement
python3 analyze_results_auto.py

# 4. Si échec détecté, tester inversé
python3 test_formule_INVERSE.py
```

### Lecture Résultats

**Fichiers générés :**
- `resultats_combined_FIXED_TIMEZONE.csv`
- `resultats_combined_INVERSE.csv` (si inversé testé)

**Ouvrir avec :**
- Excel / LibreOffice
- Python pandas : `pd.read_csv('resultats_combined_FIXED_TIMEZONE.csv')`

---

## 🔧 TIMEZONE RÈGLE CRITIQUE

**TOUJOURS APPLIQUER :**
```
Events et prices : MÊME timezone (+02:00 Bern)
14:30 Bern = 12:30:00+02:00 dans la DB
PAS de conversion nécessaire
```

**Query SQL correcte :**
```sql
WHERE datetime >= '2025-09-11 12:30:00+02:00'::TIMESTAMP
```

**❌ NE PAS FAIRE :**
```python
event_time = datetime(2025, 9, 11, 14, 30, 0, tzinfo=tz_bern)  # = 16:30 Bern ❌
```

**Documentation complète :**
- `eurusd_clean/docs/GUIDE_TIMEZONE_DEFINITIF.md`
- `project_state_new.md` section timezone

---

## 📚 DOCUMENTATION COMPLÈTE

**Répertoire : `eurusd_clean/docs/`**

**Session 92.10 :**
- `SESSION92.10_SYNTHESE_FINALE.md` - Résumé complet
- `SESSION92.10_CORRECTIONS_APPLIQUEES.md` - Détail technique
- `SESSION92.10_ANALYSE_ATTENDUE.md` - Prédictions résultats
- `PLAN_SESSION92.11.md` - Session suivante
- `ANTI_PATTERN_CRITIQUE.md` - Erreur à éviter

**Sessions précédentes :**
- `SESSION92.5_RAPPORT_COMPLET.md` - Validation Dukascopy
- `SESSION92.7_RAPPORT_COMPLET.md` - V2 surprise nette
- `SESSION92.9_RAPPORT_COMPLET.md` - Correction logique

---

## ⚠️ LIMITATIONS CONNUES

### Données Requises

**Minimum requis :**
- Événements US CPI avec score > 40
- Prix 1 minute 24h avant événement
- Données surprise (estimate, forecast, previous)

**Si manquant :**
- `load_prices_24h_before()` retourne DataFrame vide
- `analyze_date()` retourne None
- Date ignorée dans résultats

### Timezone Sensible

**CRITIQUE :** Timestamps doivent être exacts

**Vérification obligatoire :**
1. Vérifier échantillon DB : `SELECT datetime FROM prices_1m LIMIT 3`
2. Doit afficher `+02:00` dans timestamps
3. Si différent → Consulter GUIDE_TIMEZONE_DEFINITIF.md

### Overfitting Possible

**Attention :** 4 dates = échantillon petit

**Validation requise :**
- Test 40 dates minimum (Session 92.11)
- Tests statistiques significativité
- Cross-validation si nécessaire

---

## 💡 TIPS DÉVELOPPEMENT

### Debugging

**Si aucune donnée chargée :**
```python
# Vérifier timezone DB
conn = duckdb.connect(str(DB_PATH), read_only=True)
sample = conn.execute("SELECT datetime FROM prices_1m LIMIT 3").df()
print(sample)  # Doit afficher +02:00
```

**Si pic non trouvé :**
```python
# Vérifier range 24h
print(f"High 24h : {prices_24h['high'].max()}")
print(f"Low 24h  : {prices_24h['low'].min()}")
print(f"Range    : {(prices_24h['high'].max() - prices_24h['low'].min()) * 10000} pips")
```

### Extension Formule

**Pour ajouter nouveau facteur :**
1. Modifier `calculate_combined_factor()`
2. Ajouter paramètres fonction `analyze_date()`
3. Ajouter colonnes CSV résultats
4. Tester sur 4 dates référence
5. Valider amélioration vs V2

---

## 🎯 PROCHAINE ÉTAPE

**Action immédiate :**
```bash
python3 execute_test_FIXED_TIMEZONE.py
```

**Après résultats :**
- Lire verdict automatique
- Suivre décision proposée
- Créer Session 92.11 selon scénario

**Budget restant :** ~91k tokens pour Session 92.11

---

_README Session 92.8 - Direction_sentiment 24h + Timezone_  
_Dernière mise à jour : 29 octobre 2025 - Session 92.10_  
_"Lire, appliquer, tester, décider" ⚠️_
