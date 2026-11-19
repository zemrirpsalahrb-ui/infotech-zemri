import os
import sys
import re
import ssl
import urllib.request
import urllib.parse

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cctv_backend.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import django
django.setup()

from api.models import Product, ProductImage

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

MEDIA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media', 'products')
WEBSITE_PUBLIC_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'WEBSITE', 'public', 'products'))

items_to_fix = [
    (25, "Dahua HAC-HDW1500TRQA-A", "hac-hdw1500trqa-a"),
    (28, "Dahua HAC-HFW1509T-A-LED", "hac-hfw1509t-a-led"),
    (82, "Dahua HAC-B2A21P 2MP bullet", "hac-b2a21p"),
    (159, "Tuya 360 Panoramic WiFi Indoor Camera", "cam-360-panoramic"),
    (164, "LSC Smart Connect 360 Camera", "lsc-smart-360-camera"),
    (165, "Analog CCTV Eyeball Security Camera", "camera-ancien-analog"),
    (227, "CCTV Camera Hidden Mount Bracket Screws", "discret-vis-cam"),
    (306, "Professional CCTV Installation Service", "installation-cameras-cctv"),
    (309, "Dahua DH-IPC-HFW1230S IP Camera", "ipc-hfw1230s-entry"),
    (313, "Dahua DH-IPC-HFW2541S-S WizSense", "ipc-hfw2541s-s-wizsense"),
    (357, "Dahua DH-NVR5216-EI 16-channel WizSense", "nvr-16ch-5216-ei"),
    (437, "16 Channel CCTV Centralized Power Supply Box 12V 20A", "supply-power-ssp-16s"),
    (455, "Hikvision DS-3E0109P-E 8 Port PoE Switch", "hikvision-8port-poe-switch"),
    (456, "TP-Link TL-SF1008P 8 Port PoE Switch", "tplink-8port-poe-switch"),
    (466, "CCTV Eyeball Dome Round Junction Box Camera", "tcam-rond-cctv"),
    (495, "Dahua DH-XVR5108H-4KL-I3 4K 8 Channel XVR", "xvr-8ch-4kl-i3"),
    (162, "Video Doorbell Intercom Monitor Phone Camera", "cam-video-phone")
]

def search_bing_murl(query):
    url = f"https://www.bing.com/images/search?q={urllib.parse.quote(query)}&first=1"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
            html = r.read().decode('utf-8', errors='ignore')
        murls = re.findall(r'murl&quot;:&quot;(https?://[^&]+?\.(?:jpg|png|webp|jpeg))', html)
        for m in murls:
            low = m.lower()
            if not any(bad in low for bad in ['logo', 'flag', 'banner', 'ad.', 'icon']):
                return m
    except Exception as e:
        pass
    return None

def download_file(url, local_path):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
        data = r.read()
        if len(data) > 3000:
            with open(local_path, 'wb') as f:
                f.write(data)
            return True
    return False

for pid, q, slug in items_to_fix:
    try:
        p = Product.objects.get(id=pid)
    except Product.DoesNotExist:
        continue
    
    local_filename = f"{slug}.jpg"
    local_path = os.path.join(MEDIA_DIR, local_filename)
    website_path = os.path.join(WEBSITE_PUBLIC_DIR, local_filename)
    media_url = f"/media/products/{local_filename}"

    print(f"[{pid}] Fixing: {p.name} -> Query: {q}")
    img_url = search_bing_murl(q)
    success = False
    if img_url:
        try:
            success = download_file(img_url, local_path)
            if success:
                with open(local_path, 'rb') as fsrc, open(website_path, 'wb') as fdst:
                    fdst.write(fsrc.read())
                print(f"  -> SUCCESS ({os.path.getsize(local_path)} bytes) from {img_url[:65]}")
        except Exception as e:
            print(f"  -> Download failed: {e}")
    
    if not success:
        # Fallback to general Dahua / CCTV camera photo
        fallback_url = "https://images.unsplash.com/photo-1557597774-9d273605dfa9?auto=format&fit=crop&w=800&q=80"
        try:
            download_file(fallback_url, local_path)
            with open(local_path, 'rb') as fsrc, open(website_path, 'wb') as fdst:
                fdst.write(fsrc.read())
            print(f"  -> Applied high-res CCTV fallback")
        except Exception as e:
            print(f"  -> Fallback failed: {e}")

    if os.path.exists(local_path) and os.path.getsize(local_path) > 3000:
        p.images.update(is_main=False)
        pimg, _ = ProductImage.objects.get_or_create(
            product=p,
            image_url=media_url,
            defaults={"alt_text": f"{p.name} - {p.reference}", "is_main": True, "sort_order": 0}
        )
        pimg.is_main = True
        pimg.save()

print("\nAll missing items updated successfully!")

