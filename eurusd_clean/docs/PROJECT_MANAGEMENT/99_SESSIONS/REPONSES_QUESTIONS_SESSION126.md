# RÉPONSES QUESTIONS SESSION 126
## Clarifications Table, Event Keys, Mapping Country

**Date :** 10 novembre 2025  
**Pour :** Claude Session 126  
**De :** André + Claude Session 125

---

## ❓ QUESTION 1 : QUELLE TABLE UTILISER ?

### **RÉPONSE : TABLE `events` ✅**

**TOUJOURS utiliser table `events` (pas `economic_events`)**

### **Explication Confusion Session 125**

**Historique :**
- `economic_events` = Données EODHD (incomplet, 125,625 lignes)
- `events` = Données JBlanked + EODHD enrichi (complet, 26,480 lignes)

**Script `find_matching_clusters.py` ligne 89 :**
```python
df_events_all = conn.execute("""
    SELECT 
        datetime_utc,
        event_name,
        country,
        importance
    FROM economic_events  # ❌ ERREUR Session 125
```

**CORRECTION À FAIRE :**
```python
df_events_all = conn.execute("""
    SELECT 
        ts_utc as datetime_utc,
        event_key as event_name,
        country,
        importance_n
    FROM events  # ✅ CORRECT
    WHERE importance_n = 3  # HIGH seulement
```

### **Pourquoi `events` est MEILLEUR ?**

1. **Données complètes** : Inclut NFP, CPI, tous événements US HIGH
2. **Colonnes normalisées** : `ts_utc`, `event_key`, `importance_n`
3. **Validé Session 125** : Cross-validation NFP utilisait `events`

### **Action Session 126**

✅ **Utiliser UNIQUEMENT table `events`**  
❌ **Ne PAS utiliser `economic_events`**

---

## ❓ QUESTION 2 : EVENT_KEYS EXACTS RETAIL SALES + FED

### **MÉTHODE POUR TROUVER EVENT_KEYS**

```python
import duckdb

conn = duckdb.connect('warehouse.duckdb', read_only=True)

# 1. Chercher Retail Sales
query_retail = """
SELECT 
    event_key,
    COUNT(*) as count
FROM events
WHERE country = 'US'
  AND importance_n = 3
  AND event_key LIKE '%retail%'
  AND ts_utc >= '2023-01-01'
GROUP BY event_key
ORDER BY count DESC
"""

df_retail = conn.execute(query_retail).df()
print("Retail Sales event_keys :")
print(df_retail)

# 2. Chercher Fed Interest Rate
query_fed = """
SELECT 
    event_key,
    COUNT(*) as count
FROM events
WHERE country = 'US'
  AND importance_n = 3
  AND (event_key LIKE '%fed%' OR event_key LIKE '%interest%rate%')
  AND ts_utc >= '2023-01-01'
GROUP BY event_key
ORDER BY count DESC
"""

df_fed = conn.execute(query_fed).df()
print("\nFed Interest Rate event_keys :")
print(df_fed)

conn.close()
```

### **RÉPONSE PROBABLE (à confirmer par query ci-dessus)**

**Basé sur patterns Session 125 :**

**Retail Sales :**
```python
event_key = 'retail sales'  # OU 'retail_sales'
# Format : minuscules + espaces (pas underscores dans table events)
```

**Fed Interest Rate Decision :**
```python
event_key = 'fed interest rate decision'  # OU 'fomc interest rate decision'
# Format : minuscules + espaces
```

### **⚠️ IMPORTANT : Espaces vs Underscores**

**Table `events` :**
```
event_key = 'non farm payrolls'    # ESPACES
event_key = 'retail sales'          # ESPACES
```

**Fichier `event_families_eodhd_empirical.csv` :**
```
event_name = 'non_farm_payrolls'   # UNDERSCORES
event_name = 'retail_sales'         # UNDERSCORES
```

**Conversion :**
```python
def normalize_for_scores(event_key):
    """Convertir event_key (espaces) → event_name (underscores)"""
    return event_key.replace(' ', '_')

# Exemple
event_key_db = 'non farm payrolls'
event_name_scores = normalize_for_scores(event_key_db)
# → 'non_farm_payrolls'
```

