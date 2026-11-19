"""Photos reelles libres (Wikimedia Commons API officielle) pour les produits sans photo locale.
Une photo par TYPE de produit (cable HDMI, flash disk, onduleur...). Ne touche PAS MariaDB.
Usage: python fetch_photos_commons.py [--dry]
"""
import os, sys, re, ssl, json, urllib.request, urllib.parse

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cctv_backend.settings')
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import django
django.setup()
from api.models import Product, ProductImage

# horloge PC decalee -> certificats vus "expires" : lecture publique d'images uniquement
ctx = ssl._create_unverified_context()
UA = 'LogiszCatalog/1.0 (catalogue boutique; python-urllib)'
MEDIA_DIR = os.path.join(BASE, 'media', 'products')
WEB_DIR = os.path.abspath(os.path.join(BASE, '..', 'WEBSITE', 'public', 'products'))
DRY = '--dry' in sys.argv

SKIP = ["MAIN D'OEUVRE", 'AUTORISATION', 'CREDIT', 'REPARATION', 'PNEU', 'DEMO CRISTOR']

# (regex sur le nom en MAJUSCULE, terme Commons, slug fichier)
RULES = [
    (r'MAC ?K?BOOK|CARCASSE MACBOOK', 'MacBook Pro laptop', 'macbook'),
    (r'IMAC|MAG ?SAFE', 'Apple MagSafe power adapter', 'magsafe'),
    (r'IPHONE', 'iPhone 13 Pro', 'iphone'),
    (r'AIR ?POD', 'Apple AirPods', 'airpods'),
    (r'STYLE APPELE', 'Apple Pencil', 'apple-pencil'),
    (r'^STYLE', 'stylus pen tablet', 'stylet'),
    (r'CLAVIER APPLE|CLAVIER SOURIS APPLE', 'Apple Magic Keyboard', 'apple-keyboard'),
    (r'\b(ACER|ASUS|DELL|HP|LENOVO|MSI|THINKPAD)\b.*(I[3579]|CELERON|RAYZEN|RYZEN|AMD|OMEN)|THINKPAD', 'laptop computer notebook', 'laptop'),
    (r'CHARGEUR.*(TYPE C|APPLE|SURFACE|HAWAWI|ORIGINAL|GAMER|STANDARE|UNIVERSEL 19V)', 'laptop AC adapter charger', 'chargeur-laptop'),
    (r'CHARGEUR 12V|CHARGEUR UNIVERSEL|CHARGEUR 5V|^ALIMENTATION', '12V power adapter', 'adaptateur-12v'),
    (r'BLOC ALIMENTATION POUR PC', 'ATX power supply', 'alim-pc'),
    (r'BLOC ALIMENTTION|BATTERIE 12V|BATTRIE$|^BATTERIE', 'sealed lead acid battery 12V', 'batterie-12v'),
    (r'BATTRIE YOGA', 'laptop battery', 'batterie-laptop'),
    (r'ONDUL|ENDULEUR', 'uninterruptible power supply UPS', 'onduleur'),
    (r'MULTIPRISE|BANDEAU D\'ALIMENTATION', 'power strip', 'multiprise'),
    (r'PRISE ANGLAISE', 'travel plug adapter', 'adaptateur-prise'),
    (r'TUYA PRISE', 'smart plug', 'prise-connectee'),
    (r'TUYA RIDEAU|RELAIS RIDEAU', 'smart switch wall', 'interrupteur-smart'),
    (r'ARMOIRE|ETAGERE ARMOIRE', '19-inch rack cabinet network', 'armoire-rack'),
    (r'PANNEAU DE BRASSAGE', 'patch panel', 'patch-panel'),
    (r'SWITCH|POE', 'network switch ethernet ports', 'switch'),
    (r'ROUTEUR|MODEM|EXTENDER|POINT D\'ACC|AX3000|AC1300|WIFI ALPHA|CLE WIFI|RESEAU USB', 'wireless router', 'routeur-wifi'),
    (r'FIBRE OPTIQUE', 'fiber optic patch cable', 'fibre'),
    (r'KX7|COXIAL', 'coaxial cable RG59', 'coaxial'),
    (r'CABLE RESEAU|CAT ?7|RG 45|FICHE RESEAU', 'Ethernet cable RJ45', 'cable-reseau'),
    (r'RJ11|TELEPHONE FIXE', 'telephone', 'telephone'),
    (r'HDMI WIRLESS', 'wireless HDMI transmitter', 'hdmi-wireless'),
    (r'KVM|HDMI EXTENDER', 'HDMI extender', 'hdmi-extender'),
    (r'HDMI TO VGA|VGA TO HDMI|DISPLAY ?PORT|USB TO HDMI|HDMI TO 2', 'HDMI to VGA adapter', 'convertisseur-video'),
    (r'HDMI', 'HDMI cable', 'hdmi'),
    (r'VGA', 'VGA cable', 'vga'),
    (r'TYPE C \d+ IN|HUB USB', 'USB-C hub', 'hub-usbc'),
    (r'TYPE C|OTG|ADAPTATEUR', 'USB-C adapter', 'usbc'),
    (r'USB 3.0 TO SATA|RACK 2.5|RACK NVME|POCHETTE DISQUE', 'hard disk enclosure USB', 'boitier-disque'),
    (r'CABLE (EXTENSION|EXTENTION|USB|EXTENSION USB)|CABLE extension usb', 'USB extension cable', 'rallonge-usb'),
    (r'CABLE IMPRIM', 'USB printer cable', 'cable-imprimante'),
    (r'CABLE (ALIMENTATION|SECTEUR|TREFLE|ONDULEUR)|cable secteur', 'IEC power cord', 'cordon-alim'),
    (r'CABLE DISQUE|NAPPE SATA|CABLE DVR SATA', 'SATA cable', 'sata'),
    (r'CABLE DVR ALIMENTATION|POULPOU|SPLITER', 'DC power splitter cable', 'splitter-dc'),
    (r'AUDIO JACK|CARTE SON', 'USB sound card', 'audio'),
    (r'SSD|NVME|M2|512 MAX', 'solid-state drive SSD', 'ssd'),
    (r'FLASH DISK', 'USB flash drive', 'flash-disk'),
    (r'CARTE MEMOIRE', 'microSD card', 'microsd'),
    (r'RAM POUR PC', 'DDR4 RAM module', 'ram'),
    (r'CARTE GRAPHIQUE', 'graphics card GT 730', 'gpu'),
    (r'CARTE MERE', 'motherboard', 'carte-mere'),
    (r'VENTILO', 'CPU cooler fan', 'ventilo'),
    (r'PATTE', 'thermal paste', 'pate-thermique'),
    (r'DALLE|ECRAN|ecran', 'computer monitor', 'ecran'),
    (r'CLAVIER|STICKER|ESTIQUEUR', 'computer keyboard', 'clavier'),
    (r'SOURIS', 'computer mouse wireless', 'souris'),
    (r'TAPI', 'mouse pad', 'tapis-souris'),
    (r'CASQUE|ECOUTEUR', 'headset headphones', 'casque'),
    (r'BAFE|BAFFE', 'computer speakers', 'haut-parleur'),
    (r'SACOUCHE|CARTABLE', 'laptop bag', 'sacoche'),
    (r'TONNER', 'toner cartridge', 'toner'),
    (r'BOUTEILLE D\'ENCRE|PACK (EPSON|CANON|BROTHER)', 'ink cartridge printer', 'encre'),
    (r'XPRINTER', 'thermal receipt printer', 'imprimante-ticket'),
    (r'BARACODE', 'barcode scanner', 'code-barre'),
    (r'CONTEUSE DE BILLET', 'banknote counter', 'compteuse'),
    (r'DATASHOW', 'video projector', 'datashow'),
    (r'TV +BOX', 'Android TV box', 'tv-box'),
    (r'ANTI VERUS|LICENCE WINDOWS|CD GRAVE|DVD', 'DVD disc', 'logiciel'),
    (r'DVD EXTERIEUR', 'external DVD drive', 'dvd-ext'),
    (r'PILE 2032', 'CR2032 battery', 'pile'),
    (r'RAM PAPIER', 'A4 paper ream', 'papier'),
    (r'TOURNE VIS', 'screwdriver set', 'tournevis'),
    (r'ENDOSCOPE', 'inspection camera endoscope', 'endoscope'),
    (r'GPS|TAG', 'GPS tracker', 'gps'),
    (r'tag bleu|TAG BLEU', 'RFID key fob', 'badge-rfid'),
    (r'ENRIGISTEREUR AUDIO', 'digital voice recorder', 'dictaphone'),
    (r'DISCRET', 'hidden camera', 'camera-cachee'),
    (r'AJAX|ALARME|DETECTEUR|ILS', 'burglar alarm motion sensor', 'alarme'),
    (r'ARD|ARM7012', 'wireless alarm sensor', 'alarme-sans-fil'),
    (r'POINTEUSE|ZK ', 'time clock face recognition terminal', 'pointeuse'),
    (r'KIT VIDEO|VIDEO PHONE|ecran video', 'video intercom door phone', 'interphone'),
    (r'PROJECTEUR SOLAIR', 'solar LED floodlight', 'projecteur-solaire'),
    (r'JONCTION', 'CCTV camera junction box', 'boite-jonction'),
    (r'^SUPPORT|SUPPORT L', 'TV wall mount bracket', 'support'),
    (r'HIKVISION|B3A51P|HERO A1|PICOO|CAMERA', 'CCTV camera', 'camera-cctv'),
    (r'BATTRIE', 'battery', 'batterie'),
    (r'GPS', 'GPS tracker', 'gps'),
]

