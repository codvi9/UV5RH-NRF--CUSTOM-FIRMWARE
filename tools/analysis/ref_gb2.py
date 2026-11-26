d = open("baofeng-uv5rh-fw/ref/Dondji.fusion.bin","rb").read()
out = []
i = 0
n = len(d)
while i < n-1:
    if 0xA1 <= d[i] <= 0xF7 and 0xA1 <= d[i+1] <= 0xFE:
        s = bytearray(); j = i
        while j < n-1 and 0xA1 <= d[j] <= 0xF7 and 0xA1 <= d[j+1] <= 0xFE:
            s += d[j:j+2]; j += 2
        if len(s) >= 4:
            try:
                out.append("%06x %s" % (i, s.decode("gb2312")))
            except Exception:
                pass
        i = j
    else:
        i += 1
open("baofeng-uv5rh-fw/ref/strings.txt","w",encoding="utf-8").write("\n".join(out))
print("runs", len(out))
