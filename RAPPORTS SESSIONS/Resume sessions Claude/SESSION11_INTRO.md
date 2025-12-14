# 🚀 SESSION 11 - GUIDE DE DÉMARRAGE RAPIDE

**Objectif :** Intégrer la formule v9-CLEAN dans le planificateur Streamlit

---

## ⚡ DÉMARRAGE ULTRA-RAPIDE

### 📋 Checklist pré-session

- [ ] Lire SESSION10_RECAP.md (section "Plan d'intégration")
- [ ] Lire FORMULA_V9_CLEAN.md (formule et exemples)
- [ ] Ouvrir forecaster_mvp.py dans l'éditeur
- [ ] Terminal prêt pour tests

---

## 🎯 PLAN D'ACTION SESSION 11

### Phase 1️⃣ : Créer fonction v9 (30 min)

**Fichier :** `fx_impact_app/src/forecaster_mvp.py`

**Code à ajouter :**

```python
def predict_impact_v9_clean(empirical_score: float, num_events: int = 1) -> float:
    """
    Prédit l'impact en pips avec formule v9-CLEAN (Session 9)
    
    Args:
        empirical_score: Score empirique 0-100
        num_events: Nombre d'événements simultanés
    
    Returns:
        Impact prédit en pips (None si score NULL)
    
    Formule:
        - 1 événement: -7.08 + 0.419 × score
        - ≥2 événements: -10.47 + 0.477 × score
    
    Métriques (Session 9):
        - R² = 0.264
        - MAE = 6.68 pips
        - Dataset: 2,087 groupes (2024-2025)
    """
    if empirical_score is None:
        return None
    
    if num_events >= 2:
        return -10.47 + 0.477 * empirical_score
    else:
        return -7.08 + 0.419 * empirical_score
```

**Test rapide :**

```python
# Dans terminal Python
from forecaster_mvp import predict_impact_v9_clean

# Test 11 septembre (6 événements, score 81.7)
print(predict_impact_v9_clean(81.7, 6))  # Devrait donner ~28.6 pips

# Test événement seul (score 50)
print(predict_impact_v9_clean(50, 1))  # Devrait donner ~13.9 pips
```

---

### Phase 2️⃣ : Intégrer dans Planificateur (1h)

**Fichier :** `fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py`

**Localiser :** Fonction qui appelle `ForecastEngine.calculate_family_stats()`

**Modifier pour :**
1. Lire `empirical_score` depuis table `events`
2. Appeler `predict_impact_v9_clean()`
3. Utiliser résultat au lieu de `mfe_p80`

**Stratégie hybride (recommandée) :**

```python
# Si empirical_score disponible
if event['empirical_score'] is not None:
    predicted_impact = predict_impact_v9_clean(
        event['empirical_score'], 
        num_events
    )
    source = "v9-CLEAN"
else:
    # Fallback sur méthode historique
    predicted_impact = stats['mfe_p80']
    source = "historique"

# Afficher avec indication de source
st.metric(
    "Impact prédit", 
    f"{predicted_impact:.1f} pips",
    help=f"Prédiction {source}"
)
```

---

### Phase 3️⃣ : Tests (30 min)

#### Test 1 : 11 septembre 2025

```python
# Comparer prédiction vs réalité
date = '2025-09-11'
time = '14:30'
empirical_score = 81.7
num_events = 6

predicted = predict_impact_v9_clean(empirical_score, num_events)
actual_mt5 = 44.2  # Mesuré

print(f"Prédit: {predicted:.1f} pips")
print(f"Réel: {actual_mt5:.1f} pips")
print(f"Erreur: {abs(predicted - actual_mt5):.1f} pips")
```

**Résultat attendu :** ~28.6 pips prédit vs 44.2 pips réel = 15.6 pips d'erreur (acceptable)

#### Test 2 : Interface Streamlit

1. Lancer Streamlit : `streamlit run fx_impact_app/streamlit_app/Home.py`
2. Aller sur "Planificateur Multi-Événements"
3. Sélectionner 11 septembre 2025, 14:30
4. Vérifier affichage "Prédit (v9-CLEAN)"

---

### Phase 4️⃣ : Documentation (30 min)

1. **Créer RAPPORT_SESSION11_FINAL.md**
   - Ce qui a été fait
   - Tests effectués
   - Résultats obtenus

2. **Mettre à jour START_HERE.md**
   - Section "Formule active"
   - Comment utiliser v9-CLEAN

