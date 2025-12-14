# ⚠️ RÈGLES OBLIGATOIRES DE SESSION

**Version :** 3.0 - Session 94  
**Status :** IMPÉRATIF - Non négociable  
**Établi après :** 3 échecs méthodologiques (S49, S57, S59) + Échec V2.5 (S92.1-92.4)

---

## 🚨 DIRECTIVE ABSOLUE

> **Ces règles DOIVENT être lues et appliquées au début de CHAQUE session.**  
> **Aucune exception. Aucune négociation.**  
> **L'utilisateur référencera ce fichier explicitement.**

---

## 🔴 PRIORITÉ #1 : LIRE CHARTE SCIENTIFIQUE (SESSION 94)

**AVANT de lire ce fichier, lire OBLIGATOIREMENT :**

📜 **`project_state_new.md` - Section "CHARTE DE DÉVELOPPEMENT SCIENTIFIQUE"**

**Cette Charte contient :**
- Article 1 : Rigueur scientifique absolue
- Article 2 : Règle tokens 105,000 (expliquée en détail)
- Article 3 : Baseline sacrée
- Article 4 : Documentation = Contrat
- Article 5 : Échecs Sessions 92.1-92.4 (à ne JAMAIS répéter)

**Pourquoi prioritaire ?**

Sessions 92.1-92.4 ont perdu 200k+ tokens et créé code inutilisable par manque de rigueur.

**Impact financier estimé si V2.5 utilisée en production : €8,040/an perdus.**

**Cette Charte grave les principes qui empêchent de répéter ces erreurs.**

**⌛ Temps lecture Charte : 10-15 minutes**

**🛑 SI CHARTE NON LUE → SESSION INVALIDÉE**

---

1. Indiquer régulièrement les tokens utilisés a chaque étape 

## 📋 CHECKLIST OBLIGATOIRE DE DÉMARRAGE

### ⚠️ ÉTAPE 0 : LIRE CHARTE SCIENTIFIQUE (OBLIGATOIRE)

**AVANT TOUTE AUTRE ÉTAPE :**

- [ ] **Lire `project_state_new.md` section "CHARTE DE DÉVELOPPEMENT SCIENTIFIQUE"**
  - Lire INTÉGRALEMENT les 5 Articles
  - Comprendre pourquoi Sessions 92.1-92.4 ont échoué
  - Accepter engagement scientifique
  - **Temps estimé : 10-15 minutes lecture**

**SI CETTE ÉTAPE SAUTÉE → STOP IMMÉDIAT**

---

### ✅ AVANT TOUT CODE (30-40k tokens)

Cocher mentalement chaque étape :

- [ ] **0. Lire `REPERTOIRE_TRAVAIL_REFERENCE.md`** 🆕 SESSION 95
  - **Chemins absolus projet documentés**
  - Évite 5-10 min recherches par session
  - Templates Python prêts à utiliser
  - Référence permanente à consulter TOUJOURS

- [ ] **1. Lire `project_state_new.md` ENTIÈREMENT**
  - **PRIORITÉ ABSOLUE : Section "CHARTE SCIENTIFIQUE" en tête**
  - Pas de survol, pas de lecture en diagonale
  - Lire ligne par ligne les sections critiques
  - Prendre des notes mentales des découvertes clés

- [ ] **2. Lire le rapport de la session précédente**
  - `SESSION[N-1]_RAPPORT_COMPLET.md` ou `FINAL.md`
  - Comprendre ce qui a été fait
  - Identifier les problèmes rencontrés

- [ ] **3. Lire le message de transition**
  - `MESSAGE_SESSION[N-1]_SESSION[N].md`
  - Mission claire définie ?
  - Fichiers à utiliser identifiés ?

