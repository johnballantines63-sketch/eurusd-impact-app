# REF-002 : VÉRIFICATION SCORES EMPIRIQUES DEPUIS FINNHUB

**Référence :** REF-002  
**Date de création :** 2025-12-06  
**Heure de création :** 09:24:37  
**Auteur :** André Valentin avec Claude  
**Version :** 1.0

---

## 📋 OBJECTIF

Vérifier si les scores empiriques dans la table `event_families` ont été recalculés depuis l'intégration des données Finnhub, ou s'ils sont basés sur d'anciennes données (EODHD).

---

## 🔍 RÉSULTATS DE L'INVESTIGATION

### 1. État de la Table `event_families`

**Statistiques :**
- ✅ **Total entrées** : 1905
- ✅ **Scores présents** : 1905/1905 (100%)
- ✅ **Plage de scores** : 4.15 à 64.61
- ✅ **Score moyen** : 17.90
- ✅ **Score médian** : 15.71
- ✅ **Event keys uniques** : 1725
- ✅ **Pays uniques** : Multiple (US, EU, etc.)

**Structure de la table :**
- `event_key` : Clé de l'événement
- `country` : Pays
- `family` : Famille d'événement
- `empirical_score` : Score empirique (0-100)
- `avg_movement_pips` : Mouvement moyen en pips
- `sample_size` : Taille de l'échantillon
- `latency_median` : Latence médiane
- `ttr_median` : Time To Reversal médian
- `mfe_p80` : Maximum Favorable Excursion au 80e percentile

**Top 10 scores :**
1. Average Hourly Earnings MoM (US) : 64.61
2. Average Hourly Earnings YoY (US) : 64.61
3. Average Weekly Hours (US) : 64.61
4. Non Farm Payrolls (US) : 64.61
5. Nonfarm Payrolls Private (US) : 64.61
6. Participation Rate (US) : 64.61
7. U6 Unemployment Rate (US) : 63.90
8. Deposit Facility Rate (EU) : 63.26
9. ECB Interest Rate Decision (EU) : 63.26
10. Marginal Lending Rate (EU) : 63.26

---

### 2. État des Données Finnhub

**Table `events` (Finnhub) :**
- ✅ **Total événements US** : 29,846
- ✅ **Dates uniques** : Multiple
- ✅ **Dernier événement** : 2025-12-19 19:00:00+01:00
- ✅ **Couverture** : 2020-01-01 à 2025-12-19

**Table `prices_finnhub_m1` :**
- ✅ **Total bougies** : 3,604,556
- ✅ **Dates uniques** : 3,116
- ✅ **Couverture** : Données complètes disponibles

**Conclusion** : Les données Finnhub sont présentes et à jour.

---

### 3. Scripts de Recalcul Trouvés

**Scripts identifiés :** 16 scripts

**Scripts Session 123 (09 novembre 2025) :**
- `recalculate_empirical_scores_eodhd.py` : Recalcul basé sur EODHD
- `recalculate_empirical_scores_optimized.py` : Version optimisée (EODHD)
- `recalculate_by_periods.py` : Recalcul par tranches (EODHD)
- `recalculate_optimized.py` : Version optimisée (EODHD)
- `recalculate_scores_csv.py` : Export vers CSV (EODHD)

**⚠️ RÉSULTAT CRITIQUE :**
- ❌ **Aucun script de recalcul utilisant Finnhub trouvé**
- ✅ Tous les scripts trouvés utilisent **EODHD** ou autres sources
- ✅ Dernier recalcul documenté : **09 novembre 2025** (Session 123)

---

### 4. Test de Calcul depuis Finnhub

**Méthode :**
- Sélection : 5 événements CPI US (2020-01-14)
- Mesure impact depuis `prices_finnhub_m1` :
  - Baseline : OPEN première bougie après événement
  - Pic : HIGH maximum dans fenêtre 240 minutes
  - Impact = abs((peak_price - baseline_price) * 10000)

**Résultats :**
- **Moyenne impact** : 22.40 pips
- **Médiane impact** : 22.40 pips
- **P80 impact** : 22.40 pips

**Comparaison avec `event_families` :**
- **Score DB** : 11.21
- **Score calculé depuis Finnhub** : ~22.40 pips (moyenne)

**⚠️ ÉCART SIGNIFICATIF :**
- Différence : **11.19 pips** (score DB = 50% du score calculé)
- Cela suggère que les scores DB sont basés sur une **source différente** (EODHD ?)

---

## ✅ CONCLUSION

### Statut Actuel

**Les scores empiriques dans `event_families` :**
- ✅ Sont présents et complets (1905 entrées)
- ❌ **N'ONT PAS été recalculés depuis Finnhub**
- ✅ Sont basés sur **EODHD** ou une autre source (Session 123, 09 novembre 2025)
- ⚠️ **Ne correspondent pas** aux impacts mesurés depuis `prices_finnhub_m1`

### Preuves

1. **Aucun script Finnhub** : Aucun script de recalcul utilisant Finnhub trouvé
2. **Scripts EODHD** : Tous les scripts de recalcul utilisent EODHD
3. **Écart de calcul** : Score DB (11.21) vs Calculé Finnhub (22.40) = différence de 50%

---

## 📋 ACTIONS REQUISES

### Action Immédiate (Priorité HAUTE)

1. **⏳ À FAIRE** : Créer un script de recalcul des scores empiriques depuis Finnhub
   - Source : `events` (Finnhub) + `prices_finnhub_m1`
   - Méthode : Mesurer impact réel pour chaque événement historique
   - Formule : `empirical_score = (avg_movement * 0.5 + p80_movement * 0.5) * robustness`
   - Stockage : Mettre à jour `event_families`

2. **⏳ À FAIRE** : Valider la méthode de calcul
   - Comparer avec méthode EODHD actuelle
   - Vérifier cohérence des résultats
   - Documenter la nouvelle méthode

3. **⏳ À FAIRE** : Exécuter le recalcul
   - Période : 2020-01-01 à 2025-12-06
   - Événements : Tous les événements dans `events` (Finnhub)
   - Validation : Comparer avec scores actuels

### Actions Futures

1. Automatiser le recalcul périodique (mensuel ?)
2. Documenter la méthode de calcul dans REF-003
3. Créer un script de validation des scores recalculés

---

## 📊 IMPACT SUR LE PIPELINE

**Risque actuel :**
- Les scores empiriques utilisés par le pipeline peuvent être **imprécis**
- Basés sur EODHD au lieu de Finnhub (source actuelle)
- Peuvent causer des prédictions erronées

**Recommandation :**
- ⚠️ **URGENT** : Recalculer les scores depuis Finnhub avant de continuer les validations
- Les tests actuels peuvent être biaisés par des scores incorrects

---

## 📝 NOTES

- Cette investigation a été effectuée le 2025-12-06 02:15:00
- Script utilisé : `SESSION_VALIDATION_ACTUELLE/scripts/investigate_empirical_scores_finnhub.py`
- Prochaine étape : Créer script de recalcul (REF-003 ?)

---

**Fin du document REF-002**

