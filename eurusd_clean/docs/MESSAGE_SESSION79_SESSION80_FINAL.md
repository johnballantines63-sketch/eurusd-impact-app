# MESSAGE SESSION 79 → SESSION 80

**Date :** 25 octobre 2025  
**Session :** 79 → 80  
**Tokens restants :** 190,000 (budget frais)

---

## 📋 RÉSUMÉ SESSION 79

### Objectif Initial
Corriger scripts Session 78 + Résoudre timezone récurrent

### Réalisations
- ✅ Module timezone_utils.py créé (280 lignes, 4 tests)
- ✅ Scripts mis à jour
- ✅ Documentation complète

### Problème Persistant
- ❌ Events = 0 encore (malgré timezone fix correct)
- ❌ MAE : 102.6 pips (identique S78)

---

## 🔍 HYPOTHÈSE IDENTIFIÉE

### Le Vrai Problème

**Dataset contient timestamps des PICS PRIX, pas des ÉVÉNEMENTS**

**Exemple :**
```
Dataset : 2024-12-18 19:36:00+01:00 = 18:36 UTC (pic prix)
Événement CPI : ~14:30 Berne = 13:30 UTC (événement économique)
Décalage : 5 heures
```

**Conséquence :**
```
Chercher ±30 min autour de 18:36 UTC = [18:06 → 19:06 UTC]
Événements CPI à 13:30 UTC
Résultat : 0 événements trouvés ❌
```

---

## 🎯 MISSION SESSION 80

### Objectif Principal

**DIAGNOSTIC COMPLET avant toute modification**

### Questions Critiques

1. **Quelles dates dans events DB ?**
   ```sql
   SELECT DISTINCT DATE(ts_utc), COUNT(*) 
   FROM events 
   GROUP BY DATE(ts_utc) 
   ORDER BY DATE(ts_utc)
   ```

2. **Événements pour dates dataset ?**
   ```sql
   SELECT DATE(ts_utc), strftime(ts_utc, '%H:%M'), event_title, country
   FROM events 
   WHERE DATE(ts_utc) IN ('2024-12-18', '2024-04-10', '2025-09-11')
   ORDER BY ts_utc
   ```

3. **Décalage réel événements vs pics ?**
   - Comparer heures événements DB
   - Avec heures mouvements dataset
   - Calculer décalage moyen

4. **TTR observé ?**
   - Événement à 13:30 UTC
   - Pic à 18:36 UTC
   - TTR = 5 heures ? (anormal !)

---

## 📊 APPROCHE SESSION 80

### Phase 1 : Diagnostic (20-30k tokens)

**Script diagnostic simple :**
```python
# 1. Lister événements DB pour dates dataset
# 2. Afficher heures événements
# 3. Comparer avec heures pics dataset
# 4. Identifier pattern décalage
```

**Output attendu :**
```
Date        | Heure Event DB | Heure Pic Dataset | Décalage
2024-12-18  | 13:30 UTC      | 18:36 UTC        | +5h06
2024-04-10  | 12:30 UTC      | 14:04 Berne      | ?
...
```

### Phase 2 : Solution Basée sur Faits (30k tokens)

**Selon diagnostic :**

**Si décalage constant 5h :**
```python
# Chercher AVANT le pic
start = peak_time - timedelta(hours=6)
end = peak_time + timedelta(minutes=15)
```

**Si décalage variable :**
```python
# Fenêtre large adaptative
# Ou identifier événement puis chercher pic après
```

**Si autre problème :**
```python
# Solution adaptée au problème réel
```

### Phase 3 : Validation (20k tokens)

- Pipeline complet
- Vérifier Events > 0
- MAE < 50 pips attendu
- Documentation

---

## 📁 FICHIERS CLÉS SESSION 80

### À Lire

```
docs/SESSION79_RAPPORT_FINAL.md (ce fichier référence)
docs/project_state_new.md (ERREUR #10)
```

### À Utiliser

```
src/utils/timezone_utils.py (module valide)
data/warehouse.duckdb (DB)
data/movements_strong_session75_v3.csv (dataset)
```

### À Créer

```
scripts/session80/1_diagnostic_db.py (diagnostic complet)
scripts/session80/2_solution_fenetre.py (correction ciblée)
scripts/session80/run_pipeline.sh (test final)
```

---

## ⚠️ RÈGLES CRITIQUES SESSION 80

### AVANT Tout Code

1. ✅ Lire documentation
2. ✅ **DIAGNOSTIC COMPLET d'abord**
3. ✅ Comprendre problème réel
4. ✅ Valider hypothèse avec utilisateur
5. ✅ **Puis** solution ciblée

### NE PAS

- ❌ Supposer cause sans diagnostic
- ❌ Modifier code avant comprendre
- ❌ Créer multiples versions
- ❌ Ignorer résultats tests

### TOUJOURS

- ✅ Mesurer avant couper
- ✅ 1 hypothèse → 1 test → 1 solution
- ✅ Documentation claire
- ✅ Afficher tokens régulièrement

---

## 💡 HYPOTHÈSES À TESTER

### Hypothèse 1 : Décalage Temporel

**Si dataset = pics prix et DB = événements**
- Décalage constant 4-6 heures
- Solution : Fenêtre asymétrique [-360, +15] min

### Hypothèse 2 : Dates Incompatibles

**Si dates dataset ≠ dates DB**
- Dataset a des dates sans événements
- Solution : Filtrer dataset sur dates avec événements

### Hypothèse 3 : Filtres SQL Trop Restrictifs

**Si importance_n >= 2 ET score > 20 trop strict**
- Solution : Relâcher filtres temporairement
- Tester avec `importance_n >= 1` et `score > 10`

### Hypothèse 4 : Structure Dataset Incorrecte

**Si datetime dataset mal interprété**
- Solution : Vérifier format exact
- Parser différemment si nécessaire

---

## 🎯 CRITÈRES SUCCÈS SESSION 80

| Métrique | Objectif |
|----------|----------|
| Diagnostic complet | ✅ Fait |
| Problème identifié | ✅ Clair |
| Events trouvés | > 0 |
| MAE Session 75 | < 60 pips |
| Solution documentée | ✅ Complète |

---

## 📊 BUDGET TOKENS

**Session 80 : 190,000 tokens frais**

**Allocation recommandée :**
- Lecture docs : 20k
- Diagnostic : 30k
- Solution : 40k
- Tests : 20k
- Documentation : 20k
- Réserve : 60k

---

## ✅ CHECKLIST DÉMARRAGE SESSION 80

- [ ] Lire MANDATORY_SESSION_RULES.md
- [ ] Lire project_state_new.md
- [ ] Lire SESSION79_RAPPORT_FINAL.md
- [ ] Résumer compréhension
- [ ] **Créer script diagnostic AVANT solution**
- [ ] Valider diagnostic avec utilisateur
- [ ] Puis solution ciblée
- [ ] Tests et validation

---

**Session 79 : Timezone fix créé, problème plus profond identifié**  
**Session 80 : Diagnostic d'abord, solution ensuite** 🔍

**Budget : 190k tokens frais = Temps suffisant pour bien faire** ✅
