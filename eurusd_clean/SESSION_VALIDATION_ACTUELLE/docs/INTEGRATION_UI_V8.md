# Intégration UI V8 - Résumé

**Date** : 2025-01-XX  
**Objectif** : Brancher le moteur V8 backtesté dans le flux UI Calendrier et Planificateur

---

## ✅ Modifications Réalisées

### **1. Adaptateur V8 (`src/core/v8_ui_adapter.py`)**

**Fichier créé** : `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/src/core/v8_ui_adapter.py`

**Fonction principale** : `predict_cluster_v8()`

**Fonctionnalités** :
- Charge `stats_map`/`alpha_map` avec cache (évite rechargement)
- Construit `cluster_events` au format requis
- Appelle `calculate_cluster_impact_with_direction`
- Retourne format UI-friendly avec warnings SAFE runtime

**Output** :
```python
{
    'success': bool,
    'direction': 'UP' | 'DOWN' | 'UNKNOWN',
    'impact_pips': float,
    'pattern_type': 'single_wave' | 'double_wave' | 'zig_zag',
    'trigger_strength': float,
    'has_trigger': bool,
    'leg1': Optional[dict],
    'leg2': Optional[dict],
    'warnings': List[str],  # ⭐ SAFE runtime
    'skipped': bool,
    'skip_reason': Optional[str]
}
```

---

### **2. Calendrier (`streamlit_app/pages/1_Calendrier_Trading.py`)**

**Modifications** :
- Import adaptateur V8 (avec fallback si non disponible)
- Checkbox sidebar : "🔬 Utiliser moteur V8 (prédictions temps réel)"
- Calcul prédiction V8 pour chaque cluster si activé
- Affichage métriques V8 dans expander (direction, impact, pattern, trigger strength)
- Warnings SAFE affichés si `pct_missing > 10%` ou `skipped=True`

**Comportement** :
- Par défaut : utilise cache historique (comportement actuel)
- Si V8 activé : calcule prédiction temps réel et affiche badge "🔬V8"
- Fallback automatique si V8 échoue

---

### **3. Planificateur (`streamlit_app/pages/5_Planificateur_V3.2_Formule_Lineaire.py`)**

**Modifications** :
- Import adaptateur V8 (avec fallback si non disponible)
- Checkbox avant calcul : "🔬 Utiliser moteur V8 (backtesté)"
- Remplace `predict_double_wave_base` / `predict_single_wave_base` si V8 activé
- Affiche métriques V8 (direction, impact, pattern, trigger strength, cluster type)
- Warnings SAFE affichés si présents
- Format `prediction_result` compatible avec affichage existant (baseline_price, timeline, etc.)

**Comportement** :
- Par défaut : utilise formules validées actuelles (comportement actuel)
- Si V8 activé : utilise moteur V8 backtesté
- Fallback automatique si V8 échoue ou si actuals manquants

---

## 🔒 SAFE Runtime

**Warnings affichés si** :
1. `pct_missing_core_stats > 10%` : "⚠️ X% events core sans stats. Prédiction peut être moins fiable."
2. `skipped=True` : "⚠️ Prédiction non disponible: {skip_reason}"
3. Erreur lors de l'appel V8 : Message d'erreur détaillé

---

## 📋 Points d'Entrée UI Identifiés

### **Calendrier**
- **Fonction** : `build_future_clusters()` → merge avec cache → affichage
- **Point d'intégration** : Boucle `for _, row in filtered.iterrows()` (ligne ~372)
- **Calcul V8** : Avant affichage expander, si checkbox activé

### **Planificateur**
- **Fonction** : `predict_double_wave_base()` / `predict_single_wave_base()`
- **Point d'intégration** : Après saisie actuals, avant calcul prédiction (ligne ~4736)
- **Calcul V8** : Remplace calcul standard si checkbox activé

---

## 🧪 Tests à Effectuer

1. **Calendrier** :
   - [ ] Activer checkbox V8
   - [ ] Vérifier affichage prédictions V8
   - [ ] Vérifier warnings SAFE si présents
   - [ ] Vérifier fallback si V8 échoue

2. **Planificateur** :
   - [ ] Entrer actuals pour une date
   - [ ] Activer checkbox V8
   - [ ] Vérifier calcul prédiction V8
   - [ ] Vérifier affichage métriques V8
   - [ ] Vérifier compatibilité avec timeline/baseline_price

---

## 📝 Notes Techniques

- **Cache stats_map** : Évite rechargement à chaque appel (performance)
- **Fallback gracieux** : Si V8 non disponible ou échoue, utilise méthode standard
- **Compatibilité** : Format `prediction_result` compatible avec UI existante
- **Pas de régression** : Comportement par défaut inchangé (V8 optionnel)

---

**Version** : Integration UI V1  
**Status** : ✅ Complété (à tester)