- [ ] **4. Afficher tokens utilisés**
  - Dire explicitement : "Tokens utilisés : X / 190,000 (Y% - Marge : Z avant limite 105k)"
  - Répéter tous les 20k tokens
  - ⚠️ **LIMITE PROJET : 105,000 tokens MAX** (pas 190k)
  - **ARRÊT OBLIGATOIRE à 105k pour documentation complète**
  - **Alertes :**
    - 85k : "⚠️ 20k avant limite"
    - 95k : "🚨 10k avant limite - Préparer clôture"
    - 105k : "🛑 LIMITE - Documentation obligatoire"

- [ ] **5. Valider compréhension avec l'utilisateur**
  - Résumer la mission en 3-5 phrases
  - Demander confirmation AVANT tout code
  - Poser questions si ambiguïté

### ⚠️ SI UNE ÉTAPE N'EST PAS COCHÉE → STOP

**Ne pas coder. Ne pas chercher. Ne pas deviner.**

**Demander à l'utilisateur ce qui manque.**

---

## 🎯 RÈGLES PENDANT LA SESSION

### 1. RÉUTILISER, NE PAS RÉINVENTER

**TOUJOURS :**
- ✅ Chercher si un script/fonction existe déjà
- ✅ Lire le code existant AVANT de réécrire
- ✅ Copier/adapter au lieu de créer from scratch
- ✅ Utiliser les formules validées (Sessions 51-55, 64)

**JAMAIS :**
- ❌ Créer 5 versions d'un même script
- ❌ Réécrire ce qui fonctionne déjà
- ❌ Ignorer `formulas_validated.py`
- ❌ Deviner au lieu de tester

### 2. BACKUP AVANT TOUTE MODIFICATION

**TOUJOURS créer un backup AVANT de modifier un fichier :**
- ✅ Créer backup avec timestamp
- ✅ Nommer : `fichier.py.backup_session[N]_[description]`
- ✅ Exemple : `5_Planificateur.py.backup_session71_fix_labels`
- ✅ Documenter raison du backup

**Ne JAMAIS :**
- ❌ Modifier fichier sans backup
- ❌ Écraser un backup existant
- ❌ Oublier de tester après modification

### 3. TESTER IMMÉDIATEMENT

**Après CHAQUE fonction/modification :**
- ✅ Créer un test simple
- ✅ Valider sur cas référence (11 septembre 2025)
- ✅ Comparer avec résultats attendus
- ✅ Documenter écarts

**Si test échoue :**
- ✅ Corriger immédiatement
- ✅ Retester
- ✅ Documenter la correction

**Ne JAMAIS :**
- ❌ Accumuler du code non testé
- ❌ "Tester plus tard"
- ❌ Supposer que ça marche

### 4. DOCUMENTER PROGRESSIVEMENT

**Au fur et à mesure :**
- ✅ Commenter le code inline
- ✅ Créer docstrings complètes
- ✅ Noter découvertes dans rapport session
- ✅ Mettre à jour `project_state_new.md` si découverte majeure

**En fin de session :**
- ✅ Rapport complet (`SESSION[N]_RAPPORT_COMPLET.md`)
- ✅ Message transition (`MESSAGE_SESSION[N]_SESSION[N+1].md`)
- ✅ Mise à jour `project_state_new.md` (section État Actuel)

### 5. GÉRER LES TOKENS

**Monitoring obligatoire :**
- 📊 Afficher tokens tous les 20k
- 📊 S'arrêter à 110k pour documentation finale (20k réservés)
- 📊 Si 115k atteints → Créer checkpoint immédiat

**Budget type session productive :**
```
Documentation lecture :      30-40k tokens
Validation utilisateur :     5-10k tokens
Implémentation ciblée :      40-50k tokens
Tests validation :           10-15k tokens
Documentation finale :       15-20k tokens
────────────────────────────────────────
Total session réussie :      100-135k tokens
```

---

## 🚫 ANTI-PATTERNS INTERDITS

### Ces erreurs ont causé 3 échecs (S49, S57, S59)

**❌ JAMAIS faire :**

1. **Sauter directement au code**
   - Sans lire `project_state_new.md`
   - Sans lire rapport session précédente
   - Sans valider mission avec utilisateur

