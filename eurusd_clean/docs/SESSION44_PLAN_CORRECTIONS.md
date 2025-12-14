# 📋 SESSION 44 - PLAN CORRECTIONS DÉTAILLÉ

**Pour** : Session 45  
**Focus** : Latences et TTR surestimés  
**Estimation** : 85-100k tokens

---

## 🎯 VUE D'ENSEMBLE

### Problèmes Priorisés

| # | Problème | Impact | Difficulté | ROI | Priorité |
|---|----------|--------|------------|-----|----------|
| 3 | Latences ×7-10 | ⚠️⚠️⚠️ | Moyenne | ⭐⭐⭐⭐⭐ | 🔴 P0 |
| 4 | TTR ×3 | ⚠️⚠️ | Faible | ⭐⭐⭐⭐ | 🟡 P1 |
| 2 | CPI dupliqué | ⚠️ | Faible | ⭐⭐ | 🟢 P2 |

---

## 🔴 CORRECTION P0 : LATENCES (40-50k tokens)

### Analyse Situation

**Problème** :
```
Prédit : 7-10 min
Réel MT5 : ~1 min
Écart : ×7 à ×10
```

**Impact** :
- Toutes prédictions temporelles fausses
- Fenêtres de trading incorrectes
- UX dégradée (utilisateur attend trop longtemps)

### Causes Identifiées

**Cause #1 : Seuil détection**
```python
# latency_analyzer.py ligne 72
threshold_pips = 5.0  # ❌ Trop élevé
```

Si marché bouge :
- 0 → 2 pips en 30 sec (✅ réaction réelle)
- 2 → 5 pips en 5 min (⏰ détection actuelle)
- Latence mesurée : 5 min au lieu de 30 sec

**Cause #2 : Données biaisées**
- 3 ans d'historique inclut événements calmes
- Moyenne tirée vers le haut
- Médiane plus robuste mais insuffisante

### Plan Correction

#### Étape 1 : Diagnostic (5-10k tokens)

**Action** : Analyser stats actuelles

```bash
# Script à créer
python3 analyze_latency_stats_session45.py
```

**Contenu script** :
```python
# Requête stats actuelles
SELECT 
    family,
    latency_median,
    latency_p20,
    latency_p80,
    n_events_latency,
    ttr_median
FROM event_families
WHERE family IN ('CPI', 'Jobless_Claims', 'Current_Account')
ORDER BY family
```

**Sortie attendue** :
```
CPI:
  latency_median: 7.0 min
  latency_p20: 3.5 min
  latency_p80: 10.5 min
  n_events: 156
  
Jobless_Claims:
  latency_median: 7.0 min
  ...
```

#### Étape 2 : Modification threshold (5k tokens)

**Fichier** : `fx_impact_app/src/latency_analyzer.py`

**Ligne 72** :
```python
# AVANT
threshold_pips: float = 5.0

# APRÈS (Session 45)
threshold_pips: float = 2.0  # 🆕 S45 : Détection réaction rapide
```

**Ligne 143** (fonction predict_latency_for_event) :
```python
# AVANT
threshold_pips

# APRÈS
threshold_pips=2.0  # 🆕 S45 : Cohérence
```

**Sauvegarde** :
```bash
cp latency_analyzer.py latency_analyzer.py.backup_session44
```

#### Étape 3 : Re-calcul stats (10-15k tokens)

**Backup DB** :
```bash
cp fx_impact_app/data/warehouse.duckdb \
   fx_impact_app/data/warehouse_backup_session45.duckdb
```

**Exécution** :
```bash
python3 precompute_families_FINAL.py
```

**Sortie attendue** :
```
Famille CPI:
  latency_median: 1.2 min (AVANT: 7.0)
  latency_p20: 0.5 min
  latency_p80: 2.5 min
  
Amélioration: -81% ✅
```

**Durée** : ~10-15 minutes

#### Étape 4 : Validation (10-15k tokens)

**Test 1 : Vérification DB**
```python
# Script check_latency_correction_session45.py
conn = duckdb.connect(db_path)
result = conn.execute("""
    SELECT family, latency_median 
    FROM event_families 
    WHERE family = 'CPI'
""").fetchone()

assert result[1] < 3.0, "Latence toujours trop élevée !"
```

**Test 2 : Streamlit**
```bash
cd fx_impact_app
streamlit run streamlit_app/Home.py

# Charger 11/09/2025
# Vérifier Phase 1 : latence ~1-2 min ✅
```

**Test 3 : Comparaison MT5**
- Phase 1 Prédit : ~1-2 min
- Phase 1 Réel MT5 : ~1 min
- Écart : OK (± 1 min) ✅

#### Étape 5 : Documentation (5-10k tokens)

