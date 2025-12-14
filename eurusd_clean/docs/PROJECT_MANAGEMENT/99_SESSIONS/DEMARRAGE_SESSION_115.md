# 🚀 DÉMARRAGE SESSION 115 - Message prêt à utiliser

**Copie-colle ce message directement dans Claude pour démarrer Session 115**

---

```
Bonjour Claude,

Je démarre la Session 115.

═══════════════════════════════════════════════════════════════════
⚠️  LECTURE ATTENTIVE OBLIGATOIRE (MOT PAR MOT - PAS DE SURVOL)
═══════════════════════════════════════════════════════════════════

📖 LIRE MOT PAR MOT (sections critiques) :
────────────────────────────────────────────────────────────────
1. docs/PROJECT_MANAGEMENT/01_VISION/MASTER_PLAN.md
   → Section "GAP #1 : Impact TOTAL Pattern DOUBLE WAVE + OVERLAPPING" : LIRE MOT PAR MOT
   → Point clé : C'est DOUBLE WAVE + OVERLAPPING (3 phénomènes combinés)
   → Si tu comprends "overlapping simple" → TU AS MAL LU
   
2. docs/PROJECT_MANAGEMENT/99_SESSIONS/SESSION_115_HANDOFF.md
   → Section "CLARIFICATION DOUBLE WAVE + OVERLAPPING" : LIRE LIGNE PAR LIGNE
   → Tableau "Différence Critique" : LIRE CHAQUE LIGNE
   → Objectif session : Implémenter calculate_double_wave_overlapping()
   → Critère succès : MAE < 2 pips sur 11 septembre (56.2 pips total)

📋 SURVOL AUTORISÉ (structure générale) :
────────────────────────────────────────────────────────────────
3. docs/PROJECT_MANAGEMENT/00_README.md
   → Juste comprendre navigation PROJECT_MANAGEMENT/

═══════════════════════════════════════════════════════════════════

✅ QUIZ DE COMPRÉHENSION OBLIGATOIRE :
────────────────────────────────────────────────────────────────
Réponds EXACTEMENT avec ce format :

"J'ai lu attentivement les sections critiques.

CONFIRMATION COMPRÉHENSION :
- Pattern 11 septembre = [DOUBLE WAVE + OVERLAPPING / overlapping simple] ?
- Nombre de phénomènes combinés = [1 / 2 / 3] ?
- Fonction à créer = [calculate_total_impact_overlapping / calculate_double_wave_overlapping] ?
- Module existant à vérifier = [overlapping.py / double_wave.py] ?
- Wave 2 arrive [après Wave 1 / pendant pullback Wave 1] ?
- Impact cible 11 sept = [37.3 pips / 56.2 pips] ?

Si une réponse est fausse → je n'ai PAS lu attentivement → je relis."

═══════════════════════════════════════════════════════════════════

APRÈS VALIDATION QUIZ, ACTIONS :
────────────────────────────────────────────────────────────────
1. Vérifier si src/core/double_wave.py existe (Sessions 64-65)
2. Si existe : lire sa logique et comprendre son fonctionnement
3. Si absent : chercher dans documentation Sessions 64-65
4. Proposer architecture calculate_double_wave_overlapping() combinant :
   - double_wave.py (structure 2 vagues)
   - calculate_pullback_v2() (pullback logarithmique)
   - analyze_cluster_pattern() (timing overlapping)
5. Attendre validation André
6. PUIS commencer implémentation (pas avant)

═══════════════════════════════════════════════════════════════════

⛔ INTERDICTIONS ABSOLUES :
────────────────────────────────────────────────────────────────
❌ Ne survole PAS les sections critiques (GAP #1, CLARIFICATION)
❌ Ne propose RIEN avant d'avoir lu attentivement
❌ Ne commence AUCUN code avant validation architecture
❌ Ne dis PAS "ah désolé j'avais pas bien lu" après coup
❌ Ne crée PAS calculate_total_impact_overlapping (mauvais nom)
❌ Ne traite PAS comme "overlapping simple"

═══════════════════════════════════════════════════════════════════

🔥 RAPPELS CRITIQUES :
────────────────────────────────────────────────────────────────
• 11 septembre 2025 = DOUBLE WAVE + OVERLAPPING (pas overlapping simple)
• 3 phénomènes : Double Wave + Overlapping timing + Extension haussière
• Wave 1 (US CPI): 37.3 pips → Pullback 72% → Wave 2 (BCE) pendant pullback
• Impact total : 56.2 pips (pas 72.38 pips = addition simple)
• Module existant : double_wave.py (Sessions 64-65) à vérifier/utiliser

═══════════════════════════════════════════════════════════════════

NE RÉPONDS RIEN D'AUTRE QUE LA CONFIRMATION QUIZ AVANT D'AVOIR 
LU ATTENTIVEMENT LES SECTIONS CRITIQUES.
```

---

## ✅ RÉPONSES ATTENDUES QUIZ

**Si Claude a bien lu attentivement :**

```
CONFIRMATION COMPRÉHENSION :
- Pattern 11 septembre = DOUBLE WAVE + OVERLAPPING ✅
- Nombre de phénomènes combinés = 3 ✅
- Fonction à créer = calculate_double_wave_overlapping ✅
- Module existant à vérifier = double_wave.py ✅
- Wave 2 arrive = pendant pullback Wave 1 ✅
- Impact cible 11 sept = 56.2 pips ✅
```

**Si Claude répond mal → IL N'A PAS LU ATTENTIVEMENT → Il doit relire !**

---

## 📊 MÉTRIQUES SESSION 115

**Objectif :** Implémenter calculate_double_wave_overlapping()  
**Cible :** MAE < 2 pips sur 11 septembre (56.2 pips total)  
**Durée estimée :** 3-4h  
**Tokens budget :** ~120k / 190k

---

## 🎯 CRITÈRES SUCCÈS SESSION 115

**Minimum :**
- [ ] Fonction calculate_double_wave_overlapping() créée
- [ ] Test 11 septembre : MAE < 5 pips
- [ ] Documentation fonction complète
- [ ] MASTER_PLAN.md mis à jour

**Optimal :**
- [ ] Test 11 septembre : MAE < 2 pips ⭐
- [ ] Tests sur 3+ cas overlapping validés
- [ ] Formule généralisable documentée
- [ ] Module double_wave.py vérifié/utilisé

---

**Date création :** 06 novembre 2025 - Session 114  
**Auteur :** André Valentin avec Claude  
**Statut :** ✅ PRÊT À UTILISER
