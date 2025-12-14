# Synthèse Évolution et Corrections du Pipeline

**Date** : 2025-01-XX  
**Objectif** : Synthétiser l'évolution complète du pipeline et toutes les corrections apportées pour améliorer la compréhension et guider le développement

---

## 📋 ÉVOLUTION CHRONOLOGIQUE

### Phase 1 : Pipeline Initial (Pré-11h37)

**Caractéristiques** :
- Pipeline restauré depuis backup (`pipeline_backup/20251203_114640/`)
- MAE documenté : 8.4 pips
- Structure de base en 8 étapes validée

**Problèmes identifiés** :
- Valeurs CSV incorrectes (ex: 21.7 pips pour 2025-09-11)
- Détection CPI défaillante (0 clusters trouvés)
- Recherche clusters identiques lente
- Noyaux durs limités (seulement CPI/NFP)

---

### Phase 2 : Corrections Majeures (Post-11h37)

#### Correction 1 : Chargement Événements HAUT Importance

**Problème** : Événements HAUT importance (`importance_n=3`) non chargés si score empirique faible

**Solution** : Priorité 1 pour charger tous les événements `importance_n=3` même si score faible

**Fichier** : `scripts/run_pipeline_complete.py` - `etape1_charger_evenements`

**Code** :
```python
# PRIORITÉ 1 : Charger tous les événements HAUT importance (importance_n=3) même si score faible
query_high_importance = f"""
SELECT ... FROM events e
WHERE ... AND e.importance_n = 3
"""
```

**Impact** : 2025-05-29 : 24 événements HAUT importance maintenant chargés (vs 3 avant)

---

#### Correction 2 : Nouveaux Patterns Noyaux Durs

**Problème** : Noyau dur "GENERIC" pour clusters avec événements spécifiques (Jobless Claims, PCE, GDP)

**Solution** : Ajout de patterns pour détecter :
- JOBLESS_PCE (≥2 Jobless ET ≥1 PCE)
- GDP (≥2 événements GDP)
- JOBLESS (≥2 événements Jobless)
- PCE (≥1 événement PCE)

**Fichier** : `scripts/run_pipeline_complete.py` - `etape3_definir_noyau_dur`

**Hiérarchie** :
1. CPI (≥2 événements)
2. NFP (≥1 événement)
3. JOBLESS_PCE (≥2 Jobless ET ≥1 PCE)
4. GDP (≥2 événements)
5. JOBLESS (≥2 événements)
6. PCE (≥1 événement)
7. GENERIC (fallback)

**Impact** : 2025-05-29 : Noyau dur "JOBLESS_PCE" au lieu de "GENERIC"

---

#### Correction 3 : Optimisation Recherche Clusters Identiques

**Problème** : Recherche très lente (30-150 secondes pour 5 ans)

**Solution** :
1. Requête SQL directe pour toute la période (au lieu de jour par jour)
2. Filtrage précoce par heure et importance_n dans SQL
3. Groupement par date post-SQL

**Fichier** : `scripts/run_pipeline_complete.py` - `etape4_rechercher_clusters_identiques`

**Gain** : ~99.7% de réduction du temps (12-60s → 0.04-0.57s)

---

#### Correction 4 : Correction Détection CPI

**Problème** : Aucun cluster CPI trouvé pour 2025-09-11

**Causes identifiées** :
1. Anchor time incorrect (14:15 au lieu de 14:30 pour CPI US)
2. Requête SQL trop restrictive (importance_n=3 seulement)

**Solutions** :
1. Ajustement anchor_time pour clusters CPI US
2. Extension requête SQL pour inclure événements CPI même si importance_n != 3

**Fichier** : `scripts/run_pipeline_complete.py` - `etape4_rechercher_clusters_identiques`

**Impact** : 2025-09-11 : 22 clusters CPI trouvés (vs 0 avant)

---

#### Correction 5 : Seuils Jaccard Adaptatifs

**Problème** : Seuil Jaccard fixe (0.60) trop restrictif pour certains cas

**Solution** : Seuils adaptatifs (0.60 → 0.55 → 0.50) si pas assez de clusters trouvés