Créer `SESSION45_CORRECTION_LATENCES.md` :
- Stats avant/après
- Graphiques comparaison
- Validation tests
- Impact sur UX

---

## 🟡 CORRECTION P1 : TTR (15-20k tokens)

### Analyse Situation

**Problème** :
```
Prédit : 15 min
Réel MT5 : ~5 min
Écart : ×3
```

**Formule actuelle** :
```python
ttr_median = latency_median × 1.5
```

### Plan Correction

#### Étape 1 : Vérification post-latence (5k tokens)

Après correction latences :
```
latency_median = 1 min
→ ttr_median = 1 × 1.5 = 1.5 min ❌ (trop bas maintenant)

Réel MT5 = 5 min
Ratio réel = 5 / 1 = ×5
```

**Nouveau facteur requis** : ×5 ou ×3

#### Étape 2 : Test facteurs (5k tokens)

**Fichier** : `precompute_families_FINAL.py` ligne 144

**Test facteur ×3** :
```python
'ttr_median': lat_median * 3.0,  # Test 1
```

Résultat attendu : 1 min × 3 = 3 min (proche de 5 min)

**Test facteur ×5** :
```python
'ttr_median': lat_median * 5.0,  # Test 2
```

Résultat attendu : 1 min × 5 = 5 min ✅ (exact)

#### Étape 3 : Validation empirique (5-10k tokens)

Analyser plusieurs cas :
- 11/09/2025 : Facteur ×5 OK ?
- Autres dates : Cohérent ?
- Graphiques MT5 : Validation visuelle

**Décision** : Garder facteur qui minimise écart moyen

#### Étape 4 : Re-calcul (si modifié)

Si facteur changé :
```bash
python3 precompute_families_FINAL.py
```

Sinon : RAS (TTR déjà recalculé avec latences)

---

## 🟢 CORRECTION P2 : CPI DUPLIQUÉ (10k tokens)

### Analyse Situation

**Symptôme** :
```
Phase 1 : CPI + Jobless + Jobless + CPI + CPI + Jobless
```

**Diagnostic** :
- ✅ DB propre (aucun doublon vérifié)
- ❌ Doublons dans DataFrame `predictions`

### Plan Correction

#### Étape 1 : Identifier source (5k tokens)

**Fichier** : `4_Planificateur_STABLE_0159_PERFECT.py`

**Bloc suspecté** : Lignes 577-604 (normalisation événements)

```python
# Vérifier si loop crée doublons
for pred in predictions:
    event = pred['event']
    # Si même event traité plusieurs fois → doublon
```

**Debug** : Ajouter print temporaire
```python
print(f"Event : {event['family']} @ {event['ts_utc']}")
# Si CPI apparaît 3 fois → source identifiée
```

#### Étape 2 : Déduplication (3k tokens)

**Solution simple** :

```python
# AVANT passage à sequence_multi_event_timeline()
# Ligne ~577

# 🆕 SESSION 45 : Déduplication événements
seen_events = set()
predictions_dedup = []

for pred in predictions:
    event_key = f"{pred['event']['family']}_{pred['event']['ts_utc']}"
    
    if event_key not in seen_events:
        seen_events.add(event_key)
        predictions_dedup.append(pred)
    else:
        print(f"⚠️ Doublon ignoré : {pred['event']['family']}")

# Utiliser predictions_dedup au lieu de predictions
phases = sequence_multi_event_timeline(predictions_dedup, ...)
```

#### Étape 3 : Test (2k tokens)

Streamlit 11/09/2025 :
- Phase 1 affiche : "CPI + Jobless Claims" (sans répétitions) ✅

---

## 📊 BUDGET TOKENS SESSION 45

### Distribution

| Tâche | Tokens | % |
|-------|--------|---|
| **Correction P0 (Latences)** | 40-50k | 44% |
| Correction P1 (TTR) | 15-20k | 18% |
| Correction P2 (CPI) | 10k | 11% |
| Tests validation | 10k | 11% |
| Documentation | 15k | 16% |
| **TOTAL** | **90-105k** | **100%** |

**Marge sécurité** : 10k tokens buffer

### Timeline Estimée

| Phase | Durée | Tokens |
|-------|-------|--------|
| Diagnostic initial | 30 min | 10k |
| Correction latences | 2h | 40-50k |
| Correction TTR | 1h | 15-20k |
| Correction CPI | 30 min | 10k |
| Tests finaux | 30 min | 10k |
| Documentation | 45 min | 15k |
| **TOTAL** | **~5h** | **100-115k** |

---

## ✅ CHECKLIST SESSION 45

### Pré-requis

- [ ] Lire `SESSION44_RAPPORT_FINAL.md`
- [ ] Lire `MESSAGE_SESSION44_SESSION45.md`
- [ ] Lire `SESSION44_PLAN_CORRECTIONS.md` (ce fichier)
- [ ] Graphiques MT5 disponibles

