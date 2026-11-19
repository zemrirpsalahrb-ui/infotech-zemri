import urllib.request, urllib.parse, re, json, ssl
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
def ddg(q):
    r = urllib.request.urlopen(urllib.request.Request('https://duckduckgo.com/?q=' + urllib.parse.quote(q) + '&iax=images&ia=images', headers={'User-Agent': UA}), context=ctx, timeout=12).read().decode('utf-8', 'ignore')
    m = re.search(r'vqd=["\']?([\d-]+)', r)
    print('vqd', m and m.group(1))
    if not m: return []
    u = 'https://duckduckgo.com/i.js?l=fr-fr&o=json&q=' + urllib.parse.quote(q) + '&vqd=' + m.group(1) + '&f=,,,&p=1'
    j = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': UA, 'Referer': 'https://duckduckgo.com/'}), context=ctx, timeout=12).read())
    return [(x['image'], x.get('title', '')[:50]) for x in j.get('results', [])[:5]]
for q in ['Acer laptop i5 12th gen', 'KVM HDMI extender 60m', 'cable coaxial KX7 100m', 'Dahua ARD323-W2']:
    try:
        print(q, ddg(q))
    except Exception as e:
        print(q, 'ERR', e)

