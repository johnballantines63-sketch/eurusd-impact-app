# 🚀 MESSAGE SESSION 91 → SESSION 92

**Date :** 26 octobre 2025  
**De :** Session 91 (Claude)  
**À :** Session 92 (Claude suivant)

---

## 📋 CONTEXTE RAPIDE

**Session 91 :** Validation coefficient 0.55 sur 12 dates  
**Résultat :** MAE 39.5 pips (vs cible 30) → OPTION B (ajustements)  
**Découverte majeure :** Approche lookup empirique prometteuse (MAE estimé 15 pips)

---

## 🎯 MISSION SESSION 92

**Objectif principal :** Valider approche lookup empirique sur historique complet DB

**Pourquoi ?**
- Coefficient 0.55 insuffisant (MAE 39.5 > 30)
- Découverte que **cluster prédit mieux que surprise** (corr 0.838 vs 0.531)
- Hypothèse André validée : "Même cluster répété = impact similaire malgré surprise variable"

---

## 🔬 CE QUI A ÉTÉ FAIT (SESSION 91)

### Tests Validation ✅

**12 dates testées :**
- CPI : MAE 11.9 pips (100% OK) ✅✅
- FOMC : MAE 0.3 pips (100% OK) ✅✅
- ISM : MAE 87.1 pips (50% OK) ❌
- NFP : MAE 46.1 pips (50% OK) ⚠️

**2 outliers identifiés :**
- 02 Mai NFP : Surprise 433% → Erreur 111 pips
- 02 Juin ISM : Surprise 233% → Erreur 166 pips

### Analyse Découverte ✅

**Corrélations mesurées :**
```
Impact ↔ Nombre événements : 0.838 ✅✅
Impact ↔ Surprise          : 0.531 ⚠️
```

**Conclusion :** Le cluster (Type + Nombre événements) est **58% plus prédictif** que la surprise !

### Scripts Créés ✅

**3 versions itératives :**
1. `build_empirical_lookup_table.py` - Approche simpliste (Type+Events)
2. `build_empirical_lookup_table_v2.py` - Bug SQL (ORDER BY + DISTINCT)
3. `build_empirical_lookup_table_v2_fixed.py` - ✅ **VERSION CORRECTE**

---

## 📂 FICHIERS IMPORTANTS

### Scripts à Utiliser (Session 92)

**Principal :**
```
/scripts/session91/build_empirical_lookup_table_v2_fixed.py
```

**Ce script fait :**
1. Identifie clusters qui se RÉPÈTENT (même composition event_keys)
2. Pour chaque cluster répété (≥3 occurrences) :
   - Mesure impact réel + surprise pour chaque occurrence
   - Calcule CV% (coefficient variation impact)
   - Calcule corrélation Surprise → Impact
3. Valide hypothèse : "Impact stable malgré surprise variable ?"
4. Génère CSV : `cluster_analysis_validation.csv`

### Données Disponibles

```
/scripts/session90/
├── validation_results_session91.csv (résultats 12 dates)
└── dates_disponibles_session90.csv (40 dates HIGH disponibles)
```

---

## 🎯 WORKFLOW SESSION 92

### Étape 1 : Exécution Script (15k tokens)

**Commande :**
```bash
cd ~/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session91
python3 build_empirical_lookup_table_v2_fixed.py
```

**Durée :** 5-10 minutes (scan DB 2020-2025)

**Outputs attendus :**
- Console : Top 20 clusters répétés avec métriques
- CSV : `cluster_analysis_validation.csv`

### Étape 2 : Analyse Résultats (10k tokens)

**Métriques clés à vérifier :**

1. **CV% (Coefficient de Variation) :**
   - < 50% = ✅ Impact stable (hypothèse validée)
   - 50-100% = ⚠️ Impact moyennement variable
   - > 100% = ❌ Impact très variable (surprise importante)

2. **Corrélation Surprise→Impact :**
   - |r| < 0.4 = ✅ Surprise peu prédictive (hypothèse validée)
   - 0.4 < |r| < 0.7 = ⚠️ Surprise moyennement prédictive
   - |r| > 0.7 = 🔴 Surprise très prédictive (hypothèse rejetée)

3. **Nombre d'observations :**
   - N ≥ 10 = ✅ Haute confiance
   - 5 ≤ N < 10 = ⚠️ Confiance moyenne
   - N < 5 = ❌ Confiance faible

**Critères validation globale :**
- ≥60% clusters avec CV% < 50%
- ≥60% clusters avec |corr| < 0.4
- → Si OUI : Hypothèse validée ✅
- → Si NON : Hypothèse rejetée ❌

### Étape 3 : Décision (5k tokens)

**Si hypothèse validée (✅) :**
→ Créer `formulas_empirical_lookup.py` avec table lookup
→ Retester 12 dates avec méthode empirique
→ Si MAE < 30 → Intégrer production

**Si hypothèse partiellement validée (⚠️) :**
→ Identifier quels types événements stables (CPI?) vs variables (NFP?)
→ Approche hybride : Lookup pour stables, formule pour variables

