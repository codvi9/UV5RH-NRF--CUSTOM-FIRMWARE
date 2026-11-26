import struct
d = open("baofeng-uv5rh-fw/dump/fw/5RH_NRF_V0.13_231121-1.bin","rb").read()
base = 0x08001000
def find(b):
    out=[]; i=0
    while True:
        j=d.find(b,i)
        if j<0: break
        out.append(j); i=j+1
    return out
for t in ["SQL","STEP","MENU","BAND","VOX","TONE","DUAL","SCAN","FREQ","CH-","MR","VFO","FM ","WIDE","NARR","POWER","BATT"]:
    hits=find(t.encode())
    print("%-6s %d %s" % (t, len(hits), [hex(base+h) for h in hits[:4]]))
print("---- 32-bit freq constants ----")
for v in [136000000,137000000,174000000,400000000,470000000,108000000,87500000,76000000,30000000,520000000]:
    b=struct.pack("<I",v); hits=find(b)
    print("%-10d %d %s" % (v, len(hits), [hex(base+h) for h in hits[:3]]))
print("---- vector table ----")
for i in range(0,0x80,4):
    v=struct.unpack_from("<I",d,i)[0]
    print("%02x %08x" % (i, v))
