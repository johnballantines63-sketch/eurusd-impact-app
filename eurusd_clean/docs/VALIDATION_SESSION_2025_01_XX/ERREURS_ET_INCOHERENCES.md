# Erreurs et Incohérences Identifiées - Revue Ligne par Ligne

**Date** : 2025-01-XX  
**Fichier analysé** : `scripts/run_pipeline_complete.py`  
**Documentation de référence** : `docs/PIPELINE_REFERENCE/PIPELINE_KNOWLEDGE_BASE.md`

---

## 🔍 Méthodologie de Revue

1. Comparaison ligne par ligne avec la documentation
2. Vérification de la cohérence avec les modules existants
3. Identification des implémentations simplifiées vs complètes
4. Vérification des paramètres et formules

---

## ❌ ERREURS CRITIQUES

### 1. Documentation PIPELINE_KNOWLEDGE_BASE.md - Source Incorrecte

**Ligne 40** : `- **Source** : Table `economic_events` (Finnhub)`

**Réalité** : Le code utilise `load_high_impact_events` qui interroge la table `events` (pas `economic_events`).

**Code réel** (`src/core/event_loader.py` ligne 110) :
```sql
FROM events e
LEFT JOIN event_families ef
```

**Impact** : Documentation trompeuse mais code correct.

**Action** : Corriger la documentation.

---

### 2. Étape 6 : Implémentation Complètement Simplifiée

**Lignes 707-742** : `etape6_calculer_impacts_base_amplifications`

**Problème** : Retourne toujours des valeurs nulles :
```python
impacts_data.append({
    'impact_base': 0.0,
    'impact_reel': 0.0,
    'amplification_parfaite': 1.0
})
```

**Attendu selon documentation** :
- Calculer `impact_base` avec `calculate_impact_d` pour chaque cluster historique
- Mesurer `impact_reel` avec `measure_impact_from_dukascopy` (M1)
- Calculer `amplification_parfaite = impact_reel / impact_base`

**Impact** : L'Étape 6 ne fonctionne pas du tout. Les amplifications parfaites ne sont jamais calculées.

**Action** : Implémenter complètement l'Étape 6.

---

### 3. Étape 8.1 : Calcul Impact Base Incomplet

**Lignes 827-840** : Calcul de l'impact de base

**Problème** : Utilise seulement `avg_score` et `num_events` :
```python
impact_base = calculate_impact_d(
    empirical_score=avg_score,
    num_events=num_events,
    amplification=1.0,
    correction_factor=0.758
)
```

**Attendu** : `calculate_impact_d` nécessite probablement :
- Les événements individuels avec leurs scores empiriques
- Les facteurs de surprise (actual vs forecast)
- Les facteurs d'importance
- La correction RF

**Impact** : Le calcul d'impact de base est incorrect.

**Action** : Vérifier la signature de `calculate_impact_d` et corriger.

---

### 4. Étape 8.2 : Détection Tendance Simplifiée

**Lignes 842-844** : Détection de tendance

**Problème** : Toujours `False` :
```python
trend_exists = False
trend_r2 = 0.0
```

**Attendu** : Utiliser `detect_trend_by_inversion_s107` ou `detect_trend_pre_event_robust` avec les paramètres assouplis.

**Impact** : Aucune tendance n'est jamais détectée pour le cluster cible.

**Action** : Implémenter la détection de tendance réelle.

---

### 5. Étape 8.3 : Prédiction Amplification Simplifiée

**Lignes 846-853** : Prédiction d'amplification

**Problème** : Utilise seulement la moyenne simple :
```python
amplification_predite = results_df['amplification_parfaite'].mean()
```

**Attendu selon documentation** :
1. Random Forest par date (si >= 5 clusters identiques)
2. Random Forest global (fallback)
3. Modèle linéaire (fallback)
4. Moyenne historique (dernier fallback)

**Impact** : La prédiction d'amplification n'utilise pas le Random Forest validé.

**Action** : Implémenter la hiérarchie complète (RF par date → RF global → linéaire → moyenne).

---

### 6. Étape 8.4-8.5 : Ajustements Simplifiés

**Ligne 856** : Ajustements support/résistance et Finnhub

**Problème** : Toujours `1.0` :
```python
adjustment_factor = 1.0
```

**Attendu** :
- 8.4 : Ajustements support/résistance selon breakout et distance normalisée
- 8.5 : Ajustements patterns Finnhub selon patterns trouvés

**Impact** : Aucun ajustement n'est appliqué.

**Action** : Implémenter les ajustements complets.

---

### 7. Étape 8.6 : Détection Pattern Simplifiée

**Lignes 858-865** : Détection de pattern de prix

**Problème** : Toujours `NONE` :
```python
pattern_type = 'NONE'
pattern_info = {
    'pattern_type': pattern_type,
    'direction': 'UNKNOWN',
    'confidence': 0.0
}
```

**Attendu** : Utiliser `detect_double_wave_pattern` de `scripts/phase_a_robust_validation.py`.

**Impact** : Aucun pattern n'est jamais détecté.

**Action** : Implémenter la détection de pattern réelle.

---

### 8. Étape 8.7 : Stratégie Hybride Incomplète

**Lignes 867-878** : Stratégie hybride pattern/formules

**Problème** : `pattern_impact` est toujours `0.0` :
```python
pattern_impact = 0.0  # Sera rempli si pattern détecté
```

**Attendu** : Utiliser `wave2_peak_pips_absolute` du pattern détecté.

**Impact** : La stratégie hybride ne peut jamais utiliser le pattern.

**Action** : Remplir `pattern_impact` avec le pic absolu du pattern.

---

