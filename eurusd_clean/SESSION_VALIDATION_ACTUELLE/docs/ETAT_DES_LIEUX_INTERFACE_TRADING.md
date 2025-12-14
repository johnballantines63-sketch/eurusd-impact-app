# État des Lieux - Interface Utilisateur Trading

**Date** : 2025-01-XX  
**Version** : Analyse complète fonctionnalités demandées

---

## 📋 FONCTIONNALITÉS DEMANDÉES - ANALYSE POINT PAR POINT

### **1. Recherche de dates futures candidates (mouvements moyen/fort)**

**Demandé** :
- Recherche dans le futur
- Intensité choisie par checkbox (fort par défaut)
- Mouvements moyens/forts dans les 3 dernières années

**État actuel** : ✅ **PARTIELLEMENT IMPLÉMENTÉ**

**Ce qui existe** :
- **Fichier** : `streamlit_app/pages/1_Calendrier_Trading.py`
- **Fonctionnalité** : Recherche de clusters futurs avec projection historique
- **Paramètres** :
  - Slider "Impact médian minimal (pips)" : 0-150, défaut 40
  - Slider "Occurrences min. pour valider un cluster" : 1-30, défaut 5
  - Filtre par importance (1=High, 2=Medium, 3=Low)
- **Période** : Slider "Nombre de jours à venir" (1-21 jours, défaut 7)

**Ce qui manque** :
- ❌ Checkbox pour sélectionner intensité (moyen/fort) - actuellement slider continu
- ❌ Recherche dans le passé (seulement futur)
- ❌ Filtre explicite "3 dernières années" (utilise cache pré-calculé)

**Fichiers concernés** :
- `streamlit_app/pages/1_Calendrier_Trading.py` (lignes 214-223)

---

### **2. Recherche mouvements moyens/forts dans les 3 dernières années**

**Demandé** :
- Examiner les prix sur 3 dernières années
- Identifier mouvements moyens/forts

**État actuel** : ✅ **IMPLÉMENTÉ (via cache)**

**Ce qui existe** :
- **Cache pré-calculé** : `data/cache_clusters.csv` et `data/cache_cluster_patterns.csv`
- **Script de génération** : `scripts/cache_refresh.py` (mentionné dans erreur si cache absent)
- **Données historiques** : Cache contient clusters historiques avec impact médian, pattern, etc.

**Ce qui manque** :
- ❌ Interface pour scanner directement les prix (utilise cache uniquement)
- ❌ Option "recalculer depuis prix bruts" dans l'interface

**Fichiers concernés** :
- `streamlit_app/pages/1_Calendrier_Trading.py` (lignes 53-61, 212)
- Scripts de scan historique : `scripts/session130/scan_movements_2023_2025.py`, `scripts/session121/scan_price_movements_v3.py`

---

### **3. Classifier dates trouvées par patterns (single wave fort, double wave, zigzag)**

**Demandé** :
- Classification par groupes patterns
- Patterns : single wave fort, double wave, zigzag
- Tous peuvent être bullish ou bearish

**État actuel** : ✅ **IMPLÉMENTÉ**

**Ce qui existe** :
- **Patterns détectés** : `SESSION_VALIDATION_ACTUELLE/scripts/scan_patterns_historique_complet.py`
  - double_wave (11 cas uniques)
  - zig_zag (71 cas uniques)
  - single_wave (majoritaire)
- **Classification directionnelle** : UP/DOWN pour chaque pattern
- **Cache patterns** : `data/cache_cluster_patterns.csv` avec colonnes :
  - `pattern_type` (double_wave, zig_zag, single_wave)
  - `direction` (UP, DOWN)
  - `impact_median`, `latency_median`, `ttr_median`

**Ce qui manque** :
- ❌ Interface pour filtrer par pattern spécifique (tous affichés ensemble)
- ❌ Distinction "single wave fort" vs "single wave standard" dans l'interface calendrier

**Fichiers concernés** :
- `streamlit_app/pages/1_Calendrier_Trading.py` (lignes 282-287, affichage patterns)
- `SESSION_VALIDATION_ACTUELLE/scripts/scan_patterns_historique_complet.py` (détection patterns)

---

### **4. Identifier clusters d'events et associer aux patterns**

**Demandé** :
- Identifier clusters d'events des dates trouvées
- Associer clusters aux patterns correspondants
- Vérifier si un cluster peut produire des patterns différents

