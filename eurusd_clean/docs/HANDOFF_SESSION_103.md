# 🔄 HANDOFF SESSION 102 → 103

**Date :** 30 octobre 2025  
**Session 102 :** Calibration formule amplification avec détection tendance  
**Session 103 :** Debug & finalisation détection tendance + intégration formule

---

## 🔬 HYPOTHÈSES À VÉRIFIER SESSION 103

### Vue d'Ensemble du Problème

**Observation :** Évolution amplitude avec window croissant
```
window=20  (20 min)  → amplitude = 8.1 pips
window=120 (2h)      → amplitude = 5.1 pips
window=240 (4h)      → amplitude = 0.0 pips (❌)

Cible réelle (MT5) : ~83 pips
```

**Paradoxe :** Plus le window est large, PIRE c'est !

**Conclusion :** Le problème n'est PAS la détection extremum, c'est le CALCUL d'amplitude.

---

### HYPOTHeÈSE #1 : Prix Revenu au Niveau Initial

**Énoncé :**
```
Le calcul actuel mesure abs(price_end - price_start).

Si extremum détecté = pic à 1.1770
Et prix avant événement revenu à ~1.1770
→ Différence = 0 pips

MAIS le marché a oscillé 1.1770 → 1.1687 → 1.1770
→ Amplitude VRAIE = 83 pips (max-min)
```

**Test :**
```python
# Debug cas 11.09.2025
print(f"Prix début (extremum) : {prices[start_idx]}")
print(f"Prix fin (événement)  : {prices[end_idx]}")
print(f"Max segment          : {prices[start_idx:end_idx+1].max()}")
print(f"Min segment          : {prices[start_idx:end_idx+1].min()}")
print(f"Amplitude end-start  : {abs(prices[end_idx] - prices[start_idx]) * 10000}")
print(f"Amplitude max-min    : {(max - min) * 10000}")
```

**Critère validation :**
- Si `abs(price_end - price_start) < 5 pips` ET `(max - min) > 70 pips`
- → HYPOTHeÈSE CONFIRMÉE

**Action si confirmée :**
→ Passer à l'implémentation SOLUTION #1 (max-min)

---

### HYPOTHeÈSE #2 : Mauvais Extremum Détecté

**Énoncé :**
```
L'algorithme détecte un extremum qui n'est PAS
le pic principal du 9 sept 08:00.

Peut-être un petit pic/creux plus récent
qui donne amplitude faible.
```

**Test :**
```python
# Debug cas 11.09.2025
print(f"Extremum type        : {trend_info['extremum_type']}")
print(f"Extremum index       : {trend_info['start_idx']}")
print(f"Extremum timestamp   : {timestamps[start_idx]}")
print(f"Extremum prix        : {prices[start_idx]}")

# Comparer avec cible
print(f"\nCible MT5 :")
print(f"  Date : 9 sept 2025, 08:00")
print(f"  Prix : ~1.1770")
```

**Critère validation :**
- Si extremum timestamp ≠ 9 sept 08:00 (±2h)
- OU extremum prix ≠ 1.1770 (±50 pips)
- → HYPOTHeÈSE CONFIRMÉE

**Action si confirmée :**
→ Tester window=360 (6h) ou 480 (8h)
→ OU créer dataset gold standard manuel

---

### HYPOTHeÈSE #3 : Segment Trop Long, Extremum Obsolète

**Énoncé :**
```
Avec window=240 (4h), l'algorithme trouve un extremum
très loin dans le temps (> 48h avant événement).

Ce vieil extremum n'est plus pertinent pour
la tendance récente avant l'événement.
```

**Test :**
```python
# Vérifier durée segment
duree_segment = trend_info['duration_hours']

print(f"Durée segment : {duree_segment:.1f}h")
print(f"Trop long ?   : {'OUI' if duree_segment > 60 else 'NON'}")
```

**Critère validation :**
- Si durée > 60h (> 72h disponibles impossible)
- OU si extremum > 60h avant événement
- → HYPOTHeÈSE CONFIRMÉE

**Action si confirmée :**
→ Limiter durée max segment à 48-54h
→ Ignorer extrema trop anciens

---

### SOLUTION #1 : Calcul Amplitude Max-Min (PRIORITAIRE)

**Implémentation :**

