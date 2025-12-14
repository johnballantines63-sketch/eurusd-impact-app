# 📁 FICHIERS CRITIQUES DU PROJET
**Projet :** EUR/USD News Impact Calculator  
**Dernière mise à jour :** 04 novembre 2025 - Session 111

---

## 🎯 NAVIGATION RAPIDE

### Pour démarrer une nouvelle session
1. **`PROJECT_STATE_NEW.md`** - État global du projet ⭐⭐⭐
2. **`MANDATORY_SESSION_RULES.md`** - Règles obligatoires sessions ⭐⭐⭐
3. **`SESSION_XXX_RAPPORT_FINAL.md`** - Rapport session précédente ⭐⭐

### Pour comprendre le problème actuel
1. **`SESSION_111_ETAT_ACTUEL.md`** - Où on en est maintenant ⭐⭐⭐
2. **`SESSION_111_PLAN_ACTION.md`** - Ce qu'il reste à faire ⭐⭐
3. **`SESSION_110_RAPPORT_FINAL.md`** - Ce qui a été fait avant ⭐⭐

### Pour coder/implémenter
1. **`formulas_validated.py`** - Formules validées Sessions 51-55 ⭐⭐⭐
2. **`cluster_impact_calculator.py`** - Module Session 111 (nouveau) ⭐⭐⭐
3. **Planificateur V27** - Interface principale ⭐⭐

---

## 📚 DOCUMENTATION PRINCIPALE

### État Projet
```
eurusd_clean/docs/PROJECT_STATE_NEW.md
```
**Rôle :** Source de vérité unique du projet  
**Contenu :**
- État actuel (post-Session 109 documenté)
- Historique sessions importantes (92-110)
- Charte développement scientifique (Articles 1-7)
- Fichiers et scripts validés
- Erreurs récurrentes à éviter

**Quand lire :** TOUJOURS au début d'une session  
**Fréquence mise à jour :** Fin de chaque session majeure

---

### Règles Sessions
```
eurusd_clean/docs/MANDATORY_SESSION_RULES.md
```
**Rôle :** Règles non négociables pour chaque session  
**Contenu :**
- Checklist démarrage (5 étapes)
- Anti-patterns interdits
- Pattern de succès validé
- Budget tokens (105k/190k)

**Quand lire :** Début de TOUTE session  
**Critique :** Ne JAMAIS démarrer sans lire

---

### Sessions Récentes
```
eurusd_clean/docs/
├── SESSION_110_RAPPORT_FINAL.md          ⭐⭐⭐ (Interface + détection clusters)
├── SESSION_110_ETAT_PROBLEME_ARCHITECTURAL.md ⭐⭐ (Problème pattern matching)
├── SESSION_111_ETAT_ACTUEL.md            ⭐⭐⭐ (État actuel Session 111)
├── SESSION_111_PLAN_ACTION.md            ⭐⭐ (Plan détaillé 4 étapes)
├── SESSION_109_RAPPORT_COMPLET.md        ⭐⭐ (Formules dynamiques validées)
└── SESSION_107_RAPPORT_COMPLET.md        ⭐ (Amplification dynamique C#3)
```

**Rôle :** Historique détaillé des sessions  
**Quand lire :**
- Rapport session précédente : TOUJOURS
- Sessions N-2, N-3 : Si références dans rapport N-1
- Sessions plus anciennes : Si problème similaire

---

## 🧮 FORMULES & CALCULS

### Formules Validées (Sessions 51-55)
```
fx_impact_app/src/formulas_validated.py
```
**Rôle :** Module centralisé des formules GOLD STANDARD  
**Contenu :**
1. `calculate_adjusted_empirical_score()` - Ajustement score (Session 55, 99.9%)
2. `calculate_impact_d()` - Impact pips (Session 51, 98.6%)
3. `calculate_ttr_c()` - Time To Reversal (Session 52, 94.4%)
4. `calculate_pullback_v2()` - Pullback (Session 53, 99.3%)

**Utilisation :** TOUJOURS utiliser ces fonctions (ne JAMAIS recréer)  
**Documentation :** Docstrings complètes avec exemples  
**Tests :** Validés sur 11 sept 2025 (cas référence)