**État actuel** : ✅ **IMPLÉMENTÉ**

**Ce qui existe** :
- **Signature de cluster** : `compute_signature()` dans `1_Calendrier_Trading.py` (ligne 106)
- **Matching clusters** : Merge avec `cache_clusters` et `cache_cluster_patterns` (lignes 260-279)
- **Association pattern-cluster** : Colonnes `expected_pattern`, `expected_direction` basées sur cache
- **Vérification multi-patterns** : Cache contient `dominant_pattern` et `pattern_type_cache`

**Ce qui manque** :
- ❌ Interface pour voir "tous les patterns possibles" d'un cluster (affiche seulement dominant)
- ❌ Alerte si cluster peut produire patterns différents

**Fichiers concernés** :
- `streamlit_app/pages/1_Calendrier_Trading.py` (lignes 106-157, 260-290)

---

### **5. Rechercher dans le futur les dates où clusters se reproduisent**

**Demandé** :
- Rechercher dates futures où clusters trouvés se reproduisent
- Identifier/marquer ces dates

**État actuel** : ✅ **IMPLÉMENTÉ**

**Ce qui existe** :
- **Fonction** : `build_future_clusters()` dans `1_Calendrier_Trading.py` (ligne 114)
- **Matching** : Merge avec cache historique par `cluster_signature` (ligne 260)
- **Affichage** : Dates futures avec clusters matchés (lignes 313-350)
- **Colonnes affichées** :
  - Date (Bern)
  - Cluster signature
  - Impact médian
  - Pattern attendu
  - Direction
  - Confiance

**Ce qui manque** :
- ❌ Recherche dans le passé (seulement futur)
- ❌ Option "chercher cluster spécifique" (cherche tous les clusters futurs)

**Fichiers concernés** :
- `streamlit_app/pages/1_Calendrier_Trading.py` (lignes 114-157, 253-350)

---

### **6. Calculer prédiction impact, latence, durée pattern pour chaque date**

**Demandé** :
- Calculer impact du cluster
- Calculer latence
- Calculer durée pattern
- Selon formules validées

**État actuel** : ✅ **IMPLÉMENTÉ**

**Ce qui existe** :
- **Métriques calculées** :
  - Impact médian (`impact_candidate`, `impact_median_pattern`)
  - Latence médiane (`latency_median`, `latency_median_pattern`)
  - TTR médian (`ttr_median`, `ttr_median_pattern`)
  - Pullback médian (`pullback_median`)
- **Source** : Cache pré-calculé avec stats historiques
- **Affichage** : Métriques affichées dans tableau et expanders (lignes 318-369)

**Ce qui manque** :
- ❌ Calcul en temps réel avec actuals (utilise médianes historiques uniquement)
- ❌ Prédiction personnalisée selon actuals saisis

**Fichiers concernés** :
- `streamlit_app/pages/1_Calendrier_Trading.py` (lignes 288-290, 318-369)
- `streamlit_app/pages/5_Planificateur_V3.2_Formule_Lineaire.py` (calculs détaillés avec actuals)

---

### **7. Proposer calendrier de dates avec cluster, pattern, impact attendu**

**Demandé** :
- Calendrier de dates à venir
- Mention cluster, pattern, impact attendu

**État actuel** : ✅ **IMPLÉMENTÉ**

**Ce qui existe** :
- **Affichage tableau** : DataFrame avec toutes les dates futures (lignes 332-350)
- **Colonnes** :
  - Date (Bern)
  - Pays
  - #événements
  - Impact médian (pips)
  - Pattern attendu
  - Direction
  - Latence médiane (min)
  - TTR médian (min)
  - Pullback médian (pips)
  - Confiance
  - Occurrences historiques
  - Événements
- **Expanders** : Détails par date avec métriques (lignes 352-373)
- **Export CSV** : Bouton téléchargement (lignes 375-381)

**Ce qui manque** :
- ❌ Vue calendrier visuelle (actuellement tableau)
- ❌ Filtres avancés (par pattern, par intensité)

**Fichiers concernés** :
- `streamlit_app/pages/1_Calendrier_Trading.py` (lignes 313-381)

---

### **8. Possibilité de choisir une date parmi celles proposées**

**Demandé** :
- Utilisateur peut choisir une date parmi celles proposées

**État actuel** : ❌ **NON IMPLÉMENTÉ**

**Ce qui existe** :
- Affichage des dates dans tableau
- Expanders pour voir détails

