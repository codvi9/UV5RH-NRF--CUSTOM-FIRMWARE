img = open("baofeng-uv5rh-fw/dump/fw/5RH_NRF_Fangti_V0.14_231124-1.bin","rb").read()
base = 0x08001000
for pat, name in [(b"\xf1\xbf", "0xBFF1"), (b"\x28\x30", "0x3028"), (b"\x40\x61", "0x6140"), (b"\x9f\x81", "0x819F")]:
    hits = []
    i = img.find(pat)
    while i != -1:
        hits.append(i); i = img.find(pat, i+1)
    print(name, "hits:", len(hits), [hex(base+h) for h in hits[:10]])
    for h in hits[:3]:
        lo = max(0,h-8); hi = min(len(img),h+12)
        print("    @%08x ctx %s" % (base+h, img[lo:hi].hex(" ")))
