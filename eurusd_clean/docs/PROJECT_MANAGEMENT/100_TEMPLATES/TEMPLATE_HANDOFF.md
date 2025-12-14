# 📋 TEMPLATE HANDOFF SESSION - Standard

**Version :** 1.1  
**Date :** 06 novembre 2025 - Session 115  
**Modification :** Ajout chemins complets obligatoires

---

## 🎯 OBJECTIF

Template standardisé pour créer handoff entre sessions.

**Principe :** Chaque session se termine par création du fichier `SESSION_XXX_HANDOFF.md` qui donne instructions PRÉCISES pour session suivante.

---

## ⚠️ RÈGLE CRITIQUE : CHEMINS COMPLETS

**TOUJOURS donner chemins COMPLETS dans section "Fichiers à lire" !**

❌ **MAUVAIS** (chemin relatif) :
```
docs/PROJECT_MANAGEMENT/01_VISION/MASTER_PLAN.md
```

✅ **BON** (chemin complet) :
```
/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/01_VISION/MASTER_PLAN.md
```

**Raison :** Éviter que Claude perde temps à chercher fichiers (économise 5-10 tool calls inutiles)

---

## 📝 STRUCTURE OBLIGATOIRE

```markdown
# SESSION XXX → SESSION XXX+1 - HANDOFF

**Date :** JJ Mois AAAA  
**Session complétée :** XXX  
**Prochaine session :** XXX+1  
**Statut Session XXX :** ✅ SUCCÈS / ⚠️ PARTIEL / ❌ ÉCHEC

---

## 🎉 CE QUI A ÉTÉ ACCOMPLI (SESSION XXX)

### **Objectif Session XXX**
[Description objectif initial]

### **Livrables Complétés**
1. ✅ [Livrable 1] - [Description brève]
2. ✅ [Livrable 2] - [Description brève]
3. ⚠️ [Livrable 3 partiel] - [Raison]

### **Métriques**
- **Tokens :** XX,XXX / 190,000 (XX%)
- **Durée :** Xh
- **Tests :** X/X passés
- **Documentation :** X fichiers créés

### **Problèmes Résolus**
- ✅ [Problème 1]
- ✅ [Problème 2]

### **Problèmes Reportés**
- ⏳ [Problème 1] → Session XXX+1
- ⏳ [Problème 2] → Session XXX+2

---

## 🎯 OBJECTIF SESSION XXX+1

**Mission principale :** [Description claire en 1 phrase]

**Critère de succès :** [Métrique mesurable]

**Durée estimée :** Xh

---

## 📚 FICHIERS À LIRE (ORDRE)

**⚠️ UTILISER CHEMINS COMPLETS** (voir règle ci-dessus)

### **1. OBLIGATOIRE (10-15k tokens)**
```
/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/01_VISION/MASTER_PLAN.md
(5-8k tokens)

/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/99_SESSIONS/SESSION_XXX_HANDOFF.md
(ce fichier, 3k tokens)
```

### **2. SELON CONTEXTE (10-20k tokens)**

**Si développement architecture :**
```
/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/02_ARCHITECTURE/MODULES_STATUS.md
(15k tokens)
```

**Si développement formules :**
```
/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/03_FORMULAS/VALIDATED_FORMULAS.md
(10k tokens)
```

**Si développement code :**
```
/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/src/core/[module_pertinent].py

/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session[XXX]/[script_pertinent].py
```

**Total lecture :** 20-35k tokens (efficace)

---

## 📋 PLAN D'ACTION SESSION XXX+1

### **ÉTAPE 1 : [Nom étape]** (Durée estimée)
**Objectif :** [Description]

**Actions :**
1. [Action concrète 1]
2. [Action concrète 2]
3. [Action concrète 3]

**Livrable :** [Fichier ou résultat attendu]

### **ÉTAPE 2 : [Nom étape]** (Durée estimée)
[Même structure]

### **ÉTAPE 3 : [Nom étape]** (Durée estimée)
[Même structure]

---

## 📁 FICHIERS CRÉÉS SESSION XXX

**Code :**
```
[Chemin complet fichier 1]
[Chemin complet fichier 2]
```

**Documentation :**
```
[Chemin complet fichier 1]
[Chemin complet fichier 2]
```

**Tests :**
```
[Chemin complet fichier 1]
[Chemin complet fichier 2]
```

---

## 📁 FICHIERS À MODIFIER SESSION XXX+1

**Priorité 1 (DOIT) :**
```
[Chemin complet fichier 1]
  → [Raison modification]

