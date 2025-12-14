# 📋 MESSAGE DÉMARRAGE SESSION 137 - PRÊT À COPIER-COLLER

**Session :** 137  
**Objectif :** ÉTAPE 2 Workflow LOO-CV - Enrichir 396 mouvements avec événements HIGH  
**Date :** 14 novembre 2025

---

## 🎯 MESSAGE À COPIER-COLLER

```
Bonjour Claude,

Je démarre la Session 137.

═══════════════════════════════════════════════════════════════════
⚠️  LECTURE ATTENTIVE OBLIGATOIRE (MOT PAR MOT - PAS DE SURVOL)
═══════════════════════════════════════════════════════════════════

📖 LIRE MOT PAR MOT (sections critiques) :
────────────────────────────────────────────────────────────────
1. /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/00_FLOWCHARTS/doublewave_loo_validation.mermaid
   → ÉTAPE 2 workflow : LIRE MOT PAR MOT
   → Point clé : Enrichir LES 396 mouvements (PAS de cas référence spécifique)
   → Si tu comprends "chercher cas référence 11.09.2025" → TU AS MAL LU

2. /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/00_FLOWCHARTS/SESSION_132_FLOWCHART_LOO_CV.md
   → Description ÉTAPE 2 : LIRE ATTENTIVEMENT
   → Point clé : Matching ±60 min, HIGH only (importance_n = 3)
   → Si tu comprends "classifier patterns" → TU AS MAL LU

3. /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/01_VISION/MASTER_PLAN.md
   → Section "STRUCTURE DÉTAILLÉE DATABASE" : LIRE MOT PAR MOT
   → Point clé : events.ts_utc (UTC), events.importance_n (1/2/3), events.event_title
   → Si tu comprends "datetime", "importance", "event_name" → TU AS MAL LU

4. /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/99_SESSIONS/SESSION_137_HANDOFF.md
   → Section "Objectif Session 137" : LIRE LIGNE PAR LIGNE
   → Objectif : Enrichir 396 mouvements avec events HIGH
   → Critère succès : 150+ mouvements avec events (40%)

📋 SURVOL AUTORISÉ (structure générale) :
────────────────────────────────────────────────────────────────
5. /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session136/step1_scan_price_movements.py
   → Juste comprendre output ÉTAPE 1 (step1_price_movements.csv, 396 lignes)

═══════════════════════════════════════════════════════════════════

✅ QUIZ DE COMPRÉHENSION OBLIGATOIRE :
────────────────────────────────────────────────────────────────
Réponds EXACTEMENT avec ce format :

"J'ai lu attentivement les sections critiques.

CONFIRMATION COMPRÉHENSION :
- ÉTAPE 2 mission = [Enrichir 396 mouvements / Chercher cas référence / Classifier patterns] ?
- Colonne importance dans events = [importance VARCHAR / importance_n BIGINT / importance_level INT] ?
- Timezone events.ts_utc = [Europe/Zurich UTC+2 / UTC / America/New_York] ?
- Fenêtre matching ±60min = [60 min avant / 60 min après / 60 avant + 60 après = 120 total] ?
- Output ÉTAPE 2 colonnes = [pattern_type, r2 / num_events, total_score, event_keys / impact_predicted, mae] ?

Si une réponse est fausse → je n'ai PAS lu attentivement → je relis.

✅ Si TOUTES les réponses sont correctes → PASSE IMMÉDIATEMENT aux ACTIONS 1→5 ci-dessous SANS ATTENDRE validation André."

═══════════════════════════════════════════════════════════════════

APRÈS VALIDATION QUIZ, FAIS TOUTES CES ACTIONS DANS L'ORDRE :
────────────────────────────────────────────────────────────────
⚠️ TU DOIS FAIRE TOUTES LES ACTIONS 1→5 (PAS CHOISIR, TOUTES)

✅ ACTION 1 : REPORTER TOKENS LECTURE
   → "📊 Tokens lecture : XX,XXXk / 190k (XX%)"

✅ ACTION 2 : VÉRIFIER structure DB events
   → Exécuter SELECT pour confirmer colonnes (ts_utc, importance_n, event_title)
   → Compter événements HIGH (importance_n = 3) → attendu ~7,889

✅ ACTION 3 : TESTER requête matching ±60 min
   → Prendre 1 mouvement de step1_price_movements.csv (ligne 1 par exemple)
   → Tester SQL matching événements dans fenêtre ±60 min
   → Valider conversion timezone UTC → Europe/Zurich
   → Afficher combien d'events trouvés pour ce mouvement test

✅ ACTION 4 : PROPOSER architecture step2_match_clusters.py
   → Structure complète (imports, fonctions, workflow)
   → Logique matching détaillée (boucle sur 396 mouvements)
   → Gestion timezone (conversion ts_utc → Europe/Zurich)
   → Gestion scores NULL (utiliser 0.0)
   → Output CSV avec 3 colonnes (num_events, total_score, event_keys)

✅ ACTION 5 : REPORTER TOKENS ANALYSE
   → "📊 Tokens après analyse : XX,XXXk / 190k (XX%)"

✅ ACTION 6 : ATTENDRE VALIDATION ANDRÉ
   → NE CODE RIEN avant validation architecture

✅ ACTION 7 : APRÈS VALIDATION → Implémenter step2_match_clusters.py

✅ ACTION 8 : REPORTER TOKENS RÉGULIÈREMENT
   → Toutes les 3-4 interactions : "📊 Tokens : XXk / 190k"

═══════════════════════════════════════════════════════════════════

⛔ INTERDICTIONS ABSOLUES :
────────────────────────────────────────────────────────────────
❌ Ne survole PAS doublewave_loo_validation.mermaid (ÉTAPE 2)
❌ Ne survole PAS MASTER_PLAN.md (Section Structure DB)
❌ Ne propose RIEN avant d'avoir lu attentivement
❌ Ne commence AUCUN code avant validation architecture
❌ N'utilise PAS mauvais noms colonnes (datetime, importance, event_name)
❌ N'oublie PAS conversion timezone (ts_utc UTC → Europe/Zurich)
❌ Ne dis PAS "ah désolé j'avais pas bien lu" après coup
❌ N'OUBLIE PAS de reporter tokens utilisés régulièrement
❌ Ne demande PAS "quelle action préfères-tu" → FAIS TOUTES LES ACTIONS 1→5
❌ Ne cherche PAS "cas référence 11.09.2025" → Enrichir LES 396 mouvements

═══════════════════════════════════════════════════════════════════

NE RÉPONDS RIEN D'AUTRE QUE LA CONFIRMATION QUIZ AVANT D'AVOIR 
LU ATTENTIVEMENT LES SECTIONS CRITIQUES.
```

