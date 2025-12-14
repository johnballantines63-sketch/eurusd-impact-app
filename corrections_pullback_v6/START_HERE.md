# 🎯 FICHE EXPRESS - TOUT EN 1 PAGE

## ✅ OÙ J'EN SUIS ?
```
Version actuelle : STABLE (avant pullback V5)
Amplitude       : ~120-159 pips
Backup créé     : ✅ before_pullback_v5_20251014_101318.py
```

## 🤔 QUE FAIRE ?

### Option A : Garder stable (simple)
```bash
find . -name "__pycache__" -exec rm -rf {} +
# Tester : Date 11/09/2025, Prix 1.16810
```

### Option B : Activer pullback V6 (réaliste)
```bash
cd corrections_pullback_v6
./run_pullback_v6_correction.sh
find .. -name "__pycache__" -exec rm -rf {} +
# Tester : Date 11/09/2025, Prix 1.16810
```

## 🔍 DIAGNOSTIC RAPIDE
```bash
cd corrections_pullback_v6 && python3 diagnostic.py
```

## 🔄 ROLLBACK SI BESOIN
```bash
cp fx_impact_app/src/backups/price_curve_generator_before_pullback_v5_*.py \
   fx_impact_app/src/price_curve_generator.py
```

## 📚 DOCS PAR BESOIN

| Je veux...                           | Fichier                           |
|--------------------------------------|-----------------------------------|
| Savoir quoi faire                    | `ACTIONS_RAPIDES.md`              |
| Comprendre visuellement              | `GUIDE_VISUEL.md`                 |
| Détails techniques                   | `README.md`                       |
| Historique complet                   | `session_14oct2025_RESTAURATION.md` |
| Liste complète des fichiers          | `INDEX.md`                        |

## 🐛 BUG CORRIGÉ
```python
# ❌ AVANT (V5) - Bug double négatif
base_contribution -= pullback_amount * (1 if vectorial > 0 else -1)

# ✅ APRÈS (V6) - Substitution propre
pullback_level = 1.0 - (0.35 * pullback_intensity)
base_contribution = vectorial * sigmoid * pullback_level
```

## 🎯 TEST STANDARD
- **Date** : 11/09/2025
- **Prix** : 1.16810
- **Attendu** : ~120-159 pips (stable) ou ~120-159 pips + pullback (V6)

## ⚠️ N'OUBLIEZ PAS
1. ✅ Vider cache Python : `find . -name "__pycache__" -exec rm -rf {} +`
2. ✅ Vider cache navigateur : Cmd+Shift+Del
3. ✅ Tester après chaque modification

## 📊 ÉVOLUTION

| Version | Amplitude | Status |
|---------|-----------|--------|
| Initial | 463 pips | ❌ |
| V4      | 159 pips | ✅ |
| V5      | 230 pips | ❌ |
| **Actuel** | **159 pips** | **✅** |
| V6      | 159 pips + pullback | 🔧 Dispo |

## 🚀 PROCHAINE SESSION
```
"Suite restauration 14/10/2025.
Version : [stable/V6]
Amplitude : [VALEUR] pips
Status : [OK/problème]"
```

---
**14 Octobre 2025** | **Claude** | **v1.0**
