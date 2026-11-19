import urllib.request, urllib.parse, re, ssl, html as H
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
for q in ['Acer Aspire laptop', 'HDMI extender KVM 60m', 'armoire rack reseau 6U']:
    u = 'https://www.bing.com/images/async?q=' + urllib.parse.quote(q) + '&first=0&count=20&mmasync=1'
    h = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': UA, 'Accept-Language': 'fr-FR'}), context=ctx, timeout=12).read().decode('utf-8', 'ignore')
    ms = re.findall(r'murl&quot;:&quot;(https?://.+?)&quot;', h)
    ts = re.findall(r't&quot;:&quot;(.+?)&quot;', h)
    print(q, len(h), len(ms))
    for m, t in list(zip(ms, ts))[:5]:
        print('   ', m[:90], '|', H.unescape(t)[:50])
