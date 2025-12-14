# Validation Étape 3 : Définir Noyau Dur - Analyse Complète

**Date** : 2025-01-XX  
**Référence** : `docs/PIPELINE_REFERENCE/PIPELINE_KNOWLEDGE_BASE.md` ligne 49-53

---

## ⚠️ État Actuel : INCOMPLET

**Problème** : L'implémentation actuelle ne fait pas vraiment l'analyse historique. Elle met tous les événements à support 1.0 par défaut.

---

## 📋 Solution Proposée

### Option A : Utiliser Patterns de Familles (Solution Rapide)

Utiliser les patterns de familles existants (`src/core/event_families.py`) pour identifier les noyaux durs CPI et NFP :

```python
# Détecter si cluster correspond à CPI ou NFP
if cluster contient événements CPI (pattern regex):
    core_events = événements CPI du cluster
    support_scores = 1.0 pour tous (noyau dur pré-défini)
elif cluster contient événements NFP (pattern regex):
    core_events = événements NFP du cluster
    support_scores = 1.0 pour tous (noyau dur pré-défini)
else:
    # Fallback : tous les événements sont core (comportement actuel)
    core_events = tous les événements
    support_scores = 1.0 pour tous
```

**Avantages** :
- Rapide à implémenter
- Utilise les patterns existants
- Couvre les cas CPI et NFP (les plus fréquents)

**Inconvénients** :
- Ne fait pas vraiment l'analyse historique
- Ne calcule pas les vrais scores de support

### Option B : Analyse Historique Complète (Solution Complète)

Implémenter l'analyse historique complète sur 5 ans :

1. Pour chaque date dans l'historique (5 ans)
2. Charger événements HIGH impact
3. Détecter clusters (fenêtre 30 min)
4. Pour chaque événement du cluster cible :
   - Compter occurrences avec les autres événements du cluster
   - Calculer support = occurrences_ensemble / occurrences_totales
5. Filtrer par seuil >= 0.8

**Avantages** :
- Conforme à la documentation
- Calculs de support réels

**Inconvénients** :
- Beaucoup de requêtes DB (lent)
- Complexe à implémenter

---

## 🎯 Recommandation

**Pour l'instant** : Option A (patterns de familles)  
**Plus tard** : Option B (analyse historique complète) si nécessaire

**Raison** : Les cas CPI et NFP sont les plus fréquents et les plus importants. Une solution simplifiée qui les couvre est suffisante pour commencer.

---

**Statut** : ⚠️ À IMPLÉMENTER (Option A recommandée)  
**Action** : Implémenter détection CPI/NFP avec patterns de familles




