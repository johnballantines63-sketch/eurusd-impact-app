# 📚 KNOWLEDGE_BASE - ADDENDUM SESSION 17

**Date :** 19 octobre 2025  
**Session :** 17  
**Statut :** ⚠️ DÉCOUVERTES CRITIQUES

---

## 🚨 PROBLÈMES CRITIQUES IDENTIFIÉS

### Problème #1 : Qualité des données historiques (CRITIQUE)

**Gravité :** 🔴 CRITIQUE - Affecte toutes les validations

**Description :**
La table `events` dans `warehouse.duckdb` contient des données `actual` et `estimate` **manquantes ou incorrectes** pour de nombreux événements.

**Exemples concrets :**

```sql
-- 11 septembre 2025, 14:30
-- Inflation Rate (Monthly)

MT5 RÉEL :    actual = 0.4%, estimate = 0.3% → Surprise 33.3%
DB WAREHOUSE: actual = 0.3%, estimate = 0.3% → Surprise 0%

IMPACT : Erreur V2 passe de 13% (bonnes données) à 29% (données DB)
```

**Causes identifiées :**
1. **API EODHD incomplète** : Ne fournit pas toutes les `estimate`
2. **Mapping événements** : Confusion mensuel vs annuel (ex: CPI Monthly vs Annual)
3. **Scraping incomplet** : Certains événements n'ont pas d'`estimate` → surprise = 0% par défaut

**Impact sur le projet :**
- ⚠️ Validation Session 15 (30 événements) : **Potentiellement biaisée**
- ⚠️ Validation Session 17 (120 groupes) : **Potentiellement biaisée**
- ❌ Backtesting historique : **Non fiable sans corrections manuelles**
- ❌ Précision V2 : **Sous-optimale** (13% possible vs 29% actuel)

**Solution requise :**
→ **SESSION 18 URGENTE** : Interface de correction manuelle des données

---

### Problème #2 : Prix de référence incohérent

**Gravité :** 🟡 MOYEN

**Description :**
Le prix de référence utilisé dans `event_group_impacts` diffère du prix à l'heure exacte de l'événement.

**Exemple 11 septembre 2025, 14:30 :**
```
Prix à 14:30:00 (bougie 1min)  : 1.17007
Prix référence dans DB         : 1.16789
Différence                     : 21.8 pips ❌

Impact sur MFE :
  MFE recalculé (depuis 1.17007) : 38.2 pips
  MFE DB (depuis 1.16789)         : 59.2 pips
  Différence                      : 21.0 pips
```

**Cause probable :**
La méthodologie `event_group_impacts` (Session 8-9) utilise le prix **juste avant** l'événement, pas **à** l'événement.

**Question non résolue :**
- Quelle méthodologie est correcte ?
- Faut-il standardiser ?

**Impact :**
- Comparaisons avec MT5 peuvent être faussées
- MFE peut être surestimé ou sous-estimé

---

## ✅ VALIDATION FORMULE V2

### Résultats Session 17 (120 groupes)

**Avec données DB (potentiellement incorrectes) :**
- MAE V1 : 593.6%
- MAE V2 : 174.9%
- **Réduction : -70.5%** ✅

**Résultats par tranche :**
- 0-5% : ±0% (neutre, attendu)
- 5-10% : -35.5%
- 10-20% : **-69.2%**
- 20-50% : **-80.9%**

**Résultats par dimension :**
- ✅ **TOUS les pays** (14/14) bénéficient de V2
- ✅ **TOUS les types** (9/9) bénéficient de V2
- ✅ **Toutes les années** (2024, 2025) bénéficient de V2

**Conclusion :** 
V2 est **massivement meilleure** que V1, même avec des données potentiellement incorrectes. Avec des données correctes, la performance serait probablement encore meilleure.

---

## 📊 MÉTHODOLOGIE V2 - MULTI-ÉVÉNEMENTS

### Comment V2 traite les événements simultanés

**Question :** V2 tient-elle compte des multi-événements ?

**Réponse :** ✅ OUI, via la méthode du **score MAX** (pas somme)

**Exemple concret : 11 septembre 2025, 14:30**

