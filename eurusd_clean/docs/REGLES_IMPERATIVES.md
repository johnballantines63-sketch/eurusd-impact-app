# 📋 RÈGLES IMPÉRATIVES - SESSION 53+

**AVANT TOUTE ACTION DANS CHAQUE NOUVELLE SESSION**

---

## 🚨 RÈGLE #1 : LECTURE OBLIGATOIRE

### Ordre de Lecture (NON NÉGOCIABLE)

```
1. 📊 AFFICHER TOKENS INITIAL

2. 📚 LIRE PROJECT_STATE.md (INTÉGRALEMENT - 30 min)
   Chemin : eurusd_clean/docs/PROJECT_STATE.md
   Contenu : État complet projet, formules validées, problèmes résolus

3. 📚 LIRE RAPPORT SESSION PRÉCÉDENTE (20 min)
   Ex : SESSION52_RAPPORT_FINAL.md
   Contenu : Tout ce qui a été accompli

4. 📚 LIRE MESSAGE CONTINUATION (15 min)
   Ex : MESSAGE_SESSION52_SESSION53.md
   Contenu : Mission exacte, plan d'action

5. 📊 AFFICHER TOKENS APRÈS LECTURE
```

**⚠️ SI NON FAIT → L'UTILISATEUR DOIT ARRÊTER CLAUDE**

---

## 📊 RÈGLE #2 : AFFICHAGE TOKENS

### Quand Afficher

```
✅ Au démarrage (avant toute action)
✅ Après lecture documentation
✅ Après chaque phase de travail
✅ Avant toute action > 10k tokens
✅ Avant documentation finale
```

### Format

```
📊 TOKENS : X / 190,000 (Y%)
```

### Limite Critique

```
🚨 ARRÊTER À 110,000 TOKENS

À 110k tokens :
- STOP toute implémentation/test
- COMMENCER documentation finale
- Créer rapport session
- Créer message continuation
- Mettre à jour PROJECT_STATE.md
```

---

## 🎯 RÈGLE #3 : MÉTHODOLOGIE

### Ordre Impératif

```
1. 📚 LIRE documentation complète
2. 🧪 TESTER / VALIDER (avant corriger)
3. 🔧 IMPLÉMENTER (après validation)
4. 🧪 TESTER implémentation
5. 📝 DOCUMENTER résultats
```

### Interdictions Absolues

```
❌ Commencer sans lire PROJECT_STATE.md intégralement
❌ Implémenter avant valider
❌ Modifier code sans backup
❌ Dépasser 110k tokens sans documenter
❌ Deviner au lieu de tester
❌ Explorer sans raison (gaspillage tokens)
```

---

## 📁 RÈGLE #4 : CHEMINS & FICHIERS

### Chemin Documentation

```
/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/

TOUJOURS chercher documentation ICI en premier !
```

### Fichiers Essentiels

```
📂 eurusd_clean/docs/
├── PROJECT_STATE.md ⭐⭐⭐ (LIRE EN PREMIER)
├── SESSION[N]_RAPPORT_FINAL.md ⭐⭐⭐
├── MESSAGE_SESSION[N]_SESSION[N+1].md ⭐⭐⭐
├── FORMULE_*_VALIDATION.md ⭐⭐
└── ... (autres docs)
```

### Si Fichier Non Trouvé

```
1. Vérifier chemin ci-dessus
2. Si toujours absent → DEMANDER à l'utilisateur
3. NE PAS faire de recherches qui consomment tokens
```

---

## 🔧 RÈGLE #5 : BACKUPS

### Avant Toute Modification

```
TOUJOURS créer backup avec timestamp :

fichier.py → fichier.py.backup_session[N]_YYYYMMDD_HHMMSS

Exemple :
latency_analyzer.py → latency_analyzer.py.backup_session52_20251023_152910
```

---

## 📝 RÈGLE #6 : DOCUMENTATION

### Fichiers à Créer En Fin de Session

```
1. SESSION[N]_RAPPORT_FINAL.md
   → Tout ce qui a été accompli
   → Résultats, métriques, découvertes

2. MESSAGE_SESSION[N]_SESSION[N+1].md
   → Mission pour prochaine session
   → Checklist, règles, plan

3. PROJECT_STATE.md (mise à jour)
   → État actuel projet
   → Formules validées, problèmes résolus
```

---

## 📊 RÈGLE #7 : EFFICACITÉ

### Sessions Réussies (95% efficacité)

```
Sessions 51-52 :
✅ Ont lu PROJECT_STATE.md en premier
✅ Ont affiché tokens régulièrement
✅ Ont testé avant corriger
✅ Ont documenté au fur et à mesure

Résultat : Formules validées, problèmes résolus
```

### Session Échouée (0% efficacité)

```
Session 49 :
❌ N'a PAS lu PROJECT_STATE.md
❌ N'a PAS affiché tokens
❌ A exploré inutilement (70k tokens perdus)
❌ A deviné au lieu de tester

Résultat : 0 objectif atteint, session perdue
```

---

## 🎯 CHECKLIST RAPIDE

```
Session Nouvelle :
- [ ] 📊 Afficher tokens initial
- [ ] 📚 Lire PROJECT_STATE.md (intégralement)
- [ ] 📚 Lire rapport session précédente
- [ ] 📚 Lire message continuation
- [ ] 📊 Afficher tokens après lecture
- [ ] 🎯 Suivre plan de la mission
- [ ] 📊 Afficher tokens régulièrement
- [ ] ⏱️ Arrêter à 110k pour documenter
- [ ] 📝 Créer documentation finale
- [ ] 📊 Afficher tokens finaux
```

---

## 💡 PRINCIPES FONDAMENTAUX

### Ce Qui Marche

```
✅ Lire AVANT d'agir
✅ Tester AVANT de corriger
✅ Documenter au fur et à mesure
✅ Afficher tokens régulièrement
✅ Suivre méthodologie stricte
```

### Ce Qui Ne Marche Pas

```
❌ Deviner sans tester
❌ Explorer sans raison
❌ Ignorer documentation
❌ Négliger affichage tokens
❌ Corriger sans valider
```

---

## 📢 MESSAGE UTILISATEUR

```
Si Claude ne suit PAS ces règles :

1. ARRÊTE Claude immédiatement
2. Dis : "As-tu lu PROJECT_STATE.md intégralement ?"
3. Dis : "As-tu affiché les tokens ?"
4. Dis : "C'est OBLIGATOIRE avant toute action"

Ne laisse pas Claude agir sans avoir lu et affiché tokens.
```

---

## 🎓 LEÇONS HISTORIQUES

**Session 49 (Échec) :**
- Pas lu docs → 70k tokens perdus
- Pas affiché tokens → dépassement inconscient
- Exploré au hasard → 0 objectif atteint

**Sessions 51-52 (Succès) :**
- Lu docs d'abord → direction claire
- Affiché tokens → gestion stricte
- Testé méthodiquement → formules validées

**CONCLUSION : RESPECTER CES RÈGLES = SUCCÈS GARANTI**

---

*Règles établies après analyse Sessions 48-52*  
*Date : 23 octobre 2025*  
*Efficacité prouvée : 95% (Sessions 51-52)*  
*À appliquer : TOUTES sessions futures*
