# 🚀 SESSION 117 - GUIDE D'UTILISATION

**Date :** 06 novembre 2025  
**Objectif :** Scanner prix (bottom-up) pour détecter patterns réels

---

## 📁 SCRIPTS CRÉÉS

### **1. check_sept11.py** (Vérification rapide)
Vérifie que les données du 11 septembre sont accessibles et permettent de détecter le spike de 56.2 pips.

**Exécution :**
```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session117
python check_sept11.py
```

**Résultat attendu :**
- ✅ Spike détecté ~56 pips
- ✅ Données présentes 14:00-16:00

---

### **2. test_scanner.py** (Test septembre 2025)
Teste l'algorithme de détection sur septembre 2025 (période connue avec le 11 sept).

**Exécution :**
```bash
python test_scanner.py
```

**Résultat attendu :**
- ✅ Détection du 11 septembre comme Double Wave
- ✅ Impact ~56 pips
- ✅ Extension factor ~1.5x

**Paramètres test :**
- Période : 01-30 septembre 2025
- Seuil : 30 pips (réduit pour test)
- Horaires : 13:00-16:00

---

### **3. scan_price_patterns.py** (Scanner complet)
Scanner principal pour toute la période 2024-2025.

**Exécution :**
```bash
python scan_price_patterns.py
```

**Paramètres production :**
- Période : 2024-01-01 → 2025-11-06
- Seuil : 40 pips
- Horaires : 13:00-16:00 (jours ouvrés)

**Durée estimée :** 5-10 minutes (scanner 700+ jours)

**Output :** `patterns_detected.json`

---

## 🎯 WORKFLOW RECOMMANDÉ

### **ÉTAPE 1 : Vérification (1 min)**
```bash
python check_sept11.py
```

Valider que :
- Base de données accessible
- Données 11 septembre présentes
- Spike ~56 pips détectable

---

### **ÉTAPE 2 : Test algorithme (2 min)**
```bash
python test_scanner.py
```

Valider que :
- Algorithme détecte le 11 septembre
- Classification correcte (Double Wave)
- Métriques cohérentes (extension factor, pullback)

⚠️ **SI 11 SEPTEMBRE NON DÉTECTÉ :**
- Réduire seuil (30 pips → 25 pips)
- Vérifier fenêtre temporelle
- Ajuster critères pullback

---

### **ÉTAPE 3 : Scan complet (10 min)**
```bash
python scan_price_patterns.py
```

Scanner toute la période 2024-2025.

**Critère succès :**
- ✅ 10+ patterns détectés
- ✅ Dont au moins 3-5 Double Wave
- ✅ 11 septembre inclus dans résultats

**Output :** `patterns_detected.json`

---

## 📊 FORMAT OUTPUT JSON

```json
[
  {
    "pattern": "double_wave",
    "direction": "bullish",
    "baseline_price": 1.08500,
    "baseline_time": "2025-09-11T14:25:00+02:00",
    "peak1_price": 1.08873,
    "peak1_time": "2025-09-11T14:32:00+02:00",
    "spike_pips": 37.3,
    "pullback_price": 1.08605,
    "pullback_time": "2025-09-11T14:38:00+02:00",
    "pullback_pips": 26.8,
    "pullback_ratio": 0.72,
    "wave2_peak_price": 1.09062,
    "wave2_peak_time": "2025-09-11T14:52:00+02:00",
    "wave2_from_baseline_pips": 56.2,
    "extension_factor": 1.51,
    "total_impact_pips": 56.2
  }
]
```

---

## 🔧 ALGORITHME DÉTECTION

### **Détection Spike Initial**
1. Fenêtre glissante 90 minutes
2. Baseline = moyenne premiers 5 minutes
3. Chercher max|min depuis baseline
4. Seuil : > 40 pips (bullish ou bearish)

### **Classification Pattern**

#### **DOUBLE WAVE**
- ✅ Pullback > 50% du spike initial
- ✅ Wave 2 existe (pic après pullback)
- ✅ Extension ≥ 1.0x (Wave2 ≥ Wave1 depuis baseline)

#### **SINGLE WAVE FORT**
- ✅ Pullback < 30% du spike
- ✅ Momentum continu sans deuxième impulsion

#### **INTERMÉDIAIRE**
- Pullback entre 30-50%
- Non classé Double/Single

---

## ⚙️ PARAMÈTRES AJUSTABLES

### **Dans scan_price_patterns.py :**

```python
# Seuil détection spike
min_spike_pips = 40.0  # Réduire à 35 si peu de résultats

# Critère Double Wave
pullback_ratio > 0.5   # Pullback > 50%
extension_factor >= 1.0  # Wave2 ≥ Wave1

# Critère Single Wave Fort
pullback_ratio < 0.3   # Pullback < 30%

# Fenêtre temporelle
trading_hours_only = True  # 13:00-16:00 ou False pour 24h
```

---

## 📝 NOTES IMPORTANTES

### **Performance**
- Scanner optimisé : fenêtres glissantes + skip après détection
- Évite duplicates : saute 60 min après chaque pattern
- Base DuckDB : lecture seule (pas de modifications)

### **Timezone**
- Tous les timestamps en Bern time (+02:00)
- Compatible avec table events (timezone unifié)

### **Exclusions**
- Week-ends exclus automatiquement
- Seuls jours ouvrés scannés

---

## 🎯 PROCHAINES ÉTAPES APRÈS SCAN

Une fois les patterns détectés :

1. **Enrichir avec events** (`enrich_with_events.py` - à créer)
   - Mapper events causaux par spike
   - Fenêtre ±5 min autour peak

2. **Valider formule** (`validate_formula.py` - à créer)
   - Tester `calculate_double_wave_overlapping()` sur chaque cas
   - Calculer MAE par pattern

3. **Analyser patterns** (`analyze_patterns.py` - à créer)
   - Statistiques découverte
   - Insights trading

---

## ✅ CHECKLIST VALIDATION

Avant de déclarer succès Session 117 :

- [ ] check_sept11.py exécuté avec succès
- [ ] test_scanner.py détecte le 11 septembre
- [ ] scan_price_patterns.py exécuté sur 2024-2025
- [ ] 10+ patterns détectés (dont 3+ Double Wave)
- [ ] patterns_detected.json créé
- [ ] 11 septembre présent dans résultats finaux
- [ ] Métriques 11 sept cohérentes (56.2 pips, extension 1.5x)

---

**Auteur :** André Valentin avec Claude  
**Date :** 06 novembre 2025  
**Version :** 1.0