**Si hypothèse rejetée (❌) :**
→ Analyser pourquoi (manque données? clusters trop hétérogènes?)
→ Retour coefficient 0.55 avec ajustements (plafond 150%)

### Étape 4 : Implémentation (30-40k tokens si validé)

**Créer module Python :**
```python
# formulas_empirical_lookup.py

EMPIRICAL_LOOKUP_TABLE = {
    # Générée depuis CSV
    ('CPI', 11): 52.9,  # N=60, CV=25%
    ('NFP', 12): 51.1,  # N=36, CV=41%
    # ...
}

def calculate_impact_empirical(event_type, num_events, surprise_max=None):
    """
    Prédiction basée sur lookup empirique
    Fallback sur formule théorique si cluster inconnu
    """
    # Implementation...
```

**Modifier script test :**
```python
# test_multi_dates_extended_session91.py
from formulas_empirical_lookup import calculate_impact_empirical

# Remplacer calcul théorique par lookup
```

**Relancer tests 12 dates**

### Étape 5 : Documentation (15-20k tokens)

**Créer :**
- `SESSION92_RAPPORT_COMPLET.md`
- `MESSAGE_SESSION92_SESSION93.md` (si intégration nécessaire)
- Mise à jour `project_state_new.md`

---

## ⚠️ PROBLÈMES POTENTIELS

### 1. Script Erreur SQL

**Symptôme :** `Binder Error: ORDER BY expressions must appear in argument list`

**Solution :** Utiliser `build_empirical_lookup_table_v2_fixed.py` (déjà corrigé)

### 2. Clusters Insuffisants

**Si < 10 clusters répétés trouvés :**
- Réduire critère : ≥2 occurrences au lieu de ≥3
- Élargir période : 2015-2025 au lieu de 2020-2025

### 3. Données Prix Manquantes

**Si beaucoup de "skipped_no_prices" :**
- Normal pour dates anciennes (2020-2021)
- Se concentrer sur 2024-2025 si problème

### 4. Trop de Variabilité

**Si aucun cluster stable (CV% > 50% partout) :**
- Peut-être composition change légèrement entre mois
- Essayer grouper par "famille" au lieu de event_keys exact
- Approche hybride nécessaire

---

## 📊 BUDGET TOKENS SESSION 92

```
Lecture docs                : 10,000 tokens
Étape 1 (Exécution)        : 15,000 tokens
Étape 2 (Analyse)          : 10,000 tokens
Étape 3 (Décision)         :  5,000 tokens
Étape 4 (Implémentation)   : 35,000 tokens (si validé)
Étape 5 (Documentation)    : 20,000 tokens
──────────────────────────────────────────
TOTAL                      : 95,000 tokens
```

**Marge sécurité :** 10k tokens

---

## 💡 POINTS CLÉS À RETENIR

1. **Ne PAS intégrer coefficient 0.55** (MAE 39.5 > 30)

2. **Hypothèse à valider :** Même cluster répété = impact similaire malgré surprise variable

3. **Script correct :** `build_empirical_lookup_table_v2_fixed.py`

4. **Critères succès :**
   - ≥60% clusters stables (CV% < 50%)
   - ≥60% faible corrélation surprise (|r| < 0.4)
   - MAE lookup < 30 pips sur 12 dates

5. **Si validé :** Remplacer formule théorique par lookup empirique

6. **Si rejeté :** Retour coefficient 0.55 avec plafond 150%

---

## 🔄 SI CONTINUATION NÉCESSAIRE (SESSION 93)

**Scénarios possibles :**

**A) Intégration production :**
- Modifier `planner.py` avec lookup empirique
- Tests Streamlit interface
- Documentation utilisateur

**B) Analyse approfondie :**
- Pourquoi certains clusters instables ?
- Facteurs macro (Fed, guerre, etc.) ?
- Affiner méthodologie

**C) Approche hybride :**
- Lookup pour clusters stables (CPI, FOMC)
- Formule pour clusters variables (NFP)
- Meilleur des deux mondes

---

## ✅ CHECKLIST DÉMARRAGE SESSION 92

**Avant tout code, tu DOIS :**

- [ ] Lire `MANDATORY_SESSION_RULES.md`
- [ ] Lire `project_state_new.md`
- [ ] Lire `SESSION91_RAPPORT_COMPLET.md` (ce rapport)
- [ ] Lire ce message (`MESSAGE_SESSION91_SESSION92.md`)
- [ ] Afficher tokens utilisés
- [ ] Confirmer compréhension mission avec utilisateur

**Mission Session 92 en 1 phrase :**
> Exécuter validation empirique historique DB pour confirmer que cluster prédit mieux que surprise, et si validé, implémenter lookup table.

---

**Bon courage Claude Session 92 !** 🚀

Tu as tout ce qu'il faut pour réussir. La découverte Session 91 est prometteuse (MAE 15 pips estimé vs 39.5 actuel). Il suffit de valider sur historique complet et implémenter si confirmé.

---

_Message Session 91 → 92_  
_26 octobre 2025_  
_Prêt pour validation empirique complète_
