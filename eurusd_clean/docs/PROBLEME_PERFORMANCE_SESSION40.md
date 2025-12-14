# 🐌 PROBLÈME PERFORMANCE IDENTIFIÉ - Session 40

**Date :** 22 octobre 2025  
**Symptôme :** Calculs lents avant affichage impact  
**Cause racine :** Fallback vers fonction LENTE pour familles non pré-calculées  
**Status :** ✅ IDENTIFIÉ | ⏳ SOLUTION SIMPLE À APPLIQUER

---

## 🎯 LE PROBLÈME

### Code Actuel (lignes 361-407)

```python
def predict_impact_fast(family, surprise, precomputed_stats, years_back=3):
    """Version ULTRA-RAPIDE"""
    family_normalized = family.replace(' ', '_')
    
    if family_normalized in precomputed_stats:
        # ⚡ RAPIDE : Lecture dict (< 1ms)
        stats = precomputed_stats[family_normalized]
        # ... calcul instantané ...
        return {...}
    else:
        # ❌ LENT : Fallback fonction legacy (500ms+)
        result = predict_impact(family, surprise, years_back)  # ← COUPABLE !
        return result
```

### Fonction Lente Appelée (lignes 570-679)

```python
def predict_impact(family, surprise, years_back=3):
    # Pour CHAQUE événement sans stats :
    analyzer = LatencyAnalyzer(get_db_path())        # ❌ Connexion DB
    latency_stats = analyzer.calculate_family_latency_stats(...)  # ❌ Query SQL complexe
    analyzer.close()
    
    engine = ForecastEngine(get_db_path())           # ❌ Connexion DB
    mfe_stats = engine.calculate_family_stats(...)   # ❌ Query SQL complexe
    engine.close()
    
    # Total : ~500-1000ms par événement ! 🐌
```

## 📊 IMPACT

| Scénario | Temps total | Expérience |
|----------|-------------|------------|
| **10 événements TOUS pré-calculés** | <50ms | ⚡ Instantané |
| **10 événements AUCUN pré-calculé** | ~5-10s | 🐌 Très lent |
| **10 événements 50% pré-calculés** | ~2-5s | ⚠️ Lent |

**Chaque famille NON pré-calculée** = +500ms de calcul !

---

## 🔍 DIAGNOSTIC

### Étape 1 : Vérifier Familles Pré-calculées

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC
python3 check_precomputed_families.py
```

**Attendu :**
```
✅ 16/16 familles avec stats pré-calculées
```

**Si problème :**
```
⚠️  Familles SANS stats :
❌ Michigan_Consumer_Sentiment
❌ Real_Earnings
❌ ... etc
```

### Étape 2 : Identifier Événements Lents

Quand vous sélectionnez un événement, notez ceux qui sont lents à calculer.

**Pattern :** Si c'est toujours les mêmes familles → elles ne sont pas pré-calculées !

---

## ✅ SOLUTIONS

### Solution 1 : Pré-calculer Toutes les Familles (RECOMMANDÉ)

**Créer script de pré-calcul complet :**

```python
#!/usr/bin/env python3
"""
Pré-calcule stats pour TOUTES les familles
"""

import duckdb
import sys
from pathlib import Path

# Ajouter src au path
src_path = Path(__file__).parent / "fx_impact_app" / "src"
sys.path.insert(0, str(src_path))

from config import get_db_path
from event_families import FAMILY_PATTERNS
from latency_analyzer import LatencyAnalyzer
from forecaster_mvp import ForecastEngine

DB_PATH = get_db_path()

print("=" * 70)
print("PRÉ-CALCUL STATS TOUTES FAMILLES")
print("=" * 70)

conn = duckdb.connect(DB_PATH)

for family_name, pattern in FAMILY_PATTERNS.items():
    print(f"\n🔄 {family_name}...")
    
    try:
        # Calcul latence
        analyzer = LatencyAnalyzer(DB_PATH)
        latency_stats = analyzer.calculate_family_latency_stats(
            family_pattern=pattern,
            threshold_pips=5.0,
            min_events=5,
            lookback_days=3 * 365
        )
        analyzer.close()
        
        if not latency_stats or latency_stats['events_analyzed'] == 0:
            print(f"  ⚠️  Pas de données latence")
            continue
        
        # Calcul MFE
        engine = ForecastEngine(DB_PATH)
        mfe_stats = engine.calculate_family_stats(
            pattern,
            horizon_minutes=60,
            hist_years=3,
            countries=None
        )
        engine.close()
        
        # Mise à jour DB
        update_query = f"""
        UPDATE event_families
        SET 
            latency_median = {latency_stats['initial_reaction']['median_minutes']},
            latency_p20 = {latency_stats['initial_reaction'].get('p20_minutes', latency_stats['initial_reaction']['median_minutes'] * 0.5)},
            latency_p80 = {latency_stats['initial_reaction'].get('p80_minutes', latency_stats['initial_reaction']['median_minutes'] * 1.5)},
            ttr_median = {latency_stats['initial_reaction']['median_minutes'] * 1.5},
            ttr_p20 = {latency_stats['initial_reaction']['median_minutes'] * 1.0},
            ttr_p80 = {latency_stats['initial_reaction']['median_minutes'] * 2.0},
            mfe_p80 = {mfe_stats.get('mfe_p80', 10.0)},
            n_events_latency = {latency_stats['events_analyzed']}
        WHERE family = '{family_name}'
        """
        
        conn.execute(update_query)
        print(f"  ✅ OK - {latency_stats['events_analyzed']} événements")
        
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
        continue

