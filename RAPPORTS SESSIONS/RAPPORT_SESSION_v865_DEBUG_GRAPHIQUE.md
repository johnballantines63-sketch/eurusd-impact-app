# 📊 RAPPORT SESSION v8.6.5 → DEBUG GRAPHIQUE
**Date :** 16 octobre 2025  
**Durée :** ~2 heures  
**Tokens utilisés :** ~120K / 190K (63%)  
**Objectif :** Identifier pourquoi le graphique affiche des valeurs 10× trop élevées

---

## 🎯 CONTEXTE DE LA SESSION

### Situation de départ
L'utilisateur a lu le rapport complet `rapport_session_complet_v865.md` qui documentait :

- **v8.6.4** : Suppression atténuation (facteur minimum 1.00)
- **v8.6.5** : Effet Rebond implémenté (compensation pullback + momentum ×8.8)
- **Problème découvert** : Le graphique affiche des valeurs incorrectes

### Données de référence (11 septembre 2025)

**Prix MT5 réels :**
```
14:30 → 1.16810 (départ)
14:35 → 1.17170 (+360 pips Phase 1) 
14:45 → 1.16970 (-200 pips Pullback)
15:10 → 1.17380 (+410 pips Phase 2)
```

**Graphique v8.6.5 (FAUX) :**
```
Départ → 1.16810 ✅ OK
Pic P1 → 1.19220 ❌ (+2410 pips au lieu de +360)
Pullback → 1.14525 ❌ (-2445 pips)
Pic P2 → 1.18941 ❌ (+1561 pips)
```

**Ratio d'erreur :** ~10× trop fort (2410 / 260 = ×9.27)

---

## 🔍 ANALYSE EFFECTUÉE

### Fichiers lus et analysés

1. **`forecaster_mvp.py`** (calcul impact brut)
   - Calcule MFE P80 historique
   - Retourne impact en pips (ex: 207 pips)
   - ✅ Pas de problème identifié ici

2. **`sequence_multi_event_timeline_v86.py`** (application multiplicateurs)
   - **Ligne ~480-550** : Application multiplicateurs v8.6.5
   - **Phase 1 (ligne 490)** : `impact_combined *= 1.26` → 260 pips
   - **Phase 2 (ligne 493-497)** : 
     ```python
     compensation = pullback_pips  # 180 pips
     momentum = impact_combined * 8.8  # 220 pips
     impact_combined = compensation + momentum  # 400 pips
     ```
   - ⚠️ **ZONE SUSPECTE** : Le multiplicateur ×8.8 est très élevé

3. **`price_curve_generator.py`** (génération courbe)
   - **Ligne 362** : `impact_price = impact / 10000` (conversion pips → prix)
   - **Ligne 365** : `target_price = phase_start_price + (impact_price * sigmoid_progress)`
   - ✅ La conversion semble correcte

4. **Planificateur** (`4_Planificateur-Multi-Evenements.py`)
   - **Ligne ~2000-2100** : Appel au générateur de graphique
   - **Ligne ~2093** : Boucle commentée qui écrasait `events_for_generator` (déjà corrigée)
   - ✅ Pas de double multiplication détectée ici

---

## 🚨 HYPOTHÈSES SUR LA CAUSE

### Hypothèse 1 : Multiplicateur ×8.8 appliqué partout ⚠️
**Probabilité : MOYENNE**

Le multiplicateur ×8.8 de la Phase 2 pourrait être appliqué même quand :
- Il n'y a pas de pullback
- Pour toutes les phases
- Deux fois de suite

**À vérifier :**
```python
# Dans sequence_multi_event_timeline_v86.py ligne ~493
elif phase_idx > 0 and pullback_pips > 0:
    compensation = pullback_pips
    momentum = impact_combined * 8.8  # ← Ce calcul est-il toujours exécuté ?
    impact_combined = compensation + momentum
```

### Hypothèse 2 : Confusion pips/prix dans le générateur ⚠️
**Probabilité : FAIBLE**

Possible que quelque part, `impact_combined` soit traité comme un prix au lieu de pips.

**À vérifier :**
- Le générateur reçoit-il bien des **pips** dans `phase['impact_combined']` ?
- La conversion `/10000` est-elle appliquée une seule fois ?

### Hypothèse 3 : Cumul des impacts phases ⚠️
**Probabilité : ÉLEVÉE**

Le générateur pourrait **additionner** les impacts de toutes les phases au lieu de les appliquer séquentiellement.

**À vérifier dans `price_curve_generator.py` ligne ~320-400** :
- Comment sont gérées les phases multiples ?
- Y a-t-il un cumul involontaire ?

