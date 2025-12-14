# 🚀 DÉMARRAGE RAPIDE - NOUVELLE SESSION

**Pour Claude : Fichier à lire en PREMIER lors de chaque nouvelle session**

---

## 📋 CHECKLIST DÉMARRAGE SESSION

- [ ] Lire `SESSION15_INTRO.md` (prochaine session) ⭐⭐⭐
- [ ] Lire `RAPPORT_SESSION14_FINAL.md` (dernière session complétée) ⭐⭐⭐
- [ ] Lire `KNOWLEDGE_BASE.md` pour connaissances accumulées ⭐⭐
- [ ] Lire `FORMULA_V9_CLEAN.md` si travail sur prédictions ⭐⭐
- [ ] Lire `NOTE_INVESTIGATION_11SEPT.md` si travail sur calibration ⭐⭐

---

## 🎯 CONTEXTE PROJET

**Nom :** Planificateur Multi-Événements EUR/USD  
**Objectif :** Prédire l'impact des événements économiques sur EUR/USD  
**Technologie :** Python, Streamlit, DuckDB  
**Base de données :** `fx_impact_app/data/warehouse.duckdb`

---

## 📊 ÉTAT ACTUEL (Fin Session 14 - 19 octobre 2025)

### ✅ Ce qui fonctionne

| Fonctionnalité | Statut | Précision |
|----------------|--------|-----------|
| Chargement scores DB | ✅ Parfait | 100% |
| Calcul somme vectorielle | ✅ Validé | Tests: 6/6 (100%) |
| Formule v9-CLEAN | ✅ Intégrée | R²=0.264, MAE=6.68 pips |
| Direction événements | ✅ Corrigée | 100% |
| Timeline séquentielle v87 | ✅ Fonctionne | Facteur 0.758 |
| Multiplicateur non-linéaire | ✅ Intégré | v8.7.1 Session 14 |
| Interface Streamlit | ✅ Opérationnelle | Aucune erreur |

### 🔢 Formule ACTIVE : v9-CLEAN avec Somme Vectorielle (Sessions 9-13)

**Architecture complète :**

```python
# 1. Grouper événements par fenêtre temporelle
groups = group_events_by_time_window(events, window_minutes=30)

# 2. Pour chaque groupe, calculer somme vectorielle
for group in groups:
    impact_total = 0.0
    
    for event in group:
        # Calculer impact absolu avec v9-CLEAN
        if len(group) >= 2:
            impact_abs = -10.47 + 0.477 × event.empirical_score
        else:
            impact_abs = -7.08 + 0.419 × event.empirical_score
        
        # Obtenir direction (+1 ou -1)
        direction = get_event_direction(event.family, event.surprise)
        
        # Contribution vectorielle
        impact_total += impact_abs × direction
    
    # 3. Appliquer facteur de correction
    impact_final = abs(impact_total) × 0.758
```

**Fonctions clés :**
- `group_events_by_time_window()` - Groupement temporel
- `calculate_vectorial_sum()` - Somme algébrique
- `get_event_direction()` - Direction EUR/USD
- `sequence_multi_event_timeline()` - Timeline complète

**Métriques :**
- Tests automatiques : 6/6 passent (100%)
- Direction : 100% correcte
- Facteur correction : 0.758
- Module : v8.7.1 PRODUCTION (Session 14)

