# 🧠 COMPRÉHENSION DU CALCUL D'IMPACT - SESSION 8

**Date :** 17 octobre 2025  
**Après lecture attentive des fichiers sources**

---

## 📚 FICHIERS ANALYSÉS

1. ✅ `calculate_real_impacts.py` - Script Session 7 (calcul individuel)
2. ✅ `sequence_multi_event_timeline_v86.py` - Logique vectorielle existante
3. ✅ `KNOWLEDGE_BASE.md` - Documentation erreurs
4. ✅ `ADDENDUM_CRITIQUE_SESSION7.md` - Problème identifié

---

## 🔍 COMMENT LE SCRIPT ACTUEL CALCULE L'IMPACT

### Fonction `calculate_event_impact()` dans `calculate_real_impacts.py`

**Étapes du calcul :**

```python
def calculate_event_impact(event_ts, prices_df, lookback_minutes=30, lookforward_minutes=60):
    """
    1. Prix de référence : 5 minutes AVANT l'événement
    2. Prix après : De T0 à T+60 minutes
    3. Calcul des mouvements : (prix - référence) / 0.0001 = pips
    4. MFE : MAX(mouvement UP, mouvement DOWN) en valeur absolue
    5. Direction : 'bullish' si UP > DOWN, sinon 'bearish'
    6. MAE : Mouvement dans la direction opposée
    7. TTR : Temps pour revenir à ±3 pips du prix de référence
    """
```

### ⚠️ LE PROBLÈME IDENTIFIÉ

**Pour le 11 septembre 2025 à 14:30 (33 événements simultanés) :**

Le script crée **33 lignes séparées**, toutes avec :
- Même fenêtre temporelle (14:30 → 15:30)
- Même prix de référence (14:25)
- Même MFE calculé : **59.2 pips**

**Pourquoi c'est incorrect :**
- Les 33 événements ne causent PAS 33 mouvements de 59.2 pips chacun
- Ils causent UN SEUL mouvement de marché combiné
- Le script compte 33 fois le même mouvement !

---

## 🎯 CE QUE RÉVÈLENT NOS MESURES MT5

### Comparaison : Script vs Réalité terrain

| Métrique | Script (59.2 pips) | MT5 Réel | Écart |
|----------|-------------------|----------|-------|
| **MFE Phase 1** | 59.2 pips | **111.5 pips** | x1.88 |
| **Nombre de lignes** | 33 (dupliquées) | 1 (groupée) | - |
| **Range total** | Non calculé | 111.5 pips | - |
| **Impact vectoriel** | Non calculé | 198.4 pips | - |

### 🔬 Détail du mouvement réel (MT5)

```
14:29 Pré-événement : 1.16810
14:30 Spike bas    : 1.16075  (-73.5 pips MAE)
14:35 Pic haut     : 1.17190  (+111.5 pips MFE depuis bas)
                              (+38.0 pips MFE depuis pré-événement)
```

**Question :** Pourquoi le script calculait 59.2 pips ?

**Hypothèse :** Le script mesurait probablement le MFE depuis le prix de référence (14:25) dans une fenêtre de 60 minutes, mais :
- Ne capturait peut-être pas le vrai pic à 1.17190
- Ou utilisait un prix de référence différent
- Ou la fenêtre de 60 min ne couvrait pas tout le mouvement

---

## 🧮 DIFFÉRENTES MÉTRIQUES D'IMPACT POSSIBLES

### Métrique 1 : MFE Absolu (depuis point d'entrée)
```
Impact = Prix_Max - Prix_Référence
Pour 11 sept : 1.17190 - 1.16810 = 38.0 pips UP
```
**Utilité :** Profit maximum possible pour un trader entrant au bon moment

### Métrique 2 : Range Total (amplitude du mouvement)
```
Impact = Prix_Max - Prix_Min
Pour 11 sept : 1.17190 - 1.16075 = 111.5 pips
```
**Utilité :** Mesure la violence totale du mouvement, indépendamment du point d'entrée

