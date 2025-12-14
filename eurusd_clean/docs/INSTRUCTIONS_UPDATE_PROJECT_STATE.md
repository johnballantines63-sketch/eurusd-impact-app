# INSTRUCTIONS : MISE À JOUR project_state_new.md

**Date :** 3 novembre 2025  
**Fichier cible :** `eurusd_clean/docs/project_state_new.md`

---

## 📝 MODIFICATIONS À APPLIQUER

### 1. Mettre à jour l'en-tête (lignes 1-6)

**REMPLACER :**
```markdown
# 📊 PROJECT STATE - EUR/USD NEWS IMPACT CALCULATOR

**Dernière mise à jour :** 3 novembre 2025 - Session 107  
**Status :** ✅✅✅ MÉTHODE INVERSION CHOISIE (Corrélation +0.346) - CALIBRATION NÉCESSAIRE  
**Version Planner :** v2.6 (amp=2.5) - FORMULES S51-55 CONFIRMÉES  
**Prochaine étape :** Session 108 - Valider Méthode Inversion sur Cluster #1 (11 dates) + Calibration formule
```

**PAR :**
```markdown
# 📊 PROJECT STATE - EUR/USD NEWS IMPACT CALCULATOR

**Dernière mise à jour :** 3 novembre 2025 - Pre-Session 109  
**Status :** ⏳ PARENTHÈSE MÉTHODOLOGIQUE - ANALYSE EXHAUSTIVE  
**Version Planner :** v2.6 (amp=2.5) - FORMULES S51-55 CONFIRMÉES  
**Prochaine étape :** Session 109 - Tester 96 combinaisons métriques/corrélations → Identifier MEILLEURS outils
```

---

### 2. Ajouter section RÈGLE CRITIQUE après l'en-tête

**INSÉRER APRÈS** la ligne `---` (ligne 8), **AVANT** `## 🗂️ RÉFÉRENCE RAPIDE` :

```markdown
## 🎯 RÈGLE CRITIQUE DOCUMENTATION

> ⚠️ **FICHIER UNIQUE À UTILISER :** `project_state_new.md` (MINUSCULES)  
> **CONFUSION RÉCURRENTE :** Ne pas confondre avec `PROJECT_STATE.md` (MAJUSCULES - ancien)  
> Ce fichier `project_state_new.md` est la **SEULE source de vérité** du projet.  
> Mettre à jour directement ce fichier, ne pas créer de fichiers fragmentés.

---
```

---

### 3. Ajouter section SESSION 109

**INSÉRER APRÈS** la section RÈGLE CRITIQUE, **AVANT** `## 🗂️ RÉFÉRENCE RAPIDE` :