**✅ Amélioration Session 14 : Multiplicateur non-linéaire**
- Événements extrêmes (surprise > 5%) : Amplification appliquée
- Cas 11 sept : Écart 90% → 48% (+42 points d'amélioration)
- Facteur ×5.14 pour surprise +11.9%
- Tests : 10/10 passent (100%)

### 📊 Tables principales

**Base de données : `warehouse.duckdb` (90M)**

```sql
events                      -- 32,024 événements avec surprises
event_families              -- 241 types avec métadonnées  
event_group_impacts         -- 2,089 groupes temporels
prices_1m                   -- 1.1M lignes de prix minute
```

**⚠️ Attention structure :**
- Table `events` utilise `event_title` (pas `event_name`)
- Table `events` utilise `estimate` (pas `forecast`)
- Les petits `.db` (12K) sont VIDES, utiliser `warehouse.duckdb`

### ⚠️ Formules/Modules OBSOLÈTES

| Version | Statut | Raison |
|---------|--------|--------|
| Formula v6 | ❌ OBSOLÈTE | Calcul individuel incorrect |
| Timeline v86 | ⚠️ REMPLACÉE | Pas de somme vectorielle |
| Timeline v87 | ✅ PRODUCTION | Avec somme vectorielle |

### 🚀 Prochaines étapes (Session 14)

**Objectif :** Améliorer calibration pour événements extrêmes

1. **Analyser** 10-15 dates avec surprises > 5%
2. **Implémenter** multiplicateur non-linéaire pour surprises extrêmes
3. **Tester** facteur d'amplification
4. **Valider** sur dataset historique
5. **Ajuster** facteur de correction si nécessaire

**Durée estimée :** 2-3 heures

**Document de référence :** `NOTE_INVESTIGATION_11SEPT.md`

---

## 📁 FICHIERS IMPORTANTS

### Documentation (À LIRE)

```
RAPPORT_SESSION13_FINAL.md          ⭐⭐⭐ Résumé Session 13 (bug fix)
NOTE_INVESTIGATION_11SEPT.md        ⭐⭐⭐ Investigation amplitude (×10)
FORMULA_V9_CLEAN.md                 ⭐⭐⭐ Formule v9-CLEAN officielle
KNOWLEDGE_BASE.md                   ⭐⭐  Base de connaissances
RAPPORT_SESSION12_IMPLEMENTATION.md ⭐⭐  Implémentation v87
KNOWLEDGE_BASE_UPDATE_SESSION11.md  ⭐⭐  Mise à jour Session 11
SESSION13_INTRO.md                  ⭐   Guide Session 13
```

### Scripts principaux

```
sequence_multi_event_timeline_v87.py         ⭐⭐⭐ Timeline avec somme vectorielle
4_Planificateur-Multi-Evenements.py          ⭐⭐⭐ Application Streamlit
test_v87_complet.py                          ⭐⭐⭐ Tests automatiques (6/6)
test_groupement_v87.py                       ⭐⭐⭐ Tests groupement (6/6)
forecaster_mvp.py                            ⭐⭐  Moteur prédiction
```

### Scripts obsolètes (ne plus utiliser)

```
sequence_multi_event_timeline_v86.py    ❌ Pas de somme vectorielle
calculate_real_impacts.py               ❌ Calcul INCORRECT
```

---

## 🔑 INFORMATIONS CRITIQUES

### Bug corrigé en Session 13

**FAMILY_SENTIMENT pour CPI et Inflation :**

```python
# AVANT (INCORRECT - Session 12)
FAMILY_SENTIMENT = {
    'CPI': -1,        # ❌ FAUX
    'Inflation': -1,  # ❌ FAUX
}

# APRÈS (CORRECT - Session 13)
FAMILY_SENTIMENT = {
    'CPI': 1,         # ✅ CORRECT
    'Inflation': 1,   # ✅ CORRECT
}
```

**Rationale :**
- Inflation **haute** = **bad** pour EUR = EUR/USD **DOWN**
- Inflation **basse** = **good** pour EUR = EUR/USD **UP**
- Avec sentiment = +1, la logique directionnelle est correcte

**Impact :** Sans cette correction, les directions CPI/Inflation étaient inversées.

### Anomalie détectée : 11 septembre 2025

**Observation :**
- Système prédit : 52.4 pips UP ⬆️
- Mouvement réel MT5 : ~521 pips UP ⬆️
- **Écart : ×10**

**Cause probable :**
- Surprise Initial Jobless Claims : +28K (+11.9%) 🚨
- Événement "cygne noir" (> 5 sigma)
- Effets non-linéaires non modélisés (panique, cascade)

**Documentation complète :** `NOTE_INVESTIGATION_11SEPT.md`

**Action requise :** Implémenter multiplicateur pour surprises > 5% (Session 14)

### Architecture module v87

```
┌─────────────────────────────────────────────┐
│ sequence_multi_event_timeline_v87.py        │
├─────────────────────────────────────────────┤
│                                             │
│ 1. group_events_by_time_window()           │
│    └─ Groupe événements < 30 min           │
│                                             │
│ 2. calculate_vectorial_sum()               │
│    ├─ Impact = f(score, num_events)        │
│    ├─ Direction = f(family, surprise)      │
│    ├─ Somme algébrique                     │
│    └─ Facteur correction 0.758             │
│                                             │
│ 3. sequence_multi_event_timeline()         │
│    ├─ Timeline séquentielle                │
│    ├─ Pullback entre phases                │
│    └─ Prix cumulatifs                      │
│                                             │
│ 4. get_event_direction()                   │
│    └─ Retourne +1 (UP) ou -1 (DOWN)        │
│                                             │
└─────────────────────────────────────────────┘
```

### Tests automatiques

**Fichiers de test :**
```
test_v87_complet.py     - 6 tests complets (6/6 ✅)
test_groupement_v87.py  - 6 tests groupement (6/6 ✅)
```

**Commande :**
```bash
python3 test_v87_complet.py
```

**Résultats attendus :**
```
✅ PASSÉ : TEST 1 : Import module v87
✅ PASSÉ : TEST 2 : Groupement événements
✅ PASSÉ : TEST 3 : Somme vectorielle
✅ PASSÉ : TEST 4 : Génération timeline
✅ PASSÉ : TEST 5 : Comparaison résultat réel
✅ PASSÉ : TEST 6 : Statistiques TTR

🎉 TOUS LES TESTS PASSENT ! (6/6 - 100%)
```

---

## 💬 PHRASE D'ACCUEIL SESSION 14

```
Bonjour Claude !

Je démarre Session 14 du Planificateur Multi-Événements.

⚠️ IMPORTANT : Lis ces fichiers dans l'ordre :
1. RAPPORT_SESSION13_FINAL.md (contexte) - 10 min ⭐⭐⭐
2. NOTE_INVESTIGATION_11SEPT.md (anomalie ×10) - 5 min ⭐⭐⭐
3. KNOWLEDGE_BASE.md (section Session 13) - 5 min ⭐⭐

📊 Contexte :
✅ Session 13 : Bug direction corrigé + Tests 100% + Streamlit OK
⚠️  Limitation : Sous-estimation ×10 pour événements extrêmes

🎯 Session 14 : Améliorer calibration pour cas extrêmes

Objectif immédiat :
Analyser événements avec surprises > 5% et implémenter multiplicateur

Prêt pour l'investigation ! 🔍
```

---

## 📊 MÉTRIQUES CLÉS

### Tests Session 13

| Test | Résultat | Statut |
|------|----------|--------|
| Import module v87 | ✅ PASSÉ | - |
| Groupement événements | ✅ PASSÉ | - |
| Somme vectorielle | ✅ PASSÉ | - |
| Génération timeline | ✅ PASSÉ | - |
| Comparaison résultat réel | ✅ PASSÉ | 0.1% erreur |
| Statistiques TTR | ✅ PASSÉ | - |
| **TOTAL** | **6/6 (100%)** | ✅ |

### Historique précision

| Version | Méthode | 11 sept prédit | MT5 réel | Écart | Direction |
|---------|---------|----------------|----------|-------|-----------|
| v5 | Moyenne | 214.6 pips | 111.5 pips | -92% | - |
| v6 | Individuel | 59.2 pips | 111.5 pips | -47% | - |
| v9-CLEAN | Groupé | 119.5 pips | 111.5 pips | +7% | - |
| v87 (cas test) | Vectoriel | 43.4 pips | 43.4 pips | 0% | ✅ UP |
| v87 (données réelles) | Vectoriel | 52.4 pips | ~521 pips | **-90%** | ✅ UP |

**Note :** L'écart -90% sur données réelles s'explique par un événement extrême (surprise +11.9%, événement "cygne noir").

### Évolution architecture

| Version | Caractéristique | Statut |
|---------|-----------------|--------|
| v86 | Timeline séquentielle | ⚠️ Obsolète |
| v87 | + Somme vectorielle | ✅ Production |
| v87 | + Direction corrigée | ✅ Session 13 |
| v88 (futur) | + Multiplicateur non-linéaire | 📋 Session 14 |

---

## 🔄 MAINTENANCE

**Ce fichier doit être mis à jour :**
- ✅ À chaque fin de session
- ✅ Quand une amélioration majeure est appliquée
- ✅ Quand un nouveau problème est identifié

**Historique :**
- Session 7 : Création initiale
- Session 8 : Correction calcul groupé
- Session 9 : Génération v9-CLEAN
- Session 10 : Validation + documentation
- Session 11 : Somme vectorielle implémentée
- Session 12 : Module v87 créé
- **Session 13 :** Bug direction corrigé + Tests 100% + Anomalie détectée
- **En attente Session 14 :** Multiplicateur non-linéaire

---

## 📚 RÉFÉRENCES RAPIDES

### Découverte critique Session 13

**Bug :** Direction CPI/Inflation inversée dans `FAMILY_SENTIMENT`  
**Conséquence :** Prédictions incorrectes pour inflation  
**Solution :** Changer sentiment de -1 à +1 pour CPI et Inflation  
**Détails :** `RAPPORT_SESSION13_FINAL.md` - Section "PHASE 1"

### Anomalie amplitude Session 13

**Observation :** Sous-estimation ×10 sur événement extrême  
**Événement :** 11 septembre 2025, Initial Jobless Claims +11.9%  
**Hypothèse :** Effets non-linéaires (panique, cascade)  
**Détails :** `NOTE_INVESTIGATION_11SEPT.md`

### Formule v9-CLEAN avec somme vectorielle

```python
# Grouper événements
groups = group_events_by_time_window(events, 30)

# Pour chaque groupe
for group in groups:
    # Somme vectorielle
    impact_total = sum(
        predict_v9(event.score, len(group)) × direction(event)
        for event in group
    )
    
    # Facteur correction
    impact_final = abs(impact_total) × 0.758
```

**Documentation complète :** `sequence_multi_event_timeline_v87.py`

---

## 🎯 SESSION 14 - MULTIPLICATEUR NON-LINÉAIRE

### Objectif
Améliorer la précision pour événements extrêmes (surprises > 5%) en ajoutant un facteur d'amplification.

### Proposition

```python
def calculate_amplification_factor(surprise_pct):
    """
    Facteur multiplicateur pour surprises extrêmes
    
    - Surprise < 5%  : facteur = 1.0 (linéaire)
    - Surprise 5-10% : facteur = 1.5-3.0
    - Surprise > 10% : facteur = 3.0-10.0
    """
    surprise_abs = abs(surprise_pct)
    
    if surprise_abs < 5.0:
        return 1.0
    elif surprise_abs < 10.0:
        return 1.0 + (surprise_abs - 5.0) * 0.4
    else:
        return 3.0 + np.log1p(surprise_abs - 10.0) * 2.0
```

### Plan d'action

1. **Analyser événements extrêmes historiques** (30 min)
   - Requête SQL pour trouver surprises > 5%
   - Mesurer mouvement MT5 réel
   - Calculer ratio réel/prédit

2. **Implémenter multiplicateur** (1h)
   - Ajouter fonction dans v87
   - Tester sur 11 septembre 2025
   - Ajuster paramètres

3. **Valider sur échantillon** (1h)
   - Tester sur 15-20 dates
   - Comparer MAE avant/après
   - Optimiser coefficients

4. **Documentation** (30 min)
   - RAPPORT_SESSION14_FINAL.md
   - Mise à jour START_HERE.md

**Durée estimée :** 3 heures

---

**FIN DU GUIDE DE DÉMARRAGE**

**Pour toute question, consulter d'abord :**
1. `RAPPORT_SESSION13_FINAL.md` (dernière session)
2. `NOTE_INVESTIGATION_11SEPT.md` (anomalie amplitude)
3. `KNOWLEDGE_BASE.md` (base de connaissances complète)

📚 **Version :** 4.0 (Session 13)  
📅 **Dernière mise à jour :** 20 octobre 2025, 01:50  
✅ **Statut :** Système opérationnel - Calibration requise pour cas extrêmes
