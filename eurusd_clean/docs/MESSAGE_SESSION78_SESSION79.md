# 📬 MESSAGE SESSION 78 → SESSION 79

**Date :** 25 octobre 2025  
**Session actuelle :** 78 ⚠️ EN COURS  
**Prochaine session :** 79  
**Statut :** Scripts créés mais logique incorrecte

---

## 🎯 MISSION SESSION 79

**Objectif :** Corriger scripts 2 et 3 pour utiliser formules validées EXACTES

**Problème identifié :** Scripts utilisent fonction simplifiée au lieu de logique complète formulas_validated.py

---

## 📁 FICHIERS À LIRE SESSION 79

1. **MANDATORY_SESSION_RULES.md** (obligatoire)
2. **project_state_new.md** (section ERREUR #10 Timezone)
3. **SESSION78_RAPPORT_RAPIDE.md** (contexte complet)
4. **MESSAGE_SESSION77_SESSION78.md** (contexte Session 77)

---

## 🔧 TRAVAIL À FAIRE

### Corriger script 2 : `2_optimize_window_session78.py`

**Copier fonction depuis :** `scripts/session77/3_validation_session75.py` lignes 90-150

**Fonction à copier :**
```python
def calculate_impact_with_params(
    events_cluster: List[Dict],
    intercept_multi: float,
    coef_multi: float,
    intercept_single: float,
    coef_single: float
) -> float:
```

**Garder :**
- calculate_adjusted_empirical_score (ligne 63)
- calculate_amplification_factor (ligne 77)
- Structure complète somme vectorielle
- FAMILY_SENTIMENT complet
- Correction 0.758

**Ajouter uniquement :**
- Parsing timezone : `dateutil.parser.parse(row['datetime'])`
- Conversion Berne : `dt_berne = dt_dataset.astimezone(pytz.timezone('Europe/Zurich'))`

---

### Corriger script 3 : `3_validation_finale_session78.py`

**Même logique que script 2**

---

## 📊 COEFFICIENTS V2 (SESSION 77)

```python
params_v2 = {
    'intercept_multi': -18.00,
    'coef_multi': 0.300,
    'intercept_single': -15.00,
    'coef_single': 0.300
}
```

---

## ✅ CRITÈRES SUCCÈS SESSION 79

| Critère | Objectif |
|---------|----------|
| MAE 11 sept | < 10 pips |
| MAE Session 75 | < 50 pips |
| Amélioration vs S77 | Oui |

---

## 🚀 EXÉCUTION

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/scripts/session78
./run_pipeline.sh
```

---

## 📋 MESSAGE TYPE SESSION 79

```
Bonjour Claude,

Session 79 - CORRECTION FORMULES SESSION 78

AVANT TOUT :
1. Lis MANDATORY_SESSION_RULES.md
2. Lis project_state_new.md (ERREUR #10)
3. Lis SESSION78_RAPPORT_RAPIDE.md
4. Lis ce message

PROBLÈME S78 :
Scripts 2 et 3 utilisent fonction simplifiée
au lieu de formules_validated.py

MISSION S79 :
Copier fonction calculate_impact_with_params
depuis scripts/session77/3_validation_session75.py
lignes 90-150 dans scripts 2 et 3

CHANGEMENTS :
+ Parser timezone (dateutil + pytz)
+ Fenêtre ±15/20/30/45/60 min
+ Filtres qualité SQL

FICHIERS :
- scripts/session78/2_optimize_window_session78.py
- scripts/session78/3_validation_finale_session78.py

GO après validation !
```

---

**Tokens S78 :** 113,674 / 190,000  
**Budget S79 :** ~76,000 tokens
