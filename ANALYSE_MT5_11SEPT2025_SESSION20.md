# 📊 ANALYSE GRAPHIQUES MT5 - 11 SEPTEMBRE 2025

**Date :** 19 octobre 2025  
**Session :** 20  
**Cas d'étude :** 11 septembre 2025 14:30 (CPI US + événements)

---

## 🎯 VUE D'ENSEMBLE DES 6 GRAPHIQUES

### Graphique 1 : Vue large (14:05 → 16:29)
**Timeframe :** M1  
**Prix départ (14:30)** : ~1.16522  
**Prix maximum atteint** : ~1.17410 (vers 14:45-15:00)  
**Mouvement total** : **+888 pips** (1.16522 → 1.17410)

### Graphique 2 : Zoom impact initial (13:53 → 15:53)
**Focus :** Phase d'impact principal  
**Observation :** Montée quasi-verticale à 14:30 puis consolidation

### Graphique 3 : Détail phase impact (13:05 → 16:29)
**Focus :** Séquence complète impact + consolidation  
**Prix maximum** : 1.17044 visible

### Graphique 4 : Zoom serré (13:17 → 16:05)
**Focus :** Détails des bougies individuelles  
**Observation :** Volatilité élevée après 14:30

### Graphique 5 : Vue moyenne (13:29 → 16:29)
**Focus :** Contexte avant/après événement  
**Prix pré-event** : ~1.16810

### Graphique 6 : Vue très large (14:05 → 16:29, ZOOM OUT)
**Focus :** Contexte marché global  
**Observation :** Trend haussier général sur la période

---

## 📐 MESURES PRÉCISES DEPUIS LES GRAPHIQUES

### Phase 1 : Impact initial (14:30:00 → ~14:35:00)

**Prix départ** : 1.16522 (juste avant 14:30)  
**Prix pic initial** : ~1.17044 (graphique 3)  
**Mouvement Phase 1** : **522 pips** (1.16522 → 1.17044)  
**Durée** : ~5 minutes  
**Latence** : < 30 secondes (montée quasi-immédiate)

### Phase de consolidation / Pullback (14:35 → 14:45)

**Prix après Phase 1** : ~1.17044  
**Prix minimum pullback** : ~1.16930 (visible graphique 2)  
**Pullback** : **-114 pips** (1.17044 → 1.16930)  
**Durée** : ~10 minutes  
**Ratio pullback** : 114 / 522 = **21.8%** de la Phase 1

### Phase 2 : Continuation haussière (14:45 → 15:00)

**Prix départ Phase 2** : ~1.16930  
**Prix maximum atteint** : ~1.17410 (graphique 1)  
**Mouvement Phase 2** : **480 pips** (1.16930 → 1.17410)  
**Durée** : ~15 minutes

### Vue globale événement complet

**Prix pré-événement** : 1.16522 (14:29:59)  
**Prix maximum total** : 1.17410 (14:45-15:00)  
**Mouvement TOTAL** : **888 pips**  
**Durée totale impact** : ~30 minutes (14:30 → 15:00)

---

## 🔬 COMPARAISON AVEC PRÉDICTIONS ACTUELLES

### Ce que le système prédit actuellement (V2)