### Préparation

- [ ] Backup DB (`warehouse_backup_session45.duckdb`)
- [ ] Backup `latency_analyzer.py`
- [ ] Vérifier stats actuelles (script diagnostic)

### Corrections P0

- [ ] Modifier `threshold_pips = 2.0`
- [ ] Re-exécuter `precompute_families_FINAL.py`
- [ ] Vérifier stats DB (CPI, Jobless, Current Account)
- [ ] Tester Streamlit 11/09/2025
- [ ] Comparer avec graphiques MT5
- [ ] Documenter avant/après

### Corrections P1

- [ ] Calculer nouveau facteur TTR
- [ ] Tester facteur ×3 vs ×5
- [ ] Valider avec MT5
- [ ] Re-calculer si nécessaire
- [ ] Documenter choix

### Corrections P2

- [ ] Identifier source doublons CPI
- [ ] Ajouter déduplication
- [ ] Tester affichage
- [ ] Vérifier pas d'effets secondaires

### Tests Finaux

- [ ] Test complet 11/09/2025
- [ ] Toutes métriques dans cibles
- [ ] Screenshots Streamlit
- [ ] Comparaison MT5 OK

### Documentation

- [ ] `SESSION45_RAPPORT_FINAL.md`
- [ ] `SESSION45_CORRECTION_LATENCES.md`
- [ ] `MESSAGE_SESSION45_SESSION46.md`
- [ ] Mise à jour `PROJECT_STATE.md`
- [ ] Mise à jour `INDEX.md`

---

## 🎯 CRITÈRES SUCCÈS

### Latences

| Métrique | Cible | Tolérance |
|----------|-------|-----------|
| Phase 1 latence | 1 min | ± 1 min |
| Phase 2 latence | 1 min | ± 1 min |
| MAE latences | < 2 min | - |

### TTR

| Métrique | Cible | Tolérance |
|----------|-------|-----------|
| Phase 1 TTR | 5 min | ± 2 min |
| Phase 2 TTR | 5 min | ± 2 min |
| MAE TTR | < 3 min | - |

### Général

- [ ] Pullback > 0 pips ✅ (déjà OK)
- [ ] CPI affiché 1 fois
- [ ] Pas de régression autres fonctionnalités
- [ ] Documentation complète

---

## 🚨 RISQUES ET MITIGATIONS

### Risque 1 : threshold_pips trop bas

**Symptôme** : Trop de faux positifs (bruit de marché)

**Mitigation** :
- Analyser distribution avant/après
- Tester threshold = 2.5 si 2.0 trop sensible
- Garder option configuration par famille

### Risque 2 : Re-calcul trop long

**Symptôme** : > 30 min pour precompute

**Mitigation** :
- Limiter à familles critiques d'abord
- Paralléliser si possible
- Documenter temps réel

### Risque 3 : TTR toujours incorrect

**Symptôme** : Nouveau facteur ne colle pas

**Mitigation** :
- Utiliser TTR observé depuis prix réels
- Déjà implémenté dans code (v8.4)
- Activer si calcul théorique insuffisant

### Risque 4 : Régression autres familles

**Symptôme** : Latences OK pour CPI mais fausses ailleurs

**Mitigation** :
- Tester plusieurs familles
- Comparer distribution globale
- Ajuster threshold par famille si nécessaire

---

## 📚 RESSOURCES

### Scripts Disponibles

- `check_precomputed_families_status.py` - Voir stats DB
- `validate_session42_corrections.py` - Validation structure
- `check_duplicates_session44.py` - Diagnostic doublons

### Scripts À Créer Session 45

- `analyze_latency_stats_session45.py` - Analyse avant/après
- `check_latency_correction_session45.py` - Validation corrections
- `test_ttr_factors_session45.py` - Test facteurs TTR

### Documentation Existante

- `SESSION44_RAPPORT_FINAL.md` - Diagnostic complet
- `MESSAGE_SESSION44_SESSION45.md` - Instructions démarrage
- `PROJECT_STATE.md` - État projet global

---

## 🎓 LEÇONS SESSION 44

### À Appliquer Session 45

1. **Tests intermédiaires** : Ne pas attendre la fin
2. **Focus unique** : Une correction à la fois
3. **Validation graphique** : MT5 = référence
4. **Documentation continue** : Au fur et à mesure

### À Éviter

1. **Scope trop large** : 4 problèmes était trop
2. **Tokens insuffisants** : Arrêt prématuré
3. **Pas de backup** : Toujours faire avant modif DB

---

**📋 Plan Session 45 prêt ! Focus : Latences → TTR → CPI**

---

*Plan détaillé corrections - Session 44 vers 45*  
*Date : 22 octobre 2025*
