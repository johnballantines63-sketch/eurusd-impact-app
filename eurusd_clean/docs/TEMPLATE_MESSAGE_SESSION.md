# 📬 TEMPLATE - MESSAGE DÉMARRAGE SESSION

**Usage :** Copier-coller au début de chaque nouvelle session avec Claude

---

## 🎯 MESSAGE TYPE (À PERSONNALISER)

```
Bonjour Claude,

pour cette session tu dois: 

1) IMPÉRATIF - Lis d'abord ces fichiers dans l'ordre :
   - MANDATORY_SESSION_RULES.md (règles obligatoires)
   - project_state_new.md (état complet du projet)
   - SESSION[XX]_RAPPORT_COMPLET.md (session précédente)
   - MESSAGE_SESSION[XX]_SESSION[XX+1].md (brief session)

2) Après lecture, AVANT TOUT CODE :
   - Résume ta compréhension de la mission en 3-5 phrases
   - Pose tes questions si ambiguïté
   - Attends ma confirmation GO

3) Pendant la session :
   - Affiche tokens utilisés tous les 20k
   - Teste immédiatement après chaque fonction
   - Documente au fur et à mesure
   - Réutilise ce qui existe (ne réinvente pas)

4) Mission de cette session :
   [DÉCRIRE MISSION CLAIREMENT EN 2-3 PHRASES]

5) Critères de succès :
   [LISTER 3-5 CRITÈRES MESURABLES]

6) Fichiers/outils à utiliser :
   [LISTER SCRIPTS/MODULES PERTINENTS]

Règle d'or : LIRE → COMPRENDRE → VALIDER → CODER → TESTER → DOCUMENTER

GO !
```

---

## 📋 EXEMPLE CONCRET - SESSION 65

```
Bonjour Claude,

pour cette session tu dois: 

1) IMPÉRATIF - Lis d'abord ces fichiers dans l'ordre :
   - MANDATORY_SESSION_RULES.md (règles obligatoires)
   - project_state_new.md (état complet du projet)
   - SESSION64_RAPPORT_COMPLET.md (session précédente)
   - MESSAGE_SESSION64_SESSION65.md (brief session)

2) Après lecture, AVANT TOUT CODE :
   - Résume ta compréhension de la mission en 3-5 phrases
   - Pose tes questions si ambiguïté
   - Attends ma confirmation GO

3) Pendant la session :
   - Affiche tokens utilisés tous les 20k
   - Teste immédiatement après chaque fonction
   - Documente au fur et à mesure
   - Réutilise formules validées (Sessions 51-55, 64)

4) Mission de cette session :
   Intégrer la formule Double Wave en production.
   Créer module app/core/double_wave.py avec détection conditions.
   Modifier Planificateur V2 pour détecter automatiquement et afficher 2 phases.

5) Critères de succès :
   - Tests 11 septembre : 93% précision impact, 100% timing
   - Interface Streamlit fonctionne avec graphique 2 phases
   - Export CSV enrichi avec colonnes Double Wave
   - Documentation complète (guide modèle + guide utilisateur)

6) Fichiers/outils à utiliser :
   - formulas_validated.py (formules validées)
   - 5_Planificateur_V2_FORMULES_VALIDEES.py (à modifier)
   - warehouse.duckdb (base données)
   - Graphiques MT5 11 septembre (référence)

Règle d'or : LIRE → COMPRENDRE → VALIDER → CODER → TESTER → DOCUMENTER

GO !
```

---

## 🚨 VARIANTES SELON SITUATION

### Si session de correction (bug identifié)

```
4) Mission de cette session :
   CORRIGER le bug [NOM BUG] identifié en Session [XX].
   
   Bug : [DESCRIPTION 1 LIGNE]
   Cause : [CAUSE IDENTIFIÉE]
   Solution attendue : [SOLUTION 1 LIGNE]

5) Critères de succès :
   - Bug reproduit et confirmé
   - Correction appliquée
   - Tests passent (cas [X], [Y], [Z])
   - Pas de régression sur autres fonctionnalités
```

### Si session de validation

```
4) Mission de cette session :
   VALIDER [FONCTIONNALITÉ] sur [N] cas de test.
   
   Tests obligatoires :
   - Cas référence : 11 septembre 2025
   - Cas [X] : [description]
   - Cas [Y] : [description]

5) Critères de succès :
   - Tous tests passent avec précision > 90%
   - Documentation résultats détaillée
   - Identification problèmes éventuels
   - Recommandations pour amélioration
```

### Si session de recherche/analyse

```
4) Mission de cette session :
   ANALYSER [PHÉNOMÈNE/PATTERN] sur données historiques.
   
   Questions à répondre :
   - [Question 1] ?
   - [Question 2] ?
   - [Question 3] ?

5) Critères de succès :
   - Réponses factuelles aux 3 questions
   - Données chiffrées (pas d'hypothèses)
   - Graphiques/tableaux si pertinent
   - Recommandations actionnables
```

---

## ⚠️ ÉLÉMENTS OBLIGATOIRES

**Toujours inclure :**

1. ✅ Référence à `MANDATORY_SESSION_RULES.md`
2. ✅ Liste fichiers à lire (4 minimum)
3. ✅ Demande résumé compréhension AVANT code
4. ✅ Mission claire (2-3 phrases max)
5. ✅ Critères succès mesurables (3-5)
6. ✅ Rappel affichage tokens tous les 20k

**Ne JAMAIS :**

❌ Dire juste "continue le projet"
❌ Assumer que Claude sait quoi faire
❌ Oublier de référencer MANDATORY_SESSION_RULES.md
❌ Lancer sans validation compréhension

---

## 💡 CONSEILS RÉDACTION

### Mission Claire

**❌ Vague :**
"Améliore le planificateur"

**✅ Précis :**
"Intégrer formule Double Wave dans Planificateur V2 : détection auto conditions + graphique 2 phases"

### Critères Mesurables

**❌ Subjectif :**
"Ça doit bien marcher"

**✅ Objectif :**
"Tests 11 septembre : précision impact 93% ± 5%, timing 100%"

### Fichiers Pertinents

**❌ Générique :**
"Les fichiers du projet"

**✅ Spécifique :**
- `SESSION64_RAPPORT_COMPLET.md` (formule Double Wave)
- `formulas_validated.py` (à importer)
- `5_Planificateur_V2_FORMULES_VALIDEES.py` (à modifier)

---

## 📊 SUIVI QUALITÉ SESSIONS

**Indicateurs succès :**

| Indicateur | Cible | Mesure |
|------------|-------|--------|
| **Documentation lue** | 100% | Résumé correct mission |
| **Tokens lecture** | 30-40k | Affichage régulier |
| **Validation user** | Oui | Confirmation GO obtenue |
| **Tests immédiats** | Oui | Après chaque fonction |
| **Réutilisation** | Max | Pas de réinvention |
| **Efficacité** | >90% | Tokens productifs |

**Si indicateur rouge → Référencer MANDATORY_SESSION_RULES.md**

---

## 🔄 ÉVOLUTION DU TEMPLATE

**Ce template peut être amélioré.**

Si un élément manque ou pourrait être plus clair :
- ✅ Le modifier
- ✅ Tester sur session suivante
- ✅ Documenter amélioration
- ✅ Partager retour

**Objectif :** Template optimal = 0% échecs méthodologiques

---

*Template créé Session 64 après analyse échecs S49, S57, S59, S63*  
*Basé sur succès S51, S52, S53, S55, S61, S64*  
*Version : 1.0*  
*Date : 24 octobre 2025*

