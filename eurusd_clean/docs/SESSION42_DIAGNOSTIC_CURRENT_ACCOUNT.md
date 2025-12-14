# 🔴 SESSION 42 - PROBLÈME CURRENT ACCOUNT WARNING

**Tokens : 130k / 190k (68%)**

---

## 📸 PROBLÈME OBSERVÉ

D'après les captures d'écran :
- ✅ CPI fonctionne (score 45/100)
- ❌ Current Account (DE) → Warning "Aucun événement historique trouvé pour Current Account"

---

## 🔍 DIAGNOSTIC

### Cause racine : Double problème de naming

1. **DB stocke** : `Current_Account` (avec underscore)
2. **event_families.py définit** : `'Current Account': r'(?i)(current account)'` (avec espace)
3. **identify_family() retourne** : `'Current Account'` (avec espace)
4. **load_precomputed_stats_from_db() charge** : `{'Current_Account': {...}}` (avec underscore)
5. **predict_impact_fast() cherche** : `'Current Account'` (avec espace)
6. **Résultat** : Not found → Fallback vers `predict_impact()` → Warning !

---

## ✅ SOLUTION

### Option 1 : Normaliser à la lecture (RECOMMANDÉ)

Modifier `load_precomputed_stats_from_db()` pour créer DEUX entrées :
- Une avec underscore (comme en DB)
- Une avec espace (comme en code)

```python
@st.cache_data(ttl=3600)
def load_precomputed_stats_from_db():
    """Charge stats pré-calculées depuis DB"""
    try:
        conn = duckdb.connect(get_db_path(), read_only=True)
        schema = conn.execute("DESCRIBE event_families").fetchall()
        cols = [col[0] for col in schema]
        
        if 'latency_median' not in cols:
            conn.close()
            return {}
            
        query = """
            SELECT DISTINCT family, latency_median, latency_p20, latency_p80,
                   ttr_median, ttr_p20, ttr_p80, mfe_p80, n_events_latency
            FROM event_families WHERE latency_median IS NOT NULL
        """
        results = conn.execute(query).fetchall()
        conn.close()
        
        stats_dict = {}
        for row in results:
            family_db = row[0]  # Nom tel que stocké en DB (avec underscore)
            stats = {
                'latency_median': row[1], 'latency_p20': row[2], 'latency_p80': row[3],
                'ttr_median': row[4], 'ttr_p20': row[5], 'ttr_p80': row[6],
                'mfe_p80': row[7] if row[7] else 10.0, 'n_events': row[8]
            }
            
            # 🔧 CORRECTION SESSION 42 : Double clé pour compatibilité
            stats_dict[family_db] = stats  # Avec underscore (DB)
            stats_dict[family_db.replace('_', ' ')] = stats  # Avec espace (code)
            
        return stats_dict
    except:
        return {}
```

### Option 2 : Essayer les deux dans predict_impact_fast()

```python
def predict_impact_fast(family, surprise, precomputed_stats, years_back=3):
    if family is None:
        return None
    
    # 🔧 CORRECTION SESSION 42 : Essayer avec espace ET underscore
    stats = None
    if family in precomputed_stats:
        stats = precomputed_stats[family]
    elif family.replace(' ', '_') in precomputed_stats:
        stats = precomputed_stats[family.replace(' ', '_')]
    
    if stats:
        # ... (reste du code)
        return {
            'predicted_pips': impact,
            # ...
        }
    else:
        result = predict_impact(family, surprise, years_back)
        if result:
            result['source'] = 'calculated'
        return result
```

---

## 🎯 RECOMMANDATION

**Option 1 (Double clé) est MEILLEURE** car :
- ✅ Résout le problème une fois pour toutes au chargement
- ✅ Pas besoin de modifier predict_impact_fast()
- ✅ Transparent pour le reste du code
- ✅ Fonctionne pour TOUTES les familles

---

## 📝 FICHIER À MODIFIER

`fx_impact_app/streamlit_app/pages/4_Planificateur_STABLE_0159_PERFECT.py`

**Ligne ~120** : Modifier `load_precomputed_stats_from_db()`

---

**Tokens : 130k / 190k (68%)**

*Diagnostic Session 42 - 22 octobre 2025*
