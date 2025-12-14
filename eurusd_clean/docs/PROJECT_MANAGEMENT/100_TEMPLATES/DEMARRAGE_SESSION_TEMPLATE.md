# 📋 TEMPLATE DÉMARRAGE SESSION - Générique

**Version :** 1.2  
**Date :** 11 novembre 2025 - Session 126  
**Modifications :**  
- Ajout Stratégie_EUR/USD comme fichier obligatoire  
- Ajout instructions report tokens régulier  
- Ajout chemins complets obligatoires (v1.1)

**Usage :** Copie ce template et adapte pour chaque nouvelle session

---

## ⚠️ RÈGLE CRITIQUE : CHEMINS COMPLETS

**TOUJOURS utiliser chemins COMPLETS dans message de démarrage !**

❌ **MAUVAIS** :
```
docs/PROJECT_MANAGEMENT/01_VISION/MASTER_PLAN.md
```

✅ **BON** :
```
/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/01_VISION/MASTER_PLAN.md
```

**Raison :** Claude peut lire directement sans chercher (économise 5-10 tool calls)

---

## 🎯 MESSAGE DÉMARRAGE (À COPIER-COLLER)

```
Bonjour Claude,

Je démarre la Session XXX.

═══════════════════════════════════════════════════════════════════
⚠️  LECTURE ATTENTIVE OBLIGATOIRE (MOT PAR MOT - PAS DE SURVOL)
═══════════════════════════════════════════════════════════════════

📖 LIRE MOT PAR MOT (sections critiques) :
────────────────────────────────────────────────────────────────
1. /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/01_VISION/MASTER_PLAN.md
   → Section "[SECTION_CRITIQUE]" : LIRE MOT PAR MOT
   → Point clé : [DESCRIPTION_POINT_CLÉ]
   → Si tu comprends [MAUVAISE_INTERPRÉTATION] → TU AS MAL LU

2. /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/01_VISION/Strategie_EUR:USD_News_Impact Calculator.md
   → Section "[SECTION_STRATÉGIE]" : LIRE ATTENTIVEMENT
   → Point clé : [POINT_CLÉ_STRATÉGIE]
   → Si tu comprends [MAUVAISE_INTERPRÉTATION_STRATÉGIE] → TU AS MAL LU
   
3. /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/99_SESSIONS/SESSION_XXX_HANDOFF.md
   → Section "[SECTION_IMPORTANTE]" : LIRE LIGNE PAR LIGNE
   → Objectif session : [OBJECTIF_PRÉCIS]
   → Critère succès : [MÉTRIQUE_MESURABLE]

📋 SURVOL AUTORISÉ (structure générale) :
────────────────────────────────────────────────────────────────
4. /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/00_README.md
   → Juste comprendre navigation PROJECT_MANAGEMENT/

═══════════════════════════════════════════════════════════════════

✅ QUIZ DE COMPRÉHENSION OBLIGATOIRE :
────────────────────────────────────────────────────────────────
Réponds EXACTEMENT avec ce format :

"J'ai lu attentivement les sections critiques.

CONFIRMATION COMPRÉHENSION :
- [Question clé 1] = [Option A / Option B / Option C] ?
- [Question clé 2] = [Option A / Option B / Option C] ?
- [Question clé 3] = [Option A / Option B / Option C] ?
- [Question clé 4] = [Option A / Option B / Option C] ?

Si une réponse est fausse → je n'ai PAS lu attentivement → je relis."

═══════════════════════════════════════════════════════════════════

APRÈS VALIDATION QUIZ, ACTIONS :
────────────────────────────────────────────────────────────────
1. **REPORTER TOKENS UTILISÉS** : "📊 Tokens lecture : XX,XXXk / 190k (XX%)"
2. [Action 1 spécifique]
3. [Action 2 spécifique]
4. Proposer architecture/plan
5. **REPORTER TOKENS UTILISÉS** : "📊 Tokens après analyse : XX,XXXk / 190k (XX%)"
6. Attendre validation André
7. PUIS commencer implémentation (pas avant)
8. **REPORTER TOKENS RÉGULIÈREMENT** (toutes les 3-4 interactions)

═══════════════════════════════════════════════════════════════════

⛔ INTERDICTIONS ABSOLUES :
────────────────────────────────────────────────────────────────
❌ Ne survole PAS les sections critiques
❌ Ne propose RIEN avant d'avoir lu attentivement
❌ Ne commence AUCUN code avant validation architecture
❌ Ne dis PAS "ah désolé j'avais pas bien lu" après coup
❌ N'OUBLIE PAS de reporter tokens utilisés régulièrement

═══════════════════════════════════════════════════════════════════

NE RÉPONDS RIEN D'AUTRE QUE LA CONFIRMATION QUIZ AVANT D'AVOIR 
LU ATTENTIVEMENT LES SECTIONS CRITIQUES.
```

