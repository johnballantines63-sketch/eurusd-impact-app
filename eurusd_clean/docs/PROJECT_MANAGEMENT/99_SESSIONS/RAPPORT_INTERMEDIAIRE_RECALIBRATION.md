# 📊 RAPPORT INTERMÉDIAIRE - RECALIBRATION FORMULES V1.2

**Date :** 2025-01-XX  
**Statut :** 🔄 EN COURS  
**Objectif :** Recalibrer Impact/TTR/Pullback pour tous les patterns (Double Wave, Single Wave, ZigZag)

---

## ✅ CE QUI EST DÉJÀ FAIT

### 1. **Double Wave - Métriques Réelles Extraites** ✅

**Fichiers générés :**
- `scripts/session137/doublewave_real_metrics.csv` (160 cas détaillés)
- `scripts/session137/doublewave_real_metrics_summary.csv` (statistiques agrégées)

**Résultats clés :**

| Direction | N | Impact Médian (pips) | Phase 1 Time (min) | Phase 2 Time (min) | Pullback Ratio |
|-----------|---|---------------------|-------------------|-------------------|----------------|
| **UP** | 76 | 50.5 | 65.5 (Q1:52.75, Q3:70) | 93.0 (Q1:81.5, Q3:110.25) | ~40-50% |
| **DOWN** | 84 | 51.6 | 69.0 (Q1:55, Q3:70) | 89.5 (Q1:80, Q3:111.25) | ~40-50% |

**Découvertes critiques :**
- ❌ **Timeline théorique obsolète :** T+5 / T+11 / T+15 / T+40 ne correspondent PAS à la réalité
- ✅ **Timeline réelle :** Phase 1 pic à **~65-70 min**, Phase 2 pic à **~90-95 min**
- ✅ **Impact réel médian :** ~50-52 pips (vs prédictions actuelles souvent 3-4x supérieures)
- ✅ **Latence moyenne :** ~1-3 minutes entre annonce et début mouvement

**Colonnes extraites dans `doublewave_real_metrics.csv` :**
- `impact_pips` : Impact total réel
- `phase1_amp_pips`, `phase1_time_min` : Amplitude et durée Phase 1
- `pullback_amp_pips`, `pullback_time_min` : Amplitude et durée pullback
- `phase2_amp_pips`, `phase2_time_min` : Amplitude et durée Phase 2
- `dip_or_rise_ratio` : Ratio pullback/phase1
- `latency_minutes` : Délai entre annonce et début mouvement
- `event_family` : Type d'événement (CPI, NFP, etc.)

---

### 2. **Validation Ancienne Formule Impact D (V1)** ✅

**Fichier :** `scripts/session137/doublewave_formula_validation.csv`

**Résultats :**
- **MAE global :** ~160 pips (écart moyen)
- **Médiane erreur :** -110 pips (sous-estimation systématique)
- **Conclusion :** ❌ **Formule V1 obsolète** - amplification fixe 2.8 et logique Impact D ne fonctionnent plus pour patterns multiples

**Exemples d'écarts :**
```
Movement ID 1:  Prédit 124.9 pips → Réel 53.3 pips  (Erreur: -71.7)
Movement ID 2:  Prédit 252.5 pips → Réel 41.1 pips  (Erreur: -211.4)
Movement ID 64: Prédit 585.7 pips → Réel 51.4 pips  (Erreur: -534.3)
```

---

## 🔄 EN COURS

### 3. **Extraction Métriques Single Wave Fort** ⏳

**Status :** À faire  
**Objectif :** Extraire impact réel, durée, pullback pour tous les cas Single Wave Fort identifiés

**Méthode :**
- Scanner `step3_movements_with_patterns_v2.csv` pour `SINGLE_WAVE_FORT_*`
- Extraire prix réels depuis DB pour chaque mouvement
- Calculer : impact, latence, durée jusqu'à pic, pullback (si présent), stabilisation

**Livrable attendu :** `scripts/session137/singlewave_real_metrics.csv`

---

### 4. **Extraction Métriques ZigZag** ⏳

**Status :** À faire  
**Objectif :** Extraire impact net, amplitude cumulée, nombre de pics, durées entre pics

