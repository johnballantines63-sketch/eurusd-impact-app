# 🎯 SESSION 63 - Plan d'Exécution Détaillé

**Date:** 24 octobre 2025  
**Objectif:** Analyser le Pattern W sur les événements CPI  
**Budget tokens:** 90k tokens  

---

## ✅ ÉTAPE 1 : Test Infrastructure (MAINTENANT)

### A. Exécuter le test rapide

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean
python scripts/analysis/test_infrastructure.py
```

**Ce test vérifie :**
- ✅ Connexion à warehouse.duckdb
- ✅ Existence dates CPI
- ✅ Existence table prices_1min
- ✅ Période de données disponibles

**Résultat attendu :**
```
================================================================================
🧪 TEST INFRASTRUCTURE - SESSION 63
================================================================================
🔌 Test connexion base de données...
   Chemin DB: [...]/warehouse.duckdb
   ✅ Connexion réussie
   ✅ Nombre total d'événements: X,XXX

📅 Test chargement dates CPI...
   ✅ 5-10 dates CPI trouvées:
      - 2025-08-14: 9 événements
      - 2025-07-11: 9 événements
      [...]

💹 Test table prix MT5...
   ✅ Table prices_1min trouvée
   ✅ Nombre de lignes: XXX,XXX
   ✅ Période: 2024-XX-XX → 2025-XX-XX

================================================================================
✅ TOUS LES TESTS RÉUSSIS

🚀 Vous pouvez lancer l'analyse complète:
   python scripts/analysis/analyze_cpi_pattern_w.py
================================================================================
```

### B. Si tests échouent

**Problème possible 1 : Module duckdb manquant**
```bash
pip install duckdb pandas
```

**Problème possible 2 : DB introuvable**
→ Vérifier le chemin dans config.py

**Problème possible 3 : Table prices_1min manquante**
→ Vérifier si données MT5 importées

---

## ✅ ÉTAPE 2 : Analyse Pattern W (APRÈS tests réussis)

### A. Lancer l'analyse complète

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean
python scripts/analysis/analyze_cpi_pattern_w.py
```

**Le script va :**
1. Charger 5-10 dates CPI historiques
2. Pour chaque date :
   - Charger événements et prix
   - Détecter pattern (W ou linéaire)
   - Mesurer caractéristiques quantitatives
3. Calculer statistiques globales
4. Sauvegarder résultats CSV

**Durée estimée :** 30 secondes - 2 minutes

### B. Analyser les résultats

**Fichier généré :**
```
scripts/analysis/cpi_pattern_analysis_results.csv
```

**Questions à répondre :**

1. **Quelle est la fréquence du pattern W ?**
   - Si > 50% : Pattern W dominant → créer formules spécifiques
   - Si 30-50% : Pattern mixte → créer détecteur
   - Si < 30% : Pattern W exceptionnel → cas particulier

2. **Quelles sont les caractéristiques du pattern W ?**
   - Timing Peak 1 moyen : T+X min
   - Amplitude Peak 1 moyenne : XX pips (XX% impact total)
   - Timing Trough moyen : T+X min
   - Amplitude Trough moyenne : XX pips (XX% de Peak 1)
   - Timing Peak 2 moyen : T+X min
   - Amplitude Peak 2 moyenne : XX pips (XX% impact total)

3. **Le pattern W est-il corrélé à :**
   - Surprise élevée (> 30%) ?
   - Nombre d'événements simultanés (> 5) ?
   - Événement spécifique (Core CPI vs CPI) ?

---

## ✅ ÉTAPE 3 : Modélisation (Selon résultats ÉTAPE 2)

### Scénario A : Pattern W fréquent (>50%)

**Créer module de formules Pattern W :**

```bash
# Créer nouveau fichier
touch /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/app/core/formulas_pattern_w.py
```

