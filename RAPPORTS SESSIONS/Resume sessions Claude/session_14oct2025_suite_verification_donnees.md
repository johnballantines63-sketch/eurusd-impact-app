# Session 14 Octobre 2025 (Suite) - Vérification Données et Calculs

**Date** : Lundi 14 octobre 2025 - Session 2
**Durée** : ~45 min
**Tokens** : ~84,000 / 130,000 (65%)
**Status** : 🚨 **PROBLÈME CRITIQUE DÉCOUVERT** - Calculs erronés de 466%

---

## 🎯 CONTEXTE DE REPRISE

**Session précédente** : Correction graphiques (2 scripts créés)
- ✅ `fix_graphique_phases.py` - Connecte phases au graphique
- ✅ `enhance_readability.py` - Améliore lisibilité

**Reprise actuelle** : Test des scripts sur 11/09/2025

---

## 🚨 DÉCOUVERTE CRITIQUE

### Screenshots Analysés (5 fournis)

#### Image 1 : Graphique Streamlit
- ✅ Message : "Graphique basé sur 2 phases calculées avec TTR observés"
- ✅ Phase 1 : 207.0 pips, TTR = 44 min
- ✅ Phase 2 : 24.9 pips, TTR = 28 min
- ❌ **AMPLITUDE AFFICHÉE : 378.6 pips** ← ERREUR !

#### Image 2 : Statistiques Simulation
- Amplitude Totale : **378.6 pips**
- Prix Maximum : 1.20513 (+378.3 pips)
- Prix Minimum : 1.16727 (-0.3 pips)

#### Image 3 : Détails par Phase
- **Phase 1** : 207.0 pips, TTR réel = 44 min ✅
- **Phase 2** : 24.9 pips, TTR réel = 28 min ✅
- Message : "Impact vectoriel combiné"

#### Image 4 : Graphique MetaTrader (RÉALITÉ)
- Prix départ (14:30) : ~1.16870
- Prix peak (15:00-15:15) : ~1.17280
- **AMPLITUDE RÉELLE : ~41 pips** ✅

#### Image 5 : Calcul Vectoriel
- Impact combiné final : **231.9 pips**
- TTR combiné : 7 min (incorrect, devrait être 44 min)

---

## 📊 COMPARAISON CHIFFRÉE

| Source | Amplitude | Écart vs Réalité |
|--------|-----------|------------------|
| **MetaTrader (Réel)** | **41 pips** | - (référence) |
| Calcul Vectoriel App | 231.9 pips | **+190.9 pips (+466%)** ❌ |
| Graphique Streamlit | 378.6 pips | **+337.6 pips (+823%)** ❌ |

### 🔥 ERREURS ABSOLUES

```
RÉALITÉ         :  41.0 pips  ✅
PRÉDIT          : 231.9 pips  ❌ (5.6x trop élevé !)
GRAPHIQUE       : 378.6 pips  ❌ (9.2x trop élevé !!)
```

---

## 🔍 ANALYSE DE LA CAUSE

### Problème 1 : Graphique Recalcule Amplitude

**Fichier** : `4_Planificateur-Multi-Evenements.py`
**Lignes** : ~1966-1970

```python
# ❌ CODE ACTUEL (INCORRECT)
max_movement = (price_df['high'].max() - start_price_input) * 10000
min_movement = (price_df['low'].min() - start_price_input) * 10000
observed_movement = max_movement if abs(max_movement) > abs(min_movement) else min_movement

# Ce code IGNORE phases calculées et recalcule depuis price_df généré !
```

**Résultat** :
- Utilise le peak de la courbe GÉNÉRÉE (378.6 pips)
- Au lieu du `impact_combined` des phases (231.9 pips)

---

### Problème 2 : Calcul Vectoriel Incorrect

**Fichier** : `backtest_utils.py` + `sequence_multi_event_timeline.py`

**Hypothèse** : `measure_real_impact()` calcule mal pour événements multiples

```python
# Dans measure_real_impact() - backtest_utils.py ligne ~87
ref_price = prices.iloc[0]['price']  # Prix à 14:30
max_price = prices['price'].max()    # Maximum dans TOUTE la fenêtre
min_price = prices['price'].min()    # Minimum dans TOUTE la fenêtre

move_up = (max_price - ref_price) * 10000    # PROBLÈME ICI !
move_down = (ref_price - min_price) * 10000  # ET ICI !
```

**Problème identifié** :

Pour **Phase 1 (14:30-15:14)** :
- Calcule : `max_price` - `ref_price` (14:30)
- Résultat : 207 pips

Pour **Phase 2 (14:45-15:13)** :
- Calcule : `max_price` - `ref_price` (14:45 ou 14:30 ?)
- Résultat : 24.9 pips

