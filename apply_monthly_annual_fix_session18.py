"""
SESSION 18 - FIX FINAL : DISTINGUER MONTHLY VS ANNUAL
Objectif : Enrichir event_key pour éviter écrasement des variantes
Auteur : Claude
Date : 19 octobre 2025

PROBLÈME :
- EODHD envoie Inflation Rate Monthly (0.4%) ET Annual (2.9%)
- Même event_key = 'inflation rate'
- L'upsert écrase le monthly par l'annual
- Résultat : On perd la surprise de 33%

SOLUTION :
Enrichir event_key avec suffixe _monthly ou _annual basé sur magnitude
"""

import shutil
from pathlib import Path
from datetime import datetime

# Backup
client_path = Path('fx_impact_app/src/eodhd_client.py')
backup_path = Path(f'fx_impact_app/src/eodhd_client_backup_final_{datetime.now().strftime("%Y%m%d_%H%M%S")}.py')

print("=" * 80)
print("🔧 FIX FINAL : DISTINGUER MONTHLY VS ANNUAL")
print("=" * 80)

# Faire backup
print(f"\n📦 Backup : {backup_path}")
shutil.copy(client_path, backup_path)
print("✅ Backup créé")

# Lire le fichier actuel
with open(client_path, 'r') as f:
    content = f.read()

# Fonction d'enrichissement à insérer
enrich_function = '''

def _enrich_event_key_with_period(df: pd.DataFrame) -> pd.DataFrame:
    """
    SESSION 18 - Enrichit event_key pour distinguer Monthly vs Annual.
    
    Pour Inflation Rate, CPI, GDP, etc. qui ont des variantes (monthly/annual),
    on ajoute un suffixe basé sur la magnitude des valeurs.
    
    Règle heuristique :
    - Si valeur moyenne > 2.0 → probablement Annual
    - Si valeur moyenne <= 2.0 → probablement Monthly
    
    Exemple :
    - Inflation Rate : 0.4% → inflation_rate_monthly
    - Inflation Rate : 2.9% → inflation_rate_annual
    """
    if df.empty:
        return df
    
    df = df.copy()
    
    # Événements concernés (ont souvent des variantes monthly/annual)
    pattern_keys = ['inflation', 'cpi', 'gdp', 'unemployment', 'retail']
    
    for idx, row in df.iterrows():
        event_key = str(row['event_key']).lower() if pd.notna(row['event_key']) else ''
        
        # Vérifier si c'est un type concerné
        if any(pattern in event_key for pattern in pattern_keys):
            # Calculer magnitude moyenne des valeurs disponibles
            values = []
            for col in ['actual', 'estimate', 'previous']:
                if pd.notna(row[col]) and row[col] != 0:
                    values.append(abs(row[col]))
            
            if values:
                avg_magnitude = sum(values) / len(values)
                
                # Règle heuristique : > 2.0 = annual
                if avg_magnitude > 2.0:
                    # Ne pas ajouter si déjà présent
                    if 'annual' not in event_key and 'yearly' not in event_key:
                        df.at[idx, 'event_key'] = event_key + '_annual'
                else:
                    # < 2.0 = monthly
                    if 'monthly' not in event_key and 'month' not in event_key:
                        df.at[idx, 'event_key'] = event_key + '_monthly'
    
    return df

'''

# Trouver où insérer la fonction (avant calendar_to_events_df)
insertion_point = content.find('def calendar_to_events_df')

if insertion_point == -1:
    print("❌ ERREUR : Fonction calendar_to_events_df non trouvée")
    exit(1)

# Insérer la fonction
new_content = content[:insertion_point] + enrich_function + content[insertion_point:]

# Ajouter l'appel dans calendar_to_events_df
# Trouver la ligne df = df.dropna(subset=["ts_utc"])
target_line = 'df = df.dropna(subset=["ts_utc"])'
replacement = target_line + '''
    
    # ✅ SESSION 18 : ENRICHISSEMENT EVENT_KEY (Monthly vs Annual)
    # Distingue les variantes pour éviter écrasement lors de l'upsert
    df = _enrich_event_key_with_period(df)'''

new_content = new_content.replace(target_line, replacement)

# Écrire le nouveau fichier
with open(client_path, 'w') as f:
    f.write(new_content)

print("\n✅ Fix appliqué avec succès !")
print("\n📝 Modifications :")
print("  1. Fonction _enrich_event_key_with_period() ajoutée")
print("  2. Appel ajouté dans calendar_to_events_df()")
print(f"  3. Backup sauvegardé : {backup_path.name}")

print("\n" + "=" * 80)
print("🧪 TEST DU FIX")
print("=" * 80)
print("""
Test rapide :

python -c "
from fx_impact_app.src.eodhd_client import fetch_calendar_json, calendar_to_events_df
data = fetch_calendar_json('2025-09-11', '2025-09-11', countries=['US'])
df = calendar_to_events_df(data)
inf = df[df['event_key'].str.contains('inflation', na=False)]
print('\\nInflation events:')
print(inf[['event_key', 'actual', 'estimate']])
"

Résultat attendu :
- inflation_rate_monthly : 0.4, 0.3
- inflation_rate_annual  : 2.9, 2.9
""")

print("\n" + "=" * 80)
print("📋 PROCHAINES ÉTAPES")
print("=" * 80)
print("""
1. Tester le fix (commande ci-dessus)
2. Si OK → Re-importer le 11 septembre :
   python fx_impact_app/scripts/ingest_eodhd_calendar.py \\
     --from 2025-09-11 --to 2025-09-11 --countries US

3. Vérifier dans DB :
   SELECT event_key, actual, estimate 
   FROM events 
   WHERE date(ts_utc) = '2025-09-11' 
     AND event_key LIKE '%inflation%'

4. Si les deux versions sont présentes → ✅ Succès !
""")

print("\n✅ Script terminé !")
print("=" * 80)