### **Action Session 126**

1. ✅ **Exécuter query ci-dessus** pour confirmer event_keys exacts
2. ✅ **Utiliser event_keys avec ESPACES** pour requêtes DB
3. ✅ **Convertir en UNDERSCORES** pour mapping scores

---

## ❓ QUESTION 3 : MAPPING COUNTRY 'US' vs 'usd'

### **RÉPONSE : MAPPING SYSTÉMATIQUE REQUIS**

### **Le Problème**

**Table `events` :**
```sql
SELECT country FROM events WHERE country = 'US'
-- Résultat : 'US', 'GB', 'JP', 'CH', 'DE' (CODES PAYS, 2 lettres MAJUSCULES)
```

**Fichier `event_families_eodhd_empirical.csv` :**
```python
df_scores['country'].unique()
# Résultat : ['usd', 'gbp', 'jpy', 'chf', 'eur'] (CODES DEVISES, 3 lettres minuscules)
```

### **Solution : Fonction Mapping**

```python
def map_country_to_currency(country_code):
    """
    Convertir code PAYS (table events) → code DEVISE (scores CSV)
    
    Args:
        country_code: Code pays 2 lettres majuscules ('US', 'GB', etc.)
    
    Returns:
        Code devise 3 lettres minuscules ('usd', 'gbp', etc.)
    """
    mapping = {
        'US': 'usd',  # États-Unis → Dollar
        'GB': 'gbp',  # Royaume-Uni → Livre Sterling
        'JP': 'jpy',  # Japon → Yen
        'CH': 'chf',  # Suisse → Franc Suisse
        'DE': 'eur',  # Allemagne → Euro
        'FR': 'eur',  # France → Euro
        'IT': 'eur',  # Italie → Euro
        'ES': 'eur',  # Espagne → Euro
        'NL': 'eur',  # Pays-Bas → Euro
        'AU': 'aud',  # Australie → Dollar Australien
        'CA': 'cad',  # Canada → Dollar Canadien
        'NZ': 'nzd',  # Nouvelle-Zélande → Dollar Néo-Zélandais
    }
    
    return mapping.get(country_code, country_code.lower())
```

### **Usage dans Pipeline**

```python
# 1. Charger événements depuis DB (country='US')
df_events = conn.execute("""
    SELECT event_key, country FROM events WHERE country = 'US'
""").df()

# 2. Charger scores
df_scores = pd.read_csv('event_families_eodhd_empirical.csv')

# 3. Mapper événements + scores
df_events['currency'] = df_events['country'].apply(map_country_to_currency)
df_events['event_name'] = df_events['event_key'].str.replace(' ', '_')

# 4. Jointure
df_merged = df_events.merge(
    df_scores[['event_name', 'country', 'empirical_score']],
    left_on=['event_name', 'currency'],
    right_on=['event_name', 'country'],
    how='left'
)
```

### **Alternative : Jointure Directe**

```python
# Créer colonne currency dans df_events
df_events['currency'] = df_events['country'].map({
    'US': 'usd',
    'GB': 'gbp',
    'JP': 'jpy',
    'CH': 'chf'
})

# Normaliser event_key
df_events['event_name'] = df_events['event_key'].str.replace(' ', '_')

# Jointure
df_with_scores = df_events.merge(
    df_scores,
    left_on=['event_name', 'currency'],
    right_on=['event_name', 'country'],
    how='left',
    suffixes=('_db', '_score')
)
```

### **Action Session 126**

✅ **Créer fonction `map_country_to_currency()`**  
✅ **Appliquer systématiquement** avant jointure scores  
✅ **Tester** : 'US' → 'usd' doit trouver score NFP = 61.6

---

## ❓ QUESTION 4 : SCRIPTS SESSION 125 - ADAPTATION

### **ANALYSE `find_matching_clusters.py`**

**Structure actuelle (lignes approximatives) :**