**Contenu du module :**
```python
# formulas_pattern_w.py
# Session 63 - Formules pour Pattern W

def predict_peak1_timing(num_events: int, max_surprise: float) -> float:
    """Prédit timing du premier peak (minutes)"""
    # Basé sur analyse historique
    # Exemple : 5 + (num_events * 0.2)
    pass

def predict_peak1_amplitude(total_impact: float) -> float:
    """Prédit amplitude Peak 1 (% de l'impact total)"""
    # Exemple : 0.55 (55% de l'impact total)
    pass

def predict_trough_timing(peak1_time: float) -> float:
    """Prédit timing du trough (minutes)"""
    pass

def predict_trough_amplitude(peak1_amplitude: float) -> float:
    """Prédit amplitude trough (pips de descente)"""
    # Exemple : 0.84 * peak1_amplitude
    pass

def predict_peak2_timing(trough_time: float) -> float:
    """Prédit timing du deuxième peak (minutes)"""
    pass

def predict_peak2_amplitude(total_impact: float, peak1_amplitude: float) -> float:
    """Prédit amplitude Peak 2"""
    # Exemple : total_impact - peak1_amplitude
    pass
```

### Scénario B : Pattern W rare (<30%)

**Créer détecteur de pattern :**

```python
# Dans formulas_validated.py ou nouveau module

def detect_pattern_type(
    max_surprise: float,
    num_events: int,
    has_core_cpi: bool
) -> str:
    """
    Détecte si mouvement sera linéaire ou W
    
    Returns:
        'linear' ou 'w_shape'
    """
    # Règles empiriques basées sur analyse
    if max_surprise > 30 and num_events > 8:
        return 'w_shape'
    elif has_core_cpi and max_surprise > 25:
        return 'w_shape'
    else:
        return 'linear'
```

---

## ✅ ÉTAPE 4 : Amélioration Graphique Timeline

### Localiser le fichier à modifier

**Fichier :** 
```
/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/ui/streamlit_app/pages/5_Planificateur_V2_FORMULES_VALIDEES.py
```

**Fonction à réécrire :** `create_timeline_chart()` (ligne ~208)

### Nouvelle structure

```python
def create_timeline_chart_realistic(
    predictions: dict,
    start_price: float
) -> go.Figure:
    """
    Crée timeline réaliste selon pattern détecté
    """
    pattern_type = predictions.get('pattern_type', 'linear')
    
    if pattern_type == 'w_shape':
        return create_w_pattern_chart(predictions, start_price)
    else:
        return create_linear_pattern_chart(predictions, start_price)

def create_w_pattern_chart(predictions: dict, start_price: float) -> go.Figure:
    """
    Timeline Pattern W (5 phases)
    
    Phase 1a : Départ → Peak 1 (Montée 1)
    Phase 1b : Peak 1 → Trough (Pullback intermédiaire)
    Phase 1c : Trough → Peak 2 (Montée 2)
    Phase 2  : Peak 2 → TTR (Pullback majeur)
    Phase 3  : TTR → Reprise
    """
    # Implémenter avec 5 segments
    # Utiliser chandelier fictifs 1min pour chaque phase
    pass

def create_linear_pattern_chart(predictions: dict, start_price: float) -> go.Figure:
    """
    Timeline Pattern Linéaire (3 phases)
    
    Phase 1 : Départ → Peak (Montée unique)
    Phase 2 : Peak → TTR (Pullback)
    Phase 3 : TTR → Reprise
    """
    # Code existant adapté
    pass
```

---

## ✅ ÉTAPE 5 : Tests et Validation

### Test sur 11 septembre 2025

```python
# Script de test
from app.core.formulas_pattern_w import *

# Données 11 septembre
num_events = 9
max_surprise = 33.3
total_impact = 57  # pips

# Test prédictions
peak1_time = predict_peak1_timing(num_events, max_surprise)
peak1_amp = predict_peak1_amplitude(total_impact)

print(f"Peak 1 prédit : T+{peak1_time}min, {peak1_amp} pips")
print(f"Peak 1 réel : T+5min, 31 pips")

# Calculer erreur
mae_time = abs(peak1_time - 5)
mae_amp = abs(peak1_amp - 31)

print(f"MAE timing : {mae_time} min")
print(f"MAE amplitude : {mae_amp} pips")
```

