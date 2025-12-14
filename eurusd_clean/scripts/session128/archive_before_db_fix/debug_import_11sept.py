#!/usr/bin/env python3
"""Debug import - afficher TOUTES les erreurs"""
import json
from pathlib import Path
from datetime import datetime
import hashlib

data_dir = Path(__file__).parent.parent.parent / 'data'
eodhd_file = data_dir / 'eodhd_2020_2025_fixed' / 'eodhd_all_2020_2025_fixed.json'

with open(eodhd_file, 'r') as f:
    events = json.load(f)

# Filtrer 11 sept US 12:30
sept11_us_1230 = [e for e in events 
                   if '2025-09-11 12:30:00' in e.get('date', '') 
                   and e.get('country') == 'US']

print("="*80)
print(f"DEBUG IMPORT - {len(sept11_us_1230)} ÉVÉNEMENTS US 12:30")
print("="*80)
print()

country_map = {
    'US': 'US', 'GB': 'GB', 'EU': 'EU'
}

for idx, event in enumerate(sept11_us_1230, 1):
    print(f"\n{'='*80}")
    print(f"ÉVÉNEMENT {idx}/{len(sept11_us_1230)}")
    print(f"{'='*80}")
    
    event_type_raw = event.get('type', 'unknown')
    print(f"Type (raw)       : {event_type_raw}")
    
    try:
        # Date
        date_str = event.get('date', '')
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        print(f"✅ Date parsed   : {dt}")
        
        # Event name
        event_type = event_type_raw.lower().replace(' ', '_').replace('-', '_')
        comparison = event.get('comparison', '').lower()
        
        if comparison in ['mom', 'yoy', 'qoq', 'mtd', 'ytd']:
            event_name = f"{event_type}_{comparison}"
            print(f"✅ Event name    : {event_name} (avec suffixe)")
        else:
            event_name = event_type
            print(f"✅ Event name    : {event_name} (sans suffixe)")
        
        # ID
        event_json = json.dumps(event, sort_keys=True)
        event_hash = hashlib.md5(event_json.encode()).hexdigest()[:8]
        event_id = f"eodhd_{date_str}_{event.get('country', 'xx')}_{event_hash}"
        event_id = event_id.replace(' ', '_').replace(':', '').replace('.', '')[:200]
        print(f"✅ Event ID      : {event_id[:50]}...")
        
        # Country
        country_iso = event.get('country', 'XX')
        country = country_map.get(country_iso, country_iso)
        print(f"✅ Country       : {country}")
        
        # Values
        actual = event.get('actual')
        estimate = event.get('estimate')
        previous = event.get('previous')
        
        print(f"✅ Actual        : {actual}")
        print(f"✅ Estimate      : {estimate}")
        print(f"✅ Previous      : {previous}")
        
        # Convert to float
        for val_name in ['actual', 'estimate', 'previous']:
            val = locals()[val_name]
            if val and isinstance(val, str):
                try:
                    converted = float(val.replace(',', '.'))
                    print(f"✅ {val_name.capitalize():12} : {val} → {converted}")
                except Exception as e:
                    print(f"❌ {val_name.capitalize():12} : Conversion failed: {e}")
        
        print(f"\n✅ ÉVÉNEMENT OK - Serait importé")
        
    except Exception as e:
        print(f"\n❌ ERREUR : {e}")
        import traceback
        traceback.print_exc()
        print(f"\n❌ CET ÉVÉNEMENT SERAIT PERDU !")

print("\n" + "="*80)
print("RÉSUMÉ")
print("="*80)
