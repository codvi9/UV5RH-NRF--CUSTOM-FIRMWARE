import re
d = open("baofeng-uv5rh-fw/ref/Dondji.fusion.bin","rb").read()
out = []
i = 0
n = len(d)
while i < n-1:
    b1, b2 = d[i], d[i+1]
    if 0xA1 <= b1 <= 0xF7 and 0xA1 <= b2 <= 0xFE:
        s = bytearray()
        j = i
        while j < n-1 and 0xA1 <= d[j] <= 0xF7 and 0xA1 <= d[j+1] <= 0xFE:
            s += d[j:j+2]; j += 2
        if len(s) >= 4:
            try:
                t = s.decode("gb2312")
                out.append((i, t))
            except Exception:
                pass
        i = j
    else:
        i += 1
print("gb2312 runs:", len(out))
for off, t in out[:80]:
    print("%06x %s" % (off, t))
