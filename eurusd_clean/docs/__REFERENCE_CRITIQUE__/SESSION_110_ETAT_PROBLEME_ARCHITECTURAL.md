# SESSION 110 - ÉTAT & PROBLÈME ARCHITECTURAL
**Date**: 03 novembre 2025  
**Planificateur V27 - Amplification Dynamique**

---

## ✅ CE QUI A ÉTÉ FAIT

### 1. Interface Sélection Événements
- ✅ Query SQL corrigée (LEFT JOIN + tous pays)
- ✅ Déduplication événements (plus de doublons)
- ✅ Auto-sélection événements score > 20
- ✅ Override manuel avec checkboxes
- ✅ Champs "Actual" pour événements futurs
- ✅ Tri chronologique correct

### 2. Connexion au Bouton "Calculer"
- ✅ Utilise événements SÉLECTIONNÉS (pas recharge DB)
- ✅ Applique valeurs "Actual" saisies
- ✅ Valide sélection avant calcul

### 3. Résultat
**Interface fonctionne parfaitement** ✅
- Charge tous événements (y compris Current Account DE 14:45)
- Permet sélection manuelle
- Transmet sélection au calcul

---

## ❌ PROBLÈME ARCHITECTURAL DÉCOUVERT

### Symptôme
**Le graphique généré est IDENTIQUE** que l'on sélectionne :
- CPI seul (14:30)
- CPI + Current Account (14:30 + 14:45)

**Les timings et amplitudes sont FIXES !**

---

## 🔍 ANALYSE DU PROBLÈME

### Deux Systèmes Parallèles
Le code contient **DEUX logiques de calcul indépendantes** :

#### 1. Calcul Prédictions ✅
```python
def calculate_predictions(cpi_events, amplification):
    # Utilise événements sélectionnés
    # Calcule impact basé sur nombre événements
    # Calcule surprises
    # → CORRECT !
```

#### 2. Génération Graphique ❌
```python
def create_timeline_chart(predictions, start_price):
    event_time = predictions['events'].iloc[0]['ts_utc']
    
    # TIMINGS HARDCODÉS !
    t0 = event_time  # 14:30
    t1 = t0 + timedelta(minutes=5)   # 14:35
    t2 = t1 + timedelta(minutes=5)   # 14:40 ← PEAK FIXE !
    t3 = t2 + timedelta(minutes=5)   # 14:45 ← TTR FIXE !
    t4 = t3 + timedelta(minutes=25)  # 15:10
    
    # AMPLITUDES HARDCODÉES !
    impact_segment1 = impact_total * 0.52
    impact_segment2 = impact_total * 0.48
    pullback_real = impact_total + 10
```

**→ Le graphique ignore COMPLÈTEMENT les événements à 14:45 !**

---

## 📊 CAS RÉEL : 11 SEPTEMBRE 2025

### Timeline MT5 Observée
```
14:30 (12:30 UTC) - CPI Cluster
  ↓ +56 pips en 5 min
14:35 - Peak Initial (1.1744)
  ↓ Pullback -54 pips
14:45 - Creux (1.1690)
  ↓ Current Account (DE) 14:45 ← ÉVÉNEMENT IGNORÉ !
  ↓ Reprise +56 pips en 25 min
15:10 (13:10 UTC) - PEAK ABSOLU (1.1746)
  ↓ Stabilisation
```

### Ce Que Génère le Code Actuel
```
14:30 - Départ
  ↓ +30 pips
14:35 - Palier
  ↓ +26 pips
14:40 - PEAK ← FAUX ! (en réalité 15:10)
  ↓ Pullback
14:45 - TTR ← FAUX ! (en réalité début reprise)
  ↓ Reprise
15:10 - Fin
```

**→ Le graphique est décalé de 30 minutes !**

---

## 🎯 SOLUTION REQUISE

### Détecter Clusters Temporels

**Logique nécessaire :**

1. **Grouper événements par horaire**
```python
clusters = group_events_by_time(selected_events, tolerance=5min)
# Exemple résultat :
# [
#   {time: 14:30, events: [CPI, Jobless, ...], impact: 56 pips},
#   {time: 14:45, events: [Current Account], impact: 30 pips}
# ]
```