```python
# Dans detect_trend_extremum.py, ligne ~150

# AVANT (actuel - FAUX)
amplitude_pips = abs(price_end - price_start) * 10000

# APReÈS (max-min - CORRECT)
segment_prices = prices[start_idx:end_idx + 1]
amplitude_pips = (segment_prices.max() - segment_prices.min()) * 10000
```

**Justification :**
- Capture VRAIE amplitude du mouvement
- Insensible aux retours au niveau initial
- Standard en analyse technique

**Test validation :**
```python
# Après modification, relancer calibration
./run_calibration.sh

# Vérifier cas 11.09 :
# - Amplitude attendue : 70-90 pips
# - Durée attendue : 40-55h
# - R² attendu : 0.6-0.8
```

**Critères succès SOLUTION #1 :**

**✅✅ SUCCeÈS TOTAL** si :
- Amplitude cas 11.09 : 70-90 pips
- Durée cas 11.09 : 45-55h
- Amplitude moyenne (44 dates) : 60-80 pips
- Formule gagnante : coefficient dynamique ≠ 0
- Amélioration > 35%

**✅ SUCCeÈS PARTIEL** si :
- Amplitude cas 11.09 : 40-70 pips (mieux mais pas parfait)
- Amplitude moyenne : 40-60 pips
- Amélioration > 25%

**❌ ÉCHEC** si :
- Amplitude cas 11.09 : < 40 pips (toujours sous-estimé)
- Aucune amélioration vs baseline

---

### SOLUTION #2 : Limiter Durée Max Segment (SECONDAIRE)

**Si SOLUTION #1 donne durée > 60h ou extrema obsolètes**

**Implémentation :**

```python
# Dans detect_trend_extremum.py, fonction find_last_major_extremum

# Filtrer extrema trop anciens
max_hours_back = 54  # Max 54h avant événement
min_idx = len(prices) - (max_hours_back * 60)  # Convertir en minutes

# Ne garder que extrema récents
extremum = find_last_major_extremum(prices, timestamps, window_swing)
if extremum['index'] < min_idx:
    # Extremum trop ancien, prendre le plus récent acceptable
    extremum = find_most_recent_acceptable_extremum(prices, min_idx)
```

---

### SOLUTION #3 : Dataset Gold Standard Manuel (FALLBACK)

**Si SOLUTIONS #1 et #2 échouent**

**Méthode :**

1. Sélectionner 10 dates clés avec clusters HIGH
2. Pour chaque date, regarder graphique MT5
3. Noter manuellement :
   - Date/heure extremum principal
   - Prix extremum
   - Date/heure événement
   - Prix événement
   - Amplitude réelle (max-min)

4. Créer fichier gold_standard.csv
5. Valider algorithme contre ce dataset
6. Ajuster paramètres jusqu'à 100% match

**Exemple gold_standard.csv :**
```csv
date,extremum_datetime,extremum_prix,event_datetime,event_prix,amplitude_pips,type
2025-09-11,2025-09-09 08:00:00,1.1770,2025-09-11 14:30:00,1.1687,83.0,HIGH
2025-08-14,2025-08-12 14:00:00,1.1650,2025-08-14 14:30:00,1.1590,60.0,HIGH
...
```

---

## 🎯 ARBRE DÉCISION SESSION 103

```
START
  ↓
ÉTAPE B: Debug cas 11.09
  ↓
  Vérifier HYPOTHeÈSE #1 (prix revenu niveau initial)
  │
  ├─ SI CONFIRMÉE → SOLUTION #1 (max-min)
  │   │
  │   ├─ Test réussi? → VALIDATION (✅✅ FIN)
  │   └─ Test échoué? → Vérifier HYPOTHeÈSE #2
  │
  └─ SI RÉFUTÉE → Vérifier HYPOTHeÈSE #2
      │
      Vérifier HYPOTHeÈSE #2 (mauvais extremum)
      │
      ├─ SI CONFIRMÉE → Tester window 360/480
      │   │
      │   ├─ Réussi? → SOLUTION #1 + nouveau window
      │   └─ Échoué? → SOLUTION #3 (gold standard)
      │
      └─ SI RÉFUTÉE → Vérifier HYPOTHeÈSE #3
          │
          Vérifier HYPOTHeÈSE #3 (segment trop long)
          │
          ├─ SI CONFIRMÉE → SOLUTION #2 (limiter durée)
          │   └─ Puis SOLUTION #1
          │
          └─ SI TOUTES RÉFUTÉES → SOLUTION #3 (gold standard)
```

