# REF-003 : SCRIPT RECALCUL SCORES EMPIRIQUES FINNHUB

**Référence :** REF-003  
**Date de création :** 2025-12-06  
**Heure de création :** 09:50:47  
**Auteur :** André Valentin avec Claude  
**Version :** 1.0

---

## 📋 OBJECTIF

Documenter le script de recalcul des scores empiriques depuis Finnhub, créé pour répondre aux conclusions de REF-002.

---

## 📝 DESCRIPTION DU SCRIPT

**Fichier :** `SESSION_VALIDATION_ACTUELLE/scripts/recalculate_empirical_scores_finnhub.py`

**Fonctionnalités :**
1. Charge les événements depuis `events` (Finnhub)
2. Mesure l'impact réel depuis `prices_finnhub_m1` pour chaque événement
3. Calcule les statistiques (moyenne, médiane, P80, P20)
4. Calcule le score empirique selon la formule validée
5. Met à jour la table `event_families`

---

## 🔧 MÉTHODE DE CALCUL

### 1. Mesure d'Impact

**Baseline :**
- OPEN de la première bougie à ou après l'événement
- Fallback : CLOSE de la dernière bougie avant l'événement

**Pic :**
- HIGH maximum (ou LOW minimum) dans fenêtre 240 minutes après l'événement
- Impact = abs((peak_price - baseline_price) * 10000)

**Paramètres :**
- `LOOKBACK_MINUTES = 5` : Minutes avant événement pour baseline
- `LOOKAHEAD_MINUTES = 240` : Minutes après événement pour pic maximum

### 2. Formule Score Empirique

**Formule validée (Session 123) :**
```python
base_score = (avg_movement * 0.5 + p80_movement * 0.5)
robustness = facteur basé sur sample_size
score = base_score * robustness
normalized = min(100.0, (score / 100.0) * 100.0)
```

**Facteur Robustesse :**
- `sample_size >= 20` : robustness = 1.0
- `sample_size >= 10` : robustness = 0.9
- `sample_size >= 5` : robustness = 0.8
- `sample_size < 5` : robustness = 0.7

### 3. Statistiques Calculées

Pour chaque famille d'événements (event_key, country) :
- `empirical_score` : Score empirique normalisé (0-100)
- `avg_movement_pips` : Mouvement moyen en pips
- `median_movement_pips` : Mouvement médian en pips
- `p80_movement_pips` : Mouvement au 80e percentile
- `p20_movement_pips` : Mouvement au 20e percentile
- `sample_size` : Nombre d'événements mesurés
- `latency_median` : Latence médiane (estimation)
- `latency_p20` : Latence au 20e percentile
- `latency_p80` : Latence au 80e percentile

---

## 🚀 UTILISATION

### Mode Production

```bash
python3 SESSION_VALIDATION_ACTUELLE/scripts/recalculate_empirical_scores_finnhub.py \
    --start-date 2020-01-01 \
    --end-date 2025-12-06 \
    --countries US EU DE GB \
    --min-events 3
```

### Mode Test (Dry Run)

```bash
python3 SESSION_VALIDATION_ACTUELLE/scripts/recalculate_empirical_scores_finnhub.py \
    --start-date 2020-01-01 \
    --end-date 2025-12-06 \
    --countries US \
    --min-events 3 \
    --dry-run
```

### Paramètres

- `--start-date` : Date de début (format 'YYYY-MM-DD', défaut: '2020-01-01')
- `--end-date` : Date de fin (format 'YYYY-MM-DD', défaut: aujourd'hui)
- `--countries` : Liste des pays (défaut: ['US'])
- `--min-events` : Nombre minimum d'événements par famille (défaut: 3)
- `--dry-run` : Mode test (ne modifie pas la DB)
- `--verbose` : Afficher détails

---

## 🔒 SÉCURITÉ

**Backup automatique :**
- Avant toute modification, création de `event_families_backup`
- Permet de restaurer l'ancienne table si nécessaire

**Mode Dry Run :**
- Permet de tester sans modifier la DB
- Affiche les résultats calculés sans les sauvegarder

---

## 📊 VALIDATION

**Critères de validation :**
1. ✅ Utilise `events` (Finnhub) comme source
2. ✅ Utilise `prices_finnhub_m1` pour mesures
3. ✅ Formule validée (Session 123)
4. ✅ Backup automatique avant modification
5. ✅ Mode dry-run pour tests

**Tests recommandés :**
1. Exécuter en mode dry-run sur un échantillon (US, 2024-2025)
2. Comparer résultats avec scores actuels
3. Vérifier cohérence des scores calculés
4. Exécuter en mode production si validation OK

---

## ⚠️ NOTES IMPORTANTES

1. **Temps d'exécution** : Peut être long selon le nombre d'événements
   - Estimation : ~1-2 heures pour 2020-2025, tous pays

2. **Latence** : Actuellement estimée (5.0 par défaut)
   - TODO : Calculer latence réelle depuis les prix

3. **Famille d'événements** : Le champ `family` n'est pas mis à jour
   - À faire manuellement ou via script séparé

4. **Événements sans prix** : Ignorés silencieusement
   - Vérifier logs pour événements non mesurés

---

## 📝 PROCHAINES ÉTAPES

1. **⏳ À FAIRE** : Exécuter en mode dry-run pour validation
2. **⏳ À FAIRE** : Comparer résultats avec scores actuels
3. **⏳ À FAIRE** : Améliorer calcul de latence réelle
4. **⏳ À FAIRE** : Exécuter en mode production si validation OK
5. **⏳ À FAIRE** : Documenter résultats dans REF-004

---

## 🔗 RÉFÉRENCES

- **REF-001** : Définitions et règles pour tests
- **REF-002** : Vérification scores empiriques Finnhub
- **Session 123** : Formule de calcul validée

---

**Fin du document REF-003**