**Phase 1 (14:30) :**
- Impact prédit : +207 pips
- Réel observé : +522 pips
- **Erreur** : -315 pips (**-60% d'erreur !**)

**Pullback (14:35 → 14:45) :**
- Formule actuelle : `phase1_impact × 0.06 × 10 min = 207 × 0.6 = 124 pips`
- Plafond 60% : `207 × 0.60 = 124 pips`
- Prédit : -124 pips
- Réel observé : -114 pips
- **Erreur** : +10 pips (**+9% d'erreur** - TRÈS BON !)

**Phase 2 (14:45) :**
- Impact prédit : +16.4 pips
- Réel observé : +480 pips (!)
- **Erreur** : -463 pips (**-96% d'erreur !**)

### Analyse des écarts

#### ✅ Pullback : Formule CORRECTE
La formule pullback fonctionne remarquablement bien :
- Prédiction : -124 pips
- Réel : -114 pips
- Écart : 9% seulement !

**Conclusion** : Formule pullback validée ✅

#### ❌ Phase 1 : SOUS-ESTIMATION MAJEURE
La formule V2 sous-estime massivement :
- Prédit : +207 pips
- Réel : +522 pips
- Ratio : **2.52×** plus élevé que prévu

**Hypothèses :**
1. La surprise réelle (33% sur Inflation MoM) n'est pas assez amplifiée
2. Plafond 2.5× est trop conservateur pour surprises extrêmes
3. Multi-événements (CPI + Core CPI + autres) crée synergie plus forte que 1.05×

#### ❌ Phase 2 : SOUS-ESTIMATION EXTRÊME
- Prédit : +16.4 pips
- Réel : +480 pips
- Ratio : **29×** plus élevé que prévu !

**Hypothèses :**
1. Phase 2 n'est PAS un nouvel événement isolé
2. C'est la CONTINUATION du mouvement Phase 1 après pullback
3. Le système traite Phase 2 comme événement faible (14:45) alors que c'est momentum Phase 1

---

## 🎯 INSIGHTS CRITIQUES POUR SESSION 20

### 1. Le mouvement TOTAL est bien plus élevé que prévu

**Observation :**
- Système prédit : 207 + (-124) + 16.4 = **~99 pips net**
- Réel observé : **+888 pips** (prix 1.16522 → 1.17410)
- Écart : **×8.9** plus élevé !

**Explication possible :**
- Le mouvement à 14:30 déclenche un trend fort
- Les 480 pips Phase 2 ne sont PAS dus à l'événement 14:45
- C'est le MOMENTUM du CPI 14:30 qui continue

### 2. La latence est quasi-nulle

**Observation graphiques :**
- Montée IMMÉDIATE à 14:30:00
- Pas de période de "hésitation"
- Latence < 30 secondes

**Formule actuelle :**
```python
latency = 0.5 + (score/100) × 1.5  # 0.5-2 min
```

**Conclusion :** Formule latency semble correcte (0.5-1 min pour score élevé)

### 3. Le TTR (Time To Return) est incorrect

**TTR = Temps pour atteindre le maximum**

**Observation :**
- Phase 1 atteint pic à ~14:35 → **TTR ~5 minutes** ✅
- Maximum absolu atteint à 14:45-15:00 → **TTR ~15-30 minutes** ⚠️

**Formule actuelle :**
```python
ttr = 3 + (score/100) × 5  # 3-8 min
```

**Conclusion :** TTR sous-estimé pour événements à fort momentum

### 4. Le pullback est très bien modélisé

**Observation :**
- Prédit : -124 pips
- Réel : -114 pips
- Écart : 9% seulement

**Formule pullback validée** : ✅
```python
pullback = phase1_impact × 0.06 × minutes_between
pullback = min(pullback, phase1_impact × 0.60)
```

---

## 🔧 RECOMMANDATIONS POUR AMÉLIORATION

### Recommandation 1 : Re-calibrer amplification surprise

**Problème :** Plafond 2.5× trop conservateur

**Formule V2 actuelle :**
```python
if surprise < 15%:
    amp = 1.0 + (surprise - 5%) × 0.15  # Max 2.5×
else:
    amp = 2.5  # PLAFOND
```

**Proposition V3 :**
```python
if surprise < 15%:
    amp = 1.0 + (surprise - 5%) × 0.15
elif surprise < 30%:
    amp = 2.5 + (surprise - 15%) × 0.10  # Continue jusqu'à 4.0×
else:
    amp = 4.0  # NOUVEAU PLAFOND
```

**Impact attendu :**
- Surprise 33% → amp 4.0× (vs 2.5× actuel)
- Impact prédit : 207 × (4.0/2.5) = **331 pips** (vs 522 réel = -37% erreur au lieu de -60%)

### Recommandation 2 : Détecter momentum fort

**Problème :** Phase 2 (480 pips) n'est pas détectée comme continuation

**Proposition :**
- Si mouvement Phase 1 > 400 pips → marquer comme "momentum fort"
- Phase suivante (même sans événement majeur) : prédire continuation
- Formule : `phase2_predicted = phase1_impact × 0.80 × (1 - pullback_ratio)`

**Impact attendu :**
- Phase 1 : 522 pips
- Pullback : -114 pips (21.8%)
- Phase 2 prédit : 522 × 0.80 × (1-0.218) = **326 pips** (vs 480 réel = -32% erreur)

### Recommandation 3 : Ajuster TTR dynamiquement

**Problème :** TTR fixe 3-8 min ne capte pas mouvements prolongés

**Proposition :**
```python
# TTR pour atteindre 80% du mouvement
ttr_80pct = 3 + (score/100) × 5  # Actuel

# TTR pour maximum absolu (si momentum fort)
if impact_predicted > 400:
    ttr_max = ttr_80pct × 3  # Triple pour mouvements forts
else:
    ttr_max = ttr_80pct × 1.5
```

---

## 📊 TABLEAU RÉCAPITULATIF

| Métrique | Prédit V2 | Réel MT5 | Écart | Verdict |
|----------|-----------|----------|-------|---------|
| **Phase 1 Impact** | 207 pips | 522 pips | -60% | ❌ SOUS-ESTIMÉ |
| **Latence** | 0.5-1 min | <0.5 min | OK | ✅ CORRECT |
| **TTR Phase 1** | 5-8 min | ~5 min | OK | ✅ CORRECT |
| **Pullback** | -124 pips | -114 pips | +9% | ✅ TRÈS BON |
| **Phase 2 Impact** | 16 pips | 480 pips | -96% | ❌ SOUS-ESTIMÉ |
| **TTR Total** | 8 min | 30 min | -73% | ❌ SOUS-ESTIMÉ |
| **Mouvement TOTAL** | 99 pips | 888 pips | -89% | ❌ SOUS-ESTIMÉ |

---

## 🎯 PRIORITÉS POUR SESSION 20

### PRIORITÉ 1 : Valider formule impact avec données propres
- Re-mesurer V2 sur TOUS les groupes
- Voir si le problème est généralisé ou spécifique au 11 sept

### PRIORITÉ 2 : Analyser événements à surprises élevées (>20%)
- Combien d'événements avec surprise >20% dans la DB ?
- Leur impact réel vs prédit V2
- Calibrer nouveau plafond amplification

### PRIORITÉ 3 : Étudier momentum/continuation
- Détecter quand Phase 2 = continuation Phase 1
- Proposer formule de prédiction continuation

### OPTIONNEL : Analyser latence/TTR réels
- Calculer depuis prices_1m pour échantillon événements
- Valider formules actuelles

---

## 📝 NOTES TECHNIQUES

### Lecture précise des niveaux de prix

**Graphique 1 (le plus clair) :**
- Prix pré-event : 1.16522 (zone SELL_3)
- Prix post-event : 1.17410 (zone SELL_1)
- Échelle droite visible : confirme les niveaux

**Confirmation graphique 3 :**
- Prix maximum Phase 1 : 1.17044
- Pullback minimum : ~1.16930

**Méthodologie :**
- Lecture depuis l'échelle de prix (droite)
- Confirmation croisée entre les 6 graphiques
- Marges d'erreur : ±10 pips

---

**FIN DE L'ANALYSE GRAPHIQUES MT5**

**Date :** 19 octobre 2025  
**Session :** 20  
**Auteur :** Claude & André  
**Tokens utilisés :** ~77K / 190K (40.5%)  
**Importance :** ⭐⭐⭐ CRITIQUE pour calibration formules
