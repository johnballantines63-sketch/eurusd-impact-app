# 🎯 SESSION 39 - GUIDE D'ACTIONS IMMÉDIAT

**Date :** 22 octobre 2025  
**Focus :** Corrections doublons + Vérification Michigan

---

## ✅ ÉTAPE 1 : Vérifier Michigan (5 min)

### Commande :
```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC
python3 check_michigan_events.py
```

### Résultats attendus :
1. Liste des événements Michigan le 11 septembre 2025
2. Si Michigan à 14:45 existe → ✅ Pattern fonctionne
3. Si Michigan absent → Pattern OK mais événement pas dans DB

**Action selon résultat :**
- ✅ Michigan trouvé → Passer à ÉTAPE 2
- ❌ Michigan absent → Documenter et passer à ÉTAPE 2 (priorité = doublons)

---

## ✅ ÉTAPE 2 : Diagnostiquer Doublons (10 min)

### Commande :
```bash
python3 diagnose_duplicates_session39.py
```

### Ce que le script va révéler :
1. Nombre d'événements bruts (table `events`)
2. Nombre après JOIN avec `event_families`
3. Effet de SELECT DISTINCT
4. Détail des doublons CPI/Jobless Claims

### Analyser les résultats :
- **Si DISTINCT résout le problème** → Query Streamlit correcte, tester l'application
- **Si doublons persistent** → Problème dans la DB elle-même

---

## ✅ ÉTAPE 3 : Tester Application Streamlit (15 min)

### Démarrer Streamlit :
```bash
cd fx_impact_app
streamlit run streamlit_app/Home.py
```

### Tests à effectuer :

#### Test 1 : Charger 11 septembre 2025
1. Aller dans **Planificateur**
2. Sélectionner date : **11 septembre 2025**
3. Cliquer "Charger événements"

#### Test 2 : Compter événements distincts
- [ ] **CPI (US)** apparaît combien de fois ? (Attendu : **1x**)
- [ ] **Jobless Claims (US)** apparaît combien de fois ? (Attendu : **1x**)
- [ ] **Total événements mappés** : ? (Attendu : **2-3 au lieu de 7**)

#### Test 3 : Vérifier Impact Combiné
- [ ] **Impact Phase 1** : ? pips (Attendu : **~35 pips au lieu de 63**)
- [ ] Impact cohérent avec événements distincts

#### Test 4 : Michigan 14:45
- [ ] Michigan Consumer Sentiment apparaît ? (Dépend résultat ÉTAPE 1)

---

## ✅ ÉTAPE 4 : Créer Rapport Session 39 (15 min)

### Fichier : `eurusd_clean/docs/SESSION_39_RAPPORT.md`

### Contenu minimal :
```markdown
# SESSION 39 - RAPPORT

## Résultats Michigan
- [x] Script check_michigan_events.py exécuté
- Résultat : [Coller output]

## Résultats Doublons
- [x] Script diagnose_duplicates_session39.py exécuté
- Résultat : [Coller output]
- Conclusion : [DISTINCT résout / ne résout pas]

## Tests Streamlit
- Date testée : 11 septembre 2025
- CPI apparaît : X fois
- Jobless Claims apparaît : X fois
- Total événements mappés : X
- Impact Phase 1 : X pips

## Décision
- [ ] Corrections OK → Migration Planificateur
- [ ] Corrections NOK → Debug supplémentaire nécessaire
```

---

## ⚠️ PROBLÈMES POSSIBLES ET SOLUTIONS

### Problème A : Python3 introuvable
```bash
python --version  # Vérifier si python ou python3
```

### Problème B : Module duckdb introuvable
```bash
pip3 install duckdb pandas  # Installer dépendances
```

### Problème C : Streamlit ne démarre pas
```bash
cd fx_impact_app
pip3 install -r requirements.txt  # Si requirements.txt existe
```

### Problème D : Doublons persistent après DISTINCT
→ Nettoyage DB nécessaire (créer script Session 40)

---

## 📋 CHECKLIST SESSION 39

- [ ] check_michigan_events.py exécuté
- [ ] diagnose_duplicates_session39.py exécuté
- [ ] Streamlit testé avec 11 sept 2025
- [ ] Screenshots pris (si nécessaire)
- [ ] Rapport Session 39 créé
- [ ] PROJECT_STATE.md mis à jour
- [ ] INDEX.md mis à jour

---

## 🎯 CRITÈRES DE SUCCÈS

### ✅ Succès Complet :
1. Michigan vérifié (présent ou absence confirmée)
2. Doublons CPI/Jobless éliminés
3. Impact Phase 1 = ~35 pips (cohérent)
4. Application fonctionne sans erreur

### ⚠️ Succès Partiel :
1. Doublons réduits mais pas éliminés
2. Impact réduit mais encore surestimé
→ Debug supplémentaire Session 40

### ❌ Échec :
1. Doublons persistent intégralement
2. Application ne démarre pas
→ Revenir aux fondamentaux Session 40

---

## ⏱️ ESTIMATION TEMPS

| Tâche | Temps |
|-------|-------|
| ÉTAPE 1 : Michigan | 5 min |
| ÉTAPE 2 : Diagnostic doublons | 10 min |
| ÉTAPE 3 : Tests Streamlit | 15 min |
| ÉTAPE 4 : Rapport | 15 min |
| **TOTAL** | **45 min** |

Budget tokens restant : ~145,000

---

**Prêt à commencer ? Exécutez ÉTAPE 1 !**
