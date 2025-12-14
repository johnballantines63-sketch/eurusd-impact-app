# SESSION 92.3 : Validation et Implémentation Amplifications Calibrées

## 📋 Vue d'ensemble

Cette session implémente les amplifications calibrées trouvées par le grid search Session 92.2.

**Objectif :** MAE < 25 pips (amélioration vs 39.5 pips Session 91.2)

## 🗂️ Fichiers créés

### Scripts de validation (À EXÉCUTER D'ABORD)

1. **`test_11septembre_rapide.py`**
   - Test rapide sur date de référence 11.09.2024
   - Compare amplification 2.5 (V2.4) vs 2.2 (V2.5)
   - Durée : ~5 secondes

2. **`test_amplifications_calibrees.py`**
   - Validation complète sur toutes dates validation_events
   - Calcule MAE global et par type
   - Génère CSV résultats
   - Durée : ~30 secondes

### Scripts d'implémentation (À EXÉCUTER APRÈS VALIDATION OK)

3. **`modify_planificateur_v2.5.py`**
   - Modifie automatiquement le Planificateur V2.4 → V2.5
   - Crée backup automatique
   - Ajoute amplifications dynamiques
   - À exécuter UNIQUEMENT si validation réussie

## 🚀 Ordre d'exécution recommandé

### Phase 1 : Test rapide 11 septembre

```bash
cd eurusd_clean/scripts/session92.3
python test_11septembre_rapide.py
```

**Attendu :**
- Amplification V2.4 (2.5) : Erreur ~18-20 pips
- Amplification V2.5 (2.2) : Erreur ~10-12 pips
- ✅ Amélioration visible

### Phase 2 : Validation complète

```bash
python test_amplifications_calibrees.py
```

**Attendu :**
- MAE global < 25 pips ✅
- CPI : MAE ~10-15 pips
- NFP : MAE ~20-30 pips
- FOMC : MAE ~5-10 pips
- ISM : MAE ~10-20 pips

**SI MAE > 30 pips → STOP, analyser problème**

### Phase 3 : Implémentation Planificateur (SI VALIDATION OK)

```bash
python modify_planificateur_v2.5.py
```

**Ce script va :**
1. Créer backup Planificateur V2.4
2. Modifier version → V2.5
3. Ajouter dictionnaires AMPLIFICATIONS_BY_TYPE
4. Ajouter fonction get_amplification_for_type()
5. Modifier calculate_predictions() ligne 246
6. Vérifier modifications

## 📊 Amplifications calibrées (Grid Search Session 92.2)

| Type | Amplification | MAE (pips) | Dates testées |
|------|--------------|------------|---------------|
| CPI | 2.2 | 10.8 | 10 |
| NFP | 1.4 | 27.8 | 10 |
| FOMC | 1.0 | 2.8 | 3 |
| ISM | 0.5 | 7.4 | 9 |
| Employment | 0.6 | 0.5 | 1 |
| PMI | 0.6 | 1.0 | 1 |
| DEFAULT | 2.5 | - | Fallback |

## 🎯 Critères de validation

### ✅ Succès (implémentation justifiée)
- MAE global < 25 pips
- ≥70% dates avec erreur < 25 pips
- Aucun type avec MAE > 50 pips

### ⚠️ Partiel (analyse requise)
- MAE global 25-30 pips
- Types spécifiques problématiques (ISM ?)
- Envisager ajustements seuil 70%

### ❌ Échec (ne pas implémenter)
- MAE global > 30 pips
- Dégradation vs Session 91.2
- Considérer Option 3 (moyenne pondérée)

## 📈 Résultats attendus

**Session 91.2 (coefficient 0.55) :** MAE 39.5 pips
**Session 92.3 (amplifications calibrées) :** MAE ~20-25 pips
**Amélioration attendue :** +37%

## ⚠️ Points d'attention

1. **Type mixte** : Si cluster <70% d'un type → DEFAULT 2.5
2. **Fallback** : Types non calibrés → DEFAULT 2.5
3. **Mapping famille** : Vérifier FAMILY_TO_TYPE exhaustif
4. **Backup** : Toujours créé avant modification Planificateur

## 📝 Rapports générés

- `validation_amplifications_calibrees_session92.3.csv` : Résultats détaillés
- Backup Planificateur : `.py.backup_session92.3_avant_amplification_dynamique`

## 🔄 Rollback si problème

```bash
# Restaurer Planificateur V2.4 depuis backup
cd fx_impact_app/streamlit_app/pages
cp "5_Planificateur_V2_FORMULES_VALIDEES_backup_session72_fix_importance_20251024 copie 2.py.backup_session92.3_avant_amplification_dynamique" \
   "5_Planificateur_V2_FORMULES_VALIDEES_backup_session72_fix_importance_20251024 copie 2.py"
```

## 📚 Documentation complète

Voir `SESSION92.3_RAPPORT_COMPLET.md` (à créer après validation)

---

**Date :** 27 octobre 2025
**Session :** 92.3
**Objectif :** Validation rigoureuse avant implémentation production
