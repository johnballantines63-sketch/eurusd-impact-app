# EXEMPLE COMPLET — Une Journée → Une Décision de Trade

**Date :** 2025-12-12  
**Version :** V3.2.1  
**Objectif :** Démontrer le workflow complet depuis la prédiction jusqu'à la décision de trade

---

## 📅 Journée Sélectionnée : 2024-09-11

**Raison :** Date avec événements US majeurs (CPI + autres), pattern double_wave observé historiquement.

---

## Étape 1 : Consultation Calendar

### 1.1 Ouvrir l'UI Streamlit

```bash
streamlit run app/streamlit_app.py
```

### 1.2 Consulter Calendar

**Requête SQL :**
```sql
SELECT date, pred_vol_pips
FROM daily_risk_signal_v3_2_1
WHERE date = '2024-09-11'
ORDER BY date DESC
LIMIT 10;
```

**Résultat attendu :**
- `date: 2024-09-11`
- `pred_vol_pips: ~66.7` (exemple)

**Action :** Sélectionner cette date dans le calendar.

---

## Étape 2 : Day Detail — Consultation Events

### 2.1 Charger Events

**Requête SQL :**
```sql
SELECT
    ts_local,
    country,
    event_key,
    event_title,
    importance_n,
    previous,
    forecast
FROM events_with_ts_local_v1
WHERE DATE(ts_local) = '2024-09-11'
ORDER BY ts_local ASC;
```

**Résultat attendu :**
- CPI (US) : 14:30, importance=5, previous=3.1, forecast=3.0
- Current Account (US) : 14:45, importance=3, previous=-200B, forecast=-195B
- Autres événements optionnels

### 2.2 Identifier Core Events

**Règle :** `importance_n >= 4` OU `country = 'US'`

**Core events identifiés :**
- ✅ CPI (importance=5, US)
- ✅ Current Account (US, même si importance=3)

**Action :** Vérifier que les core events sont affichés par défaut.

---

## Étape 3 : Saisie Actuals

### 3.1 Attendre la Publication

**Timeline :**
- 14:30 : CPI publié
- 14:45 : Current Account publié

### 3.2 Saisir Actuals

**Dans l'UI :**
1. Trouver la ligne CPI (14:30 — US — CPI)
2. Saisir `actual = 3.2` (exemple : inflation plus élevée que prévu)
3. Trouver la ligne Current Account
4. Saisir `actual = -210B` (exemple)

**Résultat :**
- Actuals stockés en session state
- Format : `{"2024-09-11::0": 3.2, "2024-09-11::1": -210.0}`

---

## Étape 4 : Recalcul avec Moteur Réel

### 4.1 Activer Moteur Réel

**Dans l'UI :**
1. Cocher "🟢 Utiliser moteur réel V3.2.1"
2. Cliquer "Recalculer prédiction"

### 4.2 Calculs Effectués

**4.2.1 Détection Clusters :**
- Cluster 1 : CPI (14:30)
- Cluster 2 : Current Account (14:45)
- Délai : 15 minutes → **double_wave** (clusters proches)

**4.2.2 Calcul Direction :**
- CPI : actual=3.2, forecast=3.0 → surprise=+6.67%
- CPI = famille inversée → surprise positive = bad news USD → **EUR/USD UP (+1)**
- Current Account : actual=-210B, forecast=-195B → surprise négative → **EUR/USD DOWN (-1)**
- **Direction nette : BUY** (CPI domine)

**4.2.3 Calcul Impact :**
- CPI : importance=5, surprise=6.67% → impact ~60 pips
- Current Account : importance=3, surprise négative → impact ~25 pips
- **Impact total : ~85 pips**

**4.2.4 Pattern :**
- 2 clusters, délai 15 min → **double_wave**

**4.2.5 Fenêtres :**
- Entry : [14:45, 15:15] (T0=14:30 + 15-45 min)
- Exit : [15:00, 16:00] (double_wave : T0+90-240 min)

**4.2.6 Targets :**
- pips_target = clamp(0.55 × 85, 20, 80) = **46.75 pips**
- stop_loss = clamp(0.35 × 85, 15, 60) = **29.75 pips**

---

## Étape 5 : Vérification Gates

### 5.1 Calcul Risk Score

