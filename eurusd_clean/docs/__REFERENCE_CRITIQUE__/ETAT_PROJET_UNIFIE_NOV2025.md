# 🎯 ÉTAT PROJET UNIFIÉ - NOVEMBRE 2025

**Document maître :** Vue d'ensemble complète et actionnable  
**Créé :** 06 novembre 2025  
**Objectif projet :** Prédire impact multi-events/events simples EUR/USD pour aide trading

---

## 🎯 OBJECTIF PRINCIPAL

**Valider méthodologie et calculs prédictifs d'impacts pour prédire multi-events/events simples comme aide au trading.**

**Vision :** Reproduire les VRAIS mouvements MT5 avec formules validées scientifiquement.

**Objectifs quantifiés :**
- Précision impact : MAE < 5 pips ✅ (atteint Session 113)
- Précision timing : MAE < 2 minutes ⏳ (à valider)
- Détection pattern : 100% correct ⏳ (à valider multi-dates)

---

## ✅ CE QUI FONCTIONNE (PRODUCTION-READY)

### 1. Base de Données ✅✅✅

**warehouse.duckdb (205 MB)**
```
✅ events : 58,449 événements (+ 39,419 eodhd Session 113)
✅ prices_bern : Vue automatique timezone (Session 112 - INNOVATION)
✅ event_families : Scores empiriques validés
```

**Innovation Session 112 :**
```sql
CREATE VIEW prices_bern AS 
SELECT datetime + INTERVAL '2 hours' as datetime, ...
FROM prices_1m;
```
→ Event 14:30 Bern = Prix 14:30 direct (logique pure)  
→ Précision < 1 pip validée  
→ Impossible d'oublier conversion timezone

**Emplacement :** `eurusd_clean/data/warehouse.duckdb`

---

### 2. Formules Validées (Sessions 51-55) ✅✅✅

**Module :** `src/core/formulas_validated.py`

| Formule | Précision | Usage |
|---------|-----------|-------|
| Score ajusté | 99.9% | Ajustement surprise AVANT impact |
| **Impact D** | **98.6%** | Calcul impact pips ⭐ |
| TTR C | 94.4% | Time To Reversal |
| Pullback V2 | 99.3% | Retracement après peak |

**Validation 11 sept 2025 :**
- Impact prédit : 57.0 pips
- Impact MT5 : 56.2 pips
- **MAE : 0.8 pips** ✅✅✅

---

### 3. Amplification Dynamique (Sessions 107-109) ✅✅

**Cluster #3 (CPI) - Session 107 :**
```python
amplification_C3 = 0.5490 × R²_72h + 1.6988
# Amélioration : +95% vs baseline fixe 2.5
# MAE : 0.82 pips sur 6 dates CPI
```

**Cluster #1 (Manufacturing) - Session 109 :**
```python
amplification_C1 = 0.0339 × volatility_pips + 0.5352
# Amélioration : +41.8% vs baseline
# MAE : 0.291 pips sur 11 dates
```

**Status :** Formules validées scientifiquement avec Leave-One-Out

---

### 4. Architecture Clean (Session 112) ✅

```
eurusd_clean/
├── data/
│   └── warehouse.duckdb (DB unique)
├── src/
│   ├── core/
│   │   ├── formulas_validated.py ⭐
│   │   ├── impact_measurement.py (v4.0 - vue prices_bern)
│   │   ├── cluster_impact_calculator.py (Session 111)
│   │   ├── event_loader.py
│   │   ├── double_wave.py
│   │   └── single_wave_strong.py
│   └── config.py (chemins centralisés)
├── streamlit_app/
│   ├── Home.py ✅
│   └── pages/
│       ├── 1_Calendrier_Trading.py (fixé S112)
│       ├── 2_Planificateur_V2.py ✅⭐
│       ├── 3_API_Status.py ✅
│       └── 4_Mise_a_jour_DB.py ✅
└── scripts/
    └── session113/ (import eodhd + tests)
```

**Status :** Architecture propre, modules centralisés, chemins validés

---

### 5. Surprise Vectorielle (Session 113) ✅✅✅

