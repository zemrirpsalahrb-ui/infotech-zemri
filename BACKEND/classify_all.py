import os, sys, django
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cctv_backend.settings')
django.setup()
from api.models import Product

products = list(Product.objects.all())

categories = {
    'dahua_cameras': [],
    'dahua_recorders': [],
    'dahua_alarms': [],
    'imou_cameras': [],
    'cctv_power_switches': [],
    'surveillance_hdd': [],
    'cctv_accessories': [],
    'other_it': []
}

for p in products:
    full = (p.name + ' ' + p.reference).upper()
    
    # Check Dahua cameras
    if any(k in full for k in ['1200', '1400', '1500', '1509', '1800', '1801', '1809', 'T1A', 'B1A', 'B2A', 'T2A', 'HAC', 'HFW', 'HDW', 'HDBW']) and not any(k in full for k in ['ACER', 'HP', 'DELL', 'MSI']):
        categories['dahua_cameras'].append(p)
    elif any(k in full for k in ['IPC 1', 'IPC H', 'IPC 2', 'IPC 4', 'IPC-']):
        categories['dahua_cameras'].append(p)
    elif 'SPEED DOME' in full or 'CAM SOLAIR' in full or 'CAM 360' in full or 'CAMERA 360' in full or 'CAM SIM' in full or 'CAM WIFI' in full or 'TCAM' in full or 'CAMERA OEIL' in full or 'CAMERA ANCIEN' in full:
        categories['dahua_cameras'].append(p)
    elif any(k in full for k in ['XVR', 'NVR', 'DVR']):
        categories['dahua_recorders'].append(p)
    elif any(k in full for k in ['ARA14', 'ARA24', 'ARC3000', 'ARD22', 'ARD32', 'ARD82', 'ALARM DAHUA', 'CLAVIER ALARME', 'DIGI CODE']):
        categories['dahua_alarms'].append(p)
    elif 'IMOU' in full or 'HERO B1' in full:
        categories['imou_cameras'].append(p)
    elif any(k in full for k in ['SUPPLY POWER', 'BLOC ALIMENTATION', 'SWITCH POE', 'SWITCH  6P', 'SWITCH POE']):
        categories['cctv_power_switches'].append(p)
    elif 'DISQUE DURE' in full or 'HDD' in full or 'PERPEL' in full or 'PURPLE' in full or 'SKYHAWK' in full:
        categories['surveillance_hdd'].append(p)
    elif any(k in full for k in ['BNC', 'BALUN', 'CABLE RESEAU', 'CABLE COAXIAL', 'CABLE DVR', 'BOITE', 'CONNECTEUR', 'CAMAXX', 'TESTER']):
        categories['cctv_accessories'].append(p)
    else:
        categories['other_it'].append(p)

print("SUMMARY OF PRODUCTS:")
for cat_name, items in categories.items():
    print(f"=== {cat_name.upper()} ({len(items)} items) ===")
    for item in items:
        print(f"  ID:{item.id:3d} | REF:{item.reference:18s} | NAME:{item.name:36s} | IMGS:{item.images.count()}")

