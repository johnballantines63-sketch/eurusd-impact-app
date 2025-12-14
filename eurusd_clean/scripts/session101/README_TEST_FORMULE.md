# 🧪 TEST VALIDATION FORMULE V2.6

**Session 101.5 - Validation méthodologie**

---

## 🎯 OBJECTIF

Valider que la formule utilisée dans V2.6 donne les bons résultats sur le cas référence 11.09.2025 AVANT de continuer avec l'analyse complète des tendances.

**Principe :** On ne se fie pas aux références dans la doc, on TESTE réellement.

---

## 📋 CAS DE TEST

**Date :** 11 septembre 2025, 14:30 Bern
- **Événements :** 9 CPI US simultanés
- **Score base :** 44.31
- **Surprise max :** 33.33% (CPI inflation_rate_yoy)
- **Impact réel MT5 :** 56.2 pips UP

**Résultat attendu :** Impact prédit ~56-57 pips (erreur < 1 pip)

---

## 🚀 LANCEMENT

### Commande Simple

```bash
cd ~/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session101

chmod +x run_test_formule.sh

./run_test_formule.sh
```

**Durée :** < 5 secondes

---

## 📊 CE QUE LE SCRIPT FAIT

Le script teste **3 amplifications différentes** :

1. **V2.4 baseline** (amp = 2.5 fixe)
2. **V2.6 coefficient 0.55** (amp = 1.0 fixe)
3. **V2.7 dynamique** (amp = 0.5490 × R² + 1.6988)

**Pour chaque amplification :**
- Calcule score ajusté (Session 55)
- Calcule impact prédit (Session 51)
- Compare vs impact réel MT5 (56.2 pips)
- Affiche erreur absolue et relative

**Identifie la meilleure formule automatiquement.**

---

## ✅ RÉSULTATS ATTENDUS

Le script affichera quelque chose comme :

```
================================================================================
RÉSULTATS
================================================================================

🎯 MEILLEURE FORMULE : V2.4 (baseline)
   Amplification    : 2.500
   Impact prédit    : 57.0 pips
   Impact réel      : 56.2 pips
   Erreur absolue   : 0.8 pips
   Erreur relative  : 1.4%

================================================================================
VALIDATION
================================================================================

✅✅✅ FORMULE VALIDÉE - Précision exceptionnelle (< 1 pip)

Status validation : EXCELLENT
```

---

## 🎯 DÉCISION APRÈS TEST

### Si Erreur < 5 pips ✅

**→ Formule validée !**

Continuer avec le plan :
1. ✅ Utiliser cette formule comme baseline
2. ✅ Créer `analyze_trends_complete.py`
3. ✅ Analyser durée + amplitude + score composite
4. ✅ Tester corrélations multiples

### Si Erreur > 5 pips ❌

**→ Problème détecté !**

Actions nécessaires :
1. ⚠️ Vérifier données événement
2. ⚠️ Vérifier impact réel MT5
3. ⚠️ Identifier quelle formule utilise vraiment le Planificateur
4. ⚠️ NE PAS continuer avant correction

---

## 📁 FICHIERS

```
eurusd_clean/scripts/session101/
├── test_formule_11sept.py     # Script principal Python
├── run_test_formule.sh         # Script lancement bash
└── README_TEST_FORMULE.md      # Cette documentation
```

---

## 🔧 DÉPANNAGE

### Erreur "Module not found"

```bash
# Vérifier chemin
python3 -c "import sys; print(sys.path)"

# Ou exécuter directement
python3 test_formule_11sept.py
```

### Erreur import formulas_validated

```bash
# Vérifier fichier existe
ls -la ../../fx_impact_app/src/formulas_validated.py
```

---

## 📞 PROCHAINES ÉTAPES

**Après avoir exécuté le test :**

1. **Partager résultats avec Claude** (copier-coller section RÉSULTATS)
2. **Confirmer validation** (erreur < 5 pips ?)
3. **Si OK** → Claude continue avec analyse complète tendances
4. **Si pas OK** → Claude corrige d'abord le problème

---

**André, lance le test et partage-moi les résultats !** 🚀

_Session 101.5 - Test Validation Formule_  
_30 octobre 2025_  
_"Tester avant de continuer" 🧪_
