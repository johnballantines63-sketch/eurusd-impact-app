# 🔧 Correction Bug Affichage Scores - Calendrier Trading

**Date**: 13 octobre 2025  
**Status**: ✅ CORRIGÉ - EN ATTENTE DE TEST

---

## 🐛 Problème Identifié

### Symptôme
- **Capture d'écran montre**: Tous les événements affichent `Score: 0/100`
- **Attendu**: ECB devrait afficher `Score: 91/100`

### Cause Racine
Le code chargeait bien les `empirical_score` depuis la DB, MAIS:
1. ❌ Il **recalculait** un score via `scoring_engine` 
2. ❌ Au lieu d'utiliser directement `empirical_score` de la DB
3. ❌ Le scoring_engine ne retrouvait pas les bonnes stats → retournait 0

**Ligne problématique** (ligne ~388):
```python
'score': score_data['score'],  # ❌ Vient de scoring_engine
```

**Au lieu de**:
```python
'score': stats['empirical_score'],  # ✅ Directement de la DB
```

---

## ✅ Solution Appliquée

### Modification du fichier
**Fichier**: `fx_impact_app/streamlit_app/pages/1_Calendrier-Trading.py`

### Changements
1. ✅ Lecture directe de `empirical_score` depuis `st.session_state.precomputed_stats`
2. ✅ Mapping automatique EA ↔ EU pour trouver les stats (comme dans le calcul)
3. ✅ Fallback sur `scoring_engine` seulement si pas de score empirique
4. ✅ Calcul de `grade` et `tradability` basé sur `empirical_score`

### Code corrigé
```python
# ✅ UTILISER DIRECTEMENT empirical_score de la DB
precomputed = st.session_state.get('precomputed_stats', {})
event_key = event['event_key']
country = event['country']

# ⚡ MAPPING EA ↔ EU pour trouver les stats
stats = precomputed.get((event_key, country), {})
if not stats:
    if country == 'EU':
        stats = precomputed.get((event_key, 'EA'), {})
    elif country == 'EA':
        stats = precomputed.get((event_key, 'EU'), {})

# ✅ Score prioritaire: empirical_score de la DB
has_empirical = stats.get('empirical_score') is not None

if has_empirical:
    # Utiliser le score empirique directement
    score = stats['empirical_score']
    
    # Calculer grade et tradability basés sur empirical_score
    if score >= 70:
        grade = 'A'
        tradability = 'EXCELLENT'
    # ... etc
```

---

## 🧪 Tests à Effectuer

### Test 1: Vérifier la DB (Avant Streamlit)
```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC
python3 test_scores_affichage.py
```

**Résultats attendus**:
- ✅ ECB [EA] et [EU]: Score 91.0, Impact HIGH
- ✅ Couverture globale: ~96.7%
- ✅ Top 10 inclut ECB en position #1-3

### Test 2: Interface Streamlit
```bash
streamlit run fx_impact_app/streamlit_app/Home.py
```

**Checklist**:
- [ ] Aller à "Calendrier Trading"
- [ ] Sélectionner "📊 Empirique (historique)"
- [ ] Configurer: 
  - Pays: US, EU
  - Impact: HIGH, MEDIUM
  - Date: 11/09/2025 (selon screenshot)
- [ ] Cliquer "🔍 Analyser la Période"
- [ ] Chercher événement ECB à 14:15

**Résultats attendus**:
- ✅ **ECB - ecb interest rate decision (EU) | Score: 91/100** (au lieu de 0/100)
- ✅ Badge: 🟢 EXCELLENT (au lieu de ⚪)
- ✅ Stars impact: 🔴🔴🔴 HIGH (au lieu de ⚪⚪⚪)
- ✅ Section "Métriques Backtest Vérifiées" affiche:
  - Impact Vérifié: HIGH
  - Mouvement Moyen: 36.2 pips
  - Taux Réaction: 100%
  - Score Empirique: 91/100

