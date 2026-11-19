import os
import sys
import re
import ssl
import time
import urllib.request
import urllib.parse
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cctv_backend.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import django
django.setup()

from api.models import Product, ProductImage, Category, Brand

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

MEDIA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media', 'products')
WEBSITE_PUBLIC_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'WEBSITE', 'public', 'products'))

os.makedirs(MEDIA_DIR, exist_ok=True)
os.makedirs(WEBSITE_PUBLIC_DIR, exist_ok=True)

# Retrieve or get Brands
brand_dahua = Brand.objects.filter(name__iexact="Dahua Technology").first() or Brand.objects.filter(name__iexact="DAHUA").first()
brand_imou = Brand.objects.filter(name__iexact="IMOU").first()
brand_wd = Brand.objects.filter(name__iexact="Western Digital").first()
brand_hik = Brand.objects.filter(name__iexact="Hikvision").first()
brand_zk = Brand.objects.filter(slug="zkteco").first()
if not brand_zk:
    brand_zk = Brand.objects.create(name="ZKTeco", slug="zkteco", description="Systèmes de contrôle d'accès et pointage biométrique.")

# Retrieve Categories
cat_analog = Category.objects.filter(name__iexact="Analog Cameras").first()
cat_ip = Category.objects.filter(name__iexact="IP Cameras").first()
cat_wifi = Category.objects.filter(name__iexact="Wi-Fi Cameras").first()
cat_ptz = Category.objects.filter(name__iexact="PTZ Cameras").first()
cat_dvr = Category.objects.filter(name__iexact="DVR").first()
cat_nvr = Category.objects.filter(name__iexact="NVR").first()
cat_hdd = Category.objects.filter(name__iexact="Surveillance Hard Drives").first()
cat_power = Category.objects.filter(name__iexact="Power Supplies").first()
cat_alarm = Category.objects.filter(name__iexact="Alarm Systems").first()
cat_acc = Category.objects.filter(name__iexact="Accessories").first()