**Fichier** : `scripts/run_pipeline_complete.py` - `etape4_rechercher_clusters_identiques`

**Impact** : Plus de clusters trouvés pour cas difficiles

---

#### Correction 6 : MAX_PULLBACK_RATIO 0.80

**Problème** : MAX_PULLBACK_RATIO 0.75 ne donnait pas 100% cas parfaits

**Solution** : Augmentation à 0.80 (validation 27 novembre 2025)

**Fichier** : `src/core/formulas_validated.py` - `calculate_pullback_v2`

**Impact** : 100% cas parfaits (57/57) avec 0.00 min d'erreur moyenne

---

### Phase 3 : Découvertes Récentes

#### Découverte 1 : Amplification Excessive

**Problème** : Amplification 5.875x pour 2025-11-20 (surprise 138%)

**Cause** : Formule Session 88 trop agressive pour surprises 100-200%

**Hiérarchie actuelle** :
1. Formule Session 88 (si surprise >100%) ← **Priorité absolue**
2. Random Forest par date (si >= 5 clusters ET surprise ≤100%)
3. Random Forest global (non implémenté)
4. Modèle linéaire (basé sur R²)
5. Moyenne historique

**Problème** : Random Forest jamais utilisé pour surprises >100%

**Solution proposée** : Modifier hiérarchie pour permettre RF même pour surprises >100%

---

#### Découverte 2 : Valeurs CSV Incorrectes

**Problème** : Valeurs dans CSV très différentes des valeurs mesurées fraîchement

**Exemples** :
- 2025-09-11 : CSV 21.7 pips vs Mesuré 8.40 pips vs Session 110 (56.2 pips)
- 2025-08-01 : CSV 188.3 pips vs Mesuré 33.20 pips

**Action** : Création script `measure_real_impacts_all_dates.py` pour mesurer fraîchement

**Question ouverte** : Quelle est la bonne méthode de mesure ?
- Pic absolu dans fenêtre +120 min ?
- Pic du pattern détecté (wave2_peak) ?
- Autre méthode ?

---

## 🔧 ARCHITECTURE ACTUELLE DU PIPELINE

### Structure en 8 Étapes

#### Étape 1 : Charger Événements
- **Fonction** : `etape1_charger_evenements`
- **Logique** :
  1. Priorité 1 : Charger tous événements `importance_n=3` (même score faible)
  2. Priorité 2 : Seuil adaptatif (`max(20.0, max_score - 5.0)`)
- **Seuils** : US/EU = 40.0, DE = 20.0

#### Étape 2 : Détecter Clusters
- **Fonction** : `etape2_detecter_clusters`
- **Méthode** : Fenêtre glissante de 30 minutes

#### Étape 3 : Définir Noyau Dur
- **Fonction** : `etape3_definir_noyau_dur`
- **Patterns détectés** : CPI, NFP, JOBLESS_PCE, GDP, JOBLESS, PCE, GENERIC
- **Canonical IDs** : Format `event_key_country_importance`

#### Étape 4 : Rechercher Clusters Identiques
- **Fonction** : `etape4_rechercher_clusters_identiques`
- **Optimisations** :
  - Requête SQL directe (1 requête au lieu de ~1825)
  - Filtrage précoce par heure et importance_n
  - Seuils Jaccard adaptatifs (0.60 → 0.55 → 0.50)
  - Correction anchor_time pour CPI US
- **Performance** : 0.04-0.57s (vs 12-60s avant)

#### Étape 5 : Calculer Tendances
- **Fonction** : `etape5_calculer_tendances_impacts`
- **Méthode** : `detect_trend_by_inversion_s107`
- **Table** : `prices_finnhub_h1`
- **Fenêtre** : 6 jours après inversion

#### Étape 6 : Calculer Impacts Base & Amplifications
- **Fonction** : `etape6_calculer_impacts_base_amplifications`
- **Impact base** : `calculate_impact_d` avec `calculate_adjusted_empirical_score`
- **Impact réel** : `measure_impact_from_finnhub`
- **Amplification parfaite** : `impact_reel / impact_base`

#### Étape 7 : Analyser Relation Tendance → Amplification
- **Fonction** : `etape7_analyser_relation_tendance_amplification`
- **Méthode** : Corrélations R² vs amplification

