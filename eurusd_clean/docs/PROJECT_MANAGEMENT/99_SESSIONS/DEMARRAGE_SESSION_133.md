# 🚀 DÉMARRAGE SESSION 133 - Intégration DoubleWave dans Planificateur

**Date :** 13 novembre 2025  
**Objectif Session :** Intégrer module DoubleWave dans le Planificateur avec flowchart validé

---

## 📋 CHECKLIST DÉMARRAGE OBLIGATOIRE

### **1. Lecture Documents Critiques (ORDRE STRICT) :**
- [ ] SESSION_132_HANDOFF.md
- [ ] MASTER_PLAN.md  
- [ ] scripts/session131/README.md
- [ ] scripts/session132/flowchart_doublewave.md
- [ ] src/core/doublewave_prediction.py

### **2. Quiz Compréhension :**
**Q1 :** Que faire avec DoubleWave_Cascade ?  
**R1 :** EXCLURE systématiquement (variabilité 7.49×)

**Q2 :** Amplification pour Overlap standard (score 300, 8 events US) ?  
**R2 :** 0.1201

**Q3 :** Amplification pour Superposition (score 650, 20 events ECB+US) ?  
**R3 :** 0.0128

**Q4 :** Que faire avec Cascade score 50 (Serbie/Macédoine) ?  
**R4 :** EXCLURE (pays périphériques)

**Q5 :** Première étape AVANT intégration ?  
**R5 :** Créer flowchart Planificateur et le valider

✅ **Quiz réussi si toutes réponses correctes.**

---

## 🎯 OBJECTIFS SESSION 133

### **Minimum (2h) :**
1. Créer flowchart Planificateur (structure complète)
2. Intégrer module DoubleWave (code fonctionne)
3. Tester 1 date avec succès

### **Optimal (4h) :**
1. Créer flowchart Planificateur (structure complète)
2. Intégrer module DoubleWave dans Planificateur
3. Tester 3+ dates (Overlap, Superposition, Single Wave)
4. Interface affiche pattern détecté
5. Documentation utilisateur créée

---

## 🔑 POINTS CRITIQUES À RETENIR

### **Architecture Planificateur :**
- **Entrée :** Date + timezone (Europe/Zurich)
- **Sortie :** Prédiction impact avec pattern détecté
- **Logique :** 
  1. Charger events date donnée
  2. Détecter pattern (Single/Double)
  3. Si DoubleWave détecté → predict_doublewave_overlap()
  4. Si Single Wave → formule universelle (R²)
  5. Afficher prédiction + pattern + justification

### **Module DoubleWave :**
- **Fonction :** `predict_doublewave_overlap(events, debug=False)`
- **Retour :** dict avec prediction, amplification, status, reason, pattern_type
- **Patterns prédictibles :**
  - Overlap standards (score 150-350, 5-10 events) → amp 0.1201
  - Overlap superposition (score 600+, 15+ events) → amp 0.0128
- **Patterns exclus :**
  - Cascade (tous) → variabilité trop haute
  - Overlap score < 150 ou > 350 (hors superposition)
  - Overlap events < 5 ou > 10 (hors superposition)
  - Overlap pays périphériques (Serbie, Macédoine, etc.)

### **Tests Requis :**
1. **2025-09-11** (Superposition ECB+US) → amp 0.0128
2. **2024-09-12** (Overlap standard US) → amp 0.1201
3. **2024-12-18** (Single Wave Fed) → formule universelle

---

## 📁 STRUCTURE FICHIERS SESSION 133

```
scripts/session133/
├── README.md                          # Documentation session
├── flowchart_planificateur.md        # Flowchart AVANT intégration
├── test_planificateur.py             # Tests 3 dates
└── integration_doublewave.md         # Notes intégration
```

---

## ⚠️ PIÈGES À ÉVITER

1. ❌ **Coder sans flowchart validé** → Créer flowchart AVANT toute ligne de code
2. ❌ **Utiliser pattern Single_Wave_Fort** → MAE 39k pips (inutilisable)
3. ❌ **Oublier timezone** → Toujours `tz='Europe/Zurich'` pour prices_bern
4. ❌ **Mélanger approches amplification** → DoubleWave = amp fixes, Single Wave = R²
5. ❌ **Survol des sections critiques** → Lire mot par mot

---

## 🚦 PRÊT À DÉMARRER ?

**Avant de coder, confirmer :**
- ✅ Quiz réussi (5/5)
- ✅ 5 documents lus dans l'ordre
- ✅ Points critiques compris
- ✅ Flowchart Session 132 consulté

**Première action :** Créer `scripts/session133/flowchart_planificateur.md`

---

**Bonne session ! 🎯**

---

**Auteur :** André Valentin avec Claude  
**Session :** 133  
**Date :** 13 novembre 2025  
**Statut :** ✅ PRÊT À DÉMARRER
