"""
SESSION 18 - APPLICATION AUTOMATIQUE DU FIX DÉDUPLICATION
Objectif : Modifier eodhd_client.py automatiquement
Auteur : Claude
Date : 19 octobre 2025
"""

import shutil
from pathlib import Path
from datetime import datetime

# Backup
client_path = Path('fx_impact_app/src/eodhd_client.py')
backup_path = Path(f'fx_impact_app/src/eodhd_client_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.py')

print("=" * 80)
print("🔧 APPLICATION FIX DÉDUPLICATION MENSUEL/ANNUEL")
print("=" * 80)

# Faire backup
print(f"\n📦 Backup : {backup_path}")
shutil.copy(client_path, backup_path)
print("✅ Backup créé")

# Lire le fichier actuel
with open(client_path, 'r') as f:
    content = f.read()

# Fonction de déduplication à insérer
dedup_function = '''

def _deduplicate_by_surprise(df: pd.DataFrame) -> pd.DataFrame:
    """
    SESSION 18 - Déduplique les événements identiques (même pays, event_key, heure).
    Privilégie la version avec la surprise la plus élevée.
    
    Cas d'usage : EODHD retourne Inflation Rate (Monthly) ET (Annual) à la même heure.
    On garde la version Monthly (surprise plus élevée = données plus utiles).
    """
    if df.empty:
        return df
    
    # Calculer la surprise pour chaque ligne
    df = df.copy()
    df['_surprise_abs'] = 0.0
    
    valid_mask = (df['estimate'].notna()) & (df['estimate'] != 0) & (df['actual'].notna())
    
    if valid_mask.any():
        df.loc[valid_mask, '_surprise_abs'] = abs(
            (df.loc[valid_mask, 'actual'] - df.loc[valid_mask, 'estimate']) / 
            df.loc[valid_mask, 'estimate']
        )
    
    # Arrondir ts_utc à la minute pour grouper
    df['_time_group'] = df['ts_utc'].dt.floor('1min')
    
    # Grouper par (country, event_key, time_group)
    grouped = df.groupby(['country', 'event_key', '_time_group'], dropna=False)
    
    # Pour chaque groupe, garder la ligne avec la surprise max
    def keep_best(group):
        if len(group) == 1:
            return group
        # Trier par surprise décroissante
        return group.nlargest(1, '_surprise_abs')
    
    df_deduplicated = grouped.apply(keep_best, include_groups=False).reset_index(drop=True)
    
    # Supprimer les colonnes temporaires
    df_deduplicated = df_deduplicated.drop(columns=['_surprise_abs', '_time_group'], errors='ignore')
    
    return df_deduplicated

'''

# Trouver où insérer la fonction (avant calendar_to_events_df)
insertion_point = content.find('def calendar_to_events_df')

if insertion_point == -1:
    print("❌ ERREUR : Fonction calendar_to_events_df non trouvée")
    exit(1)

# Insérer la fonction
new_content = content[:insertion_point] + dedup_function + content[insertion_point:]

# Ajouter l'appel dans calendar_to_events_df
# Trouver la ligne df = df.dropna(subset=["ts_utc"])
target_line = 'df = df.dropna(subset=["ts_utc"])'
replacement = target_line + '''
    
    # ✅ SESSION 18 : DÉDUPLICATION MENSUEL/ANNUEL
    # Gère le cas où EODHD retourne Monthly ET Annual à la même heure
    df = _deduplicate_by_surprise(df)'''

new_content = new_content.replace(target_line, replacement)

# Écrire le nouveau fichier
with open(client_path, 'w') as f:
    f.write(new_content)

print("\n✅ Fix appliqué avec succès !")
print("\n📝 Modifications :")
print("  1. Fonction _deduplicate_by_surprise() ajoutée")
print("  2. Appel ajouté dans calendar_to_events_df()")
print(f"  3. Backup sauvegardé : {backup_path.name}")

print("\n" + "=" * 80)
print("🧪 PROCHAINE ÉTAPE : TESTER LE FIX")
print("=" * 80)
print("""
1. Re-scraper le 11 septembre :
   python -c "from fx_impact_app.src.eodhd_client import *; 
              data = fetch_calendar_json('2025-09-11', '2025-09-11', countries=['US']);
              df = calendar_to_events_df(data);
              print(df[df['event_key']=='inflation rate'][['event_title','actual','estimate']])"

2. Vérifier que seule la version Monthly est gardée

3. Si OK → Re-import complet depuis 2023
""")

print("\n✅ Script terminé !")
print("=" * 80)
