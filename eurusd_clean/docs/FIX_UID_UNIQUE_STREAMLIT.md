# Fix UID Unique pour Éviter Collisions Streamlit

**Date :** 2025-12-12  
**Version :** V3.2.1  
**Statut :** ✅ FIX APPLIQUÉ

---

## 🐛 Problème Identifié

### StreamlitDuplicateElementKey

Quand plusieurs événements ont le même `event_key` et le même `ts_local`, ils partagent le même `event_uid`, ce qui crée :

1. **Collision dans les widgets Streamlit** : même clé pour `st.text_input`
2. **Collision dans le stockage** : le dernier actual écrase le premier dans `st.session_state[actuals_key][event_uid]`

**Exemple :**
- Event 1 : `event_key="CPI"`, `ts_local="2024-09-11 14:30:00"` → `event_uid="CPI|2024-09-11T14:30:00"`
- Event 2 : `event_key="CPI"`, `ts_local="2024-09-11 14:30:00"` → `event_uid="CPI|2024-09-11T14:30:00"` ❌ **DOUBLON**

---

## ✅ Solution Appliquée

### 1. UID Unique dans UI (`streamlit_app.py`)

**Avant :**
```python
event_uid = f"{event_key}|{ts_iso}"
streamlit_key = f"actual_{selected_date}_{idx}_{event_uid}"
```

**Après :**
```python
event_uid = f"{event_key}|{ts_iso}|row={idx}"
streamlit_key = f"actual_{selected_date}_{idx}"
```

**Résultat :**
- Chaque event a un `event_uid` unique grâce à `row={idx}`
- Stockage sans collision dans `st.session_state[actuals_key][event_uid]`
- Clé Streamlit simplifiée mais toujours unique

---

### 2. Recherche avec Fallback dans Moteur (`compute_real_prediction.py`)

**Dans `calculate_cluster_direction_impact()` :**

**Avant :**
```python
event_uid = f"{event_key}|{ts}"
actual_val = actuals.get(event_uid)
```

**Après :**
```python
event_uid = f"{event_key}|{ts}|row={event.name}"
actual_val = actuals.get(event_uid)

# Fallback compat (anciennes sessions sans row=)
if actual_val is None:
    actual_val = actuals.get(f"{event_key}|{ts}")
```

**Dans construction `core_events_list` :**

Même logique avec `event.name` (index du DataFrame).

---

## 🔄 Compatibilité

### Backward Compatible

Le moteur cherche d'abord la nouvelle clé (`...|row=X`), puis fait un fallback vers l'ancienne clé (`...` sans `row=`) si nécessaire.

**Avantages :**
- ✅ Les nouvelles saisies utilisent la clé unique
- ✅ Les anciennes saisies (sans `row=`) fonctionnent toujours (fallback)
- ✅ Pas de perte de données lors de la migration

---

## 🧪 Test de Validation

**Test UID unique avec duplications :**
```python
df_test = pd.DataFrame({
    'ts_local': pd.to_datetime(['2024-09-11 14:30:00', '2024-09-11 14:30:00']),
    'event_key': ['CPI', 'CPI'],  # Dupliqué
})

# Résultat :
# Row 0: CPI|2024-09-11T14:30:00|row=0 ✅
# Row 1: CPI|2024-09-11T14:30:00|row=1 ✅
```

**Test fallback :**
```python
actuals = {
    'CPI|2024-09-11T14:30:00|row=0': 3.2,  # Nouvelle clé
    'OLD_KEY|2024-09-11T15:00:00': 2.8,    # Ancienne clé
}

# Recherche avec fallback fonctionne ✅
```

---

## 📝 Notes Techniques

### `event.name` dans pandas

Dans `iterrows()`, `event.name` correspond à l'index du DataFrame :
- Si DataFrame indexé par défaut (0, 1, 2...) → `event.name = 0, 1, 2...`
- Si DataFrame indexé personnalisé → `event.name = valeur de l'index`

**Usage :**
```python
for idx, event in df.iterrows():
    # idx = index (peut être non-int si index personnalisé)
    # event.name = idx (alias)
    event_uid = f"{event_key}|{ts}|row={event.name}"
```

---

## 🔗 Fichiers Modifiés

1. **`app/streamlit_app.py`**
   - Ligne ~396 : Construction `event_uid` avec `|row={idx}`
   - Ligne ~398 : Simplification `streamlit_key`

2. **`app/compute_real_prediction.py`**
   - Ligne ~165 : Recherche avec fallback dans `calculate_cluster_direction_impact()`
   - Ligne ~427 : Recherche avec fallback dans construction `core_events_list`

---

## ✅ Checklist

- [x] UID unique dans UI (`|row={idx}`)
- [x] Recherche avec fallback dans moteur
- [x] Compatibilité backward (anciennes clés)
- [x] Tests validés (duplications + fallback)
- [x] Syntaxe Python OK

---

**Document créé le :** 2025-12-12  
**Version :** V3.2.1
