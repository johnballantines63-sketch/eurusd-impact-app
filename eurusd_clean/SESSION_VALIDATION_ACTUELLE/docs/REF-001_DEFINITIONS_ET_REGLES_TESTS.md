# REF-001 : DÉFINITIONS ET RÈGLES POUR TESTS

**Référence :** REF-001  
**Date de création :** 2025-12-06  
**Heure de création :** 01:38:29  
**Auteur :** André Valentin avec Claude  
**Version :** 1.0

---

## 📋 OBJECTIF

Établir des définitions claires et des règles strictes pour les tests afin d'éviter les biais et déviances dans le développement. Ce document sert de référence unique pour toutes les validations futures.

---

## ❓ RÉPONSES AUX QUESTIONS

### Question 1 : Définition de "Mouvements Forts"

**Réponse :**

Actuellement, il n'existe **PAS de définition unique et standardisée** de "mouvements forts" dans le codebase. Différents scripts utilisent des seuils différents :

| Script | Seuil Minimum | Fenêtre | Source |
|--------|---------------|---------|--------|
| `session132/validate_doublewave_complete.py` | 30 pips | 60 min | `prices_bern` |
| `session137/extract_doublewave_real_metrics_correct_workflow.py` | Variable (`MIN_MOVEMENT_PIPS`) | Variable | `prices_finnhub_m1` |
| `session119/find_single_wave_cases.py` | 40 pips | Variable | Variable |
| Pipeline actuel | 15 pips (`min_amplitude_pips`) | Variable | `prices_finnhub_m1` |

**⚠️ PROBLÈME IDENTIFIÉ :**
- Incohérence entre les seuils (15, 30, 40 pips)
- Sources de données différentes (`prices_bern` vs `prices_finnhub_m1`)
- Pas de définition centralisée

**✅ DÉFINITION PROPOSÉE (À VALIDER) :**
```
Mouvement Fort = Impact mesuré depuis baseline >= 30 pips
- Baseline : OPEN de la première bougie à ou après l'événement
- Pic : HIGH maximum (ou LOW minimum) dans une fenêtre de 240 minutes après l'événement
- Source : prices_finnhub_m1 (source unique validée)
- Impact = abs((peak_price - baseline_price) * 10000)
```

**Références dans le code :**
- `scripts/session132/validate_doublewave_complete.py` : ligne 39-123
- `scripts/session137/extract_doublewave_real_metrics_correct_workflow.py` : ligne 49-144
- `scripts/run_pipeline_complete.py` : ligne 1001 (`min_amplitude_pips = 15.0`)

---

### Question 2 : Scores Empiriques depuis Finnhub

**Réponse :**

**STATUT :** ⚠️ **INCERTAIN - NÉCESSITE VÉRIFICATION**

**Recherche effectuée :**
- Aucun script trouvé avec `finnhub.*empirical` ou `empirical.*finnhub`
- Scripts de recalcul trouvés : `session123/recalculate_empirical_scores_*.py`
- Ces scripts semblent utiliser des données EODHD, pas Finnhub