**Innovation majeure :**
```python
# AVANT : Surprise scalaire (perdait 70% info)
surprise = max(surprises)

# APRÈS : Surprise vectorielle (somme algébrique)
surprise_net = sqrt(sum(surprise_i²))  # Magnitude vectorielle
```

**Impact :** -70% erreur sur multi-events

**Validation 11 sept Cluster 1 :**
- Impact prédit : 37.37 pips
- Impact MT5 : 37.3 pips
- **Précision : 99.8%** ✅✅✅

**Surprise en points (taux/inflation) :**
```python
# Taux : 5.25% vs 5.00% → Surprise = 0.25 points (pas 5%)
# CPI : 3.2% vs 2.4% → Surprise = 0.8 points (pas 33%)
```

---

## 🟡 EN DÉVELOPPEMENT (CRITICAL PATH)

### 1. Calcul Impact Par Cluster (Session 111) ⚠️

**Problème identifié Session 110 :**
```python
# ACTUEL (FAUX - pattern matching MT5)
impact_cluster1 = impact_total * 0.40   # Ratio fixe 40%
impact_cluster2 = impact_total * 0.82   # Ratio fixe 82%
t_peak1 = t0 + timedelta(minutes=5)     # Timing fixe T+5
```

**Solution créée Session 111 (NON TESTÉE) :**

**Fichier :** `src/core/cluster_impact_calculator.py` (500 lignes)

**Fonctions :**
```python
calculate_cluster_impact(cluster_events, amplification)
  → Calcule impact d'UN cluster isolément
  → Utilise formules S51-55 sur événements du cluster seul
  → Returns: {impact_pips, ttr_minutes, base_score}

calculate_cluster_ttr(cluster_events, cluster_impact)
  → TTR adaptatif selon taille/force cluster
  → PAS fixe à 5 min !

analyze_cluster_pattern(clusters, impacts)
  → Détecte pattern: "overlapping", "sequential", "cumulative"
  → Permet timeline adaptative vraie
```

**Status :** ⚠️ Code créé MAIS NON TESTÉ  
**Risque :** Session 111 interrompue avant validation

**Tests à faire :**
- [ ] Test Cluster 1 (14 events CPI) → Attendu 37-42 pips
- [ ] Test Cluster 2 (1 event Current Account) → Attendu 12-22 pips
- [ ] Validation 11 sept complet avec 2 clusters

---

### 2. Timeline Dynamique Vraie (Sessions 110-111) ⚠️

**Actuellement (Session 110) :**
- Détection clusters temporels ✅
- Graphique adaptatif MAIS ratios MT5 hardcodés ❌

**Objectif Session 111 (NON TERMINÉ) :**
```python
# Pour chaque cluster détecté :
for cluster in temporal_clusters:
    cluster_impact = calculate_cluster_impact(cluster.events)
    cluster_ttr = calculate_cluster_ttr(cluster.events, cluster_impact)
    
# Analyser pattern global
pattern = analyze_cluster_pattern(clusters, impacts)

# Timeline adaptative selon pattern détecté
if pattern == "overlapping":
    # Cluster 2 pendant pullback Cluster 1
elif pattern == "sequential":
    # Clusters séparés, impacts distincts
elif pattern == "cumulative":
    # Clusters simultanés, impact combiné
```

**Status :** Architecture définie MAIS implémentation incomplète

---

### 3. Planificateur V2 (État Actuel) 🟡

**Ce qui fonctionne (images fournies) :**
```
Date : 2025-09-11
Prix départ : 1.16816
✅ 7 événements HIGH trouvés
✅ Impact prédit : 57.6 pips
✅ Impact MT5 : 56.2 pips
✅ MAE : 1.4 pips (EXCELLENT)
✅ TTR prédit : 6.0 min
✅ TTR observé : 5.0 min (MAE 1 min)
✅ Pullback : 26.9 pips prédit vs 27.1 observé
✅ Graphique timeline affiché
✅ Validation MT5 visible
```

**Problème signalé André :**
> "Le planificateur v2 prédit en partie mais ne charge pas le bon nombre d'events"

**Hypothèses :**
1. Affiche 7 events MAIS Cluster 1 devrait avoir 14 events CPI ?
2. Manque events Cluster 2 (Current Account) ?
3. Déduplication trop agressive ?

