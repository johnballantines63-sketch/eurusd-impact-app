# NOTES LECTURE PLANIFICATEUR V2.4
## Session 97 - Analyse Ligne par Ligne

---

## 📌 INFORMATIONS GÉNÉRALES

**Fichier :** `5_Planificateur_V2_FORMULES_VALIDEES_backup_session72_fix_importance_20251024 copie 4.py`  
**Version :** 2.4 - Session 68  
**Lignes totales :** 550

**Architecture :**
- Import formules validées Sessions 51-55
- Détection automatique type mouvement (Session 68)
- Charge événements HIGH IMPACT (score > 40)
- Calcul global (somme vectorielle)

---

## 🔍 IMPORTS CRITIQUES (Lignes 26-50)

```python
from formulas_validated import (
    calculate_impact_d,          # Session 51 - 98.6% précision
    calculate_ttr_c,              # Session 52 - 94.4% précision
    calculate_pullback_v2,        # Session 53 - 99.3% précision
    calculate_adjusted_empirical_score,  # Session 55 - 99.9% précision
    get_all_formulas_info
)

from double_wave import (
    detect_double_wave_conditions,
    predict_double_wave_timeline
)

from single_wave_strong import (
    detect_single_wave_strong,
    predict_single_wave_timeline
)
```

**⭐ DÉCOUVERTE IMPORTANTE :**
- Le planificateur IMPORTE les formules validées
- Il ne les recalcule PAS lui-même
- Source de vérité = `formulas_validated.py`

---

## 📊 FONCTION 1 : get_high_impact_events_for_date() (Lignes 145-171)

### Query SQL (Lignes 155-167)

```sql
SELECT 
    e.event_key,
    e.event_title as label,
    e.ts_utc,
    e.actual,
    e.estimate,
    ef.family,
    ef.empirical_score,
    ef.latency_median
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE DATE(e.ts_utc) = ?
    AND e.country = 'US'
    AND ef.empirical_score IS NOT NULL
    AND ef.empirical_score > 40
ORDER BY e.ts_utc
```

**⚠️ OBSERVATIONS CRITIQUES :**

1. **Filtres appliqués :**
   - ✅ `DATE(e.ts_utc) = ?` → Date exacte
   - ✅ `e.country = 'US'` → USA uniquement
   - ✅ `ef.empirical_score IS NOT NULL` → Score existant
   - ✅ `ef.empirical_score > 40` → HIGH IMPACT
   - ✅ `ORDER BY e.ts_utc` → Chronologique

2. **Colonnes chargées :**
   - `event_key` → Identifiant unique
   - `event_title` → Nom événement (alias `label`)
   - `ts_utc` → Timestamp (UTC+2 Bern time)
   - `actual` → Valeur publiée
   - `estimate` → Consensus forecast
   - `family` → Famille événement
   - `empirical_score` → Score de base
   - `latency_median` → Latence médiane

3. **⚠️ POINT IMPORTANT :**
   - Query charge **TOUS événements HIGH** (pas uniquement CPI)
   - Session 71 mentionne correction : `event_title` au lieu de `label`
   - Session 68 stipule : Traiter CPI, NFP, Retail Sales, etc.

4. **❌ PAS DE :**
   - `forecast` (utilise `estimate`)
   - `previous`
   - Calcul surprise dans query

---

## 📊 FONCTION 2 : calculate_predictions() (Lignes 174-321)

**Architecture générale :**
```
1. Calcul score moyen + surprise max (lignes 191-203)
2. Ajustement score (Session 55) (lignes 206-207)
3. Calcul impact (Formule D) (lignes 210-216)
4. Calcul TTR (Formule C) (lignes 219-228)
5. Calcul pullback (Formule V2) (ligne 231)
6. Détection type mouvement (lignes 239-278)
7. Retour résultats (lignes 280-291)
```

### PHASE 1 : Calcul Surprise (Lignes 191-203)

```python
base_score_avg = cpi_events['empirical_score'].mean()

surprises = []
max_surprise = 0
for _, event in cpi_events.iterrows():
    if pd.notna(event['actual']) and pd.notna(event['estimate']) and event['estimate'] != 0:
        surprise_pct = abs((event['actual'] - event['estimate']) / event['estimate']) * 100
        surprises.append(surprise_pct)
        if surprise_pct > max_surprise:
            max_surprise = surprise_pct

avg_surprise = sum(surprises) / len(surprises) if surprises else 0
```

