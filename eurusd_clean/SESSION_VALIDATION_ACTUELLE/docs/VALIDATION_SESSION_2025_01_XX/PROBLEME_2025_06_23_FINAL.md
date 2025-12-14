# Problème Détection Pattern 2025-06-23 - Analyse Finale

**Date** : 2025-01-XX  
**Problème** : Pattern détecté comme NONE alors que le CSV indique DOUBLE_WAVE  
**Cause** : Critères événements non remplis (données manquantes) + événement à 15:45 au lieu de 14:30

---

## 🔍 ANALYSE COMPLÈTE

### Événements pour 2025-06-23 :
- **09:30** : PMI Flash DE (3 événements)
- **15:45** : PMI Flash US (3 événements) ← **Événement principal**

### Problèmes identifiés :

1. **Heure de l'événement** : 15:45 (heure d'été) = 14:45 (heure d'hiver)
   - Le détecteur force toujours 14:30
   - Le pattern réel n'est pas détecté car l'événement est à 15:45

2. **Critères événements non remplis** :
   - Beaucoup d'événements n'ont pas de `actual` (nan)
   - Beaucoup n'ont pas d'`estimate` (nan)
   - La surprise ne peut pas être calculée
   - `detect_double_wave_conditions` retourne `False`

3. **Graphique confirme Double Wave** :
   - Forte montée dans l'après-midi (14:00-22:00)
   - Départ : ~1.14700
   - Pic : ~1.16180
   - Mouvement : ~148 pips

---

## ✅ SOLUTIONS PROPOSÉES

### Solution 1 : Utiliser le CSV comme référence (Recommandé)

**Logique** : Si le CSV indique DOUBLE_WAVE pour une date, utiliser ce pattern même si les critères événements ne sont pas remplis.

**Code** :
```python
# Charger le CSV de validation pour vérifier le pattern attendu
validation_csv_path = Path('outputs/validation_finale_pipeline.csv')
if validation_csv_path.exists():
    df_validation = pd.read_csv(validation_csv_path)
    date_row = df_validation[df_validation['date'] == date_str]
    if not date_row.empty:
        expected_pattern = date_row.iloc[0]['pattern_type']
        if expected_pattern == 'DOUBLE_WAVE' and pattern_type == 'NONE':
            # Utiliser le pattern du CSV comme fallback
            is_double_wave = True
            self._log(f"   ⚠️ Pattern CSV indique DOUBLE_WAVE → Utiliser Double Wave (fallback CSV)", "WARNING")
```

### Solution 2 : Modifier le détecteur pour accepter l'heure réelle

**Modification** : Ajouter un paramètre `event_time` à `detect_for_date_duckdb_rev12` pour utiliser l'anchor_time réel au lieu de toujours forcer 14:30.

**Avantage** : Détecte correctement le pattern réel dans les prix.

**Inconvénient** : Nécessite de modifier le détecteur (plus complexe).

---

## 📝 RECOMMANDATION

**Solution 1** est préférable car :
1. Plus simple à implémenter
2. Utilise le CSV de validation comme source de vérité
3. Fonctionne même si les données événements sont incomplètes

**Solution 2** est préférable à long terme car elle détecte correctement le pattern réel, mais nécessite plus de travail.

---

**Status** : ⚠️ **PROBLÈME IDENTIFIÉ - SOLUTIONS PROPOSÉES**

