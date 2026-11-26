import re
def strings(p, minlen=3):
    d = open(p,"rb").read()
    return d, [(m.start(), m.group().decode("latin1")) for m in re.finditer(rb"[ -~]{%d,}"%minlen, d)]
for tag, p in [("BK","baofeng-uv5rh-fw/dump/fw/5RH_BK_V0.14_231123-1.bin"),
               ("NRF","baofeng-uv5rh-fw/dump/fw/5RH_NRF_V0.13_231121-1.bin"),
               ("AT","baofeng-uv5rh-fw/dump/fw/5RH_AT1846S_V0.07_FangtiBlueBG_230918-1.bin")]:
    d, s = strings(p)
    print("==", tag, len(d))
    for off, x in s:
        if "%s" in x or "-YP" in x or "YP0" in x or "FD68" in x or x.strip() in ("BK","NRF","5RH"):
            print("   %06x %r" % (off, x))
    for kw in (b"FD6818", b"-YP", b"YP07", b"NRFB", b"5RH"):
        idx = [hex(i) for i in range(len(d)) if d.startswith(kw, i)][:5]
        if idx: print("   raw", kw, idx)
