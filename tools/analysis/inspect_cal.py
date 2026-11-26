import os, math, collections
p = r"C:\Users\Administrator\Downloads\calibration.dat"
print("exists", os.path.exists(p), "size", os.path.getsize(p) if os.path.exists(p) else -1)
if os.path.exists(p):
    d = open(p,"rb").read()
    print("head:", d[:48].hex(" "))
    print("ascii:", "".join(chr(b) if 32 <= b < 127 else "." for b in d[:64]))
    b = d[:4096]; c = collections.Counter(b)
    ent = -sum((v/len(b))*math.log2(v/len(b)) for v in c.values())
    print("entropy %.2f" % ent)
