import sys, struct
sys.path.insert(0, "baofeng-uv5rh-fw/tools")
import bf_tool
src = "baofeng-uv5rh-fw/dump/fw/5RH_NRF_Fangti_V0.14_231124-1.bin"
d = open(src,"rb").read()
b = bf_tool.pack1(d)
out = "baofeng-uv5rh-fw/fw/restore_nrf_v0.14.BF"
open(out,"wb").write(b)
c,l1,l2 = struct.unpack(">BLL", b[:9])
print("src", len(d), "-> ", out, len(b))
print("count", c, "len1", l1, "len2", l2, "vector", d[:8].hex(), "checks", d[3]==0x20, d[7]==0x08)
