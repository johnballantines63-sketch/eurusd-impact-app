# 📋 MÉTHODOLOGIE DE TRAVAIL - RÈGLES FONDAMENTALES

**Date de création** : 2025-01-XX  
**Objectif** : Éviter de réinventer ce qui existe déjà et fonctionne

---

## 🎯 PRINCIPE FONDAMENTAL

**NE JAMAIS RÉINVENTER CE QUI EXISTE DÉJÀ ET QUI FONCTIONNE**

Avant toute action, toute proposition, toute solution :
1. **RECHERCHER** dans l'existant
2. **DOCUMENTER** la situation
3. **PROPOSER** une solution
4. **ATTENDRE LE OK** avant d'appliquer

---

## 📝 PROCESSUS OBLIGATOIRE EN 4 ÉTAPES

### ÉTAPE 1 : RECHERCHE DANS L'EXISTANT ⚠️ OBLIGATOIRE

**Avant de proposer quoi que ce soit, rechercher systématiquement :**

1. **Documentation existante**
   - `docs/` : Tous les fichiers de documentation
   - `docs/PIPELINE_REFERENCE/` : Documentation pipeline
   - `docs/VALIDATION_SESSION_*/` : Validations précédentes
   - `docs/__REFERENCE_CRITIQUE__/` : Références critiques
   - `docs/SESSION*/` : Rapports de sessions précédentes

2. **Code existant**
   - `scripts/` : Scripts de validation, tests, utilitaires
   - `src/core/` : Modules core validés
   - `streamlit_app/` : Applications existantes
   - Rechercher avec `codebase_search`, `grep`, `glob_file_search`

3. **Solutions validées**
   - Fonctions déjà implémentées et testées
   - Paramètres déjà calibrés et validés
   - Logiques déjà documentées et fonctionnelles

**Outils de recherche :**
- `codebase_search` : Recherche sémantique dans le code
- `grep` : Recherche textuelle exacte
- `glob_file_search` : Recherche de fichiers par pattern
- `read_file` : Lecture de fichiers de documentation

**Critères de recherche :**
- Chercher par mots-clés pertinents
- Chercher dans plusieurs répertoires
- Vérifier les dates de validation
- Identifier les solutions "validées" vs "expérimentales"

---

### ÉTAPE 2 : DOCUMENTATION DE LA SITUATION 📄

**Après la recherche, documenter clairement :**

1. **Ce qui a été trouvé**
   - Solutions existantes identifiées
   - Documentation pertinente
   - Code/fonctions existants
   - Paramètres validés

2. **Ce qui manque**
   - Gaps identifiés
   - Incohérences trouvées
   - Problèmes non résolus

3. **Contexte du problème**
   - Description claire du problème
   - Impact sur le système
   - Contraintes identifiées

**Format de documentation :**
- Créer un fichier dans `docs/VALIDATION_SESSION_YYYY_MM_DD/` si nouvelle session
- Ou mettre à jour un fichier existant
- Inclure références aux fichiers trouvés
- Citer les solutions existantes

---

### ÉTAPE 3 : PROPOSITION DE SOLUTION 💡

**Seulement après recherche et documentation, proposer :**

1. **Solution basée sur l'existant**
   - Réutiliser les fonctions validées
   - Utiliser les paramètres calibrés
   - Suivre les logiques documentées
   - Éviter de réécrire ce qui existe

2. **Si nouvelle solution nécessaire**
   - Justifier pourquoi l'existant ne suffit pas
   - Proposer une extension plutôt qu'un remplacement
   - Documenter les différences avec l'existant

3. **Plan d'action détaillé**
   - Étapes précises
   - Fichiers à modifier/créer
   - Tests à effectuer
   - Validation à prévoir

**Format de proposition :**
- Présenter clairement la solution
- Citer les références utilisées
- Expliquer les choix
- Proposer un plan d'action

---

### ÉTAPE 4 : VALIDATION ET APPLICATION ✅

**Seulement après validation explicite de l'utilisateur :**

1. **Attendre le "OK" explicite**
   - Ne pas appliquer sans confirmation
   - Ne pas interpréter un silence comme un accord
   - Demander clarification si nécessaire

2. **Appliquer la solution**
   - Suivre le plan d'action proposé
   - Utiliser les solutions existantes identifiées
   - Documenter les modifications

3. **Valider les résultats**
   - Tester les modifications
   - Vérifier la cohérence avec l'existant
   - Documenter les résultats

---

## 🚫 INTERDICTIONS STRICTES

### ❌ NE JAMAIS :

