# 📋 DÉMARRAGE SESSION 118

**Date :** 07 novembre 2025  
**Session précédente :** 117  
**Session actuelle :** 118  
**Objectif :** Valider formule S115 sur 13 Double Wave avec events

---

## 🎯 MESSAGE DÉMARRAGE (À COPIER-COLLER)

```
Bonjour Claude,

Je démarre la Session 118.

═══════════════════════════════════════════════════════════════════
⚠️  LECTURE ATTENTIVE OBLIGATOIRE (MOT PAR MOT - PAS DE SURVOL)
═══════════════════════════════════════════════════════════════════

📖 LIRE MOT PAR MOT (sections critiques) :
────────────────────────────────────────────────────────────────
1. /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/01_VISION/MASTER_PLAN.md
   → Section "GAP #1" : LIRE MOT PAR MOT
   → Point clé : Formule S115 validée sur 11 sept (MAE 0.29 pips)
   → Dataset créé Session 117 : 13 cas Double Wave avec events
   → Si tu comprends "tester sur 15 cas" → TU AS MAL LU (2 sans events exclus)
   
2. /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/99_SESSIONS/SESSION_117_HANDOFF.md
   → Section "Plan d'action Session 118" : LIRE LIGNE PAR LIGNE
   → Étape 1-5 détaillées
   → Objectif : MAE moyen < 5 pips sur 13 cas
   → Si tu proposes de tester patterns SANS events → TU AS MAL LU
   
3. /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session117/double_waves_enriched.json
   → Parcourir structure : comprendre format données
   → 15 Double Wave dont 13 avec events (validables)

📋 SURVOL AUTORISÉ (contexte général) :
────────────────────────────────────────────────────────────────
4. /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/00_README.md
   → Juste comprendre navigation PROJECT_MANAGEMENT/

═══════════════════════════════════════════════════════════════════

✅ QUIZ DE COMPRÉHENSION OBLIGATOIRE :
────────────────────────────────────────────────────────────────
Réponds EXACTEMENT avec ce format :

"J'ai lu attentivement les sections critiques.

CONFIRMATION COMPRÉHENSION :
- Nombre de cas à tester = [11 / 13 / 15] ?
- Critère succès MAE moyen = [< 2 pips / < 5 pips / < 10 pips] ?
- Patterns SANS events à inclure = [OUI / NON] ?
- Formule à tester = [calculate_cluster_impact / calculate_double_wave_overlapping] ?
- Référence validation = [11 septembre MAE 0.29 pips / 11 septembre MAE 4.5 pips] ?

Si une réponse est fausse → je n'ai PAS lu attentivement → je relis."

═══════════════════════════════════════════════════════════════════

APRÈS VALIDATION QUIZ, ACTIONS :
────────────────────────────────────────────────────────────────
1. Créer répertoire scripts/session118/
2. Créer script validate_formula_s115.py (structure)
3. Proposer architecture validation (extraction impacts MT5, calcul prédictions, statistiques)
4. Attendre validation André
5. PUIS commencer implémentation (pas avant)

═══════════════════════════════════════════════════════════════════

⛔ INTERDICTIONS ABSOLUES :
────────────────────────────────────────────────────────────────
❌ Ne survole PAS les sections "GAP #1" et "Plan d'action Session 118"
❌ Ne propose RIEN avant d'avoir lu attentivement
❌ Ne commence AUCUN code avant validation architecture
❌ Ne teste PAS sur les 2 patterns SANS events (inutile)
❌ Ne dis PAS "ah désolé j'avais pas bien lu" après coup

═══════════════════════════════════════════════════════════════════

NE RÉPONDS RIEN D'AUTRE QUE LA CONFIRMATION QUIZ AVANT D'AVOIR 
LU ATTENTIVEMENT LES SECTIONS CRITIQUES.
```

---

## 📝 RÉPONSES ATTENDUES QUIZ

**Réponses correctes :**
- Nombre de cas à tester = **13**
- Critère succès MAE moyen = **< 5 pips**
- Patterns SANS events à inclure = **NON**
- Formule à tester = **calculate_double_wave_overlapping**
- Référence validation = **11 septembre MAE 0.29 pips** (Session 115)

**Notes :**
- 15 Double Wave détectés MAIS 2 SANS events → **13 validables**
- 11 septembre a 2 MAE différentes :
  - **0.29 pips** (Session 115 avec formule S115 complète)
  - **4.5 pips** (Session 117 avec scanner prix seul)
  - Référence = **0.29 pips** (formule S115)

---

## 🎯 OBJECTIFS SESSION 118

### **Objectif Principal**
Valider formule S115 `calculate_double_wave_overlapping()` sur 13 cas

### **Critères Succès**
- [ ] Formule testée sur 13 cas (100%)
- [ ] MAE moyen < 5 pips
- [ ] Rapport validation créé
- [ ] Paramètres finaux documentés