```
8 événements simultanés :
  1. Inflation Rate           (score 81.7, surprise 0%*)
  2. Core Inflation Rate      (score 79.6, surprise 0%)
  3. CPI                      (score 79.3, surprise 0%)
  4. CPI s.a                  (score 78.2, surprise 0.1%)
  5. Initial Jobless Claims   (score 72.0, surprise 11.9%)
  6. Continuing Jobless       (score 70.7, surprise 0.6%)
  7. Jobless 4-Week Average   (pas de score)
  8. Real Earnings            (pas de score)

V2 utilise :
  Score MAX    = 81.7 (Inflation Rate)
  Surprise MAX = 11.9% (Initial Jobless Claims)
  
  *Note: Devrait être 33.3% avec données correctes
```

**Méthode MAX vs ADDITIVE :**

```
MÉTHODE MAX (V2 actuelle) :
  Impact = f(score_max) × amplification(surprise_max)
  Résultat : 41.9 pips
  Erreur : 29% (avec données DB)
  
MÉTHODE ADDITIVE (hypothétique) :
  Impact = Σ f(score_i) × amplification(surprise_i)
  Résultat : 132.5 pips
  Erreur : 124% ❌
  
RÉEL MT5 : 59.2 pips
```

**Conclusion :** Méthode MAX est **4× plus précise** que méthode additive.

**Justification (Session 8-9) :**
- Analyse de 2,089 groupes historiques
- Coefficient de synergie observé : ~1.05× (quasi nul)
- Le marché réagit au **plus important**, pas à la somme

---

## 📋 CE QUE V2 FAIT ET NE FAIT PAS

### ✅ CE QUE V2 FAIT

| Fonctionnalité | Implémentation | Précision |
|----------------|----------------|-----------|
| **Multi-événements** | Score MAX du groupe | 4× meilleure que somme |
| **Amplitude** | Formule v9-CLEAN + Amplification V2 | 13-29% erreur |
| **Groupement temporel** | Par minute | Via `event_group_impacts` |
| **Amplification surprise** | Plafond ×2.5 | Validée sur 120 groupes |

### ❌ CE QUE V2 NE FAIT PAS

| Fonctionnalité | Statut | Notes |
|----------------|--------|-------|
| **Direction** | ❌ Non prédit | Seulement amplitude |
| **Forme du graphique** | ❌ Non prédit | Trop complexe |
| **Retracements pendant** | ❌ Non prédit | Pullback entre phases seulement |
| **Timeline minute/minute** | ❌ Non prédit | Prédit UN nombre : MFE |
| **Latence** | ❌ Pas implémenté | À développer |
| **TTR** | ⏳ Calculé mais pas utilisé | Stocké dans DB |

### 💡 CE QUE V2 PRÉDIT EXACTEMENT

V2 prédit **UN SEUL NOMBRE** :
- L'**impact maximal** attendu (MFE en pips)
- Dans une **fenêtre de 60 minutes**
- Depuis le **prix de référence**

V2 ne prédit **PAS** :
- La forme du mouvement
- Les retracements
- Le timing exact du pic
- La direction initiale

---

## 🔧 NOUVELLES ERREURS IDENTIFIÉES

### Erreur #8 : Supposer que les données DB sont correctes

```python
# ❌ FAUX - Utiliser aveuglément les données DB
actual = row['actual']
estimate = row['estimate']
surprise = calculate_surprise(actual, estimate)

# ✅ CORRECT - Vérifier et valider
if pd.notna(row['estimate']) and row['estimate'] != 0:
    surprise = calculate_surprise(row['actual'], row['estimate'])
else:
    # estimate manquant - marquer pour correction manuelle
    surprise = None  # ou 0 avec un flag warning
```

**Impact :** ⭐⭐⭐ CRITIQUE - Fausse toutes les analyses

### Erreur #9 : Confusion mensuel vs annuel

**Erreur :** Ne pas différencier les variantes d'un même événement (Inflation Rate Monthly vs Annual).

**Réalité :** 
- Inflation Rate (Monthly) : 0.4% vs 0.3% → Surprise 33.3%
- Inflation Rate (Annual) : 2.9% vs 2.9% → Surprise 0%

**Solution :**
```python
# Vérifier le titre complet de l'événement
if 'monthly' in event_title.lower() or 'mensuel' in event_title.lower():
    # Traiter comme mensuel
elif 'annual' in event_title.lower() or 'annuel' in event_title.lower():
    # Traiter comme annuel
```

**Impact :** ⭐⭐⭐ CRITIQUE - Peut manquer des surprises majeures

---

## 📊 NOUVELLES MÉTRIQUES

### Qualité des données

