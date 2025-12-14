# Focus sur Mouvements MOYEN, FORT et TRÈS_FORT

## 🎯 Objectif

Concentrer les tests uniquement sur les mouvements **MOYEN, FORT et TRÈS_FORT**, excluant les mouvements **FAIBLE** (< 20 pips) qui ne sont pas intéressants pour le trading.

## 📊 Seuils de Classification

D'après `movement_detection_robust.py` :
- **FAIBLE** : < 20 pips ❌ (exclus des tests)
- **MOYEN** : 20-50 pips ✅
- **FORT** : 50-100 pips ✅
- **TRÈS_FORT** : >= 100 pips ✅

## ✅ Modifications Apportées

### Script `validate_on_new_dates.py`

1. ✅ Ajout classification du mouvement dans `detect_movement_for_date()`
2. ✅ Filtrage automatique : exclusion des mouvements FAIBLE
3. ✅ Message d'information sur le focus MOYEN/FORT/TRÈS_FORT

### Résultats

- **Premier test** : Sur 5 dates, 4 exclues (FAIBLE), 1 testée (MOYEN)
- **Prochaine étape** : Trouver plus de dates avec mouvements MOYEN/FORT/TRÈS_FORT

## 🔍 Prochaines Actions

1. **Scanner base de données** pour trouver toutes les dates avec mouvements >= 20 pips
2. **Créer liste de dates cibles** pour validation
3. **Tester uniquement ces dates** significatives

## 💡 Note Importante

En situation de trading, on n'utilisera pas les dates avec mouvements faibles. On choisira uniquement les mouvements **MOYEN, FORT ou TRÈS_FORT**. On reviendra sur les cas faibles une fois que tout sera opérationnel.


