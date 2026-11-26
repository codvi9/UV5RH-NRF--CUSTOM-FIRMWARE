d = open("baofeng-uv5rh-fw/dump/fw/5RH_AT1846S_V0.07_FangtiBlueBG_230918-1.bin","rb").read()
i = 0
while True:
    j = d.find(b"FM ", i)
    if j < 0: break
    lo = max(0, j-24); hi = min(len(d), j+40)
    seg = d[lo:hi]
    txt = "".join(chr(c) if 32 <= c < 127 else "." for c in seg)
    print(hex(0x08001000+j), txt)
    i = j+1
print("---- nearby strings ----")
import re
for m in re.finditer(rb"[ -~]{5,}", d):
    t = m.group().decode()
    if "FM" in t or "RADIO" in t.upper() or "87" in t:
        print(hex(0x08001000+m.start()), t)
