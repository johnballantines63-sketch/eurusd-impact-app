# 📋 PLAN SESSION 92.11 - APRÈS RÉSULTATS SESSION 92.10

**Date prévue :** 29-30 octobre 2025  
**Dépend de :** Résultats `execute_test_FIXED_TIMEZONE.py`  
**Budget estimé :** 60-80k tokens

---

## 🎯 MISSION SESSION 92.11

**Objectif :** Prendre décision finale formule impact direction

**Décision basée sur :** MAE Combined Session 92.10

---

## 📊 SCÉNARIO A : MAE COMBINED < 5 PIPS + 0 RÉGRESSIONS

### Verdict : ✅ SUCCÈS COMPLET - COMBINED VALIDÉ

**Conditions :**
- MAE Combined < 5.0 pips
- 0 régressions vs baseline (4/4 dates)
- MAE Combined < MAE V2

### Actions Session 92.11

**1. Analyse approfondie résultats (10k tokens)**
- Pourquoi Combined fonctionne mieux qu'attendu
- Analyser chaque date direction_sentiment vs résultat
- Identifier patterns communs

**2. Créer dataset 40 dates CPI (20k tokens)**

Script : `create_dataset_40_dates_CPI.py`

```python
def select_40_dates_cpi():
    """
    Sélectionne 40 dates CPI 2024-2025
    
    Critères :
    - US CPI (Core CPI, CPI YoY, CPI MoM)
    - Score > 40 (HIGH impact)
    - Diversité surprises (pos/neg, fortes/faibles)
    - Diversité impacts (20-60 pips)
    
    Returns:
        DataFrame 40 dates avec surprise_net et impact_reel
    """
```

**3. Tester Combined sur 40 dates (30k tokens)**

Script : `test_combined_40_dates.py`
- Réutilise `direction_sentiment_24h_FIXED_TIMEZONE.py`
- Calcule Baseline, V2, Combined pour 40 dates
- Génère CSV complet + métriques

**4. Validation statistique (10k tokens)**
- MAE global 40 dates
- Distribution erreurs
- Corrélation sentiment vs amélioration
- Tests significativité

**Budget total : 70k tokens**

**Résultat attendu :** Combined validé définitivement

---

## 📊 SCÉNARIO B : MAE COMBINED 5-8 PIPS

### Verdict : ⚠️ SUCCÈS PARTIEL - À APPROFONDIR

**Conditions :**
- MAE Combined 5-8 pips
- Quelques régressions (1-2 dates)
- MAE Combined < MAE V2 (légèrement)

### Actions Session 92.11

**Option B1 : Tester formule INVERSÉE**

Si analyse montre logique inversée (2+ dates) :

```bash
python3 test_formule_INVERSE.py
```

**Résultats possibles :**
- MAE inversé < 5 pips → Valider inversé sur 40 dates
- MAE inversé 5-8 pips → Choisir entre inversé/V2
- MAE inversé > 8 pips → Accepter V2

**Option B2 : Tester Combined sur 10-15 dates supplémentaires**

Si logique correcte mais variance élevée :
- Ajouter 10-15 dates CPI diverses
- Re-calculer MAE global 15-19 dates
- Si MAE < 6 pips → Valider 40 dates
- Si MAE > 6 pips → Accepter V2

**Budget : 50-60k tokens**

---

## 📊 SCÉNARIO C : MAE COMBINED > 8.5 PIPS (V2)

### Verdict : ❌ ÉCHEC - ACCEPTER V2

**Conditions :**
- MAE Combined > MAE V2 (8.5 pips)
- Ou MAE Combined 8-10 pips avec régressions

### Actions Session 92.11

**1. Analyse échec Combined (15k tokens)**
- Identifier pourquoi Combined échoue
- Vérifier logique inversée
- Analyser cas par cas

**2. Décision finale : V2 ou Inversé ? (5k tokens)**

**SI logique inversée détectée (2+ dates) :**
```bash
python3 test_formule_INVERSE.py
```

- MAE inversé < MAE V2 → Tester inversé 40 dates
- MAE inversé > MAE V2 → Accepter V2 définitivement

**SI logique correcte mais inefficace :**
- Accepter V2 (surprise nette) comme solution finale
- Direction_sentiment pas assez prédictif avec 4 dates

**3. Test V2 sur 40 dates CPI (40k tokens)**

Script : `test_v2_40_dates.py`
- Réutilise formules Sessions 51-55
- Calcule Baseline et V2 pour 40 dates
- Validation statistique finale

**Budget : 60k tokens**

**Résultat attendu :** V2 validé comme solution finale

---

## 🔬 ANALYSE LOGIQUE INVERSÉE (SI NÉCESSAIRE)

### Critères Détection

**Logique inversée présente si ≥2 dates montrent :**

**Pattern Reversal Haussier :**
- Surprise POSITIVE (+20% à +40%)
- Direction_sentiment NÉGATIF (-0.3 à -0.5)
- Combined ATTÉNUE au lieu AMPLIFIER
- Erreur Combined > Erreur V2

**Pattern Reversal Baissier :**
- Surprise NÉGATIVE (-50% à -100%)
- Direction_sentiment POSITIF (+0.3 à +0.5)
- Combined AMPLIFIE au lieu ATTÉNUER
- Erreur Combined > Erreur V2

### Vérification Automatique

Script `analyze_results_auto.py` détecte automatiquement :
```
🔍 ANALYSE ÉCHEC :
   ⚠️ 3/4 dates avec logique inversée
   → Combined atténue quand devrait amplifier (reversals)
   
➡️ RECOMMANDATION : Tester formule INVERSÉE
```