2. **Redécouvrir le connu**
   - Analyser ce qui est documenté
   - Créer des scripts de diagnostic inutiles
   - Gaspiller 80k tokens sur fausse piste

3. **Créer multiples versions**
   - `script_v1.py`, `script_v2.py`, ..., `script_v5.py`
   - Aucune testée correctement
   - Confusion totale

4. **Deviner au lieu de demander**
   - Quelle table DB utiliser ?
   - Quels sont les événements ?
   - Comment calculer X ?
   - → **DEMANDER à l'utilisateur**

5. **Ignorer les outils validés**
   - `formulas_validated.py` (Sessions 51-55)
   - `test_4_formules_11sept.py` (validation)
   - Double Wave (Session 64)
   - → **TOUJOURS utiliser ce qui fonctionne**

---

## ✅ PATTERN DE SUCCÈS VALIDÉ

### Sessions réussies : 51, 52, 53, 55, 61, 64

**Méthodologie commune :**

```
1. Lecture complète documentation        [30-40k tokens]
   - project_state_new.md (intégral)
   - Rapports sessions pertinentes
   - Message transition

2. Validation mission utilisateur        [5-10k tokens]
   - Résumer compréhension
   - Poser questions si besoin
   - Obtenir confirmation GO

3. Identification outils existants       [10-15k tokens]
   - Lister scripts/fonctions disponibles
   - Tester ce qui existe
   - Comprendre COMMENT ça marche

4. Implémentation ciblée                 [40-50k tokens]
   - Fonctions précises
   - Tests immédiats après chaque fonction
   - Corrections rapides

5. Validation résultats                  [10-15k tokens]
   - Test cas référence (11 septembre)
   - Comparaison résultats attendus
   - Documentation écarts

6. Documentation finale                  [15-20k tokens]
   - Rapport session complet
   - Message transition suivante
   - Mise à jour project_state_new.md

───────────────────────────────────────────────
RÉSULTAT : 90-100% efficacité ✅
```

---

## 🎓 RÈGLES SPÉCIFIQUES AU PROJET

### Base de Données

**Fichier :** `warehouse.duckdb` (205 MB)  
**Location :** `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/data/`

**Tables critiques :**
- `events` : Événements économiques (58,449 events)
- `event_families` : Familles + statistiques
- `prices_1m` : Prix EUR/USD minute par minute (colonne `datetime`, PAS `timestamp`)
- `validation_events` : 11 septembre 2025 (11 events référence)

**Erreurs DB à éviter :**
```sql
-- ❌ ERREUR : colonne n'existe pas
SELECT event_name FROM events

-- ✅ CORRECT
SELECT event_title FROM events

-- ❌ ERREUR : colonne NULL
SELECT timestamp FROM prices_1m

-- ✅ CORRECT
SELECT datetime FROM prices_1m
```

### Formules Validées

**Module :** `fx_impact_app/src/formulas_validated.py`

**4 formules validées (Sessions 51-55) :**
1. `calculate_adjusted_empirical_score()` - 99.9% précision
2. `calculate_impact_d()` - 98.6% précision
3. `calculate_ttr_c()` - 94.4% précision
4. `calculate_pullback_v2()` - 99.3% précision

**Formule Double Wave (Session 64) :**
- Conditions : surprise > 20%, cluster ≥ 5
- Ratios : 0.58, 0.84, 0.90
- Timing : T+5, T+11, T+15, T+40
- Précision : 93% impact, 100% timing

**⚠️ NE JAMAIS modifier ces formules sans validation utilisateur**

### Cas de Référence

**Date :** 11 septembre 2025  
**Événements :** 9 CPI US à 14h30 Berne (12h30 UTC)  
**Impact réel MT5 :** 53 pips (1.16880 → 1.17410)  
**Type mouvement :** Double Wave Momentum

**Utiliser comme test SYSTÉMATIQUE :**
- Toute nouvelle formule
- Toute modification code
- Toute optimisation