**Critères de succès :**
- MAE timing < 3 minutes
- MAE amplitude < 10 pips

---

## ✅ ÉTAPE 6 : Documentation

### A. Créer rapport Session 63

**Fichier :** `docs/SESSION63_ANALYSE_PATTERN_W.md`

**Structure :**
```markdown
# Session 63 - Analyse Pattern W

## Résumé Exécutif
- Pattern W fréquence : XX%
- Caractéristiques quantitatives
- Décision modélisation

## Méthodologie
- Dates analysées
- Critères détection
- Limites

## Résultats Détaillés
- Tableau par date
- Statistiques agrégées
- Visualisations

## Modélisation
- Formules créées (si W fréquent)
- Détecteur créé (si W rare)
- Tests validation

## Amélioration Planificateur V2
- Modifications apportées
- Comparaison avant/après
- Exemple 11 septembre

## Conclusion
- Pattern W compris
- Timeline réaliste
- Prochaines étapes
```

### B. Mettre à jour project_state_new.md

**Ajouter section :**
```markdown
## Session 63 - Pattern W Analysé (24 oct 2025)

**Découverte :** Le mouvement CPI n'est pas linéaire mais en forme de W

**Fréquence Pattern W :** XX% des cas CPI

**Caractéristiques :**
- Peak 1 : T+Xmin, XX pips (XX% impact)
- Trough : T+Xmin, -XX pips
- Peak 2 : T+Xmin, XX pips (XX% impact)

**Modélisation :**
- [Si fréquent] Formules Pattern W créées
- [Si rare] Détecteur pattern créé
- Timeline Planificateur V2 améliorée

**Fichiers modifiés :**
- `app/core/formulas_pattern_w.py` (nouveau)
- `ui/streamlit_app/pages/5_Planificateur_V2_FORMULES_VALIDEES.py`
```

### C. Créer message Session 64

**Fichier :** `docs/MESSAGE_SESSION63_SESSION64.md`

**Contenu :**
- Résumé Session 63
- Pattern W analysé
- Fréquence et caractéristiques
- Modèle créé
- Prochaines missions

---

## 📊 Checklist Complète Session 63

### Phase 1 : Infrastructure ✅
- [ ] Test connexion DB réussi
- [ ] Dates CPI chargées
- [ ] Table prices_1min accessible

### Phase 2 : Analyse ⏳
- [ ] Script analyze_cpi_pattern_w.py exécuté
- [ ] 5+ dates CPI analysées
- [ ] Fréquence Pattern W déterminée
- [ ] Caractéristiques mesurées
- [ ] CSV résultats généré

### Phase 3 : Modélisation ⏳
- [ ] Formules Pattern W créées (si >50%)
- [ ] OU Détecteur pattern créé (si <30%)
- [ ] Tests validation sur 11 septembre
- [ ] MAE < seuils acceptables

### Phase 4 : Graphique ⏳
- [ ] create_timeline_chart() réécrit
- [ ] Support pattern W et linéaire
- [ ] Test visuel satisfaisant
- [ ] Comparaison MT5 validée

### Phase 5 : Documentation ⏳
- [ ] SESSION63_ANALYSE_PATTERN_W.md créé
- [ ] project_state_new.md mis à jour
- [ ] MESSAGE_SESSION63_SESSION64.md créé
- [ ] Budget tokens < 115k

---

## 🚀 Actions Immédiates

**MAINTENANT :**

1. ✅ Scripts créés
2. ⏳ **Exécuter test_infrastructure.py**
3. ⏳ Exécuter analyze_cpi_pattern_w.py
4. ⏳ Analyser résultats
5. ⏳ Décider modélisation

**Prêt à démarrer ! Lancez le test d'infrastructure. 🎯**

---

*Session 63 - Analyse Pattern W*  
*Tokens utilisés : ~40k / 190k*  
*Budget restant : ~150k*