3. **Créer SESSION11_RECAP.md**
   - Résumé session
   - Prochaines étapes

---

## 🔧 FICHIERS À MODIFIER

### Priorité 1 (obligatoire)
- `fx_impact_app/src/forecaster_mvp.py` → Ajouter fonction v9
- `fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py` → Intégrer v9

### Priorité 2 (recommandé)
- `fx_impact_app/src/sequence_multi_event_timeline_v86.py` → Utiliser v9 pour phases

### Priorité 3 (optionnel)
- Autres pages Streamlit utilisant prédictions

---

## 📊 REQUÊTES SQL UTILES

### Lire empirical_score d'un événement

```sql
SELECT 
    ts_utc,
    event_key,
    country,
    empirical_score,
    actual,
    estimate
FROM events
WHERE DATE(ts_utc) = '2025-09-11'
  AND strftime(ts_utc, '%H:%M') = '14:30'
  AND empirical_score IS NOT NULL
ORDER BY ts_utc
```

### Compter événements avec score

```sql
SELECT 
    COUNT(*) as total,
    COUNT(empirical_score) as with_score,
    COUNT(empirical_score) * 100.0 / COUNT(*) as pct_with_score
FROM events
WHERE country IN ('US', 'EU', 'GB')
```

---

## ⚠️ PIÈGES À ÉVITER

### 1. Ne pas oublier le cas NULL
```python
# ❌ FAUX
impact = -7.08 + 0.419 * score  # Crash si score = None

# ✅ CORRECT
if score is not None:
    impact = -7.08 + 0.419 * score
else:
    impact = None
```

### 2. Distinguer événement seul vs groupé
```python
# ❌ FAUX
impact = -7.08 + 0.419 * score  # Toujours la même formule

# ✅ CORRECT
if num_events >= 2:
    impact = -10.47 + 0.477 * score
else:
    impact = -7.08 + 0.419 * score
```

### 3. Documenter la source de prédiction
```python
# ❌ FAUX
st.metric("Impact prédit", f"{impact:.1f} pips")

# ✅ CORRECT
st.metric(
    "Impact prédit", 
    f"{impact:.1f} pips",
    help="Prédiction v9-CLEAN (Session 9)"
)
```

---

## 🎯 CRITÈRES DE SUCCÈS SESSION 11

### Code ✅
- [ ] Fonction `predict_impact_v9_clean()` créée
- [ ] Tests unitaires passent
- [ ] Intégration dans Planificateur fonctionne

### Tests ✅
- [ ] 11 septembre validé
- [ ] Échantillon aléatoire testé
- [ ] Interface Streamlit OK

### Documentation ✅
- [ ] RAPPORT_SESSION11_FINAL.md créé
- [ ] START_HERE.md mis à jour
- [ ] SESSION11_RECAP.md créé

**Si tous cochés → Session 11 RÉUSSIE ! 🎉**

---

## 📚 RÉFÉRENCES RAPIDES

### Formule v9-CLEAN
```python
# 1 événement
impact = -7.08 + 0.419 × score

# ≥2 événements
impact = -10.47 + 0.477 × score
```

### Métriques
- **R² = 0.264**
- **MAE = 6.68 pips**
- **Dataset = 2,087 groupes**

### 11 septembre (groupe 14:30)
- **Score :** 81.7
- **Prédit v9 :** 28.6 pips
- **Réel MT5 :** 44.2 pips
- **Erreur :** 15.6 pips

---

## 💡 MESSAGE DE DÉMARRAGE SESSION 11

```markdown
Bonjour Claude !

Je démarre la Session 11 du Planificateur Multi-Événements.

⚠️ IMPORTANT : Lis ces fichiers dans l'ordre :
1. SESSION11_INTRO.md (ce fichier) - 5 min ⭐⭐⭐
2. SESSION10_RECAP.md (section Plan d'intégration) - 5 min ⭐⭐
3. FORMULA_V9_CLEAN.md (formule) - 2 min ⭐

📊 Contexte :
✅ Session 10 : Documentation complète + architecture analysée
🎯 Session 11 : Intégrer v9-CLEAN dans le planificateur

Objectif immédiat :
Créer fonction predict_impact_v9_clean() dans forecaster_mvp.py

Prêt ! 🚀
```

---

**FIN SESSION11_INTRO.md**

**Version :** 1.0  
**Date :** 18 octobre 2025  
**Statut :** ✅ Prêt pour Session 11