**À vérifier :**
```python
# Query SQL actuelle (Planificateur V2)
WHERE DATE(ts_utc) = ?
    AND country = 'US'
    AND ef.empirical_score > 40

# Devrait retourner pour 11 sept :
# - Cluster 1 (14:30) : 14 events CPI + Jobless
# - Cluster 2 (14:45) : 1 event Current Account DE
# Total attendu : 15 events (pas 7)
```

**Action requise :** Debug query SQL + validation nombre events

---

## 📋 ÉTAPES À RÉALISER (PRIORITÉS)

### 🔴 PRIORITÉ 1 : Valider Module Cluster (Session 111)

**Durée estimée :** 2-3h

**Actions :**
1. **Tester `calculate_cluster_impact()` sur données réelles**
   ```bash
   cd eurusd_clean/scripts/session111
   python test_cluster_calculator_REAL_DATA.py
   ```
   - Cluster 1 : MAE attendu < 5 pips
   - Cluster 2 : MAE attendu < 8 pips

2. **Si tests OK → Intégrer dans Planificateur V2**
   - Modifier `calculate_predictions()` pour utiliser calcul par cluster
   - Supprimer ratios hardcodés (0.40, 0.82)
   - Supprimer timings fixes (T+5, T+21)

3. **Si tests KO → Debug formules**
   - Vérifier surprise vectorielle appliquée
   - Vérifier amplification dynamique selon cluster
   - Comparer vs formules S51-55 directes

**Résultat attendu :** Prédiction impact par cluster avec MAE < 5 pips

---

### 🔴 PRIORITÉ 2 : Corriger Nombre Events Planificateur

**Durée estimée :** 1h

**Actions :**
1. **Debug query SQL du Planificateur**
   ```python
   # Ajouter logs debug temporaires
   events_raw = conn.execute(query).fetchdf()
   print(f"Events bruts query : {len(events_raw)}")
   print(f"Events après déduplication : {len(events_deduplicated)}")
   
   # Pour 11 sept 2025 attendu :
   # - Events bruts : ~15
   # - Après déduplication : ~15 (sauf si problème)
   ```

2. **Vérifier déduplication (Session 39 corrigée)**
   ```python
   # GROUP BY e.ts_utc, e.event_key, e.country
   # AVG(ef.empirical_score) as empirical_score
   # → Devrait préserver tous events distincts
   ```

3. **Tester query sur 11 sept manuellement**
   ```python
   # Charger DB
   # Query date 2025-09-11
   # Compter events par cluster
   # Vérifier vs attendu (14 + 1 = 15)
   ```

**Résultat attendu :** 15 events chargés (14 Cluster 1 + 1 Cluster 2)

---

### 🟡 PRIORITÉ 3 : Validation Multi-Dates

**Durée estimée :** 3-4h

**Objectif :** Prouver généralisation formules

**Dates à tester (déjà identifiées Session 83) :**
```
✅ 2025-09-11 : CPI (référence validée)
⏳ 2025-08-01 : NFP (17 events, surprise 500%)
⏳ 2025-07-15 : CPI (attendu pattern différent)
⏳ 2025-06-11 : CPI (validation Cluster #3)
⏳ 2025-02-12 : CPI (8 events, pattern simple)
```

**Métriques success :**
- MAE impact < 10 pips (80% des cas)
- MAE timing < 5 min (80% des cas)
- Pattern détection 100% correct

**Actions :**
1. Script validation automatisé
2. Pour chaque date : Prédiction vs MT5/Dukascopy
3. Calcul MAE global
4. Analyse échecs (si > 10 pips)

---

### 🟢 PRIORITÉ 4 : Documentation Production

**Durée estimée :** 2h

**À créer :**
1. **Guide Utilisateur Planificateur**
   - Comment sélectionner date
   - Interprétation résultats
   - Cas d'usage trading

2. **Guide Technique Développeur**
   - Architecture modules
   - Comment ajouter nouvelle formule
   - Process validation obligatoire

3. **Procédures Maintenance**
   - Mise à jour DB events (EODHD)
   - Mise à jour prix (Dukascopy)
   - Backup DB

---

## 🎯 DÉCISIONS CLÉS PRISES

### Session 107-109 : Amplification Dynamique

**Décision André :** Privilégier précision maximale (Méthode Inversion)