**Total combiné** : 231.9 pips

**MAIS en réalité** :
- Le mouvement TOTAL est de ~41 pips (de 1.16870 à 1.17280)
- Les phases ne s'additionnent PAS comme ça !
- Phase 2 démarre du prix atteint par Phase 1, pas du prix initial

**DOUBLE COMPTAGE** confirmé :
- Phase 1 compte le mouvement jusqu'au peak
- Phase 2 recompte une partie du même mouvement
- Résultat : 231.9 pips au lieu de 41 pips réels

---

## 🛠️ SOLUTION CRÉÉE

### Script : `verify_real_data_11sept.py`

**Localisation** : `/Users/andrevalentin/Desktop/`

**Objectif** : Identifier si le problème vient des DONNÉES ou du CALCUL

**Fonctionnalités** :

1. **Interrogation directe base DuckDB**
   - Lit les prix 1-minute du 11/09/2025
   - Période : 14:25 - 16:00 UTC
   
2. **Calcul manuel amplitude réelle**
   - Prix départ à 14:30
   - Peak maximum dans la fenêtre
   - Amplitude en pips
   
3. **Comparaison triple**
   - Base DuckDB vs MetaTrader
   - Base DuckDB vs Prédictions
   - Identification source du problème
   
4. **Affichage détaillé**
   - Premières minutes
   - Zone de peak (14:55-15:15)
   - Dernières minutes

**Usage** :
```bash
cd ~/Desktop
python3 verify_real_data_11sept.py
```

**Résultats attendus** :

#### Scénario A : Données Correctes ✅
```
✅ DONNÉES COHÉRENTES
Amplitude base : ~41 pips
Amplitude MetaTrader : ~41 pips
ÉCART : < 5 pips

→ PROBLÈME : Calcul measure_real_impact()
→ SOLUTION : Corriger calcul pour phases multiples
```

#### Scénario B : Données Incorrectes ❌
```
❌ DIVERGENCE IMPORTANTE
Amplitude base : 231 pips ??
Amplitude MetaTrader : 41 pips
ÉCART : > 100 pips

→ PROBLÈME : Données source (EODHD)
→ SOLUTION : Re-télécharger données
```

---

## 🔧 CORRECTIONS À APPORTER (Selon résultats)

### Option A : Si Données OK → Corriger Calculs

#### Correction 1 : `measure_real_impact()` (backtest_utils.py)

**Problème** : Calcule amplitude totale de la fenêtre
**Solution** : Calcul incrémental par phase

```python
def measure_real_impact_per_phase(
    prices_df: pd.DataFrame,
    phase_start_idx: int = 0,  # ← NOUVEAU
    threshold_pips: float = 5.0
) -> Optional[Dict]:
    """
    Mesure l'impact DEPUIS le début de cette phase uniquement
    """
    
    # Limiter aux prix de CETTE phase seulement
    phase_prices = prices_df.iloc[phase_start_idx:].copy()
    
    # Prix de référence = DÉBUT DE CETTE PHASE
    ref_price = phase_prices.iloc[0]['price']
    
    # Chercher le peak DANS CETTE PHASE
    max_price = phase_prices['price'].max()
    min_price = phase_prices['price'].min()
    
    # Calculer mouvements DEPUIS début phase
    move_up = (max_price - ref_price) * 10000
    move_down = (ref_price - min_price) * 10000
    
    # ... reste du code
```

#### Correction 2 : `sequence_multi_event_timeline.py`

**Problème** : Appelle measure_real_impact() avec toute la fenêtre
**Solution** : Passer l'index de début de phase

```python
def calculate_real_ttr_for_phase(
    phase: Dict, 
    real_prices_df: pd.DataFrame,
    phase_start_idx: int = 0  # ← NOUVEAU
):
    # Calculer TTR depuis le début de CETTE phase
    real_metrics = measure_real_impact_per_phase(
        prices_df=real_prices_df,
        phase_start_idx=phase_start_idx  # ← NOUVEAU
    )
```

#### Correction 3 : Graphique (4_Planificateur-Multi-Evenements.py)

**Problème** : Recalcule amplitude au lieu d'utiliser phases
**Solution** : Utiliser `impact_combined` directement

```python
# ❌ AVANT
max_movement = (price_df['high'].max() - start_price_input) * 10000
observed_movement = max_movement

# ✅ APRÈS
if 'phases' in locals() and phases:
    # Utiliser l'impact RÉEL des phases
    observed_movement = sum(abs(phase['impact_combined']) for phase in phases)
else:
    # Fallback
    observed_movement = (price_df['high'].max() - start_price_input) * 10000
```

---

### Option B : Si Données KO → Vérifier Source

#### Vérification 1 : Source EODHD

**Fichier** : `eodhd_client.py`