**⚠️ OBSERVATIONS :**

1. **Méthode surprise :**
   - Utilise UNIQUEMENT `estimate` (pas de fallback `forecast` ou `previous`)
   - Formule : `|actual - estimate| / |estimate| × 100`
   - Vérifie : `actual` et `estimate` NOT NULL
   - Vérifie : `estimate ≠ 0` (évite division par zéro)

2. **Variables calculées :**
   - `base_score_avg` → Moyenne scores bruts
   - `max_surprise` → Surprise maximale parmi tous événements
   - `avg_surprise` → Surprise moyenne

3. **⚠️ DIFFÉRENCE vs Message Session 96 :**
   - Message mentionne "fallback estimate → forecast → previous"
   - **Code réel utilise SEULEMENT estimate**
   - **PAS de fallback implémenté ici**

---

### PHASE 2 : Ajustement Score (Lignes 206-207)

```python
adjusted_score = calculate_adjusted_empirical_score(base_score_avg, max_surprise)
```

**⭐ DÉLÉGATION :**
- Appelle fonction externe `calculate_adjusted_empirical_score()`
- Module : `formulas_validated.py`
- Paramètres : `(base_score_avg, max_surprise)`
- **Je dois lire ce module pour voir la formule exacte**

---

### PHASE 3 : Calcul Impact (Lignes 210-216)

```python
impact = calculate_impact_d(
    empirical_score=adjusted_score,
    num_events=len(cpi_events),
    amplification=2.5
)
```

**⭐ DÉLÉGATION :**
- Appelle fonction externe `calculate_impact_d()`
- Module : `formulas_validated.py`
- Paramètres :
  - `empirical_score` → Score AJUSTÉ (pas brut)
  - `num_events` → Nombre d'événements
  - `amplification` → **FIXE à 2.5** (valeur optimale)

**🚨 DÉCOUVERTE CRITIQUE :**
- **Amplification = 2.5 codée en dur**
- Pas de calcul dynamique selon surprise
- **Je dois vérifier si `calculate_impact_d()` applique amplification EN PLUS**

---

### PHASE 4 : Calcul TTR (Lignes 219-228)

```python
cpi_main = cpi_events.iloc[0]
if pd.notna(cpi_main['actual']) and pd.notna(cpi_main['estimate']) and cpi_main['estimate'] != 0:
    surprise_pct = abs((cpi_main['actual'] - cpi_main['estimate']) / cpi_main['estimate']) * 100
else:
    surprise_pct = 0

latency_min = cpi_main['latency_median'] / 60 if pd.notna(cpi_main['latency_median']) else 2.0
ttr_predicted = calculate_ttr_c(latency_min, surprise_pct)
```

**⚠️ OBSERVATIONS :**

1. **Événement utilisé :**
   - Prend le PREMIER événement (`iloc[0]`)
   - Suppose que c'est le plus important
   - Recalcule surprise pour CET événement

2. **Latence :**
   - `latency_median` en secondes → Conversion `/60` en minutes
   - Fallback : 2.0 minutes si NULL

3. **⭐ DÉLÉGATION :**
   - Appelle `calculate_ttr_c(latency_min, surprise_pct)`
   - Module : `formulas_validated.py`

---

### PHASE 5 : Calcul Pullback (Ligne 231)

```python
pullback = calculate_pullback_v2(37.4, 10, 15)
```

**🚨 PROBLÈME IDENTIFIÉ :**
- Valeurs **CODÉES EN DUR** : `37.4, 10, 15`
- Ne dépend PAS de l'impact calculé
- Semble être référence 11 septembre fixe
- **Non dynamique selon impact réel**

**⚠️ HYPOTHÈSE :**
- Peut-être juste pour display ?
- Ou erreur de code ?
- **Je dois vérifier signature `calculate_pullback_v2()`**

---

### PHASE 6 : Détection Type Mouvement (Lignes 239-278)

#### Préparation événements (Lignes 242-253)

```python
events_for_detection = []
for _, event in cpi_events.iterrows():
    events_for_detection.append({
        'actual': event.get('actual'),
        'estimate': event.get('estimate'),
        'forecast': event.get('estimate'),  # ⚠️ Duplique estimate
        'previous': event.get('estimate'),  # ⚠️ Duplique estimate
        'importance_n': 3  # HIGH importance codée en dur
    })

start_time = pd.to_datetime(cpi_events.iloc[0]['ts_utc'])
```