### Hypothèse 4 : Bug dans la fonction commentée V3 ⚠️
**Probabilité : MOYENNE**

Il reste du code commenté (ligne 324-343 de `price_curve_generator.py`) d'un ancien système vectoriel. Peut-être qu'une partie de ce code s'exécute encore ?

**À vérifier :**
- Tous les blocs `# [ANCIEN CODE]` sont-ils vraiment désactivés ?
- Y a-t-il une variable globale modifiée ?

---

## 🎯 CE QUI N'A PAS ÉTÉ VÉRIFIÉ (CRITIQUE)

### 1. Valeurs réelles dans `phases` ⚠️⚠️⚠️
**Je n'ai PAS vérifié les valeurs EXACTES stockées dans `phases` après le calcul.**

**À faire :**
```python
# Ajouter ces prints dans sequence_multi_event_timeline_v86.py ligne ~500
print(f"DEBUG Phase {phase_idx + 1}:")
print(f"  impact_combined_raw = {impact_combined_raw:.1f}")
print(f"  attenuation_factor = {attenuation_factor:.2f}")
print(f"  pullback_pips = {pullback_pips:.1f}")
print(f"  FINAL impact_combined = {impact_combined:.1f}")
```

### 2. Flux complet de l'impact ⚠️⚠️⚠️
**Je n'ai PAS tracé l'impact minute par minute dans le générateur.**

**À faire :**
- Ajouter des prints dans `generate_candlestick_curve_from_phases()` :
  ```python
  # Ligne ~365
  print(f"Minute {minute}: impact={impact:.1f} pips, "
        f"impact_price={impact_price:.5f}, "
        f"target_price={target_price:.5f}")
  ```

### 3. Conversion Timestamp dans le générateur ⚠️
**La correction pandas (ligne 508-511) pourrait causer un effet de bord.**

**À vérifier :**
- Les conversions `.to_pydatetime()` fonctionnent-elles correctement ?
- Y a-t-il des erreurs silencieuses ?

### 4. Ordre d'exécution des phases ⚠️
**Les phases sont-elles appliquées dans le bon ordre ?**

**À vérifier :**
- Le générateur traite-t-il Phase 1 puis Phase 2 séquentiellement ?
- Ou y a-t-il un chevauchement/cumul ?

---

## 🔧 PLAN D'ACTION POUR PROCHAINE SESSION

### ÉTAPE 1 : Audit avec prints DEBUG (15 min)

**Fichier 1 : `sequence_multi_event_timeline_v86.py`**

Ajouter après la ligne ~500 (juste avant `phases.append(phase)`) :

```python
# === DEBUG v8.6.6 : Tracer impact exact ===
print(f"\n{'='*60}")
print(f"🔍 DEBUG PHASE {phase_idx + 1}")
print(f"{'='*60}")
print(f"Impact brut calculé     : {impact_combined_raw:.1f} pips")
print(f"Facteur atténuation     : {attenuation_factor:.2f}")
print(f"Pullback depuis Phase-1 : {pullback_pips:.1f} pips")
print(f"Multiplicateur appliqué : {impact_combined / impact_combined_raw if impact_combined_raw != 0 else 0:.2f}×")
print(f"➡️ IMPACT FINAL          : {impact_combined:.1f} pips")
print(f"Direction               : {combined_direction}")
print(f"{'='*60}\n")
# === FIN DEBUG ===
```

**Fichier 2 : `price_curve_generator.py`**

Ajouter après la ligne ~365 :

```python
# === DEBUG v8.6.6 : Tracer génération courbe ===
if minute % 5 == 0:  # Afficher toutes les 5 minutes
    print(f"📊 Minute {minute:3d} | "
          f"Phase: {active_phase_label:12s} | "
          f"Impact: {impact_price*10000:+7.1f} pips | "
          f"Target: {target_price:.5f} | "
          f"Current: {current_mid_price:.5f}")
# === FIN DEBUG ===
```

**Test à effectuer :**
```bash
cd ~/Desktop/eurusd_news_impact_calculator_MPC
# Nettoyer caches
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null

# Lancer Streamlit
streamlit run fx_impact_app/streamlit_app/Home.py

# Dans l'interface :
# 1. Aller sur "Planificateur Multi-Événements"
# 2. Charger 11 septembre 2025
# 3. Cocher événements 14:30 et 14:45
# 4. Activer mode séquentiel
# 5. Générer graphique
# 6. COPIER LA SORTIE CONSOLE COMPLÈTE
```

### ÉTAPE 2 : Analyser les logs DEBUG (10 min)

**Vérifier dans les logs :**

1. **Phase 1** : 
   - Impact brut ≈ 207 pips
   - Multiplicateur = 1.26
   - Impact final ≈ 260 pips ← **Doit être ~260**

