# Problème Ordre Priorité Amplification

**Date** : 1er août 2025  
**Status** : ⚠️ **Problème identifié**

---

## 🔍 PROBLÈME IDENTIFIÉ

### Ordre de Priorité Actuel

**Hiérarchie** (lignes 1062-1113) :
1. ✅ **RF par date (fallback moyenne)** : Si >= 5 clusters → Utilisé → `amplification_method = 'rf_per_date_fallback_mean'`
2. ⏭️ **RF global** : Si `amplification_method == 'default'` → **Jamais testé** (car méthode déjà définie)
3. ⏭️ **Modèle linéaire R²** : Si `amplification_method == 'default'` → **Jamais testé** (car méthode déjà définie)
4. ⏭️ **Moyenne historique** : Si `amplification_method == 'default'` → **Jamais testé** (car méthode déjà définie)

### Pourquoi le Modèle Linéaire N'est Pas Utilisé

**Raison** : Le RF par date (fallback moyenne) est utilisé en premier et définit `amplification_method`, donc les étapes suivantes ne sont jamais testées.

**Problème** :
- La moyenne historique (0.246x) est utilisée
- Elle ignore les caractéristiques spécifiques du cluster cible (tendance R² = 0.350)
- Le modèle linéaire R² devrait être utilisé car il prend en compte la tendance

---

## ✅ SOLUTION PROPOSÉE

### Option 1 : Utiliser Modèle Linéaire en Priorité (si tendance détectée)

**Modification** : Tester le modèle linéaire R² **avant** la moyenne historique si une tendance est détectée.

**Justification** :
- Le modèle linéaire utilise la tendance R² (0.350) qui est spécifique au cluster cible
- La moyenne historique ignore les caractéristiques spécifiques
- Le modèle linéaire devrait être plus précis

---

### Option 2 : Modifier Ordre de Priorité

**Nouvel ordre** :
1. RF par date (si implémenté)
2. **Modèle linéaire R²** (si tendance détectée) ← **Priorité avant moyenne**
3. RF global (si implémenté)
4. Moyenne historique (dernier fallback)

---

### Option 3 : Utiliser Modèle Linéaire au Lieu de Moyenne

**Modification** : Si tendance détectée, utiliser modèle linéaire au lieu de moyenne historique pour RF par date.

**Justification** : Le modèle linéaire est spécifique au cluster cible, la moyenne est générique.

---

## 📋 RECOMMANDATION

**Solution recommandée** : **Option 1** - Utiliser modèle linéaire en priorité si tendance détectée.

**Modification** :
```python
# Tester modèle linéaire AVANT moyenne historique si tendance détectée
if trend_exists and trend_r2 > 0:
    # Essayer modèle linéaire d'abord
    try:
        from core.r2_amplification_correlation import predict_amplification_from_r2
        amplification_predite = predict_amplification_from_r2(
            r2_trend=trend_r2,
            calibration_mode='linear'
        )
        amplification_method = 'linear_r2'
        # Continuer seulement si succès
    except:
        pass

# Puis tester autres méthodes si modèle linéaire n'a pas fonctionné
if amplification_method == 'default' and num_clusters >= 5:
    # Moyenne historique...
```

---

**Status** : ⚠️ **Solution proposée - À implémenter**