---

### Calcul Impact Par Cluster (Session 111)
```
fx_impact_app/src/cluster_impact_calculator.py
```
**Rôle :** Calcul impact de clusters individuels (NOUVEAU)  
**Contenu :**
1. `calculate_cluster_impact()` - Impact d'un cluster isolé
2. `calculate_cluster_ttr()` - TTR adaptatif par cluster
3. `calculate_pullback_characteristics()` - Pullback selon pattern
4. `analyze_cluster_pattern()` - Détection pattern global

**Status :** ✅ Créé Session 111, ⏳ NON TESTÉ encore  
**Dépendances :** Utilise `formulas_validated.py`

---

## 🖥️ INTERFACE PRINCIPALE

### Planificateur V27 (Production)
```
fx_impact_app/streamlit_app/pages/6_Planificateur_V27_AMPLIFICATION_DYNAMIQUE.py
```
**Rôle :** Interface Streamlit principale pour prédictions  
**Fonctionnalités actuelles :**
- Sélection événements avec checkboxes ✅
- Détection clusters temporels ✅
- Calcul prédictions ✅
- Timeline graphique ⚠️ (utilise ratios fixes - à corriger Session 111)

**Version :** V27 (Session 110)  
**À modifier :** Étape 3 Session 111 (intégration calcul dynamique)

**Fonctions clés :**
- `calculate_predictions()` - Calcul impact total
- `detect_temporal_clusters()` - Groupement événements
- `create_dynamic_timeline_chart()` - Génération graphique (à refactorer)

---

## 💾 BASE DE DONNÉES

### DuckDB Warehouse
```
eurusd_clean/app/data/warehouse.duckdb
```
**Taille :** 205 MB  
**Tables critiques :**
- `events` - 58,449 événements économiques
- `event_families` - Familles avec empirical_score
- `prices_1m` - Prix EUR/USD minute par minute
- `event_impacts_v2` - Impacts calculés

