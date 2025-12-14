# 📅 DATES DISPONIBLES - PLANIFICATEUR V2

**Dernière mise à jour :** 26 octobre 2025 - Session 82  
**Source :** warehouse.duckdb (58,449 événements)  
**Critères :** HIGH IMPACT US events avec empirical_score > 40

---

## 🎯 DATES VALIDÉES

Ces dates ont été testées et validées dans le planificateur :

| Date | Événements | Type | Impact Prédit | Status | Session |
|------|------------|------|---------------|--------|---------|
| **11.09.2025** | 11 CPI | Double Wave | 57 pips | ✅ Validé | S81 |
| **12.02.2025** | 8 CPI | Single Wave Fort | ~45 pips | ✅ Validé | S81 |

---

## 🔥 DATES PRIORITAIRES À TESTER

### 01.08.2025 - NFP Extrême ⭐⭐⭐

**Type :** NFP + Construction Spending  
**Événements HIGH IMPACT US :** 17 (cas extrême !)  
**Importance :** CRITIQUE

**Pourquoi tester :**
- Plus grand nombre d'événements HIGH IMPACT dans la DB
- Test robustesse formules sur cas extrême
- NFP = événement majeur marché (emploi US)
- Valide performance calcul (17 événements simultanés)

**Attendu :**
- Type mouvement : Double Wave (surprise élevée)
- Impact : > 60 pips
- TTR : 8-12 minutes
- Pullback : ~15-20 pips

---

### 10.04.2024 - CPI Historique ⭐⭐

**Type :** CPI US  
**Événements HIGH IMPACT US :** 10  
**Importance :** ÉLEVÉE

**Pourquoi tester :**
- Date 2024 (valide données historiques)
- Nombre moyen d'événements
- Test stabilité sur année précédente

**Attendu :**
- Type mouvement : Single Wave Fort ou Double Wave
- Impact : 45-55 pips
- Performance : Normale

---

### 18.12.2024 - Interest Rates ⭐⭐

**Type :** Fed/BCE Interest Rate Decisions  
**Événements HIGH IMPACT US :** 13  
**Importance :** TRÈS ÉLEVÉE

**Pourquoi tester :**
- Famille événements différente (pas CPI/NFP)
- Décisions taux = impact majeur marché
- Test détection automatique type mouvement

**Attendu :**
- Type mouvement : Double Wave (taux = haute volatilité)
- Impact : > 50 pips
- Surprise potentiellement élevée

---

## 📊 DATES PAR CATÉGORIE

### 🔴 Impact TRÈS ÉLEVÉ (10+ événements)

Dates avec 10 événements HIGH IMPACT US ou plus :

- **01.08.2025** - 17 événements (NFP extrême) ⭐⭐⭐
- **18.12.2024** - 13 événements (Interest Rates)
- **11.09.2025** - 11 événements (CPI) ✅ Validé
- **10.04.2024** - 10 événements (CPI)

### 🟡 Impact ÉLEVÉ (6-9 événements)

Dates avec 6-9 événements HIGH IMPACT US :

- **12.02.2025** - 8 événements (CPI) ✅ Validé
- D'autres dates à identifier via script `list_available_dates.py`

### 🟢 Impact MODÉRÉ (3-5 événements)

Dates avec 3-5 événements HIGH IMPACT US :

- À identifier via script `list_available_dates.py`

### ⚪ Impact FAIBLE (1-2 événements)

Dates avec 1-2 événements HIGH IMPACT US :

- À identifier via script `list_available_dates.py`
- Utiles pour tester cas simples

---

## 🗓️ CALENDRIER ÉCONOMIQUE US

### Événements Récurrents Majeurs

**CPI (Consumer Price Index) - Inflation**
- Fréquence : Mensuel
- Date typique : 10-15 du mois
- Impact : TRÈS ÉLEVÉ
- Exemple : 11.09.2025, 12.02.2025, 10.04.2024

**NFP (Non-Farm Payrolls) - Emploi**
- Fréquence : Mensuel
- Date typique : Premier vendredi du mois
- Impact : EXTRÊME
- Exemple : 01.08.2025

**Fed Interest Rate Decision - Taux directeurs**
- Fréquence : ~8 fois/an (FOMC meetings)
- Date typique : Mercredi mi-mois (calendrier Fed)
- Impact : EXTRÊME
- Exemple : 18.12.2024

**Jobless Claims - Demandeurs d'emploi**
- Fréquence : Hebdomadaire (jeudi)
- Impact : MOYEN à ÉLEVÉ
- Souvent combiné avec autres événements

**GDP (Gross Domestic Product) - PIB**
- Fréquence : Trimestriel
- Impact : TRÈS ÉLEVÉ
- Advance, Preliminary, Final releases

**Retail Sales - Ventes détail**
- Fréquence : Mensuel
- Date typique : Mi-mois
- Impact : ÉLEVÉ

---