### **Livrables Attendus**
1. `scripts/session118/validate_formula_s115.py`
2. `scripts/session118/validation_report_s115.md`
3. `scripts/session118/validation_results.json`
4. `scripts/session118/validation_plots/` (graphiques)

---

## 📚 FICHIERS CRITIQUES

### **Documentation**
```
/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/01_VISION/MASTER_PLAN.md
  → Version 1.2 (mise à jour Session 117)

/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/99_SESSIONS/SESSION_117_HANDOFF.md
  → Handoff Session 117→118 (ce fichier guide la session)
```

### **Dataset**
```
/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session117/double_waves_enriched.json
  → 15 Double Wave enrichis (13 avec events, 2 sans)
```

### **Code Formule**
```
/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/src/core/cluster_impact_calculator.py
  → Fonction calculate_double_wave_overlapping() à tester
```

### **Base Données**
```
/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb
  → Prices, events, event_families
```

---

## ⚠️ PIÈGES À ÉVITER

### **Erreur #1 : Tester 15 cas au lieu de 13**
**Piège :** Dataset contient 15 Double Wave  
**Solution :** Exclure 2 patterns SANS events :
- 20 janvier 2025 : 87.1 pips
- 16 juillet 2025 : 101.6 pips

**Raison :** Formule S115 nécessite events causaux

### **Erreur #2 : Utiliser MAE 4.5 pips comme référence**
**Piège :** Session 117 a MAE 4.5 pips sur 11 sept  
**Solution :** Utiliser MAE **0.29 pips** (Session 115 avec formule complète)

**Raison :** Scanner S117 seul vs formule complète S115

### **Erreur #3 : Modifier formule avant tests**
**Piège :** Vouloir ajuster paramètres trop tôt  
**Solution :** Tester d'abord les 13 cas, PUIS ajuster si MAE > 5 pips

**Raison :** Décisions basées sur données empiriques

### **Erreur #4 : Extraction impacts MT5 incorrecte**
**Piège :** Calculer impact depuis mauvais baseline  
**Solution :** Utiliser graphiques `plots_double_wave/` pour vérifier

**Raison :** Impact = baseline → Wave2 peak (pas Wave1 peak)

---

## 📊 PLAN SESSION (5 ÉTAPES)

### **ÉTAPE 1 : Environnement** (20 min)
- Créer `scripts/session118/`
- Créer structure `validate_formula_s115.py`
- Charger `double_waves_enriched.json`
- Filtrer 13 cas avec events

### **ÉTAPE 2 : Impacts MT5** (30 min)
- Extraire fenêtre prix ±2h par cas
- Calculer impact réel (baseline → Wave2)
- Valider avec graphiques
- Stocker dict `real_impacts`

### **ÉTAPE 3 : Prédictions S115** (45 min)
- Pour chaque cas : appliquer formule
- Calculer MAE par cas
- Stocker résultats DataFrame

### **ÉTAPE 4 : Statistiques** (30 min)
- MAE moyen, RMSE, R²
- Identifier outliers
- Créer graphiques

### **ÉTAPE 5 : Ajustements (si nécessaire)** (45 min)
- SI MAE > 5 pips : ajuster paramètres
- SINON : valider paramètres actuels

---

## 💡 CONSEILS

### **Avant de Coder**
1. ✅ Lire attentivement MASTER_PLAN.md (GAP #1)
2. ✅ Lire attentivement SESSION_117_HANDOFF.md (plan action)
3. ✅ Répondre au QUIZ correctement
4. ✅ Proposer architecture et ATTENDRE validation

### **Pendant Développement**
1. ✅ Tester sur 11 septembre d'abord (référence connue)
2. ✅ Vérifier extraction impacts MT5 avec graphiques
3. ✅ Logger chaque étape pour debug
4. ✅ Documenter au fur et à mesure

### **En Cas de Problème**
1. Si MAE > 10 pips → vérifier extraction impacts réels
2. Si formule échoue → vérifier events causaux dans JSON
3. Si bloqué → consulter graphiques `plots_double_wave/`
4. Si doute → demander clarification André

---

## 🎯 VALIDATION FIN SESSION 118

### **Checklist Succès**
- [ ] 13 cas testés (100%)
- [ ] MAE moyen < 5 pips
- [ ] Rapport créé avec statistiques
- [ ] Graphiques générés
- [ ] Paramètres finaux documentés
- [ ] MASTER_PLAN.md mis à jour
- [ ] SESSION_119_HANDOFF.md créé

### **Métriques Attendues**
- MAE moyen : < 5 pips (objectif)
- RMSE : < 7 pips
- R² : > 0.85
- Max outliers : 2-3 cas

---

**Auteur :** André Valentin avec Claude  
**Date :** 07 novembre 2025  
**Version :** 1.0  
**Session :** 117 → 118