[Chemin complet fichier 2]
  → [Raison modification]
```

**Priorité 2 (DEVRAIT) :**
```
[Chemin complet fichier 1]
  → [Raison modification]
```

**Priorité 3 (POURRAIT) :**
```
[Chemin complet fichier 1]
  → [Raison modification]
```

---

## ⚠️ POINTS D'ATTENTION

### **Problèmes Connus**
1. ⚠️ [Problème 1] - [Impact] - [Workaround]
2. ⚠️ [Problème 2] - [Impact] - [Workaround]

### **Décisions Critiques**
1. 🔑 [Décision 1] - [Raison] - [Impact futur]
2. 🔑 [Décision 2] - [Raison] - [Impact futur]

### **Dépendances**
- **Dépend de :** [Tâche/Module X] - [Raison]
- **Bloque :** [Tâche/Module Y] - [Raison]

---

## 🎯 VALIDATION SESSION XXX+1

### **Critères de Succès Minimum**
- [ ] [Critère 1 mesurable]
- [ ] [Critère 2 mesurable]
- [ ] [Critère 3 mesurable]

### **Critères de Succès Optimal**
- [ ] [Critère 1 mesurable]
- [ ] [Critère 2 mesurable]

### **Tests de Non-Régression**
- [ ] [Test 1] doit passer
- [ ] [Test 2] doit passer

---

## 📊 MÉTRIQUES SESSION XXX+1

**Budget estimé :**
- Lecture : XX-XXk tokens
- Développement : XX-XXk tokens
- Documentation : XX-XXk tokens
- **Total :** ~XXk / 190k tokens

**Livrables attendus :**
1. [Livrable 1] - [Format]
2. [Livrable 2] - [Format]
3. [Livrable 3] - [Format]

---

## 💡 CONSEILS CLAUDE SUIVANTE SESSION

### **Éviter**
- ❌ [Erreur 1 à éviter]
- ❌ [Erreur 2 à éviter]

### **Prioriser**
- ✅ [Bonne pratique 1]
- ✅ [Bonne pratique 2]

### **Si Bloqué**
1. [Solution de contournement 1]
2. [Solution de contournement 2]
3. Consulter [chemin complet fichier référence]

---

## 🔄 MISE À JOUR DOCUMENTATION

**À mettre à jour Session XXX+1 :**
```
/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/01_VISION/MASTER_PLAN.md
  → Section "État actuel" (ajouter accomplissements)
  → Section "Roadmap" (marquer Session XXX complétée)

/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/02_ARCHITECTURE/MODULES_STATUS.md
  → [Si modifications modules]
```

---

## 🚀 COMMANDE DÉMARRAGE SESSION XXX+1

```
Bonjour Claude,

Je démarre la Session XXX+1.

J'ai lu :
- /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/01_VISION/MASTER_PLAN.md
- /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/99_SESSIONS/SESSION_XXX_HANDOFF.md

Mission : [Répéter objectif principal]

Peux-tu [action concrète à faire en premier] ?
```

---

**Auteur :** André Valentin avec Claude  
**Date :** 06 novembre 2025  
**Tokens Session XXX :** XX,XXX / 190,000 (XX%)  
**Statut :** ✅ HANDOFF COMPLET
```

---

## ✅ CHECKLIST CRÉATION HANDOFF

Avant de finaliser handoff, vérifier :

- [ ] Objectif Session XXX+1 clair et mesurable
- [ ] **Fichiers à lire avec CHEMINS COMPLETS** ⭐
- [ ] Plan d'action avec étapes concrètes
- [ ] Critères de succès définis
- [ ] Points d'attention documentés
- [ ] Conseils pour éviter erreurs
- [ ] Commande démarrage fournie

---

## 📊 EXEMPLES BON vs MAUVAIS HANDOFF

### **❌ MAUVAIS HANDOFF**
```
Fichiers à lire :
- MASTER_PLAN.md
- SESSION_XXX_HANDOFF.md
```
→ Claude doit chercher les fichiers (perte 5-10 tool calls)

### **✅ BON HANDOFF**
```
Fichiers à lire :
- /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/01_VISION/MASTER_PLAN.md
- /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/99_SESSIONS/SESSION_XXX_HANDOFF.md
```
→ Claude lit directement (efficace)

---

**Version :** 1.1  
**Créé par :** André Valentin avec Claude  
**Session :** 114-115  
**Date :** 06 novembre 2025