1. **Réinventer une fonction existante**
   - Toujours vérifier si une fonction existe déjà
   - Utiliser les fonctions validées plutôt que d'en créer de nouvelles

2. **Réécrire une logique validée**
   - Si une logique fonctionne et est documentée, la réutiliser
   - Ne pas proposer de "meilleure" solution sans justification

3. **Ignorer la documentation**
   - Toujours lire la documentation pertinente avant d'agir
   - Respecter les paramètres validés

4. **Appliquer sans validation**
   - Ne jamais modifier le code sans OK explicite
   - Ne jamais créer de fichiers sans confirmation

5. **Proposer sans rechercher**
   - Ne jamais proposer une solution sans avoir cherché dans l'existant
   - Ne jamais assumer qu'une solution n'existe pas

---

## ✅ BONNES PRATIQUES

### 1. Recherche systématique

**Avant chaque action :**
```
1. Chercher dans docs/ avec codebase_search
2. Chercher dans scripts/ avec grep
3. Chercher dans src/ avec glob_file_search
4. Lire les fichiers pertinents trouvés
5. Identifier les solutions existantes
```

### 2. Documentation continue

**Pendant le travail :**
```
1. Documenter ce qui est trouvé
2. Documenter ce qui est fait
3. Documenter les décisions prises
4. Créer/mettre à jour les fichiers de session
```

### 3. Réutilisation prioritaire

**Lors de la proposition :**
```
1. Identifier les fonctions existantes à réutiliser
2. Identifier les paramètres validés à utiliser
3. Identifier les logiques documentées à suivre
4. Proposer une extension plutôt qu'un remplacement
```

### 4. Validation obligatoire

**Avant application :**
```
1. Présenter la solution clairement
2. Citer les références utilisées
3. Expliquer les choix
4. Attendre le OK explicite
```

---

## 📚 EXEMPLES CONCRETS

### Exemple 1 : Correction de timings

**❌ MAUVAISE APPROCHE :**
- Proposer directement une nouvelle logique
- Réécrire la détection de pattern
- Ignorer les timings validés Session 64

**✅ BONNE APPROCHE :**
1. **Recherche** : Chercher "timings parfaits", "Session 64", "predict_double_wave_timeline"
2. **Documentation** : Lire `INTEGRATION_TIMING_PARFAITS.md`, `SCRIPTS_TIMING_PARFAITS.md`
3. **Proposition** : Utiliser les fonctions existantes `predict_double_wave_timeline()` et `predict_single_wave_timeline()`
4. **Validation** : Attendre le OK avant d'appliquer

### Exemple 2 : Détection de pattern

**❌ MAUVAISE APPROCHE :**
- Créer une nouvelle fonction de détection
- Ignorer `detect_for_date_duckdb_rev12()`
- Réécrire la logique de validation

**✅ BONNE APPROCHE :**
1. **Recherche** : Chercher "detect pattern", "double wave detection", "rev12"
2. **Documentation** : Lire `SESSION83_ADDENDUM_ERREUR11.md`, `double_wave_detector_rev12.py`
3. **Proposition** : Utiliser `detect_for_date_duckdb_rev12()` existant, adapter la logique de décision
4. **Validation** : Attendre le OK avant d'appliquer

---

## 🔄 PROCESSUS ITÉRATIF

**Si problème complexe :**

1. **Itération 1** : Recherche → Documentation → Proposition → Validation
2. **Itération 2** : Recherche approfondie → Documentation mise à jour → Proposition révisée → Validation
3. **Itération N** : Continuer jusqu'à solution validée

**Ne jamais sauter d'étapes, même pour des problèmes "simples"**

---

## 📝 CHECKLIST AVANT CHAQUE ACTION

- [ ] J'ai recherché dans la documentation (`docs/`)
- [ ] J'ai recherché dans le code existant (`scripts/`, `src/`)
- [ ] J'ai identifié les solutions existantes
- [ ] J'ai documenté la situation
- [ ] J'ai proposé une solution basée sur l'existant
- [ ] J'ai attendu le OK explicite
- [ ] J'ai appliqué la solution validée
- [ ] J'ai documenté les modifications

---

## 🎯 OBJECTIF FINAL

**Toujours réutiliser ce qui existe et fonctionne, plutôt que de réinventer.**

**Toujours rechercher avant de proposer, documenter avant d'appliquer, valider avant de modifier.**

---

**Cette méthodologie doit être appliquée à CHAQUE interaction, pour CHAQUE problème, pour CHAQUE question.**

