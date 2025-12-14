# 📋 WORKFLOW SESSION 130 - CALIBRATION PAR PATTERN

**Objectif :** Calibrer fonction amplification PAR TYPE DE PATTERN (approche pattern-based)

**Principe :** Scanner mouvements → Grouper par pattern → Calibrer fonction spécifique par pattern

**Durée estimée complète :** 6-8 heures  
**Budget tokens :** 190,000 (Session 130)

---

## 🎯 STRUCTURE WORKFLOW - 10 ÉTAPES

### **PHASE 1 : FONDATIONS** (Étapes 1-3) ✅ IMPLÉMENTÉE
**Durée :** ~2h | **Tokens :** ~25k | **Priorité :** 🔴 CRITIQUE

- **ÉTAPE 1 :** Scanner mouvements 2023-2025 (seuil 35 pips)
- **ÉTAPE 2 :** Classifier patterns (DoubleWave, SingleWave, ZigZag)
- **ÉTAPE 3 :** Définir cas de référence (1 par pattern)

### **PHASE 2 : CALIBRATION** (Étapes 4-5) ⏳ À IMPLÉMENTER
**Durée :** ~40min | **Tokens :** ~10k | **Priorité :** 🟠 HAUTE

- **ÉTAPE 4 :** Calculer amplifications idéales cas référence
- **ÉTAPE 5 :** Établir table référence

### **PHASE 3 : RECHERCHE SIMILARITÉS** (Étapes 6-7) ⏳ À IMPLÉMENTER
**Durée :** ~1h30 | **Tokens :** ~25k | **Priorité :** 🟠 HAUTE

- **ÉTAPE 6 :** Trouver clusters composition similaire
- **ÉTAPE 7 :** Calculer R² pré-événement (7j avant)

### **PHASE 4 : MODÉLISATION** (Étapes 8-10) ⏳ OPTIONNEL
**Durée :** ~2h | **Tokens :** ~40k | **Priorité :** 🟡 NORMALE

- **ÉTAPE 8 :** Corrélation R² ↔ Amplification
- **ÉTAPE 9 :** Validation dates test
- **ÉTAPE 10 :** Métriques finales

---

## 🚀 QUICK START - PHASE 1

### **Lancer PHASE 1 complète** (recommandé)

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean
python scripts/session130/run_phase1.py
```

**Durée :** ~45 min  
**Outputs :**
- `movements_2023_2025_complete.json` (~100-150 mouvements)
- `patterns_classified.json` (groupés par pattern)
- `reference_cases.json` (1 cas référence par pattern)

### **Lancer étapes individuelles**

```bash
# ÉTAPE 1 : Scanner (~30-45 min)
python scripts/session130/scan_by_month.py

# ÉTAPE 2 : Classification (~2 min)
python scripts/session130/classify_patterns.py

# ÉTAPE 3 : Cas référence (~1 min)
python scripts/session130/define_reference_cases.py
```

---

## 📂 FICHIERS CRÉÉS

### **Scripts Python** (7 fichiers)

```
session130/
├── scan_movements_2023_2025.py      # Scanner principal (classe MovementScanner)
├── scan_by_month.py                 # Scanner mois par mois (progression visible)
├── classify_patterns.py             # Classification en groupes
├── define_reference_cases.py        # Sélection cas référence
├── test_scanner_quick.py            # Tests dates connues
├── run_phase1.py                    # Orchestrateur PHASE 1
└── README.md                        # Cette documentation
```

### **Données JSON** (3 fichiers après PHASE 1)

```
session130/
├── movements_2023_2025_complete.json       # Tous mouvements détectés
├── patterns_classified.json                # Groupés par pattern
└── reference_cases.json                    # Cas référence sélectionnés
```

---

## 🎯 VALIDATION RÉSULTATS

### **Critères succès PHASE 1**

✅ **Minimum viable :**
- Scanner détecte 100+ mouvements (2023-2025)
- 11 septembre 2025 présent et classifié DoubleWave
- Au moins 2 patterns avec cas référence

✅ **Optimal :**
- 150+ mouvements détectés
- 5 patterns avec cas référence (DoubleWave, SingleWave, ZigZag...)
- 11 septembre sélectionné comme référence DoubleWave_Overlap

### **Validation cas connus**

Le scanner DOIT détecter :
- **11 septembre 2025** : DoubleWave (~56 pips, validé Session 115)
- **1er août 2025** : SingleWave Fort (~174 pips, NFP)
- **5 septembre 2025** : ZigZag (~72 pips, NFP)

---

## ⚙️ CONFIGURATION SCANNER

### **Paramètres détection** (dans `scan_movements_2023_2025.py`)

```python
MIN_SPIKE_PIPS = 35.0              # Seuil détection (validé Session 117)
BASELINE_N = 5                     # Baseline locale (5 barres)
SPIKE_LOOKAHEAD_MIN = 6            # Lookahead cumulatif (6 min)
PULLBACK_WIN_MIN = 30              # Fenêtre pullback (30 min)
WAVE2_WIN_MIN = 40                 # Fenêtre Wave2 (40 min)
```

### **Critères classification patterns**

```python
# DOUBLE WAVE
PULLBACK_DOUBLE_MIN = 0.25         # Pullback min 25%
PULLBACK_DOUBLE_MAX = 0.70         # Pullback max 70%
ALPHA_WAVE2_OVER_WAVE1 = 0.60      # Wave2 >= 60% Wave1