---

## 📄 CRITÈRES DÉCISION FINALE

### ✅✅ FORMULE DYNAMIC VALIDÉE

**Conditions TOUTES remplies :**
1. Amplitude cas 11.09 : 70-90 pips (±15% de 83)
2. Durée cas 11.09 : 45-55h (±20% de 54h)
3. Amplitude moyenne : 60-80 pips
4. Formule coefficient ≠ 0 (relation dynamique)
5. Amélioration > 30% vs baseline
6. Corrélation > 0.3 OU coefficient significatif

**Action :** Intégrer formule dans Planificateur V2.7

---

### ⚠️ VALIDATION PARTIELLE

**Conditions :**
1. Amélioration 20-30% vs baseline
2. Métriques imparfaites mais meilleures
3. Coefficient ≈ 0 MAIS constante optimisée

**Action :** Utiliser amp constant optimisé (1.2 au lieu de 2.5)

---

### ❌ FORMULE REJETÉE

**Conditions :**
1. Métriques toujours fausses (amplitude < 40 pips)
2. Aucune amélioration vs baseline
3. Impossible d'avoir métriques cohérentes

**Action :** 
- Documenter tentatives et échec
- Utiliser amp constant optimisé (1.2)
- Recommander axes alternatifs (VIX, spreads, momentum)

---

## 💎 RÉCAPITULATIF QUICK START SESSION 103

### PRIORITÉ #1 : Debug + Test SOLUTION #1 (30 min)

```bash
# 1. Créer script debug
cd ~/Desktop/.../session102
python3 create_debug_case_11_09.py  # À créer Session 103

# 2. Exécuter debug
python3 debug_case_11_09.py

# 3. Analyser résultats, confirmer HYPOTHeÈSE #1

# 4. Implémenter SOLUTION #1 (max-min)
vim detect_trend_extremum.py  # Modifier ligne ~150

# 5. Relancer calibration
./run_calibration.sh

# 6. Vérifier amélioration
```

### Si SOLUTION #1 Réussit : FIN (✅✅)

### Si SOLUTION #1 Échoue : Suivre Arbre Décision

---

## 🎯 OBJECTIF SESSION 103

**Finaliser et valider la formule d'amplification dynamique basée sur tendance 72h**

**Plan d'action :**
1. ✅ Résultats test window=240 (4h)
2. 🔍 Debug cas 11.09.2025 si nécessaire
3. 🔧 Test calcul amplitude alternatif (max-min vs end-start)
4. ✅ Décision finale : valider ou rejeter hypothèse
5. 📦 Intégration dans Planificateur V2.7 si validé

---

## 📊 ÉTAT ACTUEL (Fin Session 102)

### Tests Window Swing

**window=20 (20 min) :**
- Durée moyenne : 7.6h ❌
- Amplitude moyenne : 15.4 pips ❌
- Cas 11.09 : 0.8h, 8.1 pips ❌

**window=120 (2h) :**
- Durée moyenne : 12.3h 🟡
- Amplitude moyenne : 22.7 pips 🟡
- Cas 11.09 : 24.1h, 5.1 pips (R²=0.727 ✅) 🟡

**window=240 (4h) :** EN COURS DE TEST

### Résultats Calibration (window=120)

**Meilleure formule : F7 Inverse**
```python
amp = 0.000 / (R² + 0.1) + 1.196
# ≈ amp = 1.196 (constante)
```

**Métriques :**
- MAE : 0.713
- Amélioration : 39.1% vs baseline (2.5)
- Corrélation : -0.150 (quasi-nulle)

**⚠️ PROBLÈME :** Coefficient a≈0, pas de vraie relation dynamique

---

## 🔍 DIAGNOSTIC PROBLÈME

### Symptômes

1. **R² excellent (0.727)** mais **amplitude catastrophique (5 pips vs 83 attendu)**
2. **Toutes formules convergent vers constante** (coefficient dynamique ≈ 0)
3. **Corrélations nulles** (<0.2 pour toutes formules)

### Hypothèses

**H1 : Window encore trop court**
- Test : window=240 (4h)
- Si échec → window=360 (6h) ou méthode différente

**H2 : Extremum détecté n'est pas le principal**
- Besoin : Debug visualisation cas 11.09
- Voir exactement quel extremum est trouvé

