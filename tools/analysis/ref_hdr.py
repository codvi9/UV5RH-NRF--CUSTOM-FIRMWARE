import math, collections
d = open("baofeng-uv5rh-fw/ref/Dondji.fusion.bin","rb").read()
print("size", len(d))
print("head:", d[:64].hex(" "))
print("tail:", d[-32:].hex(" "))
# entropy of first 4KB
b = d[:4096]
cnt = collections.Counter(b)
ent = -sum((c/len(b))*math.log2(c/len(b)) for c in cnt.values())
print("entropy first 4K: %.2f" % ent)
# look for a plausible vector table
import struct
for off in (0, 0x1000, 0x2000):
    sp, rst = struct.unpack_from("<II", d, off)
    print("off %#x: sp=%08x rst=%08x" % (off, sp, rst))
