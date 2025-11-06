# 📋 TEMPLATE HANDOFF SESSION - Standard

**Version :** 1.0  
**Date :** 06 novembre 2025 - Session 114

---

## 🎯 OBJECTIF

Template standardisé pour créer handoff entre sessions.

**Principe :** Chaque session se termine par création du fichier `SESSION_XXX_HANDOFF.md` qui donne instructions PRÉCISES pour session suivante.

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

### **1. OBLIGATOIRE (10-15k tokens)**
```
01_VISION/MASTER_PLAN.md           (5-8k)
99_SESSIONS/SESSION_XXX_HANDOFF.md (ce fichier, 3k)
```

### **2. SELON CONTEXTE (10-20k tokens)**

**Si développement architecture :**
```
02_ARCHITECTURE/MODULES_STATUS.md  (15k)
02_ARCHITECTURE/UML_DIAGRAM.md     (8k)
```

**Si développement formules :**
```
03_FORMULAS/VALIDATED_FORMULAS.md  (10k)
```

**Si développement fonctionnel :**
```
04_KANBAN/BACKLOG.md               (10k)
src/core/[module pertinent].py
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
[Chemin fichier 1]
[Chemin fichier 2]
```

**Documentation :**
```
[Chemin fichier 1]
[Chemin fichier 2]
```

**Tests :**
```
[Chemin fichier 1]
[Chemin fichier 2]
```

---

## 📁 FICHIERS À MODIFIER SESSION XXX+1

**Priorité 1 (DOIT) :**
```
[Fichier 1] - [Raison modification]
[Fichier 2] - [Raison modification]
```

**Priorité 2 (DEVRAIT) :**
```
[Fichier 1] - [Raison modification]
```

**Priorité 3 (POURRAIT) :**
```
[Fichier 1] - [Raison modification]
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
3. Consulter `[fichier référence]`

---

## 🔄 MISE À JOUR DOCUMENTATION

**À mettre à jour Session XXX+1 :**
```
01_VISION/MASTER_PLAN.md
  → Section "État actuel" (ajouter accomplissements)
  → Section "Roadmap" (marquer Session XXX complétée)

02_ARCHITECTURE/MODULES_STATUS.md
  → [Si modifications modules]

04_KANBAN/BACKLOG.md
  → Déplacer tâches complétées vers DONE.md
```

---

## 🚀 COMMANDE DÉMARRAGE SESSION XXX+1

```
Bonjour Claude,

Je démarre la Session XXX+1.

J'ai lu :
- 01_VISION/MASTER_PLAN.md
- 99_SESSIONS/SESSION_XXX_HANDOFF.md

Mission : [Répéter objectif principal]

Peux-tu [action concrète à faire en premier] ?
```

---

**Auteur :** [Nom]  
**Date :** [JJ Mois AAAA]  
**Tokens Session XXX :** XX,XXX / 190,000 (XX%)  
**Statut :** ✅ HANDOFF COMPLET
```

---

## ✅ CHECKLIST CRÉATION HANDOFF

Avant de finaliser handoff, vérifier :

- [ ] Objectif Session XXX+1 clair et mesurable
- [ ] Fichiers à lire listés (avec tailles tokens)
- [ ] Plan d'action avec étapes concrètes
- [ ] Critères de succès définis
- [ ] Points d'attention documentés
- [ ] Conseils pour éviter erreurs
- [ ] Commande démarrage fournie

---

## 📊 EXEMPLES BON vs MAUVAIS HANDOFF

### **❌ MAUVAIS HANDOFF**
```
Objectif : Continuer le développement
Plan : Voir ce qu'on peut faire
Fichiers : Lire la documentation
```
→ Trop vague, pas actionnable

### **✅ BON HANDOFF**
```
Objectif : Implémenter calculate_total_impact_overlapping()
         pour atteindre MAE < 2 pips sur 11 sept

Plan :
  Étape 1 (30min): Analyser interactions clusters (fichier X)
  Étape 2 (60min): Coder fonction (tests unitaires)
  Étape 3 (30min): Valider sur 11 sept + 2 autres cas

Fichiers : MASTER_PLAN.md (8k) + cluster_impact_calculator.py

Critère succès : MAE < 2 pips ET tests passent
```
→ Précis, mesurable, actionnable

---

## 📝 NOTES D'UTILISATION

### **Quand créer handoff ?**
**FIN de chaque session**, avant de finaliser.

### **Qui le crée ?**
Claude, avec validation André

### **Combien de temps ?**
10-15 minutes fin de session

### **Où le stocker ?**
`docs/PROJECT_MANAGEMENT/99_SESSIONS/SESSION_XXX_HANDOFF.md`

### **Quand le supprimer ?**
Après Session XXX+2 (garder seulement N et N+1)

---

**Version :** 1.0  
**Créé par :** André Valentin avec Claude  
**Session :** 114  
**Date :** 06 novembre 2025
