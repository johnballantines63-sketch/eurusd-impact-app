# 🚀 DÉMARRAGE RAPIDE - DEBUG GRAPHIQUE v8.6.5

**LECTURE : 3 MINUTES**  
**Date :** 16 octobre 2025

---

## LE PROBLÈME

**Graphique affiche valeurs ×9.3 trop élevées**

```
CALCUL INTERNE (logs)    GRAPHIQUE AFFICHÉ
Phase 1 : 260 pips ✅  →  2410 pips ❌ (×9.3)
Pullback: 180 pips ✅  →  2445 pips ❌
Phase 2 : 400 pips ✅  →  1561 pips ❌
```

---

## LA SOLUTION (3 ÉTAPES)

### ÉTAPE 1 : Ajouter prints DEBUG (5 min)

**Fichier 1 :** `fx_impact_app/src/sequence_multi_event_timeline_v86.py`

Chercher ligne ~500 (juste avant `phases.append(phase)`) et ajouter :

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

**Fichier 2 :** `fx_impact_app/src/price_curve_generator.py`

Chercher ligne ~365 (dans boucle génération) et ajouter :

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

### ÉTAPE 2 : Lancer test et capturer logs (5 min)

```bash
# Nettoyer
cd ~/Desktop/eurusd_news_impact_calculator_MPC
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
rm -rf ~/.streamlit/cache 2>/dev/null

# Lancer
streamlit run fx_impact_app/streamlit_app/Home.py

# Dans l'interface :
# 1. Page "Planificateur Multi-Événements"
# 2. Date : 11 septembre 2025
# 3. Cocher événements 14:30 et 14:45
# 4. Activer mode séquentiel
# 5. Cliquer "Générer Graphique"
# 6. COPIER TOUTE LA SORTIE CONSOLE
```

### ÉTAPE 3 : Analyser logs et corriger (30-60 min)

**VÉRIFIER DANS LES LOGS :**

#### A) Phase 1
```
🔍 DEBUG PHASE 1
Impact brut     : ~207 pips ← Doit être ~207
Multiplicateur  : 1.26×      ← Doit être 1.26
Impact final    : ~260 pips ← Doit être ~260
```

#### B) Phase 2
```
🔍 DEBUG PHASE 2
Impact brut     : ~25 pips   ← Doit être ~25
Pullback        : ~180 pips  ← Doit être ~180
Multiplicateur  : Variable   ← Calculer : 400/25 = 16×
Impact final    : ~400 pips  ← Doit être ~400
```

#### C) Graphique
```
Minute 0  : 1.16810 ← Départ
Minute 15 : ~1.1717 ← +360 pips (pic Phase 1, DOIT être ~1.17170)
Minute 40 : ~1.1738 ← +410 pips (pic Phase 2, DOIT être ~1.17380)
```

**DIAGNOSTIC :**

- **Si logs CORRECTS mais graphique FAUX** :
  → Problème affichage Plotly (axes/échelle)
  → Corriger create_sequential_phases_chart()

- **Si logs FAUX dès calcul** :
  → Problème multiplicateur ou générateur
  → Vérifier conditions ligne ~485-500 sequence_multi_event_timeline_v86.py

**CAUSES PROBABLES :**

1. **Multiplicateur ×8.8 appliqué partout** (probabilité haute)
   - Vérifier `elif phase_idx > 0 and pullback_pips > 0:`
   - S'assurer que ×8.8 n'est pas appliqué à Phase 1

2. **Double multiplication générateur** (probabilité moyenne)
   - Vérifier ligne ~362 : `impact_price = impact / 10000`
   - S'assurer division appliquée UNE SEULE fois

3. **Cumul phases** (probabilité élevée)
   - Vérifier si impacts s'additionnent au lieu d'être séquentiels

---

## APRÈS CORRECTION

**Créer v8.6.6 :**
```bash
# Backup
cp fx_impact_app/src/sequence_multi_event_timeline_v86.py \
   fx_impact_app/src/sequence_multi_event_timeline_v86.py.backup_v865

# Tester à nouveau
streamlit run fx_impact_app/streamlit_app/Home.py

# Vérifier graphique affiche maintenant :
# Phase 1 : ~1.17170 (+260 pips) ✅
# Phase 2 : ~1.17380 (+400 pips) ✅
```

**Documenter :**
```bash
# Créer rapport session
nano RAPPORT_CORRECTION_v866_GRAPHIQUE.md

# Noter :
# - Cause identifiée
# - Lignes modifiées
# - Tests validés
```

---

## FICHIERS RÉFÉRENCE

**Audit complet :** `AUDIT_COMPLET_PROJET_16OCT2025.md` (60-90 min lecture)

**Sections clés :**
- Section 4.1 : Problèmes identifiés
- Section 7.1 : Tests détaillés
- Section 8.1 : Recommandations

**Rapports précédents :**
- `RAPPORT_SESSION_v865_DEBUG_GRAPHIQUE.md` - Session précédente
- `rapport_session_complet_v865.md` - Contexte v8.6.5

---

## DONNÉES RÉFÉRENCE (11 SEPT 2025)

**Prix MT5 réels :**
```
14:30 → 1.16810 (départ)
14:35 → 1.17170 (+360 pips Phase 1)
14:45 → 1.16970 (-200 pips Pullback)
15:10 → 1.17380 (+410 pips Phase 2)
```

**Multiplicateurs v8.6.5 :**
```
Phase 1 : ×1.26 (207 → 260 pips)
Pullback: 12%/min × 0.73 (→ 180 pips)
Phase 2 : compensation + momentum ×8.8 (→ 400 pips)
```

---

## AIDE RAPIDE

**Rechercher dans code :**
```bash
# Multiplicateur ×8.8
grep "8.8" fx_impact_app/src/sequence_multi_event_timeline_v86.py

# Conversion pips→prix
grep "/ 10000" fx_impact_app/src/price_curve_generator.py

# Fonction pullback
grep -A 20 "def calculate_pullback" fx_impact_app/src/sequence_multi_event_timeline_v86.py
```

**Vérifier version :**
```bash
grep "Version 8.6" fx_impact_app/src/sequence_multi_event_timeline_v86.py
# Doit afficher : Version 8.6.5
```

---

## CONTACT CLAUDE SUIVANT

**Message à envoyer :**
```
Bonjour, je reprends le debug du graphique v8.6.5.

Problème : Graphique affiche 2410 pips au lieu de 260 pips (×9.3).

J'ai lu le DEMARRAGE_RAPIDE_DEBUG_v865.md.

Peux-tu m'aider à appliquer les 3 étapes :
1. Ajouter prints DEBUG
2. Lancer test 11 septembre 2025
3. Analyser logs et corriger

Merci !
```

---

**FIN - DÉMARRAGE RAPIDE**

**Temps estimé total :** 40-70 minutes  
**Résultat attendu :** v8.6.6 avec graphique corrigé
