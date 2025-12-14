# 📋 DÉMARRAGE SESSION 117

**Date :** 06 novembre 2025  
**Session précédente :** 116 (complétée)  
**Objectif Session 117 :** Scanner prix → patterns (approche bottom-up)

---

## 🚀 MESSAGE DÉMARRAGE (COPIER-COLLER)

```
Bonjour Claude,

Je démarre la Session 117.

═══════════════════════════════════════════════════════════════════
⚠️  LECTURE ATTENTIVE OBLIGATOIRE (MOT PAR MOT - PAS DE SURVOL)
═══════════════════════════════════════════════════════════════════

📖 LIRE MOT PAR MOT (sections critiques) :
────────────────────────────────────────────────────────────────
1. /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/01_VISION/MASTER_PLAN.md
   → Section "GAP #1" : LIRE MOT PAR MOT
   → Point clé : Formule validée sur 11 sept (MAE 0.29 pips), validation multi-dates nécessaire
   → Si tu comprends "GAP #1 résolu complet" → TU AS MAL LU
   
2. /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/99_SESSIONS/SESSION_117_HANDOFF.md
   → Section "SOLUTION : APPROCHE BOTTOM-UP" : LIRE MOT PAR MOT
   → Objectif session : Scanner prix pour détecter TOUS les spikes > 40 pips
   → Critère succès : 10+ cas détectés, MAE moyen < 5 pips

📋 SURVOL AUTORISÉ (structure générale) :
────────────────────────────────────────────────────────────────
3. /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/99_SESSIONS/SESSION_116_RESUME.md
   → Comprendre pourquoi S116 a identifié limitation top-down

═══════════════════════════════════════════════════════════════════

✅ QUIZ DE COMPRÉHENSION OBLIGATOIRE :
────────────────────────────────────────────────────────────────
Réponds EXACTEMENT avec ce format :

"J'ai lu attentivement les sections critiques.

CONFIRMATION COMPRÉHENSION :
- Statut GAP #1 = [RÉSOLU complet / Validé 11 sept seulement] ?
- MAE 11 septembre S115 = [0.29 pips / 2 pips / 5 pips] ?
- Problème S116 = [Pas assez de cas / Approche top-down faux positifs] ?
- Objectif S117 = [Chercher events / Scanner PRIX d'abord] ?
- Approche S117 = [Top-down (events→prix) / Bottom-up (prix→events)] ?
- Critère détection spike = [> 20 pips / > 40 pips / > 60 pips] ?
- Nombre cas cible = [3 cas / 5+ cas / 10+ cas] ?
- MAE cible moyen = [< 2 pips / < 5 pips / < 10 pips] ?

Si une réponse est fausse → je n'ai PAS lu attentivement → je relis."

═══════════════════════════════════════════════════════════════════

APRÈS VALIDATION QUIZ, ACTIONS :
────────────────────────────────────────────────────────────────
1. Créer scan_price_patterns.py (scanner prix EUR/USD)
2. Définir algorithme détection Double Wave vs Single Wave Fort
3. Tester sur période 2024-2025
4. Afficher premiers candidats trouvés
5. Attendre validation André des cas détectés
6. PUIS enrichir avec events et valider formule

═══════════════════════════════════════════════════════════════════

⛔ INTERDICTIONS ABSOLUES :
────────────────────────────────────────────────────────────────
❌ Ne reviens PAS à approche top-down (events → prix)
❌ Ne filtre PAS trop strictement (cherche TOUS les spikes)
❌ Ne commence AUCUN code avant validation quiz
❌ Ne modifie PAS formule S115 sans justification solide
❌ Ne dis PAS "GAP #1 est résolu" (validation multi-dates nécessaire)

═══════════════════════════════════════════════════════════════════

🔥 RAPPELS CRITIQUES :
────────────────────────────────────────────────────────────────
• S115 = Formule validée sur 1 cas (11 sept : MAE 0.29 pips, 99.5%)
• S116 = Limitation détectée : approche top-down génère faux positifs
• S117 = Solution : partir des PRIX (spikes réels) vers events causaux
• Objectif : Dataset exhaustif 10-20 cas pour validation robuste
• Avantage bottom-up : zéro faux positifs, découverte patterns inattendus

═══════════════════════════════════════════════════════════════════

NE RÉPONDS RIEN D'AUTRE QUE LA CONFIRMATION QUIZ AVANT D'AVOIR 
LU ATTENTIVEMENT LES SECTIONS CRITIQUES.
```

---

**Auteur :** André Valentin avec Claude  
**Date :** 06 novembre 2025  
**Version :** 1.0