2. **Phase 2** :
   - Impact brut ≈ 25 pips
   - Pullback ≈ 180 pips
   - Momentum = 25 × 8.8 ≈ 220 pips
   - Impact final = 180 + 220 ≈ 400 pips ← **Doit être ~400**

3. **Graphique** :
   - Minute 0 : 1.16810 (départ)
   - Minute 5 : ~1.1695 (+185 pips en progression)
   - Minute 15 : ~1.1717 (+360 pips = pic Phase 1) ← **Doit être ~1.17170**
   - Minute 25 : ~1.1697 (après pullback)
   - Minute 40 : ~1.1738 (+410 pips = pic Phase 2) ← **Doit être ~1.17380**

**Si les valeurs sont CORRECTES dans les logs mais FAUSSES sur le graphique :**
→ Le problème est dans l'affichage Plotly (axes, échelle, annotations)

**Si les valeurs sont FAUSSES dès les logs :**
→ Le problème est dans le calcul (sequence ou generator)

### ÉTAPE 3 : Corriger selon diagnostic (30-60 min)

**Scénario A : Multiplicateur ×8.8 appliqué partout**

Corriger dans `sequence_multi_event_timeline_v86.py` ligne ~493-500 :

```python
# AVANT (v8.6.5)
elif phase_idx > 0 and pullback_pips > 0:
    compensation = pullback_pips
    momentum = impact_combined * 8.8
    impact_combined = compensation + momentum

# APRÈS (v8.6.6) - Vérifier conditions
elif phase_idx > 0:  # Seulement Phase 2+
    if pullback_pips > 0:  # ET pullback détecté
        compensation = pullback_pips
        momentum = impact_combined * 8.8
        impact_combined = compensation + momentum
    else:
        impact_combined *= 1.5  # Pas de pullback : multiplicateur normal
```

**Scénario B : Conversion pips/prix incorrecte**

Vérifier dans `price_curve_generator.py` ligne ~362 :

```python
# Vérifier que impact est TOUJOURS en pips
impact = phase['impact_combined']  # EN PIPS
impact_price = impact / 10000  # Conversion pips → prix EUR/USD

# Ajouter assertion pour sécurité
assert 0 < impact < 1000, f"Impact invalide : {impact} pips (doit être 0-1000)"
```

**Scénario C : Cumul phases dans générateur**

Vérifier dans `price_curve_generator.py` ligne ~320-400 :
- S'assurer que chaque phase démarre depuis `phase_start_price` (pas un cumul)
- Vérifier la gestion de `cumulative_price`

### ÉTAPE 4 : Validation finale (10 min)

**Créer un test unitaire :**

```python
# test_impact_flow.py
def test_impact_calculation():
    # Test Phase 1
    impact_brut = 207
    multiplicateur = 1.26
    impact_final = impact_brut * multiplicateur
    assert abs(impact_final - 260) < 1, f"Phase 1 incorrect: {impact_final}"
    
    # Test Phase 2 avec Rebond
    impact_brut_p2 = 25
    pullback = 180
    momentum = impact_brut_p2 * 8.8
    impact_final_p2 = pullback + momentum
    assert abs(impact_final_p2 - 400) < 10, f"Phase 2 incorrect: {impact_final_p2}"
    
    # Test conversion pips → prix
    prix_depart = 1.16810
    impact_pips = 260
    prix_attendu = prix_depart + (impact_pips / 10000)
    assert abs(prix_attendu - 1.17070) < 0.0001, f"Conversion incorrecte: {prix_attendu}"
    
    print("✅ Tous les tests passent")

if __name__ == "__main__":
    test_impact_calculation()
```

---

## 📋 ÉTAT DES FICHIERS

### Fichiers MODIFIÉS dans cette session
**Aucun** - Session d'analyse uniquement

### Fichiers à MODIFIER dans la prochaine session
1. `sequence_multi_event_timeline_v86.py` (ajouter prints DEBUG)
2. `price_curve_generator.py` (ajouter prints DEBUG)
3. Possiblement corrections selon diagnostic

### Fichiers de référence importants
- `rapport_session_complet_v865.md` - Contexte complet v8.6.4→v8.6.5
- `RAPPORT_CORRECTIONS_V8.6.4_ZERO_ATTENUATION.md` - Détails v8.6.4
- `RAPPORT_CORRECTIONS_V8.6.3_CALIBRATION_MT5.md` - Détails v8.6.3

---

## 🎯 RÉSUMÉ EXÉCUTIF

