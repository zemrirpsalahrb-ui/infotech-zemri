"""Recherche web (Bing Images) et telecharge une vraie photo pour chaque produit sans photo locale.
Ne touche PAS a MariaDB : seulement la base du site (db.sqlite3 / Neon) + dossier media.
"""
import os, sys, re, ssl, urllib.request, urllib.parse, html as htmllib
from concurrent.futures import ThreadPoolExecutor

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cctv_backend.settings')
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import django
django.setup()
from django.db.models import Q
from api.models import Product, ProductImage

ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
MEDIA_DIR = os.path.join(BASE, 'media', 'products')
WEB_DIR = os.path.abspath(os.path.join(BASE, '..', 'WEBSITE', 'public', 'products'))
os.makedirs(MEDIA_DIR, exist_ok=True); os.makedirs(WEB_DIR, exist_ok=True)
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'

SKIP_WORDS = ["MAIN D'OEUVRE", 'AUTORISATION', 'CREDIT', 'REPARATION', 'PNEU', 'DEMO CRISTOR']
REPL = [
    (r'\bDISQUE DURE\b', 'disque dur'), (r'\bCOXIAL\b', 'coaxial'), (r'\bARMOIRE\b', 'armoire rack reseau'),
    (r'^KX7\b', 'cable coaxial KX7'), (r'^SUPPORT\b', 'support camera surveillance'),
    (r'^DISCRET\b', 'mini camera espion'), (r'^JONCTION\b', 'boite de jonction camera'),
    (r'\bTONNER\b', 'toner'), (r'\bSACOUCHE\b', 'sacoche ordinateur'), (r'\bBAFF?E\b', 'haut-parleur'),
    (r'\bENDULEUR\b', 'onduleur'), (r'\bONDULAIRE\b', 'onduleur'), (r'\bESTIQUEUR\b', 'autocollant'),
    (r'^STICKER CLAVIER', 'autocollant clavier'), (r'^STYLE\b', 'stylet'), (r'^DALLE\b', 'ecran laptop dalle'),
    (r'\bTAPI SOURIS\b', 'tapis de souris'), (r'^PATTE\b', 'pate thermique'), (r'^POULPOU 4S', 'cable splitter alimentation camera 4 sorties'),
    (r'^SPLITER\b', 'splitter alimentation camera 12V'), (r'\bBATTRIE\b', 'batterie'), (r'\bANTI VERUS\b', 'antivirus'),
    (r'\bNORTAN\b', 'norton'), (r'\bIMPRIMENTE\b', 'imprimante'), (r'\bIMPRIMENT\b', 'imprimante'), (r'\bBARACODE\b', 'lecteur code barre'),
    (r'\bCONTEUSE DE BILLET\b', 'compteuse de billets'), (r'^RAM PAPIER', 'rame papier A4'), (r'^TAG BLEU', 'badge RFID bleu porte-cle'),
    (r'\bAIR PODE\b', 'airpods'), (r'\bALIMENTTION\b', 'alimentation'), (r'\bENRIGISTEREUR\b', 'enregistreur'),
    (r'\bEXTENTION\b', 'extension'), (r'\bAMPLIEFIER\b', 'amplificateur'), (r'\bMACKBOOK\b', 'macbook'), (r'\bICLOUDE\b', ''),
    (r'\bCCLAVIER\b', 'clavier'), (r'\bSTANDARE\b', 'standard'), (r'\bHAWAWI\b', 'huawei'), (r'\bAPPELE\b', 'apple pencil'),
    (r'^ARD|^ARM', lambda m: 'Dahua ' + m.group(0)), (r'^B3A51P', 'Dahua HAC-B3A51P'), (r'^HERO A1', 'Imou Hero A1 2MP'),
    (r'\bPOINTEUSE\b', 'pointeuse'), (r'\bRIDEAU\b', 'volet roulant'), (r'^ILS AJAX', 'Ajax DoorProtect'),
    (r'^CABLE RESEAU', 'cable reseau RJ45'), (r'^FICHE RESEAU RG 45', 'connecteur RJ45'), (r'^RG 45', 'RJ45'),
    (r'\bPROJECTEUR SOLAIR\b', 'projecteur solaire LED'), (r'\bPRISE ANGLAISE\b', 'adaptateur prise anglaise'),
]
HINT = {'CHARGEUR': ' chargeur', 'ACER': ' laptop', 'DELL': ' laptop', 'HP ': ' laptop', 'LENOVO': ' laptop', 'ASUS': ' laptop', 'MSI': ' laptop'}

def build_query(name):
    q = re.sub(r'\s+', ' ', name).strip()
    for pat, rep in REPL:
        q = re.sub(pat, rep, q, flags=re.I)
    return q.strip()

def bing_candidates(query):
    url = 'https://www.bing.com/images/search?q=' + urllib.parse.quote(query) + '&first=1&qft=+filterui:imagesize-medium'
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'fr-FR,fr;q=0.9'})
    with urllib.request.urlopen(req, context=ctx, timeout=12) as r:
        h = r.read().decode('utf-8', errors='ignore')
    out = []
    for m in re.findall(r'murl&quot;:&quot;(https?://.+?)&quot;', h):
        m = htmllib.unescape(m)
        low = m.lower()
        if any(b in low for b in ['logo', 'flag', 'banner', 'icon', '.svg', '.gif']):
            continue
        out.append(m)
    return out[:8]

def valid_image(data):
    return len(data) > 6000 and (data[:3] == b'\xff\xd8\xff' or data[:8] == b'\x89PNG\r\n\x1a\n' or (data[:4] == b'RIFF' and data[8:12] == b'WEBP'))

def download(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'image/avif,image/webp,image/*,*/*;q=0.8', 'Referer': 'https://www.bing.com/'})
    with urllib.request.urlopen(req, context=ctx, timeout=12) as r:
        return r.read(4_000_000)

def process(p):
    q = build_query(p.name)
    try:
        cands = bing_candidates(q)
    except Exception as e:
        return (p, None, f'search fail {e}')
    for c in cands:
        try:
            data = download(c)
        except Exception:
            continue
        if not valid_image(data):
            continue
        ext = '.png' if data[:4] == b'\x89PNG' else ('.webp' if data[:4] == b'RIFF' else '.jpg')
        fn = f'p{p.id}-{p.slug or p.id}'[:80] + ext
        for d in (MEDIA_DIR, WEB_DIR):
            with open(os.path.join(d, fn), 'wb') as f:
                f.write(data)
        return (p, fn, f'{q} <- {c[:70]}')
    return (p, None, f'no valid image for "{q}"')

def main():
    local = ProductImage.objects.filter(image_url__startswith='/media/').values_list('product_id', flat=True)
    todo = [p for p in Product.objects.exclude(id__in=list(local))
            if not any(w in p.name.upper() for w in SKIP_WORDS)]
    if len(sys.argv) > 1:
        todo = todo[:int(sys.argv[1])]
    print('A traiter:', len(todo))
    ok = fail = 0
    with ThreadPoolExecutor(max_workers=6) as ex:
        for p, fn, info in ex.map(process, todo):
            if fn:
                ok += 1
                url = '/media/products/' + fn
                p.images.update(is_main=False, sort_order=1)
                ProductImage.objects.update_or_create(product=p, image_url=url,
                    defaults={'alt_text': p.name, 'is_main': True, 'sort_order': 0})
                print(f'OK  [{p.id}] {p.name} :: {info}')
            else:
                fail += 1
                print(f'--  [{p.id}] {p.name} :: {info}')
    print(f'\nTermine: {ok} photos ajoutees, {fail} non trouvees')

if __name__ == '__main__':
    main()