**H3 : Calcul amplitude inadéquat**
- Actuel : `abs(price_end - price_start)` 
- Si prix oscille/revient, sous-estime
- Alternative : `max(segment) - min(segment)`

---

## 📁 FICHIERS CLÉS SESSION 102

```
eurusd_clean/scripts/session102/
├── detect_trend_extremum.py           # Fonction détection Swing High/Low
├── calibrate_amp_formula.py           # Script calibration (window=240)
├── test_extrema.sh                    # Tests unitaires
├── run_calibration.sh                 # Lancement calibration
├── analysis_real_data_complete.csv    # Données 44 dates
└── README_*.md                        # Documentations
```

---

## 🎯 TODO SESSION 103

### ÉTAPE 1 : Analyse Résultats window=240 ⏱️ 2 min

**André lance :**
```bash
cd ~/Desktop/.../session102
./run_calibration.sh
```

**Vérifier :**
- Durée cas 11.09 : ~50h ?
- Amplitude cas 11.09 : ~80 pips ?
- Coefficient formule ≠ 0 ?

**Si succès :** Passer ÉTAPE 4 (décision finale)  
**Si échec :** Continuer ÉTAPE 2

---

### ÉTAPE 2 : Debug Cas 11.09.2025 🔍 15 min

**Objectif :** Comprendre exactement ce qui est détecté

**Créer script :**
```python
# debug_case_11_09.py
# 1. Charger prix 72h avant 11.09.2025 14:30
# 2. Appliquer detect_trend_from_extremum avec window=240
# 3. Afficher :
#    - Extremum trouvé (type, index, heure, prix)
#    - Segment utilisé (début → fin)
#    - Prix début, prix fin, amplitude calculée
#    - Max-min sur segment vs end-start
# 4. Graphique ASCII des prix avec extremum marqué
```

**Comparer avec graphique MT5 :**
- Pic 9 sept 08:00 à ~1.1770
- Événement 11 sept 14:30 à ~1.1687
- Amplitude attendue : ~83 pips

---

### ÉTAPE 3 : Test Calcul Amplitude Alternatif 🔧 10 min

**Si debug montre que extremum correct mais amplitude fausse**

**Modifier `detect_trend_extremum.py` :**
```python
# ACTUEL (peut sous-estimer si oscillations)
amplitude_pips = abs(price_end - price_start) * 10000

# ALTERNATIF (capture vraie amplitude mouvement)
amplitude_pips = (prices[start_idx:end_idx+1].max() - 
                  prices[start_idx:end_idx+1].min()) * 10000
```

**Relancer calibration et comparer résultats**

---

### ÉTAPE 4 : Décision Finale ✅ 5 min

**Critères validation formule :**

**✅✅ VALIDÉE** si :
- MAE < baseline × 0.9 (amélioration > 10%)
- Corrélation > 0.5 OU coefficient dynamique significatif
- Métriques tendance cohérentes (durée ~50h, amplitude ~80 pips)

**⚠️ PARTIELLE** si :
- MAE < baseline mais critères incomplets
- Amélioration modeste (10-20%)

**❌ REJETÉE** si :
- MAE ≥ baseline
- OU amélioration = juste constante optimisée (coefficient ≈ 0)
- OU métriques tendance incohérentes

---

### ÉTAPE 5 : Intégration ou Conclusion 📦 30 min

**Si VALIDÉE :**

1. **Créer fonction finale :**
```python
# eurusd_clean/src/utils/amplification_dynamic.py
def calculate_amplification_dynamic(event_timestamp, conn):
    """
    Calcule amplification selon tendance 72h
    
    Returns:
        float: facteur amplification (0.5-5.0)
    """
    # 1. Charger prix 72h
    # 2. Détecter tendance extremum (window optimal)
    # 3. Appliquer formule validée
    # 4. Contrainte sécurité [0.5, 5.0]
```

2. **Intégrer Planificateur V2.7**
3. **Tests unitaires**
4. **Documentation**

**Si PARTIELLE :**
- Documenter formule avec réserves
- Recommander monitoring strict
- Intégration optionnelle

**Si REJETÉE :**
- Utiliser amp constant optimisé (1.2 au lieu de 2.5)
- Documenter tentatives et échec
- Recommandations axes alternatifs

---

## 📊 DONNÉES RÉFÉRENCE

