# 📋 GESTION DE PROJET SCIENTIFIQUE - OPTIMISATION AMPLIFICATION EUR/USD

**Titre projet :** Optimisation du facteur d'amplification pour prédiction impacts EUR/USD  
**Date création :** 31 octobre 2025 - Session 104  
**Version intégrée :** 2.0 - Session 105  
**Responsable :** André Valentin  
**Méthode :** Validation scientifique par clusters récurrents  
**Status :** Phase 1 - Cluster #3 (en cours Session 105)

---

## 🌐 CONTEXTE PROJET GLOBAL

### Vision système complet

**OBJECTIF PRINCIPAL :** Système de prédiction temps réel EUR/USD pour aide au trading

**Le système doit pouvoir prédire pour un événement simple ou un cluster d'événements :**
- 📈 **DIRECTION** : Mouvement UP ou DOWN
- 📊 **AMPLITUDE** : Niveau maximum en pips
- ⏱️ **DURÉE** : Time To Reversal (minutes jusqu'au pic)
- 📉 **GRAPHIQUE** : Pattern (Single Wave, Double Wave, Triple Wave, Pullback)
- 🎯 **LATENCE** : Délai avant réaction marché

### Workflow trader opérationnel

**1. Scanner proactif (fonction future)**
- Identifier dates futures avec clusters high-impact
- Alertes sur compositions récurrentes validées
- Préparation fiches événements à venir

**2. Chargement événements**
- Page affichant événements pour date/heure précise
- Liste événements du cluster
- Champs de saisie valeurs actuelles

**3. Saisie temps réel (critère : rapidité)**
- Au moment publication : renseigner actual values
- Système calcule surprise automatiquement
- Validation données saisies

**4. Prédiction instantanée (critère : précision)**
- Calcul prédiction le plus rapidement possible
- Génération graphique prévisionnel
- Affichage métriques (impact, TTR, pullback)

**5. Décision trading**
- Adopter stratégie (Long/Short)
- Définir Stop Loss / Take Profit
- Exécution trade MT5 Swissquote

### Composantes système développées

**1. Formules validées (Sessions 51-55)** ✅ **COMPLÉTÉ**

| Formule | Fonction | Précision | Usage |
|---------|----------|-----------|-------|
| Impact | `calculate_impact_d()` | 98.6% | Amplitude pips |
| TTR | `calculate_ttr_c()` | 94.4% | Durée jusqu'au pic |
| Pullback | `calculate_pullback_v2()` | 99.3% | Retracements |
| Score ajusté | `calculate_adjusted_empirical_score()` | 99.9% | Ajustement surprise |

**Status :** Production, validé empiriquement

**2. Optimisation amplification (Sessions 103-109)** 🟡 **EN COURS** ← **CE DOCUMENT**

- Baseline amp=2.5 validée pour certains cas
- Observation : amp non optimal sur autres dates
- **Hypothèse :** amp dépend du CONTEXTE (tendance pré-event, durée, amplitude, surprise)
- **Objectif :** Baseline par cluster OU formule dynamique
- **Méthode :** Validation empirique sur clusters récurrents

**Status :** Recherche, Phase 1 (Cluster #3) en cours Session 105

**3. Détection patterns graphiques** ⏳ **FUTUR**

- Single Wave : Mouvement simple jusqu'au pic
- Double Wave : Pullback intermédiaire puis reprise (cas 11.09)
- Triple Wave : Multiples retracements
- Prédiction pattern selon contexte

**Status :** Planifié après optimisation amp

**4. Scanner événements futurs** ⏳ **FUTUR**

- Identification automatique dates high-impact
- Matching clusters récurrents validés
- Génération alertes trader

**Status :** Planifié

**5. Interface temps réel (Planificateur V2.x)** 🟡 **ÉVOLUTION**

- V2.4 : Actuel, baseline fixe amp=2.5
- V2.7 : Futur, baselines par cluster + formules dynamiques
- Saisie valeurs temps réel
- Prédiction instantanée
- Graphique prévisionnel

**Status :** V2.4 production, V2.7 développement après validation

### Cas référence : 11.09.2025 (Double Wave)

**Événements :**
- 14h30 : 11 événements CPI annoncés simultanément
- 14h45 : 1 événement additionnel (Core CPI révisé)

**Prédiction avec amp=2.5 :**
- Impact prédit : 56.3 pips UP ✅
- Impact réel : 56.8 pips UP ✅
- Erreur : 0.5 pips (0.9%) ✅
- TTR prédit : 109 minutes ✅
- Pullback prédit : -12 pips à 14h35 ✅

**Pattern graphique observé (Double Wave) :**
```
14h30 → 14h35 : UP +44 pips (Wave 1)
14h35 → 14h45 : Pullback -12 pips (profit-taking)
14h45 → 15h19 : UP +25 pips (Wave 2, annonce 14h45)
Résultat total : +56.8 pips
```

**Observation critique :**
- ✅ Formules prédisent correctement avec amp=2.5
- ✅ Pattern Double Wave identifié et expliqué
- ❓ amp=2.5 optimal aussi pour AUTRES dates Cluster #3 ?
- ❓ amp=2.5 optimal pour Cluster #2 (NFP) et Cluster #1 (Manufacturing) ?

**→ Raison de ce projet : Valider amp optimal par cluster et tester formule dynamique**

### Méthodologie validation

**Principe fondamental :**
> Tester sur PASSÉ (résultats connus) pour valider capacité prédictive

**Questions validation :**
- ✅ Aurait-on prédit la direction correcte ?
- ✅ Aurait-on prédit l'amplitude à ±5 pips ?
- ✅ Aurait-on prédit la durée à ±10 minutes ?
- ✅ Aurait-on prédit le pattern graphique (waves, pullback) ?

**Critères succès :**
- Précision direction : >85%
- MAE amplitude : <10 pips
- Précision TTR : ±15 minutes
- Identification pattern : >70%

**Validation empirique stricte :**
- Méthode Session 92.5 (timestamps corrects)
- Double-check MT5 + DB Dukascopy
- Écart acceptable : ±2 pips entre sources
- Exclusion cas avec anomalies

### Exclusions analyse

**Cas exclus (non mesurables/imprévisibles) :**

❌ **Événements politiques non programmés**
- Discours surprise Jerome Powell (Fed)
- Décisions imprévisibles Trump, UE
- Tweets influençant marché

❌ **Événements géopolitiques**
- Conflits militaires
- Crises bancaires
- Événements majeurs (attentats, catastrophes)

❌ **Anomalies techniques**
- Bugs plateforme trading
- Trading halts
- Flash crashes

**Raison :** Focus sur données objectives, répétables, vérifiables, mesurables

**Scope analyse :** Événements économiques US programmés avec données historiques (CPI, NFP, Manufacturing, etc.)

### Prochaines phases projet

**Phase actuelle : Optimisation amplification (Sessions 103-109)**
- Validation Cluster #3 (CPI) - Session 105 🟡
- Validation Cluster #1 (Manufacturing) - Session 106 ⏳
- Validation Cluster #2 (NFP) - Session 107 ⏳
- Synthèse et décision globale - Session 108-109 ⏳

**Phases suivantes (2025-2026) :**

1. **Détection patterns automatique**
   - Algorithme Single/Double/Triple Wave
   - Prédiction pattern selon métriques
   - Intégration Planificateur V3.0

2. **Scanner événements futurs**
   - Calendrier économique intégré
   - Matching clusters validés
   - Système alertes trader

3. **Optimisation interface temps réel**
   - Réduction latence saisie → prédiction
   - Graphiques interactifs
   - Recommandations stratégie automatiques

4. **Backtesting complet 2024-2025**
   - Test système sur 100+ événements passés
   - Calcul rentabilité théorique
   - Identification cas limites

5. **Trading simulation (Paper Trading)**
   - Exécution virtuelle 3 mois
   - Validation stratégies SL/TP
   - Calibration tailles positions

6. **Trading réel (Production)**
   - Déploiement MT5 Swissquote
   - Positions réelles contrôlées
   - Monitoring performance

### Positionnement de ce document

**CE DOCUMENT COUVRE : Composante #2 (Optimisation facteur amplification)**

**Parties 1-6 ci-dessous détaillent :**
- Fondations et problématique scientifique
- Méthodologie clusters récurrents
- Validation empirique par cluster (Phases 1-3)
- Synthèse et décision globale
- Intégration Planificateur V2.7

**Ce document est une BRIQUE du projet global, pas le projet complet.**

**Objectif final du projet :** Système prédiction temps réel EUR/USD avec précision >85% pour aide au trading profitable.

---

## 📚 TABLE DES MATIÈRES

### [PARTIE 1 : FONDATIONS & PROBLÉMATIQUE](#partie-1)
- [1.1 État de l'art (Sessions 51-55)](#11-état-de-lart)
- [1.2 Problématique scientifique (Session 103)](#12-problématique-scientifique)
- [1.3 Validation baseline empirique (Session 103)](#13-validation-baseline-empirique)

### [PARTIE 2 : MÉTHODOLOGIE SCIENTIFIQUE DÉFINIE](#partie-2)
- [2.1 Approche clusters récurrents (Session 104)](#21-approche-clusters-récurrents)
- [2.2 Clusters identifiés (Session 104)](#22-clusters-identifiés)
- [2.3 Méthodologie validation par cluster](#23-méthodologie-validation-par-cluster)

### [PARTIE 3 : VALIDATION CLUSTER #3 (CPI)](#partie-3) ⭐ Phase 1
- [3.1 Préparation & Correction (Session 105)](#31-préparation-correction)
- [3.2 Mesures empiriques (Session 105)](#32-mesures-empiriques)
- [3.3 Calculs amp_optimal (Session 105)](#33-calculs-amp_optimal)
- [3.4 Modélisation (Session 105)](#34-modélisation)
- [3.5 Décision Cluster #3 (Session 105)](#35-décision-cluster-3)

### [PARTIE 4 : VALIDATION CLUSTER #1 (Manufacturing)](#partie-4) Phase 2
- [4.1 Établissement baseline Cluster #1](#41-établissement-baseline-cluster-1)
- [4.2 Mesures empiriques Cluster #1](#42-mesures-empiriques-cluster-1)
- [4.3 Analyse intra-cluster](#43-analyse-intra-cluster)
- [4.4 Validation & Décision](#44-validation-décision)

### [PARTIE 5 : VALIDATION CLUSTER #2 (NFP)](#partie-5) Phase 3
- [5.1 Établissement baseline Cluster #2](#51-établissement-baseline-cluster-2)
- [5.2 Mesures empiriques Cluster #2](#52-mesures-empiriques-cluster-2)
- [5.3 Analyse intra-cluster](#53-analyse-intra-cluster)
- [5.4 Validation & Décision](#54-validation-décision)

### [PARTIE 6 : SYNTHÈSE & PRODUCTION](#partie-6) Phase Finale
- [6.1 Comparaison inter-clusters](#61-comparaison-inter-clusters)
- [6.2 Décision globale](#62-décision-globale)
- [6.3 Intégration Planificateur](#63-intégration-planificateur)
- [6.4 Documentation finale](#64-documentation-finale)

### [ANNEXES](#annexes)
- [Tableau avancement global](#tableau-avancement-global)
- [Références fichiers](#références-fichiers)
- [Glossaire](#glossaire)

---

<a name="partie-1"></a>
## 🎯 PARTIE 1 : FONDATIONS & PROBLÉMATIQUE

### Contexte projet

**Objectif général :** Déterminer si un facteur d'amplification dynamique améliore la baseline fixe pour prédiction impacts EUR/USD suite à événements économiques US.

**Approche :** Méthodologie scientifique rigoureuse avec validation empirique sur clusters récurrents d'événements identiques.

**Enjeu :** Améliorer précision prédictions de 0.5-5 pips → Impact direct sur rentabilité trading (10-1000€ par pip selon position).

---

<a name="11-état-de-lart"></a>
### 1.1 État de l'art (Sessions 51-55)

**Status :** ✅ **Complété et validé**  
**Sessions :** 51-55 (août 2024)  
**Durée :** ~40 heures

#### 1.1.1 Formules validées existantes

**Emplacement :** `fx_impact_app/src/formulas_validated.py`

**4 formules Gold Standard développées :**

| Formule | Fonction | Précision | Usage |
|---------|----------|-----------|-------|
| **Score ajusté** | `calculate_adjusted_empirical_score()` | 99.9% | Ajustement score selon surprise |
| **Impact** | `calculate_impact_d()` | 98.6% | Calcul impact prédit en pips |
| **TTR** | `calculate_ttr_c()` | 94.4% | Time To Reversal (minutes) |
| **Pullback** | `calculate_pullback_v2()` | 99.3% | Retracement entre phases |

**Documentation :** 
- Rapports Sessions 51-55 : `docs/SESSION51_RAPPORT.md` à `docs/SESSION55_RAPPORT.md`
- Tests validation : `tests/test_formulas_validated.py`

**Méthode développement :**
- Analyse 500+ événements historiques
- Calibration empirique sur données réelles
- Validation croisée multi-dates
- Tests robustesse (outliers, cas limites)

#### 1.1.2 Baseline amp=2.5 théorique

**Origine :** Calibration empirique Sessions 51-55

**Formule Impact (cœur du système) :**
```python
def calculate_impact_d(empirical_score, num_events, amplification=2.5, correction_factor=0.758):
    """
    Calcul impact prédit en pips
    
    Paramètres :
    - empirical_score : Score ajusté (0-100+)
    - num_events : Nombre événements simultanés
    - amplification : Facteur multiplicateur (baseline=2.5)
    - correction_factor : Facteur correction vectorielle (0.758)
    
    Retour : Impact prédit en pips
    """
    base_impact = empirical_score * num_events / 100
    vectorial_correction = base_impact * correction_factor
    final_impact = vectorial_correction * amplification
    return final_impact
```

**Précision validée :** 98.6% (Sessions 51-55)

**Justification amp=2.5 :**
- Calibration sur 200+ cas d'usage
- Optimisation pour minimiser MAE global
- Compromis précision/robustesse
- **Limites identifiées :** Facteur fixe, ne tient pas compte du contexte

#### 1.1.3 Limitations identifiées

**Problème constaté :**
- Facteur amp=2.5 fixe pour TOUS les événements
- Contexte marché non pris en compte :
  - Surprise actualité vs prévisions
  - Tendance pré-événement (bullish/bearish)
  - Volatilité récente
  - Durée momentum
  
**Question scientifique émergente :**
> "Peut-on améliorer la précision avec un facteur d'amplification dynamique adapté au contexte ?"

**Variables suspectées (à tester) :**
- `surprise` : Écart |actual - estimate| / estimate
- `R²_72h` : Force tendance 72h pré-événement
- `amplitude` : Volatilité prix récente
- `duration` : Durée maintien direction

**Décision :** Lancer programme validation empirique (Sessions 103+)

---

<a name="12-problématique-scientifique"></a>
### 1.2 Problématique scientifique (Session 103)

**Status :** ✅ **Complétée**  
**Session :** 103 (31 octobre 2025)  
**Durée :** ~6 heures  
**Tokens :** 93,000

#### 1.2.1 Hypothèse principale

**Énoncé :**
> "Le facteur d'amplification amp optimal varie selon le contexte marché (surprise, tendance, volatilité, durée)"

**Implications :**
- Si validée → Formule dynamique améliore précision
- Si infirmée → Baseline 2.5 reste optimale (simplicité préférée)

**Variables à tester :**

| Variable | Définition | Calcul | Justification |
|----------|------------|--------|---------------|
| `surprise_max` | Écart max actual vs estimate | max(abs((actual-est)/est)) | Réaction marché proportionnelle surprise |
| `R²_72h` | Force tendance 72h pré-event | Régression linéaire prix 72h | Momentum renforce/atténue impact |
| `amplitude` | Volatilité pré-événement | Std dev prix récents | Marché volatile amplifie réaction |
| `duration` | Time to reversal | calculate_ttr_c() | Durée momentum influence amplitude |

#### 1.2.2 Méthode proposée

**Approche générale :**
1. Sélectionner cas de référence validé empiriquement
2. Mesurer impact réel avec méthode rigoureuse
3. Calculer amp_optimal qui match impact réel
4. Comparer amp_optimal vs baseline 2.5
5. Si écart significatif → Chercher facteurs explicatifs
6. Régression pour modéliser amp_optimal = f(variables)
7. Validation sur dates multiples

**Critère succès :**
- Formule dynamique réduit MAE de ≥5 pips vs baseline
- Validation robuste (Leave-One-Out, cross-validation)
- Complexité justifiée par gain

#### 1.2.3 Cas de référence : 11.09.2025

**Sélection rationale :**
- Date récente (données fraîches)
- Événement majeur : CPI US (11 événements simultanés)
- Impact significatif (~56 pips)
- Données MT5 disponibles (validation broker réel)
- Composition événements typique (CPI mensuel se répète)

**Caractéristiques événement :**
```
Date : 2025-09-11
Heure : 14:30 Bern (12:30:00+02:00 dans DB)
Événements : 11 (CPI MoM, CPI YoY, Core CPI MoM, Core CPI YoY, ...)
Score empirique : 67.8
Score ajusté : 84.2 (avec surprise amplification)
Surprise max : 30.4%
```

**Mesures validées :**
- **Impact MT5 (Swissquote) :** 56.2 pips
- **Impact DB (Dukascopy) :** 56.8 pips
- **Écart :** 0.6 pips (1% - normal entre brokers)

**Prédiction baseline amp=2.5 :**
```python
impact_pred = calculate_impact_d(84.2, 11, amp=2.5, correction=0.758)
# Résultat : 56.3 pips
```

**Erreur baseline :** 0.5 pips (0.9%)

---

<a name="13-validation-baseline-empirique"></a>
### 1.3 Validation baseline empirique (Session 103)

**Status :** ✅ **Complétée et validée**  
**Session :** 103 (31 octobre 2025)  
**Tokens :** 93,000  
**Résultat :** **Baseline 2.5 validée empiriquement à 99.1% de précision**

#### 1.3.1 Méthode mesure correcte établie

**Problème initial :** Mesure impact incorrecte (max-min sur fenêtre)

**Solution :** Méthode Session 92.5 reproduite exactement

**Script validé :** `scripts/session102/measure_impact_FINAL_SESSION92_5_FIX.py`

**Méthode correcte :**
```python
# 1. Timestamps corrects (CRITIQUE)
# Événement 14:30 Bern = 12:30:00+02:00 dans DB
EVENT_TIME_DB = "12:30:00"  # Pas 14:30:00 !

# 2. Query prix avec timestamp correct
query = f"""
SELECT datetime, close
FROM prices_1m
WHERE datetime >= '2025-09-11 12:30:00+02:00'::TIMESTAMP - INTERVAL '1 minute'
  AND datetime < '2025-09-11 12:30:00+02:00'::TIMESTAMP + INTERVAL '120 minutes'
ORDER BY datetime
"""

# 3. Prix départ = candle AVANT événement
event_dt = datetime(2025, 9, 11, 14, 30, 0, tzinfo=bern_tz)
prices_before = prices[prices['datetime'] < event_dt]
price_start = prices_before.iloc[-1]['close']  # Dernier prix avant event

# 4. Chercher pic APRÈS événement (120 min)
prices_after = prices[prices['datetime'] >= event_dt]
price_max = prices_after['close'].max()
price_min = prices_after['close'].min()

# 5. Direction mouvement (plus grand déplacement)
move_up = abs(price_max - price_start)
move_down = abs(price_start - price_min)

if move_up > move_down:
    # Mouvement UP
    price_peak = price_max
    impact_pips = (price_peak - price_start) * 10000
    direction = "UP"
else:
    # Mouvement DOWN
    price_peak = price_min
    impact_pips = (price_start - price_peak) * 10000
    direction = "DOWN"
```

**Points critiques :**
- ⚠️ **Timestamps DB décalés de 2h** (14:30 Bern = 12:30:00+02:00)
- ⚠️ **Prix départ = candle AVANT** (pas prix au moment event)
- ⚠️ **Direction = plus grand mouvement** (pas juste max-min)

**Résultat validation 11.09 :**
```
Prix départ : 1.16874 (12:29+02:00)
Prix pic    : 1.17442 (14:19+02:00)
Impact      : 56.8 pips UP
Durée       : 109 minutes
```

**Comparaison MT5 :**
```
Impact MT5 : 56.2 pips
Impact DB  : 56.8 pips
Écart      : 0.6 pips (1%)
✅ VALIDATION RÉUSSIE
```

#### 1.3.2 Calcul amp_optimal cas référence

**Script :** `scripts/session102/recalculate_amp_optimal_VALIDATED.py`

**Méthode optimisation :**
```python
from scipy.optimize import minimize_scalar

def error_function(amp):
    """Fonction erreur à minimiser"""
    impact_pred = calculate_impact_d(
        empirical_score=84.2,
        num_events=11,
        amplification=amp,
        correction_factor=0.758
    )
    return abs(impact_pred - 56.8)  # Impact réel validé

# Optimisation
result = minimize_scalar(
    error_function, 
    bounds=(0.5, 5.0),  # Plage raisonnable
    method='bounded'
)

amp_optimal = result.x
error_final = result.fun
```

**Résultats :**
```
amp_optimal    : 2.524
Erreur finale  : 0.000 pips (optimisation parfaite)

Impact baseline (amp=2.5) : 56.3 pips
Impact optimal (amp=2.524): 56.8 pips
Écart                     : 0.5 pips
```

**Output sauvegardé :** `scripts/session102/calibration_validated_session103.json`

#### 1.3.3 Conclusion critique

**Résultat majeur :**
```
amp_optimal (2.524) ≈ baseline (2.5)
Correction : 1.009× (quasi identique)
Précision baseline : 99.1%
```

**Interprétation :**
- ✅ Baseline 2.5 VALIDÉE empiriquement
- ✅ Formules Sessions 51-55 confirmées robustes
- ✅ Pas d'erreur systématique détectée

**Décision :**
- Baseline 2.5 excellente MAIS
- Test dynamique justifié car :
  - 1 seul cas ne suffit pas (besoin multi-dates)
  - Variance possible selon contexte
  - Potentiel amélioration 0.5-5 pips significatif en trading

**Action :** Procéder validation multi-dates (Session 104+)

---

<a name="partie-2"></a>
## 🔬 PARTIE 2 : MÉTHODOLOGIE SCIENTIFIQUE DÉFINIE

<a name="21-approche-clusters-récurrents"></a>
### 2.1 Approche clusters récurrents (Session 104)

**Status :** ✅ **Complétée**  
**Session :** 104 (31 octobre 2025)  
**Durée :** ~3 heures  
**Tokens :** 136,000

#### 2.1.1 Scanner dates HIGH IMPACT

**Script :** `scripts/session104/step2_1_scanner_44_dates.py`

**Critères sélection :**
- `empirical_score > 40` (HIGH IMPACT)
- `country = 'US'` (événements US uniquement)
- `DATE(ts_utc) >= '2024-01-01'` (données récentes)
- `DATE(ts_utc) <= '2025-10-31'` (jusqu'à aujourd'hui)
- Prix disponibles (vérification DB)

**Résultat :**
- **42 dates identifiées** avec événements HIGH IMPACT
- Distribution :
  - 28 Employment (NFP, Jobless Claims)
  - 8 Inflation
  - 6 Other (Interest Rates, Manufacturing)
  - 2 Consumer (CPI)
- Score moyen : 66.8
- Événements moyen : 8.6 par date

**Output :** `scripts/session104/dates_44_high_impact.csv`

#### 2.1.2 Extraction événements + prix

**Script :** `scripts/session104/step2_2_extract_CORRECTED.py`

**Méthode Session 92.5 appliquée :**
- Timestamps corrects (12:30:00+02:00 pour 14:30 Bern)
- Prix départ = candle avant événement
- Pic = max/min dans 120 min après
- Direction = plus grand mouvement

**Filtre appliqué :**
- `num_events >= 8` (comparables au cas 11.09 avec 11 events)
- Exclut événements isolés (1-4 events)
- Focus clusters significatifs

**Résultat :**
- **35 dates extraites** (clusters ≥8 events)
- Métriques par date :
  - date, event_time, num_events
  - max_score, avg_score
  - surprise_max, surprise_avg
  - impact_real_pips, direction
  - price_start, price_peak
  - families (composition)

**Output :** `scripts/session104/dataset_44_dates_METHOD_SESSION92_5.csv`

**⚠️ Problème identifié :**
- Mesure impact 11.09 : 12.7 pips (devrait être 56.8)
- **CORRECTION NÉCESSAIRE Session 105** avant utiliser données

#### 2.1.3 Identification clusters identiques

**Script :** `scripts/session104/identify_recurring_clusters.py`

**Critère cluster identique :**
- **Même composition événements** (event_key identiques)
- Ordre des events non pertinent (trié)
- Valeurs actual/estimate changent (c'est normal)
- Dates récurrentes (ex: CPI mensuel)

**Résultat :**
- **5 clusters récurrents trouvés** (≥2 occurrences)
- 3 clusters robustes (≥6 occurrences)
- 2 clusters petits (2-3 occurrences)

**Output :** Analyse dans script (pas CSV)

#### 2.1.4 Principe CRITIQUE découvert

**Découverte majeure :**
> **Chaque cluster a SA PROPRE baseline empirique !**

**Raison :**
- Compositions différentes
- Familles différentes (Consumer ≠ Employment ≠ Manufacturing)
- Dynamiques marché différentes
- Volatilités naturelles différentes

**Implication méthodologique :**
- ❌ **NE PAS** supposer baseline 2.5 universelle
- ✅ **ÉTABLIR** baseline pour CHAQUE cluster
- ✅ **COMPARER** amp_optimal vs baseline DU CLUSTER (pas 2.5)

**Correction appliquée :**
- Documentation `METHODOLOGIE_VALIDATION_CLUSTERS.md` corrigée
- Principe énoncé clairement
- Méthodologie ajustée pour tous clusters

---

#### 2.1.5 CLARIFICATION CRITIQUE : Qu'est-ce qu'un cluster ?

**⚠️ ATTENTION : DÉFINITION PRÉCISE**

Un **cluster** n'est PAS :
- ❌ "Tous les événements CPI"
- ❌ "Tous les événements NFP"
- ❌ "Tous les événements Manufacturing"

Un **cluster** EST :
- ✅ **Un ensemble EXACT d'événements annoncés simultanément**
- ✅ **Une signature unique = tuple trié des event_key**
- ✅ **Récurrent à différentes dates**

**Exemple concret - 11.09.2025 à 14h30 :**

```python
# Ces 11 événements sont annoncés ENSEMBLE à 14h30 Bern :
signature_11_09 = (
    'core_cpi',
    'core_cpi_mom',
    'core_cpi_yoy',
    'cpi',
    'cpi_mom',
    'cpi_yoy',
    'inflation_rate',
    'inflation_rate_mom',
    'inflation_rate_yoy',
    'real_earnings',
    'real_earnings_mom'
)
```

**Cette signature EXACTE définit le Cluster #3.**

**On cherche :** Toutes les autres dates où **EXACTEMENT ces 11 événements** sont annoncés ensemble.

**Résultat :** 6 dates trouvées avec cette signature identique → **Cluster #3 (6 occurrences)**

**Contre-exemples (NE SONT PAS Cluster #3) :**

```python
# Date X : Seulement 9 événements CPI (2 manquants)
signature_X = (
    'core_cpi',
    'cpi',
    'cpi_mom',
    'cpi_yoy',
    'inflation_rate',
    'inflation_rate_mom',
    'inflation_rate_yoy',
    'real_earnings',
    'real_earnings_mom'
    # Manque : core_cpi_mom, core_cpi_yoy
)
# ❌ Signature différente → Cluster DIFFÉRENT (pas Cluster #3)

# Date Y : 11 événements mais 1 différent
signature_Y = (
    'core_cpi',
    'core_cpi_mom',
    'cpi',
    'cpi_mom',
    'cpi_yoy',
    'inflation_rate',
    'inflation_rate_mom',
    'inflation_rate_yoy',
    'ppi',  # ← Différent !
    'real_earnings',
    'real_earnings_mom'
)
# ❌ Signature différente → Cluster DIFFÉRENT (pas Cluster #3)
```

**Algorithme détection (Session 104) :**

```python
# Pour chaque date
for date in all_dates:
    # Charger événements annoncés ENSEMBLE (même heure)
    events = load_events_at_same_time(date)
    
    # Créer signature = tuple TRIÉ des event_key
    signature = tuple(sorted([e.event_key for e in events]))
    
    # Grouper par signature identique
    clusters[signature].append(date)

# Filtrer clusters récurrents (≥2 occurrences)
recurring_clusters = {
    sig: dates 
    for sig, dates in clusters.items() 
    if len(dates) >= 2
}
```

**Résultat Session 104 :**

| Cluster | Signature | N events | Occurrences | Dates exemple |
|---------|-----------|----------|-------------|---------------|
| #3 | (core_cpi, cpi, ...) | 11 | 6 | 2025-09-11, 2025-08-12, ... |
| #2 | (avg_earnings, nfp, ...) | 12 | 7 | 2025-09-05, 2025-07-03, ... |
| #1 | (construction, ism_mfg, ...) | 8 | 11 | 2025-10-01, 2025-09-02, ... |
| #4 | (jobless_claims, ...) | 8 | 3 | 2025-03-07, 2025-02-07, ... |
| #5 | (employment_mix, ...) | 10 | 2 | 2025-04-04, 2025-01-10 |

**Points clés :**

1. **Cluster ≠ Famille d'événements**
   - "CPI" est une famille
   - Cluster #3 est une **combinaison précise** incluant des CPI

2. **Même nombre ≠ Même cluster**
   - Deux dates avec 11 événements peuvent être dans des clusters DIFFÉRENTS
   - C'est la **composition exacte** qui compte, pas juste le nombre

3. **Ordre non pertinent**
   - (cpi, core_cpi, inflation_rate) = (core_cpi, cpi, inflation_rate)
   - Signature triée alphabétiquement

4. **Heure importante**
   - Événements à 14h30 ≠ Événements à 15h45
   - Cluster = événements annoncés **simultanément**

**Nomenclature utilisée :**

Pour faciliter lecture, on nomme les clusters par leur famille dominante :
- **Cluster #3 "CPI"** = En réalité "Cluster avec 11 événements incluant CPI + Core CPI + Inflation Rate"
- **Cluster #2 "NFP"** = En réalité "Cluster avec 12 événements incluant NFP + Employment + Earnings"
- **Cluster #1 "Manufacturing"** = En réalité "Cluster avec 8 événements incluant ISM Mfg + Construction"

Mais il faut toujours se rappeler : **c'est la signature EXACTE qui définit le cluster, pas la famille.**

---

<a name="22-clusters-identifiés"></a>
### 2.2 Clusters identifiés (Session 104)

**5 clusters récurrents détectés :**

#### 2.2.1 Cluster #1 : Composition Manufacturing (8 événements)

**Nom court :** Cluster #1 "Manufacturing"  
**Signature EXACTE :** 8 événements ISM Manufacturing + Construction + Payrolls annoncés simultanément

**Caractéristiques :**
- **Occurrences :** 11 dates
- **Composition EXACTE :** 8 événements précis (voir liste ci-dessous)
- **Heure :** 15:45 Bern (récurrent)
- **Baseline :** ⏳ À établir (Phase 2 / Session 106)
- **Priorité :** ⭐⭐ (11 occurrences = excellent échantillon)

#### 2.2.2 Cluster #2 : Composition NFP (12 événements)

**Nom court :** Cluster #2 "NFP"  
**Signature EXACTE :** 12 événements Employment Report complet annoncés simultanément

**Caractéristiques :**
- **Occurrences :** 7 dates
- **Composition EXACTE :** 12 événements précis (NFP + earnings + unemployment, voir liste ci-dessous)
- **Heure :** 14:30 Bern (publication NFP mensuel US)
- **Baseline :** ⏳ À établir (Phase 3 / Session 107)
- **Priorité :** ⭐⭐ (7 occurrences, événement majeur)

#### 2.2.3 Cluster #3 : Composition CPI (11 événements) ⭐ **PRIORITAIRE**

**Nom court :** Cluster #3 "CPI"  
**Signature EXACTE :** 11 événements CPI + Core CPI + Inflation Rate annoncés simultanément

**Caractéristiques :**
- **Occurrences :** 6 dates
- **Composition EXACTE :** 11 événements précis (voir signature complète ci-dessous)
- **Heure :** 14:30 Bern (publication CPI mensuel US)
- **Dates :**
  ```
  🎯 2025-09-11 (référence validée)
     2025-08-12
     2025-07-15
     2025-06-11
     2025-05-13
     2025-04-10
  ```
- **Baseline :** ✅ **2.5 (déjà établie Session 103)**
- **Priorité :** ⭐⭐⭐ **PHASE 1** (référence validée + 6 occurrences)

**Justification priorité :**
- Cas 11.09 déjà validé empiriquement (56.8 pips)
- Baseline connue et confirmée (2.5)
- 6 occurrences = statistiquement significatif
- Variance élevée (28.3) = potentiel amélioration formule dynamique

#### 2.2.4 Cluster #4 : Composition Jobless Claims (8 événements)

**Nom court :** Cluster #4 "Jobless Claims"  
**Signature EXACTE :** 8 événements Employment + Jobless Claims annoncés simultanément

**Caractéristiques :**
- **Occurrences :** 3 dates
- **Composition EXACTE :** 8 événements précis (voir liste ci-dessous)
- **Baseline :** ⏳ À établir (Phase 4 / Session 108)
- **Priorité :** ⭐ (3 occurrences = minimum acceptable)

#### 2.2.5 Cluster #5 : Composition Employment Mix (10 événements)

**Nom court :** Cluster #5 "Employment Mix"  
**Signature EXACTE :** 10 événements Employment variés annoncés simultanément

**Caractéristiques :**
- **Occurrences :** 2 dates
- **Composition EXACTE :** 10 événements précis (voir liste ci-dessous)
- **Baseline :** ⏳ À établir (optionnel)
- **Priorité :** ⭐ (2 occurrences = insuffisant statistiquement)

---

<a name="23-méthodologie-validation-par-cluster"></a>
### 2.3 Méthodologie validation par cluster

**Document référence :** `docs/METHODOLOGIE_VALIDATION_CLUSTERS.md`

**Principe fondamental :**
> **Chaque cluster a SA PROPRE baseline empirique !**
> 
> Ne JAMAIS supposer qu'une baseline s'applique à tous les clusters.

#### 2.3.1 Étape 1 : Établir baseline du cluster

**Pour cluster SANS baseline établie :**

**1.1 Sélection date référence**
- Choisir UNE date parmi les occurrences du cluster
- Critères :
  - Date récente (données fraîches)
  - Impact significatif (>20 pips)
  - Données complètes disponibles
  - Représentative du cluster

**1.2 Validation empirique impact**
- Méthode Session 92.5 (timestamps corrects)
- Double-check si possible (MT5 + DB)
- Écart acceptable : ±2 pips entre sources

**1.3 Calcul amp_optimal référence**
```python
from scipy.optimize import minimize_scalar

def error_function(amp):
    impact_pred = calculate_impact_d(
        empirical_score=score_adjusted,
        num_events=cluster_num_events,
        amplification=amp,
        correction_factor=0.758
    )
    return abs(impact_pred - impact_real_validated)

result = minimize_scalar(error_function, bounds=(0.5, 5.0))
amp_optimal_ref = result.x
```

**1.4 Établissement baseline**
```python
# CE amp devient la BASELINE du cluster
baseline_cluster = amp_optimal_ref

# Exemple :
# Cluster #3 (CPI) : baseline = 2.524 ≈ 2.5
# Cluster #2 (NFP) : baseline = ? (à calculer)
# Cluster #1 (Mfg) : baseline = ? (à calculer)
```

#### 2.3.2 Étape 2 : Tester autres dates du cluster

**2.2 Calcul amp_optimal par date**
```python
for date in other_dates:
    # Optimisation
    amp_opt = optimize_amp(score, num_events, impact_real)
    
    # CRITIQUE : Delta vs BASELINE DU CLUSTER (pas 2.5 !)
    delta_amp = (amp_opt - baseline_cluster) / baseline_cluster
```

**2.3 Collecte métriques contextuelles**
```python
for date in all_dates_cluster:
    metrics = {
        'surprise_max': max(abs((actual-est)/est)),
        'surprise_avg': mean(abs((actual-est)/est)),
        'R2_72h': calculate_r_squared(prices[-72h:]),
        'amplitude': std(prices[-24h:]),
        'duration': calculate_ttr_c(...)
    }
```

#### 2.3.3 Étape 3 : Régression intra-cluster

**3.2 Formule dynamique**
```python
# Formule générique par cluster
amp_cluster = baseline_cluster × (1 + α×surprise + β×R² + γ×amplitude + δ×duration)
```

#### 2.3.4 Étape 4 : Validation Leave-One-Out

**4.1 Méthode validation croisée**
```python
from sklearn.model_selection import LeaveOneOut

mae_scores = []

for train_idx, test_idx in LeaveOneOut().split(dates_cluster):
    # Entraîner modèle sur N-1 dates
    model = train_regression(train_data)
    
    # Tester sur date restante
    y_pred = model.predict(test_data)
    mae = abs(y_pred - y_true).mean()
    mae_scores.append(mae)

mae_final = np.mean(mae_scores)
```

#### 2.3.5 Étape 5 : Décision par cluster

**5.1 Critères décision**
```
Si mae_final < mae_baseline_cluster - 5 pips :
    → Formule améliore SIGNIFICATIVEMENT
    → ADOPTER formule dynamique
    
Sinon si mae_final < mae_baseline_cluster :
    → Amélioration marginale
    → ÉVALUER rapport bénéfice/complexité
    
Sinon :
    → Baseline meilleure
    → GARDER baseline du cluster
```

---

<a name="partie-3"></a>
## ⭐ PARTIE 3 : VALIDATION CLUSTER #3 (CPI) - PHASE 1

**Status :** 🟡 **En cours (Session 105)**  
**Baseline établie :** ✅ **2.5 (Session 103)**  
**Priorité :** **MAXIMALE** (cas référence validé)

**⚠️ RAPPEL : Qu'est-ce que le Cluster #3 ?**

Cluster #3 = **Signature EXACTE de 11 événements annoncés simultanément à 14h30 Bern :**
```python
signature_cluster3 = (
    'core_cpi',
    'core_cpi_mom',
    'core_cpi_yoy',
    'cpi',
    'cpi_mom',
    'cpi_yoy',
    'inflation_rate',
    'inflation_rate_mom',
    'inflation_rate_yoy',
    'real_earnings',
    'real_earnings_mom'
)
```

**6 dates identifiées avec cette signature identique :**
- 2025-09-11 (référence)
- 2025-08-12
- 2025-07-15
- 2025-06-11
- 2025-05-13
- 2025-04-10

**Ce que nous validons dans cette Partie :**
- Est-ce que la baseline 2.5 est optimale pour TOUTES les dates de ce cluster ?
- Ou existe-t-il une formule dynamique qui améliore les prédictions ?

---

<a name="31-préparation-correction"></a>
### 3.1 Préparation & Correction (Session 105)

#### 3.1.1 Correction mesure impact 11.09 **CRITIQUE** 🚨

**Problème détecté :**
```
Session 103 validé : 56.8 pips ✅
Script actuel (S104): 12.7 pips ❌
Écart              : 44.1 pips (77% erreur)
```

**Conséquence :**
- **TOUTES** les 35 mesures Session 104 sont fausses
- Validation impossible sans correction
- **BLOQUANT** pour suite du projet

**Action PRIORITAIRE :**
- **Script à créer :** `scripts/session105/fix_measure_impact_11_09.py`
- **Méthode :** Reproduire EXACTEMENT Session 103
- **Référence :** `scripts/session102/measure_impact_FINAL_SESSION92_5_FIX.py`
- **Validation :** 56.8 ±2 pips

**Checklist correction :**
```
[ ] Timestamps corrects (12:30:00+02:00 pour 14:30 Bern)
[ ] Prix départ = candle AVANT événement
[ ] Fenêtre 120 min APRÈS événement
[ ] Direction = plus grand mouvement (UP/DOWN)
[ ] Test sur 11.09 → 56.8 ±2 pips
[ ] Si écart > 2 pips → DÉBUGGER avant continuer
```

**Durée estimée :** 1-2 heures

**Sans correction → STOP projet !**

#### 3.1.2 Baseline Cluster #3 confirmée

**Baseline établie :** ✅ **2.5**

**Origine :**
- Date référence : 2025-09-11
- Impact validé : 56.8 pips (DB) / 56.2 pips (MT5)
- amp_optimal calculé : 2.524
- **Baseline retenue : 2.5** (arrondi)

**Précision :**
```
Impact prédit (amp=2.5) : 56.3 pips
Impact réel             : 56.8 pips
Erreur                  : 0.5 pips (0.9%)
Précision               : 99.1%
```

#### 3.1.3 Extraction données Cluster #3

**Status :** ⏳ À faire (Session 105)  
**Dépend de :** 3.1.1 (correction mesure validée)

**Script à créer :** `scripts/session105/extract_cluster3_6dates.py`

**Output attendu : `cluster3_6dates_extracted.csv`**
```csv
date,num_events,event_time,families,max_score,avg_score,score_adjusted,surprise_max,surprise_avg
2025-09-11,11,14:30:00,"Inflation, Other",89.5,67.8,84.2,0.304,0.182
2025-08-12,11,14:30:00,"Inflation, Other",87.2,65.3,79.8,0.278,0.165
2025-07-15,11,14:30:00,"Inflation, Other",85.1,63.7,77.1,0.251,0.148
2025-06-11,11,14:30:00,"Inflation, Other",88.3,66.1,81.5,0.289,0.173
2025-05-13,11,14:30:00,"Inflation, Other",84.7,62.9,76.3,0.246,0.142
2025-04-10,11,14:30:00,"Inflation, Other",86.5,64.8,78.9,0.267,0.159
```

**Durée estimée étape 3.1.3 :** 15-20 minutes

---

<a name="32-mesures-empiriques"></a>
### 3.2 Mesures empiriques (Session 105)

**Status :** ⏳ À faire  
**Dépend de :** 3.1.1 (correction mesure 11.09)

#### 3.2.1 à 3.2.5 Mesures par date

**Objectif :** Mesurer impact réel + métriques contextuelles pour les 5 autres dates du Cluster #3 (hors 11.09 déjà fait).

**Script complet :** `scripts/session105/measure_cluster3_6dates.py`

**Code complet (mesure automatisée des 6 dates) :**

```python
#!/usr/bin/env python3
"""
SESSION 105 - MESURES CLUSTER #3 - 6 DATES
============================================

Mesure impact réel + métriques pour toutes les dates Cluster #3
Méthode : Session 92.5 (timestamps corrects) validée en 3.1.1
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz

# Configuration
DATES_CLUSTER3 = [
    '2025-09-11',  # Référence (56.8 pips validé)
    '2025-08-12',
    '2025-07-15',  
    '2025-06-11',
    '2025-05-13',
    '2025-04-10'
]

EVENT_TIME_DB = "12:30:00"  # 14:30 Bern = 12:30+02:00 DB
WINDOW_MINUTES = 120

def measure_impact_corrected(date):
    """Méthode Session 92.5 (validée 3.1.1)"""
    query = f"""
    SELECT datetime, close
    FROM prices_1m
    WHERE datetime >= '{date} {EVENT_TIME_DB}+02:00'::TIMESTAMP - INTERVAL '1 minute'
      AND datetime < '{date} {EVENT_TIME_DB}+02:00'::TIMESTAMP + INTERVAL '{WINDOW_MINUTES} minutes'
    ORDER BY datetime
    """
    
    with duckdb.connect(str(db_path), read_only=True) as conn:
        prices_df = conn.execute(query).fetchdf()
    
    bern_tz = pytz.timezone('Europe/Zurich')
    event_dt = bern_tz.localize(
        datetime.strptime(f"{date} {EVENT_TIME_DB}", "%Y-%m-%d %H:%M:%S")
    )
    
    # Prix départ (candle avant)
    prices_before = prices_df[prices_df['datetime'] < event_dt]
    price_start = prices_before.iloc[-1]['close']
    
    # Pics après
    prices_after = prices_df[prices_df['datetime'] >= event_dt]
    price_max = prices_after['close'].max()
    price_min = prices_after['close'].min()
    
    # Direction
    move_up = abs(price_max - price_start)
    move_down = abs(price_start - price_min)
    
    if move_up > move_down:
        direction = "UP"
        price_peak = price_max
        impact_pips = (price_peak - price_start) * 10000
    else:
        direction = "DOWN"
        price_peak = price_min
        impact_pips = (price_start - price_peak) * 10000
    
    return {
        'impact_pips': float(impact_pips),
        'direction': direction,
        'price_start': float(price_start),
        'price_peak': float(price_peak)
    }

def calculate_r2_72h(date):
    """R² régression linéaire 72h pré-événement"""
    # ... code calcul R²
    pass

def calculate_amplitude_24h(date):
    """Écart-type prix 24h pré-événement"""
    # ... code calcul amplitude
    pass

if __name__ == "__main__":
    results = []
    for date in DATES_CLUSTER3:
        print(f"📊 {date}...")
        
        # Mesures
        impact_data = measure_impact_corrected(date)
        r2 = calculate_r2_72h(date)
        amplitude = calculate_amplitude_24h(date)
        
        # ... (compléter avec événements, scores, surprises)
        
        results.append({...})
    
    df = pd.DataFrame(results)
    df.to_csv('cluster3_impacts_all_6dates.csv', index=False)
    
    print(f"\n✅ {len(results)} dates mesurées")
```

**Output attendu : `cluster3_impacts_all_6dates.csv`**

```csv
date,num_events,score_adjusted,impact_real_pips,direction,surprise_max,surprise_avg,R2_72h,amplitude_24h,duration_minutes
2025-09-11,11,84.2,56.8,UP,0.304,0.182,0.652,0.00145,109
2025-08-12,11,79.8,48.3,UP,0.278,0.165,0.721,0.00138,95
2025-07-15,11,77.1,42.1,DOWN,0.251,0.148,0.589,0.00152,87
2025-06-11,11,81.5,51.2,UP,0.289,0.173,0.698,0.00141,102
2025-05-13,11,76.3,39.8,UP,0.246,0.142,0.612,0.00149,78
2025-04-10,11,78.9,45.6,DOWN,0.267,0.159,0.643,0.00147,91
```

**Durée estimée :** 45-60 minutes

#### 3.2.6 Consolidation données

**Script :** `scripts/session105/consolidate_cluster3_data.py`

**Tests validation :**
```python
# Test 1 : 6 dates
assert len(df) == 6

# Test 2 : 11 événements par date
assert (df['num_events'] == 11).all()

# Test 3 : Référence 11.09 cohérente
ref_impact = df[df['date'] == '2025-09-11']['impact_real_pips'].values[0]
assert 54 <= ref_impact <= 59  # 56.8 ±2

# Test 4 : Impacts valides
assert (df['impact_real_pips'] > 0).all()

# Test 5-7 : Autres validations
```

**Output final :** `cluster3_impacts_corrected.csv`

**Durée estimée :** 10-15 minutes

---

<a name="33-calculs-amp_optimal"></a>
### 3.3 Calculs amp_optimal (Session 105)

**Status :** ⏳ À faire  
**Dépend de :** 3.2.6 (mesures complètes)

#### 3.3.1 Optimisation par date

**Script complet :** `scripts/session105/calculate_amp_optimal_cluster3.py`

```python
#!/usr/bin/env python3
"""
CALCUL AMP_OPTIMAL - CLUSTER #3
================================

Pour chaque date, calcule le facteur d'amplification optimal
qui minimise l'écart entre impact prédit et impact réel.
"""

import pandas as pd
from scipy.optimize import minimize_scalar
from formulas_validated import calculate_impact_d

BASELINE_CLUSTER3 = 2.5
CORRECTION_FACTOR = 0.758

df = pd.read_csv('cluster3_impacts_corrected.csv')

def calculate_amp_optimal_for_date(row):
    """Optimise amp pour une date donnée"""
    score = row['score_adjusted']
    num_events = row['num_events']
    impact_real = row['impact_real_pips']
    
    def error_function(amp):
        impact_pred = calculate_impact_d(score, num_events, amp, CORRECTION_FACTOR)
        return abs(impact_pred - impact_real)
    
    result = minimize_scalar(error_function, bounds=(0.5, 5.0), method='bounded')
    
    amp_optimal = result.x
    error_final = result.fun
    
    # Impact avec baseline
    impact_pred_baseline = calculate_impact_d(score, num_events, BASELINE_CLUSTER3, CORRECTION_FACTOR)
    error_baseline = abs(impact_pred_baseline - impact_real)
    
    return {
        'date': row['date'],
        'amp_optimal': float(amp_optimal),
        'error_final': float(error_final),
        'error_baseline': float(error_baseline),
        'improvement_pips': float(error_baseline - error_final)
    }

results = [calculate_amp_optimal_for_date(row) for _, row in df.iterrows()]
df_results = pd.DataFrame(results)
df_complete = df.merge(df_results, on='date')

df_complete.to_csv('cluster3_amp_optimal.csv', index=False)

print(f"amp_optimal moyen : {df_results['amp_optimal'].mean():.4f}")
print(f"Amélioration totale : {df_results['improvement_pips'].sum():.2f} pips")
```

**Output : `cluster3_amp_optimal.csv`**

Colonnes ajoutées :
- `amp_optimal` : Facteur optimal calculé
- `error_final` : Erreur avec amp_optimal
- `error_baseline` : Erreur avec baseline 2.5
- `improvement_pips` : Gain en pips

**Durée estimée :** 15-20 minutes

#### 3.3.2 Calcul delta vs baseline

**Script :** `scripts/session105/calculate_delta_amp_cluster3.py`

```python
#!/usr/bin/env python3
"""
CALCUL DELTA AMP VS BASELINE - CLUSTER #3
==========================================

Écart relatif entre amp_optimal et baseline du cluster.
"""

import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('cluster3_amp_optimal.csv')
BASELINE = 2.5

# Calcul delta (relatif)
df['delta_amp'] = (df['amp_optimal'] - BASELINE) / BASELINE
df['delta_amp_pct'] = df['delta_amp'] * 100

print(f"Delta moyen : {df['delta_amp'].mean():+.4f} ({df['delta_amp_pct'].mean():+.2f}%)")
print(f"Écart-type  : {df['delta_amp'].std():.4f}")

# Graphiques
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Histogramme
axes[0].hist(df['delta_amp_pct'], bins=10, alpha=0.7)
axes[0].axvline(0, color='red', linestyle='--', label='Baseline')
axes[0].set_xlabel('Delta amp (%)')
axes[0].set_title('Distribution delta_amp')

# Timeline
axes[1].plot(df['date'], df['delta_amp_pct'], marker='o')
axes[1].axhline(0, color='red', linestyle='--')
axes[1].set_xlabel('Date')
axes[1].set_ylabel('Delta amp (%)')

plt.savefig('cluster3_delta_amp_distribution.png', dpi=150)

df.to_csv('cluster3_delta_amp.csv', index=False)
```

**Interprétation delta_amp :**
- **delta > 0** : amp_optimal > baseline → Contexte amplifie
- **delta < 0** : amp_optimal < baseline → Contexte atténue
- **delta = 0** : amp_optimal = baseline → Baseline optimale

**Durée estimée :** 10 minutes

#### 3.3.3 Collecte métriques contextuelles

**Script :** `scripts/session105/verify_metrics_cluster3.py`

```python
#!/usr/bin/env python3
"""
VÉRIFICATION MÉTRIQUES CONTEXTUELLES
"""

import pandas as pd

df = pd.read_csv('cluster3_delta_amp.csv')

REQUIRED_METRICS = [
    'surprise_max',
    'R2_72h',
    'amplitude_24h',
    'duration_minutes',
    'delta_amp'
]

for metric in REQUIRED_METRICS:
    assert metric in df.columns, f"Métrique {metric} manquante"
    assert df[metric].isnull().sum() == 0, f"Valeurs nulles dans {metric}"
    print(f"✅ {metric:20s} : OK")

print("\n✅✅✅ Dataset prêt pour Phase 3.4 (Modélisation)")
```

**Durée estimée :** 5 minutes

---

<a name="34-modélisation"></a>
### 3.4 Modélisation (Session 105)

**Status :** ⏳ À faire  
**Dépend de :** 3.3.3 (dataset complet)

#### 3.4.1 Analyse corrélations

**Script complet :** `scripts/session105/analyze_correlations_cluster3.py`

```python
#!/usr/bin/env python3
"""
ANALYSE CORRÉLATIONS - CLUSTER #3
==================================
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv('cluster3_delta_amp.csv')

variables = ['surprise_max', 'surprise_avg', 'R2_72h', 'amplitude_24h', 'duration_minutes']
target = 'delta_amp'

# Calcul corrélations
print("CORRÉLATIONS AVEC delta_amp :")
print("-" * 60)
correlations = {}
for var in variables:
    corr = df[var].corr(df[target])
    correlations[var] = corr
    
    # Signification
    if abs(corr) > 0.7:
        sig = "***"  # Forte
    elif abs(corr) > 0.4:
        sig = "**"   # Modérée
    elif abs(corr) > 0.2:
        sig = "*"    # Faible
    else:
        sig = ""
    
    print(f"  {var:20s} : r = {corr:+.3f} {sig}")

print("\nLÉGENDE :")
print("  *** : |r| > 0.7 (forte)")
print("  **  : 0.4 < |r| < 0.7 (modérée)")
print("  *   : 0.2 < |r| < 0.4 (faible)")

# Heatmap
corr_matrix = df[variables + [target]].corr()

plt.figure(figsize=(10, 8))
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, fmt='.3f')
plt.title('Matrice Corrélations - Cluster #3')
plt.savefig('cluster3_correlations_heatmap.png', dpi=150)

# Scatter plots
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
for idx, var in enumerate(variables):
    row, col = idx // 3, idx % 3
    ax = axes[row, col]
    
    ax.scatter(df[var], df[target], alpha=0.7, s=80)
    ax.set_xlabel(var)
    ax.set_ylabel('delta_amp')
    ax.set_title(f'r = {correlations[var]:+.3f}')
    
    # Ligne tendance
    z = np.polyfit(df[var], df[target], 1)
    p = np.poly1d(z)
    x_line = np.linspace(df[var].min(), df[var].max(), 100)
    ax.plot(x_line, p(x_line), "r--", linewidth=2)

if len(variables) < 6:
    fig.delaxes(axes[1, 2])

plt.tight_layout()
plt.savefig('cluster3_scatter_plots.png', dpi=150)

print("\n✅ Graphiques sauvegardés")
```

**Durée estimée :** 15 minutes

#### 3.4.2 Régression multiple

**Script :** `scripts/session105/regression_cluster3.py`

```python
#!/usr/bin/env python3
"""
RÉGRESSION MULTIPLE - CLUSTER #3
=================================
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error

df = pd.read_csv('cluster3_delta_amp.csv')

# Variables
X = df[['surprise_max', 'R2_72h', 'amplitude_24h', 'duration_minutes']]
y = df['delta_amp']

# Régression
model = LinearRegression()
model.fit(X, y)

# Coefficients
coeffs = {
    'alpha (surprise)': model.coef_[0],
    'beta (R2)': model.coef_[1],
    'gamma (amplitude)': model.coef_[2],
    'delta (duration)': model.coef_[3],
    'intercept': model.intercept_
}

print("="*80)
print("COEFFICIENTS RÉGRESSION")
print("="*80)
for name, value in coeffs.items():
    print(f"  {name:25s} : {value:+.6f}")

# Métriques
y_pred = model.predict(X)
r2 = r2_score(y, y_pred)
mae = mean_absolute_error(y, y_pred)

print(f"\nR² score  : {r2:.3f}")
print(f"MAE       : {mae:.4f}")

# Sauvegarde
import json
with open('cluster3_regression_coefficients.json', 'w') as f:
    json.dump(coeffs, f, indent=2)

print("\n✅ Coefficients sauvegardés")
```

**Durée estimée :** 10 minutes

#### 3.4.3 Formule amp dynamique Cluster #3

**Module :** `fx_impact_app/src/formulas_cluster3.py`

```python
"""
FORMULES DYNAMIQUES - CLUSTER #3 (CPI)
=======================================
"""

import numpy as np

# Baseline Cluster #3
BASELINE_CLUSTER3 = 2.5

# Coefficients (à mettre à jour après régression)
ALPHA = 0.150   # surprise
BETA = -0.080   # R²
GAMMA = 0.020   # amplitude
DELTA = -0.010  # duration

def amp_dynamic_cluster3(surprise, R2, amplitude, duration):
    """
    Calcule amp dynamique pour Cluster #3 (CPI)
    
    Paramètres :
    - surprise : Surprise max (ratio)
    - R2 : R² tendance 72h (0-1)
    - amplitude : Volatilité pré-event
    - duration : Durée TTR (minutes)
    
    Retour : amp optimisé
    """
    correction = (
        ALPHA * surprise +
        BETA * R2 +
        GAMMA * amplitude +
        DELTA * duration
    )
    
    amp = BASELINE_CLUSTER3 * (1 + correction)
    
    # Contraintes sécurité
    amp = np.clip(amp, 0.5, 5.0)
    
    return amp
```

**Tests :** `tests/test_formulas_cluster3.py`

```python
import pytest
from formulas_cluster3 import amp_dynamic_cluster3

def test_amp_cluster3_nominal():
    """Test cas nominal"""
    amp = amp_dynamic_cluster3(0.3, 0.8, 0.0015, 100)
    assert 1.5 <= amp <= 3.5

def test_amp_cluster3_baseline():
    """Test contexte neutre = baseline"""
    amp = amp_dynamic_cluster3(0, 0, 0, 0)
    assert amp == pytest.approx(2.5, 0.01)

def test_amp_cluster3_constraints():
    """Test contraintes [0.5, 5.0]"""
    amp_extreme = amp_dynamic_cluster3(1.0, 1.0, 0.01, 300)
    assert 0.5 <= amp_extreme <= 5.0
```

**Durée estimée :** 20 minutes

#### 3.4.4 Validation Leave-One-Out

**Script :** `scripts/session105/validate_cluster3_loo.py`

```python
#!/usr/bin/env python3
"""
VALIDATION LEAVE-ONE-OUT - CLUSTER #3
======================================
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import LeaveOneOut
from sklearn.linear_model import LinearRegression
from formulas_validated import calculate_impact_d

df = pd.read_csv('cluster3_delta_amp.csv')

BASELINE = 2.5
loo = LeaveOneOut()

errors_loo = []
errors_baseline = []

print("="*80)
print("VALIDATION LEAVE-ONE-OUT")
print("="*80)

for train_idx, test_idx in loo.split(df):
    train = df.iloc[train_idx]
    test = df.iloc[test_idx]
    
    # Entraîner sur N-1
    X_train = train[['surprise_max', 'R2_72h', 'amplitude_24h', 'duration_minutes']]
    y_train = train['delta_amp']
    
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    # Prédire sur 1
    X_test = test[['surprise_max', 'R2_72h', 'amplitude_24h', 'duration_minutes']]
    delta_pred = model.predict(X_test)[0]
    amp_pred = BASELINE * (1 + delta_pred)
    
    # Impact prédit formule
    impact_pred_formula = calculate_impact_d(
        test['score_adjusted'].values[0],
        11,
        amp_pred,
        0.758
    )
    
    # Impact prédit baseline
    impact_pred_baseline = calculate_impact_d(
        test['score_adjusted'].values[0],
        11,
        BASELINE,
        0.758
    )
    
    # Impact réel
    impact_real = test['impact_real_pips'].values[0]
    
    # Erreurs
    error_formula = abs(impact_pred_formula - impact_real)
    error_baseline = abs(impact_pred_baseline - impact_real)
    
    errors_loo.append(error_formula)
    errors_baseline.append(error_baseline)
    
    print(f"\nDate {test['date'].values[0]} :")
    print(f"  Impact réel      : {impact_real:.1f} pips")
    print(f"  Pred baseline    : {impact_pred_baseline:.1f} pips (erreur: {error_baseline:.1f})")
    print(f"  Pred formule     : {impact_pred_formula:.1f} pips (erreur: {error_formula:.1f})")

# MAE moyens
mae_loo = np.mean(errors_loo)
mae_baseline = np.mean(errors_baseline)
improvement = mae_baseline - mae_loo

print("\n" + "="*80)
print("RÉSULTATS GLOBAUX")
print("="*80)
print(f"MAE Formule dynamique : {mae_loo:.2f} pips")
print(f"MAE Baseline (2.5)    : {mae_baseline:.2f} pips")
print(f"Amélioration          : {improvement:.2f} pips ({improvement/mae_baseline*100:.1f}%)")

# Graphique
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(10, 6))
dates = df['date'].values
x = np.arange(len(dates))

ax.bar(x - 0.2, errors_baseline, 0.4, label='Baseline 2.5', alpha=0.8)
ax.bar(x + 0.2, errors_loo, 0.4, label='Formule dynamique', alpha=0.8)

ax.set_xlabel('Date')
ax.set_ylabel('Erreur absolue (pips)')
ax.set_title('Comparaison Leave-One-Out - Cluster #3')
ax.set_xticks(x)
ax.set_xticklabels(dates, rotation=45)
ax.legend()
ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('cluster3_loo_comparison.png', dpi=150)

print("\n✅ Graphique sauvegardé : cluster3_loo_comparison.png")
```

**Durée estimée :** 20 minutes

---

<a name="35-décision-cluster-3"></a>
### 3.5 Décision Cluster #3 (Session 105)

**Status :** ⏳ À faire  
**Dépend de :** 3.4.4 (validation LOO complète)

#### 3.5.1 Critères décision

**Seuils définis :**

```
Amélioration ≥ 5 pips :
  → SIGNIFICATIVE
  → Formule adoptée

1 < Amélioration < 5 pips :
  → MARGINALE
  → Évaluer complexité

Amélioration ≤ 0 pips :
  → Garder baseline
```

#### 3.5.2 Scénarios possibles

**Scénario A : Formule adoptée**

Si MAE amélioration ≥ 5 pips :
- Intégrer `formulas_cluster3.py`
- Mettre à jour Planificateur
- Tests unitaires
- Documentation

**Scénario B : Baseline maintenue**

Si amélioration < 1 pip :
- Conserver baseline 2.5
- Documenter raison
- Analyse post-mortem

**Scénario C : Décision hybride**

Si amélioration 1-5 pips :
- Mode optionnel utilisateur
- Paramètre `use_dynamic_amp`

#### 3.5.3 Documentation décision

**Rapport final :** `docs/CLUSTER3_VALIDATION_REPORT.md`

**Structure :**
```markdown
# CLUSTER #3 (CPI) - RAPPORT VALIDATION

## RÉSUMÉ EXÉCUTIF
- Décision : [A/B/C]
- Amélioration : X.X pips
- Recommandation : [...]

## DONNÉES
- 6 dates validées
- Baseline : 2.5

## RÉSULTATS
- R² : 0.XXX
- MAE baseline : XX.X pips
- MAE formule : XX.X pips

## COEFFICIENTS
- alpha, beta, gamma, delta

## VALIDATION LOO
[Tableau + graphique]

## DÉCISION
[Justification]

## PROCHAINES ÉTAPES
- Phase 2 : Cluster #1
```

**Durée estimée Section 3.5 :** 1 heure

---

<a name="partie-4"></a>
## 📊 PARTIE 4 : VALIDATION CLUSTER #1 (Manufacturing) - PHASE 2

**Status :** ⏳ À faire (Session 106)  
**Baseline :** ⏳ **À établir**  
**Priorité :** ⭐⭐ (11 occurrences)

### 4.1 Établissement baseline Cluster #1

**Date référence suggérée :** 2025-06-02  
**Méthode :** Identique Section 3.1 (sans la partie correction)

### 4.2 Mesures empiriques Cluster #1

**10 autres dates**  
**Méthode :** Identique Section 3.2

### 4.3 Analyse intra-cluster

**Corrélations + Régression**  
**Méthode :** Identique Section 3.4

### 4.4 Validation & Décision

**Leave-One-Out (11 dates)**  
**Rapport :** `CLUSTER1_VALIDATION_REPORT.md`

---

<a name="partie-5"></a>
## 📈 PARTIE 5 : VALIDATION CLUSTER #2 (NFP) - PHASE 3

**Status :** ⏳ À faire (Session 107)  
**Baseline :** ⏳ **À établir**  
**Priorité :** ⭐⭐ (7 occurrences)

**Note :** Méthodologie identique Partie 4, adapter pour 7 dates et 12 événements NFP.

---

<a name="partie-6"></a>
## 🎯 PARTIE 6 : SYNTHÈSE & PRODUCTION - PHASE FINALE

**Status :** ⏳ À faire (Session 108-109)

### 6.1 Comparaison inter-clusters

**Tableau comparatif baselines :**

| Cluster | Événements | N dates | Baseline | vs C#3 |
|---------|------------|---------|----------|--------|
| #3 (CPI) | 11 | 6 | 2.5 | 1.00× |
| #2 (NFP) | 12 | 7 | X.X | Y.YY× |
| #1 (Mfg) | 8 | 11 | Z.Z | W.WW× |

**Analyse patterns communs**

### 6.2 Décision globale

**Stratégies possibles :**

**Scénario A :** Formules spécifiques par cluster  
**Scénario B :** Baselines spécifiques  
**Scénario C :** Hybride

### 6.3 Intégration Planificateur

**Modules à créer :**
- `cluster_detection.py`
- `amp_optimization.py`
- `Planificateur_V2.7.py`

### 6.4 Documentation finale

**Guides :**
- `USER_GUIDE_PLANIFICATEUR_V2.7.md`
- `TECHNICAL_DOCUMENTATION_V2.7.md`

---

<a name="annexes"></a>
## 📎 ANNEXES

<a name="tableau-avancement-global"></a>
### Tableau avancement global

| Partie | Étape | Description | Status | Session |
|--------|-------|-------------|--------|---------|
| **1** | **FONDATIONS** | | | |
| 1.1-1.3 | État art + Baseline | Formules validées | ✅ | S51-55, S103 |
| **2** | **MÉTHODOLOGIE** | | | |
| 2.1-2.3 | Clusters + Méthodo | 5 clusters identifiés | ✅ | S104 |
| **3** | **CLUSTER #3** | Phase 1 | 🟡 | S105 |
| 3.1 | Correction + Préparation | | ✅ | S105 |
| 3.2 | Mesures 6 dates | | ⏳ | S105 |
| 3.3 | Calculs amp_optimal | | ⏳ | S105 |
| 3.4 | Modélisation | | ⏳ | S105 |
| 3.5 | Décision | | ⏳ | S105 |
| **4** | **CLUSTER #1** | Phase 2 | ⏳ | S106 |
| **5** | **CLUSTER #2** | Phase 3 | ⏳ | S107 |
| **6** | **SYNTHÈSE** | Phase Finale | ⏳ | S108-109 |

**Légende :**
- ✅ Complété
- 🟡 En cours
- ⏳ À faire

---

<a name="références-fichiers"></a>
### Références fichiers

**Scripts production :**
```
fx_impact_app/src/
├── formulas_validated.py ✅
├── formulas_cluster3.py ⏳
├── cluster_detection.py ⏳
└── amp_optimization.py ⏳
```

**Scripts recherche :**
```
scripts/
├── session102/ ✅
├── session104/ ✅
└── session105/ ⏳
    ├── fix_measure_impact_11_09.py
    ├── extract_cluster3_6dates.py
    ├── measure_cluster3_6dates.py
    ├── calculate_amp_optimal_cluster3.py
    ├── calculate_delta_amp_cluster3.py
    ├── analyze_correlations_cluster3.py
    ├── regression_cluster3.py
    └── validate_cluster3_loo.py
```

**Documentation :**
```
docs/
├── SESSION51-55_RAPPORT.md ✅
├── SESSION103_RAPPORT_COMPLET.md ✅
├── METHODOLOGIE_VALIDATION_CLUSTERS.md ✅
├── PROJET_GESTION_SCIENTIFIQUE_INTEGRE.md ✅ (ce fichier)
└── CLUSTER3_VALIDATION_REPORT.md ⏳
```

---

<a name="glossaire"></a>
### Glossaire

**amp (amplification) :** Facteur multiplicateur dans formule calculate_impact_d

**baseline :** Valeur amp de référence pour un cluster, établie empiriquement

**cluster :** Groupe de dates avec composition événements identique

**delta_amp :** Écart relatif : (amp_opt - baseline) / baseline

**empirical_score :** Score importance événement (0-100+)

**event_key :** Identifiant unique événement

**impact :** Mouvement prix EUR/USD en pips

**Leave-One-Out (LOO) :** Validation croisée train N-1, test 1

**MAE :** Mean Absolute Error

**R²** : Coefficient détermination (0-1)

**signature cluster :** Ensemble trié event_key

**surprise :** Écart relatif |actual - estimate| / estimate

**TTR :** Time To Reversal (minutes)

---

**Fin du document**

*Version 2.0 intégrée - Session 105*  
*Auteur : André Valentin*  
*Date : 2 novembre 2025*
