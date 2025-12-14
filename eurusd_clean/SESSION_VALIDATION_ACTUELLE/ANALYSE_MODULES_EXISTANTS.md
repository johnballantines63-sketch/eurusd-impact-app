# Analyse : Modules Existants pour Prédiction Direction

**Date** : 2025-12-07  
**Découverte** : Modules existants déjà développés pour prédiction directionnelle

---

## ✅ Modules Existants Découverts

### 1. `impact_measurement.py` - Détection Direction Réelle

**Localisation** : `src/core/impact_measurement.py`

**Fonction** : `measure_impact_from_dukascopy()`

**Méthode** :
```python
# Lignes 155-169
peak_high = prices_after['pips_high'].max()
peak_low = prices_after['pips_low'].max()

if peak_high > peak_low:
    impact_pips = peak_high
    direction = 1  # UP
else:
    impact_pips = peak_low
    direction = -1  # DOWN
```

**Utilisation** :
- ✅ Détecte la direction **RÉELLE** après l'événement
- ✅ Compare mouvement haut vs mouvement bas
- ✅ Le plus grand mouvement détermine la direction

**Statut** : ✅ **Fonctionne - Détecte direction réelle**

---

### 2. `trend_detection_pre_event_s107.py` - Détection Tendance Pré-Événement

**Localisation** : `src/core/trend_detection_pre_event_s107.py`

**Fonction** : `detect_trend_by_inversion_s107()`

**Méthode** :
1. Découpe période en segments (12h)
2. Calcule tendance (régression) pour chaque segment
3. Détecte inversions : UP→DOWN (pic) ou DOWN→UP (creux)
4. Prend dernière inversion valide
5. Mesure tendance depuis inversion

**Retourne** :
```python
{
    'trend_exists': True,
    'direction': 'UP' ou 'DOWN',  # ⭐ Direction tendance
    'r2': float,  # Qualité tendance
    'duration_hours': float,
    'amplitude_pips': float
}
```

**Utilisation** :
- ✅ Détecte tendance **AVANT** l'événement
- ✅ Utilise inversion de tendance comme point de départ
- ✅ Retourne direction de la tendance (UP/DOWN)

**Statut** : ✅ **Existe - À tester comme prédicteur**

---

## 🎯 Hypothèse à Tester

**Question** : La direction de la tendance pré-événement prédit-elle la direction réelle du mouvement ?

**Hypothèse** :
- Si tendance pré-événement = UP → Mouvement réel = UP ?
- Si tendance pré-événement = DOWN → Mouvement réel = DOWN ?

**Méthode de Test** :
1. Pour chaque date avec mouvement FORT/TRÈS_FORT
2. Détecter tendance pré-événement avec `detect_trend_by_inversion_s107()`
3. Comparer direction tendance vs direction réelle
4. Calculer accuracy

---

## 📊 Avantages de Cette Approche

### 1. Utilise Données Réelles (Prix)

- ✅ **Pas dépendant de surprise** (qui n'est pas fiable)
- ✅ Utilise **comportement réel du marché** avant l'événement
- ✅ **Indépendant** des événements (pas besoin de familles/sentiments)

### 2. Méthode Validée

- ✅ Déjà utilisée dans le pipeline (Session 107)
- ✅ Détection robuste par inversion
- ✅ Retourne direction avec qualité (R²)

### 3. Logique Marché

- ✅ Les tendances continuent souvent après événements
- ✅ Le marché suit souvent la tendance pré-événement
- ✅ Plus cohérent avec comportement réel du marché

---

## 🔍 Test à Effectuer

### Script : `test_trend_as_direction_predictor.py`

**Objectif** :
1. Utiliser `detect_trend_by_inversion_s107()` pour chaque date
2. Comparer direction tendance vs direction réelle
3. Calculer accuracy

**Métriques** :
- Accuracy globale
- Accuracy par direction (UP/DOWN)
- Comparaison avec méthode surprise actuelle

---

## 💡 Si Tendance Fonctionne

**Implémentation** :
1. ✅ Utiliser `detect_trend_by_inversion_s107()` dans `validate_on_new_dates.py`
2. ✅ Utiliser direction tendance comme prédiction
3. ✅ Fallback sur surprise si tendance non détectée

**Avantages** :
- ✅ Plus fiable que surprise seule
- ✅ Utilise données réelles (prix)
- ✅ Déjà intégré dans le pipeline

---

## ⚠️ Si Tendance Ne Fonctionne Pas

**Options** :
1. Combiner tendance + surprise (voting)
2. Analyser contexte global (autres événements)
3. Utiliser pattern historique par famille
4. Machine learning sur features combinées

---

**Status** : 🔍 **Modules existants identifiés - Test en cours**