## 🔍 COMMENT IDENTIFIER UNE BONNE DATE

### Critères Date Test Idéale

✅ **HIGH IMPACT US events ≥ 5**
- Plus d'événements = test plus significatif
- Valide somme vectorielle multi-événements

✅ **empirical_score > 40**
- Score élevé = impact marché confirmé historiquement
- Filtré automatiquement par planificateur

✅ **Période récente (2024-2025)**
- Données plus fiables
- Contexte marché actuel

✅ **Familles événements diverses**
- CPI (inflation)
- NFP (emploi)
- Interest Rates (taux)
- GDP (croissance)

### Dates à Éviter

❌ **Événements LOW/MEDIUM importance**
- Impact trop faible pour validation
- Pas dans la DB du planificateur

❌ **Dates sans surprise**
- actual = forecast
- Pas de mouvement significatif

❌ **Événements isolés uniques**
- Préférer clusters multi-événements
- Valide mieux les formules

---

## 🛠️ OUTILS DISPONIBLES

### Script : list_available_dates.py

**Chemin :**
```
eurusd_clean/scripts/session82/list_available_dates.py
```

**Usage :**
```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC
python3 eurusd_clean/scripts/session82/list_available_dates.py
```

**Output :**
- Top 50 dates disponibles
- Statistiques globales
- Distribution par nombre d'événements
- Recommandations dates tests

**Export CSV :**
```
eurusd_clean/scripts/session82/dates_disponibles.csv
```

---

## 📈 PATTERN DATES FORTES

### CPI Dates (Inflation)

**Pattern :** 10-15 du mois
**Exemples :**
- 11.09.2025 ✅
- 12.02.2025 ✅
- 10.04.2024 ⏳
- 13.11.2024
- 11.10.2024

**Caractéristiques :**
- Cluster 8-12 événements simultanés
- Surprise fréquente > 10%
- Double Wave probable

### NFP Dates (Emploi)

**Pattern :** Premier vendredi du mois
**Exemples :**
- 01.08.2025 ⏳
- 07.06.2024
- 03.05.2024
- 05.04.2024

**Caractéristiques :**
- 12-17 événements (NFP + Jobless + autres)
- Surprise extrême possible
- Impact maximum EUR/USD

### Fed Dates (Taux)

**Pattern :** 8 FOMC meetings/an
**Exemples :**
- 18.12.2024 ⏳
- 31.07.2024
- 12.06.2024
- 01.05.2024

**Caractéristiques :**
- 10-15 événements (décision + conférence presse)
- Volatilité extrême
- Double Wave systématique

---

## 🎯 PLAN TEST RECOMMANDÉ SESSION 82

### Phase 1 : Dates Prioritaires (CRITIQUE)

1. ✅ **11.09.2025** - Re-test stabilité
2. ✅ **12.02.2025** - Re-test stabilité
3. ⏳ **01.08.2025** - NFP extrême (PRIORITÉ ABSOLUE)

### Phase 2 : Validation Diverse (IMPORTANT)

4. ⏳ **10.04.2024** - CPI historique 2024
5. ⏳ **18.12.2024** - Interest Rates

### Phase 3 : Tests Additionnels (OPTIONNEL)

6. ⏳ Une date faible impact (2-3 événements)
7. ⏳ Une date moyen impact (5-6 événements)

**Total recommandé :** 5-7 dates pour validation exhaustive

---

## 📝 NOTES IMPORTANTES

### Timezone

**Base de données : UTC+2 (Berne time)**
- Tous les ts_utc sont en Berne time
- Ne PAS convertir (correction déjà appliquée)

### Filtres Planificateur

**Appliqués automatiquement :**
- `country = 'US'` (événements US uniquement)
- `importance = 'HIGH'` (haute importance)
- `empirical_score > 40` (impact historique confirmé)

### Formules Utilisées

**Validées Sessions 51-55 :**
- calculate_adjusted_empirical_score() - 99.9% précision
- calculate_impact_d() - 98.6% précision
- calculate_ttr_c() - 94.4% précision
- calculate_pullback_v2() - 99.3% précision

**Facteur correction vectoriel :** 0.758

---

## 🔗 RÉFÉRENCES

**Documentation :**
- `GUIDE_TEST_PLANIFICATEUR_SESSION82.md` - Mode d'emploi tests
- `SESSION81_RAPPORT_COMPLET.md` - Heisenbug résolu
- `project_state_new.md` - État projet global

**Scripts :**
- `list_available_dates.py` - Lister dates DB
- `test_planificateur_multi_dates.py` - Tests automatiques

**Planificateur :**
```
fx_impact_app/streamlit_app/pages/5_Planificateur_V2_FORMULES_VALIDEES_backup_session_72_copie.py
```

---

*Guide créé Session 82 - 26 octobre 2025*  
*Source : warehouse.duckdb (58,449 événements)*  
*Critères : HIGH IMPACT US + empirical_score > 40*