**Formules validées :**
- Cluster #3 (CPI) : R² 72h → +95% amélioration
- Cluster #1 (Manufacturing) : Volatility → +42% amélioration

**Status :** Production-ready pour ces 2 clusters

---

### Session 110 : Détection Clusters

**Découverte :** Pattern "overlapping" (Cluster 2 PENDANT pullback Cluster 1)

**Impact :** Timeline adaptative nécessaire (pas ratios fixes MT5)

**Décision :** Créer module calcul par cluster (Session 111)

---

### Session 112 : Vue prices_bern

**Innovation :** Conversion timezone automatique en SQL

**Impact :** Impossible d'oublier conversion (+2h)

**Résultat :** Précision < 1 pip validée

**Décision :** TOUJOURS utiliser prices_bern (pas prices_1m)

---

### Session 113 : Surprise Vectorielle

**Découverte :** Somme scalaire perdait 70% info multi-events

**Solution :** Surprise vectorielle (magnitude) + points pour taux

**Résultat :** 99.8% précision Cluster 1

**Décision :** Intégrer dans `cluster_impact_calculator.py`

---

## 📊 MÉTRIQUES PROJET

### Performance Formules

| Composant | Précision | Status |
|-----------|-----------|--------|
| Formule Impact D | 98.6% | ✅ Validé |
| Formule TTR C | 94.4% | ✅ Validé |
| Formule Pullback V2 | 99.3% | ✅ Validé |
| Amp dynamique CPI | +95% vs baseline | ✅ Validé |
| Surprise vectorielle | 99.8% | ✅ Validé S113 |
| Calcul par cluster | ? | ⚠️ Non testé |
| Timeline dynamique | ? | ⚠️ Ratios MT5 |

### Couverture Validation

```
✅ Cas référence 11 sept : Validé (56.2 pips MT5)
✅ Cluster #3 (CPI) : Validé 6 dates
✅ Cluster #1 (Manufacturing) : Validé 11 dates
⏳ Validation multi-dates : 1/5 (20%)
⏳ Patterns variés : En cours
⏳ Production multi-users : Pas encore
```

### Code Quality

```
✅ Architecture clean : eurusd_clean/ centralisé
✅ Modules validés : src/core/ organisé
✅ Tests unitaires : Partiels (à compléter)
✅ Documentation : Bonne (ce document)
⏳ CI/CD : Absent
⏳ Monitoring production : Absent
```

---

## 🚨 RISQUES IDENTIFIÉS

### 🔴 Risque CRITIQUE : Module Cluster Non Testé

**Problème :** `cluster_impact_calculator.py` créé MAIS jamais exécuté

**Impact potentiel :**
- Formules incorrectes → Prédictions fausses
- Bugs runtime → Planificateur casse
- Logique erronée → Généralisation impossible

**Mitigation :** TESTER AVANT toute intégration Planificateur

**Priorité :** ABSOLUE (bloque tout le reste)

---

### 🟡 Risque MOYEN : Ratios MT5 Hardcodés

**Problème :** Timeline actuelle = pattern matching, pas prédiction

**Impact potentiel :**
- Fonctionne uniquement sur cas similaires 11 sept
- Échoue sur patterns différents
- Pas généralisable multi-dates

**Mitigation :** Intégrer calcul par cluster (Session 111)

**Priorité :** HAUTE (après tests module)

---

### 🟢 Risque FAIBLE : Validation Multi-Dates Incomplète

**Problème :** Seulement 1 date validée exhaustivement (11 sept)

**Impact potentiel :**
- Overfitting sur cas référence
- Mauvaises surprises sur dates variées
- Confiance utilisateur compromise

**Mitigation :** Tests sur 5+ dates diverses

**Priorité :** MOYENNE (après Priorités 1-2)

---

## 🎯 ROADMAP IMMÉDIATE (2-3 SESSIONS)

### Session 114 : Tests & Intégration Cluster

**Objectifs :**
1. ✅ Tester `cluster_impact_calculator.py` sur données réelles
2. ✅ Valider MAE < 5 pips par cluster
3. ✅ Intégrer dans Planificateur V2 si tests OK
4. ✅ Corriger nombre events chargés (15 attendus)

