# REF-004 : COMPARAISON SCORES EMPIRIQUES CALCULÉS vs DB ACTUELLE

**Référence :** REF-004  
**Date de création :** 2025-12-06  
**Heure de création :** 12:05:00  
**Auteur :** André Valentin avec Claude  
**Version :** 1.0

---

## 📋 OBJECTIF

Comparer les scores empiriques calculés depuis Finnhub avec ceux actuellement stockés dans la DB pour identifier les écarts et valider la nécessité d'un recalcul complet.

---

## 📊 RÉSULTATS DE LA COMPARAISON

### Données Comparées

- **Période** : 2024-01-01 à 2024-12-31 ⚠️ **SEULEMENT 2024**
- **Pays** : US
- **⚠️ IMPORTANT** : Cette comparaison ne couvre que 2024, pas toutes les années (2020-2025)
- **Total événements dans DB actuelle** : 860
- **Total événements calculés** : 255
- **Événements présents dans les deux** : 253

### Statistiques Générales des Écarts

**Écarts absolus (Calculé - Actuel) :**
- **Écart moyen** : +1.82 pips
- **Écart médian** : +1.25 pips

**Écarts relatifs (%) :**
- **Écart moyen** : +8.5%
- **Écart médian** : +3.6%

**Conclusion** : Les scores calculés sont en moyenne **légèrement plus élevés** que ceux de la DB actuelle, mais l'écart médian est faible (3.6%).

---

## 🔍 ANALYSE DÉTAILLÉE

### Top 10 Écarts Positifs (Calculé > Actuel)

| Event Key | Actuel | Calculé | Écart | Écart % |
|-----------|--------|---------|-------|---------|
| building permits mom final | 19.00 | 44.13 | +25.12 | +132.2% |
| building permits final | 19.14 | 44.13 | +24.99 | +130.6% |
| mba mortgage applications | 15.16 | 34.99 | +19.83 | +130.8% |
| mba purchase index | 15.39 | 34.99 | +19.61 | +127.4% |
| mba 30year mortgage rate | 15.53 | 34.99 | +19.46 | +125.3% |
| mba mortgage market index | 15.53 | 34.99 | +19.46 | +125.3% |
| mba mortgage refinance index | 15.53 | 34.99 | +19.46 | +125.3% |
| nonfarm productivity qoq prel | 23.36 | 39.55 | +16.20 | +69.3% |
| unit labour costs qoq prel | 23.36 | 39.55 | +16.20 | +69.3% |
| balance of trade | 22.53 | 36.96 | +14.43 | +64.1% |

**Observations :**
- **Building Permits** : Écarts très élevés (+130%+) - Scores actuels probablement sous-estimés
- **MBA Mortgage** : Écarts élevés (+125%+) - Groupe d'événements cohérent
- **Productivity/Labour Costs** : Écarts modérés (+69%) - Scores actuels peut-être obsolètes

### Top 10 Écarts Négatifs (Calculé < Actuel)

| Event Key | Actuel | Calculé | Écart | Écart % |
|-----------|--------|---------|-------|---------|
| fed press conference | 60.40 | 42.08 | -18.33 | -30.3% |
| fed collins speech | 27.72 | 12.15 | -15.57 | -56.2% |
| fed interest rate decision | 61.23 | 47.26 | -13.98 | -22.8% |
| jolts job quits | 35.57 | 22.46 | -13.10 | -36.8% |
| jolts job openings | 34.22 | 22.46 | -11.76 | -34.4% |
| ny fed treasury purchases 45 to 7 yrs | 19.08 | 8.41 | -10.66 | -55.9% |
| fed schmid speech | 17.55 | 7.33 | -10.22 | -58.2% |
| fed mester speech | 19.36 | 9.78 | -9.57 | -49.5% |
| fed chair powell testimony | 27.71 | 19.12 | -8.59 | -31.0% |
| 10year note auction | 17.81 | 9.46 | -8.35 | -46.9% |

**Observations :**
- **Fed Events** : Scores actuels plus élevés que calculés
  - Fed Press Conference : -30.3%
  - Fed Interest Rate Decision : -22.8%
  - Fed Speeches : -50% à -60%
- **JOLTS** : Scores actuels plus élevés (-35% à -37%)
- **Auctions** : Scores actuels plus élevés (-47%)

**Hypothèse** : Les scores actuels pour les événements Fed peuvent être basés sur une période différente ou une méthode de calcul différente.

---

## 📈 INTERPRÉTATION DES RÉSULTATS

### Événements avec Écarts Significatifs

**Écarts > 20 pips ou > 50% :**
- **Building Permits** : +25 pips (+130%) - Probablement sous-estimés dans DB actuelle
- **MBA Mortgage** : +19 pips (+125%) - Groupe cohérent, probablement sous-estimés
- **Fed Events** : -10 à -18 pips (-30% à -60%) - Scores actuels peut-être sur-estimés ou basés sur période différente

### Événements avec Écarts Faibles

**Écarts < 5 pips et < 20% :**
- La majorité des événements (environ 70%) ont des écarts faibles
- Cela suggère que les scores actuels sont globalement cohérents pour la plupart des événements

---

## ⚠️ PROBLÈMES IDENTIFIÉS

### 1. Événements Sous-Estimés dans DB Actuelle

- **Building Permits** : Scores actuels ~19, calculés ~44 (+130%)
- **MBA Mortgage** : Scores actuels ~15, calculés ~35 (+125%)
- **Impact** : Ces événements peuvent être ignorés ou sous-pondérés dans les prédictions

### 2. Événements Sur-Estimés dans DB Actuelle

- **Fed Events** : Scores actuels ~60, calculés ~42 (-30%)
- **Fed Speeches** : Scores actuels ~18-28, calculés ~7-19 (-50% à -60%)
- **Impact** : Ces événements peuvent être sur-pondérés dans les prédictions

### 3. Événements Manquants

- **607 événements** dans DB actuelle non recalculés (860 - 253)
- **2 événements** calculés non présents dans DB actuelle
- **Impact** : Certains événements peuvent avoir des scores obsolètes ou manquants

---

## ✅ RECOMMANDATIONS

### Action Immédiate (Priorité HAUTE)

1. **⏳ À FAIRE** : Recalculer les scores pour les événements avec écarts > 20 pips ou > 50%
   - Building Permits
   - MBA Mortgage
   - Fed Events (vérifier méthode de calcul)

2. **⏳ À FAIRE** : Investiguer les écarts Fed Events
   - Pourquoi les scores calculés sont-ils plus bas ?
   - Méthode de calcul différente ?
   - Période de référence différente ?

3. **⏳ À FAIRE** : Recalculer tous les événements manquants
   - 607 événements dans DB actuelle non recalculés
   - S'assurer que tous les événements ont des scores à jour

### Actions Futures

1. Automatiser le recalcul périodique (mensuel ?)
2. Créer un système d'alerte pour écarts significatifs
3. Documenter la méthode de calcul pour chaque type d'événement

---

## 📝 NOTES

- Cette comparaison a été effectuée sur la période 2024 uniquement
- Un recalcul complet (2020-2025) pourrait révéler d'autres écarts
- Les écarts pour Fed Events nécessitent une investigation approfondie

---

## 🔗 RÉFÉRENCES

- **REF-001** : Définitions et règles pour tests
- **REF-002** : Vérification scores empiriques Finnhub
- **REF-003** : Script recalcul scores Finnhub
- **Fichier de résultats** : `SESSION_VALIDATION_ACTUELLE/outputs/comparison_empirical_scores.csv`

---

**Fin du document REF-004**

