# Explication Complète : Timings Wave2 Peak

**Date** : 2025-01-XX  
**Objectif** : Expliquer clairement le problème des timings Wave2 peak

---

## 📊 QU'EST-CE QUE T+15 ?

### Signification Simple

**T+15** = **15 minutes après l'événement**

**Exemple concret** :
- **Événement** : 14:30 (CPI US publié)
- **T+15** : 14:30 + 15 minutes = **14:45**
- **Signification** : Le pic Wave2 devrait se produire à **14:45**

---

## 🔍 LE PROBLÈME : LOGIQUE ADAPTATIVE

### Timings Session 64 (Standard)

Pour un pattern **DOUBLE_WAVE** avec **un seul cluster** :

| Timing | Signification | Exemple (événement 14:30) |
|--------|---------------|---------------------------|
| **T+5** | Wave1 peak | **14:35** |
| **T+11** | Pullback low | **14:41** |
| **T+15** | **Wave2 peak** | **14:45** |
| **T+40** | Stabilization | **15:10** |

---

### Timings Adaptatifs (Clusters Multiples)

**Pour 2025-09-11** : Il y a **2 clusters** (Cluster 1 à 14:30, Cluster 2 à 14:45)

**Le code adapte les timings** :
- Pullback : **T+19** (au lieu de T+11) = 14:49
- **Wave2 peak : T+40** (au lieu de T+15) = **15:10**

**Raison** : Le code détecte plusieurs clusters et adapte les timings.

---

## 🎯 POURQUOI C'EST UN PROBLÈME ?

### Exemple : 2025-09-11

**Événement** : 14:30

**Timing Standard (T+15)** : **14:45** ✅  
**Timing Adaptatif (T+40)** : **15:10** ⚠️  
**Pic Réel Détecté** : **15:25** ❌

**Erreur** : 15:25 - 14:45 = **40 minutes**

**Problème** : 
1. Le code utilise la logique adaptative (T+40) au lieu du standard (T+15)
2. Mais même avec T+40, le pic réel est à 15:25 (encore 15 min d'erreur)

---

## 🔧 CE QUI DOIT ÊTRE CORRIGÉ

### Option 1 : Toujours Utiliser T+15 (Standard)

**Solution** : Ignorer la logique adaptative et toujours utiliser T+15

**Avantage** : Cohérence avec validation Session 64 (0.00 min erreur)

**Inconvénient** : Ne prend pas en compte les clusters multiples

---

### Option 2 : Corriger Logique Adaptative

**Solution** : Améliorer la détection des clusters multiples et les timings adaptatifs

**Avantage** : Prend en compte les cas complexes

**Inconvénient** : Plus complexe à valider

---

### Option 3 : Utiliser T+15 par Défaut, T+40 si Cluster 2 Détecté

**Solution** : Utiliser T+15 sauf si un cluster 2 est détecté à T+15 exactement

**Avantage** : Équilibre entre simplicité et adaptation

---

## 📋 EXEMPLE CONCRET

### Cas : 2025-09-11

**Événement** : 14:30

**Clusters détectés** :
- Cluster 1 : 14:30 (CPI US)
- Cluster 2 : 14:45 (Current Account DE)

**Timings utilisés** :
- Wave1 peak : **14:35** (T+5) ✅
- Pullback low : **14:49** (T+19, adaptatif) ⚠️
- **Wave2 peak : 15:10 (T+40, adaptatif)** ⚠️
- Stabilization : **15:10** (T+40) ✅

**Problème** : Le pic réel est à **15:25**, pas à **15:10**

**Question** : Faut-il utiliser T+15 (14:45) ou T+40 (15:10) ou le pic réel (15:25) ?

---

## ✅ RECOMMANDATION

**Utiliser T+15 par défaut** pour toutes les dates DOUBLE_WAVE :
- Cohérence avec validation Session 64
- Timings fixes et prévisibles
- 0.00 min d'erreur validé

**Si clusters multiples détectés** :
- Garder T+15 pour Wave2 peak
- Adapter seulement Pullback si nécessaire

---

**Dernière mise à jour** : 2025-01-XX  
**Statut** : ⚠️ Problème identifié, logique adaptative cause des erreurs




