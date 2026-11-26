import re
def runs(p):
    d = open(p,"rb").read()
    return d, sorted({m.group().decode("latin1") for m in re.finditer(rb"[ -~]{4,}", d)})
for p in ["baofeng-uv5rh-fw/dump/fw/5RH_BK_V0.14_231123-1.bin",
          "baofeng-uv5rh-fw/dump/fw/5RH_NRF_V0.13_231121-1.bin"]:
    d, s = runs(p)
    print("==", p, len(d), "strings:", len(s))
    for x in list(s)[:40]:
        print("   ", repr(x))
    print("   --- hits ---")
    for x in s:
        if any(k in x for k in ("5RH","NRF","BK","YP","V0.","Fangti")):
            print("   *", repr(x))
a = open("baofeng-uv5rh-fw/dump/fw/5RH_BK_V0.14_231123-1.bin","rb").read()
b = open("baofeng-uv5rh-fw/dump/fw/5RH_NRF_V0.13_231121-1.bin","rb").read()
n = min(len(a),len(b)); same = sum(1 for i in range(n) if a[i]==b[i])
print("BK vs NRF: %d/%d bytes identical (%.1f%%)" % (same, n, 100*same/n))