### Métrique 3 : Impact Net (résultat final)
```
Impact = Prix_Fin - Prix_Début
Pour 11 sept Phase 1 : 1.17190 - 1.16810 = 38.0 pips UP
Pour 11 sept Total   : 1.16529 - 1.16810 = -28.1 pips DOWN
```
**Utilité :** Direction finale du marché

### Métrique 4 : Impact Vectoriel (somme absolue)
```
Impact = |MFE_DOWN| + |MFE_UP| + |MFE_Phase2|
Pour 11 sept : 73.5 + 111.5 + 13.4 = 198.4 pips
```
**Utilité :** Volatilité totale (tous mouvements)

---

## 💡 COMPRÉHENSION DE LA LOGIQUE VECTORIELLE

### Dans `sequence_multi_event_timeline_v86.py`

Ce fichier gère **correctement** les événements multiples :

**Principe :**
1. **Grouper** les événements simultanés en phases
2. **Calculer** l'impact combiné de chaque phase
3. **Appliquer** séquentiellement chaque phase
4. **Gérer** le pullback entre phases rapprochées

**Exemple 11 septembre :**
```python
Phase 1 (14:30) :
  - 33 événements simultanés
  - Impact combiné = UN SEUL impact calculé
  - Durée : 5 minutes
  - MFE : 111.5 pips (range)

Pullback (14:35-14:45) :
  - 10 minutes de consolidation
  - Pullback : 28 pips (empirique)

Phase 2 (14:45) :
  - 1 événement (Current Account)
  - Impact : 13.4 pips
  - Durée : 5 minutes
```

**Formule pullback (v8.6.6) :**
```python
pullback_pct = 4% par minute
pullback_pips = phase1_impact × min(0.04 × minutes, 0.50)
```

---

## 🎯 CE QU'IL FAUT CORRIGER

### Problème principal

**`calculate_real_impacts.py` traite les événements INDIVIDUELLEMENT**

```python
# ❌ ACTUEL (INCORRECT)
for event in events:
    impact = calculate_event_impact(event.ts_utc, prices_df)
    # Résultat : 33 lignes avec le même MFE

# ✅ CORRECT
events_by_minute = events.groupby(pd.Grouper(key='ts_utc', freq='1min'))
for time_group, group_events in events_by_minute:
    impact = calculate_group_impact(time_group, prices_df)
    # Résultat : 1 ligne par groupe temporel
```

### Nouvelle approche recommandée

**Créer :** `calculate_grouped_impacts.py`

**Logique :**
1. **Grouper** événements par minute (time_group)
2. **Calculer UN impact** par groupe temporel
3. **Identifier** les phases successives (gap > 5 min)
4. **Appliquer** le pullback entre phases
5. **Stocker** l'impact avec la liste des événements du groupe

---

## 📊 QUELLE MÉTRIQUE UTILISER ?

### Recommandation : RANGE par Phase

**Pourquoi ?**
- ✅ Mesure la violence totale du mouvement
- ✅ Indépendant du point d'entrée exact
- ✅ Capture toute l'amplitude (spike + rebond)
- ✅ Comparable entre différents événements
- ✅ Correspond à l'observation terrain MT5

**Calcul :**
```python
def calculate_group_impact(time_group, prices_df, lookforward_minutes=60):
    """
    Pour un groupe d'événements simultanés à time_group :
    
    1. Prix de référence : 5 min avant time_group
    2. Fenêtre d'observation : time_group + 0 à +lookforward_minutes
    3. Prix_Max = max(prix dans fenêtre)
    4. Prix_Min = min(prix dans fenêtre)
    5. Range = Prix_Max - Prix_Min  (en pips)
    6. Direction = 'UP' si (Prix_Final - Prix_Ref) > 0 else 'DOWN'
    
    Return : {
        'mfe_pips': Range en pips,
        'direction': 'UP' ou 'DOWN',
        'mae_pips': Mouvement adverse max,
        'ttr_minutes': Temps retour à référence
    }
    """
```

**Alternative : MFE Absolu**