#### Étape 8 : Appliquer au Cluster Cible

**8.1 Calcul Impact Base** :
- Méthode détaillée par événement
- Ajustement scores selon surprise
- Correction factor 0.758 pour multi-événements

**8.2 Détection Tendance** :
- `detect_trend_by_inversion_s107`
- Table : `prices_finnhub_m30`

**8.3 Prédiction Amplification** :
- Hiérarchie : Session 88 → RF par date → RF global → Linéaire → Moyenne
- ⚠️ Problème : Session 88 priorité absolue pour surprises >100%

**8.4 Ajustements Support/Résistance** :
- Calcul ATR
- Détection niveaux S/R
- Ajustements : +15% à -30%

**8.5 Ajustements Patterns Finnhub** :
- `load_finnhub_patterns`
- Ajustements : +5% à +10% ou -10% à -15%

**8.6 Détection Pattern de Prix** :
- `detect_for_date_duckdb_rev12`
- Patterns : DOUBLE_WAVE, SINGLE_WAVE_STRONG
- Baseline mode : `prev_close_14_29`
- Minutes after hint : 120

**8.7 Stratégie Hybride Pattern/Formules** :
- Option C (révisée) : Si différence < 10 pips → formules, sinon pattern

**8.8 Calcul Target de Sortie** :
- 80% du impact final prédit

---

## 📊 PROBLÈMES IDENTIFIÉS ET SOLUTIONS

### Problème 1 : Amplification Excessive

**Symptôme** : Amplification 5.875x pour 2025-11-20 (surprise 138%)

**Cause** : Formule Session 88 trop agressive pour surprises 100-200%

**Solutions proposées** :
1. Ajuster formule Session 88 pour surprises 100-200%
2. Modifier hiérarchie pour permettre RF même pour surprises >100%
3. Limiter amplification maximale (ex: 3.0x)

**Statut** : ⚠️ À implémenter

---

### Problème 2 : Valeurs CSV Incorrectes

**Symptôme** : Valeurs très différentes des mesures fraîches

**Action** : Script `measure_real_impacts_all_dates.py` créé

**Question** : Quelle méthode de mesure utiliser ?

**Statut** : ⚠️ À valider

---

### Problème 3 : Impact Base Très Élevé

**Symptôme** : Impact base 273.78 pips pour 2025-11-20

**Cause possible** : Scores empiriques élevés + 10 événements

**Action requise** : Vérifier calcul et correction factor

**Statut** : ⚠️ À analyser

---

## ✅ CORRECTIONS VALIDÉES

1. ✅ Chargement événements HAUT importance
2. ✅ Nouveaux patterns noyaux durs
3. ✅ Optimisation recherche clusters identiques
4. ✅ Correction détection CPI
5. ✅ Seuils Jaccard adaptatifs
6. ✅ MAX_PULLBACK_RATIO 0.80

---

## 📋 PROCHAINES ÉTAPES PRIORITAIRES

### Priorité 1 : Valider Méthode de Mesure

1. Analyser méthode Session 110 (56.2 pips pour 2025-09-11)
2. Comparer avec méthode actuelle
3. Ajuster script si nécessaire
4. Re-mesurer avec méthode validée

### Priorité 2 : Corriger Amplification Excessive

1. Analyser pourquoi Formule Session 88 trop agressive
2. Proposer ajustements
3. Tester sur cas problématiques
4. Implémenter solution validée

### Priorité 3 : Analyser Impact Base Élevé

1. Vérifier calcul impact base pour 2025-11-20
2. Vérifier correction factor 0.758
3. Comparer avec autres dates
4. Corriger si nécessaire

---

## 🔗 RÉFÉRENCES CLÉS

- **Pipeline complet** : `scripts/run_pipeline_complete.py`
- **Formules validées** : `src/core/formulas_validated.py`
- **Random Forest** : `src/core/random_forest_amplification.py`
- **Documentation** : `docs/VALIDATION_SESSION_2025_01_XX/`
- **Référence** : `docs/PIPELINE_REFERENCE/`

---

**Dernière mise à jour** : 2025-01-XX