---

## 📞 MESSAGE TYPE DÉBUT DE SESSION

**Template pour l'utilisateur :**

```
Bonjour Claude,

Nouvelle session [N].

AVANT TOUT :
1. Lis MANDATORY_SESSION_RULES.md
2. Lis project_state_new.md (intégral)
3. Lis SESSION[N-1]_RAPPORT_COMPLET.md
4. Lis MESSAGE_SESSION[N-1]_SESSION[N].md

Ensuite :
5. Résume ta compréhension de la mission
6. Demande confirmation AVANT de coder

Mission session [N] : [Description claire]

GO !
```

---

## 🔄 MISE À JOUR DES RÈGLES

**Ce fichier est vivant.**

Si une nouvelle règle critique émerge :
- ✅ Ajouter à ce fichier
- ✅ Documenter pourquoi (quelle erreur évitée)
- ✅ Référencer session d'origine
- ✅ Mettre à jour version

### 2. PROTOCOLE 105k TOKENS (SESSION 94)

**À 105,000 tokens utilisés - PROTOCOLE OBLIGATOIRE :**

1. ✅ **STOP immédiat** tout code/tests/analyses
2. ✅ Créer `SESSION[N]_RAPPORT_COMPLET.md`
   - Résultats tests avec CSV
   - Comparaisons AVANT/APRÈS
   - Limitations connues
   - Aucun claim sans preuve
3. ✅ Créer `MESSAGE_SESSION[N]_SESSION[N+1].md`
   - Mission session suivante
   - Fichiers à utiliser
   - Checklist obligatoire
4. ✅ Mettre à jour `project_state_new.md`
   - Section État Actuel
   - Ajout session N dans historique
5. ✅ Vérifier cohérence 3 documents

**Marge restante : 85,000 tokens pour documentation complète**

**Pourquoi 105k au lieu de 190k ?**
- Claude termine souvent sessions avant 190k
- 105k garantit marge confortable documentation
- Évite rapports tronqués ou incomplets
- Buffer clarifications utilisateur (10-20k)

**CETTE RÈGLE EST NON NÉGOCIABLE**

---

### 3. BACKUP AVANT TOUTE MODIFICATION

**Méthode EFFICACE (recommandée) :**
- ✅ Utiliser shutil.copy() ou commande système
- ✅ Consommation : ~0 tokens
- ✅ Rapide et fiable

**Ne JAMAIS :**
- ❌ Lire fichier entier puis réécrire
- ❌ Gaspille 10-20k tokens inutilement


**Historique versions :**
- v1.0 : Session 60 (règles initiales)
- v2.0 : Session 64 (ajout Double Wave, anti-patterns)
- v2.1 : Session 71 (ajout règle backup obligatoire)

---

## ✅ VALIDATION DE COMPRÉHENSION

**À la fin de la lecture de ce fichier, Claude doit pouvoir répondre :**

1. Quels sont les 5 fichiers à lire AVANT de coder ?
2. Quel est le budget tokens recommandé pour documentation ?
3. Quelle est la règle #1 avant de créer du nouveau code ?
4. Quel est le cas de test de référence systématique ?
5. À quelle fréquence afficher les tokens utilisés ?

**Si Claude ne peut pas répondre → Relire ce fichier.**

---

## 🎯 RÉSUMÉ EN 3 LIGNES

1. **LIRE d'abord** (40k) → **VALIDER avec user** (5k) → **CODER ensuite** (50k)
2. **RÉUTILISER ce qui existe** → **TESTER immédiatement** → **DOCUMENTER progressivement**
3. **AFFICHER tokens** tous les 20k → **ARRÊTER à 110k** pour doc finale

---

*Règles établies après analyse échecs Sessions 49, 57, 59, 63*  
*Validées par succès Sessions 51, 52, 53, 55, 61, 64*  
*Mise à jour : 24 octobre 2025 - Session 71*  
*Version : 2.1*