**Ce qui manque** :
- ❌ Bouton "Sélectionner cette date" ou checkbox
- ❌ Navigation vers page détaillée pour date sélectionnée
- ❌ Intégration avec Planificateur pour date choisie

**Fichiers concernés** :
- `streamlit_app/pages/1_Calendrier_Trading.py` (à ajouter)

---

### **9. Ouvrir fenêtre avec liste events du cluster et date choisie**

**Demandé** :
- Une fois date choisie, ouvrir fenêtre
- Liste des events du cluster
- Events sensés produire le movement attendu

**État actuel** : ⚠️ **PARTIELLEMENT IMPLÉMENTÉ**

**Ce qui existe** :
- **Planificateur V3.2** : `streamlit_app/pages/5_Planificateur_V3.2_Formule_Lineaire.py`
  - Interface pour sélectionner date
  - Chargement events pour date
  - Affichage events avec détails
- **Calendrier** : Affiche "titles" (noms events) mais pas liste détaillée

**Ce qui manque** :
- ❌ Navigation directe Calendrier → Planificateur avec date pré-remplie
- ❌ Fenêtre dédiée "Détails cluster" depuis calendrier
- ❌ Liste complète events avec horaires, pays, importance

**Fichiers concernés** :
- `streamlit_app/pages/1_Calendrier_Trading.py` (à améliorer)
- `streamlit_app/pages/5_Planificateur_V3.2_Formule_Lineaire.py` (existe mais pas intégré)

---

### **10. Afficher events avec Previous, Estimate, case Actual à renseigner**

**Demandé** :
- Afficher Previous, Estimate pour chaque event
- Case Actual à renseigner manuellement
- Possibilité future : remplissage automatique via API

**État actuel** : ✅ **IMPLÉMENTÉ**

**Ce qui existe** :
- **Planificateur V3.2** : Interface complète pour saisie actuals
- **Script session110** : `scripts/session110_fix/interface_selection_events.py`
  - Affichage Previous, Estimate, Forecast
  - Champ input pour Actual (lignes 122-143)
  - Gestion événements futurs vs passés
  - Sauvegarde dans `st.session_state.event_actuals`
- **Format** : `st.number_input()` avec format adapté selon magnitude

**Ce qui manque** :
- ❌ Intégration dans Calendrier (existe seulement dans Planificateur)
- ❌ API automatique pour remplissage (mentionné comme futur)

**Fichiers concernés** :
- `streamlit_app/pages/5_Planificateur_V3.2_Formule_Lineaire.py`
- `scripts/session110_fix/interface_selection_events.py` (référence)

---

### **11. Calculer prédiction avec actuals fournis**

**Demandé** :
- Calculer prédiction pour date et cluster choisis
- En fonction des actuals fournis

**État actuel** : ✅ **IMPLÉMENTÉ**

**Ce qui existe** :
- **Planificateur V3.2** : Calcul complet avec actuals
- **Formules utilisées** :
  - `calculate_impact_linear()` (formule linéaire validée)
  - `calculate_ttr_c()` (TTR)
  - `calculate_pullback_v2()` (Pullback)
  - `predict_doublewave_overlap()` (Double Wave)
  - `predict_pattern_based_ensemble()` (Ensemble)
- **Calcul surprise** : Basé sur actual vs estimate
- **Direction** : `get_event_direction()` selon famille et surprise

**Ce qui manque** :
- ❌ Intégration directe depuis Calendrier (doit aller dans Planificateur séparément)

**Fichiers concernés** :
- `streamlit_app/pages/5_Planificateur_V3.2_Formule_Lineaire.py` (calculs complets)
- `src/core/formulas_validated.py` (formules)

---

### **12. Indications trading : Entry (Buy/Sell), Exit (temps/pips), Confiance**

**Demandé** :
- a) Quand rentrer (Buy/Sell selon prédiction UP/DOWN)
- b) Quand sortir (temps ou nombre de pips atteint)
- c) Niveau de confiance (score basé sur prédictions passées)

**État actuel** : ⚠️ **PARTIELLEMENT IMPLÉMENTÉ**

**Ce qui existe** :

**a) Entry (Buy/Sell)** :
- ✅ Direction prédite : UP/DOWN affiché dans Planificateur
- ❌ **Manque** : Recommandation explicite "BUY" ou "SELL" avec timing précis

