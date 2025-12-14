# 📨 MESSAGE TRANSITION SESSION 101 → SESSION 102

**Date :** 30 octobre 2025  
**De :** Session 101  
**À :** Session 102  
**Priorité :** ⭐⭐⭐ HAUTE

---

## ✅ RÉSUMÉ SESSION 101

**Mission :** Re-calibrer amplification dynamique avec impacts CORRECTS (Session 100)

**SUCCÈS :**
```
Formule validée : amplification = 0.5490 × R²_72h + 1.6988

MAE BASELINE (amp=2.5) : 25.38 pips
MAE DYNAMIQUE          : 22.06 pips
AMÉLIORATION           : 13.1% ✅✅
```

**DÉCISION :** ✅ VALIDER formule dynamique pour Planificateur V2.7

**LIMITATION :** Corrélation R² vs amp = 0.111 (faible) → R² seul insuffisant

---

## 🎯 MISSION SESSION 102

**OBJECTIF PRINCIPAL :** Intégrer formule dynamique dans Planificateur V2.7

### Tâches Critiques

**1. Modifier Planificateur V2.6 → V2.7** ⭐⭐⭐
   - Ajouter fonction `calculate_r_squared_72h()`
   - Modifier `calculate_predictions()` pour utiliser amp dynamique
   - Ajouter indicateur UI "Amplification Dynamique"
   - Backup V2.6 avant modification

**2. Tests Validation** ⭐⭐⭐
   - Test 11.09.2025 : MAE doit rester < 10 pips
   - Test 5 autres dates CPI diverses
   - Comparaison V2.7 vs V2.6 vs V2.5
   - Export CSV résultats

**3. Documentation Utilisateur** ⭐⭐
   - Expliquer amplification dynamique
   - Graphique R² 72h interactif
   - Guide interprétation

---

## 📁 FICHIERS CLÉS À UTILISER

### Scripts Session 101

```
eurusd_clean/scripts/session101/
├── step2_calculate_r2_72h.py         # Fonction R² à intégrer
├── step3_optimize_amplification.py   # Tests validation
└── step3_formula_dynamique.txt       # Formule finale
```

### Planificateur Actuel

```
fx_impact_app/streamlit_app/pages/
└── 5_Planificateur_V2_FORMULES_VALIDEES_backup_session72_fix_importance_20251024 copie 4.py
```

**Version actuelle :** V2.6 (amp=1.0 fixe)  
**Version cible :** V2.7 (amp dynamique)

---

## 🔧 MODIFICATIONS EXACTES NÉCESSAIRES

### Fonction 1 : Calcul R² 72h

```python
def calculate_r_squared_72h(event_timestamp_utc, conn):
    """
    Calcule R² régression linéaire sur prix 72h AVANT événement
    
    Args:
        event_timestamp_utc: Timestamp événement (datetime aware UTC)
        conn: Connexion DuckDB
    
    Returns:
        float: R² (0.0 à 1.0)
    """
    from datetime import timedelta
    import numpy as np
    
    # Fenêtre 72h avant événement
    start_time = event_timestamp_utc - timedelta(hours=72)
    end_time = event_timestamp_utc
    
    # Query prix
    query = """
    SELECT close
    FROM prices_1m
    WHERE datetime >= ?
      AND datetime <= ?
    ORDER BY datetime ASC
    """
    
    prices = conn.execute(query, [start_time, end_time]).fetchdf()
    
    if len(prices) == 0:
        return 0.0
    
    # Régression linéaire
    prices_array = prices['close'].values
    t = np.arange(1, len(prices_array) + 1)
    
    t_mean = np.mean(t)
    y_mean = np.mean(prices_array)
    
    numerator = np.sum((t - t_mean) * (prices_array - y_mean))
    denominator = np.sum((t - t_mean) ** 2)
    slope = numerator / denominator if denominator > 0 else 0
    
    y_pred = slope * t + (y_mean - slope * t_mean)
    
    ss_tot = np.sum((prices_array - y_mean) ** 2)
    ss_res = np.sum((prices_array - y_pred) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    
    return r_squared
```

