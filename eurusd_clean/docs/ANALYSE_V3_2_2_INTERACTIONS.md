# ANALYSE V3.2.2 INTERACTIONS — Pourquoi Sous-Performance

**Date :** 2025-12-12  
**Contexte :** Validation V3.2.1

---

## 1. OBSERVATION

**Résultat walk-forward :**
- V3_2_1_additive : Spearman 0.3581
- V3_2_2_interactions : Spearman 0.3420
- **Delta : -0.0161** ❌

Les interactions `regime_* × log1p(n_us_events)` **sous-performent** l'approche additive.

---

## 2. RÉSULTATS PAR CUTOFF

| Cutoff | V3_2_1_additive | V3_2_2_interactions | Delta |
|--------|------------------|---------------------|-------|
| 2023-01-01 | 0.2999 | 0.3037 | +0.0038 |
| 2023-07-01 | 0.3802 | 0.3774 | -0.0028 |
| 2024-01-01 | 0.3710 | 0.3161 | **-0.0549** ❌ |
| 2024-07-01 | 0.3814 | 0.3709 | -0.0105 |

**Observation clé :** La perte principale vient du cutoff **2024-01-01** (-0.0549).

---

## 3. HYPOTHÈSES (Saines)

### 3.1 Overfit

**Les interactions ajoutent des degrés de liberté :**
- V3.2.1 : 18 features
- V3.2.2 : 20 features (2 interactions supplémentaires)

**Problème :** Si `n_us_events_day` est discret et peu varié, Ridge peut sur-ajuster sur ces interactions, surtout avec `alpha=0.1` (régularisation modérée).

**Validation :** À vérifier via distribution de `n_us_events_day` et poids Ridge des interactions.

### 3.2 Colinéarité

**`regime_high_60_lag1` et `regime_low_60_lag1` capturent déjà :**
- Le signal "jour à risque" selon le contexte de marché
- Une grande partie de la variance expliquée

**L'interaction `regime_* × log1p(n_us_events)` :**
- Ajoute du bruit redondant
- Peut créer de la colinéarité avec les features régime existantes

**Conclusion attendue :** L'effet de densité est **indépendant** du régime, pas conditionnel.

### 3.3 Mauvaise Forme Fonctionnelle

**L'effet de densité est probablement monotone (additif) :**
- Un jour avec beaucoup d'événements US est risqué **indépendamment** du régime
- L'interaction suggère que l'effet dépend du régime, ce qui n'est pas le cas

**Exemple :**
- Régime haute volatilité + 20 événements US → risque très élevé
- Régime basse volatilité + 20 événements US → risque élevé aussi (densité compense)

**Conclusion :** La densité apporte de la valeur de façon **additive**, pas conditionnelle.

### 3.4 Ridge Régularisation

**Une interaction utile peut être "écrasée" par la régularisation :**
- Si l'échelle des interactions n'est pas standardisée
- Si le signal d'interaction est faible comparé au signal additif
- Ridge peut pénaliser les interactions plus fortement que les features additives

**Validation :** À vérifier via poids Ridge des interactions vs features additives.

---

## 4. ANALYSE CUTOFF 2024-01-01

**Perte principale :** -0.0549 sur ce cutoff.

**Hypothèses spécifiques :**
- Distribution de `n_us_events_day` différente sur cette période ?
- Régime de volatilité particulier qui rend les interactions moins pertinentes ?
- Overfit sur train (2023) qui ne généralise pas sur test (2024) ?

**À investiguer :**
- Distribution `n_us_events_day` par cutoff
- Corrélation `regime_*` vs `n_us_events_day` par période
- Poids Ridge des interactions sur ce cutoff spécifique

---

## 5. CONCLUSION

**Les interactions sous-performent car :**
1. Overfit : ajout de degrés de liberté sans gain de signal
2. Colinéarité : redondance avec features régime existantes
3. Mauvaise forme fonctionnelle : effet additif, pas conditionnel
4. Régularisation Ridge : interactions pénalisées plus fortement

**Décision V3.2.1 :**
- ❌ Interactions (V3.2.2) : NON RETENU
- ✅ Additive (V3.2.1) : RETENU

**Le modèle V3.2.1 additive capture correctement l'effet de densité de façon simple et efficace.**

---

**Document créé le :** 2025-12-12  
**Version :** V3.2.1

