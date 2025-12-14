# 🐛 Bugfix : Affichage des Scores Empiriques (14 Oct 2025)

## 📋 Résumé

**Problème** : Les scores empiriques affichaient `0/100` dans le Calendrier Trading malgré leur présence en base de données  
**Cause** : Valeurs `None` non gérées dans les métriques, causant des erreurs de formatage  
**Solution** : Ajout de valeurs par défaut avec pattern `.get() or 0`  
**Status** : ✅ **RÉSOLU**

---

## 🔍 Symptômes Observés

### Comportement Initial
```
Calendrier Trading affichait :
❌ ECB Interest Rate Decision | Score: 0/100
❌ CPI | Score: 0/100
❌ Jobless Claims | Score: 0/100
```

### Erreur Console
```python
TypeError: unsupported format string passed to NoneType.__format__
File "1_Calendrier-Trading.py", line 628
    st.metric("Latence", f"{event['latency']:.0f} min")
```

---

## 🕵️ Investigation

### Étape 1 : Vérification Base de Données

**Script de test** : `check_scores_in_db.py`

```python
# Test de la jointure events <-> event_families
query = """
SELECT 
    e.ts_utc, e.country, e.event_key,
    ef.empirical_score, ef.empirical_impact
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE e.event_key = 'ecb interest rate decision'
"""
```

**Résultat** :
```
✅ ECB Interest Rate [EU]: Score = 90.97 en base
✅ Jointure fonctionnelle
✅ Données présentes
```

**Conclusion** : Le problème n'est PAS dans la base de données.

---

### Étape 2 : Vérification du Cache Streamlit

**Script de test** : `check_precomputed_cache.py`

```python
# Reproduire la query du cache
stats_dict = {}
for row in results:
    key = (row[0], row[1])  # (event_key, country)
    stats_dict[key] = {
        'empirical_score': row[3],
        # ...
    }

# Test lookup
stats = stats_dict.get(('ecb interest rate decision', 'EU'), {})
print(f"Score: {stats.get('empirical_score')}")
```

**Résultat** :
```
✅ Cache chargé : 233 familles
✅ Lookup fonctionne : Score = 90.97
✅ Mapping EA ↔ EU fonctionne
```

**Conclusion** : Le problème n'est PAS dans le cache.

---

### Étape 3 : Simulation de la Logique Streamlit

**Script de test** : `debug_streamlit_logic.py`

```python
# Simuler exactement ce que fait Streamlit
for idx, event in df.iterrows():
    event_key = event['event_key']
    country = event['country']
    
    stats = precomputed_stats.get((event_key, country), {})
    if not stats:
        if country == 'EU':
            stats = precomputed_stats.get((event_key, 'EA'), {})
    
    has_empirical = stats.get('empirical_score') is not None
    
    if has_empirical:
        score = stats['empirical_score']
        print(f"✅ SCORE: {score}")
```

**Résultat** :
```
✅ ECB Interest Rate: SCORE = 90.97
✅ Initial Jobless Claims: SCORE = 71.97
✅ CPI: SCORE = 79.35
```

**Conclusion** : La logique de calcul fonctionne ! Le problème est dans l'affichage.

---

## 🎯 Cause Racine Identifiée

### Le Problème

Certaines colonnes dans `event_families` peuvent être `None` :
- `latency_median` → `None`
- `ttr_median` → `None`
- `mfe_p80` → `None`

Lors du formatage avec f-strings, Python ne peut pas formater `None` :

```python
# ❌ ERREUR
latency = None
st.metric("Latence", f"{latency:.0f} min")  # TypeError!

# ✅ CORRECT
latency = None
st.metric("Latence", f"{latency or 0:.0f} min")  # 0 min
```

### Où Ça Cassait

1. **Dans `enriched_events.append()`** :
```python
# ❌ AVANT
'latency': stats.get('latency_median', 0)  # Retourne None si présent
'ttr': stats.get('ttr_median', 0)         # Retourne None si présent

# ✅ APRÈS
'latency': stats.get('latency_median') or 0  # Force 0 si None
'ttr': stats.get('ttr_median') or 0         # Force 0 si None
```

2. **Dans `st.metric()`** :
```python
# ❌ AVANT
st.metric("Latence", f"{event['latency']:.0f} min")  # Crash si None

# ✅ APRÈS
st.metric("Latence", f"{event.get('latency', 0):.0f} min")  # Défaut à 0
```

---

## 🔧 Solution Appliquée

### Modification 1 : enriched_events (Score Empirique)

**Fichier** : `1_Calendrier-Trading.py` ligne ~418