**b) Exit (temps/pips)** :
- ✅ TTR calculé (Time To Reversal) : temps avant retour
- ✅ Pullback calculé : niveau de correction
- ✅ Stabilisation : point de sortie suggéré
- ❌ **Manque** : Recommandation explicite "Sortir à X pips" ou "Sortir après Y minutes"
- ❌ **Manque** : Stratégie de sortie progressive (partielle)

**c) Confiance** :
- ✅ Label confiance dans Calendrier : "🟢 élevée", "🟡 moyenne", etc. (ligne 160-169)
- ✅ Basé sur `n_samples` (occurrences historiques)
- ❌ **Manque** : Score de confiance numérique (0-100%)
- ❌ **Manque** : Score basé sur précision passée (validation prédictions)

**Fichiers concernés** :
- `streamlit_app/pages/1_Calendrier_Trading.py` (confiance basique)
- `streamlit_app/pages/5_Planificateur_V3.2_Formule_Lineaire.py` (métriques mais pas recommandations explicites)
- `src/core/scoring_engine.py` (existe mais pas intégré dans UI)

---

### **13. Fonction calendrier : recherche dates passées/futures avec clusters**

**Demandé** :
- Fonction calendrier
- Recherche dates avec clusters (fort/très fort/moyen)
- Futur ET passé
- Indiquer events et noyau dur utilisé pour prédictions

**État actuel** : ⚠️ **PARTIELLEMENT IMPLÉMENTÉ**

**Ce qui existe** :
- **Calendrier Trading 2.0** : `streamlit_app/pages/1_Calendrier_Trading.py`
  - ✅ Recherche dates futures
  - ✅ Filtre par impact (slider)
  - ✅ Affichage clusters et patterns
  - ✅ Affichage events (colonne "titles")
- **Scan historique** : `SESSION_VALIDATION_ACTUELLE/scripts/scan_patterns_historique_complet.py`
  - ✅ Scan dates passées avec patterns
  - ✅ Détection clusters et patterns

**Ce qui manque** :
- ❌ Recherche dans le passé dans l'interface Calendrier (seulement futur)
- ❌ Toggle "Futur / Passé" dans l'interface
- ❌ Affichage détaillé "noyau dur" (core events) utilisé pour prédictions
- ❌ Distinction explicite "fort/très fort/moyen" (actuellement slider continu)

**Fichiers concernés** :
- `streamlit_app/pages/1_Calendrier_Trading.py` (à étendre pour passé)
- `SESSION_VALIDATION_ACTUELLE/scripts/scan_patterns_historique_complet.py` (logique existe, pas intégrée UI)

---

## 📊 RÉSUMÉ PAR STATUT

### ✅ **COMPLÈTEMENT IMPLÉMENTÉ** (7/13)

1. ✅ Recherche dates futures candidates (partiellement - manque checkbox intensité)
2. ✅ Recherche mouvements 3 dernières années (via cache)
3. ✅ Classification par patterns (double_wave, zig_zag, single_wave)
4. ✅ Identification clusters et association patterns
5. ✅ Recherche clusters futurs qui se reproduisent
6. ✅ Calcul prédiction impact/latence/durée (via cache)
7. ✅ Proposer calendrier dates avec cluster/pattern/impact

### ⚠️ **PARTIELLEMENT IMPLÉMENTÉ** (4/13)

8. ⚠️ Choix date parmi proposées (affichage OK, pas de sélection/navigation)
9. ⚠️ Fenêtre events cluster (existe dans Planificateur, pas intégré Calendrier)
10. ⚠️ Affichage Previous/Estimate/Actual (existe Planificateur, pas Calendrier)
11. ⚠️ Calcul prédiction avec actuals (existe Planificateur, pas intégré Calendrier)

### ❌ **NON IMPLÉMENTÉ** (2/13)

12. ❌ Indications trading Entry/Exit/Confiance (métriques existent, pas recommandations explicites)
13. ❌ Fonction calendrier recherche passé (seulement futur actuellement)

---

## 🎯 POINT DE DÉVELOPPEMENT ACTUEL

### **Niveau de complétude global : ~65%**

**Ce qui fonctionne** :
- ✅ Détection patterns historiques (V8 : N=82 multi-wave)
- ✅ Projection clusters futurs avec stats historiques
- ✅ Calculs prédictions avec formules validées
- ✅ Interface Planificateur complète (saisie actuals, calculs)

