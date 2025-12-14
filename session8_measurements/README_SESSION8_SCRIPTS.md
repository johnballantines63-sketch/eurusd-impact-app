# 📊 SESSION 8 - SCRIPTS DE CALCUL GROUPÉ

**Date :** 17 octobre 2025  
**Objectif :** Corriger le calcul d'impacts (groupé vs individuel)

---

## 🎯 PROBLÈME CORRIGÉ

**Ancien script (`calculate_real_impacts.py`)** :
- Calculait l'impact pour CHAQUE événement individuellement
- Pour 33 événements à 14:30 → 33 lignes avec le même MFE (59.2 pips)
- ❌ Sous-estimait les impacts réels

**Nouveau script (`calculate_grouped_impacts.py`)** :
- Groupe les événements par minute
- Calcule UN impact par groupe temporel
- Pour 33 événements à 14:30 → 1 ligne avec le range réel (111.5 pips)
- ✅ Correspond aux mesures MT5

---

## 📁 FICHIERS CRÉÉS

### 1. `calculate_grouped_impacts.py` ⭐
**Script principal de calcul**

**Usage :**
```bash
python calculate_grouped_impacts.py
```

**Durée :** 10-20 minutes

**Ce qu'il fait :**
1. Groupe les événements par minute (time_group)
2. Calcule le RANGE TOTAL pour chaque groupe
3. Crée la table `event_group_impacts`
4. Détecte les phases successives
5. Compare avec l'ancien calcul

**Table créée : `event_group_impacts`**
- `time_group` : Minute du groupe (ex: 2025-09-11 14:30:00)
- `num_events` : Nombre d'événements simultanés
- `range_pips` : Range total (Prix_Max - Prix_Min)
- `mfe_pips` : Maximum Favorable Excursion
- `mae_pips` : Maximum Adverse Excursion
- `direction` : 'UP' ou 'DOWN'
- `ttr_minutes` : Time To Return
- Etc.

---

### 2. `validate_grouped_impacts.py` ⭐
**Script de validation**

**Usage :**
```bash
python validate_grouped_impacts.py
```

**Ce qu'il fait :**
1. Valide le 11 septembre 2025
2. Compare avec mesures MT5 (111.5 pips)
3. Compare avec ancien script (59.2 pips)
4. Analyse la distribution des impacts
5. Vérifie la qualité des données

**Validations importantes :**
- ✅ Cohérence range = max - min
- ✅ Détection valeurs aberrantes
- ✅ Vérification TTR
- ✅ Comparaison MT5 vs Script

---

## 📊 RÉSULTATS ATTENDUS

### Pour le 11 septembre 2025 à 14:30

**Ancien calcul :**
- 33 lignes (1 par événement)
- MFE : 59.2 pips (dupliqué 33 fois)
- ❌ Sous-estimation de 47%

**Nouveau calcul :**
- 1 ligne (groupe de 33 événements)
- Range : ~111.5 pips
- ✅ Correspond à MT5

**Mesure MT5 (référence) :**
- Range : 111.5 pips (1.17190 - 1.16075)
- MFE : 38.0 pips (depuis pré-événement)
- Direction : UP (net)

---

## 🚀 EXÉCUTION RECOMMANDÉE

### Ordre d'exécution :

```bash
# 1. Calculer les impacts groupés
python calculate_grouped_impacts.py

# 2. Valider les résultats
python validate_grouped_impacts.py
```

### Vérifications critiques :

Après exécution, vérifier :
- [ ] Table `event_group_impacts` créée
- [ ] 11 septembre : 1 ligne pour 14:30 (pas 33)
- [ ] Range calculé ≈ 111.5 pips (écart < 20%)
- [ ] Direction = UP
- [ ] Nombre total de groupes << nombre d'événements

---

## 📏 MÉTRIQUE UTILISÉE

**RANGE TOTAL** = Prix_Max - Prix_Min dans fenêtre d'observation

**Pourquoi ?**
- ✅ Mesure la violence totale du mouvement
- ✅ Indépendant du point d'entrée exact
- ✅ Capture spike + rebond
- ✅ Comparable entre événements
- ✅ Correspond aux observations MT5

**Alternative :** MFE Absolu (max favorable depuis référence)
- Utilisé pour calcul de profit potentiel
- Stocké dans colonne `mfe_pips`

---

## 🔄 DIFFÉRENCES AVEC ANCIEN SCRIPT

| Aspect | Ancien | Nouveau |
|--------|--------|---------|
| **Granularité** | Par événement | Par groupe (minute) |
| **Lignes 11 sept** | 33 | ~4-5 |
| **Impact 14:30** | 59.2 pips | ~111.5 pips |
| **Dupliquations** | Oui (même MFE) | Non (unique) |
| **Phases** | Non détectées | Détectées |
| **Pullback** | Non géré | Identifiable |

---

## 📝 PROCHAINES ÉTAPES

Après exécution et validation :

1. **Ré-analyser les corrélations**
   - Relancer `analyze_and_generate_formula.py`
   - Utiliser `event_group_impacts` au lieu de `event_impacts_calculated`

2. **Générer formule v9**
   - Basée sur les vrais impacts groupés
   - R² attendu > 0.4 (meilleur que v7)

3. **Mettre à jour KNOWLEDGE_BASE.md**
   - Ajouter erreur #7 (calcul individuel vs groupé)
   - Documenter métriques v9

4. **Créer RAPPORT_SESSION8_FINAL.md**
   - Documenter corrections apportées
   - Nouvelles métriques
   - Leçons apprises

---

## ⚠️ NOTES IMPORTANTES

### Fenêtre temporelle
- **Lookback :** 5 minutes avant (prix de référence)
- **Lookforward :** 60 minutes après (observation mouvement)
- Réduit de 120 → 60 min en Session 7

### Prix de référence
- Prix 5 minutes AVANT le groupe
- Évite le spread de la news juste avant
- Permet mesure objective

### Groupement
- Par minute (floor à la minute)
- Événements à 14:30:15 et 14:30:45 → même groupe 14:30:00

### Phases
- Détectées si gap > 5 minutes entre groupes
- Permet d'identifier séquences multi-phases
- Exemple 11 sept : Phase 1 (14:30) → Phase 2 (14:45)

---

## 🐛 DÉPANNAGE

### Erreur : "Table event_group_impacts not found"
→ Exécuter d'abord `calculate_grouped_impacts.py`

### Erreur : "No data for 2025-09-11"
→ Vérifier que `prices_1m` contient bien les données 2025
→ Vérifier que `events` contient les événements 2025

### Range calculé très différent de MT5
→ Vérifier la fenêtre lookforward (60 min)
→ Vérifier les timestamps (UTC ?)
→ Consulter les prix min/max dans la sortie

### Script trop lent
→ Normal : 10-20 min pour tous les groupes
→ Utiliser tqdm pour barre de progression
→ Les checkpoints affichent la progression

---

**FIN DU README**

**Version :** 1.0  
**Date :** 17 octobre 2025  
**Statut :** ✅ Prêt à exécuter