**Méthode :**
- Scanner `step3_movements_with_patterns_v2.csv` pour `ZIGZAG_*`
- Extraire prix réels depuis DB
- Calculer : impact net, amplitude cumulée, timing entre pics, pullback ratios

**Livrable attendu :** `scripts/session137/zigzag_real_metrics.csv`

---

## 📋 PROCHAINES ÉTAPES PLANIFIÉES

### Phase 1 : Calibration Impact D V2

**Objectif :** Créer fonction `calculate_impact_d_v2()` calibrée par pattern et famille d'événement

**Approche :**
1. **Par pattern :** Double Wave, Single Wave Fort, ZigZag
2. **Par famille d'événement :** CPI, NFP, Retail Sales, Manufacturing, etc.
3. **Intégration latence :** Impact = f(score_adjusted, num_events, latency, pattern_type, event_family)

**Formule conceptuelle :**
```python
def calculate_impact_d_v2(
    score_adjusted: float,
    num_events: int,
    latency_minutes: float,
    pattern_type: str,
    event_family: str
) -> float:
    """
    Calcule impact prédit en pips avec calibration par pattern/famille.
    
    Returns:
        Impact prédit (pips)
    """
    # Coefficients calibrés depuis métriques réelles
    base_impact = score_adjusted * num_events * AMPLIFICATION_BASE[pattern_type][event_family]
    
    # Ajustement latence (plus la latence est longue, plus l'impact peut être atténué)
    latency_factor = 1.0 - (latency_minutes / 10.0) * 0.1  # Exemple
    
    return base_impact * latency_factor
```

**Livrable :** `src/core/formulas_validated.py` (nouvelle fonction + coefficients JSON)

---

### Phase 2 : Calibration Durées / TTR V2

**Objectif :** Remplacer timelines fixes (T+5, T+11, etc.) par fonctions dynamiques

**Approche :**
- **Méthode inversion de courbe :** Détecter durée réelle par analyse de pente/angle
- **Calibration par pattern :** Durées médianes observées comme base
- **Ajustement dynamique :** Durée = f(score, volatilité pré-event, amplitude phase1)

**Formule conceptuelle :**
```python
def calculate_ttr_v2(
    pattern_type: str,
    phase: int,  # 1 ou 2
    score_adjusted: float,
    volatility_pre_event: float
) -> float:
    """
    Calcule Time To Reversal (ou durée jusqu'à pic) en minutes.
    
    Returns:
        Durée en minutes
    """
    # Durée médiane observée pour ce pattern/phase
    base_duration = MEDIAN_DURATIONS[pattern_type][phase]
    
    # Ajustement selon score (plus le score est élevé, plus la durée peut être longue)
    score_factor = 1.0 + (score_adjusted / 1000.0) * 0.1
    
    # Ajustement volatilité (plus volatile = mouvement plus rapide)
    volatility_factor = 1.0 - (volatility_pre_event / 0.001) * 0.05
    
    return base_duration * score_factor * volatility_factor
```

**Livrable :** `src/core/formulas_validated.py` (nouvelle fonction + coefficients)

---

### Phase 3 : Calibration Pullback V3

**Objectif :** Recalculer amplitude pullback en fonction de pente pré-event et amplitude Phase 1

**Approche :**
- Ratio pullback observé : ~40-50% pour Double Wave
- Ajustement selon : pente pré-event (R²), amplitude Phase 1, type d'événement

**Formule conceptuelle :**
```python
def calculate_pullback_v3(
    phase1_impact: float,
    r2_pre_event: float,
    pattern_type: str
) -> float:
    """
    Calcule amplitude pullback en pips.
    
    Returns:
        Amplitude pullback (pips)
    """
    # Ratio médian observé
    base_ratio = PULLBACK_RATIOS[pattern_type]  # ~0.45 pour Double Wave
    
    # Ajustement selon R² (tendance forte = pullback plus faible)
    r2_factor = 1.0 - (r2_pre_event * 0.2)
    
    return phase1_impact * base_ratio * r2_factor
```

**Livrable :** `src/core/formulas_validated.py` (nouvelle fonction)

---

### Phase 4 : Formule Direction / Latence (NOUVELLE)

