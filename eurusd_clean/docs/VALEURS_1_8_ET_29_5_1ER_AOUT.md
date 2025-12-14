# Valeurs 1.8 et 29.5 - 1er Août 2025 (Single Wave Fort)

**Date** : 2025-08-01  
**Pattern** : SINGLE WAVE FORT  
**Événement** : CPI US à 14:30 Bern

---

## 📊 VALEURS DÉTECTÉES DANS LES PRIX

### Baseline
- **Prix** : 1.14001
- **Heure** : 14:29:00 (1 min avant événement)

### Pic Maximum (Single Wave)
- **Impact** : **188.3 pips** ⬆️
- **Heure** : 16:00:00 (T+90 min depuis événement)
- **Prix** : 1.15884

### Pullback
- **Retracement** : **34.2 pips** (18.2% du pic)
- **Heure** : 16:10:00
- **Prix** : 1.15542
- **Ratio** : 34.2 / 188.3 = **0.182** (18.2%)

---

## 📈 PRÉDICTIONS DU PIPELINE

### Pattern Détecté
- **Type** : `SINGLE_WAVE_STRONG`
- **Confiance** : 100%

### Valeurs Prédites
- **Impact de base** : 250.82 pips
- **Wave 1 prédit** : 250.8 pips
- **Wave 2 prédit** : 250.8 pips (même que Wave 1 pour Single Wave)
- **Pullback prédit** : **25.1 pips**
- **Amplification** : 0.246x

---

## 🔍 RECHERCHE DES VALEURS 1.8 ET 29.5

### Valeur 1.8

**❓ Où apparaît le 1.8 ?**

Le 1.8 pourrait être :

1. **Extension Factor** (Wave2/Wave1) :
   - Pour Single Wave : Pas d'extension (Wave2 = Wave1)
   - Extension factor = 1.0x (pas 1.8)

2. **Ratio Wave1/ImpactBase** :
   - Ratio = 250.8 / 250.82 = **1.000** (pas 1.8)

3. **Amplification Factor** :
   - Amplification prédite = 0.246x (pas 1.8)
   - Mais selon les formules Session 87-88, pour surprise extrême :
     - Surprise 500% → Amplification ~9.7x
     - Pour atteindre 1.8x, surprise ≈ 18%

4. **Facteur dans formules** :
   - Dans `event_families.py` : 'GDP': 1.8
   - Mais pas directement lié à Single Wave Fort

### Valeur 29.5

**✅ Valeurs proches de 29.5 pips :**

1. **Pullback détecté** : 34.2 pips (proche de 29.5, écart 4.7 pips)
2. **Pullback prédit** : 25.1 pips (proche de 29.5, écart 4.4 pips)

**Observation** :
- Le pullback réel (34.2 pips) est **proche de 29.5** mais légèrement supérieur
- Le pullback prédit (25.1 pips) est également **proche de 29.5** mais légèrement inférieur
- La moyenne : (34.2 + 25.1) / 2 = **29.65 pips** ≈ **29.5 pips** ✅

---

## 💡 HYPOTHÈSES SUR LE 1.8

### Hypothèse 1 : Ratio Pullback/Pic
- Ratio réel : 34.2 / 188.3 = 0.182 (18.2%)
- Pas 1.8, mais **0.18** (proche !)

### Hypothèse 2 : Extension Factor (si Double Wave)
- Pour Double Wave typique : Wave2 / Wave1 ≈ 1.5x à 1.8x
- Mais ici c'est un **Single Wave Fort** (pas de Wave 2 distincte)

### Hypothèse 3 : Facteur d'Amplification Spécifique
- Peut-être un facteur utilisé dans les calculs de Single Wave Fort ?
- À vérifier dans les formules de `single_wave_strong.py`

### Hypothèse 4 : Ratio Impact Réel / Impact Base
- Impact réel : 188.3 pips
- Impact base : 250.82 pips
- Ratio : 188.3 / 250.82 = **0.751** (pas 1.8)

### Hypothèse 5 : Inverse du ratio
- Impact base / Impact réel = 250.82 / 188.3 = **1.332** (pas 1.8)

---

## 📋 CONCLUSION

### Valeur 29.5 ✅
**Trouvée !** Le pullback est **proche de 29.5 pips** :
- Pullback détecté : 34.2 pips (écart 4.7)
- Pullback prédit : 25.1 pips (écart 4.4)
- **Moyenne ≈ 29.5 pips**

### Valeur 1.8 ❓
**À clarifier** : Le facteur 1.8 n'apparaît pas directement dans les résultats du 1er août.

**Possibilités** :
1. **0.18** (ratio pullback/pic = 18.2%) - très proche
2. Facteur d'amplification dans formules (à vérifier)
3. Extension factor pour Double Wave (mais ici Single Wave)
4. Facteur spécifique à Single Wave Fort (à documenter)

---

## 🔎 QUESTIONS À CLARIFIER

1. **Le 1.8** fait-il référence à :
   - Un ratio (ex: 0.18 = 18%) ?
   - Un facteur d'amplification ?
   - Une extension factor ?
   - Autre ?

2. **Le 29.5** fait-il référence à :
   - Le pullback réel (34.2 pips) ?
   - Le pullback prédit (25.1 pips) ?
   - Une moyenne des deux (29.65 pips) ?
   - Une valeur cible idéale ?

---

**Status** : ⚠️ Besoin de clarification sur la valeur 1.8