**Durée :** 3-4h  
**Tokens :** ~80-100k

---

### Session 115 : Validation Multi-Dates

**Objectifs :**
1. ✅ Tester 5 dates diverses (01.08, 15.07, 11.06, 13.05, 12.02)
2. ✅ Mesurer MAE globale
3. ✅ Analyser patterns détectés
4. ✅ Documenter échecs et causes

**Durée :** 3-4h  
**Tokens :** ~80-100k

---

### Session 116 : Documentation Production

**Objectifs :**
1. ✅ Guide utilisateur Planificateur
2. ✅ Guide technique développeur
3. ✅ Procédures maintenance DB
4. ✅ Checklist validation formules

**Durée :** 2h  
**Tokens :** ~50k

---

## 📚 FICHIERS RÉFÉRENCES CRITIQUES

### Code Production

```
src/core/formulas_validated.py          ⭐ Formules S51-55
src/core/cluster_impact_calculator.py   ⚠️ À tester
src/core/impact_measurement.py          ✅ v4.0 (prices_bern)
src/config.py                            ✅ Chemins centralisés
streamlit_app/pages/2_Planificateur_V2.py  🟡 Fonctionnel (à améliorer)
```

### Documentation

```
__REFERENCE_CRITIQUE__/METHODES_VALIDEES.md          ⭐ Ce qui fonctionne
__REFERENCE_CRITIQUE__/SESSION_113_RAPPORT_FINAL.md  ⭐ Surprise vectorielle
__REFERENCE_CRITIQUE__/SESSION_112_RAPPORT_FINAL.md  ⭐ Vue prices_bern
__REFERENCE_CRITIQUE__/SESSION_111_ETAT_ACTUEL.md    ⚠️ Module non testé
__REFERENCE_CRITIQUE__/SESSION_110_RAPPORT_FINAL.md  🟡 Timeline dynamique
__REFERENCE_CRITIQUE__/REFERENCE_CASE_11_SEPT_2025.md  ⭐ Cas référence
__REFERENCE_CRITIQUE__/ETAT_PROJET_UNIFIE_NOV2025.md  ⭐ CE DOCUMENT
```

### Scripts Critiques

```
scripts/session113/import_eodhd_surprise_vectorielle.py  ✅
scripts/session112/CREATE_VIEW_prices_bern.py            ✅
scripts/session111/test_cluster_calculator_REAL_DATA.py  ⚠️ À exécuter
```

---

## 💡 PRINCIPES VALIDÉS

### 1. "On laisse rien au hasard"

**Application :**
- Mesures MT5 précises au pip près
- Validation sur données réelles (pas théoriques)
- Tests exhaustifs avant production

**Exemple Session 113 :** 99.8% précision (0.07 pips MAE)

---

### 2. "Pas d'approximations en trading réel"

**Application :**
- Formules validées scientifiquement (Leave-One-Out)
- Pas de ratios hardcodés (Session 110 à corriger)
- Timezone exacte (vue prices_bern)

**Contre-exemple Session 110 :** Ratios MT5 0.40/0.82 = approximation ❌

---

### 3. "Tester AVANT intégrer"

**Application :**
- Module cluster : TESTER d'abord (Session 111 violée)
- Validation multi-dates : AVANT production
- Cas référence 11 sept : TOUJOURS vérifier

**Leçon Session 111 :** Module créé non testé = risque critique

---

### 4. "Architecture avant optimisation"

**Application :**
- Structure clean eurusd_clean/ d'abord
- Modules centralisés avant performance
- Vue prices_bern avant optimisation queries

**Succès Session 112 :** Restructuration complète avant intégration

---

## 🎓 LEÇONS APPRISES (Sessions 110-113)

### ✅ Succès

**Session 112 - Vue prices_bern :**
> Innovation majeure qui résout 20+ sessions confusion timezone

**Session 113 - Surprise vectorielle :**
> -70% erreur en corrigeant méthodologie calcul surprise

**Sessions 107-109 - Amplification dynamique :**
> +95% amélioration avec approche scientifique rigoureuse

---

### ⚠️ Échecs / Leçons

**Session 110 - Ratios hardcodés :**
> Pattern matching ≠ Prédiction. Fonctionne uniquement sur cas similaires.

