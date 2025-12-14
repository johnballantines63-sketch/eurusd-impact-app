# 🚀 SESSION 8 - CORRECTION CALCUL IMPACTS GROUPÉS

**Date de création :** 17 octobre 2025  
**Session précédente :** Session 7 (voir RAPPORT_SESSION7_FINAL.md)

---

## ⚠️ AVANT DE COMMENCER - LECTURE OBLIGATOIRE

**Lis dans CET ORDRE :**

1. **`ADDENDUM_CRITIQUE_SESSION7.md`** ⭐⭐⭐ CRITIQUE
   - Explique l'erreur découverte en fin de Session 7
   - Invalide certaines conclusions de Session 7
   - **5 minutes de lecture qui éviteront des heures d'erreur**

2. **`START_HERE.md`** ⭐⭐
   - État général du projet
   - Fichiers importants

3. **`KNOWLEDGE_BASE.md`** ⭐⭐
   - Erreurs à éviter
   - Formules testées (⚠️ v7/v8 à recalculer)

4. **`RAPPORT_SESSION7_FINAL.md`** ⭐ (si besoin de contexte)
   - Détails complets Session 7

---

## 📋 RÉSUMÉ RAPIDE SESSION 7

### ✅ Ce qui a été réussi

| Réalisation | Statut | Impact |
|-------------|--------|--------|
| **Système documentation** | ✅ Complet | Gain 85% temps mise en contexte |
| **Structure DB documentée** | ✅ Parfait | Plus d'erreurs DB |
| **Scripts analyse créés** | ✅ Fonctionnels | Réutilisables |
| **Découverte estimate** | ✅ Fait | Peu utile finalement |

### ⚠️ Ce qui doit être corrigé

**Problème identifié en fin de Session 7 :**

Le script `calculate_real_impacts.py` calcule les impacts **par événement individuel** alors qu'il faudrait calculer **par groupe temporel**.

**Exemple problématique :**
- 11 septembre 14:30 : 33 événements simultanés
- Script actuel : 33 lignes avec MFE = 59.2 pips (même valeur !)
- Correct : 1 ligne avec impact combiné du groupe

**Conséquence :** Les formules v7/v8 et métriques sont basées sur des calculs incorrects.

---

## 🎯 OBJECTIFS SESSION 8

### Priorité HAUTE (obligatoire)

1. **Mesure manuelle MT5** (30 min)
   - Mesurer impact Phase 1 (14:30) en pips sur graphique
   - Mesurer impact Phase 2 (14:45) en pips
   - Documenter : Impact total = Phase 1 + Phase 2

2. **Comprendre code existant** (1h)
   - Lire `sequence_multi_event_timeline_v86.py`
   - Comprendre calcul impacts combinés
   - Identifier la logique vectorielle existante

3. **Créer script corrigé** (2h)
   - `calculate_grouped_impacts.py`
   - Grouper événements par time_group (minute)
   - Calculer UN impact par groupe
   - Gérer phases successives

### Priorité MOYENNE (si temps)

4. **Ré-analyser avec bons impacts** (1h)
   - Relancer `analyze_and_generate_formula.py`
   - Obtenir vrai R²
   - Générer formule v9 finale

5. **Implémenter formule finale** (1h)
   - Créer `fix_impacts_v9_final.py`
   - Tester sur plusieurs dates
   - Valider vs MT5

---

## 📊 DONNÉES DE RÉFÉRENCE

### Test principal : 11 septembre 2025

**Événements :**
- **14:15** : ECB Interest Rate Decision (5 événements)
- **14:30** : CPI, Inflation, Jobless (33 événements simultanés)
- **14:45** : Current Account (1 événement)
- **20:00** : Monthly Budget Statement (1 événement)

