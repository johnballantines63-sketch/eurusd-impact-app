# 🧪 GUIDE TEST SESSION 68

## 🚀 Lancement Rapide

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app
streamlit run pages/5_Planificateur_V2_FORMULES_VALIDEES.py
```

---

## 📋 CHECKLIST TESTS

### ✅ Test 1 : CPI Standard (2025-02-12)

**Configuration :**
- Date : 12 février 2025
- Prix départ : 1.17000

**Résultats Attendus :**
```
🟢 Type : Single Wave Fort
Cluster : 4 événements CPI
Surprise max : ~66%
Peak : T+8 min (14:38)
Pullback : 10% (surprise >50%)
Stabilisation : T+25 min
```

**Points de Vérification :**
- [ ] Badge "Single Wave Fort" affiché
- [ ] Info box : "Surprise > 15% (66%)"
- [ ] Info box : "Cluster ≥ 3 événements (4)"
- [ ] Info box : "Pattern standard CPI/NFP"
- [ ] Graphique : 3 phases distinctes
- [ ] Timeline : Montée T+0→T+8, Pullback T+8→T+15, Stab T+15→T+25
- [ ] Export CSV : Movement_Type = "Single Wave Fort"
- [ ] Export CSV : Peak_Time_T+8 = "14:38:00"

---

### ✅ Test 2 : NFP Gros Cluster (2024-12-06)

**Configuration :**
- Date : 6 décembre 2024
- Prix départ : 1.17000

**Résultats Attendus :**
```
🟢 Type : Single Wave Fort
Cluster : 8 événements NFP
Surprise max : ~30%
Peak : T+8 min
Pullback : 12% (30% < surprise < 50%)
Stabilisation : T+25 min
```

**Points de Vérification :**
- [ ] Badge "Single Wave Fort" affiché
- [ ] Gestion correcte 8 événements
- [ ] Pullback adapté à surprise 30%
- [ ] Timeline cohérente
- [ ] Export complet

---

### ✅ Test 3 : Cas Edge (Petit Cluster)

**Configuration :**
- Chercher date avec 1-2 événements seulement

**Résultats Attendus :**
```
⚪ Type : Single Wave Standard
Conditions SWF non remplies : Cluster < 3
```

**Points de Vérification :**
- [ ] Badge "Single Wave Standard"
- [ ] Fallback sur formules classiques
- [ ] Graphique standard affiché
- [ ] Pas d'erreur

---

## 🎯 VALIDATION GRAPHIQUES

### Single Wave Fort

**Structure Attendue :**
```
14:30 ─────────────→ 14:38 (PEAK)
      Montée linéaire   ↓
                     14:38 ─→ 14:45 (Pullback léger)
                              ↓
                           14:45 ─→ 14:55 (Stabilisation)
```

**Éléments Visuels :**
- [ ] 8 bougies vertes (montée)
- [ ] 7 bougies oranges (pullback)
- [ ] 10 bougies horizontales (stab)
- [ ] Annotation "Montée Linéaire +XX pips / 8 min"
- [ ] Annotation "PEAK 14:38 +XX pips"
- [ ] Annotation "Pullback Léger -XX pips (XX%)"
- [ ] Annotation "Stabilisation 14:45 - 14:55"
- [ ] Lignes horizontales repères

---

## 📊 VALIDATION EXPORT CSV

### Colonnes Requises

```csv
Date,Nombre_CPI,Score_Base_Moyen,Score_Ajusté,Surprise_Max_%,
Phase1_Impact_Pips,Phase1_TTR_Minutes,Phase2_Pullback_Pips,
Phase2_Duree_Minutes,Phase3_Reprise_Pips,Phase3_Duree_Minutes,
Mouvement_Net_Final_Pips,Movement_Type,Peak_Time_T+8,
Pullback_Low_Time,Final_Peak_Time,Stabilization_Time
```

### Validation Valeurs

**Pour Single Wave Fort :**
- Movement_Type = "Single Wave Fort"
- Peak_Time_T+8 ≠ "N/A"
- Pullback_Low_Time ≠ "N/A"
- Final_Peak_Time = Peak_Time_T+8 (même valeur)
- Stabilization_Time ≠ "N/A"

**Pour Double Wave (si détecté) :**
- Movement_Type = "Double Wave Momentum"
- Peak_Time_T+8 ≠ Final_Peak_Time (différent)

---

## 🐛 DEBUGGING COMMUN

### Problème : ImportError single_wave_strong

**Solution :**
```bash
# Vérifier path
cd fx_impact_app/src
ls -la single_wave_strong.py

