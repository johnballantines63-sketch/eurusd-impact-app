# 📋 MESSAGE DÉMARRAGE SESSION 128

**Version :** 1.2 (Template Session 127)  
**Date :** 12 novembre 2025  
**Usage :** COPIER-COLLER directement dans Claude

---

## ⚠️ IMPORTANT : CHEMINS COMPLETS

Ce message utilise des **CHEMINS COMPLETS** pour tous les fichiers.  
Claude peut lire directement sans chercher (économise 5-10 tool calls).

---

## 🎯 MESSAGE (COPIER-COLLER)

```
Bonjour Claude,

Je démarre la Session 128.

═══════════════════════════════════════════════════════════════════
⚠️  LECTURE ATTENTIVE OBLIGATOIRE (MOT PAR MOT - PAS DE SURVOL)
═══════════════════════════════════════════════════════════════════

📖 LIRE MOT PAR MOT (sections critiques) :
────────────────────────────────────────────────────────────────
1. /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/01_VISION/MASTER_PLAN.md
   → Section "Session 127" : LIRE MOT PAR MOT
   → Point clé : Mapping variantes + correction DB/CSV formats
   → Si tu comprends "chercher directement dans CSV" → TU AS MAL LU

2. /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/01_VISION/Strategie_EUR:USD_News_Impact Calculator.md
   → Section "8.1 Session 127 Complétée" : LIRE ATTENTIVEMENT
   → Point clé : Fonction strip_variant_suffix() OBLIGATOIRE pour recherche scores
   → Si tu comprends "mapping optionnel" → TU AS MAL LU
   
3. /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/99_SESSIONS/SESSION_128_HANDOFF.md
   → Section "Plan d'action Session 128" : LIRE LIGNE PAR LIGNE
   → Objectif session : Validation système + Intégration Planificateur V2.5
   → Critère succès : Tests non-régression 100% + MAE < 5 pips

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
- Fonction recherche score à utiliser = [get_empirical_score_with_variants / recherche_directe_csv] ?
- Fonction strip obligatoire = [strip_variant_suffix / optionnelle] ?
- Format DB events = [avec_suffixes_mom_yoy_qoq / sans_suffixes] ?
- Format CSV scores = [avec_suffixes / sans_suffixes] ?

Si une réponse est fausse → je n'ai PAS lu attentivement → je relis."

═══════════════════════════════════════════════════════════════════

APRÈS VALIDATION QUIZ, ACTIONS :
────────────────────────────────────────────────────────────────
1. **REPORTER TOKENS UTILISÉS** : "📊 Tokens lecture : XX,XXXk / 190k (XX%)"
2. Vérifier que utils_mapping_variants.py existe et est accessible
3. Proposer architecture validation système (tests non-régression)
4. **REPORTER TOKENS UTILISÉS** : "📊 Tokens après analyse : XX,XXXk / 190k (XX%)"
5. Attendre validation André
6. PUIS commencer implémentation (pas avant)
7. **REPORTER TOKENS RÉGULIÈREMENT** (toutes les 3-4 interactions)

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

## ✅ RÉPONSES CORRECTES QUIZ

**Pour validation Claude :**

```
CONFIRMATION COMPRÉHENSION :
- Fonction recherche score à utiliser = get_empirical_score_with_variants
- Fonction strip obligatoire = strip_variant_suffix
- Format DB events = avec_suffixes_mom_yoy_qoq
- Format CSV scores = sans_suffixes

Si toutes correctes → Continue
Si une fausse → Claude doit relire
```

---

**Date création :** 12 novembre 2025 - Session 127  
**Auteur :** André Valentin avec Claude  
**Statut :** ✅ PRÊT POUR SESSION 128