**Méthode de calcul actuelle (d'après scripts Session 123) :**
```python
def calculate_empirical_score(avg_movement, p80_movement, sample_size):
    base_score = (avg_movement * 0.5 + p80_movement * 0.5)
    
    # Facteur robustesse
    if sample_size >= 20:
        robustness = 1.0
    elif sample_size >= 10:
        robustness = 0.9
    elif sample_size >= 5:
        robustness = 0.8
    else:
        robustness = 0.7
    
    score = base_score * robustness
    normalized = min(100.0, (score / 100.0) * 100.0)
    return normalized
```

**Stockage :**
- Table : `event_families`
- Colonnes : `event_key`, `country`, `empirical_score`, `family`, `latency_median`
- Jointure : `events` LEFT JOIN `event_families` ON `event_key` AND `country`

**VÉRIFICATION EFFECTUÉE (2025-12-06 01:56:04) :**
- ✅ Table `event_families` contient 1905 entrées
- ✅ Toutes les entrées ont un `empirical_score` (1905/1905)
- ✅ Plage de scores : 4.15 à 64.61
- ✅ Score moyen : 17.90

**⚠️ ACTION REQUISE :**
1. ⏳ **À VÉRIFIER** : Les scores ont-ils été recalculés depuis l'intégration Finnhub ?
   - Les scripts de recalcul trouvés (Session 123) semblent utiliser EODHD
   - Aucun script trouvé avec "finnhub" dans le nom pour le recalcul
2. ⏳ **À FAIRE** : Si non, créer un script de recalcul basé sur `prices_finnhub_m1` et `events` (Finnhub)
3. ⏳ **À FAIRE** : Documenter la méthode de calcul utilisée et la date du dernier recalcul

**Références dans le code :**
- `src/core/event_loader.py` : ligne 98-124 (requête SQL)
- `scripts/session123/recalculate_empirical_scores_optimized.py` : ligne 23-41 (formule)
- `scripts/session123/recalculate_empirical_scores_eodhd.py` : ligne 107-132 (formule détaillée)

---

### Question 3 : Définition du "Noyau Dur"

**Réponse :**

**DÉFINITION ACTUELLE (d'après `scripts/run_pipeline_complete.py`) :**

Le "noyau dur" (core events) est un sous-ensemble d'événements d'un cluster qui :
1. **Apparaissent fréquemment ensemble** dans des clusters similaires
2. **Sont identifiés par patterns pré-définis** (CPI, NFP, JOBLESS_PCE, GDP, etc.)
3. **Servent à rechercher des clusters identiques** dans l'historique

**Méthode de détection (Étape 3 du pipeline) :**

1. **Patterns pré-définis :**
   - `CPI_PATTERN` : CPI, Consumer Price, Inflation Rate, Core Inflation
   - `NFP_PATTERN` : Non Farm Payrolls, Nonfarm
   - `JOBLESS_PATTERN` : Jobless Claims, Unemployment Claims
   - `PCE_PATTERN` : PCE Prices, Personal Consumption Expenditure
   - `GDP_PATTERN` : GDP, Gross Domestic Product

2. **Priorité de détection :**
   - PRIORITÉ 1 : CPI (≥ 2 événements CPI) → `core_type = 'CPI'`
   - PRIORITÉ 2 : NFP (≥ 1 événement NFP) → `core_type = 'NFP'`
   - PRIORITÉ 3 : JOBLESS_PCE (≥ 2 Jobless ET ≥ 1 PCE) → `core_type = 'JOBLESS_PCE'`
   - PRIORITÉ 4 : GDP (≥ 2 événements GDP) → `core_type = 'GDP'`
   - PRIORITÉ 5 : JOBLESS seul (≥ 2 Jobless) → `core_type = 'JOBLESS'`
   - PRIORITÉ 6 : PCE seul (≥ 1 PCE) → `core_type = 'PCE'`
   - FALLBACK : Tous les événements → `core_type = 'GENERIC'`

3. **Support :**
   - Pour les noyaux durs pré-définis : `support_score = 1.0` (100%)
   - Pour les autres : `support_score = 0.0`

**Utilisation :**
- Recherche de clusters identiques dans l'historique (Étape 4)
- Similarité Jaccard basée sur les événements core uniquement
- Calcul de tendances et amplifications sur clusters similaires

**Références dans le code :**
- `scripts/run_pipeline_complete.py` : ligne 400-600 (Étape 3)
- `scripts/test_r2_amplification_identical_clusters.py` : ligne 555-598 (extraction noyau dur)

---

### Question 4 : Utilisation des CSV dans les Tests

**Réponse :**

**STATUT ACTUEL :** ⚠️ **PROBLÉMATIQUE**

**Problèmes identifiés :**
1. **Validation circulaire** : Les CSV contiennent parfois des prédictions du pipeline au lieu de mesures réelles indépendantes
2. **Données obsolètes** : Les CSV peuvent contenir des données pré-Finnhub
3. **Pas de traçabilité** : Impossible de vérifier l'origine des données CSV
4. **Incohérences** : Différences entre CSV et mesures réelles depuis la DB

**Exemples de problèmes rencontrés :**
- `impacts_reels_mesures.csv` : Contenait des prédictions au lieu de mesures réelles
- `validation_finale_pipeline.csv` : Valeurs incorrectes pour certaines dates
- CSV avec `anchor_time` fixe (14:30) au lieu de l'`anchor_time` réel du pipeline

**✅ SOLUTION (Règle 1) :**
Ne plus utiliser les CSV pour les tests. Toujours recalculer depuis la DB.

---

## 📜 RÈGLES ÉTABLIES

### Règle 1 : Pas de CSV dans les Tests

**Énoncé :**
> Pour tous les tests, ne plus utiliser les CSV mais recalculer à chaque fois d'après les données de la DB pour éviter les erreurs.

**Application :**
- ✅ Mesurer les impacts réels directement depuis `prices_finnhub_m1`
- ✅ Extraire les événements directement depuis `events` (Finnhub)
- ✅ Calculer les scores empiriques depuis `event_families`
- ❌ Ne plus charger de CSV avec `pd.read_csv()` pour les données de validation
- ✅ Les CSV peuvent être utilisés pour **sauvegarder** les résultats, mais pas pour les **charger** dans les tests

**Exemple d'implémentation :**
```python
# ❌ ANCIEN (à éviter)
df_real = pd.read_csv('impacts_reels_mesures.csv')
impact_real = df_real[df_real['date'] == date_str]['impact_real'].iloc[0]

# ✅ NOUVEAU (correct)
impact_real = measure_real_impact_from_db(
    date_str=date_str,
    anchor_time=anchor_time,
    db_path=DB_PATH
)
```

---

### Règle 2 : Exécution Complète du Pipeline

**Énoncé :**
> Exécuter à chaque fois qu'on teste l'intégralité du pipeline quand on tente de prédire.

**Application :**
- ✅ Toujours utiliser `PipelineExecutor.execute_complete_pipeline(date_str)`
- ✅ Ne pas court-circuiter les étapes (même pour des tests unitaires)
- ✅ Utiliser les résultats complets du pipeline pour les validations
- ❌ Ne pas utiliser des fonctions individuelles isolées pour les tests de prédiction

**Exemple d'implémentation :**
```python
# ✅ CORRECT
executor = PipelineExecutor(DB_PATH, verbose=False)
result = executor.execute_complete_pipeline(date_str)
impact_predicted = result['final_prediction']['prediction_finale']

# ❌ INCORRECT (pour tests de prédiction)
impact_base = calculate_impact_d(empirical_score, num_events)  # Court-circuit
```

**Exception :**
Les tests unitaires des fonctions individuelles sont autorisés, mais doivent être clairement identifiés comme tels.

---

### Règle 3 : Numérotation et Horodatage des Documents

**Énoncé :**
> Tous les documents doivent dorénavant être numérotés avec un no de référence incrémenté afin de pouvoir les repérer et les retrouver facilement et également datés et horodatés avec l'heure de création.

**Format :**
```
REF-XXX : TITRE_DU_DOCUMENT.md

Référence : REF-XXX
Date de création : YYYY-MM-DD
Heure de création : HH:MM:SS
Auteur : [Nom]
Version : X.Y
```

**Application :**
- ✅ Tous les nouveaux documents dans `SESSION_VALIDATION_ACTUELLE/docs/` doivent suivre ce format
- ✅ Numérotation incrémentée : REF-001, REF-002, REF-003, etc.
- ✅ Date et heure de création obligatoires
- ✅ Version initiale : 1.0

**Exemple :**
```markdown
# REF-002 : ANALYSE_PROBLEME_AMPLIFICATION.md

**Référence :** REF-002  
**Date de création :** 2025-12-XX  
**Heure de création :** 14:30:15  
**Auteur :** André Valentin avec Claude  
**Version :** 1.0
```

---

## 📊 RÉSUMÉ DES ACTIONS REQUISES

### Actions Immédiates

1. **✅ CRÉÉ** : Ce document REF-001
2. **⏳ À FAIRE** : Vérifier si scores empiriques recalculés depuis Finnhub
3. **⏳ À FAIRE** : Standardiser définition "mouvements forts" (30 pips ?)
4. **⏳ À FAIRE** : Créer script de recalcul scores empiriques depuis Finnhub si nécessaire
5. **⏳ À FAIRE** : Mettre à jour tous les scripts de test pour respecter Règle 1 et 2

### Actions Futures

1. Créer un index centralisé des documents REF-XXX
2. Documenter la méthode de calcul des scores empiriques (si recalculée)
3. Valider la définition standardisée de "mouvements forts"

---

## 📝 NOTES

- Ce document est la référence unique pour toutes les validations futures
- Toute modification doit être documentée avec version incrémentée
- Les règles établies sont **obligatoires** pour tous les nouveaux tests

---

**Fin du document REF-001**