**Session 111 - Module non testé :**
> Créer sans tester = risque critique. TOUJOURS valider avant intégrer.

**Dilution documentation :**
> Trop de docs fragmentés → Nouvelles sessions redécouvrent tout.  
> **Solution :** CE document unique (ETAT_PROJET_UNIFIE_NOV2025.md)

---

## 🔧 COMMANDES RAPIDES

### Lancer Planificateur

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean
source .venv/bin/activate
streamlit run streamlit_app/Home.py
```

### Tester Module Cluster (URGENT)

```bash
cd eurusd_clean/scripts/session111
python test_cluster_calculator_REAL_DATA.py
```

### Vérifier DB

```python
import duckdb
conn = duckdb.connect('eurusd_clean/data/warehouse.duckdb', read_only=True)
print(conn.execute("SELECT COUNT(*) FROM events").fetchone()[0])
print(conn.execute("SELECT COUNT(*) FROM prices_bern").fetchone()[0])
```

### Debug Nombre Events Planificateur

```python
# Dans Planificateur, ajouter logs temporaires
query = "SELECT ... WHERE DATE(ts_utc) = '2025-09-11' ..."
events_raw = conn.execute(query).fetchdf()
print(f"DEBUG: Events bruts = {len(events_raw)}")
print(events_raw[['ts_utc', 'event_title', 'empirical_score']])
```

---

## ✅ CHECKLIST PROCHAINE SESSION

**Avant de commencer :**
- [ ] Lire CE document (ETAT_PROJET_UNIFIE_NOV2025.md) ⭐
- [ ] Lire SESSION_113_RAPPORT_FINAL.md (surprise vectorielle)
- [ ] Lire SESSION_111_ETAT_ACTUEL.md (module à tester)
- [ ] Vérifier token budget (actuellement ~100k/190k disponibles)

**Priorité 1 - Tests Module Cluster :**
- [ ] Exécuter `test_cluster_calculator_REAL_DATA.py`
- [ ] Vérifier MAE Cluster 1 < 5 pips
- [ ] Vérifier MAE Cluster 2 < 8 pips
- [ ] Si OK → Intégrer Planificateur
- [ ] Si KO → Debug formules

**Priorité 2 - Corriger Nombre Events :**
- [ ] Debug query SQL Planificateur
- [ ] Vérifier déduplication
- [ ] Test manuel 11 sept (attendu 15 events)
- [ ] Corriger si nécessaire

**À NE PAS FAIRE :**
- ❌ Créer nouveau document fragmenté
- ❌ Réinventer formules validées
- ❌ Intégrer code non testé
- ❌ Ignorer cas référence 11 sept

---

## 📞 SI SESSION INTERROMPUE

**Pour reprendre :**
1. Lire CE document en entier (vue complète)
2. Identifier dernière étape complétée
3. Continuer à l'étape suivante (voir ROADMAP)
4. Mettre à jour CE document si changements

**Documents à NE PAS recréer :**
- PROJECT_STATE_NEW.md existe déjà
- METHODES_VALIDEES.md existe déjà
- Rapports Sessions 110-113 existent déjà

**CE document = Source unique de vérité état projet**

---

## 🎯 VISION FINALE

**Court terme (1-2 semaines) :**
✅ Module cluster validé et intégré  
✅ Timeline dynamique vraie (pas ratios MT5)  
✅ Validation 5+ dates diverses  
✅ Documentation production complète

**Moyen terme (1 mois) :**
✅ Planificateur production-ready multi-users  
✅ Monitoring performance continu  
✅ Alertes automatiques cas extrêmes  
✅ Interface web optimisée

**Long terme (3 mois) :**
✅ Extension autres paires (GBP/USD, etc.)  
✅ Intégration ML avancé (si dataset > 100 dates)  
✅ API publique pour utilisateurs externes  
✅ Mobile app iOS/Android

---

**FIN DOCUMENT**

---

**Dernière mise à jour :** 06 novembre 2025  
**Statut :** ✅ Document maître unifié  
**Maintenance :** Mettre à jour à CHAQUE session importante  
**Principe :** UN document, PAS de fragmentation

**Questions/Clarifications :** Se référer à ce document AVANT créer nouveau doc
