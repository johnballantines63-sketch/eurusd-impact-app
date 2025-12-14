# 📋 DÉMARRAGE SESSION 127 - Recalibration Scores

**Version :** 1.0  
**Date :** 11 novembre 2025 - Session 126  
**Session cible :** 127

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

Je démarre la Session 127.

═══════════════════════════════════════════════════════════════════
⚠️  LECTURE ATTENTIVE OBLIGATOIRE (MOT PAR MOT - PAS DE SURVOL)
═══════════════════════════════════════════════════════════════════

📖 LIRE MOT PAR MOT (sections critiques) :
────────────────────────────────────────────────────────────────
1. /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/01_VISION/MASTER_PLAN.md
   → Section "SESSION 125-126 - Fonction Amplification Universelle Validée" : LIRE MOT PAR MOT
   → Point clé : Fonction universelle validée sur 3 familles (CPI, NFP, Fed)
   → Si tu comprends "fonction spécifique par famille" → TU AS MAL LU

2. /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/01_VISION/Strategie_EUR:USD_News_Impact Calculator.md
   → Section "6.1 Ce qui est Validé" : LIRE ATTENTIVEMENT Session 126
   → Section "8. Prochaines Étapes" : Comprendre Priorité 1 (Session 127)
   → Point clé : Fonction universelle + Pipeline master opérationnel
   → Si tu comprends "calibrer cluster par cluster" → TU AS MAL LU
   
3. /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/99_SESSIONS/SESSION_126_HANDOFF.md
   → Section "Plan d'action Session 127" : LIRE LIGNE PAR LIGNE
   → Objectif session : Recalibration scores 143 événements US HIGH manquants
   → Critère succès : Tous événements US HIGH ont scores empiriques validés

4. /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session126/audit_scores_mapping.txt
   → LIRE ATTENTIVEMENT les 3 catégories scores
   → 179 scores OK / 46 variantes / 24 manquants
   → Comprendre différence "variantes" vs "manquants"

📋 SURVOL AUTORISÉ (structure générale) :
────────────────────────────────────────────────────────────────
5. /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/00_README.md
   → Juste comprendre navigation PROJECT_MANAGEMENT/

═══════════════════════════════════════════════════════════════════

✅ QUIZ DE COMPRÉHENSION OBLIGATOIRE :
────────────────────────────────────────────────────────────────
Réponds EXACTEMENT avec ce format :

"J'ai lu attentivement les sections critiques.

CONFIRMATION COMPRÉHENSION :
- Fonction universelle validée sur combien de familles = [3 / 5 / 10] ?
- Amélioration moyenne Session 126 = [+50% / +71.6% / +90%] ?
- Pipeline master créé Session 126 = [OUI / NON] ?
- Scores utilisables directement (mapping parfait) = [179 / 272 / 100] ?
- Scores avec VARIANTES (nécessitent décision) = [24 / 46 / 69] ?
- Scores MANQUANTS (nécessitent recalcul) = [24 / 46 / 143] ?

Si une réponse est fausse → je n'ai PAS lu attentivement → je relis."

═══════════════════════════════════════════════════════════════════

APRÈS VALIDATION QUIZ, ACTIONS :
────────────────────────────────────────────────────────────────
1. **REPORTER TOKENS UTILISÉS** : "📊 Tokens lecture : XX,XXXk / 190k (XX%)"
2. Lire rapport audit complet (audit_scores_mapping.txt)
3. Analyser 3 catégories scores (179 OK / 46 variantes / 24 manquants)
4. Proposer stratégie mapping pour 46 scores avec variantes
5. Proposer méthodologie recalcul pour 24 scores manquants
6. **REPORTER TOKENS UTILISÉS** : "📊 Tokens après analyse : XX,XXXk / 190k (XX%)"
7. Attendre validation André
8. PUIS commencer implémentation (pas avant)
9. **REPORTER TOKENS RÉGULIÈREMENT** (toutes les 3-4 interactions)

═══════════════════════════════════════════════════════════════════

⛔ INTERDICTIONS ABSOLUES :
────────────────────────────────────────────────────────────────
❌ Ne survole PAS les sections critiques
❌ Ne propose RIEN avant d'avoir lu attentivement
❌ Ne commence AUCUN code avant validation architecture
❌ Ne dis PAS "ah désolé j'avais pas bien lu" après coup
❌ Ne confonds PAS "variantes" (event_key multiples) avec "manquants" (aucun event_key)
❌ N'OUBLIE PAS de reporter tokens utilisés régulièrement

═══════════════════════════════════════════════════════════════════

