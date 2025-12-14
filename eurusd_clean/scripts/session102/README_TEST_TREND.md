# 🧪 TEST HYPOTHÈSE TENDANCE SUR CLUSTERS

**Session 102 - Test Final**

---

## 🎯 HYPOTHÈSE TESTÉE

**"Pour des clusters SIMILAIRES (même composition CPI US),**
**la tendance 72h AVANT explique-t-elle la variance d'amplification ?"**

### Logique

```
Tendance FORTE 72h (R² élevé, amplitude forte)
→ Prix déjà ajusté / anticipations intégrées
→ Cluster réagit MOINS que prévu
→ Amplification FAIBLE nécessaire

Corrélation attendue : NÉGATIVE (tendance ↑ → amp ↓)
```

---

## 🚀 LANCEMENT

```bash
cd ~/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session102

chmod +x run_test_trend.sh && ./run_test_trend.sh
```

**Durée :** < 5 secondes

---

## 📊 CE QUE ÇA FAIT

### ÉTAPE 1 : Charge données Session 102
- Résultats analyse avec vraies données
- Métriques tendance 72h (Session 101.5)

### ÉTAPE 2 : Filtre clusters SIMILAIRES
- Garde seulement CPI US typiques (9-11 events, score 43-46)
- Élimine outliers (score anormal, trop peu/trop events)

### ÉTAPE 3 : Test corrélations PRIMAIRES
- R² 72h vs amp_parfaite
- Amplitude 72h vs amp_parfaite
- Score composite vs amp_parfaite

### ÉTAPE 4 : Subdivision par surprise
- Groupe surprise FAIBLE
- Groupe surprise FORTE
- Test si corrélation varie selon surprise

### ÉTAPE 5 : Régression multiple CONTRÔLÉE
- Contrôle pour surprise + score résiduel
- Mesure effet PROPRE de tendance
- Coefficients standardisés pour comparaison

### ÉTAPE 6 : Visualisations ASCII
- Scatter plots amp vs R²
- Scatter plots amp vs amplitude

### ÉTAPE 7 : DÉCISION automatique
- ✅✅ VALIDÉE (corr > 0.5, p < 0.05)
- ⚠️ PARTIELLE (corr > 0.3)
- ❌ REJETÉE (corr < 0.3)

---

## 📋 RÉSULTATS ATTENDUS

### Scénario A : Hypothèse VALIDÉE ✅✅

```
🎯 Meilleure corrélation : R² 72h
   Corrélation : -0.652 (négative)
   P-value     : 0.008 (significatif)

✅✅ HYPOTHÈSE VALIDÉE
   R² élevé → Amp faible (conforme hypothèse)
   
Formule dynamique possible :
   amp = 2.5 - (0.8 × r_squared)
```

### Scénario B : Hypothèse PARTIELLE ⚠️

```
🎯 Meilleure corrélation : Amplitude 72h
   Corrélation : -0.387
   P-value     : 0.145 (non significatif)

⚠️ HYPOTHÈSE PARTIELLEMENT VALIDÉE
   Effet détecté mais trop faible
   
Recommandation : Élargir dataset
```

### Scénario C : Hypothèse REJETÉE ❌

```
🎯 Meilleure corrélation : R² 72h
   Corrélation : -0.089
   P-value     : 0.687

❌ HYPOTHÈSE REJETÉE
   Tendance 72h n'explique PAS amplification
   
Recommandation : Rester baseline amp=2.5
```

---

## 🎯 POINTS CLÉS

### Ce qu'on teste

✅ **Clusters multi-événements** (9-11 CPI simultanés)  
✅ **Composition similaire** (score ~45)  
✅ **Impact calculé vectoriellement** (correction 0.758)  
✅ **Corrélations sur sous-ensemble homogène**

### Ce qu'on NE teste PAS

❌ Événements individuels isolés  
❌ Mix types différents (CPI + NFP + FOMC)  
❌ Corrélation globale sans filtrage  
❌ Impact réel vs amp (circulaire)

---

## 💡 INTERPRÉTATIONS POSSIBLES

### Si corrélation NÉGATIVE forte (-0.5 ou moins)

**Conforme hypothèse :**
- Tendance forte → Prix ajusté → Amp faible
- Formule dynamique recommandée
- amp = 2.5 - (k × tendance)

### Si corrélation POSITIVE forte (+0.5 ou plus)

**Contraire hypothèse :**
- Tendance forte → Momentum → Amp forte
- Effet amplification au lieu d'atténuation
- amp = 2.5 + (k × tendance)

### Si corrélation NULLE (< 0.3)

**Tendance non-prédictive :**
- Facteurs externes dominent
- Contexte macro, sentiment, surprises politiques
- Baseline amp=2.5 reste optimal

---

## 📞 APRÈS EXÉCUTION

**Partage avec Claude :**
- Section "DÉCISION FINALE"
- Meilleure corrélation trouvée
- Recommandations

**Actions selon résultat :**

**Si VALIDÉE :**
→ Session 103 : Créer formule dynamique amp(tendance)

**Si PARTIELLE :**
→ Discussion : Élargir dataset ou accepter baseline

**Si REJETÉE :**
→ Session 103 : Intégrer baseline V2.7 dans Planificateur

---

**Lance le script et partage-moi les résultats ! 🎯**

_Session 102 - Test Hypothèse Tendance_  
_30 octobre 2025_  
_"Clusters similaires seulement" 📊_
