# ⚡ SESSION 91 - TL;DR ULTRA-COURT

**Mission :** Tester coefficient 0.55 + Décider intégration

---

## 🚀 ACTIONS CLAUDE SESSION 91

### 1. Lister dates (30 sec)
```bash
python3 scripts/session90/list_available_dates.py
```
→ Afficher résultats console complets

### 2. Demander à André (2 min)
"Quelles dates tester ? Options :
- A) Test rapide (3 dates, 5 min)
- B) Validation complète (10-15 dates, 30 min)
- C) Semi-auto (5-7 dates, 15 min)"

### 3. Configurer dates (5 min)
Éditer `test_multi_dates_extended.py` ligne 31 avec dates choisies

### 4. Lancer validation (10-20 min)
```bash
python3 scripts/session90/test_multi_dates_extended.py
```
→ Afficher TOUS résultats

### 5. Analyser MAE (5 min)
- MAE < 30 pips ? → Intégrer ✅
- MAE 30-40 pips ? → Ajuster ⚠️
- MAE > 40 pips ? → Reporter ❌

### 6. Exécuter décision (20-40 min)
- Si ✅ : Intégrer `planner.py` (backup d'abord!)
- Si ⚠️ : Tester coef 0.50/0.60
- Si ❌ : Documentation seulement

### 7. Documenter (15 min)
- Rapport complet
- Mise à jour project_state
- Message Session 92 (si besoin)

---

## ⚠️ LIMITES CRITIQUES

- **105,000 tokens MAX**
- **Backup AVANT modification**
- **Afficher résultats COMPLETS**
- **Demander confirmation intégration**

---

## 🎯 RÉSULTAT ATTENDU

**Si MAE < 30 pips :**
→ Planificateur avec coefficient 0.55 intégré ✅

**Sinon :**
→ Plan clair pour Session 92 📋

---

**Fichier détaillé :** `SESSION91_INSTRUCTIONS_CLAIRES.md`

_TL;DR Session 91 - 26 oct 2025_
