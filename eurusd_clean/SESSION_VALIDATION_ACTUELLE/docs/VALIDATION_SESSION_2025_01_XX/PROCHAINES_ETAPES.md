# Prochaines Étapes - Plan d'Action

**Date** : 2025-01-XX  
**Statut Actuel** : ✅ Recherche de clusters identiques optimisée et validée

---

## 📊 ÉTAT ACTUEL

### ✅ Réalisé dans cette Session

1. **Optimisation recherche clusters identiques** :
   - ✅ Requête SQL directe (1 requête au lieu de ~1825)
   - ✅ Filtrage précoce par heure et importance
   - ✅ Groupement par date
   - ✅ Performance : 0.14-0.34 secondes (vs 30-150s avant)

2. **Correction problème CPI** :
   - ✅ Utilisation heure événements CPI (14:30) au lieu anchor_time cluster (14:15)
   - ✅ 22 clusters CPI trouvés pour 2025-09-11
   - ✅ Jaccard 1.000 pour tous les clusters

3. **Nouveaux patterns noyaux durs** :
   - ✅ JOBLESS_PCE, GDP, JOBLESS, PCE
   - ✅ Validation sur 2025-05-29 (JOBLESS_PCE détecté)

4. **Documentation complète** :
   - ✅ Investigation problème CPI documentée
   - ✅ Optimisations documentées
   - ✅ Seuils Jaccard adaptatifs documentés

### ⚠️ À Faire

1. **TODOs restants** :
   - `fix_impact_reel_2025_11_26` : Corriger impact réel mesuré
   - `fix_impact_reel_2025_10_10` : Corriger impact réel mesuré
   - `fix_impact_reel_2025_06_23` : Corriger impact réel mesuré

2. **Tests isolés manquants** :
   - Étape 7 : Analyser Relation Tendance → Amplification
   - Étape 8.3 : Prédiction d'Amplification

3. **Validation pipeline complet** :
   - Tester sur plus de dates historiques
   - Comparer prédictions vs impacts réels
   - Calculer MAE global

---

## 🎯 OPTIONS POUR PROCHAINE ÉTAPE

### Option 1 : Corriger les Impacts Réels (TODOs)

**Priorité** : Moyenne  
**Complexité** : Variable selon le problème

**Actions** :
1. Investiguer pourquoi les impacts réels sont incorrects pour ces dates
2. Vérifier baseline, fenêtre de détection, anchor_time
3. Corriger et valider

**Avantages** :
- Améliore la précision des prédictions
- Permet de calculer des amplifications plus précises

**Inconvénients** :
- Peut être spécifique à certaines dates
- Nécessite investigation approfondie

---

### Option 2 : Tester Étapes 7 et 8.3 Isolément

**Priorité** : Moyenne  
**Complexité** : Faible

**Actions** :
1. Créer `scripts/test_etape7_relation_tendance_amplification.py`
2. Créer `scripts/test_etape8_3_prediction_amplification.py`
3. Exécuter et documenter les résultats

**Avantages** :
- Complète la couverture de tests
- Valide la logique de ces étapes critiques
- Documentation complète du pipeline

**Inconvénients** :
- Ne résout pas de problème immédiat
- Tests de validation plutôt que correction

---

### Option 3 : Validation Pipeline Complet Multi-Dates

**Priorité** : Haute  
**Complexité** : Moyenne

**Actions** :
1. Tester le pipeline complet sur 10-20 dates historiques
2. Comparer prédictions vs impacts réels
3. Calculer MAE, RMSE, précision
4. Identifier les cas problématiques

**Avantages** :
- Validation globale du pipeline
- Identification des problèmes systémiques
- Mesure de performance réelle

**Inconvénients** :
- Peut révéler de nombreux problèmes
- Nécessite analyse approfondie des résultats

---

### Option 4 : Optimiser Autres Parties du Pipeline

**Priorité** : Basse  
**Complexité** : Variable

**Actions** :
1. Identifier les goulots d'étranglement
2. Optimiser les étapes lentes
3. Améliorer la performance globale

**Avantages** :
- Améliore l'expérience utilisateur
- Réduit les temps d'exécution

**Inconvénients** :
- Le pipeline est déjà rapide (0.14-0.34s)
- Priorité moins élevée

---

## 💡 RECOMMANDATION

**Option 3 : Validation Pipeline Complet Multi-Dates**

**Raison** :
1. Le pipeline fonctionne mais n'a pas été validé sur un large échantillon
2. Permet d'identifier les problèmes systémiques avant de corriger des cas spécifiques
3. Donne une vision globale de la performance
4. Les TODOs restants peuvent être traités après avoir identifié les patterns de problèmes

**Plan d'Action** :
1. Créer script de validation multi-dates (10-20 dates)
2. Exécuter et analyser les résultats
3. Calculer métriques (MAE, RMSE, précision)
4. Identifier les cas problématiques
5. Prioriser les corrections selon l'impact

---

## 📋 PLAN DÉTAILLÉ - Option 3

### Phase 1 : Préparation

1. **Sélectionner dates de test** :
   - Dates avec différents types de noyaux durs (CPI, NFP, JOBLESS_PCE, etc.)
   - Dates avec impacts réels connus (depuis `validation_finale_pipeline.csv`)
   - Mélange de dates récentes et historiques

2. **Créer script de validation** :
   - `scripts/validate_pipeline_multi_dates.py`
   - Exécuter pipeline complet pour chaque date
   - Comparer prédictions vs impacts réels
   - Calculer métriques

### Phase 2 : Exécution

1. **Exécuter validation** sur 10-20 dates
2. **Collecter résultats** :
   - Prédictions par date
   - Impacts réels (depuis CSV ou base de données)
   - Erreurs (absolues et relatives)
   - Types de patterns détectés

### Phase 3 : Analyse

1. **Calculer métriques globales** :
   - MAE (Mean Absolute Error)
   - RMSE (Root Mean Squared Error)
   - Précision (pourcentage de prédictions dans ±10 pips)
   - Distribution des erreurs

2. **Identifier patterns** :
   - Dates avec erreurs élevées
   - Types de noyaux durs problématiques
   - Patterns de prix mal détectés
   - Problèmes récurrents

### Phase 4 : Documentation

1. **Créer rapport de validation** :
   - Résultats par date
   - Métriques globales
   - Analyse des erreurs
   - Recommandations

2. **Prioriser corrections** :
   - Identifier les problèmes les plus impactants
   - Créer plan de correction
   - Documenter les solutions

---

## ✅ CRITÈRES DE SUCCÈS

- ✅ Pipeline exécuté sur 10-20 dates sans erreur
- ✅ Métriques calculées (MAE, RMSE, précision)
- ✅ Rapport de validation créé
- ✅ Problèmes identifiés et priorisés
- ✅ Plan de correction défini

---

## 🔗 RÉFÉRENCES

- `outputs/validation_finale_pipeline.csv` : Dates avec impacts réels connus
- `docs/PIPELINE_REFERENCE/PIPELINE_KNOWLEDGE_BASE.md` : Documentation complète du pipeline
- `scripts/test_validation_multi_dates.py` : Script existant (à améliorer)

