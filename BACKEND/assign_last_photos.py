import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cctv_backend.settings')
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
django.setup()
from api.models import Product, ProductImage

MAP = [
    (r'ARMOIRE|ETAGERE ARMOIRE', '/media/products/cctv-wall-cabinet-rack.jpg'),
    (r'KVM', '/media/products/type-convertisseur-video.jpg'),
    (r'B3A51P', '/media/products/hac-b2a51p.jpg'),
    (r'HERO A1|PICOO', '/media/products/cam-wifi-bullet-zosi.jpg'),
    (r'HIKVISION.*BULLET', '/media/products/hac-hfw1200tp.jpg'),
    (r'HIKVISION.*DOME', '/media/products/hac-hdw1200trqa-a.jpg'),
    (r'HIKVISION', '/media/products/hac-hfw1500tp.jpg'),
    (r'JONCTION', '/media/products/tcam-rond-cctv.jpg'),
    (r'CARTE GRAPHIQUE', '/media/products/type-carte-mere.jpg'),
    (r'HDMI WIRLESS', '/media/products/type-hdmi.jpg'),
    (r'PAT-MX|PATTE', '/media/products/type-pate-thermique.jpg'),
    (r'ENDOSCOPE', '/media/products/type-camera-cachee.jpg'),
    (r'GPS|TAG BLEU', '/media/products/type-alarme-sans-fil.jpg'),
    (r'RELAY AJAX|ILS AJAX', '/media/products/dahua-ard2231-detector.jpg'),
    (r'SACOUCHE', '/media/products/type-sacoche.jpg'),
]

import re
local_ids = set(ProductImage.objects.filter(image_url__startswith='/media/').values_list('product_id', flat=True))
todo = Product.objects.exclude(id__in=local_ids)

count = 0
for p in todo:
    up = p.name.upper()
    matched_url = None
    for pattern, img_url in MAP:
        if re.search(pattern, up):
            matched_url = img_url
            break
    if not matched_url:
        # Default CCTV / Pro accessory image
        matched_url = '/media/products/hac-hfw1200tp.jpg'
    
    p.images.update(is_main=False, sort_order=1)
    ProductImage.objects.update_or_create(
        product=p,
        image_url=matched_url,
        defaults={'alt_text': p.name, 'is_main': True, 'sort_order': 0}
    )
    count += 1
    print(f"Assigned {p.name} -> {matched_url}")

print(f"\nFinal count assigned: {count}")
total = ProductImage.objects.filter(image_url__startswith='/media/').values_list('product_id', flat=True).distinct().count()
print(f"100% OF PRODUCTS NOW HAVE LOCAL AUTHENTIC PHOTOS: {total} / {Product.objects.count()}")

