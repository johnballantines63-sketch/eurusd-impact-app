# Corrections Patterns et Seuils Adaptatifs

**Date** : 2025-01-XX  
**Problèmes** : Patterns détectés comme NONE, événements non trouvés pour certaines dates  
**Solutions** : Seuil adaptatif + Priorité pattern réel

---

## 🔍 PROBLÈMES IDENTIFIÉS

### 1. Événements non trouvés (2025-11-26, 2025-06-23)
- **Cause** : Seuil 40.0 trop élevé (score max disponible < 40.0)
- **Impact** : Aucun événement chargé → Pipeline échoue

### 2. Patterns détectés comme NONE (2025-11-26, 2025-10-10, 2025-06-23)
- **Cause** : Pattern réel détecté (DOUBLE_WAVE) mais critères événements non remplis → pattern_type reste NONE
- **Impact** : Patterns incorrects → Prédictions incorrectes

---

## ✅ SOLUTIONS IMPLÉMENTÉES

### 1. Seuil Adaptatif pour Étape 1

**Localisation** : `scripts/run_pipeline_complete.py`, `etape1_charger_evenements`

**Logique** :
1. Essayer d'abord avec seuil standard (40.0 pour US/EU, 20.0 pour DE)
2. Si aucun événement trouvé, chercher le score max disponible pour ce pays/date
3. Utiliser un seuil adaptatif : `max(20.0, max_score - 5.0)`
4. Réessayer avec ce seuil adaptatif

**Code** :
```python
# Si aucun événement trouvé avec seuil initial
if events.empty:
    # Chercher score max disponible
    query_max_score = f"""
    SELECT MAX(ef.empirical_score) as max_score
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE DATE(e.ts_utc) = DATE '{date_str}'
        AND e.country = '{country}'
        AND ef.empirical_score IS NOT NULL
    """
    max_score_result = conn.execute(query_max_score).df()
    max_score = max_score_result['max_score'].iloc[0] if not max_score_result.empty else None
    
    if max_score is not None and max_score > 0:
        # Seuil adaptatif : max_score - 5 (minimum 20.0)
        min_score_adaptive = max(20.0, max_score - 5.0)
        if min_score_adaptive < min_score_initial:
            events = load_high_impact_events(
                self.db_path,
                target_date,
                country=country,
                min_empirical_score=min_score_adaptive,
                verbose=False
            )
```

**Résultats** :
- 2025-11-26 : Score max 37.4 → Seuil adaptatif 32.4 → Événements trouvés ✅
- 2025-06-23 : Score max 35.9 → Seuil adaptatif 30.9 → Événements trouvés ✅

---

### 2. Priorité Pattern Réel sur Critères Événements

**Localisation** : `scripts/run_pipeline_complete.py`, `etape8_appliquer_cluster_cible`

**Logique** :
1. **PRIORITÉ 1** : Si pattern réel détecté dans prix = DOUBLE_WAVE → Utiliser DOUBLE_WAVE (même si critères événements non remplis)
2. **PRIORITÉ 2** : Si critères événements remplis → Vérifier pattern réel
3. **PRIORITÉ 3** : Sinon → Vérifier Single Wave Strong

**Code** :
```python
# ⚠️ LOGIQUE PRIORITAIRE : Pattern réel détecté dans les prix prime sur critères événements
if pattern_real_result and pattern_real_result.get('double_wave', False):
    # Pattern réel = Double Wave → Utiliser Double Wave (priorité absolue)
    is_double_wave = True
    is_single_wave_strong = False
    if is_double_wave_events:
        self._log(f"   ✅ Double Wave confirmé : pattern réel + critères événements", "SUCCESS")
    else:
        self._log(f"   ✅ Double Wave détecté dans prix (critères événements non remplis mais pattern réel confirmé)", "SUCCESS")
elif is_double_wave_events:
    # Critères Double Wave remplis → Vérifier pattern réel
    # ...
```

**Résultats** :
- 2025-11-26 : Pattern réel DOUBLE_WAVE → Pattern détecté ✅ (au lieu de NONE)
- 2025-10-10 : Pattern réel DOUBLE_WAVE → Pattern détecté ✅ (au lieu de NONE)
- 2025-06-23 : Pattern réel DOUBLE_WAVE → Pattern détecté ✅ (au lieu de NONE)

---

## 📊 RÉSULTATS

**Avant corrections** :
- 2025-11-26 : ❌ Aucun événement trouvé
- 2025-10-10 : ❌ Pattern NONE
- 2025-06-23 : ❌ Pattern NONE

**Après corrections** :
- 2025-11-26 : ✅ Événements trouvés (seuil adaptatif 32.4), Pattern DOUBLE_WAVE
- 2025-10-10 : ✅ Pattern DOUBLE_WAVE détecté
- 2025-06-23 : ✅ Événements trouvés (seuil adaptatif 30.9), Pattern DOUBLE_WAVE

---

## 📝 NOTES IMPORTANTES

1. **Seuil adaptatif** : Permet de charger des événements même si le score max est inférieur au seuil standard (40.0). Le seuil adaptatif est calculé comme `max(20.0, max_score - 5.0)` pour garantir au moins quelques événements.

2. **Priorité pattern réel** : Le pattern réel détecté dans les prix (via `detect_for_date_duckdb_rev12`) prime sur les critères événements. Cela garantit que si un pattern DOUBLE_WAVE est détecté dans les prix, il est utilisé même si les critères événements (surprise, cluster size, importance) ne sont pas remplis.

3. **Compatibilité** : Ces corrections sont compatibles avec la logique existante pour 2025-08-01 (Single Wave malgré critères Double Wave remplis) et 2025-09-11 (Double Wave avec clusters multiples).

---

**Status** : ✅ **CORRIGÉ ET VALIDÉ**




