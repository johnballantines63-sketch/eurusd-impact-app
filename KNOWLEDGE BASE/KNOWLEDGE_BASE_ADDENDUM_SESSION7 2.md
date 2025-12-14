### Décision #4 : Fenêtre temporelle pour calcul MFE

**Contexte :** Quelle durée analyser après l'événement pour calculer le MFE ?

**Options :**
1. 30 minutes (trop court)
2. 60 minutes (optimal)
3. 120 minutes (trop de bruit)

**Décision Session 7 :** Option 2 - 60 minutes

**Rationale :**
- ✅ Élimine valeurs aberrantes (3,703 → 1,056 pips)
- ✅ Améliore corrélation (0.108 → 0.292)
- ✅ Plus proche observation MT5
- ✅ Capte l'impact immédiat sans le bruit long terme

### Décision #5 : Utiliser 'estimate' au lieu de 'forecast'

**Contexte :** Quel champ utiliser pour calculer le surprise_index ?

**Options :**
1. `forecast` (toujours NULL)
2. `estimate` (41% de coverage)
3. `previous` (fallback)

**Décision Session 7 :** Option 2 avec fallback sur 3

**Rationale :**
- ✅ EODHD fournit `estimate`, pas `forecast`
- ✅ 13,089 valeurs disponibles (41%)
- ✅ Amélioration corrélation attendue : 0.007 → > 0.2
- ✅ Fallback sur `previous` si `estimate` NULL

**Code :**
```python
CASE 
    WHEN estimate IS NOT NULL AND estimate != 0 
    THEN ABS((actual - estimate) / estimate)
    WHEN previous IS NOT NULL AND previous != 0
    THEN ABS((actual - previous) / previous)
    ELSE 0 
END as surprise_index
```

---