### Test 3: Autres événements
Vérifier que d'autres événements affichent aussi leurs scores:
- [ ] US CPI → devrait afficher ~70-80
- [ ] US NFP → devrait afficher ~86
- [ ] US Fed Interest Rate → devrait afficher ~89

---

## 📁 Fichiers Créés/Modifiés

### Modifié
- ✅ `fx_impact_app/streamlit_app/pages/1_Calendrier-Trading.py`
  - Section enrichissement des événements (lignes ~371-430)
  - Utilisation directe de empirical_score

### Créés
- ✅ `fix_calendar_scores.py` - Script de correction (référence)
- ✅ `test_scores_affichage.py` - Script de test DB
- ✅ `CORRECTION_BUG_SCORES.md` - Ce document

---

## 🔍 Diagnostic Supplémentaire (Si Problème Persiste)

### Si les scores restent à 0 après correction:

#### 1. Vérifier le cache Streamlit
```bash
# Dans terminal Streamlit, appuyer sur 'c' puis 'Enter' pour clear cache
# Ou redémarrer complètement Streamlit (Ctrl+C puis relancer)
```

#### 2. Vérifier precomputed_stats
Ajouter temporairement après ligne ~50:
```python
if 'preloaded' not in st.session_state:
    with st.spinner("⚡ Chargement stats DB..."):
        precomputed_stats = load_precomputed_stats_from_db()
        if precomputed_stats:
            st.session_state.precomputed_stats = precomputed_stats
            
            # DEBUG: Afficher combien de stats chargées
            st.write(f"DEBUG: {len(precomputed_stats)} stats chargées")
            
            # DEBUG: Afficher si ECB est dedans
            ecb_stats = {k: v for k, v in precomputed_stats.items() 
                        if 'ecb' in k[0].lower() or 'interest' in k[0].lower()}
            st.write(f"DEBUG: {len(ecb_stats)} stats ECB trouvées")
```

#### 3. Vérifier le mapping
Ajouter après ligne ~378:
```python
# DEBUG: Afficher les lookups
if 'ecb' in event_key.lower():
    st.write(f"DEBUG: Cherche {event_key} [{country}]")
    st.write(f"DEBUG: Stats trouvées: {stats.get('empirical_score')}")
```

---

## 📊 Résumé de la Session

### Avant
- ❌ Scores calculés et stockés dans DB (91.0 pour ECB)
- ❌ Mais affichés comme 0/100 dans l'interface
- ❌ Mapping EA ↔ EU ne fonctionnait pas dans l'affichage

### Après
- ✅ Scores lus directement depuis DB
- ✅ Mapping EA ↔ EU appliqué dans l'affichage
- ✅ Fallback intelligent sur scoring_engine
- ✅ Grade et tradability cohérents avec empirical_score

### Impact
- 🎯 ECB devrait maintenant afficher: **Score: 91/100** avec badge 🟢 EXCELLENT
- 🎯 Tous les 233 événements avec score (96.7%) devraient s'afficher correctement
- 🎯 Les 8 événements sans score continuent d'afficher 0 (normal, pas de données)

---

## 🎯 Prochaines Étapes

### Immédiat (Maintenant)
1. ✅ Correction appliquée
2. ⏳ Lancer `python3 test_scores_affichage.py`
3. ⏳ Tester dans Streamlit

### Si Test OK
1. Screenshot "après" pour documentation
2. Comparer avec screenshot "avant"
3. Mettre à jour résumé de session

### Si Test KO
1. Activer DEBUG (voir section Diagnostic)
2. Vérifier logs console Streamlit
3. Vérifier que DB contient bien les scores

---

**Status Final**: ✅ CORRECTION APPLIQUÉE - EN ATTENTE DE VALIDATION PAR TESTS

---

*Document créé le 13 octobre 2025*
*Dernière mise à jour: Application de la correction*