---

## 📝 NOTES PERSONNALISATION

**Session :** 137  
**Objectif :** ÉTAPE 2 Workflow LOO-CV - Enrichir 396 mouvements  
**Sections critiques :**
- doublewave_loo_validation.mermaid (ÉTAPE 2)
- SESSION_132_FLOWCHART_LOO_CV.md (description)
- MASTER_PLAN.md (Structure DB)

**Points d'attention Session 136 :**
- Bug timezone résolu (ts_utc UTC vs Europe/Zurich)
- Noms colonnes DB clarifiés (ts_utc, importance_n, event_title)
- Filtrage temporel validé (temps réel vs index)

**Quiz validation :**
- 5 questions discrimination claire
- Réponses correctes : Enrichir 396 mouvements, importance_n BIGINT, UTC, 120 total, num_events/total_score/event_keys
- PAS de question sur "cas référence" !

**Workflow correct :**
- ÉTAPE 1 (Session 136 ✅) : 396 mouvements détectés
- ÉTAPE 2 (Session 137) : Enrichir ces 396 mouvements
- PAS de cas référence spécifique dans ÉTAPE 2

---

**Créé par :** Claude avec André  
**Date :** 14 novembre 2025  
**Session :** 136 → 137  
**Statut :** ✅ VERSION CORRIGÉE (pas de cas référence)
