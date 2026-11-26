import struct, collections, os
p1 = "baofeng-uv5rh-fw/dump/fw/5RH_NRF_V0.13_231121-1.bin"
p2 = "baofeng-uv5rh-fw/dump/fw/5RH_NRF_V0.13_231121-2.bin"
d = open(p1,"rb").read(); c = open(p2,"rb").read()
print("region1", len(d), "region2", len(c))
sp, rst = struct.unpack_from("<II", d, 0)
print("SP=%08x  RESET=%08x" % (sp, rst))
print("tail of r1:", d[-32:].hex(" "))
print("r2 head:", c[:32].hex(" "))
# ASCII strings
import re
s = re.findall(rb"[ -~]{4,}", d)
uniq = []
seen = set()
for x in s:
    t = x.decode("ascii", "ignore")
    if t not in seen:
        seen.add(t); uniq.append(t)
print("ascii strings:", len(s), "unique:", len(uniq))
for t in uniq[:60]:
    print("  ", t)