# Model query mapping helper
def build_search_query_and_meta(p):
    name = p.name.strip()
    ref = p.reference.strip()
    u = (name + ' ' + ref).upper()
    
    # 1. Dahua Cooper Cameras
    if 'T1A21P' in u:
        return ("Dahua HAC-T1A21P camera", "hac-t1a21p", brand_dahua, cat_analog)
    if 'T1A51P' in u:
        return ("Dahua HAC-T1A51P 5MP camera", "hac-t1a51p", brand_dahua, cat_analog)
    if 'B1A21P' in u:
        return ("Dahua HAC-B1A21P bullet camera", "hac-b1a21p", brand_dahua, cat_analog)
    if 'B2A21P' in u:
        return ("Dahua HAC-B2A21P bullet camera", "hac-b2a21p", brand_dahua, cat_analog)
    if 'B2A51P' in u:
        return ("Dahua HAC-B2A51P 5MP bullet camera", "hac-b2a51p", brand_dahua, cat_analog)
    if 'T2A21P' in u:
        return ("Dahua HAC-T2A21P eyeball camera", "hac-t2a21p", brand_dahua, cat_analog)

    # 2. Dahua HDCVI 1200 Series
    if '1200 TP-Z' in u or '1200 TPZ' in u:
        return ("Dahua HAC-HFW1200TP-Z motorized camera", "hac-hfw1200tp-z", brand_dahua, cat_analog)
    if '1200 TP-A' in u:
        return ("Dahua HAC-HFW1200TP-A mic camera", "hac-hfw1200tp-a", brand_dahua, cat_analog)
    if '1200 TP' in u:
        return ("Dahua HAC-HFW1200TP bullet camera", "hac-hfw1200tp", brand_dahua, cat_analog)
    if '1200 TRQA' in u:
        return ("Dahua HAC-HDW1200TRQA-A eyeball camera", "hac-hdw1200trqa-a", brand_dahua, cat_analog)

    # 3. Dahua HDCVI 1400 Series
    if '1400 EP' in u:
        return ("Dahua HAC-HDW1400EP eyeball camera", "hac-hdw1400ep", brand_dahua, cat_analog)

    # 4. Dahua HDCVI 1500 Series
    if '1500 CLQP-IL-A' in u:
        return ("Dahua HAC-HDW1500CLQP-IL-A dual light camera", "hac-hdw1500clqp-il-a", brand_dahua, cat_analog)
    if '1500 CMP-IL-A' in u:
        return ("Dahua HAC-HFW1500CMP-IL-A dual light camera", "hac-hfw1500cmp-il-a", brand_dahua, cat_analog)
    if '1500 RLP-IL-A' in u:
        return ("Dahua HAC-HDW1500RLP-IL-A camera", "hac-hdw1500rlp-il-a", brand_dahua, cat_analog)
    if '1500 TLMP-A' in u:
        return ("Dahua HAC-HFW1500TLMP-A camera", "hac-hfw1500tlmp-a", brand_dahua, cat_analog)
    if '1500 TPZ-A' in u or '1500 TPZ' in u:
        return ("Dahua HAC-HFW1500TP-Z-A camera", "hac-hfw1500tp-z-a", brand_dahua, cat_analog)
    if '1500 TP' in u:
        return ("Dahua HAC-HFW1500TP bullet camera", "hac-hfw1500tp", brand_dahua, cat_analog)
    if '1500 TRQA' in u:
        return ("Dahua HAC-HDW1500TRQA-A eyeball camera", "hac-hdw1500trqa-a", brand_dahua, cat_analog)

    # 5. Dahua Full-Color 1509 Series
    if '1509 TLMQP' in u:
        return ("Dahua HAC-HFW1509TLMQP-LED full color camera", "hac-hfw1509tlmqp-led", brand_dahua, cat_analog)
    if '1509 TUP-Z' in u:
        return ("Dahua HAC-HFW1509TUP-Z-A-LED motorized camera", "hac-hfw1509tup-z-a-led", brand_dahua, cat_analog)
    if '1509T-A' in u:
        return ("Dahua HAC-HFW1509T-A-LED full color camera", "hac-hfw1509t-a-led", brand_dahua, cat_analog)

    # 6. Dahua HDCVI 1800 / 1801 / 1809 4K Series
    if '1800 TLA' in u:
        return ("Dahua HAC-HFW1800TL-A 4K bullet camera", "hac-hfw1800tl-a", brand_dahua, cat_analog)
    if '1801 CMP-IL-A' in u:
        return ("Dahua HAC-HFW1801CMP-IL-A 4K camera", "hac-hfw1801cmp-il-a", brand_dahua, cat_analog)
    if '1801 TLMP-IL-A' in u:
        return ("Dahua HAC-HFW1801TLMP-IL-A 4K camera", "hac-hfw1801tlmp-il-a", brand_dahua, cat_analog)
    if '1801 TLQA' in u:
        return ("Dahua HAC-HDW1801TLQA-A 4K eyeball camera", "hac-hdw1801tlqa-a", brand_dahua, cat_analog)
    if '1801T-Z' in u:
        return ("Dahua HAC-HFW1801T-Z-A 4K motorized camera", "hac-hfw1801t-z-a", brand_dahua, cat_analog)
    if '1801T-A' in u:
        return ("Dahua HAC-HFW1801T-A 4K camera", "hac-hfw1801t-a", brand_dahua, cat_analog)
    if '1809TLMP-A' in u:
        return ("Dahua HAC-HFW1809TLMP-A-LED 4K full color camera", "hac-hfw1809tlmp-a", brand_dahua, cat_analog)

    # 7. Dahua Pro HDCVI
    if '2501TUP-Z' in u:
        return ("Dahua HAC-HFW2501TUP-Z-A starlight camera", "hac-hfw2501tup-z-a", brand_dahua, cat_analog)
    if '2802T-Z' in u:
        return ("Dahua HAC-HFW2802T-Z-A 4K starlight camera", "hac-hfw2802t-z-a", brand_dahua, cat_analog)

    # 8. Dahua IP Cameras (IPC)
    if 'IPC 1230' in u:
        return ("Dahua DH-IPC-HFW1230S IP camera", "ipc-hfw1230s", brand_dahua, cat_ip)
    if 'IPC HDBW2541E-S' in u:
        return ("Dahua DH-IPC-HDBW2541E-S dome camera", "ipc-hdbw2541e-s", brand_dahua, cat_ip)
    if 'IPC HDBW2841EP-S-S2' in u:
        return ("Dahua DH-IPC-HDBW2841EP-S-S2 4K dome camera", "ipc-hdbw2841ep-s-s2", brand_dahua, cat_ip)
    if 'IPC HFW1639TC' in u:
        return ("Dahua DH-IPC-HFW1639TC-A-LED smart dual IP camera", "ipc-hfw1639tc-a-led", brand_dahua, cat_ip)
    if 'IPC HFW2541S-S' in u:
        return ("Dahua DH-IPC-HFW2541S-S WizSense IP camera", "ipc-hfw2541s-s", brand_dahua, cat_ip)
    if 'IPC HFW2841SP-S-S2' in u:
        return ("Dahua DH-IPC-HFW2841SP-S-S2 4K IP camera", "ipc-hfw2841sp-s-s2", brand_dahua, cat_ip)

    # 9. Speed Dome & PTZ
    if 'SPEED DOME' in u or 'PTZ X4' in u:
        return ("Dahua SD22404T-GN 4MP 4X PTZ speed dome", "dahua-sd22404t-gn-ptz", brand_dahua, cat_ptz)
    if 'SOLAIR' in u and 'PTZ' in u:
        return ("Dahua 4G Solar PTZ security camera kit", "dahua-solar-4g-ptz", brand_dahua, cat_ptz)
    if 'CAM SIM OKAM' in u:
        return ("4G SIM Solar Dual Lens PTZ Security Camera", "cam-4g-sim-dual-lens", brand_dahua, cat_wifi)
    if 'CAM WIFI BULLET ZOSI' in u:
        return ("ZOSI WiFi Bullet Security Camera", "cam-wifi-bullet-zosi", None, cat_wifi)
    if '360 LSC' in u or 'CAM 360' in u or 'CAMERA 360' in u:
        return ("Smart 360 Panoramic WiFi Indoor Camera", "smart-360-wifi-camera", brand_imou, cat_wifi)
    if 'OEIL DE BOEUF' in u:
        return ("Digital Door Peephole Viewer Camera with Screen", "camera-oeil-de-boeuf-ecran", brand_dahua, cat_wifi)

    # 10. Imou Cameras
    if 'IMOU' in u and 'RANGER' in u:
        return ("Imou Ranger 2 3MP Pan Tilt WiFi Camera", "imou-ranger-2-3mp", brand_imou, cat_wifi)
    if 'IMOU' in u and '4MP' in u and 'F42N' in u:
        return ("Imou Bullet 2C 4MP Outdoor WiFi Camera", "imou-bullet-2c-4mp", brand_imou, cat_wifi)
    if 'IMOU' in u and '5MP' in u and 'F42N' in u:
        return ("Imou Bullet 2 5MP Outdoor WiFi Camera", "imou-bullet-2-5mp", brand_imou, cat_wifi)
    if 'IMOU' in u and 'PS8E' in u:
        return ("Imou Cruiser SE Full Color PTZ Camera", "imou-cruiser-se-ptz", brand_imou, cat_wifi)
    if 'HERO B1' in u:
        return ("Imou Dahua Hero B1 3MP WiFi Camera", "imou-hero-b1-3mp", brand_imou, cat_wifi)

    # 11. Dahua XVR Recorders
    if 'XVR 4CH 4KL' in u:
        return ("Dahua DH-XVR5104H-4KL-I3 4K XVR", "dh-xvr5104h-4kl-i3", brand_dahua, cat_dvr)
    if 'XVR 4CH 5MP' in u or 'XVR 4CH I3' in u or 'XVR 4CH' in u:
        return ("Dahua DH-XVR5104HS-I3 4-channel XVR", "dh-xvr5104hs-i3", brand_dahua, cat_dvr)
    if 'XVR 8CH 4KL' in u:
        return ("Dahua DH-XVR5108H-4KL-I3 4K 8-channel XVR", "dh-xvr5108h-4kl-i3", brand_dahua, cat_dvr)
    if 'XVR 8CH 2MP' in u:
        return ("Dahua DH-XVR1B08 8-channel Cooper XVR", "dh-xvr1b08", brand_dahua, cat_dvr)
    if 'XVR 8CH 5MP' in u or 'XVR 8CH I3' in u or 'XVR 8CH' in u:
        return ("Dahua DH-XVR5108HS-I3 8-channel XVR", "dh-xvr5108hs-i3", brand_dahua, cat_dvr)
    if 'XVR 16CH 4KL' in u:
        return ("Dahua DH-XVR5116H-4KL-I3 16-channel 4K XVR", "dh-xvr5116h-4kl-i3", brand_dahua, cat_dvr)
    if 'XVR 16CH' in u:
        return ("Dahua DH-XVR5116HS-I3 16-channel XVR", "dh-xvr5116hs-i3", brand_dahua, cat_dvr)
    if 'XVR 5232' in u or '32CH' in u:
        return ("Dahua DH-XVR5232AN-I3 32-channel XVR", "dh-xvr5232an-i3", brand_dahua, cat_dvr)

    # 12. Dahua NVR Recorders
    if 'NVR 8CH 5208' in u:
        return ("Dahua DH-NVR5208-EI 8-channel WizSense NVR", "dh-nvr5208-ei", brand_dahua, cat_nvr)
    if 'NVR 8CH POE' in u:
        return ("Dahua DH-NVR4108-8P-4KS2 8-channel PoE NVR", "dh-nvr4108-8p-4ks2", brand_dahua, cat_nvr)
    if 'NVR5216-EI 4K POE' in u:
        return ("Dahua DH-NVR5216-16P-EI 16-channel 4K PoE NVR", "dh-nvr5216-16p-ei", brand_dahua, cat_nvr)
    if 'NVR 16CH 5216' in u:
        return ("Dahua DH-NVR5216-EI 16-channel WizSense NVR", "dh-nvr5216-ei", brand_dahua, cat_nvr)
    if 'NVR 16CH 5416' in u:
        return ("Dahua DH-NVR5416-4KS2 16-channel 4-HDD NVR", "dh-nvr5416-4ks2", brand_dahua, cat_nvr)

    # 13. Dahua Alarms & Access Control
    if 'ALARM DAHUA' in u or 'ARC3000' in u:
        return ("Dahua ARC3000H-03-GW02-868 wireless alarm hub", "dahua-arc3000h-hub", brand_dahua, cat_alarm)
    if 'CLAVIER ALARME' in u:
        return ("Dahua ARK30T wireless alarm keypad", "dahua-ark30t-keypad", brand_dahua, cat_alarm)
    if 'ARA14' in u:
        return ("Dahua ARA14-W2-868 wireless indoor siren", "dahua-ara14-siren", brand_dahua, cat_alarm)
    if 'ARA24' in u:
        return ("Dahua ARA24-W2 wireless remote keyfob", "dahua-ara24-remote", brand_dahua, cat_alarm)
    if 'ARD2231' in u:
        return ("Dahua ARD2231-W2 dual-tech motion detector", "dahua-ard2231-detector", brand_dahua, cat_alarm)
    if 'ARD225E' in u:
        return ("Dahua ARD225E-W2 outdoor PIR detector", "dahua-ard225e-pir", brand_dahua, cat_alarm)
    if 'ARD323' in u:
        return ("Dahua ARD323-W2 wireless door contact", "dahua-ard323-door-contact", brand_dahua, cat_alarm)
    if 'ARD821' in u:
        return ("Dahua ARD821-W2 wireless panic button", "dahua-ard821-panic-button", brand_dahua, cat_alarm)
    if 'DIGI CODE DAHUA' in u:
        return ("Dahua ASI1201E standalone access keypad RFID", "dahua-asi1201e-digicode", brand_dahua, cat_alarm)
    if 'DIGI CODE' in u:
        return ("Standalone Waterproof RFID Keypad Access Control", "rfid-digicode-keypad", None, cat_alarm)

    # 14. Surveillance Hard Drives (WD Purple / Seagate SkyHawk)
    if '8 TB' in u and ('PERPEL' in u or 'PURPLE' in u or 'DISQUE' in u):
        return ("Western Digital Purple 8TB Surveillance Hard Drive", "wd-purple-8tb-surveillance", brand_wd, cat_hdd)
    if '6TB' in u and ('PERPEL' in u or 'PURPLE' in u or 'DISQUE' in u):
        return ("Western Digital Purple 6TB Surveillance Hard Drive", "wd-purple-6tb-surveillance", brand_wd, cat_hdd)
    if '4 TB' in u and ('PERPEL' in u or 'PURPLE' in u or 'DISQUE' in u):
        return ("Western Digital Purple 4TB Surveillance Hard Drive", "wd-purple-4tb-surveillance", brand_wd, cat_hdd)
    if '3TB' in u and ('PERPEL' in u or 'PURPLE' in u or 'DISQUE' in u):
        return ("Western Digital Purple 3TB Surveillance Hard Drive", "wd-purple-3tb-surveillance", brand_wd, cat_hdd)
    if '2 TB' in u and ('PERPEL' in u or 'PURPLE' in u or 'DISQUE' in u):
        return ("Western Digital Purple 2TB Surveillance Hard Drive", "wd-purple-2tb-surveillance", brand_wd, cat_hdd)
    if '1 TB' in u and 'SEAGATE' in u:
        return ("Seagate SkyHawk 1TB Surveillance Hard Drive", "seagate-skyhawk-1tb", None, cat_hdd)
    if '1 TB' in u and ('PERPEL' in u or 'PURPLE' in u or 'DISQUE' in u):
        return ("Western Digital Purple 1TB Surveillance Hard Drive", "wd-purple-1tb-surveillance", brand_wd, cat_hdd)
    if '500 GB' in u and 'DISQUE' in u:
        return ("Seagate Video 500GB Surveillance Hard Drive", "cctv-hdd-500gb", None, cat_hdd)

    # 15. Power Supplies & PoE Switches
    if 'SUPPLY POWER 16S DAHUA' in u or 'BLOC ALIMENTATION 16CH' in u:
        return ("Dahua 16 Channel CCTV Centralized Power Supply Box 12V 20A", "dahua-power-supply-16ch", brand_dahua, cat_power)
    if 'SUPPLY POWER 8S' in u or 'BLOC ALIMENTATION 9S' in u:
        return ("Dahua 8 Channel CCTV Power Supply Box 12V 10A", "dahua-power-supply-8ch", brand_dahua, cat_power)
    if 'SUPPLY POWER 4S' in u or 'BLOC ALIMENTATION 4S' in u:
        return ("4 Channel CCTV Centralized Power Supply Box 12V 5A", "cctv-power-supply-4ch", brand_dahua, cat_power)
    if 'SWITCH  6P DAHUA' in u:
        return ("Dahua DH-PFS3006-4ET-60 6-Port PoE Switch", "dahua-pfs3006-poe-switch", brand_dahua, cat_power)
    if 'SWITCH POE 24 PORT DAHUA' in u:
        return ("Dahua 24-Port Gigabit Managed PoE Switch", "dahua-24port-poe-switch", brand_dahua, cat_power)
    if 'PFS3010' in u or 'SWITCH 8 PORT POE' in u:
        return ("Dahua PFS3010-8ET-96 8-Port Fast Ethernet PoE Switch", "dahua-pfs3010-8port-poe", brand_dahua, cat_power)
    if 'SWITCH POE 16 PORT' in u and 'HIKVISION' in u:
        return ("Hikvision 16-Port Gigabit Unmanaged PoE Switch", "hikvision-16port-poe-switch", brand_hik, cat_power)
    if 'SWITCH POE 8 PORT' in u and 'HIKVISION' in u:
        return ("Hikvision 8-Port PoE Switch", "hikvision-8port-poe-switch", brand_hik, cat_power)

    # 16. Accessories
    if 'BNC ASERTIR' in u:
        return ("BNC Crimp Connector for RG59 Coaxial Cable", "bnc-crimp-connector", brand_dahua, cat_acc)
    if 'RACORD BNC' in u:
        return ("BNC Coupler Barrel Connector Female to Female", "bnc-coupler-connector", brand_dahua, cat_acc)
    if 'BNC' in u:
        return ("BNC Male Video Connector for CCTV Camera", "bnc-male-connector", brand_dahua, cat_acc)
    if 'CABLE RESEAU FTP' in u:
        return ("Cat6 FTP Pure Copper 300M Network Cable Drum", "cat6-ftp-300m-drum", None, cat_acc)
    if 'CAMAXX' in u or 'ARMOIRE MURAL' in u:
        return ("Wall Mount 19 Inch CCTV Network Data Cabinet Rack", "cctv-wall-cabinet-rack", None, cat_acc)
    if 'IP CCTV TESTER' in u:
        return ("All-in-one 4K IP CCTV Tester Tool Monitor IPC Analog", "ipc-cctv-tester-tool", None, cat_acc)
    if 'ZK 3969' in u:
        return ("ZKTeco Face & Fingerprint Time Attendance Device", "zkteco-face-attendance", brand_zk, cat_acc)

    return (None, None, None, None)