# SINGLE WAVE
PULLBACK_SINGLE_MAX = 0.30         # Pullback max 30%
Impact > 40 pips → SingleWave_Fort
Impact 20-40 pips → SingleWave_Intermediate

# ZIG ZAG
Pullback < 60% + 3+ pics successifs
```

### **Fenêtre événements causaux**

```python
window_minutes = 30                # ±30 min autour peak
importance_n >= 2                  # MEDIUM + HIGH seulement
```

---

## 🔍 STRUCTURE DONNÉES

### **movements_2023_2025_complete.json**

```json
{
  "metadata": {
    "scan_date": "2025-11-12T...",
    "period_start": "2023-01-01",
    "period_end": "2025-11-07",
    "threshold_pips": 35.0,
    "total_movements": 150
  },
  "statistics": {
    "pattern_counts": {
      "DoubleWave_Overlap": 10,
      "SingleWave_Fort": 35,
      ...
    },
    "pattern_avg_impact": { ... }
  },
  "movements": [
    {
      "date": "2025-09-11",
      "baseline_time": "2025-09-11T14:25:00+02:00",
      "peak_time": "2025-09-11T14:35:00+02:00",
      "direction": "bullish",
      "impact_pips": 56.2,
      "pattern": "DoubleWave_Overlap",
      "wave1_pips": 33.7,
      "pullback_ratio": 0.73,
      "wave2_pips": 51.7,
      "events": [
        {
          "event_key": "cpi_mom",
          "ts_utc": "2025-09-11T12:30:00+00:00",
          "country": "US",
          "actual": 0.2,
          "forecast": 0.2,
          "previous": 0.2,
          "importance": "HIGH"
        },
        ...
      ],
      "n_events": 2
    },
    ...
  ]
}
```

### **reference_cases.json**

```json
{
  "metadata": { ... },
  "reference_cases": {
    "DoubleWave_Overlap": {
      "date": "2025-09-11",
      "impact_real": 56.2,
      "baseline_time": "...",
      "peak_time": "...",
      "events": [...],
      "n_events": 2,
      "status": "validated"  // ou "to_validate"
    },
    "SingleWave_Fort": { ... },
    ...
  },
  "validated_cases": {
    "DoubleWave_Overlap": {
      "date": "2025-09-11",
      "reason": "Validé Session 115 (MAE 0.29 pips)",
      "priority": 1
    }
  }
}
```

---

## ⚠️ POINTS D'ATTENTION CRITIQUES

### **1. Timezone** ⚠️⚠️⚠️

**TOUJOURS utiliser `utils_timezone.py` pour conversions !**

```python
# ✅ CORRECT
from utils_timezone import ensure_bern_time, get_price_window

ts_bern = ensure_bern_time(event_ts_utc)
start, event, end = get_price_window(cluster_time)

# ❌ FAUX (double conversion +2h)
ts_bern = event_ts_utc + timedelta(hours=2)
```

**Raison :** `events.ts_utc` stocke DÉJÀ en Bern time (+02:00)

### **2. Filtrage cluster événements**

```python
# ✅ CORRECT : Filtrer ±5 min autour cluster_time
cluster_start = cluster_time - timedelta(minutes=5)
cluster_end = cluster_time + timedelta(minutes=5)
df_cluster = df[df['ts_utc'].between(cluster_start, cluster_end)]

# ❌ FAUX : Prendre TOUS événements du jour
df_cluster = df[df['ts_utc'].dt.date == date]
```

### **3. Approche pattern-based vs event-based**

```python
# ✅ CORRECT : Calibrer PAR PATTERN
amp_DoubleWave = calibrate_pattern("DoubleWave_Overlap", cases)
amp_SingleWave = calibrate_pattern("SingleWave_Fort", cases)

