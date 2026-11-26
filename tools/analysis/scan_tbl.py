import sys
sys.path.insert(0, "baofeng-uv5rh-fw/tools")
img = open("baofeng-uv5rh-fw/dump/fw/5RH_NRF_Fangti_V0.14_231124-1.bin","rb").read()
print("size", len(img))
pats = {
  "RXAGC1 0x13=0x03DF": bytes([0x13,0x03,0xDF]),
  "POWER 0x37=0x9D1F": bytes([0x37,0x9D,0x1F]),
  "AF_OUT 0x47=0x6140": bytes([0x47,0x61,0x40]),
  "VOL 0x48=0x33A8": bytes([0x48,0x33,0xA8]),
}
for name, p in pats.items():
    hits = []
    i = img.find(p)
    while i != -1:
        hits.append(i); i = img.find(p, i+1)
    print(name, "hits:", [hex(h) for h in hits[:6]])
    for h in hits[:2]:
        lo = max(0, h-24); hi = min(len(img), h+40)
        print("   ctx @%06x: %s" % (h, img[lo:hi].hex(" ")))