---

### Fonction 2 : Modifier calculate_predictions()

**LIGNE ~227 actuelle (V2.6) :**
```python
impact = calculate_impact_d(
    empirical_score=adjusted_score,
    num_events=len(cpi_events),
    amplification=1.0  # V2.6 fixe
)
```

**NOUVELLE VERSION (V2.7) :**
```python
# Calculer R² 72h
event_timestamp = pd.to_datetime(cpi_events.iloc[0]['ts_utc'])
conn = get_db_connection()
r_squared_72h = calculate_r_squared_72h(event_timestamp, conn)
conn.close()

# Amplification dynamique (Session 101)
amplification_dynamic = 0.5490 * r_squared_72h + 1.6988

impact = calculate_impact_d(
    empirical_score=adjusted_score,
    num_events=len(cpi_events),
    amplification=amplification_dynamic  # V2.7 dynamique
)

# Stocker pour affichage UI
prediction_result['r_squared_72h'] = r_squared_72h
prediction_result['amplification'] = amplification_dynamic
```

---

### Interface Utilisateur

**Ajouter après affichage impact principal :**
```python
# Après ligne affichage impact
st.markdown("---")
st.markdown("### 📊 Amplification Dynamique")

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "R² Tendance 72h",
        f"{predictions['r_squared_72h']:.3f}",
        help="Coefficient détermination régression linéaire 72h avant événement"
    )

with col2:
    st.metric(
        "Amplification",
        f"{predictions['amplification']:.2f}",
        delta=f"vs 2.5 baseline",
        help="Facteur calibré selon force tendance pré-événement"
    )

# Interprétation
if predictions['r_squared_72h'] > 0.7:
    st.success("🟢 Tendance forte 72h → Amplification élevée")
elif predictions['r_squared_72h'] > 0.3:
    st.info("🟡 Tendance modérée → Amplification standard")
else:
    st.warning("🔴 Pas de tendance claire → Amplification conservatrice")
```

---

## ✅ CHECKLIST SESSION 102

### Avant de Commencer

- [ ] Lire SESSION101_RAPPORT_COMPLET.md
- [ ] Lire ce message (MESSAGE_SESSION101_SESSION102.md)
- [ ] Vérifier Planificateur V2.6 actuel fonctionne

### Développement

- [ ] Créer backup Planificateur V2.6
- [ ] Ajouter fonction calculate_r_squared_72h()
- [ ] Modifier calculate_predictions() (amp dynamique)
- [ ] Ajouter indicateurs UI (R², amp)
- [ ] Tester localement date 11.09.2025

### Validation

- [ ] Test 11.09.2025 : MAE < 10 pips
- [ ] Test 5 autres dates CPI
- [ ] Comparaison V2.7 vs V2.6 vs V2.5
- [ ] Export CSV résultats comparatifs

### Documentation

- [ ] Créer SESSION102_RAPPORT_COMPLET.md
- [ ] Mettre à jour project_state_new.md
- [ ] Screenshots interface V2.7
- [ ] Guide utilisateur amplification dynamique

---

## 📊 TESTS OBLIGATOIRES

### Dates de Test Recommandées

| Date | Impact Réel | R² 72h | Amp Attendue | Notes |
|------|-------------|--------|--------------|-------|
| **2025-09-11** | 57.1 pips | 0.742 | 2.11 | Cas référence ⭐ |
| 2025-08-12 | 62.6 pips | 0.572 | 2.01 | Impact fort |
| 2025-07-15 | 24.7 pips | 0.008 | 1.70 | R² faible |
| 2025-02-12 | 5.0 pips | 0.661 | 2.06 | Impact faible |
| 2024-11-13 | 26.4 pips | 0.770 | 2.12 | R² élevé |
| 2023-11-14 | 117.4 pips | 0.562 | 2.01 | Impact exceptionnel |