_cache = {}
CHOICE_FILE = os.path.join(BASE, 'commons_choices.json')
CHOICES = json.load(open(CHOICE_FILE, encoding='utf-8')) if os.path.exists(CHOICE_FILE) else {}

def api_get(url):
    import time
    for attempt in range(6):
        time.sleep(1.5)
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), context=ctx, timeout=30).read()
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = int(e.headers.get('Retry-After') or 20)
                print(f'     (limite de debit, pause {wait}s)')
                time.sleep(wait)
                continue
            raise
    raise RuntimeError('trop de 429')

def commons_first(term):
    if term in _cache:
        return _cache[term]
    if term in CHOICES:  # fichier choisi a la main
        u = ('https://commons.wikimedia.org/w/api.php?action=query&format=json&prop=imageinfo&iiprop=url|mime|size&iiurlwidth=900&titles='
             + urllib.parse.quote(CHOICES[term]))
        pages = list(json.loads(api_get(u)).get('query', {}).get('pages', {}).values())
        if pages and pages[0].get('imageinfo'):
            ii = pages[0]['imageinfo'][0]
            _cache[term] = (pages[0]['title'], ii.get('thumburl') or ii['url'], ii.get('descriptionurl'))
            return _cache[term]
    u = ('https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search&gsrnamespace=6&gsrlimit=10'
         '&gsrsearch=' + urllib.parse.quote(term + ' filetype:bitmap') + '&prop=imageinfo&iiprop=url|mime|size&iiurlwidth=900')
    j = json.loads(api_get(u))
    pages = sorted(j.get('query', {}).get('pages', {}).values(), key=lambda p: p.get('index', 99))
    res = None
    for p in pages:
        ii = (p.get('imageinfo') or [{}])[0]
        if ii.get('mime') in ('image/jpeg', 'image/png') and ii.get('width', 0) >= 400 and ii.get('thumburl'):
            res = (p['title'], ii['thumburl'], ii.get('descriptionurl'))
            break
    _cache[term] = res
    return res