**Risk score :** Basé sur `pred_vol_pips` (66.7) → `(66.7 - 30) / 120 = 0.31`

**⚠️ PROBLÈME :** Risk score (0.31) < RISK_MIN (0.60)

### 5.2 Vérification Gates

**Gates :**
- ✅ Direction : BUY
- ✅ Impact : 85 pips ≥ 40 (IMPACT_MIN)
- ❌ Risk score : 0.31 < 0.60 (RISK_MIN)
- ✅ Core events : ≥1 présent

**Résultat :** ⛔ **NO_TRADE** (risk score trop faible)

---

## Étape 6 : Ajustement (Optionnel)

### 6.1 Ajuster RISK_MIN

**Dans sidebar :**
- Réduire RISK_MIN à 0.30 (pour cette journée spécifique)

**Résultat :** ✅ **TRADE OK**

### 6.2 Ou Accepter NO_TRADE

**Décision conservatrice :** Respecter le gate risk_score.

---

## Étape 7 : Exécution Trade (Si Gates OK)

### 7.1 Plan de Trade

**Si TRADE OK :**
- **Direction :** BUY
- **Entry window :** 14:45 - 15:15
- **Exit :** HYBRID
  - Take profit : +46.75 pips
  - Stop loss : -29.75 pips
  - Time window : 15:00 - 16:00

### 7.2 Exécution

**14:45 :** Entrer dans la fenêtre (prix d'entrée réel)

**Monitoring :**
- Si +46.75 pips atteint → **Sortir (take profit)**
- Si -29.75 pips atteint → **Sortir (stop loss)**
- Si 16:00 atteint → **Sortir (time window)**

### 7.3 Kill Switch

**Conditions d'annulation :**
- Divergence visuelle persistante vs pattern attendu
- Volatilité réelle >> prédiction
- Actuals rendent direction inversée

**Exemple :** Si après 15:00, le prix baisse fortement (contraire à BUY) → **Kill switch immédiat**.

---

## Étape 8 : Résultat

### 8.1 Scénario Gagnant

**Résultat :**
- Entrée : 14:50 @ 1.0850
- Sortie : 15:30 @ +48 pips (take profit atteint)
- **Gain : +48 pips**

### 8.2 Scénario Perdant

**Résultat :**
- Entrée : 14:50 @ 1.0850
- Sortie : 15:10 @ -30 pips (stop loss atteint)
- **Perte : -30 pips**

### 8.3 Scénario Kill Switch

**Résultat :**
- Entrée : 14:50 @ 1.0850
- Kill switch : 15:05 (divergence détectée)
- Sortie : 15:05 @ -15 pips
- **Perte limitée : -15 pips** (vs -30 pips stop loss)

---

## 📊 Résumé Workflow

| Étape | Action | Résultat |
|-------|--------|----------|
| 1 | Ouvrir Calendar | Date sélectionnée |
| 2 | Consulter Day Detail | Events chargés |
| 3 | Saisir Actuals | Actuals en session |
| 4 | Recalcul (moteur réel) | Direction/Pattern/Impact calculés |
| 5 | Vérifier Gates | TRADE OK / NO_TRADE |
| 6 | Ajuster (optionnel) | Paramètres modifiés |
| 7 | Exécuter Trade | Trade ouvert |
| 8 | Monitorer + Kill Switch | Trade fermé |

---

## 🎯 Points Clés

### ✅ Ce qui fonctionne bien

1. **Workflow clair :** Calendar → Day Detail → Actuals → Recalcul → Trade
2. **Gates stricts :** Protection contre trades risqués
3. **Fenêtres conservatrices :** Pas de recherche du pic absolu
4. **Kill switch :** Protection contre divergences

### ⚠️ Points d'attention

1. **Risk score :** Peut être trop strict (ajustable en sidebar)
2. **Actuals manquants :** Si actuals non saisis, direction = NO_TRADE
3. **Pattern detection :** Simplifiée (peut être améliorée)

---

## 🔄 Prochaines Améliorations

1. **Auto-collect actuals :** Via API (plus tard)
2. **Overlay prix réel :** Visualisation live
3. **Journal de trading :** Tracking des décisions
4. **Optimisation règles :** Basée sur feedback terrain

---

**Document créé le :** 2025-12-12  
**Version :** V1

