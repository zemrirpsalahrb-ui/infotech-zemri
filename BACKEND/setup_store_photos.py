import os, ssl, urllib.request

ctx = ssl._create_unverified_context()
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'

STORE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media', 'store')
WEB_STORE_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'WEBSITE', 'public', 'store'))
os.makedirs(STORE_DIR, exist_ok=True)
os.makedirs(WEB_STORE_DIR, exist_ok=True)

# High-resolution CCTV & IT equipment store showroom photos
STORE_PHOTOS = [
    ("magasin_01_facade_showroom.jpg", "https://images.unsplash.com/photo-1577495508048-b635879837f1?auto=format&fit=crop&w=1200&q=85"),
    ("magasin_02_rayon_cctv.jpg", "https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=1200&q=85"),
    ("magasin_03_comptoir_service.jpg", "https://images.unsplash.com/photo-1556740738-b6a63e27c4df?auto=format&fit=crop&w=1200&q=85"),
    ("magasin_04_stock_equipements.jpg", "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?auto=format&fit=crop&w=1200&q=85")
]

for filename, url in STORE_PHOTOS:
    dst1 = os.path.join(STORE_DIR, filename)
    dst2 = os.path.join(WEB_STORE_DIR, filename)
    print(f"Downloading {filename}...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        data = urllib.request.urlopen(req, context=ctx, timeout=25).read()
        if len(data) > 5000:
            with open(dst1, 'wb') as f:
                f.write(data)
            with open(dst2, 'wb') as f:
                f.write(data)
            print(f" -> Saved ({len(data)} bytes)")
    except Exception as e:
        print(f" -> Error: {e}")

print("Store photos ready!")

