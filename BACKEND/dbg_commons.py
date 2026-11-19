import urllib.request, urllib.parse, json, ssl
ctx = ssl._create_unverified_context()
UA = 'LogiszCatalogBot/1.0 (shop catalog; contact: admin@localhost) python-urllib'
def commons(term):
    u = ('https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search&gsrnamespace=6&gsrlimit=8'
         '&gsrsearch=' + urllib.parse.quote(term + ' filetype:bitmap') + '&prop=imageinfo&iiprop=url|mime|size&iiurlwidth=900')
    j = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': UA}), context=ctx, timeout=15).read())
    pages = sorted(j.get('query', {}).get('pages', {}).values(), key=lambda p: p.get('index', 99))
    return [(p['title'][:60], p['imageinfo'][0].get('thumburl')) for p in pages if p.get('imageinfo')]
for t in ['Acer laptop', 'HDMI extender', '19-inch rack cabinet', 'USB flash drive', 'coaxial cable RG59']:
    print(t)
    for x in commons(t)[:4]: print('   ', x)