def search_image_for_query(query):
    # Try Bing images search
    url = f"https://www.bing.com/images/search?q={urllib.parse.quote(query)}&first=1"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
            html = r.read().decode('utf-8', errors='ignore')
        murls = re.findall(r'murl&quot;:&quot;(https?://[^&]+?\.(?:jpg|png|webp|jpeg))', html)
        for m in murls:
            # Skip logos, flags, generic banners
            low = m.lower()
            if any(bad in low for bad in ['logo', 'flag', 'banner', 'ad.', 'tracking', 'pixel', 'icon']):
                continue
            return m
    except Exception as e:
        pass
    return None

def download_image(url, local_path):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
        data = r.read()
        if len(data) < 3000:
            return False
        with open(local_path, 'wb') as f:
            f.write(data)
        return True

print("Starting CCTV product image search and attachment...")
products = list(Product.objects.all())
matched_count = 0
downloaded_count = 0

for p in products:
    query, file_slug, brand_obj, cat_obj = build_search_query_and_meta(p)
    if not query:
        continue
    
    matched_count += 1
    
    # Update brand & category if needed
    if brand_obj and p.brand != brand_obj:
        p.brand = brand_obj
    if cat_obj and p.category != cat_obj:
        p.category = cat_obj
    p.save()

    local_filename = f"{file_slug}.jpg"
    local_path = os.path.join(MEDIA_DIR, local_filename)
    website_path = os.path.join(WEBSITE_PUBLIC_DIR, local_filename)
    media_url = f"/media/products/{local_filename}"

    # Check if already downloaded
    already_exists = os.path.exists(local_path) and os.path.getsize(local_path) > 3000

    if not already_exists:
        print(f"[{p.id}] Searching image for: {p.name} -> Query: '{query}'")
        img_url = search_image_for_query(query)
        if img_url:
            try:
                success = download_image(img_url, local_path)
                if success:
                    # also copy to website public
                    with open(local_path, 'rb') as fsrc, open(website_path, 'wb') as fdst:
                        fdst.write(fsrc.read())
                    print(f"  -> Successfully downloaded ({os.path.getsize(local_path)} bytes) from {img_url[:60]}")
                    downloaded_count += 1
                else:
                    print(f"  -> Download rejected (too small) from {img_url[:60]}")
            except Exception as e:
                print(f"  -> Download failed: {e}")
        else:
            print(f"  -> No image found for {query}")
        time.sleep(0.3)  # Gentle rate limiting
    else:
        # ensure file also in website public
        if not os.path.exists(website_path):
            with open(local_path, 'rb') as fsrc, open(website_path, 'wb') as fdst:
                fdst.write(fsrc.read())

    # Attach to Product in database
    if os.path.exists(local_path) and os.path.getsize(local_path) > 3000:
        # Check if ProductImage already exists
        pimg = ProductImage.objects.filter(product=p, image_url=media_url).first()
        if not pimg:
            # Set other images to non-main
            p.images.update(is_main=False)
            ProductImage.objects.create(
                product=p,
                image_url=media_url,
                alt_text=f"{p.name} - {p.reference}",
                is_main=True,
                sort_order=0
            )
        else:
            if not pimg.is_main:
                p.images.update(is_main=False)
                pimg.is_main = True
                pimg.save()

print(f"\n==========================================")
print(f"DONE! Processed {matched_count} targeted CCTV items. Newly downloaded: {downloaded_count}.")
print(f"==========================================")
