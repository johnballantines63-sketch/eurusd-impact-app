# 📋 DÉMARRAGE SESSION 119

**Date :** 07 novembre 2025  
**Session précédente :** 118  
**Session actuelle :** 119  
**Objectif :** Créer détecteurs patterns restants + validation automatique

---

## 🎯 MESSAGE DÉMARRAGE (À COPIER-COLLER)

```
Bonjour Claude,

Je démarre la Session 119.

═══════════════════════════════════════════════════════════════════
⚠️  LECTURE ATTENTIVE OBLIGATOIRE (MOT PAR MOT - PAS DE SURVOL)
═══════════════════════════════════════════════════════════════════

📖 LIRE MOT PAR MOT (sections critiques) :
────────────────────────────────────────────────────────────────
1. /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/99_SESSIONS/SESSION_118_HANDOFF.md
   → Section "CE QUI A ÉTÉ ACCOMPLI (SESSION 118)" : LIRE MOT PAR MOT
   → Point clé : JSON Session 117 avait timestamps incorrects (baseline 9 min trop tôt)
   → Solution : Approche event-driven (récupération DB directe)
   → Algorithme validé : DoubleWaveDetector (51.7 vs 56.2 pips, MAE 4.5 pips)
   → Si tu proposes d'utiliser JSON timestamps → TU AS MAL LU
   
2. /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/99_SESSIONS/SESSION_118_HANDOFF.md
   → Section "PLAN D'ACTION SESSION 119" : LIRE LIGNE PAR LIGNE
   → Phase 1-4 détaillées (Single Fort, Zig Zag, Classifier, Validation)
   → Points d'attention critiques (Baseline, Post-processing, Distinction patterns)
   → Si tu proposes baseline = low(event_time) → TU AS MAL LU
   
3. /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session118/double_wave_detector.py
   → Comprendre architecture DoubleWaveDetector (référence pour nouveaux détecteurs)
   → find_local_extrema(), filter_significant_extrema(), identify_double_wave_pattern()
   → POST-PROCESSING (Étapes 3.4 & 3.5) : extrema BRUTS pas filtrés
   → Si tu utilises extrema filtrés pour pullback/wave2 → TU AS MAL LU

📋 SURVOL AUTORISÉ (contexte général) :
────────────────────────────────────────────────────────────────
4. /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/01_VISION/MASTER_PLAN.md
   → Section "SESSION 118" pour contexte
   → Juste comprendre état projet global

═══════════════════════════════════════════════════════════════════

✅ QUIZ DE COMPRÉHENSION OBLIGATOIRE :
────────────────────────────────────────────────────────────────
Réponds EXACTEMENT avec ce format :

"J'ai lu attentivement les sections critiques.

CONFIRMATION COMPRÉHENSION :
- Baseline correct = [close(t-1) / low(t) / open(t)] ?
- Post-processing utilise extrema = [filtrés / bruts] ?
- Patterns à créer Session 119 = [2 / 3 / 4] ?
- Pullback Single Fort = [< 20% / 20-80% / > 80%] ?
- Pullback Zig Zag = [< 20% / 20-80% / > 80%] ?
- Référence code = [double_wave_detector.py / price_pattern_scanner.py] ?
- JSON Session 117 timestamps = [corrects / incorrects] ?

Si une réponse est fausse → je n'ai PAS lu attentivement → je relis."

═══════════════════════════════════════════════════════════════════

APRÈS VALIDATION QUIZ, ACTIONS :
────────────────────────────────────────────────────────────────
1. Créer scripts/session119/pattern_detectors.py (structure classes)
2. Proposer architecture (Base + SingleFort + ZigZag + Classifier)
3. Attendre validation André
4. PUIS commencer implémentation Phase 1 (Single Fort)
5. Tester sur 3 cas réels trouvés dans DB
6. Valider avec André avant Phase 2

═══════════════════════════════════════════════════════════════════

⛔ INTERDICTIONS ABSOLUES :
────────────────────────────────────────────────────────────────
❌ Ne propose RIEN avant d'avoir lu attentivement
❌ N'utilise PAS timestamps JSON Session 117 (incorrects)
❌ N'utilise PAS extrema filtrés pour post-processing
❌ Ne commence AUCUN code avant validation architecture
❌ Ne calcule PAS baseline avec low(event_time) ou open(event_time)
❌ Ne dis PAS "ah désolé j'avais pas bien lu" après coup

═══════════════════════════════════════════════════════════════════

NE RÉPONDS RIEN D'AUTRE QUE LA CONFIRMATION QUIZ AVANT D'AVOIR 
LU ATTENTIVEMENT LES SECTIONS CRITIQUES.
```

---

## 📝 RÉPONSES ATTENDUES QUIZ

**Réponses correctes :**
- Baseline correct = **close(t-1)**
- Post-processing utilise extrema = **bruts**
- Patterns à créer Session 119 = **4** (SingleFort, ZigZag, SingleIntermediate, Classifier)
- Pullback Single Fort = **< 20%**
- Pullback Zig Zag = **< 20%**
- Référence code = **double_wave_detector.py**
- JSON Session 117 timestamps = **incorrects**