### 9. Étape 8.8 : Formule Exit Target Incorrecte

**Ligne 881** : Calcul du target de sortie

**Problème** : Formule incorrecte :
```python
exit_target = min(prediction_finale * 0.80, prediction_finale * 1.5)
```

**Attendu selon documentation** :
```python
exit_target = min(impact_predicted * 0.80, impact_predicted * 1.5)
```

**Note** : La formule semble correcte mathématiquement, mais vérifier si c'est bien ce qui est attendu.

**Impact** : Potentiellement incorrect si la documentation est précise.

**Action** : Vérifier avec la documentation et corriger si nécessaire.

---

## ⚠️ INCOHÉRENCES ET PROBLÈMES MOYENS

### 10. Étape 1 : Commentaire vs Documentation

**Ligne 112** : Commentaire dit "Table `events` (pas `economic_events`)"

**Documentation** : Dit "Table `economic_events` (Finnhub)"

**Impact** : Confusion mais code correct.

**Action** : Aligner documentation et commentaires.

---

### 11. Étape 5 : Paramètres de Détection

**Lignes 631-653** : Paramètres pour `detect_trend_by_inversion_s107`

**Vérification nécessaire** :
- `segment_hours=20` pour H1 : Correct selon validation
- `min_hours_before_event=24` : Documentation dit 12h (assoupli)
- `lookback_days=14` : Correct
- `min_r2=0.15` : Correct
- `min_amplitude_pips=15.0` : Correct

**Problème potentiel** : `min_hours_before_event=24` alors que documentation dit 12h.

**Impact** : Critères plus stricts que prévu.

**Action** : Vérifier si 24h ou 12h est correct selon validation.

---

### 12. Étape 4 : Recherche Uniquement sur US

**Ligne 425** : `country='US'` hardcodé

**Problème** : Ne recherche que sur US, pas sur EU/DE.

**Impact** : Peut manquer des clusters identiques pour événements EU/DE.

**Action** : Étendre la recherche à tous les pays du cluster cible.

---

## ✅ CORRECTIONS VALIDÉES (Déjà Présentes)

### Normalisation Event Keys
- ✅ Fonction `normalize_event_key` présente (ligne 270)
- ✅ Utilisée pour création identifiants canoniques (ligne 282)

### Colonne Country
- ✅ `e.country` ajouté dans `load_high_impact_events` (vérifié dans event_loader.py)

### Seuil Jaccard Adaptatif
- ✅ Seuils adaptatifs [0.60, 0.55, 0.50] présents (ligne 409)
- ✅ Logique de sélection selon `min_clusters_found` (ligne 497)

### Paramètres Étape 5
- ✅ `segment_hours=20` pour H1 (ligne 638)
- ✅ `prices_finnhub_h1` utilisé (ligne 588)
- ✅ Fenêtre étendue à 6 jours après événement (ligne 598)

---

## 📊 RÉSUMÉ DES PROBLÈMES

| Problème | Gravité | Étape | Lignes | Statut |
|----------|---------|-------|--------|--------|
| Étape 6 simplifiée | 🔴 Critique | 6 | 707-742 | ❌ À implémenter |
| Étape 8.1 incomplet | 🔴 Critique | 8.1 | 827-840 | ❌ À corriger |
| Étape 8.2 simplifiée | 🔴 Critique | 8.2 | 842-844 | ❌ À implémenter |
| Étape 8.3 simplifiée | 🔴 Critique | 8.3 | 846-853 | ❌ À implémenter |
| Étape 8.4-8.5 simplifiée | 🔴 Critique | 8.4-8.5 | 856 | ❌ À implémenter |
| Étape 8.6 simplifiée | 🔴 Critique | 8.6 | 858-865 | ❌ À implémenter |
| Étape 8.7 incomplète | 🔴 Critique | 8.7 | 867-878 | ❌ À corriger |
| Étape 8.8 formule | 🟡 Moyen | 8.8 | 881 | ⚠️ À vérifier |
| Documentation source | 🟡 Moyen | Doc | 40 | ⚠️ À corriger |
| Paramètre 24h vs 12h | 🟡 Moyen | 5 | 639 | ⚠️ À vérifier |
| Recherche uniquement US | 🟡 Moyen | 4 | 425 | ⚠️ À améliorer |

---

## 🎯 PRIORITÉS DE CORRECTION

### Priorité 1 (Critique) :
1. **Étape 6** : Implémenter calcul impacts base & amplifications
2. **Étape 8.2** : Implémenter détection tendance réelle
3. **Étape 8.6** : Implémenter détection pattern réelle
4. **Étape 8.7** : Utiliser pic absolu du pattern

### Priorité 2 (Important) :
5. **Étape 8.1** : Corriger calcul impact base avec tous les paramètres
6. **Étape 8.3** : Implémenter hiérarchie RF (par date → global → linéaire)
7. **Étape 8.4-8.5** : Implémenter ajustements support/résistance et Finnhub

### Priorité 3 (Amélioration) :
8. **Étape 8.8** : Vérifier formule exit target
9. **Étape 4** : Étendre recherche à tous les pays
10. **Étape 5** : Vérifier paramètre 24h vs 12h
11. **Documentation** : Corriger source (events vs economic_events)

---

## 📝 NOTES

- Les étapes 1-5 sont globalement correctes et validées
- Les étapes 6-8 sont largement simplifiées et nécessitent une implémentation complète
- La documentation doit être alignée avec le code réel
- Certains modules référencés (RF, exit_strategy, phase_a_robust_validation) doivent être vérifiés pour existence et compatibilité

---

**Statut** : ✅ Revue complète terminée  
**Prochaines étapes** : Implémenter les corrections par ordre de priorité




