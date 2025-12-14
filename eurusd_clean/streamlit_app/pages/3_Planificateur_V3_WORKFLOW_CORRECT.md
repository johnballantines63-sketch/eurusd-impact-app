# Refactorisation Planificateur V3 - Workflow Correct

## Problème Identifié

Le planificateur V3 actuel suit le workflow **INVERSE** :
1. Charger événements
2. Charger prix
3. Détecter pattern (basé sur événements)
4. Prédire

## Workflow Correct (selon stratégie originale)

1. **Charger prix** pour la date
2. **Scanner prix** pour détecter mouvement fort > x pips
3. **Identifier le pattern** (SINGLE_WAVE, DOUBLE_WAVE, etc.) depuis les prix
4. **Calculer l'impact réel** depuis la stabilisation/TTR
5. **Trouver le cluster** d'événements qui a causé ce mouvement

## Solution

Créer deux modes dans le planificateur :

### Mode 1 : Analyse Historique (Workflow Correct)
- Pour dates passées
- Scanner prix → Mouvement → Pattern → Cluster

### Mode 2 : Prédiction Future (Workflow Actuel)
- Pour dates futures
- Charger événements → Prédire impact

## Implémentation

1. Ajouter fonction `scan_price_movements_for_date()` basée sur `scripts/session136/step1_scan_price_movements.py`
2. Ajouter fonction `detect_pattern_from_prices()` basée sur `scripts/session121/scan_price_movements_v3.py`
3. Ajouter fonction `find_cluster_for_movement()` pour trouver événements après détection mouvement
4. Modifier interface pour choisir entre "Analyse Historique" et "Prédiction Future"

