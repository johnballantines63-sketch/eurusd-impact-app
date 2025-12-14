# Nouveaux Patterns de Noyaux Durs

**Date** : 2025-01-XX  
**Problème** : Noyau dur "GENERIC" pour 2025-05-29 malgré événements significatifs (Jobless Claims + PCE)  
**Solution** : Ajout de patterns pour détecter d'autres types de noyaux durs

---

## 🔍 PROBLÈME IDENTIFIÉ

Pour **2025-05-29**, le cluster principal contenait :
- 2 événements Jobless Claims (continuing, 4week average)
- 2 événements PCE Prices (core pce prices, pce prices)
- 2 autres événements (GDP Sales, Real Consumer Spending)

**Résultat** : Noyau dur détecté comme "GENERIC" (tous les 6 événements core)

**Impact** : Recherche de clusters similaires moins précise car le noyau dur était trop large.

---

## ✅ SOLUTION IMPLÉMENTÉE

### Patterns Ajoutés

1. **JOBLESS_PATTERN** : `(?i)(jobless claims|unemployment claims|initial jobless|continuing jobless)`
2. **PCE_PATTERN** : `(?i)(pce prices|personal consumption expenditure|core pce)`
3. **GDP_PATTERN** : `(?i)(gdp|gross domestic product)`

### Hiérarchie de Détection

Les noyaux durs sont détectés par ordre de priorité :

1. **CPI** (≥2 événements CPI)
   - Pattern : `cpi|consumer price|inflation rate|core inflation|harmonised inflation`
   - Exemple : Cluster CPI avec inflation rate, core inflation

2. **NFP** (≥1 événement NFP)
   - Pattern : `non farm payrolls|nonfarm`
   - Exemple : Cluster NFP avec non farm payrolls

3. **JOBLESS_PCE** (≥2 Jobless ET ≥1 PCE) ⭐ **NOUVEAU**
   - Pattern : Jobless Claims + PCE Prices
   - Exemple : 2025-05-29 (2 Jobless, 2 PCE)
   - Core events : Jobless Claims + PCE Prices uniquement

4. **GDP** (≥2 événements GDP) ⭐ **NOUVEAU**
   - Pattern : `gdp|gross domestic product`
   - Exemple : Cluster avec GDP growth rate, GDP sales, GDP price index

5. **JOBLESS** (≥2 événements Jobless) ⭐ **NOUVEAU**
   - Pattern : Jobless Claims uniquement
   - Exemple : Cluster avec initial + continuing jobless claims

6. **PCE** (≥1 événement PCE) ⭐ **NOUVEAU**
   - Pattern : PCE Prices uniquement
   - Exemple : Cluster avec core pce prices

7. **GENERIC** (fallback)
   - Tous les événements sont core si aucun pattern ne correspond

---

## 📊 RÉSULTATS

### Avant Correction (2025-05-29)

```
Type : GENERIC
Core events : 6/6 événements
   - continuing jobless claims_US_3 ✅
   - core pce prices qoq 2nd est_US_3 ✅
   - gdp sales qoq 2nd est_US_3 ✅
   - jobless claims 4week average_US_3 ✅
   - pce prices qoq 2nd est_US_3 ✅
   - real consumer spending qoq 2nd est_US_3 ✅
```

### Après Correction (2025-05-29)

```
Type : JOBLESS_PCE
Core events : 4/6 événements
   - continuing jobless claims_US_3 ✅ CORE
   - core pce prices qoq 2nd est_US_3 ✅ CORE
   - gdp sales qoq 2nd est_US_3 ❌ Non-core
   - jobless claims 4week average_US_3 ✅ CORE
   - pce prices qoq 2nd est_US_3 ✅ CORE
   - real consumer spending qoq 2nd est_US_3 ❌ Non-core
```

### Validation Cluster Historique (2025-02-27)

```
Type : JOBLESS_PCE
Core events : 4 événements
Jaccard avec 2025-05-29 : 1.000 (parfait)
Événements communs :
   - continuing jobless claims_US_3
   - jobless claims 4week average_US_3
   - core pce prices qoq 2nd est_US_3
   - pce prices qoq 2nd est_US_3
```

---

## 📝 CODE MODIFIÉ

**Fichier** : `scripts/run_pipeline_complete.py`  
**Fonction** : `etape3_definir_noyau_dur`  
**Lignes** : ~351-424

### Ajout des Patterns

```python
# Patterns de familles pour détection noyaux durs pré-définis
CPI_PATTERN = r'(?i)(cpi|consumer price|inflation rate|core inflation|harmonised inflation)'
NFP_PATTERN = r'(?i)(non farm payrolls|nonfarm)'
JOBLESS_PATTERN = r'(?i)(jobless claims|unemployment claims|initial jobless|continuing jobless)'  # NOUVEAU
PCE_PATTERN = r'(?i)(pce prices|personal consumption expenditure|core pce)'  # NOUVEAU
GDP_PATTERN = r'(?i)(gdp|gross domestic product)'  # NOUVEAU
```

### Logique de Détection

```python
# PRIORITÉ 3 : Jobless Claims + PCE (≥2 Jobless ET ≥1 PCE)
elif jobless_count >= 2 and pce_count >= 1:
    core_type = 'JOBLESS_PCE'
    # Tous les événements Jobless ET PCE sont core
    # Autres événements = pas core
```

---

## 🎯 IMPACT

### Avant
- Noyau dur trop large (tous les événements)
- Recherche de clusters similaires moins précise
- Risque de trouver des clusters non pertinents

### Après
- Noyau dur plus précis (4 événements au lieu de 6)
- Recherche de clusters similaires plus précise
- Meilleure identification des clusters historiques pertinents

---

## 📊 STATISTIQUES

**Dates historiques avec clusters JOBLESS_PCE** (14:20-14:40) :
- Total trouvé : 20 dates (2020-2025)
- Exemples : 2025-02-27, 2025-01-30, 2024-12-19, 2024-11-27, etc.

---

## ✅ VALIDATION

- ✅ Pattern JOBLESS_PCE détecté pour 2025-05-29
- ✅ Pattern JOBLESS_PCE détecté pour 2025-02-27 (historique)
- ✅ Jaccard similarity = 1.000 entre clusters similaires
- ✅ Core events identiques entre clusters similaires

---

**Status** : ✅ **IMPLÉMENTÉ ET VALIDÉ**