**Notes :**
- **Baseline :** close de la minute AVANT events (pas low ou open du moment events)
- **Post-processing :** extrema bruts pour trouver vrai pullback et wave2
- **Single Fort vs Zig Zag :** Tous deux < 20% pullback MAIS Single Fort = 1 pic, Zig Zag = 3+ pics
- **JSON Session 117 :** Timestamps incorrects → toujours récupérer données DB directement

---

## 🎯 OBJECTIFS SESSION 119

### **Objectif Principal**
Créer détecteurs patterns restants + classifier + validation automatique

### **Critères Succès**
- [ ] SingleWaveFortDetector validé (≥3 cas, MAE < 10 pips)
- [ ] ZigZagDetector validé (≥2 cas, MAE < 10 pips)
- [ ] SingleWaveIntermediateDetector créé
- [ ] PatternClassifier fonctionnel (80%+ précision)
- [ ] Script validation automatique opérationnel
- [ ] Documentation complète

### **Livrables Attendus**
1. `scripts/session119/pattern_detectors.py`
2. `scripts/session119/validate_all_patterns.py`
3. `scripts/session119/validation_report_s119.md`
4. `SESSION_119_RAPPORT_FINAL.md`
5. `SESSION_120_HANDOFF.md`

---

## 📚 FICHIERS CRITIQUES

### **Documentation (OBLIGATOIRE)**
```
/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/99_SESSIONS/SESSION_118_HANDOFF.md
  → Handoff Session 118→119 (guide complet)
  → CODE RÉUTILISABLE (fonctions get_events_from_db, get_baseline_price)
  → PLAN D'ACTION détaillé Phase 1-4
  → POINTS D'ATTENTION critiques

/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/99_SESSIONS/SESSION_118_RAPPORT_FINAL.md
  → Ce qui a été accompli Session 118
  → Découvertes clés
  → Problèmes en suspens
```

### **Code Référence (OBLIGATOIRE)**
```
/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session118/double_wave_detector.py
  → Architecture à réutiliser pour nouveaux détecteurs
  → Méthodes find_local_extrema(), filter_significant_extrema()
  → Pattern post-processing (extrema bruts)
```

### **Base Données**
```
/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb
  → Tables events, prices_bern (timezone UTC+2)
  → event_families (possiblement vide pour latency_median)
```

### **Documentation DB (SURVOL)**
```
/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/DATABASE_SCHEMAS.md
  → Structure tables (survol rapide si besoin)
```

---

## ⚠️ PIÈGES À ÉVITER

### **Erreur #1 : Utiliser timestamps JSON Session 117**
**Piège :** JSON contient timestamps incorrects (baseline 9 min trop tôt)  
**Solution :** Récupérer données DB directement avec approche event-driven

**Raison :** Session 118 a découvert erreurs fatales dans JSON

### **Erreur #2 : Baseline = low(event_time)**
**Piège :** Tentation d'utiliser low de la minute des events  
**Solution :** **Baseline = close(event_time - 1 minute)**

**Raison :** low capture spikes anormaux (Session 118 : 77.6 vs 51.7 pips)

### **Erreur #3 : Extrema filtrés pour post-processing**
**Piège :** Utiliser extrema_filtered pour trouver pullback/wave2  
**Solution :** Chercher dans extrema BRUTS (pas filtrés)

**Raison :** Filtres éliminent vrais points critiques (Session 118)

### **Erreur #4 : Confondre Single Fort et Zig Zag**
**Piège :** Les deux ont pullback < 20%  
**Solution :** 
- Single Fort = **1 pic dominant**
- Zig Zag = **3+ pics successifs**

**Raison :** Distinction basée sur nombre de pics, pas pullback ratio

### **Erreur #5 : event_families table vide**
**Piège :** Tenter d'utiliser latency_median qui n'existe pas  
**Solution :** Utiliser défaut 2.0 min si latency_median NULL

**Raison :** Table possiblement vide (à vérifier Session 119)

---

## 📊 PLAN SESSION (4 PHASES)

### **PHASE 1 : Single Wave Fort Detector** (2-3h)
**Objectif :** Créer détecteur montée directe 1 pic

**Étapes :**
1. Créer BasePatternDetector (méthodes communes de DoubleWaveDetector)
2. Créer SingleWaveFortDetector héritant de Base
3. Implémenter detect_pattern() :
   - Détecter extrema locaux
   - Trouver peak maximum après events
   - Vérifier pullback < 20%
   - Calculer impact
4. Trouver 3 cas réels dans DB (mouvements > 40 pips, 1 pic)
5. Tester et valider (MAE < 10 pips)

**Livrable :** SingleWaveFortDetector validé sur 3 cas

### **PHASE 2 : Zig Zag Detector** (2-3h)
**Objectif :** Créer détecteur montée escalier 3+ pics

**Étapes :**
1. Créer ZigZagDetector héritant de Base
2. Implémenter detect_pattern() :
   - Détecter tous peaks après events
   - Vérifier pullbacks < 20% entre chaque
   - Valider tendance continue (peaks croissants ±10%)
   - Calculer somme amplitudes
