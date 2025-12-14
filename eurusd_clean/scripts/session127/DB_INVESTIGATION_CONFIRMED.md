# RÉSULTATS INVESTIGATION DB RÉELLE
## Basé sur rapport audit Session 126

**Date :** 11 novembre 2025  
**Source :** audit_scores_mapping.txt (Session 126)

---

## ✅ EVENT_KEY RÉELS DANS LA DB (country='US')

### **UNEMPLOYMENT - EVENT_KEY TROUVÉS :**

**Dans Catégorie 1 (FOUND_EXACT) :**
```
event_key: 'unemployment rate'
  → importance: HIGH (3)
  → count: 25 événements
  → score CSV correspondant: 60.18
```

**Pas trouvé dans le rapport :**
- ❌ `u-6 unemployment rate`
- ❌ `u6 unemployment rate`  
- ❌ `underemployment rate`

**CONCLUSION :** Le score CSV `u_6_unemployment_rate` (63.96) n'a PAS de correspondance directe dans la DB.

---

### **GDP - EVENT_KEY TROUVÉS :**

**Dans Catégorie 2 (FOUND_VARIANTS) :**

Plusieurs event_key GDP trouvés avec variantes :

```
1. gdp_growth_rate (CSV score 38.52)
   → event_key: 'gdp growth rate_qoq' (21 événements HIGH)
   → event_key: 'gdp growth rate qoq adv' (7 événements HIGH)

2. gdp_sales (CSV score 38.06)
   → event_key: 'gdp sales_qoq' (20 événements HIGH)
   → event_key: 'gdp sales qoq adv' (7 événements HIGH)

3. gdp_price_index (CSV score 38.06)
   → event_key: 'gdp price index_qoq' (20 événements HIGH)
   → event_key: 'gdp price index qoq adv' (7 événements HIGH)
```

**Dans Catégorie 1 (FOUND_EXACT) :**
```
event_key: 'atlanta fed gdpnow'
  → importance: HIGH (3)
  → count: 7 événements
  → score CSV correspondant: 18.56
```

**Pas trouvé dans le rapport :**
- ❌ `gross domestic product` (exact)

**CONCLUSION :** Le score CSV `gross_domestic_product` (39.70) n'a PAS de correspondance EXACTE, mais plusieurs variantes GDP existent.

---

### **MORTGAGE RATE - EVENT_KEY TROUVÉS :**

**Dans Catégorie 1 (FOUND_EXACT) :**
```
event_key: 'mba 30-year mortgage rate'
  → importance: MED (2)
  → count: 94 événements
  → score CSV correspondant: 13.16 (mba_30_year_mortgage_rate)
```

**Pas trouvé dans le rapport :**
- ❌ `30-year mortgage rate` (sans préfixe MBA)
- ❌ `15-year mortgage rate`

**CONCLUSION :** Le score CSV `30_year_mortgage_rate` (13.84) correspond probablement à `mba 30-year mortgage rate` (score proche 13.16).

---

### **MONEY SUPPLY - EVENT_KEY TROUVÉS :**

**Dans Catégorie 1 (FOUND_EXACT) :**
```
event_key: 'money supply'
  → importance: MED (2)
  → count: 9 événements
  → score CSV correspondant: 10.41
```

**Pas trouvé dans le rapport :**
- ❌ `m2 money supply` (spécifique M2)

**CONCLUSION :** Le score CSV `m2_money_supply` (10.99) correspond probablement à `money supply` (score proche 10.41).

---

## 📊 SYNTHÈSE INVESTIGATION

### **SCORE 1 : u_6_unemployment_rate (63.96)** ❌

**Statut :** **INTROUVABLE dans DB**

**Event_key le plus proche :**
- `unemployment rate` (score 60.18, HIGH, 25 événements)

**Analyse :**
- U-6 = Taux chômage élargi BLS (inclut temps partiel involontaire)
- Statistique spécialisée non présente dans calendrier économique standard
- L'event_key `unemployment rate` (U-3 standard) est disponible

**Décision :**
- ✅ **IGNORER** `u_6_unemployment_rate` 
- ✅ **UTILISER** `unemployment_rate` à la place (60.18)
- Raison : U-3 standard suffit pour trading, U-6 trop spécialisé

---

### **SCORE 2 : gross_domestic_product (39.70)** ✅ DOUBLON

**Statut :** **DOUBLON de gdp_growth_rate**

**Event_key correspondant :**
- `gdp growth rate_qoq` (21 événements HIGH)

**Analyse :**
- Scores très proches : 39.70 vs 38.52
- Même donnée économique (croissance PIB)
- `gdp_growth_rate` déjà mappé en Phase 1.1

**Décision :**
- ✅ **MAPPER** `gross_domestic_product` → `gdp growth rate_qoq`
- Utiliser même event_key que `gdp_growth_rate`

---

### **SCORE 3 : 30_year_mortgage_rate (13.84)** ✅ TROUVÉ

**Statut :** **VARIANTE MBA trouvée**

**Event_key correspondant :**
- `mba 30-year mortgage rate` (94 événements MED)

**Analyse :**
- Scores proches : 13.84 vs 13.16
- Même donnée (taux mortgage 30 ans)
- MBA = Mortgage Bankers Association (source officielle)

**Décision :**
- ✅ **MAPPER** `30_year_mortgage_rate` → `mba 30-year mortgage rate`

---

### **SCORE 4 : m2_money_supply (10.99)** ✅ TROUVÉ

**Statut :** **VARIANTE SIMPLE trouvée**

**Event_key correspondant :**
- `money supply` (9 événements MED)

**Analyse :**
- Scores proches : 10.99 vs 10.41
- M2 = Agrégat monétaire spécifique
- DB a `money supply` générique

**Décision :**
- ✅ **MAPPER** `m2_money_supply` → `money supply`

---

## 🎯 DÉCISIONS FINALES

### **SCORES HIGH (2/2 résolus) :**

1. ✅ `u_6_unemployment_rate` → IGNORER (utiliser `unemployment_rate` à la place)
2. ✅ `gross_domestic_product` → MAPPER vers `gdp growth rate_qoq`

**Résultat :** ✅✅✅ **100% SCORES HIGH COUVERTS**

---

### **SCORES BONUS TROUVÉS (2/2) :**

3. ✅ `30_year_mortgage_rate` → MAPPER vers `mba 30-year mortgage rate`
4. ✅ `m2_money_supply` → MAPPER vers `money supply`

---

### **SCORES IGNORÉS (21) :**

- 15 auctions Treasury (MED/LOW)
- 1 mortgage 15 ans (MED)  
- 5 autres (LOW)

**Justification :** Effort élevé, impact trading modéré

---

## ✅ CONFIRMATION DÉCISIONS

**Les décisions prises en Phase 1.2 (avant investigation DB réelle) sont CONFIRMÉES :**

1. ✅ u_6 → IGNORER (correct, introuvable)
2. ✅ GDP → DOUBLON (correct, même event_key)
3. ✅ Mortgage 30y → TROUVÉ (correct, variante MBA)
4. ✅ M2 money → TROUVÉ (correct, variante simple)

**Impact :** Aucune modification nécessaire au mapping Phase 1.

---

**Auteur :** André Valentin avec Claude  
**Session :** 127  
**Phase :** 1.2 Investigation DB (validation)  
**Statut :** ✅ CONFIRMÉ