2. **Générer timeline adaptée**
```python
if len(clusters) == 1:
    # Single Wave Standard
    # Peak = T0 + 5-8 min
    
elif len(clusters) == 2:
    # Double Cluster Pattern
    # Peak1 = après cluster 1 + TTR
    # Pullback = jusqu'à cluster 2
    # Peak2 = après cluster 2 + propagation
    # Délai entre peaks = temps entre clusters
```

3. **Utiliser VRAIS horaires**
```python
t0 = cluster1['time']
t1 = t0 + ttr_formula(cluster1)
t2 = cluster2['time']  # ← VRAI horaire !
t3 = t2 + propagation_formula(cluster2)  # ← VRAI peak !
```

---

## 🔧 MODIFICATIONS NÉCESSAIRES

### Fichiers à Modifier
```
fx_impact_app/streamlit_app/pages/
  └── 6_Planificateur_V27_AMPLIFICATION_DYNAMIQUE.py
```

### Fonctions à Créer
1. `detect_temporal_clusters(events_df, tolerance_minutes=5)`
   - Groupe événements par proximité temporelle
   - Retourne liste de clusters avec horaires

2. `calculate_cluster_impact(cluster_events)`
   - Calcule impact d'un cluster
   - Utilise formule validée Session 51-55

3. `create_multi_cluster_timeline(clusters, start_price)`
   - Génère timeline adaptée au nombre de clusters
   - Utilise VRAIS horaires des événements
   - Calcule peaks/pullbacks selon pattern réel

### Fonctions à Modifier
- `calculate_predictions()` → Ajouter détection clusters
- `create_timeline_chart()` → Utiliser clusters au lieu de timings fixes
- Idem pour `create_single_wave_strong_chart()` et `create_double_wave_chart()`

---

## 📋 TODO SESSION 111

### Priorité 1 - Détection Clusters
- [ ] Créer fonction `detect_temporal_clusters()`
- [ ] Tester sur 11 sept (doit trouver 2 clusters : 14:30 + 14:45)
- [ ] Valider impact par cluster

### Priorité 2 - Timeline Dynamique
- [ ] Modifier `create_timeline_chart()` pour utiliser clusters
- [ ] Gérer cas 1 cluster (Single Wave)
- [ ] Gérer cas 2+ clusters (Multi-Phase)
- [ ] Utiliser vrais horaires des événements

### Priorité 3 - Validation
- [ ] Tester 11 sept avec CPI seul → Peak à 14:35-14:40
- [ ] Tester 11 sept avec CPI + Current Account → Peak à 15:10
- [ ] Vérifier amplitudes cohérentes
- [ ] Comparer avec MT5

---

## 🎓 LEÇONS APPRISES

### Erreur de Design
**Séparer calcul d'impact et génération graphique était une ERREUR !**

Le graphique doit être **dérivé** du calcul, pas codé en parallèle.

### Bonne Pratique
**Un seul flux de données :**
```
Événements sélectionnés
  ↓
Détection clusters
  ↓
Calcul impacts par cluster
  ↓
Génération timeline basée sur clusters
  ↓
Graphique final
```

### Pattern "Hardcodé vs Adaptatif"
**Hardcoder des patterns observés sur UNE date = BAD IDEA !**
- Fonctionne pour 11 sept uniquement
- Échoue dès qu'on change la sélection
- Non généralisable

**Il faut des patterns ADAPTATIFS :**
- Détectent automatiquement la structure temporelle
- S'ajustent au nombre d'événements
- Utilisent les vrais horaires

---

## 📊 BUDGET TOKENS

**Utilisé** : 142,000 / 190,000 (75%)  
**Restant** : 48,000 tokens

**Recommandation** : Documenter et passer en Session 111 pour implémenter solution.

---

## 🚀 NEXT STEPS

1. **Finir Session 110** avec cette documentation
2. **Session 111** : Implémenter détection clusters + timeline dynamique
3. **Session 112** : Validation complète + tests multi-dates

**Statut** : Architecture clarifiée, solution identifiée, prêt pour implémentation.
