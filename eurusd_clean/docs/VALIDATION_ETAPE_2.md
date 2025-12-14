# Validation Étape 2 : Détecter Clusters

**Date** : 2025-01-XX  
**Référence** : `docs/PIPELINE_REFERENCE/PIPELINE_KNOWLEDGE_BASE.md` ligne 44-47

---

## 📋 Spécifications selon Documentation

- **Méthode** : Fenêtre glissante de 30 minutes
- **Groupement** : Par heure d'ancrage
- **Sortie** : Liste de clusters avec anchor_time

---

## ✅ Validation du Code Actuel

**Fichier** : `scripts/run_pipeline_complete.py` ligne 160-225

### Vérifications

1. ✅ **Fenêtre glissante de 30 minutes** : `window_minutes: int = 30` (paramètre par défaut)
2. ✅ **Algorithme** :
   - Parcourt les événements triés par `ts_utc`
   - Pour chaque événement non traité :
     - Crée fenêtre `[event_time, event_time + 30 min]`
     - Trouve tous les événements dans cette fenêtre
     - Crée un cluster avec ces événements
     - Marque les événements comme traités
3. ✅ **Anchor time** : `anchor_time = cluster_events.iloc[0]['ts_utc']` (premier événement)
4. ✅ **Structure de sortie** :
   ```python
   {
       'events': DataFrame,
       'anchor_time': datetime,
       'n_events': int
   }
   ```

### Conformité

✅ **CONFORME** à PIPELINE_KNOWLEDGE_BASE.md

**Aucune modification nécessaire**

---

## 📝 Notes

- L'algorithme utilise une fenêtre glissante (pas de fenêtre fixe)
- Les événements sont marqués comme traités pour éviter les doublons
- L'anchor_time est bien le premier événement du cluster
- Les clusters sont triés par anchor_time

---

**Statut** : ✅ VALIDÉE  
**Action** : Passer à l'Étape 3




