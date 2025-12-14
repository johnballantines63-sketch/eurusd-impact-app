"""
NOTES SESSION 110 - CORRECTION PLANIFICATEUR V27
================================================

PROBLÈMES IDENTIFIÉS :
1. Query SQL filtre country='US' uniquement → Exclut EUR/DE événements
2. Query filtre score > 40 → Exclut Jobless Claims (score 27)
3. Pas d'UI de sélection avec checkboxes
4. Pas de champs pour renseigner "actual" si manquant

LOGIQUE CORRECTE (depuis 4_Planificateur_STABLE_0159_PERFECT.py) :

1. CHARGEMENT ÉVÉNEMENTS
   - Tous pays : US, EU, DE, FR, IT, ES, GB, NL, BE, AT, PT, IE, GR
   - Pas de filtre score (OU score > 20 minimum)
   - Fenêtre temporelle ±30 min
   - Group by pour éviter doublons

2. INTERFACE UTILISATEUR
   - Liste événements avec CHECKBOXES (sélection)
   - Afficher : Heure, Event, Country, Score, Previous, Forecast
   - Champ "Actual" SEULEMENT si :
     * Événement futur (temps réel)
     * OU actual manquant en DB
   - Si actual existe en DB → Utiliser directement (pas de re-saisie)

3. DOUBLE WAVE DETECTION
   - Détecter 2 CLUSTERS séparés de 10-20 min
   - Exemple 11.09.2025 :
     * Cluster 1 : 14:30 CPI+Jobless (US)
     * Cluster 2 : 14:45 Current Account (DE)
   - Pas juste 1 cluster avec conditions surprise/size

4. QUERY SQL CORRIGÉE
```sql
SELECT 
    e.ts_utc,
    e.event_key,
    e.country,
    MAX(COALESCE(e.event_title, e.event_key)) as label,
    MAX(e.actual) as actual,
    MAX(e.estimate) as estimate,
    MAX(e.forecast) as forecast,
    MAX(e.previous) as previous,
    MIN(ef.family) as family,
    AVG(ef.empirical_score) as empirical_score,
    AVG(ef.latency_median) as latency_median
FROM events e
INNER JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE DATE(e.ts_utc) = ?
    AND e.country IN ('US', 'EU', 'DE', 'FR', 'IT', 'ES', 'GB', 'NL', 'BE', 'AT', 'PT', 'IE', 'GR')
GROUP BY e.ts_utc, e.event_key, e.country
HAVING AVG(ef.empirical_score) > 20  -- Baisser seuil pour inclure Jobless
ORDER BY e.ts_utc
```

5. FORMATAGE NOMS
   - Utiliser format_event_name() pour affichage propre
   - "inflation_rate_yoy" → "Inflation Rate (YoY)"
   - "cpi s.a" → "CPI (s.a)"

ACTION IMMÉDIATE :
- Créer interface avec checkboxes
- Modifier query SQL
- Ajouter logique "actual" conditionnel
- Grouper par fenêtre temporelle (30 min)
"""