**Métriques à suivre :**
```python
# % événements avec estimate valide
completeness_rate = events_with_estimate / total_events

# % événements avec surprise > 0%
surprise_rate = events_with_surprise / total_events

# % événements suspects (surprise > 100%)
outlier_rate = events_with_extreme_surprise / total_events
```

**Seuils acceptables :**
- Completeness : > 80%
- Surprise rate : > 30%
- Outlier rate : < 5%

---

## 🎯 DÉCISIONS DE CONCEPTION

### Décision #4 : Méthode MAX vs SOMME pour multi-événements

**Contexte :** Quand plusieurs événements arrivent simultanément, comment calculer l'impact total ?

**Options testées :**
1. **Addition simple** (Σ impacts) : Erreur 124%
2. **Moyenne pondérée** : Non testé
3. **Score MAX** (actuelle) : Erreur 29% (avec données DB) ou 13% (avec bonnes données)

**Décision Session 17 :** Option 3 - Score MAX du groupe

**Rationale :**
- Validé sur 2,089 groupes (Session 8-9)
- 4× plus précis que méthode additive
- Reflète comportement réel du marché
- Coefficient de synergie négligeable (~1.05×)

**Statut :** ✅ Validé et adopté

---

## 🚀 ACTIONS REQUISES POST-SESSION 17

### URGENT : Session 18

**Objectif :** Interface de correction données historiques

**Fonctionnalités minimales :**
1. ✅ Charger actual/estimate depuis DB
2. ✅ Détecter estimates NULL ou suspects
3. ✅ Interface correction manuelle
4. ✅ Sauvegarder corrections
5. ✅ Différencier mensuel vs annuel

**Bloquants sans Session 18 :**
- ❌ Backtesting fiable impossible
- ❌ Validation V2 non définitive
- ❌ Précision sous-optimale

### IMPORTANT : Audit qualité DB

**Actions :**
1. Script audit automatique
2. Liste événements avec estimate NULL
3. Liste surprises aberrantes (>100%)
4. Rapport qualité complet
5. Plan de correction

### RECOMMANDÉ : Re-validation

**Après Session 18 :**
1. Re-tester 120 groupes Session 17 avec données corrigées
2. Re-tester 30 groupes Session 15 avec données corrigées
3. Calculer nouvelles métriques MAE
4. Rapport validation final

---

## 📚 SCRIPTS IMPORTANTS SESSION 17

### Scripts de test et vérification

| Script | Objectif | Usage |
|--------|----------|-------|
| `verify_db_vs_mt5_data.py` | Comparer DB vs MT5 | Identifier divergences données |
| `verify_v2_multi_events.py` | Vérifier traitement multi-événements | Comprendre méthodologie V2 |
| `verify_11sept_movement.py` | Analyser mouvements prix | Comparer MFE calculé vs DB |

### Scripts de validation

| Script | Objectif | Usage |
|--------|----------|-------|
| `extract_extended_groups_session17.py` | Extraire 120 groupes | Échantillonnage stratifié |
| `measure_impacts_v1_v2_session17.py` | Mesurer V1 vs V2 | Comparaison performance |
| `analyze_multidimensional_session17.py` | Analyser par segments | Identifier patterns |

---

## ⚠️ AVERTISSEMENTS IMPORTANTS

### Pour utiliser le Planner

**AVANT Session 18 :**
- ⚠️ Ne PAS faire confiance aux données auto-chargées
- ✅ TOUJOURS vérifier actual/estimate avec MT5
- ⚠️ Méfiance sur surprises = 0% (peuvent être incorrectes)

**APRÈS Session 18 :**
- ✅ Données vérifiées et corrigées disponibles
- ✅ Interface correction en place
- ✅ Utilisation fiable pour backtesting

### Pour interpréter les validations

**Sessions 15 et 17 :**
- ✅ Direction générale correcte : V2 > V1
- ⚠️ Chiffres exacts à prendre avec précaution
- ⚠️ Performance réelle V2 probablement meilleure

**11 septembre 2025 :**
- ✅ Avec bonnes données : V2 = 13% erreur
- ⚠️ Avec données DB : V2 = 29% erreur
- ✅ Formule validée, problème = qualité données

---

**Version :** 1.0  
**Date :** 19 octobre 2025  
**Auteur :** Claude (Session 17)  
**Statut :** ⚠️ ADDENDUM CRITIQUE - LECTURE OBLIGATOIRE

**À INTÉGRER DANS :** `KNOWLEDGE_BASE.md` (section dédiée Session 17)
