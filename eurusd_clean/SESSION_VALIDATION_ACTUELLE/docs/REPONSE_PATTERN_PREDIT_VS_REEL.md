# Réponse : Pattern Prédit vs Pattern Réel

**Date** : 2025-01-XX  
**Question** : Le pattern utilisé est-il prédit ou comment est-il déterminé ?

---

## 📊 RÉPONSE DIRECTE

**Le pipeline utilise DEUX types de patterns** :

1. **Pattern Réel** : Détecté depuis les prix historiques (après l'événement)
2. **Pattern Prédit** : Calculé avec des formules et ratios (avant l'événement)

**Problème actuel** : Le pipeline utilise le **pattern prédit** (timeline) au lieu du **pattern réel** pour les cas problématiques.

---

## 🔍 DÉTAILS TECHNIQUES

### 1. Pattern Réel (Détection depuis Prix)

**Fonction** : `detect_for_date_duckdb_rev12()` (ligne 1895)

**Source** : Prix historiques M1 depuis `prices_finnhub_m1`

**Méthode** :
- Charge les prix M1 autour de l'événement (fenêtre ±2h)
- Détecte les pics et creux réels dans les prix
- Mesure les amplitudes réelles observées
- Retourne un pattern avec **valeurs réelles mesurées**

**Exemple retour** :
```python
{
    'double_wave': True,
    'wave1_amp_pips': 45.2,  # Réel mesuré depuis prix
    'wave2_amp_pips': 62.1,  # Réel mesuré depuis prix
    'confidence': 95.0,
    'baseline_price': 1.16823
}
```

**Quand disponible** : Après l'événement (données historiques)

---

### 2. Pattern Prédit (Timeline Session 64)

**Fonction** : `predict_double_wave_timeline_s64()` (ligne 2227)

**Source** : Formules et calculs basés sur événements

**Méthode** :
- Calcule `base_impact_for_timeline = impact_base * amplification`
- Applique des ratios fixes :
  - `PHASE1_RATIO = 0.80` (80% de base_impact)
  - `PULLBACK_RATIO = 0.50` (50% de phase1)
  - `PHASE2_RATIO = 0.90` (90% de base_impact)
- Utilise des timings fixes (T+5, T+11, T+15, T+40)
- Retourne un timeline avec **valeurs prédites**

**Exemple retour** :
```python
{
    'phase1': {'impact_pips': 326.79},  # Prédit = 408.49 * 0.80
    'phase2': {'impact_pips': 367.64},  # Prédit = 408.49 * 0.90
    'total_net_pips': 408.49
}
```

**Quand disponible** : Avant l'événement (prédiction)

---

## ⚠️ PROBLÈME IDENTIFIÉ

### Logique Actuelle (ligne 2268-2328)

```python
# 1. Initialisation depuis timeline prédit
wave2_peak_pips_absolute = timeline.get('phase2', {}).get('impact_pips', 0.0)
# Pour 2025-05-29 : = 367.64 pips (timeline prédit)

# 2. Remplacement par pattern réel si disponible
if pattern_real_result and pattern_real_result.get('double_wave', False):
    wave2_real = pattern_real_result.get('wave2_amp_pips', 0.0)
    if wave2_real > 0:
        wave2_peak_pips_absolute = wave2_real
    # Sinon, reste 367.64 (timeline prédit)
```

**Problème pour 2025-05-29** :
- `pattern_real_result` existe et `double_wave = True`
- Mais `wave2_amp_pips = 0.0` ou non disponible
- Donc `wave2_peak_pips_absolute` reste **367.64** (timeline prédit)
- **Mais ensuite, cette valeur devient 15.00 pips quelque part !**

**Hypothèse** :
- Il y a peut-être un autre endroit où `wave2_peak_pips_absolute` est modifié
- Ou le pattern réel n'est pas correctement détecté pour ces dates
- Ou `wave2_amp_pips` du pattern réel est 0.0 car le pattern n'est pas valide

---

## 🔍 VÉRIFICATION NÉCESSAIRE

Pour comprendre pourquoi `wave2_peak_pips_absolute = 15.00` au lieu de 367.64 ou du pattern réel :

1. **Vérifier si le pattern réel est détecté** :
   - Appeler `detect_for_date_duckdb_rev12()` directement
   - Vérifier si `wave2_amp_pips > 0`

2. **Vérifier s'il y a d'autres modifications** :
   - Chercher tous les endroits où `wave2_peak_pips_absolute` est modifié
   - Vérifier s'il y a des conditions qui réduisent cette valeur

3. **Vérifier la logique de recherche du pic absolu étendu** :
   - Lignes 2284-2328 : Recherche pic absolu sur fenêtre ±2h
   - Peut-être que cette recherche trouve 15.00 pips au lieu de 74.40 pips

---

## ✅ CONCLUSION

**Réponse à la question** :

Le pattern utilisé est **DÉTERMINÉ** de deux manières :

1. **Pattern Réel** : Détecté depuis les prix historiques (méthode préférée)
2. **Pattern Prédit** : Calculé avec formules (fallback si pattern réel non disponible)

**Problème actuel** :
- Pour 2025-05-29 et 2025-06-23, le pattern réel est détecté mais `wave2_amp_pips = 0.0`
- Donc le pipeline utilise le timeline prédit (15.00/15.50) au lieu du pattern réel (74.40/88.60)
- Il faut investiguer pourquoi `wave2_amp_pips = 0.0` malgré pattern détecté

---

**Dernière mise à jour** : 2025-01-XX  
**Statut** : ✅ Explication complète, investigation en cours