**Objectif :** Prédire direction (UP/DOWN) et latence entre annonce et début mouvement

**Approche :**
1. **Direction :** Pente 30 min pré-annonce (R², signe) + signe surprise
2. **Latence :** Type d'événement + volatilité pré-event

**Formule conceptuelle :**
```python
def estimate_trend_direction(
    r2_pre_30min: float,
    slope_pre_30min: float,  # positif = hausse, négatif = baisse
    surprise_pct: float  # positif = meilleur que prévu, négatif = pire
) -> Tuple[str, float]:
    """
    Estime direction et probabilité.
    
    Returns:
        ('UP' ou 'DOWN', probabilité 0-1)
    """
    # Si surprise positive ET pente pré-event positive → UP fort
    # Si surprise négative ET pente pré-event négative → DOWN fort
    # Sinon → direction selon surprise dominante
    
    if surprise_pct > 0 and slope_pre_30min > 0:
        direction = 'UP'
        probability = min(0.9, 0.5 + abs(surprise_pct) / 100.0)
    elif surprise_pct < 0 and slope_pre_30min < 0:
        direction = 'DOWN'
        probability = min(0.9, 0.5 + abs(surprise_pct) / 100.0)
    else:
        direction = 'UP' if surprise_pct > 0 else 'DOWN'
        probability = 0.6
    
    return direction, probability


def estimate_latency(
    event_family: str,
    volatility_pre_event: float
) -> float:
    """
    Estime latence en minutes entre annonce et début mouvement.
    
    Returns:
        Latence en minutes
    """
    # Latence médiane observée par famille
    base_latency = LATENCY_BY_FAMILY[event_family]  # Ex: CPI = 1.5 min, NFP = 2.0 min
    
    # Ajustement volatilité (plus volatile = réaction plus rapide)
    volatility_factor = 1.0 - (volatility_pre_event / 0.001) * 0.2
    
    return base_latency * volatility_factor
```

**Livrable :** `src/core/formulas_validated.py` (nouvelles fonctions)

---

## 📊 VALIDATION PRÉVUE

### Cas de Référence à Tester

1. **11/09/2025 - Double Wave CPI US + Current Account DE**
   - Impact réel : ~53 pips
   - Pic réel : 15h10 (vs T+15 théorique = 14h45)
   - Latence : ~1-2 minutes

2. **Autres cas Double Wave** (160 cas disponibles)

3. **Cas Single Wave Fort** (à identifier depuis dataset)

4. **Cas ZigZag** (à identifier depuis dataset)

---

## 🎯 CRITÈRES DE SUCCÈS

- ✅ **MAE Impact < 10 pips** (vs ~160 pips actuellement)
- ✅ **MAE Durée < 10 minutes** (vs écarts de 30-60 min actuellement)
- ✅ **Direction correcte > 80%** (nouveau critère)
- ✅ **Latence prédite ± 2 minutes** (nouveau critère)

---

## 📁 FICHIERS DE RÉFÉRENCE

- `docs/PROJECT_MANAGEMENT/03_FORMULAS/VALIDATED_FORMULAS.md` - Formules V1 actuelles
- `scripts/session137/doublewave_real_metrics.csv` - Métriques réelles Double Wave
- `scripts/session137/doublewave_real_metrics_summary.csv` - Statistiques agrégées
- `scripts/session137/doublewave_formula_validation.csv` - Validation ancienne formule
- `src/core/formulas_validated.py` - Module formules (à mettre à jour)

---

## ⏭️ PROCHAINES ACTIONS IMMÉDIATES

1. ✅ **Extraire métriques Single Wave Fort** (script Python)
2. ✅ **Extraire métriques ZigZag** (script Python)
3. ✅ **Analyser corrélations Score → Impact par pattern/famille** (statistiques)
4. ✅ **Créer fonctions V1.2** (Impact D V2, TTR V2, Pullback V3, Direction/Latence)
5. ✅ **Valider sur cas de référence** (11/09 et autres)
6. ✅ **Intégrer dans Planificateur V3** (remplacer anciennes formules)

---

**Note :** Ce rapport sera mis à jour au fur et à mesure de l'avancement.