NE RÉPONDS RIEN D'AUTRE QUE LA CONFIRMATION QUIZ AVANT D'AVOIR 
LU ATTENTIVEMENT LES SECTIONS CRITIQUES.
```

---

## 📝 CONTEXTE SESSION 127

### **Problème à résoudre :**

Session 126 a découvert gap mapping scores CSV ↔ DB events :

**3 Catégories identifiées :**

1. **179 scores OK (65.8%)** ✅
   - Mapping parfait `event_name` → `event_key`
   - Utilisables immédiatement
   - Exemple : `non_farm_payrolls` → `non farm payrolls`

2. **46 scores VARIANTES (16.9%)** ⚠️
   - 1 `event_name` → Plusieurs `event_key` dans DB
   - Exemple : `retail_sales` → `retail sales_mom`, `retail sales_yoy`
   - **Nécessite DÉCISION** : Agréger ? Mapper principal ? Ignorer ?

3. **24 scores MANQUANTS (8.8%)** ❌
   - `event_name` existe dans CSV
   - Aucun `event_key` correspondant dans DB
   - **Nécessite RECALCUL** scores empiriques

### **Objectif Session 127 :**

Compléter mapping pour atteindre 100% événements US HIGH avec scores validés.

**Méthode :**
1. Créer table mapping `event_name` ↔ `event_key(s)`
2. Définir règles décision pour variantes
3. Recalculer scores empiriques pour manquants
4. Valider intégrité (pipeline doit fonctionner)

---

## 💡 CONSEILS RÉDACTION QUESTIONS QUIZ

### **✅ Bonnes questions (discrimination claire) :**

```
Fonction validée sur combien de familles = [3 / 5 / 10] ?
Scores variantes à décider = [24 / 46 / 69] ?
Scores manquants à recalculer = [24 / 46 / 143] ?
```

**Pourquoi c'est bon :**
- ✅ Chiffres précis à retenir
- ✅ Discrimination claire (3 options différentes)
- ✅ Prouve lecture attentive (pas baratinage)

### **❌ Mauvaises questions (trop vagues) :**

```
As-tu compris le problème ? [oui / non]
C'est important ? [oui / non]
Faut-il recalculer ? [oui / non]
```

**Pourquoi c'est mauvais :**
- ❌ Pas de discrimination (toujours "oui")
- ❌ Ne prouve pas lecture attentive
- ❌ Claude peut baratiner

---

## 🎯 OBJECTIF QUIZ

**Le quiz doit :**
1. ✅ Prouver lecture attentive (pas survol)
2. ✅ Identifier erreurs interprétation immédiatement
3. ✅ Économiser tokens (pas de relecture)
4. ✅ Éviter faux chemins de développement

**Si Claude répond mal au quiz → il se rend compte et relit**

---

## 📊 RÉPONSES CORRECTES QUIZ SESSION 127

**Pour validation André :**

```
RÉPONSES CORRECTES :
- Fonction universelle validée sur combien de familles = 3
  (CPI, NFP, Fed Interest Rate Decision)

- Amélioration moyenne Session 126 = +71.6%
  (Moyenne : 98.6% CPI + 88.3% NFP + 58.7% Fed + 52.3% Fed→CPI + 60.0% Fed→NFP)

- Pipeline master créé Session 126 = OUI
  (`calibrate_universal_amplification.py` + 5 modules)

- Scores utilisables directement (mapping parfait) = 179
  (65.8% des 272 scores USD)

- Scores avec VARIANTES (nécessitent décision) = 46
  (16.9% - exemple: retail_sales → retail sales_mom, retail sales_yoy)

- Scores MANQUANTS (nécessitent recalcul) = 24
  (8.8% - event_name existe dans CSV mais aucun event_key dans DB)
```

**Si Claude répond 143 à la dernière question → il confond "total problématique" (69) avec "manquants" (24)**

---

## 📚 FICHIERS RÉFÉRENCE SESSION 127

### **Créés Session 126 (à utiliser) :**

**Pipeline master (6 modules) :**
```
/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session126/calibrate_universal_amplification.py
→ Pipeline master CLI (pour tester après recalibration)

/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session126/utils_mapping.py
→ Fonctions mapping event_name ↔ event_key
→ get_empirical_score(), map_country_to_currency()

/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session126/validate_predictions.py
→ Validation prédictions vs baseline

/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session126/decide_integration.py
→ Décision automatique (EXCELLENT/GOOD/MODERATE/FAILED)
```

**Rapports audit :**
```
/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session126/audit_scores_mapping.txt
→ Rapport complet 3 catégories (CRITIQUE à lire)
→ Liste exhaustive problèmes

/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session126/db_inventory_complete.txt
→ Inventaire 26,480 événements (2023-2026)
```

### **À modifier Session 127 :**

```
/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session123/validation_results/event_families_eodhd_empirical.csv
→ Fichier scores à compléter
```

---

## ✅ CHECKLIST AVANT ENVOYER MESSAGE

```
☐ Message copié (tout le bloc entre ```)
☐ Questions quiz pertinentes (chiffres précis Session 126)
☐ Sections critiques identifiées (MASTER_PLAN + HANDOFF + audit)
☐ Interdictions listées (ne pas confondre variantes/manquants)
☐ Actions post-quiz définies (analyser 3 catégories)
☐ Chemins complets utilisés (tous les fichiers)

Si tout coché → ENVOYER à Claude
```

---

## 🔄 AMÉLIORATION CONTINUE

**Si malgré message Claude lit mal :**

### **Version encore plus stricte (citer textuellement) :**

```
Après lecture, cite EXACTEMENT (copie-colle) :
- Les 3 catégories scores avec chiffres exacts
- Le pourcentage scores OK (ligne rapport audit)
- L'objectif Session 127 (phrase exacte HANDOFF)

Si tu ne peux pas citer → tu n'as pas lu attentivement.
```

---

**Date création :** 11 novembre 2025 - Session 126  
**Auteur :** André Valentin avec Claude  
**Version :** 1.0  
**Statut :** ✅ PRÊT POUR SESSION 127