# Vérifier imports dans Streamlit
python -c "import sys; sys.path.insert(0, 'src'); import single_wave_strong"
```

### Problème : Aucun événement trouvé

**Solution :**
- Vérifier date format : YYYY-MM-DD
- Vérifier que date contient CPI/NFP
- Tester avec dates connues :
  - 2025-02-12 (CPI)
  - 2024-12-06 (NFP)

### Problème : Graphique vide

**Solution :**
- Vérifier que timeline existe : `predictions['single_wave_timeline']`
- Vérifier logs console Streamlit
- Tester create_single_wave_strong_chart() séparément

---

## 📸 SCREENSHOTS ATTENDUS

### Interface Principale

```
🎯 Planificateur V2 - Formules Validées
Version 2.4 - Session 55 + détection automatique

[Date selector] [Prix input] [Calculer button]

✅ 4 événement(s) CPI trouvé(s)

📊 Résultats - Méthode Session 55

[Impact: +23.0 pips] [TTR: 4.5 min] [Pullback: 2.3 pips] ...

🌊 Type de Mouvement Détecté

✅ SINGLE WAVE FORT détecté ! (Session 67-68)

Conditions remplies :
- ✅ Surprise > 15% (66.7%)
- ✅ Cluster ≥ 3 événements (4)
- ✅ Pattern standard CPI/NFP (95% des cas)

🟢 Type : Single Wave Fort

📈 Timeline Prédite
[Graphique chandelier avec 3 phases]

📋 Événements CPI Chargés
[Tableau avec 4 lignes]

💾 Export
[Bouton télécharger CSV]
```

---

## ✅ CRITÈRES SUCCÈS

### Fonctionnel
- [x] Application démarre sans erreur
- [ ] Détection automatique fonctionne
- [ ] 3 types mouvements supportés
- [ ] Graphiques s'affichent correctement
- [ ] Export CSV fonctionne
- [ ] Timing précis dans export

### Performance
- [ ] Calculs < 2 secondes
- [ ] Graphique fluide
- [ ] Pas de memory leak

### UX
- [ ] Badge clair et visible
- [ ] Info box informative
- [ ] Timeline lisible
- [ ] Export intuitif

---

## 🎓 SCÉNARIOS AVANCÉS

### Test Comparaison Types

1. Chercher date Double Wave potentielle
2. Comparer timing SWF vs DW
3. Valider différences graphiques

### Test Edge Cases

1. Date sans événements → Message clair
2. Date événements non-CPI → Filtrage correct
3. Surprise 0% → Standard fallback
4. Cluster 2 events → Standard fallback

### Test Cohérence

1. Re-tester même date plusieurs fois
2. Vérifier résultats identiques
3. Valider cache fonctionnel

---

## 📞 SUPPORT

### Logs Utiles

```bash
# Voir logs Streamlit
streamlit run pages/5_Planificateur_V2_FORMULES_VALIDEES.py --logger.level=debug

# Logs Python
python -c "from single_wave_strong import *; print(detect_single_wave_strong.__doc__)"
```

### Contacts

- Session 68 documentation : `SESSION68_RAPPORT_INTEGRATION.md`
- Module source : `fx_impact_app/src/single_wave_strong.py`
- Tests validation : `fx_impact_app/src/tests/test_single_wave.py` (si créé)

---

**Bon test ! 🚀**
