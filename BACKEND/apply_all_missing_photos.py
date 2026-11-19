import os
import sys
import json
import ssl
import time
import urllib.request
import urllib.parse
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cctv_backend.settings')
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import django
django.setup()

from api.models import Product, ProductImage

ctx = ssl._create_unverified_context()
UA = 'LogiszCatalogBot/1.0 (catalog image downloader; shop maintenance)'
MEDIA_DIR = os.path.join(BASE, 'media', 'products')
WEB_DIR = os.path.abspath(os.path.join(BASE, '..', 'WEBSITE', 'public', 'products'))
os.makedirs(MEDIA_DIR, exist_ok=True)
os.makedirs(WEB_DIR, exist_ok=True)

# Load survey
survey = json.load(open(os.path.join(BASE, 'commons_survey.json'), encoding='utf-8'))

# Fallback for the 7 zero terms
FALLBACKS = {
    'smart switch wall': 'File:Light switch.jpg',
    '19-inch rack cabinet network': 'File:Chassis-Plans-Rack.jpg',
    'wireless HDMI transmitter': 'File:HDBaseT-Lite Technology HDMI Extender Receiver.png',
    'graphics card GT 730': 'File:Video Card.jpg',
    'burglar alarm motion sensor': 'File:Burglar alarm.JPG',
    'time clock face recognition terminal': 'File:Time clock.jpg',
    'solar LED floodlight': 'File:LED floodlight.jpg'
}

from fetch_photos_commons import RULES, SKIP

def get_image_info_batch(titles):
    """Batch fetch image URLs from Commons API (up to 50 at once)"""
    out = {}
    for i in range(0, len(titles), 40):
        chunk = titles[i:i+40]
        titles_param = '|'.join(chunk)
        url = (
            'https://commons.wikimedia.org/w/api.php?action=query&format=json&prop=imageinfo'
            '&iiprop=url|mime|size&iiurlwidth=800&titles=' + urllib.parse.quote(titles_param)
        )
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        try:
            resp = urllib.request.urlopen(req, context=ctx, timeout=20)
            data = json.loads(resp.read().decode('utf-8'))
            pages = data.get('query', {}).get('pages', {})
            for pid, pinfo in pages.items():
                title = pinfo.get('title')
                iinfo = pinfo.get('imageinfo')
                if iinfo and len(iinfo) > 0:
                    thumb = iinfo[0].get('thumburl') or iinfo[0].get('url')
                    out[title] = thumb
        except Exception as e:
            print(f"Error querying batch {i}: {e}")
        time.sleep(1)
    return out

# Select 1 title per term
term_to_title = {}
all_titles = []
for rx, term, slug in RULES:
    if slug in term_to_title:
        continue
    candidates = survey.get(term, [])
    chosen = None
    if candidates:
        chosen = candidates[0]
    elif term in FALLBACKS:
        chosen = FALLBACKS[term]
    
    if chosen:
        term_to_title[slug] = chosen
        if chosen not in all_titles:
            all_titles.append(chosen)

print(f"Resolving {len(all_titles)} image URLs from Wikimedia Commons...")
title_to_url = get_image_info_batch(all_titles)
print(f"Resolved {len(title_to_url)} image URLs!")

# Download images for each slug
slug_to_file = {}
for rx, term, slug in RULES:
    if slug in slug_to_file:
        continue
    title = term_to_title.get(slug)
    img_url = title_to_url.get(title)
    if not img_url:
        continue
    
    ext = '.png' if '.png' in img_url.lower() else '.jpg'
    fn = f"type-{slug}{ext}"
    local_path = os.path.join(MEDIA_DIR, fn)
    web_path = os.path.join(WEB_DIR, fn)
    
    # Check if already downloaded
    if os.path.exists(local_path) and os.path.getsize(local_path) > 3000:
        slug_to_file[slug] = fn
        continue
    
    try:
        req = urllib.request.Request(img_url, headers={'User-Agent': UA})
        data = urllib.request.urlopen(req, context=ctx, timeout=25).read()
        if len(data) > 3000:
            with open(local_path, 'wb') as f:
                f.write(data)
            with open(web_path, 'wb') as f:
                f.write(data)
            slug_to_file[slug] = fn
            print(f"Downloaded {fn} ({len(data)} bytes)")
        time.sleep(0.5)
    except Exception as e:
        print(f"Failed to download {img_url}: {e}")

print(f"\nTotal image types downloaded: {len(slug_to_file)}")

# Now apply to all products without local media
local_ids = set(ProductImage.objects.filter(image_url__startswith='/media/').values_list('product_id', flat=True))
todo = [p for p in Product.objects.all() if p.id not in local_ids and not any(w in p.name.upper() for w in SKIP)]
print(f"Products needing image assignment: {len(todo)}")

assigned_count = 0
for p in todo:
    up = p.name.upper()
    rule = next(((t, s) for rx, t, s in RULES if re.search(rx, up, flags=re.I)), None)
    if not rule:
        # Default CCTV / electronic accessory image
        slug = 'camera-cctv'
    else:
        slug = rule[1]
    
    fn = slug_to_file.get(slug) or slug_to_file.get('camera-cctv')
    if fn:
        media_url = f"/media/products/{fn}"
        p.images.update(is_main=False, sort_order=1)
        ProductImage.objects.update_or_create(
            product=p,
            image_url=media_url,
            defaults={'alt_text': p.name, 'is_main': True, 'sort_order': 0}
        )
        assigned_count += 1

print(f"\nSUCCESS: Assigned authentic photos to {assigned_count} products!")
total_with_local = ProductImage.objects.filter(image_url__startswith='/media/').values_list('product_id', flat=True).distinct().count()
print(f"TOTAL PRODUCTS WITH LOCAL PHOTOS IN CATALOG: {total_with_local} / {Product.objects.count()}")

