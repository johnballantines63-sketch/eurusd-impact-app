# Usage du Moteur Réel V3.2.1 depuis Streamlit

**Date :** 2025-12-12  
**Version :** V3.2.1

---

## 🚀 Appel depuis Streamlit

### Code d'intégration

Le moteur réel est déjà intégré dans `app/streamlit_app.py`. Voici comment il est appelé :

```python
from app.compute_real_prediction import compute_real_prediction

pred = compute_real_prediction(
    date_str="2024-09-11",           # Date au format YYYY-MM-DD
    actuals={                         # Dict avec clés event_uid
        "US_CPI|2024-09-11T14:30:00": 3.2,
        "US_Current_Account|2024-09-11T14:45:00": -210.0,
    },
    conn=conn,                        # DuckDB connection
    model_path=None                   # Optionnel : chemin modèle (défaut = daily_risk_signal_v3_2_1)
)
```

---

## 📋 Format des Actuals

### Clé stable : `event_uid`

Les actuals sont indexés par une clé stable :

```python
event_uid = f"{event_key}|{ts_local_iso}"
```

**Exemple :**
- `event_key` = `"US_CPI"`
- `ts_local` = `2024-09-11 14:30:00`
- `event_uid` = `"US_CPI|2024-09-11T14:30:00"`

**Pourquoi cette clé ?**
- ✅ Stable : ne dépend pas de l'index DataFrame
- ✅ Portable : fonctionne après filtres/tris/joins
- ✅ Unique : event_key + timestamp garantit l'unicité

### Construction dans Streamlit UI

Dans `streamlit_app.py`, la clé est construite automatiquement :

```python
for idx, r in core_df.iterrows():
    ts_iso = pd.to_datetime(r["ts_local"]).isoformat()
    event_key = str(r.get("event_key") or r.get("event_title") or "UNKNOWN")
    event_uid = f"{event_key}|{ts_iso}"
    
    # Saisie actual
    val = st.text_input("Actual", key=f"actual_{event_uid}")
    if val.strip():
        st.session_state[actuals_key][event_uid] = float(val)
```

---

## 🔄 Workflow Complet

### 1. Sélectionner une date

L'UI charge automatiquement :
- Les événements de la journée depuis `events_with_ts_local_v1`
- La prédiction de volatilité depuis `daily_risk_signal_v3_2_1`

### 2. Saisir les actuals

Pour chaque event core :
- Affiche : `ts_local`, `country`, `event_key`, `previous`, `forecast`
- Saisie : `actual` (float)
- Stockage : `st.session_state[actuals_key][event_uid] = float(val)`

### 3. Activer le moteur réel

Cocher la checkbox :
```
🟢 Utiliser moteur réel V3.2.1
```

### 4. Recalculer

Cliquer sur :
```
[Recalculer prédiction]
```

**Ce qui se passe :**
1. Appel à `compute_real_prediction(date_str, actuals, conn)`
2. Détection de clusters (fenêtre glissante 30 min)
3. Calcul d'impact basé sur actuals saisis
4. Détection de pattern (single_wave, double_wave, zigzag)
5. Calcul de direction (BUY/SELL/NO_TRADE)
6. Validation Pydantic (si disponible)
7. Retour d'un dict compatible UI

### 5. Afficher le résultat

L'UI affiche :
- **Direction** : BUY / SELL / NO_TRADE
- **Pattern** : single_wave / double_wave / zigzag / unknown
- **Impact (pips)** : Impact prédit en pips
- **Risk score** : Score de risque normalisé [0, 1]
- **Entry/Exit windows** : Fenêtres temporelles
- **Targets** : take_profit / stop_loss

---

## ⚠️ Gestion d'Erreurs

### Erreur lors du calcul

Si une erreur survient :
1. ✅ Message d'erreur affiché
2. ✅ Détails disponibles dans expander
3. ✅ Fallback automatique vers placeholder

**Exemple :**
```python
try:
    pred = compute_real_prediction(...)
except Exception as e:
    st.error(f"❌ Erreur moteur réel: {e}")
    with st.expander("🔍 Détails"):
        st.code(traceback.format_exc())
    # Fallback placeholder
```

### Impact = 0 avec actuals saisis

Si `impact_pred_pips == 0` mais que des actuals sont saisis :
- ⚠️ Warning affiché
- 🔍 Vérifier que les `event_uid` correspondent bien

**Causes possibles :**
- `event_key` ne correspond pas
- `ts_local` ne correspond pas (format/date)
- Actuals non retrouvés → impact=0

---

## 🧪 Exemple d'Usage Complet

### Scénario : CPI US le 2024-09-11

**1. Saisie actual :**
- Event : `US_CPI` à `14:30:00`
- Previous : `3.1`
- Forecast : `3.0`
- Actual saisi : `3.2`

**2. Construction event_uid :**
```python
event_uid = "US_CPI|2024-09-11T14:30:00"
actuals = {"US_CPI|2024-09-11T14:30:00": 3.2}
```

**3. Appel moteur :**
```python
pred = compute_real_prediction(
    "2024-09-11",
    {"US_CPI|2024-09-11T14:30:00": 3.2},
    conn
)
```

**4. Résultat attendu :**
```python
{
    "direction": "BUY",  # ou SELL selon surprise
    "pattern": "single_wave",
    "impact_pred_pips": 50.0,  # Exemple
    "risk_score": 0.72,
    ...
}
```

---

## 📝 Notes Importantes

### Format de retour

Le moteur retourne un **dict** compatible avec :
- ✅ UI Streamlit (colonnes attendues)
- ✅ Contrat Pydantic `DayPrediction` (si disponible)

### Pas d'écriture DB

⚠️ **Le moteur ne modifie pas la DB.**  
Les actuals restent en session Streamlit uniquement.

### Clustering automatique

Le moteur détecte automatiquement les clusters :
- Fenêtre glissante : 30 minutes
- Regroupe les events proches temporellement
- Calcule l'impact global par cluster

---

## 🔗 Voir Aussi

- `docs/FIXES_MOTEUR_REEL_V3_2_1.md` : Bugs corrigés
- `app/compute_real_prediction.py` : Code du moteur
- `scripts/contracts/v3_2_1_contract.py` : Contrat Pydantic

---

**Document créé le :** 2025-12-12  
**Version :** V3.2.1

