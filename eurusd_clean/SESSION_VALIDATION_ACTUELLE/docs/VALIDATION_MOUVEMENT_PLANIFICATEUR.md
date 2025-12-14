# Validation Mouvement Planificateur - Vérification Complète

**Date** : 2025-01-XX  
**Fichier** : `streamlit_app/pages/5_Planificateur_V3.2_Formule_Lineaire.py`

---

## ✅ Vérification des 4 Points Demandés

### **1. Calcul de `cluster_ts` en UTC cohérente**

**Emplacement** : Lignes 4720-4734

**Code vérifié** :
```python
# =============================================================================
# 1) Calculer cluster_ts (ancre) en UTC cohérente
# =============================================================================
# Anchor du cluster (doit être UTC pour comparer aux prix)
cluster_ts = pd.Timestamp(selected_cluster["date"])

# Si anchor_ts existe dans selected_cluster, l'utiliser
if "anchor_ts" in selected_cluster and pd.notna(selected_cluster["anchor_ts"]):
    cluster_ts = pd.Timestamp(selected_cluster["anchor_ts"])

# Normaliser en UTC
if cluster_ts.tzinfo is None:
    cluster_ts = cluster_ts.tz_localize("UTC")
else:
    cluster_ts = cluster_ts.tz_convert("UTC")
```

**✅ Status** : Implémenté correctement
- Utilise `selected_cluster["date"]` par défaut
- Fallback vers `anchor_ts` si disponible
- Normalisation en UTC garantie
- **PAS d'utilisation de `anchor_ts_bern`** pour comparaison avec prix

---

### **2. Filtrage du mouvement détecté (proximité <= 15 min)**

**Emplacement** : Lignes 4762-4777

**Code vérifié** :
```python
# =============================================================================
# 2) Filtrer le mouvement détecté : "accepté seulement si proche"
# =============================================================================
movement_start_time = None
movement_is_valid = False

if pattern_result.get("movement"):
    mst = pd.Timestamp(pattern_result["movement"].get("start_time"))
    mst = mst.tz_localize("UTC") if mst.tzinfo is None else mst.tz_convert("UTC")
    
    delta_min = abs((cluster_ts - mst).total_seconds()) / 60.0
    
    # On accepte le mouvement s'il est dans une fenêtre raisonnable autour du cluster
    if delta_min <= 15:
        movement_start_time = mst
        movement_is_valid = True
```

**✅ Status** : Implémenté correctement
- `movement_start_time` initialisé à `None`
- `movement_is_valid` initialisé à `False`
- Normalisation du mouvement en UTC
- Calcul du delta en minutes
- Validation uniquement si `delta_min <= 15`

---

### **3. Warning seulement si mouvement "trop loin"**

**Emplacement** : Lignes 4779-4791

**Code vérifié** :
```python
# =============================================================================
# 3) Warning seulement si mouvement "trop loin"
# =============================================================================
if pattern_result.get("movement") and not movement_is_valid:
    mst = pd.Timestamp(pattern_result["movement"].get("start_time"))
    mst = mst.tz_localize("UTC") if mst.tzinfo is None else mst.tz_convert("UTC")
    delta_min = abs((cluster_ts - mst).total_seconds()) / 60.0
    st.warning(
        f"⚠️ Attention : Le mouvement détecté commence à {mst.strftime('%H:%M')} UTC, "
        f"alors que le cluster est à {cluster_ts.strftime('%H:%M')} UTC "
        f"(écart de {delta_min:.0f} minutes). "
        f"Vérifiez que c'est bien le bon mouvement ou réduisez le seuil min_pips."
    )
```

**✅ Status** : Implémenté correctement
- Warning affiché uniquement si mouvement détecté ET non validé
- Delta calculé et affiché en minutes
- Message clair avec heures UTC et recommandation

---

### **4. Ne passer `movement_start_time` à V8 que si validé**

**Emplacement** : Lignes 4828-4837

**Code vérifié** :
```python
# ⭐ movement_start_time est déjà validé (proximité <= 15 min)
# Si mouvement trop loin, movement_start_time = None (pas de pollution V8)

# Appeler adaptateur V8
v8_pred = predict_cluster_v8(
    date=pd.Timestamp(selected_cluster['date']),
    events_df=events_v8,
    db_path=DB_PATH,
    conn=None,
    movement_start_time=movement_start_time,  # ✅ Maintenant filtré (None si trop loin)
    trigger_z=1.0,
    theta=0.05
)
```

**✅ Status** : Implémenté correctement
- `movement_start_time` passé à V8 est déjà validé
- Si mouvement trop loin → `movement_start_time = None` → V8 ne reçoit pas de mouvement parasite
- Commentaire explicite dans le code

---

## ✅ Utilisation de `movement_start_time` validé pour baseline_time

**Emplacement** : Lignes 5043-5055

**Code vérifié** :
```python
# PRIORITÉ : Utiliser l'heure du mouvement validé (proximité <= 15 min)
if movement_is_valid and movement_start_time is not None:
    # Utiliser le mouvement validé
    baseline_time = movement_start_time
    if 'movement' in pattern_result and pattern_result['movement']:
        baseline_price = pattern_result['movement'].get('baseline_price')
        direction = pattern_result['movement'].get('direction', 'UP')
elif 'movement' in pattern_result and pattern_result['movement']:
    # Fallback : utiliser mouvement même si non validé (pour affichage)
    baseline_price = pattern_result['movement'].get('baseline_price')
    baseline_time = pattern_result['movement'].get('start_time')
    direction = pattern_result['movement'].get('direction', 'UP')
```

**✅ Status** : Implémenté correctement
- Priorité au mouvement validé pour `baseline_time`
- Fallback vers mouvement non validé uniquement pour affichage (pas pour V8)

---

## 🧪 Plan de Test Recommandé

### **Test 1 : Date 01.08.2025**

1. Ouvrir Planificateur
2. Sélectionner date 01.08.2025
3. Entrer actuals
4. Activer V8
5. **Vérifier** :
   - Delta affiché dans warning (si mouvement trop loin)
   - Que V8 reçoit `None` quand `delta > 15 min` (log temporaire si besoin)
   - Que le warning disparaît si on baisse `min_pips` et qu'un mouvement plus proche est détecté

### **Résultat Attendu**

- ✅ Warning peut rester si détecteur voit un mouvement trop loin
- ✅ **Mais ça ne pollue plus la prédiction V8** (V8 reçoit `None`)
- ✅ Si on baisse `min_pips`, mouvement plus proche détecté → warning disparaît

---

## 📋 Status Global du Développement

### ✅ Complété

- ✅ Adaptateur V8 OK + cache + SAFE warnings
- ✅ Calendrier : syntaxe OK + option V8 temps réel
- ✅ Planificateur : option V8 + bloc Straddle/Exit
- ✅ Validation mouvement (proximité <= 15 min)
- ✅ Protection V8 contre mouvements parasites

### 🔜 À Valider en Conditions Réelles

- 🔜 Cohérence timezone anchor vs prix
- 🔜 Robustesse movement detector (proximité)
- 🔜 Absence de faux patterns injectés à V8
- 🔜 Straddle/exit logique sur plusieurs patterns

---

**Version** : Validation Mouvement V1  
**Status** : ✅ Toutes modifications implémentées et vérifiées

