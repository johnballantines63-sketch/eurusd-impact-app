# 🧪 GUIDE TEST PLANIFICATEUR V2 - SESSION 82

**Date :** 26 octobre 2025  
**Version Planificateur :** 2.5 (Session 81 - Debug Mode)  
**Objectif :** Validation exhaustive multi-dates

---

## 📋 PRÉPARATION

### Étape 1 : Lancer Streamlit

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app
streamlit run streamlit_app/pages/5_Planificateur_V2_FORMULES_VALIDEES_backup_session_72_copie.py
```

### Étape 2 : Activer Mode Debug (Recommandé)

Dans la sidebar gauche :
- ✅ Cocher **"🔍 Mode Debug"**

Cela affichera les logs détaillés pour chaque date testée.

---

## 🎯 DATES À TESTER

### Test 1 : 11.09.2025 (Référence Validée) ✅

**Statut :** ✅ Déjà validé Session 81  
**Type :** CPI US (11 événements HIGH IMPACT)  
**Attendu :**
- Événements trouvés : **11**
- Type mouvement : **Double Wave** ou **Single Wave Fort**
- Impact : **~57 pips** (formules S51-55)
- Graphique : ✅ S'affiche

**Instructions :**
1. Sélectionner **11/09/2025** dans le date picker
2. Cliquer **"🎯 Calculer Prédictions"**
3. Vérifier logs debug (si activé)
4. Confirmer graphique s'affiche

**Résultat attendu :** ✅ SUCCÈS

---

### Test 2 : 12.02.2025 (Validé Session 81) ✅

**Statut :** ✅ Déjà validé Session 81  
**Type :** CPI US (8 événements HIGH IMPACT)  
**Attendu :**
- Événements trouvés : **8**
- Type mouvement : **Single Wave Fort**
- Impact : **~40-50 pips**
- Graphique : ✅ S'affiche

**Instructions :**
1. Sélectionner **12/02/2025** dans le date picker
2. Cliquer **"🎯 Calculer Prédictions"**
3. Vérifier logs debug
4. Confirmer changement de date fonctionne

**Résultat attendu :** ✅ SUCCÈS

---

### Test 3 : 01.08.2025 (NFP Extrême) ⏳ PRIORITAIRE

**Statut :** ⏳ À tester Session 82  
**Type :** NFP US (17 événements HIGH IMPACT)  
**Attendu :**
- Événements trouvés : **17** (cas extrême !)
- Type mouvement : **Double Wave** (surprise élevée)
- Impact : **> 60 pips** (très fort)
- Graphique : ✅ Devrait s'afficher

**Pourquoi prioritaire :**
- Plus grand nombre d'événements HIGH IMPACT
- Test robustesse formules sur cas extrême
- NFP = événement majeur marché

**Instructions :**
1. Sélectionner **01/08/2025** dans le date picker
2. Cliquer **"🎯 Calculer Prédictions"**
3. **OBSERVER ATTENTIVEMENT** :
   - Nombre événements chargés
   - Type mouvement détecté
   - Impact prédit (devrait être élevé)
   - Performance calcul (17 événements)
4. Vérifier graphique s'affiche correctement

**Critères succès :**
- [ ] 17 événements chargés
- [ ] Calcul complété sans erreur
- [ ] Impact > 50 pips
- [ ] Graphique affiché
- [ ] Pas de crash ou timeout

---

### Test 4 : 10.04.2024 (CPI Historique) ⏳

**Statut :** ⏳ À tester Session 82  
**Type :** CPI US (10 événements HIGH IMPACT)  
**Attendu :**
- Événements trouvés : **10**
- Type mouvement : **Single Wave Fort** ou **Double Wave**
- Impact : **~50 pips**

**Pourquoi tester :**
- Date 2024 (valider données historiques)
- Nombre moyen d'événements
- Test stabilité sur année précédente

**Instructions :**
1. Sélectionner **10/04/2024** dans le date picker
2. Cliquer **"🎯 Calculer Prédictions"**
3. Vérifier résultats cohérents
4. Comparer avec dates 2025

**Critères succès :**
- [ ] 10 événements chargés
- [ ] Calcul complété
- [ ] Impact raisonnable (40-60 pips)
- [ ] Graphique affiché

---

### Test 5 : 18.12.2024 (Interest Rates) ⏳

**Statut :** ⏳ À tester Session 82  
**Type :** Fed/BCE Interest Rate Decisions (13 événements HIGH IMPACT)  
**Attendu :**
- Événements trouvés : **13**
- Type mouvement : **Double Wave** (taux = surprise forte)
- Impact : **> 50 pips**

**Pourquoi tester :**
- Famille événements différente (pas CPI/NFP)
- Test détection automatique type mouvement
- Importance majeure marché

**Instructions :**
1. Sélectionner **18/12/2024** dans le date picker
2. Cliquer **"🎯 Calculer Prédictions"**
3. Observer type mouvement détecté
4. Vérifier cohérence prédictions

**Critères succès :**
- [ ] 13 événements chargés
- [ ] Type mouvement correct
- [ ] Impact élevé
- [ ] Graphique affiché

---

## 📊 TEMPLATE RAPPORT RÉSULTATS

Pour chaque date testée, documenter :

```markdown
### Date : DD/MM/YYYY

