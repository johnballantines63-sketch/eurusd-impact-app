# 🚀 SESSION 37 - INSTRUCTIONS DÉMARRAGE

**Date :** 22 octobre 2025  
**Tokens Session 36 :** 105,866 / 190,000 (55.7%)  
**Tokens disponibles Session 37 :** 190,000  
**Limite pratique :** 115,000 tokens maximum

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🎯 REPRISE EXACTE : TEST STREAMLIT

**Où on en est :**
- ✅ Session 36 : Wrappers créés + validation 6/6 tests
- ✅ Fonctions clean validées sur données réelles
- ⏳ Planificateur PAS ENCORE testé dans Streamlit
- ⏳ Fonctions inline (~450 lignes) toujours présentes

**Prochaine action immédiate :** **TESTER STREAMLIT**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📋 WORKFLOW SESSION 37

### ÉTAPE 1 : Lire documentation (10 min) ⭐ OBLIGATOIRE

**Lire dans cet ordre :**
1. `eurusd_clean/docs/WORKFLOW_OBLIGATOIRE_SESSION_36_PLUS.md`
2. `eurusd_clean/PROJECT_STATE.md` - **SECTION 0 surtout** (erreurs communes)
3. `eurusd_clean/docs/SESSION_36_SUMMARY.md` (ce qui a été fait)
4. Ce fichier (MESSAGE_SESSION_37.md)

**IMPORTANT :** La Section 0 de PROJECT_STATE.md contient **6 erreurs documentées** à ne pas refaire.

---

### ÉTAPE 2 : Test Streamlit (30-45 min) 🎯 PRIORITÉ ABSOLUE

**Commande :**
```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app
streamlit run streamlit_app/Home.py
```

**Tests à effectuer dans l'ordre :**

1. **Démarrage application**
   - [ ] Application démarre sans erreur
   - [ ] Page Home charge

2. **Navigation vers Planificateur**
   - [ ] Cliquer sur "4_Planificateur-Multi-Evenements"
   - [ ] Page charge sans erreur
   - [ ] Pas d'erreur dans console

3. **Initialisation DataService**
   - [ ] Vérifier dans logs : pas de création multiple DataService
   - [ ] Initialisation st.session_state.data_service_global OK

4. **Sélection événements**
   - [ ] Sélectionner date/pays
   - [ ] Liste événements s'affiche
   - [ ] Cocher quelques événements

5. **Génération prédictions**
   - [ ] Cliquer "Générer prédictions"
   - [ ] Prédictions s'affichent
   - [ ] Pas d'erreur

6. **Timeline**
   - [ ] Timeline visuelle s'affiche
   - [ ] Événements positionnés correctement
   - [ ] Pas d'erreur plotly

7. **Graphiques backtest** (si événements passés)
   - [ ] Graphiques s'affichent
   - [ ] Prix réels chargés
   - [ ] Comparaison prédiction vs réalité OK

8. **Score tradabilité**
   - [ ] Score 0-100 affiché
   - [ ] Cohérent avec événements

**SI TOUS LES TESTS PASSENT → Passer ÉTAPE 3**  
**SI UN TEST ÉCHOUE → Debug avant de continuer**

---

### ÉTAPE 3 : Suppression progressive inline (2-3h)

**⚠️ SEULEMENT SI ÉTAPE 2 RÉUSSIE**

**Fichier :** `4_Planificateur-Multi-Evenements.py`

**Procédure STRICTE pour chaque fonction :**
```
1. COMMENTER la fonction inline (ne PAS supprimer)
2. Sauvegarder
3. Relancer Streamlit (Ctrl+C puis streamlit run...)
4. Tester la fonctionnalité concernée
5. Si OK → Supprimer définitivement la fonction commentée
6. Si KO → Dé-commenter, debug, réessayer
```

**Ordre de suppression (9 fonctions) :**

**Batch 1 - Simple (15 min chacune) :**
1. `calculate_fibonacci_levels()` (ligne ~480-500, ~20 lignes)
   - Test : Fibonacci levels s'affichent