def survey():
    """Liste 10 candidats par terme -> commons_survey.json (pour choisir a la main)."""
    out = {}
    for _, term, slug in RULES:
        if term in out: continue
        u = ('https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search&gsrnamespace=6&gsrlimit=12'
             '&gsrsearch=' + urllib.parse.quote(term + ' filetype:bitmap') + '&prop=imageinfo&iiprop=mime|size')
        pages = sorted(json.loads(api_get(u)).get('query', {}).get('pages', {}).values(), key=lambda p: p.get('index', 99))
        out[term] = [p['title'] for p in pages if p.get('imageinfo') and p['imageinfo'][0].get('mime') in ('image/jpeg', 'image/png') and p['imageinfo'][0].get('width', 0) >= 500]
        print(term, '->', len(out[term]), flush=True)
        json.dump(out, open(os.path.join(BASE, 'commons_survey.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

def download(url, path):
    data = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), context=ctx, timeout=30).read()
    if len(data) < 5000:
        raise ValueError('trop petit')
    for d in (MEDIA_DIR, WEB_DIR):
        with open(os.path.join(d, path), 'wb') as f:
            f.write(data)

def main():
    os.makedirs(MEDIA_DIR, exist_ok=True); os.makedirs(WEB_DIR, exist_ok=True)
    local_ids = set(ProductImage.objects.filter(image_url__startswith='/media/').values_list('product_id', flat=True))
    todo = [p for p in Product.objects.order_by('name') if p.id not in local_ids and not any(w in p.name.upper() for w in SKIP)]
    print('Produits sans photo locale:', len(todo))
    done_files = {}
    ok = miss = 0
    for p in todo:
        up = p.name.upper()
        rule = next(((t, s) for rx, t, s in RULES if re.search(rx, up, flags=re.I)), None)
        if not rule:
            print('  ?? pas de regle:', p.id, p.name); miss += 1; continue
        term, slug = rule
        if slug not in done_files:
            hit = commons_first(term)
            if not hit:
                print('  !! aucun resultat Commons pour', term); done_files[slug] = None
            else:
                title, thumb, desc = hit
                ext = '.png' if thumb.lower().split('?')[0].endswith('.png') else '.jpg'
                fn = f'type-{slug}{ext}'
                print(f'  [{slug}] {term} -> {title}')
                if not DRY:
                    try:
                        download(thumb, fn); done_files[slug] = fn
                    except Exception as e:
                        print('     download KO', e); done_files[slug] = None
                else:
                    done_files[slug] = fn
        fn = done_files.get(slug)
        if not fn:
            miss += 1; continue
        ok += 1
        if not DRY:
            url = '/media/products/' + fn
            p.images.update(is_main=False, sort_order=1)
            ProductImage.objects.update_or_create(product=p, image_url=url,
                defaults={'alt_text': p.name, 'is_main': True, 'sort_order': 0})
    print(f'\nTermine: {ok} produits avec photo, {miss} sans.')

if __name__ == '__main__':
    survey() if '--survey' in sys.argv else main()