**Type événements :** [CPI / NFP / Interest Rate / Mixte]

**Résultats :**
- ✅/❌ Événements trouvés : X (attendu : Y)
- ✅/❌ Type mouvement : [DOUBLE_WAVE / SINGLE_WAVE_STRONG / STANDARD]
- ✅/❌ Impact prédit : X.X pips
- ✅/❌ TTR : X minutes
- ✅/❌ Pullback : X.X pips
- ✅/❌ Graphique affiché

**Logs debug (si activé) :**
```
[Copier logs pertinents]
```

**Screenshots :** [Si nécessaire]

**Statut final :** ✅ SUCCÈS / ⚠️  PARTIEL / ❌ ÉCHEC

**Notes :**
[Observations, anomalies, commentaires]
```

---

## 🔍 POINTS D'ATTENTION

### Mode Debug

**Logs à surveiller :**
1. **Date sélectionnée** - Doit correspondre à la date choisie
2. **Date convertie** - Format `YYYY-MM-DD HH:MM:SS`
3. **Événements trouvés** - Nombre doit matcher attendu
4. **Aperçu événements** - Tableau avec labels et scores
5. **Impact prédit** - Valeur en pips
6. **Type mouvement** - DOUBLE_WAVE / SINGLE_WAVE_STRONG

### Erreurs Possibles

**Scénario A : 0 événements trouvés**
- ❌ Problème : Date n'a pas d'événements HIGH IMPACT US
- ✅ Solution : Vérifier date dans DB ou choisir autre date

**Scénario B : Erreur calcul prédictions**
- ❌ Problème : Données manquantes (actual, forecast)
- ✅ Solution : Vérifier qualité données pour cette date

**Scénario C : Graphique ne s'affiche pas**
- ❌ Problème : Erreur création graphique Plotly
- ✅ Solution : Logs debug montreront l'erreur exacte

**Scénario D : Performance lente (17 événements)**
- ⚠️  Attendu : Calcul peut prendre 2-3 secondes
- ✅ Acceptable si < 10 secondes

---

## 📈 CRITÈRES VALIDATION GLOBALE

### Pour valider le planificateur complètement :

**Fonctionnel (CRITIQUE) :**
- [ ] Au moins **5 dates testées** avec succès
- [ ] Au moins **1 date NFP** testée (01.08.2025)
- [ ] Au moins **1 date historique 2024** testée
- [ ] **Changement de date** fonctionne entre tests
- [ ] **Graphique s'affiche** pour toutes les dates

**Performance (IMPORTANT) :**
- [ ] Temps calcul < 10 secondes (même 17 événements)
- [ ] Pas de crash ou timeout
- [ ] Interface responsive

**Qualité (SOUHAITABLE) :**
- [ ] Prédictions cohérentes (40-70 pips pour HIGH)
- [ ] Type mouvement correctement détecté
- [ ] Logs debug informatifs (si activés)

---

## 🎯 RÉSUMÉ SESSION 82

**Objectif :** 5 dates testées et validées

**Priorités :**
1. ⭐⭐⭐ Test 01.08.2025 (NFP extrême - 17 événements)
2. ⭐⭐ Test 10.04.2024 (historique 2024)
3. ⭐⭐ Test 18.12.2024 (Interest Rates)
4. ⭐ Re-test 11.09.2025 (confirmer stabilité)
5. ⭐ Re-test 12.02.2025 (confirmer stabilité)

**Temps estimé :** 30-45 minutes pour 5 tests complets

---

## 📝 APRÈS LES TESTS

### Décision Mode Debug

**Option A : Garder toggle (RECOMMANDÉ) ✅**
- Interface propre par défaut
- Debug accessible si besoin
- Pas d'impact performance
- Facilite troubleshooting futur

**Option B : Retirer logs debug ❌**
- Code plus léger
- Perd capacité debug
- Risque si bugs futurs

**Recommandation Session 82 :** GARDER le toggle debug

### Documentation à Créer

Une fois tests complétés :
1. **SESSION82_RAPPORT_COMPLET.md** - Résultats détaillés
2. **GUIDE_DATES_DISPONIBLES.md** - Liste dates DB
3. **GUIDE_UTILISATEUR_PLANIFICATEUR.md** - Mode d'emploi
4. **MESSAGE_SESSION82_SESSION83.md** - Transition

---

*Guide créé Session 82 - 26 octobre 2025*  
*Planificateur Version 2.5 (Debug Mode)*