**⚠️ Colonnes importantes :**
- `datetime` (pas `timestamp` qui est NULL)
- `empirical_score` (pas `empirical_impact` qui n'existe pas)

**Guide timezone :** `GUIDE_TIMEZONE_DEFINITIF.md`

---

### Dataset CPI Validé (Session 99-100)
```
eurusd_clean/scripts/session99/real_impacts_TIMEZONE_FIX_FINAL.csv
```
**Contenu :** 29 dates CPI US avec impacts réels MT5  
**Colonnes :**
- `date` - Date événement
- `impact_pips_observed` - Impact réel mesuré
- `event_time_bern` - Heure événement (UTC+2)
- `price_before` - Prix avant
- `price_after` - Prix après

**Utilisation :** Validation formules, tests multi-dates  
**Timezone :** Corrigé Session 100 (événements et prix en Bern +02:00)

---

## 🔬 SCRIPTS VALIDATION

### Validation Prédictions vs Réalité
```
eurusd_clean/scripts/session84/validate_predictions_vs_reality.py
```
**Rôle :** Compare prédictions (formules S51-55) vs prix réels MT5/Dukascopy  
**Métriques :** MAE, RMSE, corrélation  
**Utilisation :** Tester sur nouvelles dates

---

### Test Cas Référence (11 sept 2025)
```
eurusd_clean/scripts/sessionXX/test_4_formules_11sept.py
```
**Rôle :** Validation guard-rail sur cas référence  
**Attendu :**
- Impact prédit : 56-57 pips
- Impact réel MT5 : 56.2 pips
- Écart < 1 pip ✅

**Utilisation :** Exécuter AVANT tout déploiement

---

### Scanner Dates Disponibles
```
eurusd_clean/scripts/session82/list_available_dates.py
```
**Rôle :** Liste dates HIGH IMPACT (score > 40) dans DB  
**Output :** `dates_disponibles.csv`  
**Utilisation :** Trouver dates pour tests validation

---

## 📊 CAS DE RÉFÉRENCE

### 11 Septembre 2025 - Cas Gold Standard
```
eurusd_clean/docs/REFERENCE_CASE_11_SEPT_2025.md
```
**Événements :** 9 CPI US simultanés (14:30 Bern)  
**Résultats validés :**
- Impact réel : 56.2 pips UP
- Impact prédit : 57.0 pips (MAE 0.8 pips) ✅
- TTR réel : 5 min
- TTR prédit : 4.7 min ✅
- Direction : UP ✅

**Utilisation :** Validation TOUTE nouvelle formule  
**Timezone :** Événement 14:30+02:00 → Prix 14:30+02:00 (même timezone)

---

### Observations MT5 (Session 110)
**Timeline détaillée 11 sept 2025 :**
```
14:30 - Cluster 1 (CPI + Jobless, 14 events)
14:35 - Peak 1 (+37.4 pips en 5 min)
14:45 - Cluster 2 (Current Account DE, 1 event) ← Arrive PENDANT pullback !
14:49 - Creux (-27.1 pips depuis peak 1, 4 min APRÈS cluster 2)
15:10 - Peak 2 Absolu (+45.9 pips depuis creux en 21 min)
```

**Ratios observés :**
- Impact C1 / Total : 66.5%
- Pullback / Peak 1 : 72.5%
- Impact C2 / Total : 81.7%

**Pattern :** Overlapping (cluster 2 pendant pullback cluster 1)

---

## 🎓 GUIDES UTILISATEUR

### Guide Timezone (CRITIQUE)
```
eurusd_clean/docs/GUIDE_TIMEZONE_DEFINITIF.md
```
**Rôle :** Éviter erreurs timezone (erreur récurrente Sessions 84-100)  
**Règle :** Événements ET prix en Bern +02:00 (pas de conversion)

---

### Guide Planificateur
```
eurusd_clean/docs/GUIDE_UTILISATEUR_PLANIFICATEUR.md
```
**Rôle :** Utilisation interface Planificateur  
**Contenu :**
- Sélection événements
- Interprétation prédictions
- Export CSV

---

### Guide Double Wave
```
eurusd_clean/docs/DOUBLE_WAVE_GUIDE_UTILISATEUR.md
eurusd_clean/docs/DOUBLE_WAVE_MODEL.md
```
**Rôle :** Pattern Double Wave (rare, 0.5-1% cas)  
**Conditions :** surprise > 20%, cluster ≥ 5, importance HIGH  
**Utilisation :** Référence historique (pattern exceptionnel)

---

## 🧪 SCRIPTS TESTS (À CRÉER SESSION 111)

### Tests Cluster Calculator
```
eurusd_clean/scripts/session111/
├── test_cluster_calculator_11sept.py    ⏳ (À créer Étape 2)
└── validation_multi_dates.py            ⏳ (À créer Étape 4)
```

**Rôle :** Valider fonctions `cluster_impact_calculator.py`  
**Tests :**
- Cluster 1 (14 events) : Impact 37-42 pips
- Cluster 2 (1 event) : Impact 12-22 pips
- Pattern détection : 'overlapping'

---

## 🚨 ERREURS RÉCURRENTES DOCUMENTÉES

### Anti-Patterns Critiques
```
eurusd_clean/docs/ANTI_PATTERN_CRITIQUE.md
eurusd_clean/docs/ERREURS_RECURRENTES_A_EVITER.md (section PROJECT_STATE_NEW.md)
```

**Top 3 erreurs :**
1. Colonne `datetime` vs `timestamp` (timestamp est NULL !)
2. `empirical_score` vs `empirical_impact` (empirical_impact n'existe pas)
3. Timezone conversions (ne PAS convertir, tout en Bern +02:00)

---

## 🔄 HISTORIQUE SESSIONS IMPORTANTES

### Sessions Formules Validées
```
SESSION_51_RAPPORT_FINAL.md - Formule Impact D (98.6%)
SESSION_52_RAPPORT_FINAL.md - Formule TTR C (94.4%)
SESSION_53_RAPPORT_FINAL.md - Formule Pullback V2 (99.3%)
SESSION_55_RAPPORT_FINAL.md - Score ajusté (99.9%)
```

### Sessions Amplification Dynamique
```
SESSION_101_RAPPORT_COMPLET.md - Amplification dynamique R² 72h (+13.1%)
SESSION_107_RAPPORT_COMPLET.md - Validation Cluster #3 (+95%)
SESSION_109_RAPPORT_COMPLET.md - Validation Cluster #1 (+42%)
```

### Sessions Timezone (CRITIQUES)
```
SESSION_100_METHODOLOGIE_VALIDEE.md - Fix timezone définitif
SESSION_106_METHODE_VALIDEE_MESURE_IMPACT.md - Méthode mesure standardisée
```

### Sessions Interface
```
SESSION_110_RAPPORT_FINAL.md - Interface sélection + détection clusters
SESSION_72_RAPPORT_COMPLET.md - Planificateur V2.4 (baseline stable)
```

---

## 📋 CHECKLIST UTILISATION FICHIERS

### Début Session (OBLIGATOIRE)
- [ ] Lire `PROJECT_STATE_NEW.md` (10 min)
- [ ] Lire `MANDATORY_SESSION_RULES.md` (5 min)
- [ ] Lire rapport session précédente (10 min)
- [ ] Lire message transition si existe (5 min)
- [ ] Vérifier token budget

### Avant Coder
- [ ] Consulter `formulas_validated.py` (réutiliser, ne pas recréer)
- [ ] Vérifier schéma DB (`DATABASE_SCHEMAS.md`)
- [ ] Lire guide timezone si manipulation dates/prix

### Avant Tester
- [ ] Cas référence 11 sept d'abord
- [ ] Dataset CPI validé (`real_impacts_TIMEZONE_FIX_FINAL.csv`)
- [ ] Scripts validation existants

### Fin Session
- [ ] Créer rapport session (`SESSION_XXX_RAPPORT_FINAL.md`)
- [ ] Mettre à jour `PROJECT_STATE_NEW.md`
- [ ] Créer message transition session suivante

---

## 🎯 FICHIERS PAR USE CASE

### "Je veux calculer un impact"
1. `formulas_validated.py` → `calculate_impact_d()`
2. Valider sur 11 sept (`test_4_formules_11sept.py`)

### "Je veux comprendre les clusters"
1. `SESSION_110_RAPPORT_FINAL.md` (observations MT5)
2. `cluster_impact_calculator.py` (nouveau module)
3. `SESSION_111_PLAN_ACTION.md` (détails patterns)

### "Je veux tester sur une nouvelle date"
1. `validate_predictions_vs_reality.py` (framework)
2. `real_impacts_TIMEZONE_FIX_FINAL.csv` (exemples)
3. `GUIDE_TIMEZONE_DEFINITIF.md` (éviter erreurs)

### "Je veux modifier le Planificateur"
1. Lire `SESSION_110_ETAT_PROBLEME_ARCHITECTURAL.md` (comprendre problème)
2. Module `cluster_impact_calculator.py` (nouvelles fonctions)
3. Planificateur V27 (fichier à modifier)

### "Je veux comprendre une erreur"
1. `PROJECT_STATE_NEW.md` → Section "Erreurs Récurrentes"
2. `ANTI_PATTERN_CRITIQUE.md`
3. Sessions 84-100 (timeline fixes)

---

## 📞 CONTACT SI BESOIN

**Si fichier manquant ou introuvable :**
- Vérifier dans `/eurusd_clean/docs/`
- Vérifier dans `/eurusd_clean/scripts/sessionXXX/`
- Consulter `PROJECT_STATE_NEW.md` → Section "Référence Rapide"

**Si documentation contradictoire :**
- `PROJECT_STATE_NEW.md` fait autorité (source unique vérité)
- En cas de doute, préférer sessions récentes (100+)

**Si information obsolète :**
- Sessions < 100 peuvent contenir approches abandonnées
- Toujours valider avec PROJECT_STATE_NEW avant d'appliquer

---

**Dernière mise à jour :** 04 novembre 2025 - Session 111  
**Fichiers totaux :** ~300+ fichiers docs  
**Fichiers critiques :** ~30 listés ci-dessus  
**Utilisation recommandée :** Bookmarker ce fichier comme référence
