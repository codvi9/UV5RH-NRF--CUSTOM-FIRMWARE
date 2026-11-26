import re
d = open("baofeng-uv5rh-fw/dump/factory_memory.img","rb").read()
print("size", len(d))
strs = [(m.start(), m.group().decode()) for m in re.finditer(rb"[ -~]{4,}", d)]
for off, s in strs[:80]:
    print("%06x  %s" % (off, s))
print("--- keyword hits ---")
for kw in (b"5RH", b"NRF", b"YP0", b"BK", b"0.2", b"V01"):
    idx = [i for i in range(len(d)) if d.startswith(kw, i)][:6]
    print(kw.decode(), [hex(i) for i in idx])