### Cas 11.09.2025 (Ground Truth MT5)

```
Date événement  : 11 septembre 2025, 14:30 Bern
Pic identifié   : 9 septembre 2025, 08:00
Prix pic        : ~1.1770
Prix événement  : ~1.1687
Amplitude réelle: ~83 pips
Durée tendance  : ~54 heures
Direction       : DOWN (baissière)
Impact réel     : 57.1 pips
Amp parfaite    : 2.537
```

### Statistiques Attendues (44 dates)

```
Durée moyenne tendance     : 45-55h
Amplitude moyenne tendance : 70-90 pips
R² moyen                   : 0.6-0.7
Score force moyen          : 60-70/100
```

---

## 🧪 ALTERNATIVES SI TOUT ÉCHOUE

**Si même avec window=360 (6h) ça ne marche pas :**

### Alternative 1 : Dataset Gold Standard Manuel

**Créer référence manuelle pour 10 dates clés :**
- Regarder chaque graphique MT5
- Noter manuellement : extremum (date, heure, prix)
- Valider algorithme contre ce dataset
- Ajuster paramètres si nécessaire

### Alternative 2 : Méthode Fractals (Bill Williams)

```python
def detect_fractals(prices, n=5):
    """
    Fractal High: center > n voisins de chaque côté
    Fractal Low: center < n voisins de chaque côté
    """
    # Plus standard en trading
    # Peut être plus robuste
```

### Alternative 3 : Variables Marché Alternatives

**Au lieu de tendance pré-événement :**
- VIX / volatilité implicite
- Bid-Ask spreads
- Volume
- Momentum indicators (RSI, MACD)
- Sentiment indices

### Alternative 4 : Abandon Détection Automatique

**Accepter limitation :**
- Amp constant optimisé = 1.2
- Déjà 39% amélioration vs 2.5
- Focus sur autres axes (TTR, clustering)

---

## 💡 APPRENTISSAGES SESSION 102

### Ce Qui A Marché ✅

1. **Méthodologie rigoureuse** : Test unitaires avant calibration
2. **Correction itérative** : window 20→120→240
3. **Amélioration 39%** : Même avec formule constante
4. **Tests synthétiques validés** : Algo marche sur données propres

### Ce Qui N'A Pas Marché ❌

1. **Détection automatique extrema** : Sensible au bruit réel
2. **Calcul amplitude** : Sous-estimation systématique
3. **Relation dynamique** : Corrélations quasi-nulles
4. **Généralisation** : Tests unitaires ≠ vraies données

### Insights Importants 💡

1. **Données financières ≠ données synthétiques** : Bruit, gaps, microstructure
2. **Amplitude nécessite définition précise** : End-start vs max-min
3. **Window critique** : 20min trop court, 120min insuffisant, 240min à tester
4. **Constante optimisée déjà utile** : amp=1.2 > amp=2.5

---

## 🎯 SUCCESS CRITERIA SESSION 103

**Mission accomplie si :**

**Minimum (Acceptable) :**
- ✅ Décision claire : valider, rejeter, ou amp constant
- ✅ Métriques cas 11.09 comprises (même si imparfaites)
- ✅ Documentation complète des tentatives

**Optimal (Souhaité) :**
- ✅ Formule dynamique validée (coefficient ≠ 0, corr > 0.3)
- ✅ Métriques cohérentes (durée ~50h, amplitude ~80 pips)
- ✅ Intégration Planificateur V2.7
- ✅ Tests unitaires passent

**Exceptionnel (Bonus) :**
- ✅ Amélioration > 40% vs baseline
- ✅ Corrélation > 0.5
- ✅ Validation sur hold-out set

---

## 📞 HANDOFF COMPLET

**André, tu es prêt pour Session 103 avec :**

**Contexte :** ✅ (ce document)  
**Scripts :** ✅ (session102/ prêts)  
**Prochaine action :** ✅ (tester window=240)  
**Fallbacks :** ✅ (debug, amplitude, alternatives)

**Claude Session 103 devra :**
1. Analyser résultats window=240
2. Créer debug si nécessaire
3. Tester alternatives si échec
4. Décider et intégrer/conclure

---

**Tokens utilisés Session 102 :** ~130,000 / 190,000 (68%)  
**Marge Session 103 :** 190,000 tokens frais ✅

**Prêt pour la suite ! 🚀**