**Observations MT5 (d'après utilisateur) :**
- Phase 1 (14:30-14:35) : Spike initial
- TTR Phase 1 (14:35-14:45) : Consolidation/pullback
- Phase 2 (14:45-15:10) : Current Account + stabilisation

**Impact total attendu :** À mesurer manuellement sur MT5

**Calcul actuel (INCORRECT) :**
- Impact calculé : 59.2 pips (juste le MFE d'une fenêtre)
- ⚠️ Ne reflète pas l'impact total multi-phases

---

## 🔧 APPROCHE RECOMMANDÉE

### Étape 1 : Validation terrain

**Avant tout calcul, obtenir la vérité terrain :**

```
1. Ouvrir graphiques MT5 du 11 septembre 2025
2. Identifier le prix à 14:29 (avant événements)
3. Mesurer le MFE de la Phase 1 (14:30-14:35)
4. Identifier le prix avant Phase 2 (14:44)
5. Mesurer le MFE de la Phase 2 (14:45-15:10)
6. Calculer impact total

Documenter dans un fichier MT5_MEASUREMENTS.md
```

### Étape 2 : Comprendre l'existant

**Fichier clé :** `sequence_multi_event_timeline_v86.py`

Ce fichier gère déjà :
- Regroupement événements simultanés
- Calcul impact combiné
- Phases successives
- Pullback entre phases

**Action :**
```python
# Lire le fichier
# Identifier la fonction qui calcule l'impact combiné
# Comprendre la logique vectorielle
# S'inspirer pour le nouveau script
```

### Étape 3 : Nouveau script

**Créer :** `calculate_grouped_impacts.py`

**Logique :**
```python
# 1. Charger événements et prix
events_df = load_events()
prices_df = load_prices()

# 2. Grouper par minute
events_df['time_group'] = pd.to_datetime(events_df['ts_utc']).dt.floor('1min')
grouped = events_df.groupby('time_group')

# 3. Pour chaque groupe temporel
results = []
for time_group, group_events in grouped:
    # Calculer UN SEUL impact pour tout le groupe
    impact = calculate_combined_impact(time_group, prices_df)
    
    # Stocker avec métadonnées du groupe
    results.append({
        'time_group': time_group,
        'num_events': len(group_events),
        'max_score': group_events['empirical_score'].max(),
        'mean_score': group_events['empirical_score'].mean(),
        'event_keys': ','.join(group_events['event_key'].tolist()),
        'mfe_pips': impact['mfe'],
        'mae_pips': impact['mae'],
        'ttr_minutes': impact['ttr'],
        'direction': impact['direction']
    })

# 4. Sauvegarder
save_to_db(results, 'event_group_impacts')
```

### Étape 4 : Phases successives

**Pour gérer 14:30 puis 14:45 :**

```python
# Détecter phases successives (gap > 5 minutes)
phases = detect_phases(grouped_impacts, min_gap_minutes=5)

# Pour chaque séquence de phases
for sequence in phases:
    # Calculer impact total
    total_impact = sum(phase['mfe_pips'] for phase in sequence)
    
    # Gérer pullback entre phases
    # (Utiliser logique de sequence_multi_event_timeline_v86.py)
```

---

## 📁 FICHIERS IMPORTANTS

### Documentation (À JOUR)

```
ADDENDUM_CRITIQUE_SESSION7.md      ⭐⭐⭐ LIS EN PREMIER !
START_HERE.md                      ⭐⭐  État général
KNOWLEDGE_BASE.md                  ⭐⭐  Erreurs/formules
DB_STRUCTURE_REFERENCE.md          ⭐    Structure DB
RAPPORT_SESSION7_FINAL.md          ⭐    Détails Session 7
```

### Scripts à consulter

```
sequence_multi_event_timeline_v86.py   ← Logique vectorielle existante
calculate_real_impacts.py              ← Script incorrect (référence)
analyze_and_generate_formula.py        ← Analyse (à relancer après correction)
```

### Scripts à créer Session 8

```
calculate_grouped_impacts.py           ← Nouveau calcul correct
validate_grouped_impacts.py            ← Validation
MT5_MEASUREMENTS.md                    ← Mesures manuelles terrain
```

---

## 🎯 CRITÈRES DE SUCCÈS SESSION 8

### Validation

- [ ] Mesure manuelle MT5 documentée
- [ ] Impact groupé calculé ≠ impact individuel
- [ ] 11 septembre : 1 ligne par time_group, pas 33
- [ ] Validation terrain : calcul ≈ observation MT5

### Analyse

- [ ] R² amélioré (ou au moins compréhension pourquoi faible)
- [ ] Formule v9 générée
- [ ] Précision > 70% sur test 11 septembre

### Documentation

- [ ] KNOWLEDGE_BASE.md mis à jour (erreur #7 ajoutée)
- [ ] RAPPORT_SESSION8_FINAL.md créé
- [ ] Metrics v9 documentées

---

## 💡 CONSEILS POUR SESSION 8

### 1. Ne pas se précipiter

La Session 7 a montré qu'il vaut mieux :
- Valider contre terrain AVANT de conclure
- Vérifier la cohérence des résultats
- Ne pas hésiter à remettre en question

### 2. Utiliser l'existant

`sequence_multi_event_timeline_v86.py` contient probablement la bonne approche. Pas besoin de réinventer, juste de s'inspirer.

### 3. Mesure manuelle = référence

30 minutes à mesurer manuellement sur MT5 éviteront des heures de calculs basés sur de mauvaises hypothèses.

### 4. R² faible ≠ échec

Si R² reste à 0.3-0.4 :
- C'est OK ! L'impact a une composante aléatoire
- Mieux vaut 0.3 précis que 0.8 basé sur calculs faux
- La formule sera quand même utile

---

## 🔄 MISE À JOUR DOCUMENTATION

### À faire en fin de Session 8

```markdown
1. Mettre à jour KNOWLEDGE_BASE.md
   - Ajouter erreur #7 (calcul groupé vs individuel)
   - Marquer v7/v8 comme obsolètes
   - Ajouter v9 avec vraies métriques

2. Créer RAPPORT_SESSION8_FINAL.md
   - Documenter corrections apportées
   - Nouvelles métriques
   - Formule finale v9

3. Mettre à jour START_HERE.md
   - État actuel après Session 8
   - Prochaines étapes Session 9
```

---

## 📞 MESSAGE D'ACCUEIL SESSION 8

```
Bonjour Claude !

Je démarre la Session 8 du Planificateur Multi-Événements.

⚠️ IMPORTANT : Lis d'ABORD ces fichiers dans cet ordre :
1. ADDENDUM_CRITIQUE_SESSION7.md (CRITIQUE !)
2. START_HERE.md
3. KNOWLEDGE_BASE.md

Contexte :
✅ Session 7 : Documentation + scripts créés
⚠️ Erreur découverte : calcul individuel vs groupé
🎯 Session 8 : Corriger l'approche de calcul

Objectif immédiat :
Mesurer manuellement les impacts sur MT5 pour avoir une référence fiable.

Prêt à commencer ! 🚀
```

---

## 📊 CHECKLIST DÉMARRAGE SESSION 8

- [ ] Lu ADDENDUM_CRITIQUE_SESSION7.md
- [ ] Lu START_HERE.md
- [ ] Lu KNOWLEDGE_BASE.md (en sachant v7/v8 incorrects)
- [ ] Compris le problème : individuel vs groupé
- [ ] Identifié sequence_multi_event_timeline_v86.py comme référence
- [ ] Prêt à mesurer manuellement sur MT5

**Si tous les points sont cochés → GO ! 🚀**

---

**FIN SESSION8_INTRO.md**

**Version :** 1.0  
**Date :** 17 octobre 2025  
**Statut :** ✅ Prêt pour Session 8

**Prochaine étape :** Mesure manuelle MT5 du 11 septembre 2025
