# 🚨 ERREUR #11 : TIMEZONE PRICES - CRITIQUE SESSION 85

**Date découverte :** 26 octobre 2025  
**Session :** 85  
**Priorité :** ⭐⭐⭐ CRITIQUE - IMPÉRATIF  
**Impact :** Bloque validation complète système

---

## ❌ ERREUR COMMISE

### Contexte

**Mission Session 85 :** Identifier source données prix MT5/Dukascopy montrant ~190 pips pour 01.08.2025 NFP.

**Problème identifié Session 84 :** Table `prices_1m` montre seulement 26 pips au lieu de ~190 pips.

### Ce Qui A Été Fait (INCORRECT)

**Claude Session 85 a :**

1. ✅ Créé scripts investigation DB (`investigate_db_simple.py`, `check_view.py`)
2. ✅ Exécuté investigation complète (22 tables analysées)
3. ❌ **CONCLU À TORT** que données 1m étaient incomplètes
4. ❌ **PROPOSÉ** d'utiliser `prices_5m` (158 pips) comme "meilleure approximation"
5. ❌ **IGNORÉ** information critique documentée : **PROBLÈME TIMEZONE**

### Résultats Investigation (Session 85)

**Données 01.08.2025 trouvées :**

| Table | Range | Conclusion Claude |
|-------|-------|-------------------|
| prices_1m | 19.5 pips | ❌ "Incomplet - données manquantes" |
| prices_5m | 158 pips | ✅ "Meilleure source disponible" |
| MT5 (image utilisateur) | ~195 pips | ✅ "Vérité terrain" |

**Proposition Claude :** Utiliser `prices_5m` avec résolution 5min.

---

## ⚠️ POURQUOI C'EST UNE ERREUR CRITIQUE

### 1. Information Déjà Documentée (3x)

**project_state_new.md contient EXPLICITEMENT :**

#### Erreur #6 (page ~60)
> **Database timezone handling is critical** - events are stored in UTC+2 (Bern time) while price data uses UTC, requiring careful 2-hour offset corrections.

#### Erreur #10 (page ~80)
> **Erreur #10 : Confusion importance_n vs empirical_score**  
> La colonne `ts_utc` est mal nommée - elle contient +02:00 (Bern time), pas UTC pur !

#### Section Timezone (page ~110)
> **Note critique :** Toujours vérifier timezone EXPLICITEMENT avec query test

### 2. Checklist Non Respectée

**MANDATORY_SESSION_RULES.md exige :**

```
- [ ] Lire `project_state_new.md` (ce fichier) ENTIÈREMENT
      Pas de survol, pas de lecture en diagonale
      Lire ligne par ligne les sections critiques
```

**Claude Session 85 a :**
- ✅ Lu project_state_new.md
- ❌ **PAS appliqué** les leçons timezone documentées
- ❌ **PAS vérifié** timezone avant conclusion

### 3. Preuve Utilisateur Ignorée

**L'utilisateur André a fourni graphique MT5 montrant :**
- Spike à **14:30** heure Bern (UTC+2)
- Départ : **1.13925**
- Peak : **~1.15875**
- Range : **~195 pips**

**Query Claude utilisait :**
```sql
WHERE datetime >= '2025-08-01 14:25:00'  -- Bern time
  AND datetime <= '2025-08-01 14:50:00'
```

**MAIS** colonne `datetime` a `+02:00` donc recherche décalée !

### 4. Conséquence Grave

**Si Session 85 avait continué sans correction :**
- ❌ Adaptation script pour `prices_5m` (résolution dégradée)
- ❌ Validation sur données 158 pips au lieu de vraies données
- ❌ Perte précision timing (5min vs 1min)
- ❌ **3-4 sessions supplémentaires** pour re-corriger
- ❌ **30-40k tokens gaspillés**

---

## ✅ CORRECTION APPLIQUÉE

### Intervention Utilisateur

**André a rappelé :**

> "toujours le même probleme de timezone price 1m stockée avec autre timezone que utc ?? problème documenté plusieurs fois dans project_state_new.md"

### Action Corrective Session 85