# ❌ FAUX : Calibrer PAR TYPE ÉVÉNEMENT
amp_CPI = calibrate_event("CPI", cases)  # Naïf !
amp_NFP = calibrate_event("NFP", cases)
```

**Raison :** Même événement (NFP) peut créer patterns différents → calibrations différentes

---

## 📊 STATISTIQUES ATTENDUES

### **Distribution patterns typique**

```
DoubleWave_Overlap      : ~10-15  (rare, ~10%)
DoubleWave_Cascade      : ~5-10   (très rare)
SingleWave_Fort         : ~30-40  (fréquent, ~30%)
SingleWave_Intermediate : ~40-50  (majoritaire, ~40%)
ZigZag                  : ~15-20  (modéré, ~15%)
Other                   : ~10-15  (edge cases)
```

### **Taux avec événements causaux**

```
Avec events (validables) : ~80-90%
Sans events (techniques) : ~10-20%
```

**Note :** Patterns techniques (sans events) = mouvements inexplicables par données économiques

---

## 🐛 TROUBLESHOOTING

### **Problème : Scanner ne détecte rien**

1. Vérifier connexion DB
2. Vérifier période prix disponible (`prices_bern`)
3. Abaisser seuil détection (ex: 30 pips au lieu 35)
4. Vérifier timezone conversions

### **Problème : 11 septembre non détecté**

1. Vérifier seuil 35 pips (pas 40 pips)
2. Baseline locale correcte (5 barres)
3. Lookahead 6 min minimum
4. Vérifier données prix 11 septembre complètes

### **Problème : Classification pattern incorrecte**

1. Vérifier seuils pullback (25-70% pour DoubleWave)
2. Vérifier fenêtre Wave2 (40 min)
3. Critère Alpha (Wave2 >= 60% Wave1)
4. Comparer avec détecteurs validés Session 117-120

### **Problème : Aucun cas référence sélectionné**

1. Vérifier critère n_events >= 2
2. Assouplir filtre percentile (50-75%)
3. Accepter n_events >= 1 en fallback
4. Vérifier données événements disponibles

---

## 🎯 PROCHAINES ÉTAPES

### **Après PHASE 1 réussie**

1. **Valider résultats :**
   - Vérifier 11 septembre présent et classifié DoubleWave
   - Vérifier >= 2 patterns avec cas référence
   - Valider distribution patterns cohérente

2. **Lancer PHASE 2 (à implémenter) :**
   - Créer `calculate_ideal_amplifications.py`
   - Calculer `amp_ideal = impact / (score × sqrt(n))`
   - Enrichir `reference_cases.json` avec amp idéales

3. **Décision budget tokens :**
   - Si < 60k restants → arrêter et documenter
   - Si >= 60k restants → continuer PHASES 3-4

---

## 📚 RÉFÉRENCES

### **Sessions précédentes**

- **Session 115 :** Validation 11 septembre (MAE 0.29 pips)
- **Session 117 :** Scanner prix bottom-up (42 patterns, seuil 35 pips)
- **Session 120 :** DoubleWaveDetector Rev12 (MAE 4.5 pips)
- **Session 129 :** Correction timezone + validation +95.2%

### **Documentation**

- **HANDOFF :** `SESSION_130_HANDOFF.md` (workflow complet)
- **MASTER PLAN :** `MASTER_PLAN.md` (vision projet)
- **Utils timezone :** `session129/utils_timezone.py` (OBLIGATOIRE)

### **Scripts validés réutilisés**

- `session117/price_pattern_scanner_rev7_multimin.py` (scanner baseline)
- `session120/double_wave_detector_rev12.py` (détecteur patterns)
- `session129/utils_timezone.py` (timezone handling)

---

## 📞 SUPPORT

**Problème technique ?**
1. Lire section Troubleshooting ci-dessus
2. Vérifier HANDOFF Session 130 (section POINTS D'ATTENTION)
3. Comparer avec scripts validés sessions précédentes

**Budget tokens insuffisant ?**
- Arrêter après PHASE 1 (minimum viable)
- Documenter état complet
- Reporter PHASES 2-4 à Session 131

---

**Auteur :** André Valentin avec Claude  
**Date :** 12 novembre 2025 - Session 130  
**Version :** 1.0  
**Statut :** ✅ PHASE 1 IMPLÉMENTÉE - PRÊT À LANCER