```python
# Lignes 1-50 : Configuration + imports

# Lignes 50-120 : ÉTAPE 1 - Charger cas référence
with open(REF_CASE_PATH, 'r') as f:
    cas_reference = json.load(f)
ref_signature = ...

# Lignes 120-180 : ÉTAPE 2 - Charger TOUS événements HIGH
df_events_all = conn.execute("""
    SELECT * FROM economic_events  # ❌ À corriger
    WHERE importance = 'HIGH'
    ...
""").df()

# Lignes 180-250 : ÉTAPE 3 - Grouper par clusters temporels
df_events_all['cluster_key'] = ...
clusters_detected = []
for cluster_time, group in df_events_all.groupby('cluster_key'):
    ...

# Lignes 250-300 : ÉTAPE 4 - Comparer signatures
matching_clusters = []
for cluster in clusters_detected:
    if cluster['signature'] == ref_signature:
        matching_clusters.append(cluster)

# Lignes 300-400 : ÉTAPE 5 - Mesurer impacts réels
for match in matching_clusters:
    df_prices = conn.execute(...)
    impact = ...
```

### **RÉPONSE : SCRIPT FAIT TOUT, MAIS À ADAPTER**

**Ce que le script fait BIEN :**
1. ✅ Charge signature cas référence
2. ✅ Scanner DB historique complet
3. ✅ Groupe par fenêtres temporelles
4. ✅ Compare signatures
5. ✅ Mesure impacts

**Ce qui DOIT être changé :**

1. **Table : `economic_events` → `events`**
2. **Colonnes : Adapter noms colonnes**
3. **Paramétrable : Enlever dépendance cas référence fixe**

### **Architecture Pipeline Master (Recommandation)**

```python
# calibrate_universal_amplification.py

def find_matching_clusters(
    event_type: str,           # "CPI", "NFP", "Retail Sales"
    min_occurrences: int = 3,
    time_window_minutes: int = 5
) -> List[Dict]:
    """
    MODULE 1 : Trouve clusters identiques pour un type d'événement
    
    RÉUTILISE LOGIQUE find_matching_clusters.py MAIS :
    - Table `events` (pas economic_events)
    - Paramétré par event_type (pas cas référence fixe)
    - Retourne liste clusters avec impacts mesurés
    """
    
    # 1. Définir signature dynamiquement
    # (Au lieu de charger depuis cas référence fixe)
    
    # 2. Scanner DB events (pas economic_events)
    df_events = conn.execute("""
        SELECT 
            ts_utc,
            event_key,
            country,
            importance_n
        FROM events
        WHERE country = 'US'
          AND importance_n = 3
          AND ts_utc >= '2015-01-01'
        ORDER BY ts_utc
    """).df()
    
    # 3. Grouper par clusters (GARDER LOGIQUE Session 125)
    df_events['cluster_key'] = df_events['ts_utc'].dt.floor(f'{time_window_minutes*2}T')
    
    clusters_detected = []
    for cluster_time, group in df_events.groupby('cluster_key'):
        if len(group) < 2:
            continue
        
        signature = tuple(sorted([
            (row['event_key'], row['country']) 
            for _, row in group.iterrows()
        ]))
        
        clusters_detected.append({
            'cluster_time': cluster_time,
            'signature': signature,
            'events': group.to_dict('records')
        })
    
    # 4. Filtrer par event_type
    # Si event_type = "CPI" → garder clusters contenant CPI
    # Si event_type = "NFP" → garder clusters contenant NFP
    # etc.
    
    matching_clusters = []
    for cluster in clusters_detected:
        # Vérifier si cluster contient event_type
        cluster_events = [e[0] for e in cluster['signature']]
        
        if event_type.lower() in ' '.join(cluster_events).lower():
            matching_clusters.append(cluster)
    
    # 5. Mesurer impacts (GARDER LOGIQUE Session 125)
    for cluster in matching_clusters:
        impact = measure_impact(conn, cluster['cluster_time'])
        cluster['impact_measured'] = impact
    
    return matching_clusters


def measure_impact(conn, cluster_time, window_minutes=60):
    """
    RÉUTILISER EXACTEMENT logique find_matching_clusters.py lignes 300-350
    """
    # (Code existant Session 125)
    pass
```

### **Recommandation Session 126**