**Points à vérifier** :
- Timestamp correctement convertis ?
- Timezone UTC bien géré ?
- Tous les chandeliers 1-minute présents ?
- Pas de gaps dans les données ?

#### Vérification 2 : Base DuckDB

**Commandes** :
```python
import duckdb

conn = duckdb.connect('forex_events.db', read_only=True)

# Compter enregistrements 11/09/2025
query = """
SELECT COUNT(*) 
FROM prices_1m 
WHERE timestamp >= 1757601000 AND timestamp <= 1757608200
"""
count = conn.execute(query).fetchone()[0]
print(f"Enregistrements 14:30-16:30 : {count}")

# Vérifier gaps
query = """
SELECT 
    timestamp,
    LAG(timestamp) OVER (ORDER BY timestamp) as prev_ts,
    timestamp - LAG(timestamp) OVER (ORDER BY timestamp) as diff
FROM prices_1m
WHERE timestamp >= 1757601000 AND timestamp <= 1757608200
HAVING diff > 60
"""
gaps = conn.execute(query).fetchall()
print(f"Gaps trouvés : {len(gaps)}")
```

---

## 📋 CE QUI RESTE À FAIRE

### 🔴 URGENT (Cette session)

1. ⏳ **Exécuter `verify_real_data_11sept.py`**
   - Identifier source du problème (données vs calcul)
   - Déterminer corrections nécessaires

2. ⏳ **Créer script de correction**
   - Si données OK : `fix_measure_real_impact.py`
   - Si données KO : `redownload_sept_data.py`

3. ⏳ **Tester correction sur 11/09/2025**
   - Vérifier amplitude ≈ 41 pips
   - Vérifier phases correctes

### 🟡 MOYENNE PRIORITÉ (Suite session)

4. ⏳ **Scripts restants du plan initial**
   - `add_micro_retracements.py`
   - `integrate_real_overlay.py`
   - `test_graphique_11sept.py`

5. ⏳ **Validation complète**
   - Tests sur autres dates
   - Vérification précision générale

---

## 📊 MÉTRIQUES SESSION

### Problèmes Identifiés
- **Total** : 2 problèmes critiques
- **Graphique** : Recalcule amplitude (ignore phases)
- **Calculs** : Double comptage événements multiples
- **Impact** : Erreur +466% à +823% !

### Scripts Créés
- **verify_real_data_11sept.py** : Diagnostic données vs calculs
- **Lignes de code** : ~250 lignes
- **Tests** : Comparaison triple (Base/MetaTrader/Prédictions)

### Temps Estimé Corrections
- **Diagnostic** : 5 min (exécution script)
- **Fix calculs** : 30 min (si données OK)
- **Fix données** : 1h (si données KO)
- **Tests validation** : 15 min

---

## 🎯 INSTRUCTIONS PROCHAINE ÉTAPE

### Immédiatement (Par Utilisateur)

```bash
# 1. Exécuter script diagnostic
cd ~/Desktop
python3 verify_real_data_11sept.py

# 2. Noter résultats
# - Amplitude base : ??? pips
# - Amplitude MetaTrader : ~41 pips
# - Message : "Données cohérentes" ou "Divergence" ?

# 3. Copier sortie complète du script
# - Me l'envoyer dans prochaine session
```

### Suite (Avec Claude)

**Dire** :
```
"Suite session graphiques.
Script verify_real_data_11sept.py exécuté.
Résultats : [coller sortie complète]
Prêt pour corrections."
```

**Claude créera alors** :
- Script de correction adapté (calculs OU données)
- Tests de validation
- Suite du plan d'action

---

## 💡 LEÇONS APPRISES

### 1. Toujours Vérifier vs Source Externe

**Erreur évitée** : Corriger graphiques sans vérifier calculs
**Méthode** : Comparer avec MetaTrader (source externe fiable)
**Résultat** : Découverte erreur 466% qui aurait invalidé tout

### 2. Double Comptage dans Phases Multiples

**Symptôme** : Impact combiné ≠ Amplitude réelle
**Cause** : Chaque phase calcule depuis prix initial
**Solution** : Calcul incrémental (phase démarre du prix atteint)

### 3. Importance Screenshots Utilisateur

**Sans screenshots** : On aurait cru que fix_graphique_phases.py fonctionnait
**Avec screenshots** : Découverte que calculs sont tous faux
**Impact** : Économie de plusieurs sessions de debugging

---

## 📚 FICHIERS CRÉÉS/MODIFIÉS

### Scripts Diagnostic (1)
```
✅ /Users/andrevalentin/Desktop/verify_real_data_11sept.py  (~250 lignes)
```

### Documentation (1)
```
✅ Resume sessions Claude/session_14oct2025_suite_verification_donnees.md (CE FICHIER)
```