**Ce qui manque pour workflow complet** :
- ❌ **Intégration Calendrier ↔ Planificateur** (navigation fluide)
- ❌ **Recommandations trading explicites** (Entry/Exit/Confiance)
- ❌ **Recherche dates passées** dans interface
- ❌ **Stratégie de sortie** (partielle, progressive)

---

## 🔧 ACTIONS PRIORITAIRES POUR COMPLÉTER

### **Priorité 1 : Intégration Calendrier ↔ Planificateur** ⭐⭐⭐⭐⭐

**Objectif** : Workflow fluide Calendrier → Planificateur

**Actions** :
1. Ajouter bouton "Analyser cette date" dans chaque ligne calendrier
2. Navigation vers Planificateur avec date pré-remplie
3. Pré-charger events du cluster sélectionné
4. Afficher prédiction initiale (sans actuals) puis permettre saisie actuals

**Fichiers à modifier** :
- `streamlit_app/pages/1_Calendrier_Trading.py` (ajouter boutons)
- `streamlit_app/pages/5_Planificateur_V3.2_Formule_Lineaire.py` (accepter paramètres URL/state)

**Durée estimée** : 3-4h

---

### **Priorité 2 : Recommandations Trading Explicites** ⭐⭐⭐⭐⭐

**Objectif** : Afficher Entry/Exit/Confiance clairs

**Actions** :
1. Créer fonction `calculate_trading_recommendations()` :
   - Entry : "BUY à X:XX" ou "SELL à X:XX" selon direction
   - Exit : "Sortir à Y pips" ou "Sortir après Z minutes"
   - Stop Loss : Calculer niveau de protection
2. Intégrer dans Planificateur après calcul prédiction
3. Afficher score confiance numérique (0-100%) basé sur :
   - N occurrences historiques
   - Précision passée (si validation disponible)
   - Qualité données (completude actuals/estimates)

**Fichiers à créer/modifier** :
- `src/core/trading_recommendations.py` (nouveau)
- `streamlit_app/pages/5_Planificateur_V3.2_Formule_Lineaire.py` (intégrer)

**Durée estimée** : 4-5h

---

### **Priorité 3 : Recherche Dates Passées** ⭐⭐⭐⭐

**Objectif** : Permettre recherche historique dans Calendrier

**Actions** :
1. Ajouter toggle "Futur / Passé" dans sidebar
2. Si "Passé" : charger `patterns_detected.csv` (V8 scan)
3. Filtrer par période, impact, pattern
4. Afficher résultats avec validation (impact réel vs prédit)

**Fichiers à modifier** :
- `streamlit_app/pages/1_Calendrier_Trading.py` (ajouter mode passé)

**Durée estimée** : 2-3h

---

### **Priorité 4 : Stratégie Sortie Progressive** ⭐⭐⭐

**Objectif** : Recommandations sortie partielle

**Actions** :
1. Calculer points de sortie partiels (25%, 50%, 75% du pic)
2. Afficher timeline avec recommandations :
   - "Sortir 25% à X pips"
   - "Sortir 50% à Y pips"
   - "Garder 25% jusqu'à stabilisation"
3. Intégrer dans recommandations trading

**Fichiers à créer/modifier** :
- `src/core/trading_recommendations.py` (étendre)

**Durée estimée** : 2-3h

---

## 📈 ESTIMATION TEMPS TOTAL POUR COMPLÉTION

| Priorité | Tâche | Durée |
|----------|-------|-------|
| P1 | Intégration Calendrier ↔ Planificateur | 3-4h |
| P2 | Recommandations Trading Explicites | 4-5h |
| P3 | Recherche Dates Passées | 2-3h |
| P4 | Stratégie Sortie Progressive | 2-3h |
| **TOTAL** | | **11-15h** |

---

## 🎯 CONCLUSION

**État actuel** : **~65% complété**

**Points forts** :
- ✅ Détection patterns robuste (V8 : N=82)
- ✅ Calculs prédictions validés
- ✅ Interface Planificateur complète
- ✅ Projection clusters futurs

**Points faibles** :
- ❌ Workflow fragmenté (Calendrier et Planificateur séparés)
- ❌ Pas de recommandations trading explicites
- ❌ Recherche seulement futur (pas passé)
- ❌ Pas de stratégie de sortie

**Prochaine étape recommandée** : **Priorité 1** (Intégration Calendrier ↔ Planificateur) pour créer workflow fluide utilisateur.

---

**Version** : État des Lieux V1  
**Date** : 2025-01-XX