### Métriques Succès

**Critères validation V2.7 :**
- MAE global < MAE V2.6 (amp=1.0) ✅
- MAE 11.09.2025 < 10 pips ✅
- Pas de régression vs V2.5 sur dates "normales" ✅
- Interface UI fonctionnelle et claire ✅

---

## ⚠️ POINTS D'ATTENTION

### 1. Timezone Prix 72h

**CRITIQUE :** Utiliser même correction que Session 100

```python
# Event 14:30 Bern → Query 12:30 UTC
event_timestamp_utc = event_timestamp_bern - timedelta(hours=2)
```

### 2. Gestion Connexion DB

**IMPORTANT :** Fermer connexion après calcul R²

```python
conn = get_db_connection()
r_squared_72h = calculate_r_squared_72h(event_timestamp, conn)
conn.close()  # ← NE PAS OUBLIER
```

### 3. Cas R² = 0 ou NULL

**Fallback :** Si erreur calcul R² → amp = 1.7 (intercept)

```python
try:
    r_squared_72h = calculate_r_squared_72h(event_timestamp, conn)
except Exception as e:
    print(f"⚠️ Erreur calcul R² : {e}")
    r_squared_72h = 0.0  # Fallback sûr

# Fallback amp si R² invalide
if r_squared_72h < 0 or r_squared_72h > 1:
    amplification = 1.70  # Intercept seul
else:
    amplification = 0.5490 * r_squared_72h + 1.6988
```

### 4. Performance UI

**R² 72h peut prendre 1-2 secondes**

Ajouter indicateur chargement :
```python
with st.spinner("Calcul amplification dynamique (72h tendance)..."):
    r_squared_72h = calculate_r_squared_72h(event_timestamp, conn)
```

---

## 💡 AMÉLIORATIONS FUTURES (SESSION 103+)

### Modèle Multi-Variables

**Session 103 :** Tester formule étendue

```python
amplification = a × R²_72h 
              + b × surprise_max 
              + c × num_events 
              + d
```

**Variables disponibles immédiatement :**
- R² 72h : ✅ Calculé
- surprise_max : ✅ Dans Planificateur
- num_events : ✅ Dans Planificateur

**Méthodologie :**
1. Régression linéaire multiple (3 variables)
2. Validation croisée Leave-One-Out
3. Comparer avec formule Session 101 (1 variable)

---

### Dataset Élargi

**Session 104 :** Ajouter NFP, FOMC

**Actions :**
1. Mesurer impacts réels NFP (10+ dates)
2. Mesurer impacts réels FOMC (5+ dates)
3. Re-calibrer formule sur dataset mixte
4. Tester généralisation

---

## 📈 MÉTRIQUE AMÉLIORATION CONTINUE

**Objectif long terme :**
```
MAE actuel  : 25.38 pips (baseline amp=2.5)
MAE V2.7    : 22.06 pips (Session 101, -13.1%)
MAE cible   : <15 pips (amélioration 40%+)
```

**Stratégie :**
- Session 102 : Intégration formule actuelle
- Session 103 : Multi-variables (+5-10% amélioration attendue)
- Session 104 : Dataset élargi (validation généralisation)
- Session 105 : Tests production utilisateurs réels

---

## 🎯 RÉSUMÉ SESSION 102

**EN 1 PHRASE :**  
Intégrer amplification dynamique (R² 72h) dans Planificateur V2.7 et valider MAE < MAE V2.6

**FICHIERS À MODIFIER :** 1 (Planificateur)  
**FONCTIONS À AJOUTER :** 1 (calculate_r_squared_72h)  
**LIGNES À MODIFIER :** ~30  
**TESTS À FAIRE :** 6 dates minimum  
**BUDGET ESTIMÉ :** 40-50k tokens

---

**BONNE CHANCE SESSION 102 ! 🚀**

**— Claude, Session 101**  
**30 octobre 2025**
