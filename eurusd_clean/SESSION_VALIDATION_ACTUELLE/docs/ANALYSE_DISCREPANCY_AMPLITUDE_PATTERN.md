# Analyse Discrepancy Amplitude Pattern

**Date** : 2025-01-XX  
**Problème** : Amplitudes détectées très faibles par rapport aux valeurs réelles  
**Dates analysées** : 2025-06-23, 2025-05-29

---

## 🔍 PROBLÈMES IDENTIFIÉS

### 2025-06-23

**Détection** :
- Baseline : 12:44 @ 1.14666
- Peak2 détecté : 13:16 @ 1.14729
- Amplitude détectée : **6.30 pips**

**Réel** :
- Baseline M30 : 13:00 @ 1.14646
- Pic réel M30 : 15:30 @ 1.14942
- Amplitude réelle M30 : **29.60 pips**
- Réel mesuré : **76.50 pips**

**Différence** : 23.30 pips (369.8% plus élevé) vs détection

**Causes identifiées** :
1. ⚠️ **Peak2 détecté trop tôt** : 13:16 vs réel 15:30 (134 min avant)
2. ⚠️ **Fenêtre de détection trop courte** : Pic réel (15:30) arrive 45 min après fin fenêtre (14:45)
3. ⚠️ **Baseline différente** : M1=1.14666 vs M30=1.14646 (2.00 pips de différence)
4. ⚠️ **Algorithme stagnation** : Détection s'arrête après 20 bars de stagnation, mais mouvement continue

---

### 2025-05-29

**Détection** :
- Baseline : 17:59 @ 1.13698
- Peak2 détecté : 18:16 @ 1.13801
- Amplitude détectée : **10.30 pips**

**Réel** :
- À mesurer

**Causes probables** (similaires à 2025-06-23) :
1. ⚠️ Fenêtre de détection trop courte (120 min)
2. ⚠️ Algorithme stagnation arrête détection trop tôt

---

## 📊 ANALYSE DÉTAILLÉE

### Problème 1 : Fenêtre de Détection Trop Courte

**Configuration actuelle** :
- `minutes_after_hint = 120` (2 heures après événement)
- Fenêtre : `anchor_time` + 120 min

**Problème** :
- Pour 2025-06-23 : Pic réel à 15:30, fenêtre jusqu'à 14:45 → **45 min trop court**
- Le mouvement réel continue bien au-delà de la fenêtre

**Solution proposée** :
- Augmenter `minutes_after_hint` à 180 ou 240 min (3-4 heures)
- Ou utiliser fenêtre adaptative selon type d'événement

---

### Problème 2 : Algorithme Stagnation Arrête Trop Tôt

**Configuration actuelle** :
- `max_idle_bars = 20` (stagnation 20 bars = pic maximum trouvé)
- Algorithme s'arrête après 20 bars sans nouveau pic

**Problème** :
- Pour 2025-06-23 : Pic détecté à 13:16, mais mouvement continue jusqu'à 15:30
- L'algorithme considère que le pic maximum est atteint trop tôt

**Solution proposée** :
- Augmenter `max_idle_bars` à 30 ou 40 bars
- Ou utiliser fenêtre temporelle minimale (ex: au moins 2 heures après événement)

---

### Problème 3 : Baseline Différente M1 vs M30

**Observation** :
- Baseline M1 : 1.14666 @ 12:44
- Baseline M30 : 1.14646 @ 13:00
- Différence : 2.00 pips

**Cause** :
- M1 utilise `prev_close_14_29` qui cherche baseline à 12:44
- M30 utilise prix à 13:00 (anchor_time réel)

**Impact** :
- Différence de baseline affecte amplitude mesurée
- Mais différence minime (2 pips) vs écart total (23 pips)

---

### Problème 4 : Pic Réel Après Fenêtre

**Observation** :
- Fenêtre détection : jusqu'à 14:45 (anchor_time 12:45 + 120 min)
- Pic réel M30 : 15:30
- **45 min après fin fenêtre**

**Cause** :
- Fenêtre fixe de 120 min ne couvre pas tout le mouvement
- Certains mouvements prennent plus de temps

**Solution proposée** :
- Fenêtre adaptative selon type d'événement
- Ou fenêtre minimale de 180-240 min

---

## 💡 SOLUTIONS PROPOSÉES

### Solution 1 : Augmenter Fenêtre de Détection

**Modification** :
```python
# Dans detect_for_date_duckdb_rev12
minutes_after_hint = 180  # Au lieu de 120 (3 heures)
```

**Avantages** :
- Couvre mouvements plus longs
- Capture pics réels qui arrivent plus tard

**Inconvénients** :
- Plus de données à analyser
- Peut capturer mouvements non liés à l'événement

---

### Solution 2 : Augmenter Seuil Stagnation

**Modification** :
```python
# Dans detect_double_wave_on_df_rev12
max_idle_bars = 40  # Au lieu de 20
```

**Avantages** :
- Continue recherche de pic plus longtemps
- Capture pics qui arrivent après stagnation temporaire

**Inconvénients** :
- Peut capturer pics non liés au mouvement initial

---

### Solution 3 : Fenêtre Adaptative

**Principe** :
- Fenêtre minimale : 120 min
- Fenêtre maximale : 240 min
- Extension si mouvement continue

**Implémentation** :
```python
# Si mouvement continue après 120 min, étendre fenêtre jusqu'à 240 min
if has_ongoing_movement:
    minutes_after_hint = 240
```

---

### Solution 4 : Utiliser Pic Absolu sur Fenêtre Étendue

**Principe** :
- Détecter pattern normalement
- Ensuite, chercher pic absolu sur fenêtre étendue (jusqu'à 4 heures)
- Utiliser pic absolu pour `wave2_peak_pips_absolute`

**Avantages** :
- Conserve détection pattern existante
- Capture pic réel même s'il arrive plus tard

---

## 🎯 RECOMMANDATION

**Solution recommandée** : **Solution 1 + Solution 4**

1. **Augmenter fenêtre de détection** à 180 min (3 heures)
2. **Ajouter recherche pic absolu** sur fenêtre étendue (jusqu'à 4 heures) après détection pattern

**Rationnel** :
- Solution 1 capture la majorité des mouvements
- Solution 4 garantit capture du pic réel même pour mouvements très longs
- Conserve logique de détection existante

---

## ✅ CONCLUSION

**Problème principal** : Fenêtre de détection trop courte (120 min) et algorithme stagnation arrête trop tôt

**Solutions** :
1. ✅ Augmenter `minutes_after_hint` à 180 min
2. ✅ Ajouter recherche pic absolu sur fenêtre étendue
3. ⚠️ Optionnel : Augmenter `max_idle_bars` à 30-40

**Impact attendu** : Amplitudes détectées plus proches des valeurs réelles

---

**Dernière mise à jour** : 2025-01-XX  
**Statut** : ✅ Analyse complète, solutions proposées




