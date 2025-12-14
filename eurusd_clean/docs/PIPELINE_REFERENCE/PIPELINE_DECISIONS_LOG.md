# Journal des Décisions Techniques

## 2025-01-XX : Solution Pic Absolu

**Problème** : Pattern DOUBLE_WAVE s'arrêtait à Wave 2 alors que mouvement continuait (ex: 2025-06-23, 33 pips supplémentaires).

**Décision** : Utiliser `wave2_peak_pips_absolute` au lieu de `impact_pips`.

**Résultat** :
- MAE réduit de 23.4 à 8.4 pips (64.3%)
- 7 cas sur 15 améliorés
- 0 cas dégradés

**Fichier** : `docs/VALIDATION/SOLUTION_PATTERN_INCOMPLET.md`

---

## 2025-01-XX : Assouplissement Critères Tendance

**Problème** : Critères trop stricts (24h avant, 12h durée) empêchaient détection de tendances valides (ex: 2025-04-24).

**Décision** :
- Réduire `min_hours_before_event` de 24 à 12 heures
- Adapter `min_duration_hours` selon timeframe (6h pour M30/H1, 8h pour M1/M5/M15)

**Résultat** :
- 2 tendances détectées au lieu d'1 pour 2025-06-23
- Amélioration précision amplification

**Fichier** : `docs/VALIDATION/ANALYSE_ERREUR_23_06.md`

---

## 2025-01-XX : Seuil Jaccard à 0.60

**Problème** : Seuil 0.8 trop strict, ne trouvait pas de clusters identiques (ex: 2025-11-26).

**Décision** : Réduire à 0.60 pour permettre variations mineures.

**Résultat** :
- 2 clusters identiques trouvés pour 2025-06-23 (au lieu de 0)
- Meilleur match observé : 0.625

---

## 2025-01-XX : Option C pour Pattern/Formules

**Problème** : Pondération hybride dégradait les bons cas.

**Décision** : Seuils stricts sans pondération :
- Écart < 10 pips : Garder formules
- Écart >= 10 pips : Utiliser pattern directement

**Résultat** :
- Protection des bons cas
- Pas de dégradation observée

---

## 2025-01-XX : Désactivation Corrections DOUBLE_WAVE

**Problème** : Corrections dynamiques dégradées globalement malgré améliorations locales.

**Décision** : Désactiver corrections DOUBLE_WAVE.

**Résultat** :
- Taux acceptable : 63.2% (vs 50.0% avec correction)
- Taux excellent : 55.3% (vs 34.2% avec correction)

**Fichier** : `docs/VALIDATION/DECISION_FINALE_TRADING.md`

---

## 2025-01-XX : Random Forest pour Correction Factor

**Problème** : Facteur de correction fixe (0.758) sous-estimait certains cas.

**Décision** : Utiliser Random Forest pour prédire le facteur de correction.

**Résultat** :
- Amélioration de 17.7% après retraining avec amplifications réelles
- Meilleure adaptation aux différents types de clusters

---

## 2025-01-XX : Timeframe M30 pour Impact

**Problème** : Quelle timeframe utiliser pour prédiction d'impact ?

**Décision** : M30 par défaut (M1 reste pour pattern detection).

**Raison** : Meilleure performance observée pour prédiction d'impact.

---

## 2025-01-XX : Stratégie de Sortie à 80%

**Problème** : Comment déterminer le target de sortie optimal ?

**Décision** : Sortie à 80% du prédit avec limite 1.5x.

**Raison** : Protection contre sur-estimation, stratégie originale validée.

---

## 2025-01-XX : Priorisation Premier Mouvement

**Problème** : Mouvements complexes (ex: 2025-11-26) avec plusieurs vagues difficiles à trader.

**Décision** : Prioriser le premier mouvement significatif pour trading.

**Résultat** : Simplification stratégie, meilleure exécution.

**Fichier** : `docs/VALIDATION/STRATEGIE_PREMIER_MOUVEMENT.md`

---

## 2025-01-XX : Patterns Finnhub Phase 2

**Problème** : Patterns Finnhub comme features Random Forest dégradaient résultats.

**Décision** : Utiliser uniquement pour ajustement d'amplification, pas comme features RF.

**Résultat** : Amélioration modeste mais stable.

---

## 2025-01-XX : Plafond Intelligent

**Problème** : Amplifications trop élevées pour certains cas.

**Décision** : Plafond dynamique basé sur principes logiques (pattern ratio, impact base).

**Résultat** : Réduction des sur-estimations.

**Fichier** : `src/core/smart_cap_amplification.py`

---

## Décisions Abandonnées

### 1. Volume comme Feature
**Raison** : Corrélation très faible (-0.114), pas de discrimination.

### 2. Pondération Hybride Pattern/Formules
**Raison** : Dégradait les bons cas où formules étaient déjà précises.

### 3. Corrections Dynamiques DOUBLE_WAVE
**Raison** : Dégradation globale malgré améliorations locales.

### 4. Random Forest Per Date avec Corrélations
**Raison** : Approche trop complexe, pas d'amélioration significative.

---

## Principes Directeurs

1. **Protection des Bons Cas** : Ne pas dégrader les cas où le système fonctionne bien
2. **Validation Robuste** : Tester systématiquement avant implémentation
3. **Simplicité** : Préférer solutions simples qui fonctionnent
4. **Trading First** : Optimiser pour le trading, pas seulement la précision
5. **Fallbacks** : Toujours avoir des fallbacks pour chaque étape

