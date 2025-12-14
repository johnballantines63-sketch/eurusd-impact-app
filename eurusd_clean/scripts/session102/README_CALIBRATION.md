# 🧮 CALIBRATION FORMULE AMPLIFICATION

**Session 102 - Méthode Scientifique Complète**

---

## 🎯 OBJECTIF

Trouver la **formule mathématique optimale** qui prédit `amp_parfaite` à partir de tendance 72h.

**Méthode :**
1. ✅ Ancrage sur cas référence 11.09.2025
2. ✅ 7 formules mathématiques candidates
3. ✅ Calibration paramètres (scipy.optimize)
4. ✅ Test sur TOUS les clusters
5. ✅ Sélection meilleure formule (MAE minimal)

---

## 📐 FORMULES TESTÉES

### F1 : Linéaire Simple
```
amp = a × R² + b
```

### F2 : Ratio Proportionnel (Ancré)
```
amp = amp_ref × (R² / R²_ref)^k
amp = 2.537 × (R² / 0.742)^k
```

### F3 : Delta Additive (Ancré)
```
amp = amp_ref + k × (R² - R²_ref)
amp = 2.537 + k × (R² - 0.742)
```

### F4 : Exponentielle (Ancré)
```
amp = amp_ref × exp(k × (R² - R²_ref))
amp = 2.537 × exp(k × (R² - 0.742))
```

### F5 : Linéaire Dual (R² + Amplitude)
```
amp = a × R² + b × amplitude + c
```

### F6 : Delta Dual (Ancré)
```
amp = amp_ref + k1×(R²-R²_ref) + k2×(amplitude-amp_ref)
amp = 2.537 + k1×(R²-0.742) + k2×(amplitude-114.3)
```

### F7 : Inverse (Tendance forte → Amp faible)
```
amp = a / (R² + 0.1) + b
```

---

## 🚀 LANCEMENT

```bash
cd ~/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session102

chmod +x run_calibration.sh && ./run_calibration.sh
```

**Durée :** 5-10 secondes

---

## 📊 PROCESSUS

### ÉTAPE 1 : Cas Référence
```
11 septembre 2025 :
- Amp parfaite    : 2.537
- R² 72h          : 0.742
- Amplitude 72h   : 114.3 pips
- Impact réel     : 57.1 pips
```

### ÉTAPE 2 : Définition Formules
- 7 formules mathématiques candidates
- Chaque formule a 1-3 paramètres à calibrer

### ÉTAPE 3 : Dataset Calibration
- Filtrage clusters similaires (9-11 events, score 43-46)
- ~25 dates pour calibration

### ÉTAPE 4 : Calibration Paramètres
- `scipy.optimize.minimize` pour chaque formule
- Objectif : Minimiser MAE(amp_prédite, amp_parfaite)
- Contrainte : amp entre 0.5 et 5.0

### ÉTAPE 5 : Test Global
- Application sur TOUS les clusters (~44 dates)
- Calcul MAE, RMSE, Corrélation
- Comparaison vs baseline amp=2.5

### ÉTAPE 6 : Sélection
- **Meilleure formule = MAE minimal**
- Vérification amélioration > 10% vs baseline

### ÉTAPE 7 : Décision
- ✅✅ VALIDÉE (MAE < baseline×0.9 ET corr > 0.5)
- ⚠️ PARTIELLE (MAE < baseline mais critères incomplets)
- ❌ REJETÉE (MAE ≥ baseline)

---

## 📋 RÉSULTATS ATTENDUS

### Scénario A : Formule VALIDÉE ✅✅

```
🏆 MEILLEURE FORMULE : F3: Delta additive
   
   Équation : amp = 2.537 + 1.245 × (R² - 0.742)
   
   Métriques :
   - MAE                : 0.845
   - vs Baseline (2.5)  : +45.2%
   - Corrélation        : +0.687

✅✅ FORMULE VALIDÉE
   Amélioration : 45.2%
   RECOMMANDATION : Intégrer dans Planificateur V2.7
```

### Scénario B : Validation PARTIELLE ⚠️

```
🏆 MEILLEURE FORMULE : F5: Linéaire dual
   
   Équation : amp = 1.234 × R² + 0.0045 × amplitude + 1.234
   
   Métriques :
   - MAE                : 1.345
   - vs Baseline (2.5)  : +8.5%
   - Corrélation        : +0.387

⚠️ VALIDATION PARTIELLE
   Amélioration < 10% OU Corrélation < 0.5
   RECOMMANDATION : Tester en production avec monitoring
```

### Scénario C : Formule REJETÉE ❌

```
🏆 MEILLEURE FORMULE : F1: Linéaire simple
   
   Équation : amp = 0.456 × R² + 2.145
   
   Métriques :
   - MAE                : 1.567
   - vs Baseline (2.5)  : -3.2%
   - Corrélation        : +0.156

❌ FORMULE REJETÉE
   Aucune amélioration vs baseline
   RECOMMANDATION : Rester avec baseline amp=2.5
```

---

## 📊 TABLEAU COMPARATIF FINAL

```
Formule                                  MAE      Amélioration    Corr
--------------------------------------------------------------------------------
BASELINE amp=2.5                        1.489         0.0%        N/A
F3: Delta additive                      0.845       +45.2%       +0.687
F6: Delta dual                          0.912       +38.7%       +0.654
F5: Linéaire dual (R²+amplitude)        1.123       +24.6%       +0.523
F2: Ratio proportionnel                 1.234       +17.1%       +0.445
F1: Linéaire simple                     1.345       +9.7%        +0.387
F4: Exponentielle                       1.456       +2.2%        +0.234
F7: Inverse                             1.567       -5.2%        +0.156
```

---

## 🎯 DÉCISION AUTOMATIQUE

Le script donne automatiquement la décision :

**✅✅ VALIDÉE** si :
- MAE < baseline × 0.9 (amélioration > 10%)
- ET Corrélation > 0.5

**⚠️ PARTIELLE** si :
- MAE < baseline
- MAIS critères incomplets

**❌ REJETÉE** si :
- MAE ≥ baseline

---

## 💡 INTERPRÉTATIONS

### Si F3 (Delta additive) gagne

**Formule :**
```python
amp = 2.537 + k × (R² - 0.742)
```

**Si k > 0 :** Tendance forte → Amp forte (momentum)  
**Si k < 0 :** Tendance forte → Amp faible (saturation)

### Si F7 (Inverse) gagne

**Formule :**
```python
amp = a / (R² + 0.1) + b
```

**Confirme :** Tendance forte → Amp faible (hypothèse initiale)

### Si F5/F6 (Dual) gagne

**Besoin de 2 variables :** R² + amplitude

**Complexité accrue mais meilleure précision**

---

## 📞 APRÈS EXÉCUTION

**Partage avec Claude :**
- Section "SÉLECTION MEILLEURE FORMULE"
- Équation finale
- Section "DÉCISION FINALE"
- Tableau comparatif

**Actions selon résultat :**

**Si VALIDÉE :**
→ Session 103 : Intégrer formule dans Planificateur V2.7

**Si PARTIELLE :**
→ Discussion : Test production ou rester baseline

**Si REJETÉE :**
→ Session 103 : Baseline amp=2.5 définitive

---

**Lance le script et partage-moi les résultats ! 🚀**

_Session 102 - Calibration Formule Amplification_  
_30 octobre 2025_  
_"Méthode scientifique rigoureuse" 🧮_
