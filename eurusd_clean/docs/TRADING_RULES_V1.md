# TRADING_RULES_V1 — V3.2.1 (EURUSD) — READY TO TRADE

**Version:** V1  
**Model:** V3.2.1 additive (ridge alpha=0.1)  
**Signal table:** `daily_risk_signal_v3_2_1`  
**Date:** 2025-12-12

---

## 0) Objectif

Transformer une prédiction journalière (vol + direction + pattern) en un plan de trade **exécutable** :
- Décider TRADE / NO_TRADE
- Définir entrée (fenêtre) + sortie (fenêtre et/ou pips)
- Garantir une gestion conservatrice (pas de recherche du pic absolu)

---

## 1) Définitions

- **risk_score** : score de risque (0..1) produit par la pipeline (ou dérivé).
- **impact_pred_pips** : amplitude attendue (pips) issue du pattern/cluster.
- **direction** : BUY / SELL / NO_TRADE.
- **pattern** : single_wave / double_wave / zigzag.
- **core events** : events essentiels qui conditionnent la prédiction (Actuals à renseigner).
- **non-core events** : events affichés optionnellement, non requis pour décision.

---

## 2) Décision TRADE / NO_TRADE (gates durs)

### 2.1 NO_TRADE si l'une des conditions est vraie

- direction == NO_TRADE
- impact_pred_pips < IMPACT_MIN_PIPS
- risk_score < RISK_MIN
- nombre de core events == 0 (si direction BUY/SELL)
- incohérence visuelle flagrante (pattern réel ne ressemble pas à la prédiction) → **KILL SWITCH**

### 2.2 TRADE autorisé si toutes vraies

- direction ∈ {BUY, SELL}
- impact_pred_pips ≥ IMPACT_MIN_PIPS
- risk_score ≥ RISK_MIN
- ≥ 1 core event renseignable (previous + forecast disponibles)

**Paramètres (V1):**
- IMPACT_MIN_PIPS = 40
- RISK_MIN = 0.60

---

## 3) Entrée (time-based, conservatrice)

L'entrée est **une fenêtre**, pas un prix absolu.

### 3.1 Fenêtre par défaut

- Entry window = [T0 + 15min, T0 + 45min]

où **T0 = heure du premier core event du cluster**.

### 3.2 Règle d'annulation (avant entrée)

- Si l'évolution réelle est déjà contraire à la direction (ex: SELL mais impulsion haussière forte et persistante) → NO_TRADE.

---

## 4) Sortie (objectif "trades gagnants", pas "pic absolu")

### 4.1 Modes

- **TIME_WINDOW** : sortir dans [T_exit_start, T_exit_end]
- **PIPS_TARGET** : sortir à +pips_target (BUY) / -pips_target (SELL)
- **HYBRID (défaut)** : sortir au premier atteint entre time_window et pips_target

### 4.2 Paramètres conservateurs (V1)

- pips_target = clamp( 0.55 * impact_pred_pips, 20, 80 )
- stop_loss_pips = clamp( 0.35 * impact_pred_pips, 15, 60 )
- exit time window par pattern:
  - single_wave: [T0+60min, T0+180min]
  - double_wave: [T0+90min, T0+240min]
  - zigzag:      [T0+120min, T0+300min]

---

## 5) KILL SWITCH (sécurité ++)

### 5.1 Conditions de sortie manuelle immédiate

- divergence visuelle persistante vs pattern attendu
- volatilité réelle >> prédiction (spike inattendu)
- actuals saisis rendent la direction inversée

---

## 6) Workflow (trader)

1) Ouvrir Calendar → choisir date (tri par risk_score, impact)
2) Ouvrir Day Detail
3) Renseigner Actuals (core only)
4) Recalcul → vérifier direction/pattern/impact
5) Si gates OK → exécuter entrée dans la fenêtre
6) Appliquer HYBRID exit (pips_target / time_window)
7) Si divergence → kill switch

---

## 7) Backlog (non bloquant)

- Brancher prix réel live + overlay
- Export des ordres vers MT5 (plus tard)
- Auto-collect actuals via API (plus tard)

---

**Document créé le :** 2025-12-12  
**Version :** V1