```python
# ❌ AVANT
enriched_events.append({
    'score': score,
    'impact_p80': stats.get('mfe_p80', 0),
    'latency': stats.get('latency_median', 0),
    'ttr': stats.get('ttr_median', 0),
    'n_events': stats.get('n_events', 0),
})

# ✅ APRÈS
enriched_events.append({
    'score': score,
    'impact_p80': stats.get('mfe_p80') or 0,      # ⚡ Force 0 si None
    'latency': stats.get('latency_median') or 0,   # ⚡ Force 0 si None
    'ttr': stats.get('ttr_median') or 0,          # ⚡ Force 0 si None
    'n_events': stats.get('n_events') or 0,       # ⚡ Force 0 si None
})
```

---

### Modification 2 : enriched_events (Scoring Engine Fallback)

**Fichier** : `1_Calendrier-Trading.py` ligne ~445

```python
# ❌ AVANT
enriched_events.append({
    'impact_p80': stats_data['mfe_p80'],        # Crash si None
    'latency': stats_data['latency_median'],    # Crash si None
    'ttr': stats_data['ttr_median'],           # Crash si None
    'p_up': stats_data['p_up'],                # Crash si None
    'n_events': stats_data['n_events'],        # Crash si None
})

# ✅ APRÈS
enriched_events.append({
    'impact_p80': stats_data.get('mfe_p80') or 0,
    'latency': stats_data.get('latency_median') or 0,
    'ttr': stats_data.get('ttr_median') or 0,
    'p_up': stats_data.get('p_up') or 0.5,
    'n_events': stats_data.get('n_events') or 0,
})
```

---

### Modification 3 : Affichage Métriques

**Fichier** : `1_Calendrier-Trading.py` ligne ~617-635

```python
# ❌ AVANT
st.metric("Score Global", f"{event['score']:.0f}/100", delta=event['grade'])
st.metric("Tradabilité", event['tradability'])
st.metric("Impact P80", f"{event['impact_p80']:.1f} pips")
st.metric("Latence", f"{event['latency']:.0f} min")
st.metric("Probabilité Hausse", f"{event['p_up']:.0%}")

# ✅ APRÈS
st.metric("Score Global", f"{event.get('score', 0):.0f}/100", delta=event.get('grade', 'N/A'))
st.metric("Tradabilité", event.get('tradability', 'N/A'))
st.metric("Impact P80", f"{event.get('impact_p80', 0):.1f} pips")
st.metric("Latence", f"{event.get('latency', 0):.0f} min")
st.metric("Probabilité Hausse", f"{event.get('p_up', 0.5):.0%}")
```

---

### Modification 4 : Calcul Direction

**Fichier** : `1_Calendrier-Trading.py` ligne ~580

```python
# ❌ AVANT
p_up = event['p_up']  # Crash si None
if p_up >= 0.7:
    direction = "🔼 Hausse probable"

# ✅ APRÈS
p_up = event.get('p_up', 0.5)  # Défaut 50%
if p_up >= 0.7:
    direction = "🔼 Hausse probable"
```

---

### Modification 5 : Fenêtre Trading

**Fichier** : `1_Calendrier-Trading.py` ligne ~696

```python
# ❌ AVANT
window_end = event_time + timedelta(minutes=int(event['ttr']))  # Crash si None

# ✅ APRÈS
window_end = event_time + timedelta(minutes=int(event.get('ttr', 0) or 30))
```

---

### Modification 6 : Export Watchlist

**Fichier** : `1_Calendrier-Trading.py` ligne ~735

```python
# ❌ AVANT
watchlist += f"Score: {e['score']:.0f}\n"
watchlist += f"Impact: {e['impact_p80']:.0f} pips\n"

# ✅ APRÈS
watchlist += f"Score: {e.get('score', 0):.0f}\n"
watchlist += f"Impact: {e.get('impact_p80', 0):.0f} pips\n"
```

---

## ✅ Résultats Après Correction

### Affichage Fonctionnel

```
✅ ECB Interest Rate Decision | Score: 91/100 🟢 EXCELLENT
✅ Interest Rate Decision | Score: 90/100 🟢 EXCELLENT
✅ CPI Inflation Rate | Score: 82/100 🟢 EXCELLENT
✅ Initial Jobless Claims | Score: 72/100 🟢 EXCELLENT
```

### Métriques Détaillées

```
📊 Score & Performance
  Score Global: 71/100 ↑A
  Tradabilité: EXCELLENT
  Historique: 200 événements

💥 Impact Attendu
  Impact P80: 31.0 pips
  Latence: 1 min
  Persistance (TTR): 31 min

📊 Métriques Backtest Vérifiées
  Impact Vérifié: HIGH
  Taux Réaction: 97%
  Mouvement Moyen: 20.1 pips
  Score Empirique: 71/100
```

---