**Création de cette documentation (ERREUR_11) pour :**
1. ✅ Documenter erreur avec **priorité CRITIQUE**
2. ✅ Expliquer pourquoi c'est une erreur **RÉCURRENTE**
3. ✅ Établir **procédure obligatoire** timezone
4. ✅ Empêcher répétition futures sessions

---

## 🎯 RÈGLE IMPÉRATIVE TIMEZONE (NOUVELLE)

### ⚠️ OBLIGATION ABSOLUE - PRIORITÉ HAUTE

**AVANT TOUTE QUERY SUR TABLES PRIX, VOUS DEVEZ :**

#### Étape 1 : Vérifier Timezone Colonne

```sql
-- OBLIGATOIRE : Inspecter échantillon avec timezone
SELECT datetime, close 
FROM prices_1m 
LIMIT 3;

-- Exemple résultat :
--                  datetime   close
-- 2024-06-17 18:12:00+02:00 1.07308  ← Noter le +02:00 !
```

**Si vous voyez `+02:00` → Colonne en heure Bern (UTC+2)**  
**Si vous voyez rien → Colonne probablement UTC naïf**

#### Étape 2 : Adapter Query Selon Timezone

**Cas A : Colonne avec `+02:00` (Bern time)**

```sql
-- ✅ CORRECT : Utiliser heure Bern directement
SELECT * FROM prices_1m
WHERE datetime >= '2025-08-01 14:25:00+02:00'
  AND datetime <= '2025-08-01 14:50:00+02:00'
```

**Cas B : Colonne UTC naïf (vue `prices_1m_v`)**

```sql
-- ✅ CORRECT : Convertir événement Bern → UTC
-- Événement 14:30 Bern = 12:30 UTC
SELECT * FROM prices_1m_v
WHERE ts_utc >= '2025-08-01 12:25:00'  -- -2h
  AND ts_utc <= '2025-08-01 12:50:00'  -- -2h
```

#### Étape 3 : Valider avec Cas Connu

**TOUJOURS tester avec cas référence :**

```python
# Test 01.08.2025 14:30 Bern
# Doit trouver départ ~1.13925 (confirmé MT5)

result = query_prices(date='2025-08-01', time_bern='14:30')
assert result['close'].min() < 1.14000, "Spike initial manqué !"
```

#### Étape 4 : Documenter Timezone Utilisé

```python
def extract_real_prices(date, event_time_bern, window_minutes=60):
    """
    Extrait prix réels autour événement
    
    TIMEZONE : Événement en heure Bern (UTC+2)
    TABLE : prices_1m (colonne datetime avec +02:00)
    CONVERSION : Aucune (table déjà en Bern)
    
    Args:
        event_time_bern: Heure événement en Bern (ex: 14:30)
    """
```

---

## 🔑 CHECKLIST TIMEZONE (OBLIGATOIRE)

**AVANT toute analyse prix, vérifier :**

- [ ] **Échantillon inspecté** avec `LIMIT 3` pour voir timezone
- [ ] **Timezone documenté** dans commentaires code
- [ ] **Query adaptée** selon timezone colonne
- [ ] **Test cas connu** (01.08.2025 ou 11.09.2025)
- [ ] **Résultat cohérent** avec données MT5/Dukascopy

**Si UNE SEULE case non cochée → STOP et corriger**

---

## 📊 CAS RÉFÉRENCE TIMEZONE

### 01.08.2025 - NFP (Cas Test)

**Événement :**
- Heure Bern : **14:30** (UTC+2)
- Heure UTC : **12:30**

**Prix attendus (MT5) :**
- Départ 14:30 Bern : **1.13925**
- Peak : **~1.15875**
- Range : **~195 pips**

**Tables disponibles :**

| Table | Colonne | Timezone | Query |
|-------|---------|----------|-------|
| prices_1m | datetime | +02:00 Bern | `datetime >= '2025-08-01 14:30:00+02:00'` |
| prices_1m_v | ts_utc | UTC naïf | `ts_utc >= '2025-08-01 12:30:00'` |
| prices_5m | datetime | +02:00 Bern | `datetime >= '2025-08-01 14:30:00+02:00'` |