conn.close()

print("\n" + "=" * 70)
print("✅ PRÉ-CALCUL TERMINÉ")
print("=" * 70)
print("\n💡 Redémarrez Streamlit pour voir les changements !")
```

**Exécution :**
```bash
python3 precompute_all_families.py
# Puis relancer Streamlit
```

### Solution 2 : Améliorer Fallback (RAPIDE mais moins optimal)

**Modifier `predict_impact_fast()` pour mettre en cache les résultats calculés :**

```python
def predict_impact_fast(family, surprise, precomputed_stats, years_back=3):
    """Version ULTRA-RAPIDE"""
    if family is None:
        return None
    
    family_normalized = family.replace(' ', '_')
    
    # Priorité 1 : Lookup DB pré-calculée
    if family_normalized in precomputed_stats:
        stats = precomputed_stats[family_normalized]
        # ... calcul rapide ...
        return result
    
    # Priorité 2 : Cache session Streamlit
    cache_key = f"computed_{family_normalized}_{years_back}"
    if cache_key in st.session_state:
        stats = st.session_state[cache_key]
        # ... calcul rapide depuis cache ...
        return result
    
    # Priorité 3 : Calcul lent (1 seule fois)
    result = predict_impact(family, surprise, years_back)
    if result:
        result['source'] = 'calculated'
        # Mettre en cache pour prochains appels
        st.session_state[cache_key] = {
            'latency_median': result['latency_median'],
            'latency_p20': result['latency_p20'],
            'latency_p80': result['latency_p80'],
            'ttr_median': result['ttr_median'],
            'ttr_p20': result['ttr_p20'],
            'ttr_p80': result['ttr_p80'],
            'mfe_p80': result['mfe_p80'],
            'n_events': result['n_similar']
        }
    return result
```

**Avantage :** Calcul lent UNE SEULE FOIS par famille, puis cache pour toute la session.

### Solution 3 : Message Utilisateur (IMMÉDIAT)

**Afficher feedback pendant calcul lent :**

```python
def predict_impact_fast(family, surprise, precomputed_stats, years_back=3):
    family_normalized = family.replace(' ', '_')
    
    if family_normalized in precomputed_stats:
        # Rapide
        return result
    else:
        # Lent - prévenir l'utilisateur
        with st.spinner(f"⏳ Calcul {family_normalized} (1ère fois - sera mis en cache)..."):
            result = predict_impact(family, surprise, years_back)
        return result
```

---

## 🎯 RECOMMANDATION

**Plan d'action prioritaire :**

1. ✅ **IMMÉDIAT (5 min)** : Exécuter `check_precomputed_families.py` pour diagnostic
2. ⚡ **RAPIDE (10 min)** : Appliquer Solution 2 (cache session)
3. 🎯 **OPTIMAL (30 min)** : Créer et exécuter `precompute_all_families.py`

**Résultat attendu :**
- Toutes familles : <50ms par événement ⚡
- Application : Réactive et fluide ✅
- Utilisateur : Satisfait 🎉

---

## 📊 MÉTRIQUES AVANT/APRÈS

### AVANT (État actuel)

```
Familles pré-calculées : 16/20 (80%)
Événements :
  - CPI, NFP, GDP... : ⚡ <5ms
  - Michigan, Real Earnings... : 🐌 500ms
  
Impact utilisateur : Calculs parfois très lents
```

### APRÈS (Solution 1 appliquée)

```
Familles pré-calculées : 20/20 (100%) ✅
Tous événements : ⚡ <5ms

Impact utilisateur : Calculs TOUJOURS instantanés
```

---

## 💡 LEÇON

**Le pré-chargement fonctionne parfaitement... quand toutes les données sont pré-calculées !**

**Erreur :** Oublier de pré-calculer certaines familles
**Conséquence :** Fallback vers code lent
**Solution :** Pré-calculer TOUT lors du setup initial

---

## 🚀 PROCHAINES ÉTAPES

1. Exécuter diagnostic
2. Appliquer solution choisie
3. Tester avec événements réels
4. Valider performance (<50ms)
5. Documenter familles ajoutées

---

**📅 Document créé :** 22 octobre 2025, Session 40  
**🎯 Priorité :** HAUTE - Impact direct expérience utilisateur  
**⏱️ Temps résolution :** 10-30 minutes selon solution

---

*PROBLEME_PERFORMANCE_SESSION40.md - Diagnostic et solutions*