3. Trouver 2 cas réels dans DB (3+ pics successifs)
4. Tester et valider (MAE < 10 pips)

**Livrable :** ZigZagDetector validé sur 2 cas

### **PHASE 3 : Pattern Classifier** (1-2h)
**Objectif :** Décider automatiquement quel pattern

**Étapes :**
1. Créer PatternClassifier
2. Implémenter classify() :
   - Compter peaks significatifs
   - Mesurer pullbacks en %
   - Décider type pattern
3. Tester sur mix de patterns
4. Vérifier précision 80%+

**Livrable :** PatternClassifier fonctionnel

### **PHASE 4 : Validation Automatique** (2h)
**Objectif :** Script validation tous cas historiques

**Étapes :**
1. Créer validate_all_patterns.py
2. Boucle sur cas historiques :
   - Récupérer events DB
   - Calculer baseline
   - Détecter extrema
   - Classifier pattern
   - Appliquer détecteur approprié
   - Comparer avec MT5 réel
3. Statistiques (MAE, RMSE, R²)
4. Graphiques

**Livrable :** Rapport validation complet

---

## 💡 CODE RÉUTILISABLE SESSION 118

### **Fonction 1 : Récupération Events**
```python
def get_events_from_db(conn, start_time, end_time):
    """Récupère events depuis DB avec enrichissement"""
    query = """
        SELECT ts_utc as datetime, event_title, event_key,
               country, actual, estimate, previous,
               importance_n as importance
        FROM events
        WHERE ts_utc >= ? AND ts_utc <= ?
          AND actual IS NOT NULL
        ORDER BY ts_utc
    """
    df = conn.execute(query, [start_time, end_time]).df()
    # Enrichir avec latency_median + empirical_score
    return df
```

### **Fonction 2 : Baseline**
```python
def get_baseline_price(conn, event_time):
    """Close de la minute AVANT events"""
    baseline_time = event_time - timedelta(minutes=1)
    query = f"""
        SELECT close FROM prices_bern
        WHERE datetime = '{baseline_time.strftime('%Y-%m-%d %H:%M:%S%z')}'
    """
    return conn.execute(query).df()['close'].values[0]
```

### **Méthodes 3-4 : Extrema**
Copier de DoubleWaveDetector :
- `find_local_extrema(df, window=3)`
- `filter_significant_extrema(extrema_df, min_variation_pips=10)`

---

## 📋 DISTINCTION PATTERNS

| Pattern | Pics | Pullback | Impact | Formule |
|---------|------|----------|--------|---------|
| **Single Fort** | 1 | < 20% | > 40 pips | calculate_impact_d |
| **Single Intermediate** | 1 | < 20% | 20-40 pips | calculate_impact_d |
| **Double Wave** | 2 | 20-80% | Variable | calculate_double_wave_overlapping |
| **Zig Zag** | 3+ | < 20% | Variable | Sommation amplitudes |

**Points clés :**
- Single Fort vs Intermediate : **Amplitude** (> 40 vs 20-40 pips)
- Single Fort vs Zig Zag : **Nombre pics** (1 vs 3+)
- Double Wave vs Zig Zag : **Pullback ratio** (20-80% vs < 20%)

---

## 💡 CONSEILS

### **Avant de Coder**
1. ✅ Lire attentivement SESSION_118_HANDOFF.md (plan action + code réutilisable)
2. ✅ Lire double_wave_detector.py (architecture référence)
3. ✅ Répondre au QUIZ correctement
4. ✅ Proposer architecture et ATTENDRE validation

### **Pendant Développement**
1. ✅ Commencer par Single Fort (priorité #1, 95% cas réels)
2. ✅ Réutiliser find_local_extrema() et filter_significant_extrema()
3. ✅ Post-processing sur extrema bruts (pas filtrés)
4. ✅ Baseline = close(t-1) TOUJOURS
5. ✅ Tester progressivement (phase par phase)

### **En Cas de Problème**
1. Si extrema incorrects → vérifier window=3 cohérent
2. Si baseline bizarre → vérifier timezone UTC+2 Bern
3. Si pullback ratio faux → vérifier utilisation extrema bruts
4. Si bloqué → relire SESSION_118_HANDOFF.md section concernée

---

## 🎯 VALIDATION FIN SESSION 119

### **Checklist Succès**
- [ ] SingleWaveFortDetector validé (3 cas, MAE < 10 pips)
- [ ] ZigZagDetector validé (2 cas, MAE < 10 pips)
- [ ] SingleWaveIntermediateDetector créé
- [ ] PatternClassifier fonctionnel (80%+ précision)
- [ ] Script validation automatique
- [ ] Documentation complète (rapport + handoff S120)
- [ ] MASTER_PLAN.md mis à jour

### **Métriques Attendues**
- Single Fort MAE : < 10 pips
- Zig Zag MAE : < 10 pips
- Classifier précision : > 80%
- Tests patterns : ≥ 5 cas validés

---

**Auteur :** André Valentin avec Claude  
**Date :** 07 novembre 2025  
**Version :** 1.0  
**Session :** 118 → 119
