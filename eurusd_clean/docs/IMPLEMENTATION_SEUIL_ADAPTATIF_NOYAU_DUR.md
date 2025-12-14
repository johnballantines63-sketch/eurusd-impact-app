# Implémentation Seuil Adaptatif Noyau Dur

## Date
2025-01-XX

## Contexte

Lors de l'analyse des événements CPI pour le cluster du 11 septembre 2025, certains événements importants (importance 1-2) avaient un support historique légèrement inférieur au seuil de 60% :
- **Core Inflation Rate MoM** : Support 46.4%, Importance 1
- **CPI SA** : Support 53.6%, Importance 2
- **Inflation Rate MoM** : Support 51.8%, Importance 1

Ces événements sont économiquement importants et devraient être inclus dans le noyau dur même si leur récurrence historique est légèrement inférieure au seuil standard.

## Solution Implémentée : Option 1 - Seuil Adaptatif

### Logique
Un événement est considéré comme "core" si :
- **Support >= 60%** : Événement core (seuil standard)
- **OU (support >= 40% ET importance <= 2)** : Événement core aussi (seuil adaptatif)

Cette logique permet d'inclure les événements importants même si leur récurrence historique est légèrement inférieure au seuil standard.

### Avantages
1. **Plus flexible** : Prend en compte l'importance du calendrier économique
2. **Plus robuste** : Inclut les événements importants même avec récurrence légèrement inférieure
3. **Logique métier** : Un événement d'importance 1 avec support 46.4% est plus pertinent qu'un événement d'importance 3 avec support 50%

### Impact Attendu
- Meilleure détection des clusters identiques (plus d'événements core = meilleure correspondance)
- Prédictions plus précises pour les clusters CPI complexes

## Tests Comparatifs

### Option 1 vs Option 2

**Option 1** : Seuil adaptatif (support >= 60% OU (support >= 40% ET importance <= 2))
**Option 2** : Seuil ajusté par type (CPI: 50%, NFP: 60%)

### Résultats

#### 11 septembre 2025 (CPI)
- **Option 1** : 6 événements core (inclut "core inflation rate mom" avec support 46.4%)
- **Option 2** : 5 événements core (n'inclut pas "core inflation rate mom")

#### 1er août 2025 (NFP)
- **Option 1** : 9 événements core
- **Option 2** : 9 événements core (identique car seuil 60% pour NFP)

### Conclusion
L'Option 1 a été choisie car elle est plus flexible et prend en compte l'importance économique des événements.

## Implémentation

### Fichier Modifié
`scripts/run_pipeline_complete.py`

### Méthode Modifiée
`etape3_definir_noyau_dur`

### Code Ajouté
```python
# ✅ OPTION 1 : Seuil adaptatif selon importance
# Filtrer événements avec support >= seuil OU (support >= 40% ET importance <= 2)
for event_id, support in support_scores.items():
    # Trouver l'importance de l'événement correspondant
    event_found = None
    for idx, event in cluster_events.iterrows():
        event_key = str(event.get('event_key', '')).lower().strip()
        country = event.get('country', '')
        importance = event.get('importance_n', 3)
        event_id_check = f"{event_key}_{country}_{importance}"
        if event_id_check == event_id:
            event_found = event
            break
    
    if event_found is not None:
        importance = event_found.get('importance_n', 3)
        # Option 1 : support >= 60% OU (support >= 40% ET importance <= 2)
        if support >= support_threshold or (support >= 0.40 and importance <= 2):
            core_events.append(event_id)
    else:
        # Fallback si événement non trouvé : utiliser seuil standard
        if support >= support_threshold:
            core_events.append(event_id)
```

## Validation

### Test sur 11 septembre 2025
```
✅ Noyau dur: 6/12 événements (type: CPI)
  ✅ CORE core inflation rate yoy    | Support:  78.6%
  ✅ CORE cpi                         | Support:  78.6%
  ✅ CORE inflation rate yoy          | Support:  78.6%
  ✅ CORE cpi sa                      | Support:  53.6% (importance 2)
  ✅ CORE inflation rate mom          | Support:  51.8% (importance 1)
  ✅ CORE core inflation rate mom     | Support:  46.4% (importance 1) ← Inclus grâce au seuil adaptatif
```

## Notes

- Le seuil adaptatif s'applique uniquement aux clusters CPI et NFP (pas aux clusters GENERIC)
- Les événements d'importance 3 nécessitent toujours un support >= 60% pour être inclus
- Les événements d'importance 1-2 peuvent être inclus avec un support >= 40%