**Option A : Adapter `find_matching_clusters.py`** ⭐ RECOMMANDÉ
```python
# 1. Corriger table events
# 2. Paramétrer par event_type (enlever cas référence fixe)
# 3. Garder logique clustering (validée)
# 4. Garder logique mesure impact (validée)
```

**Option B : Créer nouveau script from scratch**
```python
# Plus long, risque bugs
# Mais architecture plus propre
```

### **Action Session 126**

✅ **Option A recommandée** : Adapter script existant  
✅ **Changements minimaux** :
1. Table `economic_events` → `events`
2. Colonnes `datetime_utc` → `ts_utc`, `importance` → `importance_n`
3. Paramètre `event_type` au lieu de cas référence fixe
4. Mapping country → currency pour scores

---

## 📋 RÉSUMÉ RÉPONSES

| Question | Réponse | Action |
|----------|---------|--------|
| **1. Table ?** | `events` ✅ | Corriger find_matching_clusters.py ligne 89 |
| **2. Event keys ?** | Exécuter query exploration | Query fournie ci-dessus |
| **3. Mapping country ?** | 'US' → 'usd' | Fonction map_country_to_currency() |
| **4. Scripts ?** | Adapter existant | Option A recommandée |

---

## 🔧 SCRIPT QUERY EVENT_KEYS (À EXÉCUTER IMMÉDIATEMENT)

```python
#!/usr/bin/env python3
"""
Trouver event_keys exacts pour Retail Sales + Fed
"""
import duckdb
from pathlib import Path

DB_PATH = Path(__file__).parents[2] / "data" / "warehouse.duckdb"

conn = duckdb.connect(str(DB_PATH), read_only=True)

print("="*80)
print("RECHERCHE EVENT_KEYS : RETAIL SALES + FED")
print("="*80)
print()

# 1. Retail Sales
print("🔍 RETAIL SALES :")
print()

query_retail = """
SELECT 
    event_key,
    COUNT(*) as count
FROM events
WHERE country = 'US'
  AND importance_n = 3
  AND event_key LIKE '%retail%'
  AND ts_utc >= '2023-01-01'
GROUP BY event_key
ORDER BY count DESC
"""

df_retail = conn.execute(query_retail).df()

if len(df_retail) > 0:
    for idx, row in df_retail.iterrows():
        print(f"   {row['count']:3d}× '{row['event_key']}'")
    print()
    print(f"✅ EVENT_KEY RETAIL SALES : '{df_retail.iloc[0]['event_key']}'")
else:
    print("   ⚠️ Aucun event_key trouvé")

print()

# 2. Fed Interest Rate
print("🔍 FED INTEREST RATE DECISION :")
print()

query_fed = """
SELECT 
    event_key,
    COUNT(*) as count
FROM events
WHERE country = 'US'
  AND importance_n = 3
  AND (
    event_key LIKE '%fed%interest%rate%' 
    OR event_key LIKE '%fomc%'
    OR event_key LIKE '%interest%rate%decision%'
  )
  AND ts_utc >= '2023-01-01'
GROUP BY event_key
ORDER BY count DESC
LIMIT 10
"""

df_fed = conn.execute(query_fed).df()

if len(df_fed) > 0:
    for idx, row in df_fed.iterrows():
        print(f"   {row['count']:3d}× '{row['event_key']}'")
    print()
    print(f"✅ EVENT_KEY FED : '{df_fed.iloc[0]['event_key']}'")
else:
    print("   ⚠️ Aucun event_key trouvé")

conn.close()

print()
print("="*80)
print("COPIER LES EVENT_KEYS DANS VOTRE CODE")
print("="*80)
```

**Exécuter :**
```bash
python find_event_keys.py
```

---

## ✅ CHECKLIST SESSION 126

Avant de commencer développement :

- [ ] Table `events` confirmée (pas economic_events)
- [ ] Event_keys Retail Sales + Fed identifiés (query exécutée)
- [ ] Fonction `map_country_to_currency()` créée
- [ ] Stratégie adaptation scripts décidée (Option A ou B)
- [ ] Scripts Session 125 chargés et compris

---

**Auteur :** André + Claude Session 125  
**Pour :** Claude Session 126  
**Date :** 10 novembre 2025  
**Statut :** ✅ RÉPONSES COMPLÈTES