```markdown
## 🔬 SESSION 109 : PARENTHÈSE MÉTHODOLOGIQUE (EN ATTENTE)

### Type : ANALYSE EXHAUSTIVE MÉTRIQUES & CORRÉLATIONS

**Contexte :**
Questions André (3 nov 2025) ont révélé limitation méthodologique Session 108 :
- ⚠️ On n'a testé qu'UNE métrique tendance (R² linéaire) parmi 12+ disponibles
- ⚠️ On n'a testé qu'UNE corrélation (Pearson linéaire) parmi 8+ disponibles
- ⚠️ Risque : passer à côté vraie relation par mauvais choix outils

**Décision :** 
ANALYSE EXHAUSTIVE avant de continuer
- ✅ Tester 96 combinaisons (12 métriques × 8 corrélations)
- ✅ Identifier MEILLEURS outils mathématiques
- ✅ PUIS les utiliser pour baseline C#1 et suite

### Objectif Session 109

**Répondre à 2 questions critiques :**

1. **Existe-t-il UNE métrique tendance qui prédit amp ?**
   - R² linéaire (actuel) : r=+0.084 ❌
   - ADX, Hurst, Spearman, Pente, etc. : À tester
   
2. **Existe-t-il UNE méthode corrélation plus pertinente ?**
   - Pearson linéaire (actuel) : r=+0.084 ❌
   - Spearman, Polynomial, Kendall, etc. : À tester

### Plan 4 Phases

**Phase 1 (2-3h) :** Calculer 12 métriques tendance sur 17 dates  
**Phase 2 (1-2h) :** Tester 96 combinaisons (12 × 8)  
**Phase 3 (30min) :** Sélectionner Top 3 selon p-value, force, robustesse  
**Phase 4 (1-2h) :** Valider & décider quelle approche adopter

### Métriques à Tester (12)

**Linéaires :**
1. R² linéaire (actuel)
2. R Pearson (avec signe)
3. Pente (pips/heure)
4. Durée tendance

**Non-linéaires :**
5. R² polynomial deg 2
6. R² polynomial deg 3
7. Spearman Rho

**Trading :**
8. **ADX** (Average Directional Index) ⭐
9. Amplitude tendance
10. Volatilité tendance

**Avancées :**
11. **Hurst Exponent** (persistance) ⭐
12. Autocorrélation Lag 1

### Corrélations à Tester (8)

1. Pearson (actuel)
2. **Spearman** (monotone) ⭐
3. Kendall Tau (robuste)
4. Régression linéaire
5. **Polynomial deg 2** (U inversé) ⭐
6. Polynomial deg 3
7. Distance Correlation
8. Mutual Information

### Résultats Possibles

**Scénario 1 : Jackpot ✅✅✅**
```
Métrique X + Corrélation Y : r > 0.6, p < 0.01
→ Excellente relation trouvée !
→ Session 110 : Implémentation formule dynamique
```

**Scénario 2 : Modéré ✅**
```
Métrique Z + Corrélation W : r = 0.4-0.6, p < 0.05
→ Relation significative mais modérée
→ Comparer avec amp par cluster
```

**Scénario 3 : Rien ❌**
```
Toutes combinaisons : p > 0.05
→ AUCUNE variable ne prédit amp
→ Confirme Session 108
→ Retour amp par cluster fixe
→ MAIS on SAIT qu'on a tout testé !
```

### Documentation Créée (Pre-Session 109)

**Fichiers disponibles :**
1. `SESSION_109_PLAN.md` - Plan détaillé 4 phases ✅
2. `METHODOLOGIES_ALTERNATIVES.md` - Catalogue 12 métriques + 8 corrélations ✅
3. `MESSAGE_SESSION_108_TO_109.md` - Handoff détaillé ✅
4. `SESSION_109_CHECKLIST.md` - Checklist complète ✅

### Après Session 109

**Si métrique trouvée :**
- Session 110 : Implémentation formule amp = f(métrique)
- Baseline C#1 avec meilleure métrique
- Tests comparatifs

**Si rien trouvé :**
- Session 110 : Retour amp par cluster fixe
- Baseline C#1 = 1.5, C#3 = 2.5
- **Décision éclairée : on a tout testé scientifiquement**

---
```

---

## ✅ RÉSUMÉ DES CHANGEMENTS

**3 modifications à faire :**

1. **En-tête** : Mise à jour date + status + prochaine étape
2. **Nouvelle section** : RÈGLE CRITIQUE DOCUMENTATION (éviter confusion fichier)
3. **Nouvelle section** : SESSION 109 complète (parenthèse méthodologique)

**Emplacement :**
- Sections à ajouter : **Après** `---`, **AVANT** `## 🗂️ RÉFÉRENCE RAPIDE`

---

## 📝 MÉTHODE RAPIDE

**Option A : Copier-coller manuel (recommandé)**
1. Ouvrir `project_state_new.md`
2. Remplacer lignes 1-6 par nouvel en-tête
3. Après ligne 8 (`---`), insérer RÈGLE CRITIQUE
4. Après RÈGLE CRITIQUE, insérer SESSION 109
5. Sauvegarder

**Option B : Utiliser find/replace éditeur**
1. Chercher : `**Dernière mise à jour :** 3 novembre 2025 - Session 107`
2. Remplacer par : `**Dernière mise à jour :** 3 novembre 2025 - Pre-Session 109`
3. Puis insérer manuellement les deux nouvelles sections

---

## 🎯 VÉRIFICATION FINALE

**Après modification, vérifier :**
- [ ] En-tête mis à jour (Pre-Session 109)
- [ ] Section RÈGLE CRITIQUE présente
- [ ] Section SESSION 109 présente et complète
- [ ] Reste du fichier inchangé
- [ ] Pas de duplication de sections
- [ ] Fichier cohérent

---

**FIN INSTRUCTIONS**

*Document créé : 3 novembre 2025*  
*Instructions de mise à jour project_state_new.md*  
*3 modifications à appliquer*