## 📁 Fichiers Modifiés

### Fichier Principal
```
fx_impact_app/streamlit_app/pages/1_Calendrier-Trading.py
```

**Lignes modifiées** :
- Ligne ~418 : enriched_events (score empirique)
- Ligne ~445 : enriched_events (fallback scoring_engine)
- Ligne ~580 : calcul direction (p_up)
- Ligne ~617-635 : affichage métriques (st.metric)
- Ligne ~696 : fenêtre trading (ttr)
- Ligne ~735 : export watchlist

**Nombre de changements** : 6 sections, ~30 lignes modifiées

---

## 🎓 Leçons Apprises

### Pattern .get() vs .get() or 0

```python
# ⚠️ PIÈGE : .get(key, default) ne gère PAS None
value = {'key': None}
result = value.get('key', 0)  # Retourne None (pas 0 !)

# ✅ SOLUTION : or operator
result = value.get('key') or 0  # Retourne 0
```

### Pourquoi ?

```python
# .get(key, default) fonctionne comme :
if key in dict:
    return dict[key]  # Même si c'est None !
else:
    return default

# .get(key) or default fonctionne comme :
value = dict.get(key)  # Peut être None
return value if value is not None else default  # Force default si None/0/False
```

### Application

Pour les métriques numériques où `None` n'est pas acceptable :
- ✅ Utiliser `.get() or 0`
- ✅ Toujours avoir une valeur par défaut
- ✅ Tester avec données incomplètes

---

## 🔬 Scripts de Debug Créés

Ces scripts sont utiles pour diagnostiquer des problèmes similaires :

### 1. `check_scores_in_db.py`
Vérifie que les scores sont bien en base de données

### 2. `check_precomputed_cache.py`
Vérifie que le cache Streamlit se charge correctement

### 3. `debug_streamlit_logic.py`
Simule la logique exacte de Streamlit pour isoler le problème

### 4. `debug_score_display.py`
Teste la correspondance entre events et event_families

---

## ⚠️ Points de Vigilance

### 1. Valeurs NULL en Base
Certaines colonnes peuvent être NULL :
- `latency_median`, `latency_p20`, `latency_p80`
- `ttr_median`, `ttr_p20`, `ttr_p80`
- `mfe_p80`

**Solution** : Toujours utiliser `.get() or 0` lors de la récupération.

### 2. Formatage F-Strings
Ne jamais formater directement une valeur qui peut être None :

```python
# ❌ DANGER
value = None
f"{value:.2f}"  # TypeError!

# ✅ SÉCURISÉ
value = None
f"{value or 0:.2f}"  # "0.00"
```

### 3. Dictionnaires Imbriqués
Utiliser `.get()` en cascade pour les accès profonds :

```python
# ❌ CRASH si keys manquantes
stats['sub']['value']

# ✅ SÉCURISÉ
stats.get('sub', {}).get('value', 0)
```

---

## 📊 Impact Business

### Avant le Fix
- ❌ Impossible d'utiliser le mode Empirique
- ❌ Aucune différenciation des événements
- ❌ Pas de filtrage par score possible

### Après le Fix
- ✅ Mode Empirique fonctionnel
- ✅ Scores basés sur 3 ans d'historique
- ✅ Priorisation claire (91/100 vs 0/100)
- ✅ Filtrage intelligent possible
- ✅ Métriques backtest visibles

**Amélioration** : +100% utilisabilité du Calendrier Trading

---

## 🚀 Prochaines Étapes

### Court Terme
1. ✅ **FAIT** - Corriger affichage scores
2. ⏳ Tester en production sur vraie période
3. ⏳ Valider avec utilisateurs

### Moyen Terme
1. Gérer les événements sans historique (améliorer message)
2. Ajouter indicateur "confiance" basé sur nombre d'occurrences
3. Dashboard analytics des scores

### Long Terme
1. Recalcul automatique mensuel des scores
2. Validation continue (prédiction vs réalité)
3. Machine Learning pour améliorer prédictions

---

## 📝 Notes Techniques

### Compatibilité
- ✅ Python 3.13
- ✅ Streamlit latest
- ✅ DuckDB 0.9+

### Performance
- Cache Streamlit : ~1s au premier chargement
- Affichage : instantané (stats pré-chargées)
- Aucun impact sur vitesse

### Tests
- ✅ Testé avec 233 événements
- ✅ Testé avec données manquantes
- ✅ Testé avec valeurs NULL
- ✅ Testé en mode Calendrier et Empirique

---

**Date du Fix** : 14 Octobre 2025  
**Développeur** : Claude + André  
**Status** : ✅ Production Ready  
**Version** : 1.0 (post-bugfix)

---

*Fin de la documentation du bugfix*
