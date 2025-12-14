# Validation Étape 3 : Définir Noyau Dur

**Date** : 2025-01-XX  
**Référence** : `docs/PIPELINE_REFERENCE/PIPELINE_KNOWLEDGE_BASE.md` ligne 49-53

---

## 📋 Spécifications selon Documentation

- **Méthode** : Analyse de fréquence sur 5 ans
- **Seuil** : Support >= 0.8 (80%)
- **Support** : Noyaux durs pré-définis (CPI, NFP)
- **Sortie** : Core events avec scores de support

---

## ⚠️ État Actuel du Code

**Fichier** : `scripts/run_pipeline_complete.py` ligne 231-297

### Problèmes Identifiés

1. ❌ **Analyse historique simplifiée** : 
   - Ligne 280 : `support_scores[event_id] = 1.0  # Par défaut, tous sont core`
   - Pas de vraie analyse de fréquence dans l'historique

2. ❌ **Pas d'utilisation des noyaux durs pré-définis** :
   - Les fichiers `docs/VALIDATION/CORE_EVENTS_CPI.txt` et `CORE_EVENTS_NFP.txt` ne sont pas utilisés
   - Pas de vérification contre ces noyaux durs pré-définis

3. ⚠️ **Algorithme incomplet** :
   - Ne calcule pas vraiment la fréquence d'apparition ensemble
   - Ne cherche pas dans l'historique les occurrences de ces événements ensemble

---

## ✅ Ce qui Est Correct

1. ✅ Paramètres : `support_threshold=0.8`, `years_lookback=5`
2. ✅ Structure de sortie correcte
3. ✅ Création d'identifiants canoniques pour les événements

---

## 🔧 Implémentation Nécessaire

### Algorithme Complet Requis

1. **Charger historique 5 ans** :
   - Pour chaque date dans [anchor_time - 5 ans, anchor_time]
   - Charger événements HIGH impact (`empirical_score > 40`)
   - Détecter clusters avec même fenêtre (30 min)

2. **Calculer support pour chaque événement** :
   - Pour chaque événement du cluster cible :
     - Compter combien de fois il apparaît avec les autres événements du cluster
     - Support = (nombre occurrences ensemble) / (nombre total occurrences)
     - Exemple : Si CPI apparaît 10 fois et CPI + Core CPI apparaissent ensemble 8 fois → support = 0.8

3. **Utiliser noyaux durs pré-définis** :
   - Charger `CORE_EVENTS_CPI.txt` et `CORE_EVENTS_NFP.txt`
   - Si le cluster correspond à un noyau dur pré-défini, utiliser directement
   - Sinon, calculer support depuis historique

4. **Filtrer par seuil** :
   - Garder seulement événements avec support >= 0.8

---

## 📝 Plan d'Action

**Option 1** : Implémenter analyse historique complète (complexe, nécessite beaucoup de requêtes DB)

**Option 2** : Utiliser noyaux durs pré-définis + fallback simplifié (plus rapide)

**Option 3** : Utiliser cache de clusters si disponible (le plus rapide)

**Recommandation** : Option 2 pour l'instant, avec possibilité d'améliorer plus tard

---

**Statut** : ⚠️ À COMPLÉTER  
**Action** : Implémenter analyse historique ou utiliser noyaux durs pré-définis




