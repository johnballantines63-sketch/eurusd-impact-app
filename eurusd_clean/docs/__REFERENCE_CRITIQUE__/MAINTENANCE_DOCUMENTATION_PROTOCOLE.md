# 🔄 MAINTENANCE DOCUMENTATION - PROTOCOLE PERMANENT

**Date création:** 05 novembre 2025  
**Statut:** PROTOCOLE OBLIGATOIRE  
**Principe:** Documentation synchronisée avec progression code

---

## 🎯 OBJECTIF

**Problème à éviter:**
> Documentation obsolète qui ne reflète plus l'état réel du projet

**Solution:**
> Système de maintenance automatique basé sur triggers

**Règle d'or:**
> À CHAQUE changement significatif → Mise à jour documentation immédiate

---

## 📋 TRIGGERS DE MISE À JOUR

### 🔴 TRIGGER 1: Nouvelle Formule Validée

**QUAND:** Formule testée et précision > 90%

**FICHIERS À METTRE À JOUR (dans l'ordre):**

1. **`METHODES_VALIDEES.md`** ⭐⭐⭐
   ```markdown
   Ajouter dans section appropriée:
   ### X. Formule [NOM] (Session [N])
   
   **Précision:** XX.X% ✅✅✅
   
   **Fonction:**
   ```python
   function_name(params)
   ```
   
   **Usage:** Description
   **Validation:** Tests effectués
   **Fichier:** Emplacement code
   ```

2. **`PROGRESSION_PROJET.md`** ⭐⭐⭐
   ```markdown
   Mettre à jour section "✅ ÉTAPES VALIDÉES"
   Ajouter ligne dans tableau formules:
   | Formule X | XX.X% | Session N | ✅ GOLD |
   ```

3. **`CONTINUITE_PROJET_SESSION_XXX.md`** ⭐⭐
   ```markdown
   Ajouter dans section acquis correspondante
   Mettre à jour métriques progression
   ```

4. **`PROJECT_STATE.md`** ⭐
   ```markdown
   Mettre à jour section "Formules validées"
   Incrémenter % progression
   ```

**CHECKLIST:**
- [ ] Formule ajoutée METHODES_VALIDEES.md
- [ ] Tableau mis à jour PROGRESSION_PROJET.md
- [ ] Continuité documentée
- [ ] PROJECT_STATE actualisé
- [ ] Tests résultats documentés

---

### 🔴 TRIGGER 2: Nouvelle Session Complétée

**QUAND:** Session terminée avec résultats

**FICHIERS À METTRE À JOUR (dans l'ordre):**

1. **`SESSION_XXX_RAPPORT_FINAL.md`** ⭐⭐⭐ (CRÉER)
   ```markdown
   # SESSION XXX - RAPPORT FINAL
   
   **Objectifs:** [Ce qui était prévu]
   **Réalisations:** [Ce qui a été fait]
   **Problèmes résolus:** [Liste]
   **Fichiers créés/modifiés:** [Liste]
   **Tests:** [Résultats]
   **Prochaine session:** [TODO]
   ```

2. **`PROGRESSION_PROJET.md`** ⭐⭐⭐
   ```markdown
   Section "🔄 HISTORIQUE CHANGEMENTS MAJEURS":
   **Session XXX:** [Description changement principal]
   
   Section "⏳ ÉTAPES EN COURS":
   Mettre à jour ou déplacer vers "✅ VALIDÉES"
   
   Section "📊 MÉTRIQUES PROGRESSION":
   Mettre à jour barres progression
   ```

3. **`CONTINUITE_PROJET_SESSION_XXX.md`** ⭐⭐⭐ (CRÉER si session majeure)
   ```markdown
   Si changement architectural ou méthodologique majeur:
   Créer nouveau document CONTINUITE_PROJET_SESSION_XXX.md
   Lier avec sessions précédentes
   Expliquer ponts ancien/nouveau
   ```

4. **`PROJECT_STATE.md`** ⭐⭐
   ```markdown
   Section "Dernière mise à jour": Nouvelle date
   Section "Status global": Pourcentages actualisés
   Section "Prochaines sessions": Mise à jour TODO
   ```

5. **`ROADMAP_AVANCEMENT.md`** ⭐
   ```markdown
   Cocher étapes complétées
   Ajouter nouvelles étapes identifiées
   Mettre à jour estimations temps
   ```

**CHECKLIST:**
- [ ] Rapport session créé
- [ ] PROGRESSION_PROJET mis à jour
- [ ] CONTINUITE créé si nécessaire
- [ ] PROJECT_STATE actualisé
- [ ] ROADMAP à jour

---

### 🟠 TRIGGER 3: Changement Architecture

**QUAND:** Modification structure fichiers/dossiers

**FICHIERS À METTRE À JOUR (dans l'ordre):**

1. **`CONTINUITE_PROJET_SESSION_XXX.md`** ⭐⭐⭐ (CRÉER)
   ```markdown
   Section "🔄 CE QUE SESSION XXX A CHANGÉ"
   
   ### Nouvelle Structure
   AVANT:
   [Ancienne structure]
   
   APRÈS:
   [Nouvelle structure]
   
   ### Ponts Ancien → Nouveau
   Fichier X → Nouvel emplacement Y
   Module A → Accès via import B
   ```

2. **`PROJECT_STATE.md`** ⭐⭐⭐
   ```markdown
   Section "🗄️ ARCHITECTURE ACTUELLE":
   Remplacer structure complète
   
   Section "Fichier → Nouvel Emplacement":
   Table de correspondance
   ```

3. **`INDEX_CHEMINS_CRITIQUES.md`** ⭐⭐
   ```markdown
   Mettre à jour tous chemins
   Ajouter redirections ancien → nouveau
   ```

4. **`FICHIERS_CRITIQUES_PROJET.md`** ⭐
   ```markdown
   Mettre à jour emplacements
   Vérifier liens toujours valides
   ```

**CHECKLIST:**
- [ ] CONTINUITE créé avec ponts
- [ ] PROJECT_STATE structure MAJ
- [ ] INDEX_CHEMINS MAJ
- [ ] FICHIERS_CRITIQUES MAJ
- [ ] Tous liens vérifiés

---

### 🟠 TRIGGER 4: Nouveau Module/Fichier Code

**QUAND:** Création fichier .py significatif

**FICHIERS À METTRE À JOUR (dans l'ordre):**

1. **`REGISTRY_MODULES_VALIDES.md`** ⭐⭐⭐
   ```markdown
   Ajouter entrée:
   
   ### module_name.py
   **Session:** XXX
   **Emplacement:** chemin/complet
   **Statut:** [En développement / Validé / Production]
   **Fonctions principales:**
   - function1(): Description
   - function2(): Description
   **Tests:** [Oui/Non - Emplacement tests]
   **Dépendances:** [Liste]
   ```

2. **`PROJECT_STATE.md`** ⭐⭐
   ```markdown
   Section "Architecture actuelle":
   Ajouter dans arborescence
   
   Section "Modules validés" (si applicable):
   Ajouter référence
   ```

3. **`FICHIERS_CLES_SESSION_XXX.md`** ⭐
   ```markdown
   Ajouter dans liste fichiers créés
   Indiquer importance (⭐⭐⭐ / ⭐⭐ / ⭐)
   ```

**CHECKLIST:**
- [ ] REGISTRY_MODULES entrée créée
- [ ] PROJECT_STATE arborescence MAJ
- [ ] FICHIERS_CLES liste MAJ
- [ ] Docstrings dans code
- [ ] Tests créés (si validé)

---

### 🟡 TRIGGER 5: Problème Identifié/Résolu

**QUAND:** Bug trouvé ou corrigé

**FICHIERS À METTRE À JOUR (dans l'ordre):**

1. **`ANTI_PATTERN_CRITIQUE.md`** ⭐⭐⭐
   ```markdown
   Si erreur récurrente potentielle:
   
   ### Erreur: [Description]
   
   **Symptôme:** [Ce qu'on voit]
   
   **Cause:** [Pourquoi ça arrive]
   
   **Solution:**
   ```python
   # ❌ FAUX
   code_incorrect
   
   # ✅ CORRECT
   code_correct
   ```
   
   **Détecté:** Session XXX
   ```

2. **`SESSION_XXX_RAPPORT_FINAL.md`** ⭐⭐
   ```markdown
   Section "Problèmes résolus":
   - [X] Problème Y (détails)
   ```

3. **`PROGRESSION_PROJET.md`** ⭐
   ```markdown
   Section "Bloquants résolus":
   - ✅ [Description] (résolu Session XXX)
   ```

**CHECKLIST:**
- [ ] ANTI_PATTERN MAJ si récurrent
- [ ] Rapport session documente résolution
- [ ] PROGRESSION bloquants MAJ
- [ ] Tests régression ajoutés

---

### 🟡 TRIGGER 6: Test/Validation Effectué

**QUAND:** Test important passé ou échoué

**FICHIERS À METTRE À JOUR (dans l'ordre):**

1. **`REFERENCE_CASE_11_SEPT_2025.md`** ⭐⭐⭐ (si test cas référence)
   ```markdown
   Section résultats:
   
   ### Test [Description] - Session XXX
   **Date:** [Date test]
   **Formule testée:** [Nom]
   **MAE:** XX.X pips
   **Status:** [✅ Validé / ❌ Rejeté]
   ```

2. **`METHODES_VALIDEES.md`** ⭐⭐⭐
   ```markdown
   Section formule concernée:
   **Validation:**
   - Test date1: MAE X pips ✅
   - Test date2: MAE Y pips ✅
   ```

3. **`PROGRESSION_PROJET.md`** ⭐⭐
   ```markdown
   Section phase concernée:
   Mettre à jour statut avec résultats tests
   ```

**CHECKLIST:**
- [ ] REFERENCE_CASE MAJ (si applicable)
- [ ] METHODES_VALIDEES résultats ajoutés
- [ ] PROGRESSION statut MAJ
- [ ] Graphiques/captures écran si pertinent

---

### 🟢 TRIGGER 7: Amélioration Métrique

**QUAND:** Précision/performance améliorée

**FICHIERS À METTRE À JOUR (dans l'ordre):**

1. **`METHODES_VALIDEES.md`** ⭐⭐⭐
   ```markdown
   Mettre à jour précision formule:
   **Précision:** XX.X% ✅✅✅ (était YY.Y%)
   **Amélioration:** +ZZ% (Session XXX)
   ```

2. **`PROGRESSION_PROJET.md`** ⭐⭐⭐
   ```markdown
   Section "🔄 HISTORIQUE CHANGEMENTS":
   **Session XXX:** Amélioration formule [Nom] (+XX%)
   
   Mettre à jour métriques:
   Phase X : █████████░░░ 90% (était 75%)
   ```

3. **`SESSION_XXX_RAPPORT_FINAL.md`** ⭐⭐
   ```markdown
   Section "Réalisations":
   - ✅ Amélioration précision formule X : +XX%
   ```

**CHECKLIST:**
- [ ] METHODES_VALIDEES précision MAJ
- [ ] PROGRESSION métriques MAJ
- [ ] Rapport session amélioration documentée
- [ ] Tests comparatifs documentés

---

### 🟢 TRIGGER 8: Documentation Créée

**QUAND:** Nouveau fichier .md important

**FICHIERS À METTRE À JOUR (dans l'ordre):**

1. **`INDEX_DOCUMENTATION.md`** ⭐⭐⭐
   ```markdown
   Ajouter dans section appropriée:
   
   ### NOUVEAU_FICHIER.md (X pages) ⭐⭐⭐
   **Description**
   - Point 1
   - Point 2
   **Localisation:** chemin/complet
   ```

2. **`LECTURE_OBLIGATOIRE_SESSION.md`** ⭐⭐
   ```markdown
   Si document critique:
   Ajouter dans ordre lecture recommandé
   Indiquer importance (⭐⭐⭐)
   ```

3. **`QUICK_START.md`** ⭐
   ```markdown
   Si document démarrage rapide:
   Ajouter dans "Lectures essentielles"
   ```

**CHECKLIST:**
- [ ] INDEX_DOCUMENTATION entrée créée
- [ ] LECTURE_OBLIGATOIRE MAJ si critique
- [ ] QUICK_START MAJ si pertinent
- [ ] Liens croisés ajoutés

---

## 🔄 MAINTENANCE PÉRIODIQUE

### Chaque Session (Obligatoire)

**Avant de terminer TOUTE session:**

1. **Créer rapport session** (20 min)
   - SESSION_XXX_RAPPORT_FINAL.md
   - Objectifs / Réalisations / TODO

2. **Mettre à jour progression** (10 min)
   - PROGRESSION_PROJET.md
   - Métriques à jour
   - Historique changements

3. **Actualiser PROJECT_STATE** (5 min)
   - Date mise à jour
   - Status global
   - Prochaines étapes

**Total: 35 minutes OBLIGATOIRES en fin de session**

---

### Hebdomadaire (Si projet actif)

**Vérification cohérence:**

1. **Vérifier liens** (15 min)
   - Tous chemins valides
   - Pas de références obsolètes
   - Redirections fonctionnelles

2. **Synchroniser métriques** (10 min)
   - PROJECT_STATE
   - PROGRESSION_PROJET
   - ROADMAP_AVANCEMENT
   - Tous doivent correspondre

3. **Index à jour** (10 min)
   - INDEX_DOCUMENTATION
   - INDEX_CHEMINS_CRITIQUES
   - FICHIERS_CRITIQUES_PROJET

**Total: 35 minutes hebdomadaires**

---

### Mensuel (Maintenance profonde)

**Audit complet:**

1. **Revue METHODES_VALIDEES** (30 min)
   - Précisions toujours valides ?
   - Nouveaux tests effectués ?
   - Formules obsolètes ?

2. **Revue PROGRESSION_PROJET** (20 min)
   - Roadmap réaliste ?
   - Estimations temps justes ?
   - Bloquants actualisés ?

3. **Revue CONTINUITE_PROJET** (15 min)
   - Liens toujours clairs ?
   - Nouvelles sessions majeures ?
   - Créer nouveau document si nécessaire

4. **Cleanup** (15 min)
   - Supprimer documents obsolètes
   - Archiver si nécessaire
   - Réorganiser si pertinent

**Total: 80 minutes mensuels**

---

## 📊 FICHIERS PAR IMPORTANCE

### ⭐⭐⭐ CRITIQUE (Mise à jour fréquente)

```
METHODES_VALIDEES.md           → Chaque formule validée
PROGRESSION_PROJET.md          → Chaque session
PROJECT_STATE.md               → Chaque session
CONTINUITE_PROJET_SESSION_XXX  → Sessions majeures
SESSION_XXX_RAPPORT_FINAL      → Chaque session
```

### ⭐⭐ IMPORTANT (Mise à jour régulière)

```
REGISTRY_MODULES_VALIDES.md    → Chaque nouveau module
INDEX_DOCUMENTATION.md         → Chaque nouveau doc
ANTI_PATTERN_CRITIQUE.md       → Chaque erreur récurrente
REFERENCE_CASE_11_SEPT_2025    → Chaque test cas référence
ROADMAP_AVANCEMENT.md          → Hebdomadaire
```

### ⭐ UTILE (Mise à jour occasionnelle)

```
QUICK_START.md                 → Changements démarrage
INDEX_CHEMINS_CRITIQUES.md     → Changements structure
FICHIERS_CRITIQUES_PROJET.md   → Changements fichiers
LECTURE_OBLIGATOIRE_SESSION    → Nouveaux docs critiques
```

---

## 🎯 CHECKLIST SESSION COMPLÈTE

**À la fin de CHAQUE session, vérifier:**

### Documentation Session
- [ ] SESSION_XXX_RAPPORT_FINAL.md créé
- [ ] Objectifs / Réalisations documentés
- [ ] Problèmes résolus listés
- [ ] Fichiers créés/modifiés listés
- [ ] Prochaine session TODO défini

### Progression
- [ ] PROGRESSION_PROJET.md mis à jour
- [ ] Métriques progression actualisées
- [ ] Historique changements ajouté
- [ ] Bloquants/validations MAJ

### État Global
- [ ] PROJECT_STATE.md actualisé
- [ ] Date dernière MAJ changée
- [ ] Status global reflète réalité
- [ ] Prochaines étapes claires

### Continuité (si applicable)
- [ ] CONTINUITE créé si session majeure
- [ ] Liens ancien/nouveau documentés
- [ ] Acquis préservés validés

### Méthodes (si applicable)
- [ ] METHODES_VALIDEES MAJ si formule
- [ ] REGISTRY_MODULES MAJ si nouveau module
- [ ] ANTI_PATTERN MAJ si erreur récurrente

### Tests (si applicable)
- [ ] REFERENCE_CASE MAJ si test effectué
- [ ] Résultats documentés
- [ ] Métriques précision actualisées

---

## 🚨 RÈGLES ABSOLUES

### ✅ TOUJOURS FAIRE

1. **Créer rapport en fin de session**
   - Même si session courte
   - Même si peu de changements
   - Traçabilité absolue

2. **Mettre à jour PROGRESSION_PROJET**
   - Reflet exact état projet
   - Métriques honnêtes
   - TODO réalistes

3. **Synchroniser PROJECT_STATE**
   - Status global correct
   - Date à jour
   - Cohérent avec PROGRESSION

4. **Documenter changements majeurs**
   - Architecture
   - Méthodologie
   - Découvertes importantes

5. **Valider avant de marquer "validé"**
   - Tests effectués
   - Résultats documentés
   - Précision mesurée

---

### ❌ NE JAMAIS FAIRE

1. **Terminer session sans rapport**
   - Perte continuité
   - Oubli acquis
   - Confusion prochaine session

2. **Marquer validé sans tests**
   - Fausse confiance
   - Erreurs production
   - Temps perdu debug

3. **Laisser métriques obsolètes**
   - Vision fausse progression
   - Décisions basées fausses données
   - Perte crédibilité

4. **Oublier liens ancien/nouveau**
   - Code orphelin
   - Duplication travail
   - Confusion équipe

5. **Négliger METHODES_VALIDEES**
   - Perte méthodologie
   - Réinvention roue
   - Régression qualité

---

## 📋 TEMPLATE RAPPORT SESSION

**Copier ce template pour chaque session:**

```markdown
# SESSION XXX - RAPPORT FINAL

**Date:** [Date]
**Durée:** [Temps]
**Tokens:** [Utilisés / Total]
**Status:** [✅ Succès / ⚠️ Partiel / ❌ Échec]

---

## 🎯 OBJECTIFS SESSION

1. [Objectif 1]
2. [Objectif 2]
3. [Objectif 3]

---

## ✅ RÉALISATIONS

### [Domaine 1]
- ✅ [Réalisation 1]
- ✅ [Réalisation 2]

### [Domaine 2]
- ✅ [Réalisation 3]

---

## 🐛 PROBLÈMES RÉSOLUS

1. **[Problème 1]**
   - Cause: [Explication]
   - Solution: [Ce qui a été fait]
   - Fichiers: [Liste]

---

## 📁 FICHIERS CRÉÉS/MODIFIÉS

### Créés (X)
- `chemin/fichier1.py` - [Description]
- `chemin/fichier2.md` - [Description]

### Modifiés (Y)
- `chemin/fichier3.py` - [Changements]

---

## 🧪 TESTS EFFECTUÉS

### [Test 1]
- **Résultat:** [MAE / Status]
- **Attendu:** [Valeur]
- **Obtenu:** [Valeur]
- **✅ Validé** / **❌ Échoué**

---

## 📊 MÉTRIQUES

```
Objectifs atteints:     X/Y (Z%)
Formules validées:      X
Tests passés:           X/Y
Précision moyenne:      XX.X%
```

---

## 📋 PROCHAINE SESSION

**Objectifs Session XXX:**
1. [TODO 1]
2. [TODO 2]

**Durée estimée:** [Temps]

**Fichiers à lire:**
1. [Document 1]
2. [Document 2]

---

**DOCUMENTATION MISE À JOUR:**
- [x] PROGRESSION_PROJET.md
- [x] PROJECT_STATE.md
- [x] METHODES_VALIDEES.md (si applicable)
- [x] CONTINUITE créé (si session majeure)
```

---

## 🎓 RESPONSABILITÉ

**Qui maintient documentation:**
- **Claude:** Créer/mettre à jour AUTOMATIQUEMENT
- **André:** Valider cohérence / Signaler oublis

**Quand Claude doit MAJ:**
- ✅ Fin de chaque session (obligatoire)
- ✅ Après validation formule (immédiat)
- ✅ Après changement architecture (immédiat)
- ✅ Après test important (immédiat)

**Si Claude oublie:**
- André rappelle ce protocole
- Claude exécute immédiatement
- Ajout dans checklist session

---

## 🔍 VÉRIFICATION QUALITÉ

**Critères documentation à jour:**

1. **Cohérence**
   - PROJECT_STATE = PROGRESSION_PROJET
   - Métriques identiques partout
   - Dates synchronisées

2. **Complétude**
   - Tous triggers traités
   - Tous fichiers listés
   - Tous changements documentés

3. **Accessibilité**
   - Index à jour
   - Liens fonctionnels
   - Ordre lecture clair

4. **Actualité**
   - Dernière MAJ < 1 session
   - Status reflète réalité
   - TODO réalistes

5. **Traçabilité**
   - Historique complet
   - Décisions expliquées
   - Résultats mesurés

---

## 🚀 MISE EN ŒUVRE

**À partir de maintenant (Session 113+):**

1. **Début session:** Lire protocole (5 min)
2. **Pendant session:** Noter triggers activés
3. **Fin session:** Exécuter checklist (35 min)
4. **Validation:** Vérifier cohérence globale

**Ce protocole est PERMANENT et s'applique à TOUTES les sessions futures.**

---

*Protocole créé: 05 novembre 2025 - Session 112*  
*Statut: OBLIGATOIRE*  
*Application: Session 113+*
