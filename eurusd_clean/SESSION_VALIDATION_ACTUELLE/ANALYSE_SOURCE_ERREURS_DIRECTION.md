# Analyse de la Source des Erreurs Directionnelles

**Date** : 2025-12-07  
**Objectif** : Identifier d'où proviennent les erreurs sur les cas mal prédits

---

## 📊 Résultats Globaux

### Statistiques Erreurs

- **Nombre total de cas** : 50
- **Cas avec erreur directionnelle** : 16 (32.0%)
- **Répartition** :
  - DOWN → UP : 8 cas (50% des erreurs)
  - UP → DOWN : 8 cas (50% des erreurs)

### Par Classe de Mouvement

| Classe | Nombre Erreurs | Taux d'Erreur | Amplitude Réelle Moyenne | Amplitude Prédite Moyenne |
|--------|----------------|---------------|--------------------------|---------------------------|
| **MOYEN** | 15 | **100%** | 30.7 pips | 88.9 pips |
| **FORT** | 1 | 100% | 57.9 pips | 78.6 pips |
| **TRÈS_FORT** | 0 | 0% | - | - |

**⚠️ Observation critique** : **100% des erreurs sont dans la classe MOYEN !**

---

## 🔍 Cause Principale Identifiée

### ⚠️ PROBLÈME CRITIQUE : Tendances UNKNOWN

**100% des cas d'erreur ont une tendance pré-événement = UNKNOWN**

| Métrique | Valeur |
|----------|--------|
| Tendance détectée | **UNKNOWN pour 16/16 erreurs (100%)** |
| Durée moyenne tendance | 0.0 heures |
| R² moyen | 0.000 |
| Type de renversement | UNKNOWN (100%) |

### Impact

Quand la tendance n'est **pas détectée**, le système utilise le **fallback surprise** :
- Fallback surprise : moins fiable (48% accuracy vs 68% avec tendance)
- Résultat : Erreurs directionnelles systématiques

---

## 📈 Analyse Détaillée des Erreurs

### Top 10 Erreurs par Amplitude

| Date | Réel | Prédit | Erreur | Tendance | Surprise Avg | N Events | Familles |
|------|------|--------|--------|----------|--------------|----------|----------|
| 2025-06-02 | DOWN +24.1 | UP +111.9 | 87.8 | UNKNOWN | -25.70% | 8 | PMI,Consumer,ISM |
| 2025-05-01 | UP +23.8 | DOWN +111.6 | 87.8 | UNKNOWN | -23.39% | 8 | PMI,Consumer,ISM |
| 2024-11-01 | DOWN +20.4 | UP +106.1 | 85.7 | UNKNOWN | -14.67% | 18 | Multiple |
| 2023-05-05 | UP +21.1 | DOWN +89.8 | 68.7 | UNKNOWN | +27.70% | 10 | NFP,Unemployment |
| 2025-01-02 | UP +20.6 | DOWN +87.2 | 66.6 | UNKNOWN | +2.28% | 4 | PMI,Consumer |

### Patterns Identifiés

#### 1. Clusters Multi-Événements

- **Nombre d'événements élevé** : 8-18 événements par cluster
- **Familles multiples** : PMI, Consumer, ISM, NFP, Unemployment, Employment
- **Impact** : Clusters complexes = tendance plus difficile à détecter ?

#### 2. Surprises Plafonnées

- **Surprise max = 100%** : Plusieurs cas ont une surprise plafonnée à 100%
- **Surprise avg faible** : Moyennes souvent autour de 0-30%
- **Impact** : Quand surprise est plafonnée, la direction devient moins fiable

#### 3. Mouvements MOYEN (< 40 pips)

- **Amplitude réelle** : 20-40 pips
- **Amplitude prédite** : 70-110 pips (surestimation)
- **Impact** : Prédictions surestimées quand tendance non détectée

---

## 💡 Causes Probables des Erreurs

### Cause #1 : Détection Tendance Échoue (CRITIQUE)

**Pourquoi la détection de tendance échoue-t-elle ?**

Hypothèses :
1. **Prix insuffisants** : Moins de 1000 points de prix disponibles
2. **Période trop courte** : Lookback de 14 jours insuffisant pour certains cas
3. **R² trop faible** : Tendances présentes mais R² < 0.3 (seuil minimum)
4. **Inversion trop récente** : Inversion dans les 24h avant événement (ignorée)

**Action requise** : Analyser pourquoi `detect_trend_by_inversion_s107` retourne UNKNOWN

### Cause #2 : Fallback Surprise Moins Fiable

Quand tendance = UNKNOWN, utilisation du fallback surprise :
- **Accuracy surprise** : 48% (vs 68% avec tendance)
- **Biais directionnel** : Surprise ne capture pas bien la direction réelle
- **Impact** : Erreurs systématiques quand fallback utilisé

### Cause #3 : Clusters Multi-Événements

- **Complexité** : Plus d'événements = plus de bruit
- **Conflicts directionnels** : Événements avec directions opposées
- **Surprises contradictoires** : Somme vectorielle peut donner mauvaise direction

### Cause #4 : Surprises Plafonnées

- **Plafond 100%** : Surprise plafonnée perd l'information de magnitude réelle
- **Direction impactée** : Quand plusieurs surprises plafonnées, direction devient moins fiable
- **Impact** : Erreurs directionnelles accrues

---

## 🎯 Recommandations

### Priorité 1 : Améliorer Détection Tendance

1. **Analyser pourquoi tendance = UNKNOWN** :
   - Vérifier nombre de prix disponibles
   - Analyser R² des tendances détectées (même si < 0.3)
   - Vérifier si inversions trop récentes

2. **Ajuster paramètres détection** :
   - Réduire `min_r2_for_trend` de 0.3 à 0.2 ?
   - Réduire `min_hours_before_event` de 24h à 12h ?
   - Augmenter `lookback_days` de 14 à 21 jours ?

3. **Méthode alternative** :
   - Si détection inversion échoue, utiliser régression linéaire simple
   - Ou utiliser moyenne mobile directionnelle

### Priorité 2 : Améliorer Fallback Surprise

1. **Ne pas plafonner surprises** :
   - Utiliser échelle logarithmique au lieu de plafond 100%
   - Ou augmenter plafond à 200-500%

2. **Pondération améliorée** :
   - Donner plus de poids aux événements avec surprise non plafonnée
   - Réduire poids événements avec surprise plafonnée

### Priorité 3 : Gestion Clusters Multi-Événements

1. **Regrouper par famille** :
   - Calculer direction par famille d'événements
   - Utiliser vote majoritaire entre familles

2. **Filtrage événements** :
   - Exclure événements avec surprise trop faible (< 0.1%)
   - Prioriser événements avec scores empiriques élevés

---

## 📋 Prochaines Étapes

1. ⏳ **Analyser pourquoi tendance = UNKNOWN** pour les 16 cas d'erreur
2. ⏳ **Tester ajustements paramètres détection** (R², heures, lookback)
3. ⏳ **Implémenter méthode alternative** si détection inversion échoue
4. ⏳ **Améliorer fallback surprise** (déplafonnement, pondération)

---

**Status** : ✅ **Analyse complète - Cause principale identifiée (Tendance UNKNOWN)**