### Ce qu'on sait
✅ Le problème affecte l'affichage graphique (valeurs ×10 trop fortes)  
✅ Les multiplicateurs v8.6.5 sont implémentés : Phase 1 ×1.26, Phase 2 Rebond  
✅ La structure du code est correcte (pas de boucle orpheline)  
✅ La conversion pips→prix utilise `/10000` (semble correcte)

### Ce qu'on ne sait PAS encore ⚠️
❌ Les valeurs EXACTES dans `phases` après calcul  
❌ Les valeurs EXACTES utilisées par le générateur minute par minute  
❌ Si le multiplicateur ×8.8 est appliqué correctement (seulement Phase 2 avec pullback)  
❌ Si les phases sont traitées séquentiellement ou cumulativement

### Cause la plus probable
**Le multiplicateur ×8.8 est appliqué à toutes les phases au lieu de seulement Phase 2 avec pullback.**

Ratio observé : ×9.27 ≈ 1.26 (Phase 1) + 8.8 (Rebond) = ×10.06

### Action prioritaire prochaine session
**AJOUTER LES PRINTS DEBUG ET RELANCER LE TEST**

Durée estimée : 15 minutes  
Résultat attendu : Logs console avec valeurs exactes à chaque étape

---

## 💡 RECOMMANDATIONS

### Pour l'utilisateur
1. **Garder ce rapport** comme référence pour la prochaine session
2. **Ne pas modifier le code** avant d'avoir les logs DEBUG
3. **Tester d'abord sur le 11 septembre 2025** (cas de référence bien documenté)
4. **Copier TOUTE la sortie console** (pas seulement le graphique)

### Pour Claude suivant
1. **LIRE CE RAPPORT EN ENTIER** avant de commencer
2. **AJOUTER LES PRINTS DEBUG** (Étape 1) immédiatement
3. **ANALYSER LES LOGS** (Étape 2) pour identifier la cause exacte
4. **CORRIGER** (Étape 3) seulement après avoir compris le problème
5. **NE PAS deviner** - suivre la méthode scientifique

### Phrases clés pour Claude suivant
- "Le graphique affiche 2410 pips au lieu de 360 pips pour Phase 1 (ratio ×6.7)"
- "Les multiplicateurs v8.6.5 sont : Phase 1 ×1.26, Phase 2 Rebond = compensation + momentum ×8.8"
- "Cause probable : multiplicateur ×8.8 appliqué partout au lieu de seulement Phase 2"
- "ACTION REQUISE : Ajouter prints DEBUG selon Étape 1 du plan d'action"

---

## 📊 MÉTRIQUES SESSION

**Durée :** ~2 heures  
**Tokens utilisés :** ~120K / 190K (63%)  
**Fichiers lus :** 4 (forecaster, sequence, generator, planificateur)  
**Lignes de code analysées :** ~800  
**Hypothèses formulées :** 4  
**Tests effectués :** 0 (analyse uniquement)  
**Corrections appliquées :** 0  
**Clarté du diagnostic :** 60% (besoin de logs DEBUG)

---

## 🚀 POUR DÉMARRER LA PROCHAINE SESSION

**Copier-coller ce message à Claude :**

```
Bonjour Claude,

Je reprends le debug du graphique v8.6.5 qui affiche des valeurs 10× trop élevées.

CONTEXTE :
- Fichier rapport : RAPPORT_SESSION_v865_DEBUG_GRAPHIQUE.md
- Problème : Graphique affiche 2410 pips au lieu de 360 pips (Phase 1)
- Cause probable : Multiplicateur ×8.8 appliqué partout

ACTION IMMÉDIATE :
Lis le rapport complet puis applique l'ÉTAPE 1 du plan d'action :
- Ajouter prints DEBUG dans sequence_multi_event_timeline_v86.py (ligne ~500)
- Ajouter prints DEBUG dans price_curve_generator.py (ligne ~365)
- Relancer le test sur 11 septembre 2025
- Analyser les logs console

Le rapport contient TOUT le contexte nécessaire. Ne commence RIEN avant de l'avoir lu.
```

---

**Date création :** 16 octobre 2025  
**Version projet :** v8.6.5 (avec bug graphique)  
**Prochaine version :** v8.6.6 (correction après diagnostic)  
**Status :** 🔴 DEBUG EN COURS - LOGS REQUIS

---

**✅ FIN DU RAPPORT DE SESSION**

**🔑 Fichiers critiques pour prochaine session :**
1. Ce rapport (RAPPORT_SESSION_v865_DEBUG_GRAPHIQUE.md)
2. rapport_session_complet_v865.md (contexte v8.6.5)
3. sequence_multi_event_timeline_v86.py (ligne ~490-550)
4. price_curve_generator.py (ligne ~320-400)

**⏱️ Temps estimé prochaine session :** 1-2 heures (debug + correction + test)