---

## 📁 SCRIPTS SESSION 92.11 REQUIS

### Si Scénario A (Succès Combined)

**Fichiers à créer :**
```
session92.11/
├── create_dataset_40_dates_CPI.py (200 lignes)
├── test_combined_40_dates.py (400 lignes)
└── analyze_combined_40_dates.py (300 lignes)
```

### Si Scénario B (Partiel)

**Option B1 - Formule inversée :**
```
session92.11/
├── test_formule_INVERSE.py ✅ (déjà créé session92.8)
└── analyze_inverse_results.py (150 lignes)
```

**Option B2 - Dates supplémentaires :**
```
session92.11/
├── add_10_dates_CPI.py (150 lignes)
└── test_combined_19_dates.py (350 lignes)
```

### Si Scénario C (Échec Combined)

**Fichiers à créer :**
```
session92.11/
├── test_v2_40_dates.py (350 lignes)
└── validate_v2_final.py (250 lignes)
```

---

## 🎯 DÉCISION FINALE SESSION 92.11

### Arbre Décision Complet

```
execute_test_FIXED_TIMEZONE.py (Session 92.10)
    ↓
MAE Combined ?
    ↓
    ├─ < 5 pips ✅ → Test Combined 40 dates → Validation finale
    │
    ├─ 5-8 pips ⚠️ → Analyse logique
    │                   ↓
    │                   ├─ Inversée ? → Test formule INVERSE
    │                   │                  ↓
    │                   │                  ├─ INVERSE < V2 → 40 dates INVERSE
    │                   │                  └─ INVERSE > V2 → Accepter V2
    │                   │
    │                   └─ Correcte ? → 10-15 dates sup → Décision finale
    │
    └─ > 8.5 pips ❌ → Analyse échec
                          ↓
                          ├─ Inversée ? → Test formule INVERSE
                          │                  ↓
                          │                  ├─ INVERSE < V2 → 40 dates INVERSE
                          │                  └─ INVERSE > V2 → Accepter V2
                          │
                          └─ Correcte ? → Accepter V2 → 40 dates V2
```

---

## 📊 MÉTRIQUES VALIDATION 40 DATES

### Objectifs Stricts

| Métrique | Objectif | Excellent | Inacceptable |
|----------|----------|-----------|--------------|
| MAE global | < 10 pips | < 7 pips | > 15 pips |
| RMSE | < 15 pips | < 10 pips | > 20 pips |
| Corrélation | > 0.5 | > 0.7 | < 0.3 |
| Régressions | < 10% | < 5% | > 20% |

### Tests Significativité

**Test t-Student :**
- H0 : Amélioration = hasard
- H1 : Amélioration significative
- p-value < 0.05 requis

**Bootstrap 1000 itérations :**
- Intervalle confiance 95%
- Validation robustesse

---

## 🔄 ITÉRATIONS POSSIBLES

### Si 40 dates insuffisantes

**Option 1 : Élargir à NFP (80 dates total)**
- 40 CPI + 40 NFP
- Valider généralisation multi-familles

**Option 2 : Calibration par type**
- CPI : Facteur X
- NFP : Facteur Y
- Création lookup table

**Option 3 : Machine Learning**
- Retour Sessions 74-76 (avec dataset >100)
- Régression + gradient boosting
- Validation cross-fold

---

## 💡 LEÇONS SESSION 92.11

### Méthodologie Rigoureuse

**FAIRE :**
- ✅ Analyser résultats 92.10 AVANT tout code
- ✅ Décision basée sur DONNÉES réelles
- ✅ Tests statistiques significativité
- ✅ Documentation honnête échecs

**NE PAS FAIRE :**
- ❌ Créer "tests simplifiés"
- ❌ Ignorer résultats négatifs
- ❌ Changer formules sans validation
- ❌ Complexifier sans amélioration mesurable

---

## 📋 CHECKLIST SESSION 92.11

**Avant démarrage :**
- [ ] Résultats Session 92.10 disponibles
- [ ] CSV `resultats_combined_FIXED_TIMEZONE.csv` généré
- [ ] Analyse automatique exécutée (`analyze_results_auto.py`)
- [ ] Scénario identifié (A/B/C)
- [ ] Budget tokens restant > 60k

**Pendant session :**
- [ ] Lire résultats 92.10 COMPLETS
- [ ] Analyser AVANT décision
- [ ] Suivre arbre décision ci-dessus
- [ ] Tests statistiques sur 40 dates
- [ ] Documentation complète

**Fin session :**
- [ ] Décision finale documentée
- [ ] Formule validée identifiée
- [ ] Prochaines étapes claires
- [ ] Rapport session créé
- [ ] Message transition session 92.12

---

## 🎯 OBJECTIF FINAL SESSION 92.11

**UNE SEULE formule validée pour production :**
- ✅ Combined (si MAE < 5-7 pips sur 40 dates)
- ✅ Combined INVERSÉ (si MAE < V2 sur 40 dates)
- ✅ V2 surprise nette (si Combined/Inversé échouent)

**Critères validation :**
- MAE < 10 pips (40 dates)
- RMSE < 15 pips
- p-value < 0.05 (amélioration significative)
- Robuste sur diversité cas

**Résultat attendu :**
- Formule prête intégration Planificateur V2.5
- Documentation complète
- Tests unitaires
- Guide utilisateur

---

_Plan Session 92.11 - Décision finale formule impact_  
_Flexible selon résultats Session 92.10_  
_Budget 60-80k tokens selon scénario_
