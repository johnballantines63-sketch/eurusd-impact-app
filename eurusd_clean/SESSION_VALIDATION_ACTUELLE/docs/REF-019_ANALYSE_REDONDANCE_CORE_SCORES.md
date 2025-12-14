# REF-019 : Analyse Redondance core_scores vs Clusters Identiques

**Date :** 2025-12-06  
**Question :** Y a-t-il redondance entre l'utilisation de `core_scores` et la recherche de clusters identiques dans le pipeline ?

---

## 🔍 ANALYSE DE LA SITUATION ACTUELLE

### 1. Étape 4 : Recherche Clusters Identiques

**Fonction :** `etape4_rechercher_clusters_identiques()`

**Méthode :**
- Utilise le **noyau dur** (core_events) pour trouver des clusters historiques similaires
- Similarité Jaccard entre noyaux durs
- Recherche sur 5 ans d'historique
- Filtrage par heure d'événement (±10 minutes)

**Résultat :**
- Liste de clusters historiques avec le **même noyau dur**
- Chaque cluster contient :
  - Date
  - Événements (avec actual, estimate, surprise)
  - Impact réel mesuré (dans l'étape 6)

**Utilisation :**
- **Étape 6** : Calculer impacts réels pour chaque cluster identique
- **Étape 7** : Analyser relation tendance → amplification
- **Étape 8.3** : Entraîner Random Forest sur ces clusters identiques

---

### 2. core_scores (Table Agrégée)

**Structure :**
- Clé primaire : `(core_type, country)`
- Score agrégé : `empirical_score` = moyenne des impacts réels pour ce core_type
- Basé sur : Toutes les dates historiques avec ce noyau dur

**Calcul :**
```python
# Pour chaque date avec core_type = CPI (US) :
#   - Mesurer impact réel
#   - Calculer score = (avg_movement * 0.5 + p80_movement * 0.5) * robustness
# Score final = moyenne de tous les scores individuels
```

**Utilisation actuelle :**
- ❌ **PAS UTILISÉ dans le pipeline actuel**
- ✅ Stocké pour référence future
- ✅ Utilisé dans les tests d'analyse (REF-017)

---

## ⚠️ REDONDANCE IDENTIFIÉE

### Redondance Conceptuelle

**Les deux méthodes utilisent la même source de données :**

1. **Clusters Identiques (Étape 4)** :
   - Trouve dates historiques avec **même noyau dur**
   - Mesure impacts réels pour chaque date
   - Utilise ces impacts pour prédiction (Random Forest, corrélations)

2. **core_scores** :
   - Agrège impacts réels pour **même noyau dur**
   - Calcule score moyen
   - **Représente la même information, mais agrégée**

### Double Calcul de l'Importance

**Problème identifié :**

1. **Première fois** : Dans la recherche de clusters identiques
   - Le noyau dur est utilisé pour **identifier** les dates similaires
   - Les impacts réels de ces dates sont **mesurés individuellement**
   - Ces impacts sont utilisés pour **entraîner** le Random Forest

2. **Deuxième fois** (si on intègre core_scores) :
   - Le core_score agrège **déjà** ces mêmes impacts
   - Utiliser core_score reviendrait à **réutiliser** une information déjà exploitée

**Exemple concret :**

Pour CPI (US) :
- **Clusters identiques** : Trouve 32 dates avec CPI comme noyau dur
- **core_scores** : Score = 75.06 (moyenne des 32 impacts)
- **Si on utilise core_score** : On réutilise la moyenne au lieu des 32 valeurs individuelles

---

## 💡 ANALYSE : REDONDANCE OU COMPLÉMENTARITÉ ?

### Scénario 1 : Utilisation Redondante ❌

**Si on utilise core_score comme remplacement :**
```python
# ❌ MAUVAIS : Remplacer clusters identiques par core_score
impact_predicted = core_score * amplification
```

**Problèmes :**
- Perte d'information (moyenne vs valeurs individuelles)
- Pas de prise en compte du contexte spécifique (tendance, surprise, etc.)
- Random Forest ne peut pas s'entraîner sur données agrégées

### Scénario 2 : Utilisation Complémentaire ✅

**Si on utilise core_score comme facteur d'ajustement :**
```python
# ✅ BON : Utiliser core_score comme multiplicateur de calibration
ratio_mean = impact_real_mean / core_score_mean  # Par core_type
impact_predicted = (impact_base * amplification) * ratio_mean
```

**Avantages :**
- Calibration selon le core_type (CPI vs NFP vs JOBLESS_PCE)
- Correction de biais systématique
- Complémentaire aux clusters identiques (pas remplacement)

### Scénario 3 : Pas d'Utilisation (Actuel) ⚠️

**État actuel :**
- core_scores calculé mais **non utilisé** dans le pipeline
- Clusters identiques utilisés pour Random Forest et corrélations

**Avantages :**
- Pas de redondance
- Utilisation optimale des données individuelles

**Inconvénients :**
- Pas de calibration par core_type
- Pas de correction de biais systématique

---

## 🎯 RECOMMANDATION

### Option A : Utiliser core_scores comme Multiplicateur de Calibration ✅ (RECOMMANDÉ)

**Principe :**
- Utiliser les **clusters identiques** pour Random Forest et corrélations (comme actuellement)
- Utiliser **core_scores** pour calculer un ratio de calibration par core_type
- Appliquer ce ratio comme multiplicateur final

**Formule :**
```python
# 1. Calculer ratio moyen depuis core_scores_by_date
ratio_cpi_mean = 0.831  # Impact réel moyen / core_score pour CPI

# 2. Appliquer comme multiplicateur
impact_predicted = (impact_base * amplification) * ratio_cpi_mean
```

**Avantages :**
- Pas de redondance (utilise les deux de manière complémentaire)
- Calibration par core_type
- Correction de biais systématique
- Conserve l'utilisation des clusters identiques pour Random Forest

### Option B : Ne Pas Utiliser core_scores ⚠️

**Principe :**
- Continuer à utiliser uniquement les clusters identiques
- Ne pas intégrer core_scores dans le pipeline

**Avantages :**
- Pas de redondance
- Simplicité

**Inconvénients :**
- Pas de calibration par core_type
- Pas de correction de biais systématique

### Option C : Remplacer Clusters Identiques par core_scores ❌ (NON RECOMMANDÉ)

**Principe :**
- Utiliser core_score au lieu de clusters identiques
- Perdre l'information individuelle

**Problèmes :**
- Perte d'information (moyenne vs valeurs individuelles)
- Random Forest ne peut pas s'entraîner
- Pas de prise en compte du contexte

---

## 📊 COMPARAISON DES APPROCHES

| Aspect | Clusters Identiques | core_scores | Complémentaire (A) |
|--------|---------------------|-------------|-------------------|
| **Information** | Individuelle (32 dates) | Agrégée (moyenne) | Les deux |
| **Random Forest** | ✅ Peut s'entraîner | ❌ Données agrégées | ✅ Peut s'entraîner |
| **Calibration** | ❌ Pas de calibration | ✅ Calibration possible | ✅ Calibration optimale |
| **Redondance** | - | ⚠️ Si utilisé seul | ✅ Pas de redondance |
| **Complexité** | Moyenne | Faible | Moyenne |

---

## 🔧 IMPLÉMENTATION RECOMMANDÉE

### Étape 1 : Calculer Ratios Moyens

```python
# Depuis core_scores_by_date
ratios_by_core_type = {
    'CPI': 0.831,      # Impact réel moyen / core_score
    'NFP': 1.396,     # ...
    'JOBLESS_PCE': 1.671  # ...
}
```

### Étape 2 : Intégrer dans Pipeline (Étape 8)

```python
# Dans etape8_appliquer_cluster_cible
core_type = cluster_info.get('core_type')
ratio_calibration = ratios_by_core_type.get(core_type, 1.0)

# Appliquer comme multiplicateur final
impact_predicted = (impact_base * amplification) * ratio_calibration
```

### Étape 3 : Conserver Clusters Identiques

- ✅ Continuer à utiliser pour Random Forest
- ✅ Continuer à utiliser pour corrélations
- ✅ Ajouter ratio comme facteur de calibration

---

## ✅ CONCLUSION

### Réponse à la Question

**Oui, il y a redondance SI on utilise core_scores comme remplacement des clusters identiques.**

**Non, il n'y a PAS de redondance SI on utilise core_scores comme facteur de calibration complémentaire.**

### Recommandation Finale

**Option A : Utiliser core_scores comme multiplicateur de calibration**

- ✅ Pas de redondance (utilisation complémentaire)
- ✅ Calibration par core_type
- ✅ Correction de biais systématique
- ✅ Conserve l'utilisation optimale des clusters identiques

**Avant intégration :**
1. ✅ Remplir `core_scores_by_date` avec toutes les dates historiques
2. ✅ Calculer ratios moyens par core_type
3. ✅ Valider sur dates de test
4. ✅ Intégrer comme multiplicateur final

---

**Document créé le :** 2025-12-06  
**Dernière mise à jour :** 2025-12-06




