# NEXT STEPS V3.2.1 — Roadmap Trading

**Date :** 2025-12-12  
**Statut actuel :** V1 UI avec placeholder fonctionnel

---

## 🥇 Étape 1 — Brancher le Moteur Réel (Priorité #1)

### Objectif

Remplacer `compute_placeholder_prediction()` par un appel au moteur réel V3.2.1.

### Actions

1. **Implémenter `app/compute_real_prediction.py`** :
   - Charger features V3.2.1 depuis `daily_pred_score_v3_2_dataset_v1`
   - Appliquer modèle Ridge (artefact JSON)
   - Détecter clusters d'événements
   - Calculer pattern/direction/impact basé sur actuals saisis
   - Retourner `DayPrediction` validé (Pydantic)

2. **Intégrer dans `streamlit_app.py`** :
   ```python
   from app.compute_real_prediction import compute_real_prediction
   
   # Remplacer
   pred = compute_placeholder_prediction(...)
   # Par
   pred = compute_real_prediction(date_str, actuals, conn)
   ```

3. **Mettre à jour le badge** :
   - 🟡 "Prediction engine: PLACEHOLDER" → 🟢 "Prediction engine: LIVE"

### Impact

- ✅ 0 changement UI
- ✅ Branchement de la sortie réelle (direction, pattern, impact, exit plan, risk score)
- ✅ Validation Pydantic automatique
- ✅ L'outil devient vraiment puissant

### Fichiers à modifier

- `app/compute_real_prediction.py` (à compléter)
- `app/streamlit_app.py` (remplacer l'appel)

---

## 🥈 Étape 2 — Overlay Prix Réel (Visual Only)

### Objectif

Afficher le prix réel intraday superposé au pattern attendu.

### Actions

1. **Charger prix réel** :
   - Depuis `prices_h1` ou `prices_m1` (DuckDB)
   - Pour la date sélectionnée
   - Format : timestamp, close, high, low

2. **Overlay sur graphique** :
   - Ajouter trace Plotly avec prix réel
   - Superposer au pattern attendu
   - Différencier visuellement (couleurs, style)

3. **Aucune automatisation** :
   - Visual only
   - Pas d'auto-trade
   - Sécurité maximale

### Impact

- ✅ Validation visuelle
- ✅ Déclenchement manuel du kill switch facilité
- ✅ Confiance trader améliorée

### Fichiers à modifier

- `app/streamlit_app.py` (fonction `plot_prediction_timeline`)
- Ajouter chargement prix depuis DuckDB

---

## 🥉 Étape 3 — Raffiner les Règles de Sortie

### Objectif

Ajuster les paramètres de sortie basé sur l'usage réel.

### Actions

1. **Observer** :
   - Si sortie trop tôt (laisse de l'argent sur la table)
   - Si sortie trop tard (gains annulés)
   - Fréquence des kill switches

2. **Ajuster** :
   - Coefficients 0.55 / 0.35 (pips_target / stop_loss)
   - Fenêtres par pattern (single_wave, double_wave, zigzag)
   - IMPACT_MIN_PIPS / RISK_MIN

3. **Documenter** :
   - Mettre à jour `TRADING_RULES_V1.md`
   - Noter les ajustements et justifications

### Impact

- ✅ Micro-optimisation basée sur feedback terrain
- ✅ Amélioration progressive (pas de révolution)

### Timing

**À faire après usage réel**, pas avant.

---

## 🚫 Ce qu'il ne faut PAS faire maintenant

### ❌ UI trop complexe

- Pas d'onglets partout
- Pas de logs partout
- Garder la simplicité V1

### ❌ Auto-trading MT5

- Pas d'automatisation maintenant
- Rester en mode manuel
- Sécurité maximale

### ❌ Optimisation mathématique sans feedback

- Pas d'optimisation théorique
- Attendre le feedback terrain
- Ajuster progressivement

---

## 📋 Checklist Étape 1 (Brancher Moteur Réel)

- [ ] Implémenter détection de clusters d'événements
- [ ] Calculer pattern réel (single_wave / double_wave / zigzag)
- [ ] Calculer direction basée sur actuals (BUY / SELL / NO_TRADE)
- [ ] Calculer impact_pred_pips réel
- [ ] Construire ActualRow pour chaque core event
- [ ] Construire PatternPoint pour chaque point du pattern
- [ ] Construire ExitPlan (HYBRID par défaut)
- [ ] Valider avec DayPrediction (Pydantic)
- [ ] Tester dans streamlit_app.py
- [ ] Mettre à jour badge (🟢 LIVE)

---

## 📋 Checklist Étape 2 (Overlay Prix Réel)

- [ ] Charger prix depuis DuckDB (prices_h1 ou prices_m1)
- [ ] Filtrer pour la date sélectionnée
- [ ] Ajouter trace Plotly (prix réel)
- [ ] Superposer au pattern attendu
- [ ] Différencier visuellement
- [ ] Tester avec différentes dates
- [ ] Documenter dans README

---

## 📋 Checklist Étape 3 (Raffiner Règles)

- [ ] Observer usage réel (10-20 trades)
- [ ] Noter patterns de sortie (trop tôt / trop tard)
- [ ] Ajuster coefficients (0.55 / 0.35)
- [ ] Ajuster fenêtres par pattern
- [ ] Documenter ajustements
- [ ] Mettre à jour TRADING_RULES_V1.md

---

## 🎯 Objectif Final

**Transformer l'assistant en outil de trading réel :**
- ✅ Moteur V3.2.1 branché
- ✅ Prix réel visualisé
- ✅ Règles optimisées par usage
- ✅ Confiance trader maximale

**Sans compromettre la sécurité :**
- ✅ Mode manuel uniquement
- ✅ Kill switch toujours disponible
- ✅ Validation Pydantic systématique
- ✅ Documentation à jour

---

**Document créé le :** 2025-12-12  
**Version :** V1