**⚠️ OBSERVATIONS :**
- `forecast` et `previous` → Dupliquent `estimate` (hack ?)
- `importance_n = 3` → HIGH codé en dur
- `start_time` → Timestamp premier événement

#### Test Single Wave Strong (Lignes 256-260)

```python
is_single_wave_strong = detect_single_wave_strong(
    events_for_detection,
    surprise_threshold=15.0,
    min_cluster_size=3
)
```

**Conditions :**
- `surprise_threshold = 15.0%`
- `min_cluster_size = 3` événements

#### Test Double Wave (Lignes 263-267)

```python
is_double_wave = detect_double_wave_conditions(
    events_for_detection,
    surprise_threshold=20.0,
    min_cluster_size=5
)
```

**Conditions :**
- `surprise_threshold = 20.0%` (plus strict)
- `min_cluster_size = 5` événements (plus strict)

#### Logique Décision (Lignes 270-291)

```python
if is_double_wave:
    movement_type = "Double Wave Momentum"
    double_wave_timeline = predict_double_wave_timeline(...)
elif is_single_wave_strong:
    movement_type = "Single Wave Fort"
    single_wave_timeline = predict_single_wave_timeline(...)
else:
    movement_type = "Single Wave Standard"
```

**⭐ PRIORITÉ :**
1. Double Wave (conditions les plus strictes)
2. Single Wave Fort (conditions moyennes)
3. Single Wave Standard (défaut)

---

## 🎯 RÉSUMÉ PHASE 1 LECTURE

### ✅ CE QUI EST CLAIR

1. **Query événements :**
   - Filtre : `score > 40`, `country = 'US'`, `NOT NULL`
   - Colonnes : `event_key`, `ts_utc`, `actual`, `estimate`, `empirical_score`, `latency_median`

2. **Calcul surprise :**
   - Formule : `|actual - estimate| / |estimate| × 100`
   - Utilise SEULEMENT `estimate` (pas de fallback)
   - Calcule `max_surprise` et `avg_surprise`

3. **Délégation formules :**
   - `calculate_adjusted_empirical_score()` → ajustement score
   - `calculate_impact_d()` → impact (avec amplification 2.5 fixe)
   - `calculate_ttr_c()` → TTR
   - `calculate_pullback_v2()` → pullback

4. **Détection mouvement :**
   - Priorité : Double Wave → Single Wave Fort → Standard
   - Seuils surprise : 20%, 15%
   - Taille cluster : 5, 3

### ❓ QUESTIONS À RÉSOUDRE

1. **Fallback surprise :**
   - Message S96 mentionne "estimate → forecast → previous"
   - Code réel utilise SEULEMENT `estimate`
   - **Où est le fallback ?**

2. **Amplification 2.5 :**
   - Codée en dur dans appel `calculate_impact_d()`
   - Est-ce que `calculate_impact_d()` applique d'autres amplifications ?
   - Ou 2.5 est la valeur FINALE ?

3. **Pullback codé en dur :**
   - `pullback = calculate_pullback_v2(37.4, 10, 15)`
   - Pas dynamique
   - Juste pour display ou erreur ?

4. **Query TOUS événements HIGH :**
   - Charge CPI, NFP, Retail Sales, etc.
   - Commentaires disent "uniquement CPI"
   - **Quelle est la vérité ?**

### 📋 PROCHAINES LECTURES OBLIGATOIRES

**PRIORITÉ 1 :**
```
fx_impact_app/src/formulas_validated.py
```
→ Voir formules EXACTES :
- `calculate_adjusted_empirical_score()`
- `calculate_impact_d()`
- `calculate_ttr_c()`
- `calculate_pullback_v2()`

**PRIORITÉ 2 :**
```
eurusd_clean/docs/SESSION51_RAPPORT_COMPLET.md  (Impact D)
eurusd_clean/docs/SESSION52_RAPPORT_COMPLET.md  (TTR C)
eurusd_clean/docs/SESSION53_RAPPORT_COMPLET.md  (Pullback V2)
eurusd_clean/docs/SESSION55_RAPPORT_COMPLET.md  (Ajustement Score)
```

---

**Token usage actuel : ~50k / 190k (26%)**
**Marge avant limite 105k : 55k tokens**

**Prochaine étape : Lecture `formulas_validated.py`**
