# ANALYSE PLANIFICATEURS CANDIDATS

**Date :** 2025-12-06  
**Objectif :** Analyser les deux candidats et déterminer si réécriture complète nécessaire

---

## 📋 CANDIDATS IDENTIFIÉS

### 1. `2_Planificateur_V2.py` (dans `_ARCHIVES/`)
- **Statut :** Version archivée
- **Format sorties :** Correspond au format des captures d'écran
- **Localisation :** `streamlit_app/pages/_ARCHIVES/2_Planificateur_V2.py`

### 2. `3_Planificateur_V3_WORKFLOW_CORRECT.md`
- **Statut :** Documentation (pas un fichier Python)
- **Contenu :** Spécification workflow correct
- **Localisation :** `streamlit_app/pages/3_Planificateur_V3_WORKFLOW_CORRECT.md`

### 3. `5_Planificateur_V3.1_CLEAN_OLD.py` (actuel)
- **Statut :** Version actuelle utilisée
- **Localisation :** `streamlit_app/pages/5_Planificateur_V3.1_CLEAN_OLD.py`

---

## 🎯 FONCTIONNALITÉS REQUISES (13 points)

### Fonctionnalités Identifiées dans Captures d'Écran

**Ce qui fonctionne actuellement :**
- ✅ Affichage timings prédits (Baseline, Pic Wave 1, Pullback, Pic Wave 2)
- ✅ Graphique prix avec annotations
- ✅ Prédictions (impact base, amplification, impact prédit, target sortie)
- ✅ Pattern détecté (type, direction, confiance)
- ✅ Informations cluster (événements totaux, noyau dur, clusters identiques)
- ✅ Paramètres configurables (fenêtre cluster, seuils, lookback)
- ✅ Contrôles zoom temporel et amplitude Y

**Ce qui manque (selon 13 fonctionnalités) :**
- ❓ Recherche dates futures candidates (fonctionnalité 1)
- ❓ Recherche mouvements historiques 3 dernières années (fonctionnalité 2)
- ❓ Classification patterns (single wave fort, double wave, zigzag) (fonctionnalité 3)
- ❓ Identification clusters et association patterns (fonctionnalité 4)
- ❓ Recherche dates futures avec clusters similaires (fonctionnalité 5)
- ❓ Calendrier dates futures avec cluster/pattern/impact (fonctionnalité 7)
- ❓ Sélection date par utilisateur (fonctionnalité 8)
- ❓ Fenêtre événements avec Previous/Estimate/Actual (fonctionnalité 9-10)
- ❓ Calcul prédiction avec actuals fournis (fonctionnalité 11)
- ❓ Indications trading (buy/sell, timing sortie, score confiance) (fonctionnalité 12)
- ❓ Stratégie sortie (fonctionnalité 13)

---

## 🔍 ANALYSE DÉTAILLÉE

### Planificateur_V2 (Archivé)

**À analyser :**
- Fonctions de recherche dates futures
- Fonctions de calcul prédictions
- Interface utilisateur
- Intégration avec pipeline

### Planificateur_V3.1_CLEAN_OLD (Actuel)

**Fonctions identifiées :**
- ✅ `search_future_clusters()` - Recherche clusters futurs
- ✅ `detect_pattern_type()` - Détection patterns
- ✅ `load_cache_patterns()` - Cache patterns
- ✅ `enrich_pattern_with_finnhub()` - Enrichissement patterns

**Problèmes potentiels :**
- ⚠️ Version "OLD" - peut être obsolète
- ⚠️ Workflow peut être inversé (selon documentation V3_WORKFLOW_CORRECT.md)

### Documentation V3_WORKFLOW_CORRECT

**Problème identifié :**
- Workflow actuel : Événements → Prix → Pattern → Prédiction (INVERSE)
- Workflow correct : Prix → Mouvement → Pattern → Cluster → Prédiction

**Solution proposée :**
- Mode 1 : Analyse Historique (Workflow Correct)
- Mode 2 : Prédiction Future (Workflow Actuel)

---

## 📊 COMPARAISON AVEC PIPELINE ACTUEL

### Pipeline Complet (`run_pipeline_complete.py`)

**Étapes du pipeline :**
1. Charger Événements
2. Détecter Clusters
3. Définir Noyau Dur
4. Rechercher Clusters Identiques
5. Calculer Tendances
6. Calculer Impacts Base & Amplifications
7. Analyser Relation Tendance → Amplification
8. Appliquer au Cluster Cible + Pattern + Ajustements

**Intégration avec planificateur :**
- Le planificateur doit utiliser ce pipeline pour les prédictions
- Le planificateur doit afficher les résultats du pipeline

---

## ✅ PROPOSITION

### Option 1 : Adapter Planificateur_V2 (Recommandé)

**Avantages :**
- Format sorties correspond aux captures d'écran
- Probablement plus complet que V3.1_CLEAN_OLD
- Peut être adapté pour utiliser le pipeline actuel

**Actions :**
1. Analyser fonctions de V2
2. Adapter pour utiliser `run_pipeline_complete.py`
3. Ajouter fonctionnalités manquantes (calendrier, recherche futures, etc.)

### Option 2 : Réécrire Complètement

**Avantages :**
- Structure propre et moderne
- Intégration native avec pipeline actuel
- Toutes fonctionnalités requises dès le départ

**Inconvénients :**
- Plus de temps de développement
- Risque de perdre fonctionnalités existantes

### Option 3 : Adapter Planificateur_V3.1_CLEAN_OLD

**Avantages :**
- Déjà en place
- Fonctions de base présentes

**Inconvénients :**
- Version "OLD" - peut être obsolète
- Workflow peut être inversé

---

## 📋 PROCHAINES ÉTAPES

1. **Analyser en détail `2_Planificateur_V2.py`**
   - Identifier toutes les fonctions
   - Vérifier compatibilité avec pipeline actuel
   - Identifier fonctionnalités manquantes

2. **Comparer avec fonctionnalités requises**
   - Checklist complète des 13 fonctionnalités
   - Identifier ce qui existe vs ce qui manque

3. **Proposer plan d'action**
   - Adapter V2 ou réécrire complètement
   - Plan d'intégration avec pipeline

---

**En attente d'analyse détaillée des fichiers...**