### 11.09.2025 - CPI (Cas Validé)

**Événement :**
- Heure Bern : **14:30** (UTC+2)  
- Heure UTC : **12:30**

**Prix validés (Session 81) :**
- Impact : **53 pips**
- Type : Double Wave

**Query correcte :**
```sql
WHERE datetime >= '2025-09-11 14:25:00+02:00'
```

---

## 💡 POURQUOI CETTE ERREUR EST RÉCURRENTE

### Facteurs Aggravants

1. **Nom trompeur** : `ts_utc` contient en fait +02:00
2. **Multiples tables** : `prices_1m` vs `prices_1m_v` (timezone différents)
3. **Documentation dispersée** : Erreur #6, #10, section timezone
4. **Lecture rapide** : Claude lit mais n'applique pas

### Pattern Échec Observé

```
Session X : 
1. Lit project_state_new.md ✅
2. Voit info timezone ✅
3. Commence investigation ✅
4. Oublie vérifier timezone ❌
5. Conclut données manquantes ❌
6. Utilisateur corrige ✅
```

**Ce pattern s'est répété 3 fois (Sessions 74, 84, 85) !**

---

## 🎯 SOLUTION PÉRENNE

### Modification project_state_new.md

**Ajouter section AVANT "Erreurs Récurrentes" :**

```markdown
## 🚨 RÈGLE IMPÉRATIVE #1 : TIMEZONE PRIX (PRIORITÉ ABSOLUE)

⚠️ **LIRE AVANT TOUTE QUERY PRIX** ⚠️

TOUTES les tables prix ont des timezones spécifiques :
- prices_1m.datetime : UTC+2 (Bern) avec +02:00
- prices_1m_v.ts_utc : UTC naïf (PAS de +02:00)
- prices_5m.datetime : UTC+2 (Bern) avec +02:00

PROCÉDURE OBLIGATOIRE :
1. Inspecter échantillon (LIMIT 3)
2. Noter timezone dans code
3. Adapter query selon timezone
4. Tester cas connu (01.08 ou 11.09)
5. Valider cohérence MT5

SI OUBLIÉ → 3-4 sessions perdues garanties ❌
```

### Checklist Session Modifiée

**MANDATORY_SESSION_RULES.md - Ajouter :**

```markdown
- [ ] **Timezone vérifié AVANT query prix**
  - Échantillon inspecté ?
  - Query adaptée ?
  - Test cas connu passé ?
```

---

## 📚 RÉFÉRENCES

**Fichiers à consulter :**
- `project_state_new.md` - Erreur #6, #10, section timezone
- `ERREUR_10_TIMEZONE_DB.md` - Documentation erreur précédente
- `ERREUR_11_TIMEZONE_PRICES_SESSION85.md` - Ce fichier

**Cas tests :**
- 01.08.2025 14:30 Bern : 1.13925 → 1.15875 (~195 pips)
- 11.09.2025 14:30 Bern : Impact 53 pips validé

**Scripts référence :**
- `validate_predictions_vs_reality.py` - À corriger avec timezone

---

## ✅ VALIDATION COMPRÉHENSION

**Pour confirmer lecture de ce document, répondre :**

1. Quelle timezone pour `prices_1m.datetime` ?
2. Quelle timezone pour `prices_1m_v.ts_utc` ?
3. Événement 14:30 Bern = quelle heure UTC ?
4. Quelle étape OBLIGATOIRE avant query prix ?
5. Quel prix départ attendu 01.08.2025 14:30 ?

**Réponses attendues :**
1. UTC+2 (Bern) avec +02:00
2. UTC naïf
3. 12:30 UTC
4. Inspecter échantillon timezone
5. ~1.13925

---

*Erreur documentée Session 85 - 26 octobre 2025*  
*Priorité : CRITIQUE ⭐⭐⭐*  
*Impact : Bloque validation système*  
*Action requise : Appliquer checklist timezone SYSTÉMATIQUEMENT*

**🔴 NE PLUS JAMAIS IGNORER CETTE RÈGLE 🔴**
