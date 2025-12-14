# 🚨 ERREUR #10 : TIMEZONE DB (CRITIQUE - SE RÉPÈTE 10+ SESSIONS)

**Ajout :** Session 77  
**Fréquence :** **10+ occurrences** (Sessions 20, 35, 45, 50, 56, 62, 68, 72, 74, 77)  
**Priorité :** 🔴🔴🔴 CRITIQUE

---

## ⚠️ PROBLÈME

**DB warehouse.duckdb stocke timestamps en UTC+2 (Berne time), PAS en UTC**

**Conséquence :** Query cherchant 12h30 UTC ne trouve RIEN → Scripts échouent

---

## 🔍 SYMPTÔMES

```sql
-- ❌ FAUX : Cherche 12h30 UTC
WHERE DATE(e.ts_utc) = '2025-09-11'
  AND strftime(e.ts_utc, '%H:%M') = '12:30'
-- Résultat : 0 événement trouvé ❌

-- ✅ CORRECT : Cherche 14h30 Berne (UTC+2)
WHERE DATE(e.ts_utc) = '2025-09-11'
  AND strftime(e.ts_utc, '%H:%M') = '14:30'
-- Résultat : 9 événements CPI US trouvés ✅
```

---

## ✅ SOLUTIONS VALIDÉES SESSION 77

### Solution 1 : Query Directe (Cas Connu)

**Usage :** Quand timestamp exact connu (ex: 11 septembre 14h30)

```python
# ✅ CORRECT
WHERE strftime(e.ts_utc, '%H:%M') = '14:30'

# Fallback décalage 1-2 min
WHERE strftime(e.ts_utc, '%H:%M') BETWEEN '14:28' AND '14:32'
```

### Solution 2 : Fenêtre Élargie

**Usage :** Timestamp approximatif

```python
# ✅ Fenêtre ±120 min (gère timezone)
start_time = dt - timedelta(minutes=120)
end_time = dt + timedelta(minutes=120)
```

**⚠️ Risque :** Capture événements non liés  
**Optimum :** ±15-30 min si timezone confirmée

---

## 📋 CHECKLIST OBLIGATOIRE

**AVANT toute query events :**

- [ ] DB = UTC+2 (Berne), PAS UTC
- [ ] NE PAS convertir -2h
- [ ] Tester sur 11 sept 14h30
- [ ] Vérifier ~9 événements CPI US
- [ ] Fenêtre : ±15-30 min optimal

---

## 🧪 CAS TEST RÉFÉRENCE

```python
# ✅ Query validation
query = """
SELECT e.event_title, e.ts_utc
FROM events e
WHERE DATE(e.ts_utc) = '2025-09-11'
  AND strftime(e.ts_utc, '%H:%M') = '14:30'
  AND e.country = 'US'
"""
# Attendu : 9-15 événements CPI US
```

---

## 🔧 SOLUTIONS PAR CONTEXTE

**Contexte A : Timestamp exact connu**
→ Query directe 14h30

**Contexte B : Dataset timezone mixte**
→ Fenêtre ±120-130 min

**Contexte C : Scan prix → événements**
→ Fenêtre ±30 min + filtres qualité

---

## 📊 HISTORIQUE (10+ occurrences)

S20, S35, S45, S50, S56, S62, S68, S72, S74, **S77**

**Fréquence :** ~1 session sur 8 🔴

---

## 🎯 RECOMMANDATIONS FUTURES

1. ✅ **Toujours tester sur 11 sept** avant déploiement
2. ✅ **Fenêtre ±15-30 min** (compromis optimal)
3. ✅ **Filtres qualité** : importance_n≥2, score>20
4. ❌ **Ne JAMAIS supposer UTC** standard

---

*Erreur documentée Session 77 - 25 octobre 2025*  
*À ajouter dans project_state_new.md section "ERREURS RÉCURRENTES"*
