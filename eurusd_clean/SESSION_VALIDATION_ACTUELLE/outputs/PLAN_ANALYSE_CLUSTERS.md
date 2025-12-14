# 📊 PLAN D'ANALYSE : CLUSTERS D'ÉVÉNEMENTS AUTOUR DES MOUVEMENTS FORTS

**Date** : 2025-12-09  
**Objectif** : Identifier le "noyau dur" d'événements réellement déclencheurs des mouvements forts

---

## 🎯 HYPOTHÈSE CENTRALE

**Les mouvements forts/très forts sont déclenchés par un petit noyau d'événements "rates-relevant"** :
- CPI, NFP, Jobless Claims, FOMC
- PMI/ISM, Retail Sales, GDP flash
- **Pas** les bill auctions ou autres secondaires

**En diluant avec 200 secondaires, on introduit** :
- Bruit
- Annulation de signaux
- Compression vers 0 (observé dans V5)

---

## 📋 MÉTHODOLOGIE

### 1. Détection : Calcul du "Lift" (Sur-représentation)

**Formule** :
```
lift = freq_strong / freq_all

où:
- freq_strong = % des mouvements forts qui ont cet événement
- freq_all = % de toutes les fenêtres (mouvements faibles) qui l'ont
```

**Interprétation** :
- `lift >> 1` → Événement sur-représenté dans mouvements forts
- `lift ≈ 1` → Événement neutre
- `lift << 1` → Événement sous-représenté

**Fenêtre temporelle** :
- Lookback : **-4h** avant le début du mouvement
- Lookahead : **+30min** après le début

### 2. Co-occurrence : Clusters fréquents

**Objectif** : Identifier si certains couples/triples se présentent ensemble

**Métrique** :
```
P(A ∧ B | strong) vs P(A)P(B)

Si P(A ∧ B | strong) >> P(A)P(B) → Co-occurrence significative
```

**Méthode** :
- Calculer fréquences individuelles : `freq_A`, `freq_B`
- Calculer co-occurrence : `freq_AB`
- Comparer à fréquence attendue : `freq_A * freq_B`
- Lift de co-occurrence : `freq_AB / (freq_A * freq_B)`

### 3. Direction : Score restreint au noyau

**Score directionnel restreint** :
```
S_cluster = Σ w_i * surprise_z_i

où i seulement dans {CPI, Jobless, NFP, FOMC, ISM/PMI...}
```

**Normalisation** : `S = S_raw / sqrt(n_active)` (comme F2)

**Classification** :
- `S > 0.05` → UP
- `S < -0.05` → DOWN
- `|S| ≤ 0.05` → UNKNOWN

**Métriques** :
- Accuracy globale
- Accuracy UP / DOWN séparément
- Coverage (% non-UNKNOWN)

---

## 🔧 SCRIPT CRÉÉ

**Fichier** : `SESSION_VALIDATION_ACTUELLE/scripts/analyze_cluster_strong_moves.py`

**Fonctionnalités** :
1. ✅ Charge mouvements forts depuis `all_movements_detected.csv`
2. ✅ Calcule lift pour chaque event_key/famille
3. ✅ Analyse co-occurrence par paires
4. ✅ Teste score directionnel restreint au noyau identifié
5. ✅ Exporte résultats CSV

**Configuration** :
```python
LOOKBACK_HOURS = -4      # 4h avant mouvement
LOOKAHEAD_MINUTES = 30   # 30min après
MIN_STRONG_PIPS = 40.0   # Seuil mouvement fort
MIN_VERY_STRONG_PIPS = 60.0  # Seuil très fort
```

---

## 📊 RÉSULTATS ATTENDUS

### Phase 1 : Identification du noyau

**Top 10 familles par lift** :
- CPI, NFP, Jobless Claims, FOMC, PMI, ISM, Retail Sales, GDP, PPI, PCE

**Top 5 co-occurrences** :
- CPI + Jobless Claims
- NFP + CPI
- FOMC + CPI
- etc.

### Phase 2 : Test directionnel

**Objectif** : Accuracy > 55% sur mouvements forts avec noyau restreint

**Seuil go/no-go** :
- Si cluster ≤5 familles couvre >60% des strong moves
- ET donne direction >55%
- → **Bascule modèle sur ce noyau**

---

## 🚀 UTILISATION

### Étape 1 : Scanner mouvements (si pas déjà fait)

```bash
cd SESSION_VALIDATION_ACTUELLE/scripts
python3 scan_all_movements_independent.py
```

### Étape 2 : Analyser clusters

```bash
python3 analyze_cluster_strong_moves.py
```

### Étape 3 : Examiner résultats

**Fichiers générés** :
- `outputs/cluster_lift_analysis.csv` : Lift par event_key/famille
- `outputs/cluster_cooccurrence_analysis.csv` : Co-occurrences par paires

**Interprétation** :
1. Identifier top 5-10 familles avec `lift > 2.0`
2. Vérifier co-occurrences significatives (`lift > 1.5`)
3. Tester score restreint avec ce noyau
4. Comparer accuracy avec modèle complet (V5)

---

## 📈 MÉTRIQUES DE SUCCÈS

### Succès si :

1. **Lift élevé** : Top 5 familles avec `lift > 2.0`
2. **Co-occurrence** : Au moins 3 paires avec `lift > 1.5`
3. **Accuracy améliorée** : Score restreint > accuracy modèle complet
4. **Coverage acceptable** : > 50% des mouvements forts classifiés

### Échec si :

1. **Lift faible** : Aucune famille avec `lift > 1.5`
2. **Pas de co-occurrence** : Toutes les paires indépendantes
3. **Accuracy dégradée** : Score restreint < accuracy modèle complet
4. **Coverage trop faible** : < 30% des mouvements forts classifiés

---

## 🔄 PROCHAINES ÉTAPES

### Si succès :

1. **Refit modèle** : Entraîner alpha weights seulement sur noyau identifié
2. **Simplifier pipeline** : Retirer secondaires du calcul S
3. **Réévaluer** : Mesurer impact sur corrélation S ↔ direction

### Si échec :

1. **Analyser pourquoi** : Vérifier fenêtre temporelle, seuils, etc.
2. **Ajuster méthodologie** : Peut-être fenêtre différente ou autre approche
3. **Reconsidérer hypothèse** : Peut-être que les secondaires comptent vraiment

---

## 📝 NOTES

- **Fenêtre temporelle** : `[-4h, +30min]` est un choix initial. À ajuster si nécessaire.
- **Seuils mouvement** : `40 pips` pour fort, `60 pips` pour très fort. À valider empiriquement.
- **Normalisation** : Utilise `sqrt(n_active)` comme F2. Cohérent avec V5.

---

## ✅ VALIDATION

**Critères de validation** :
- ✅ Script syntaxiquement correct
- ✅ Charge données mouvements forts
- ✅ Calcule lift et co-occurrence
- ✅ Teste score directionnel restreint
- ⏳ À exécuter pour résultats réels

