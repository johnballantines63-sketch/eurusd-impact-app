# Fonctions Validées Trouvées pour Étapes 8.4-8.8

**Date** : 2025-01-XX  
**Objectif** : Documenter les fonctions validées trouvées pour compléter le pipeline

---

## ✅ FONCTIONS TROUVÉES

### Étape 8.4-8.5 : Ajustements Support/Résistance et Finnhub

#### 8.4 : Support/Résistance
**Documentation** : `docs/PIPELINE_REFERENCE/PIPELINE_REFERENCE_COMPLETE.md` (lignes 235-246)

**Logique documentée** :
- Détection de breakout (direction cluster ≠ direction tendance)
- Distance normalisée à la barrière directionnelle (en ATR)
- Ajustements selon proximité et type de breakout

**Ajustements** :
- Breakout + très proche (< 0.15 ATR) : +15%
- Breakout + proche (< 0.40 ATR) : +5%
- Pas de breakout + très proche (< 0.10 ATR) : -30%
- Pas de breakout + proche (< 0.20 ATR) : -10%
- Beaucoup de marge (> 1.40 ATR) : +15%

**Status** : ⚠️ Fonction spécifique non trouvée, mais logique documentée

#### 8.5 : Patterns Finnhub
**Fichier trouvé** : `src/core/finnhub_patterns.py` ✅

**Fonction principale** : `load_finnhub_patterns()`
- Charge les patterns Finnhub pour une date donnée
- Fenêtre de recherche : 24h par défaut
- Retourne DataFrame avec patterns

**Documentation** : `docs/PIPELINE_REFERENCE/PIPELINE_REFERENCE_COMPLETE.md` (lignes 248-259)

**Multiplicateurs documentés** :
- Patterns forts validant direction : +5% à +10%
- Patterns forts invalidant direction : -10% à -15%
- Pas de patterns : -5% (réduction de confiance)

**Status** : ✅ Fonction de chargement trouvée, logique d'ajustement documentée

---

### Étape 8.6 : Détection Pattern de Prix

**Documentation** : `docs/PIPELINE_REFERENCE/PIPELINE_REFERENCE_COMPLETE.md` (lignes 261-287)

**Fichiers trouvés** :
- ✅ `scripts/session120/double_wave_detector_rev12.py` - `detect_double_wave_on_df_rev12()`
- ✅ `src/core/doublewave_prediction.py` - `predict_doublewave_overlap()`
- ✅ `src/core/double_wave.py` - `detect_double_wave_conditions()`

**Fonction principale** : `detect_double_wave_on_df_rev12()` dans `scripts/session120/double_wave_detector_rev12.py`

**Paramètres documentés** :
- `MIN_PHASE1_PIPS` : 20.0 pips
- `MIN_PHASE2_PIPS` : 14.0 pips
- `MIN_PULLBACK_RATIO` : 0.20 (20%)
- `MAX_PULLBACK_RATIO` : 0.80 (80%)
- `PHASE1_WINDOW_MINUTES` : 90 minutes
- `PULLBACK_WINDOW_MINUTES` : 45 minutes
- `PHASE2_WINDOW_MINUTES` : 180 minutes

**⚠️ CRITIQUE : Pic Absolu**
- Documentation mentionne `wave2_peak_pips_absolute` : Pic réel dans toute la fenêtre (capture Wave 3)
- Utilisé au lieu de `impact_pips` (basé sur Wave 2 détecté uniquement)

**Status** : ✅ Fonction de détection trouvée, mais vérifier calcul du pic absolu

---

### Étape 8.7 : Stratégie Hybride Pattern/Formules

**Documentation** : `docs/PIPELINE_REFERENCE/PIPELINE_REFERENCE_COMPLETE.md` (lignes 288-300)

**Option C (révisée)** :

**Condition 1** : Écart < 10 pips
- → Garder formules (ignorer pattern)
- **Raison** : Protection des bons cas

**Condition 2** : Écart >= 10 pips
- → Utiliser pattern directement (100%)
- **Raison** : Pattern plus fiable pour écarts importants

**Pas de pondération hybride** : Dégradait les bons cas

**Status** : ✅ Logique documentée clairement

---

### Étape 8.8 : Calcul Target de Sortie

**Documentation** : `docs/PIPELINE_REFERENCE/PIPELINE_REFERENCE_COMPLETE.md` (lignes 301-312)

**Stratégie documentée** :
- Sortie à 80% de l'impact prédit
- Limite maximale : 1.5x du prédit
- Pas de compensation (stratégie originale)

**Calcul** :
```python
exit_target = min(impact_predicted * 0.80, impact_predicted * 1.5)
```

**Note** : Cette formule semble incorrecte (min de 0.80x et 1.5x donnera toujours 0.80x). Probablement :
```python
exit_target = min(impact_predicted * 0.80, impact_predicted * 1.5)
# Devrait être :
exit_target = min(impact_predicted * 0.80, impact_predicted * 1.5)
# Mais cela donne toujours 0.80x...
# Probablement :
exit_target = max(impact_predicted * 0.80, min(impact_predicted * 1.5, ...))
```

**Status** : ⚠️ Formule à vérifier/clarifier

---

## 📋 RÉSUMÉ

| Étape | Fonction Trouvée | Status | Action |
|-------|------------------|--------|--------|
| 8.4 | Logique documentée | ⚠️ | Implémenter selon documentation |
| 8.5 | `load_finnhub_patterns()` | ✅ | Utiliser fonction existante |
| 8.6 | `detect_double_wave_on_df_rev12()` | ✅ | Utiliser fonction existante, vérifier pic absolu |
| 8.7 | Logique documentée | ✅ | Implémenter selon documentation |
| 8.8 | Formule documentée | ⚠️ | Vérifier/clarifier formule |

---

## 🎯 PROCHAINES ACTIONS

1. **Étape 8.4** : Implémenter logique support/résistance selon documentation
2. **Étape 8.5** : Utiliser `load_finnhub_patterns()` et appliquer multiplicateurs
3. **Étape 8.6** : Utiliser `detect_double_wave_on_df_rev12()` et vérifier calcul pic absolu
4. **Étape 8.7** : Implémenter Option C selon documentation
5. **Étape 8.8** : Clarifier formule exit target et implémenter

---

**Approche** : Utiliser les fonctions validées trouvées et implémenter selon la documentation !

