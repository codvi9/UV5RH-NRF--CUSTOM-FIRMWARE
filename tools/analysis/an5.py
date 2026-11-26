import struct
d = open("baofeng-uv5rh-fw/dump/fw/5RH_NRF_V0.13_231121-1.bin","rb").read()
base = 0x08001000
def find16(v):
    out=[]; i=0; b=struct.pack("<H", v)
    while True:
        j=d.find(b,i)
        if j<0: break
        out.append(base+j); i=j+1
    return out
tests = [
 ("IF_SEL 0x2AAB (FM)", 0x2AAB),
 ("AF 0x6040 (mute)", 0x6040),
 ("AF 0x6140 (RX)", 0x6140),
 ("TX unmute 0x3B20", 0x3B20),
 ("DAC 0x0B40", 0x0B40),
 ("RX state 0xBFF1", 0xBFF1),
 ("TX state 0xC1FE", 0xC1FE),
 ("idle 0x0200", 0x0200),
 ("power 0x9D1F", 0x9D1F),
 ("AF filter 0xF50B", 0xF50B),
 ("0x9009", 0x9009),
 ("0x31A9", 0x31A9),
 ("AM vol 0xB3AA", 0xB3AA),
 ("AM AF 0x6740", 0x6740),
]
for name, v in tests:
    h = find16(v)
    print("%-24s %-6s hits=%-3d %s" % (name, hex(v), len(h), [hex(x) for x in h[:4]]))