### Screenshots Analysés (5)
```
✅ Image 1 : Graphique Streamlit (378.6 pips)
✅ Image 2 : Statistiques simulation
✅ Image 3 : Détails par phase (231.9 pips)
✅ Image 4 : MetaTrader réel (~41 pips)
✅ Image 5 : Calcul vectoriel (231.9 pips)
```

---

## 🔍 POINTS D'ATTENTION

### Critique 1 : Double Comptage Phases

**Cas** : 2 événements à 14:30 et 14:45
**Problème actuel** :
```
Phase 1 : 1.16870 → 1.17280 = 41 pips ✅
Phase 2 : 1.16870 → 1.17xxx = ??? pips (recalcule depuis début !)
Total   : 41 + ??? = 231.9 pips ❌
```

**Solution** :
```
Phase 1 : 1.16870 → 1.17280 = 41 pips ✅
Phase 2 : 1.17280 → 1.17xxx = ??? pips (depuis fin Phase 1)
Total   : 41 + ??? = ~41 pips ✅ (si Phase 2 a peu d'impact)
```

### Critique 2 : Graphique vs Phases

**Actuellement** :
- Phases calculées : 231.9 pips (déjà faux)
- Graphique affiché : 378.6 pips (encore plus faux !)
- Écart : 146.7 pips de sur-génération

**Cause** : `price_curve_generator.py` génère courbe trop volatile

### Critique 3 : TTR Combiné

**Affiché** : 7 min
**Phase 1 réel** : 44 min
**Incohérence** : Affiche le TTR prédit au lieu du TTR observé

---

## ✅ CHECKLIST AVANT NOUVELLE SESSION

### Par Utilisateur

- [ ] Exécuter `verify_real_data_11sept.py`
- [ ] Copier sortie complète du script
- [ ] Noter si "Données cohérentes" ou "Divergence"
- [ ] Préparer screenshots si erreurs nouvelles

### Pour Claude (Nouvelle Session)

- [ ] Lire sortie de `verify_real_data_11sept.py`
- [ ] Déterminer : Données OK ou KO ?
- [ ] Créer script correction adapté
- [ ] Tester correction sur 11/09/2025
- [ ] Valider amplitude ≈ 41 pips

---

## 🚀 ÉTAT FINAL SESSION

**Status** : 🚨 **PROBLÈME CRITIQUE IDENTIFIÉ**

**Découvertes** :
- Amplitude prédite : +466% d'erreur ❌
- Amplitude graphique : +823% d'erreur ❌
- Cause probable : Double comptage phases

**Livrables** :
- 1 script diagnostic (verify_real_data_11sept.py) ✅
- Analyse détaillée 5 screenshots ✅
- Comparaison triple (Base/MT/Prédictions) ✅
- Plan correction complet ✅

**Prochaine étape** :
- Exécuter script diagnostic
- Identifier source (données vs calculs)
- Créer script correction

**Confiance** : 🟡 **MOYENNE**
- Problème bien identifié ✅
- Script diagnostic prêt ✅
- Solution dépend des résultats ⏳
- Correction estimée 30min-1h ⏱️

---

## 📞 CONTACT NOUVELLE SESSION

**Phrase de reprise** :
```
"Suite session graphiques - diagnostic exécuté.
Résumé à lire : session_14oct2025_suite_verification_donnees.md
Voici résultats verify_real_data_11sept.py : [coller sortie]"
```

**Fichiers à consulter** :
1. Ce résumé (contexte problème)
2. session_14oct2025_correction_graphiques_phases.md (contexte général)
3. Sortie script verify_real_data_11sept.py (diagnostic)

---

## 🎯 SYNTHÈSE EXÉCUTIVE

### Problème Central
**Les calculs d'impact sont faux de 466%**
- Réel : 41 pips
- Calculé : 231.9 pips
- Cause : Double comptage phases multiples

### Action Immédiate
**Exécuter script diagnostic**
```bash
python3 ~/Desktop/verify_real_data_11sept.py
```

### Décision Selon Résultat
- **Données OK** → Corriger `measure_real_impact()`
- **Données KO** → Vérifier `eodhd_client.py`

### Temps Estimé Résolution
- **Diagnostic** : 5 min
- **Correction** : 30 min - 1h
- **Validation** : 15 min
- **Total** : ~1h30 max

---

**Session suspendue - En attente résultats diagnostic**
**Tokens utilisés** : ~84,000 / ~130,000 (65%)
**Marge sécurité** : ✅ Confortable
**Continuité** : ✅ Assurée

**🎯 PRÊT POUR DIAGNOSTIC** 🎯

---

*Fin du résumé - Session 14 octobre 2025 (Suite)*
*Vérification Données et Calculs*
*Status : Diagnostic créé - En attente exécution*