2. `detect_overlaps()` (ligne ~500-530, ~30 lignes)
   - Test : Chevauchements détectés

3. `calculate_tradability_score()` (ligne ~530-550, ~20 lignes)
   - Test : Score affiché

**Batch 2 - Moyen (20 min chacune) :**
4. `group_events_by_time_window()` (ligne ~190-240, ~50 lignes)
   - Test : Clusters créés

5. `calculate_cluster_impact()` (ligne ~230-280, ~50 lignes)
   - Test : Impact cumulé calculé

6. `measure_real_impact()` (ligne ~590-640, ~50 lignes)
   - Test : Métriques réelles si événements passés

**Batch 3 - Complexe (30 min chacune) :**
7. `create_timeline_chart()` (ligne ~400-480, ~80 lignes)
   - Test : Timeline s'affiche correctement

8. `create_backtest_chart()` (ligne ~640-750, ~110 lignes)
   - Test : Graphiques backtest OK

**Batch 4 - CRITIQUE (45 min) :**
9. `get_real_prices_batch()` (ligne ~550-590, ~40 lignes) ⚠️
   - Test : Prix réels récupérés pour backtest
   - **LE PLUS IMPORTANT** - Tester avec événement passé

**Total suppression :** ~450 lignes

---

### ÉTAPE 4 : Documentation finale (1h)

1. Mettre à jour `PROJECT_STATE.md`
   - Statut : Phase 3/3 COMPLÉTÉE
   - Progression : 89% → 92%

2. Créer `SESSION_37_SUMMARY.md`
   - Récapitulatif tests Streamlit
   - Liste fonctions supprimées
   - Problèmes rencontrés et solutions

3. Créer `MESSAGE_SESSION_38.md` si nécessaire

---

### Temps total estimé : 4-5 heures
### Tokens estimés : 80,000-100,000

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🚨 RAPPELS CRITIQUES

### ⚠️ Erreurs à ne PAS refaire (voir PROJECT_STATE.md Section 0)

1. **Config :** Utiliser `config.get_db_path()` pas `config.db_path`
2. **DataService :** Créer UNE SEULE FOIS dans st.session_state
3. **Structure DB :** Colonne `datetime` pas `timestamp`
4. **Dates :** Plage disponible juin-oct 2024 seulement
5. **Clés dict :** `predicted_pips` pas `impact_pips`
6. **Tokens :** Arrêt à 115k maximum

### ✅ Bonnes pratiques

1. **Tester AVANT de supprimer** (approche pro, pas amateur)
2. **Une fonction à la fois** (jamais tout d'un coup)
3. **Backup accessible** : `backup_session35` en cas de problème
4. **Documenter tout** : erreurs, solutions, décisions

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📁 FICHIERS IMPORTANTS

**Planificateur :**
- `fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py`
- Backup : `.backup_session35` (même dossier)

**Documentation :**
- `eurusd_clean/PROJECT_STATE.md` ⭐ SOURCE UNIQUE DE VÉRITÉ
- `eurusd_clean/docs/SESSION_36_SUMMARY.md` ⭐ Ce qui a été fait
- `eurusd_clean/docs/DECOUVERTE_PLANIFICATEUR_SESSION_32.md` - Lignes fonctions

**Scripts utiles :**
- `eurusd_clean/scripts/validate_planificateur_migration.py` - Validation 6/6

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🎯 OBJECTIF SESSION 37

**Finaliser Phase 3/3 Migration Planificateur :**
- ✅ Test Streamlit complet
- ✅ Suppression ~450 lignes inline
- ✅ Planificateur 100% clean
- ✅ Progression 89% → 92%

**Critère de succès :**
Le Planificateur fonctionne parfaitement dans Streamlit en utilisant UNIQUEMENT les fonctions depuis eurusd_clean (zéro code dupliqué).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Prêt pour Session 37 !** 🚀

**Action immédiate :** Lancer Streamlit et tester le Planificateur.