Si tu préfères mesurer le gain maximum possible :
```python
MFE = max(|Prix_Max - Prix_Ref|, |Prix_Min - Prix_Ref|)
```

---

## 🔄 STRUCTURE DE DONNÉES RECOMMANDÉE

### Table `event_group_impacts`

```sql
CREATE TABLE event_group_impacts (
    time_group TIMESTAMP PRIMARY KEY,  -- Minute du groupe (14:30:00)
    num_events INTEGER,                -- Nombre d'événements simultanés
    event_keys TEXT,                   -- Liste des event_keys (séparés par virgule)
    max_empirical_score REAL,          -- Score max du groupe
    mean_empirical_score REAL,         -- Score moyen du groupe
    countries TEXT,                    -- Pays impliqués
    
    -- Impacts calculés
    mfe_pips REAL,                     -- Range ou MFE absolu
    mae_pips REAL,                     -- Maximum Adverse Excursion
    ttr_minutes REAL,                  -- Time To Revert
    direction TEXT,                    -- 'UP' ou 'DOWN'
    
    -- Prix de référence
    reference_price REAL,              -- Prix 5 min avant
    peak_price REAL,                   -- Prix au pic (max ou min)
    peak_time TIMESTAMP,               -- Timestamp du pic
    
    -- Métadonnées
    lookforward_window INTEGER,        -- Fenêtre utilisée (60 min)
    calculation_date TIMESTAMP         -- Date du calcul
);
```

---

## 🚀 PROCHAINES ÉTAPES

### 1. Décision métrique (URGENT)
- [ ] Choisir entre Range Total ou MFE Absolu
- [ ] Valider avec quelques exemples manuels MT5

### 2. Créer le nouveau script
- [ ] `calculate_grouped_impacts.py`
- [ ] Implémenter la logique de groupement
- [ ] Gérer les phases successives

### 3. Validation
- [ ] Tester sur 11 septembre 2025
- [ ] Vérifier : 1 ligne pour 14:30 (pas 33)
- [ ] Comparer impact calculé vs MT5

### 4. Ré-analyse
- [ ] Relancer analyse de corrélation
- [ ] Générer nouvelle formule v9
- [ ] Valider précision améliorée

---

## ❓ QUESTIONS EN SUSPENS

### Question 1 : Fenêtre temporelle
**Actuel :** 60 minutes forward  
**Suffisant ?** Le 11 sept montre un pic à 14:35 (5 min), mais des mouvements jusqu'à 15:00+

**Recommandation :** Garder 60 minutes, mais documenter si pic atteint avant

### Question 2 : Prix de référence
**Actuel :** 5 minutes avant l'événement  
**Alternative :** Prix à T-1 minute (plus proche)

**Recommandation :** Garder 5 minutes (évite le spread de la news juste avant)

### Question 3 : Pullback entre phases
**Le calculer automatiquement ?**  
**Ou le stocker séparément ?**

**Recommandation :** Stocker séparément pour chaque phase, ne pas mélanger dans le MFE

---

**FIN DU DOCUMENT DE COMPRÉHENSION**

**Statut :** ✅ Compréhension complète  
**Prochaine action :** Décision sur métrique + création script  
**Version :** 1.0

---

## 📝 SYNTHÈSE POUR L'UTILISATEUR

**Ce que j'ai compris :**

1. Le script actuel calcule le MFE **individuellement** pour chaque événement
2. Pour 33 événements simultanés, il crée 33 lignes avec le **même MFE**
3. Nos mesures MT5 montrent un **range de 111.5 pips** (pas 59.2)
4. Le fichier `sequence_multi_event_timeline_v86.py` a déjà la **bonne logique vectorielle**
5. Il faut créer un nouveau script qui **groupe par minute** et calcule **UN impact par groupe**

**Ma recommandation :**
- Utiliser le **RANGE TOTAL** comme métrique d'impact (111.5 pips pour le 11 sept)
- Créer `calculate_grouped_impacts.py` qui groupe les événements simultanés
- Tester sur plusieurs dates pour validation