---

## 📝 GUIDE PERSONNALISATION

### **Remplacer ces champs :**

**[SESSION_XXX]** → Numéro session (ex: 115, 116, etc.)

**[SECTION_CRITIQUE]** → Nom section MASTER_PLAN.md à lire attentivement
- Ex: "GAP #1", "État actuel", "Roadmap"

**[DESCRIPTION_POINT_CLÉ]** → Point critique à comprendre
- Ex: "C'est DOUBLE WAVE + OVERLAPPING (3 phénomènes combinés)"

**[MAUVAISE_INTERPRÉTATION]** → Erreur fréquente à éviter
- Ex: "overlapping simple", "addition simple des impacts"

**[SECTION_STRATÉGIE]** → Section Stratégie_EUR/USD à lire (si pertinent)
- Ex: "6.1 Ce qui est Validé", "8. Prochaines Étapes", "Fonction universelle"

**[POINT_CLÉ_STRATÉGIE]** → Point clé stratégie à comprendre
- Ex: "Fonction universelle validée", "Pipeline master opérationnel"

**[MAUVAISE_INTERPRÉTATION_STRATÉGIE]** → Erreur à éviter
- Ex: "calibrer cluster par cluster", "formules spécifiques"

**[SECTION_IMPORTANTE]** → Section HANDOFF à lire attentivement
- Ex: "CLARIFICATION DOUBLE WAVE", "Plan d'action"

**[OBJECTIF_PRÉCIS]** → Mission session en 1 phrase
- Ex: "Implémenter calculate_double_wave_overlapping()"

**[MÉTRIQUE_MESURABLE]** → Critère succès quantifiable
- Ex: "MAE < 2 pips sur 11 septembre (56.2 pips)"

**[Question clé 1-4]** → Questions prouvant lecture attentive
- Ex: "Pattern 11 sept = [DOUBLE WAVE + OVERLAPPING / overlapping simple] ?"

**[Action 1-2]** → Actions immédiates après quiz
- Ex: "Vérifier si src/core/double_wave.py existe"
- **IMPORTANT:** Toujours demander report tokens après lecture et après analyse

**⚠️ IMPORTANT :** Toujours utiliser **CHEMINS COMPLETS** pour les fichiers !

**📊 NOUVEAU (Session 126) :**
- **Stratégie_EUR/USD** est maintenant fichier obligatoire à lire pour contexte projet
- **Instructions tokens** : Demander report régulier pour suivre consommation

---

## 💡 CONSEILS RÉDACTION QUESTIONS QUIZ

### **✅ Bonnes questions (discrimination claire) :**

```
Pattern = [DOUBLE WAVE + OVERLAPPING / overlapping simple] ?
Fonction = [calculate_total_impact / calculate_double_wave] ?
Module existant = [double_wave.py / overlapping.py] ?
Nombre phénomènes = [1 / 2 / 3] ?
```

### **❌ Mauvaises questions (trop vagues) :**

```
As-tu compris ? [oui / non]
C'est important ? [oui / non]
Faut-il lire ? [oui / non]
```

---

## 🎯 OBJECTIF QUIZ

**Le quiz doit :**
1. ✅ Prouver lecture attentive (pas survol)
2. ✅ Identifier erreurs interprétation immédiatement
3. ✅ Économiser tokens (pas de relecture)
4. ✅ Éviter faux chemins de développement

**Si Claude répond mal au quiz → il se rend compte et relit**

---

## 📊 EXEMPLE QUIZ SESSION 115

```
CONFIRMATION COMPRÉHENSION :
- Pattern 11 septembre = [DOUBLE WAVE + OVERLAPPING / overlapping simple] ?
- Nombre de phénomènes combinés = [1 / 2 / 3] ?
- Fonction à créer = [calculate_total_impact_overlapping / calculate_double_wave_overlapping] ?
- Module existant à vérifier = [overlapping.py / double_wave.py] ?
- Wave 2 arrive [après Wave 1 / pendant pullback Wave 1] ?
```

**Réponses correctes :**
- DOUBLE WAVE + OVERLAPPING
- 3
- calculate_double_wave_overlapping
- double_wave.py
- pendant pullback Wave 1

---

**Date création :** 06 novembre 2025 - Session 114-115  
**Dernière mise à jour :** 11 novembre 2025 - Session 126  
**Auteur :** André Valentin avec Claude  
**Version :** 1.2
