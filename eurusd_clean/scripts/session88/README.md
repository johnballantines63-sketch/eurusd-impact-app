# SESSION 88 - GUIDE D'EXÉCUTION

## 🎯 OBJECTIF
Ajuster amplification pour surprises extrêmes (>100%) et valider sur 4 dates.

---

## 📋 ÉTAPES D'EXÉCUTION

### ÉTAPE 1 : Test Initial 01.08.2025 ⏳

**But :** Mesurer impact réel et vérifier si coefficient 1.8 est optimal.

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session88
python test_amplification_0108.py
```

**Résultat attendu :**
```
Surprise MAX : 500%
Amplification : 9.69x
Impact prédit : ~222 pips
Impact réel : ??? pips  ← CRITIQUE
```

**Décisions :**
- Si impact réel ≈ 220 pips → Coefficient 1.8 optimal ✅ Passer Étape 2
- Si impact réel ≈ 160 pips → Coefficient trop élevé ⚠️ Passer Étape 1B
- Si impact réel autre → Analyser et ajuster

---

### ÉTAPE 1B : Ajustement Coefficient (Si nécessaire)

**Uniquement si MAE > 30 pips sur 01.08.2025**

1. Éditer `adjust_coefficient.py` ligne 163 :
   ```python
   test_results = [
       {
           'name': '01 Août',
           'surprise_max': 500.0,
           'impact_real': XXX,  # ← Mettre valeur réelle mesurée
           'impact_brut': 30.3
       }
   ]
   ```

2. Exécuter :
   ```bash
   python adjust_coefficient.py
   ```

3. Suivre recommandations pour mise à jour automatique

---

### ÉTAPE 2 : Test Multi-Dates

**But :** Valider sur 4 dates avec coefficient ajusté (ou 1.8 si optimal).

```bash
python test_multi_dates.py
```

**Résultat attendu :**
```
┌───────────────┬────────┬────────┬────────┬────────┬─────────┐
│ Date          │ Évts   │ Surpr  │ Prédit │ Réel   │ Erreur  │
├───────────────┼────────┼────────┼────────┼────────┼─────────┤
│ 01 Août       │      X │  500%  │  XXXp  │  XXXp  │  XXXp ✅│
│ 17 Sept       │      X │   XX%  │  XXXp  │  XXXp  │  XXXp ✅│
│ 05 Sept       │      X │   XX%  │  XXXp  │  XXXp  │  XXXp ✅│
│ 10 Déc        │      X │   XX%  │  XXXp  │  XXXp  │  XXXp ✅│
└───────────────┴────────┴────────┴────────┴────────┴─────────┘

MAE  : XX.X pips
RMSE : XX.X pips
Tests OK : 4/4

✅✅✅ VALIDATION RÉUSSIE !
```

**Critères succès :**
- MAE global < 30 pips
- Tous les tests individuels < 30 pips
- Pas de régression sur zones 1-3 (surprises < 100%)

---

### ÉTAPE 3 : Validation Complète (Optionnel)

**Si tout est OK, tester avec script complet Double Wave :**

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session84
python validate_predictions_vs_reality.py
```

Ceci testera le système complet (amplification étendue + Double Wave).

---

## 📊 INTERPRÉTATION RÉSULTATS

### Scénario A : Coefficient 1.8 optimal ✅
```
01.08 : Impact réel ~220 pips, Erreur < 30 pips
→ Aucune modification nécessaire
→ Passer directement test multi-dates
```

### Scénario B : Coefficient trop élevé ⚠️
```
01.08 : Impact réel ~160 pips, Erreur > 50 pips
→ Coefficient suggéré : ~0.75
→ Exécuter adjust_coefficient.py
→ Retest après ajustement
```

### Scénario C : Coefficient trop faible ⚠️
```
01.08 : Impact réel ~300 pips, Erreur > 70 pips
→ Coefficient suggéré : ~2.5
→ Exécuter adjust_coefficient.py
→ Retest après ajustement
```

---

## 🔍 DIAGNOSTICS PROBLÈMES

### Erreur "Aucun événement HIGH IMPACT"
**Cause :** Date ou filtre incorrect  
**Solution :** Vérifier table `events` pour la date

```sql
SELECT event_title, ts_utc, actual, estimate
FROM events e
LEFT JOIN event_families ef ON e.event_key = ef.event_key
WHERE DATE(ts_utc) = '2025-08-01'
  AND country = 'US'
ORDER BY ts_utc;
```

### Erreur "Pas de données prix"
**Cause :** Timezone ou gap de données  
**Solution :** Vérifier table `prices_1m`

```sql
SELECT datetime, open, close
FROM prices_1m
WHERE DATE(datetime) = '2025-08-01'
  AND EXTRACT(HOUR FROM datetime) = 12
ORDER BY datetime;
```

### Amplification bizarre (< 1.0 ou > 10.0)
**Cause :** Bug dans calculate_amplification_extended  
**Solution :** Vérifier formulas_validated.py ligne 42-133

---

## 📁 FICHIERS SESSION 88

```
eurusd_clean/scripts/session88/
├── test_amplification_0108.py    ← Test isolé 01.08
├── test_multi_dates.py           ← Test 4 dates
├── adjust_coefficient.py         ← Ajustement auto
└── README.md                     ← Ce fichier

eurusd_clean/docs/
└── SESSION88_RAPPORT_INTERMEDIAIRE.md  ← État actuel

fx_impact_app/src/
└── formulas_validated.py         ← Fonction ajoutée
```

---

## ✅ CHECKLIST VALIDATION

- [ ] Test 01.08.2025 exécuté
- [ ] Impact réel mesuré : ___ pips
- [ ] MAE 01.08 < 30 pips
- [ ] Coefficient ajusté (si nécessaire)
- [ ] Test multi-dates exécuté
- [ ] MAE global < 30 pips
- [ ] Tous tests individuels OK
- [ ] Documentation finalisée
- [ ] Message Session 89 préparé

---

## 🚀 PROCHAINE SESSION

**Session 89 :** 
- Intégrer amplification étendue dans Planificateur
- Tests production avec Streamlit
- Validation utilisateur final

---

**Questions ?** Lire `SESSION88_RAPPORT_INTERMEDIAIRE.md` pour détails techniques.
