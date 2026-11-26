import struct
d = open("baofeng-uv5rh-fw/dump/fw/5RH_NRF_V0.13_231121-1.bin","rb").read()
base = 0x08001000
for reg in (0x74,0x44,0x45,0x48,0x47,0x28,0x29,0x78,0x0C):
    b = struct.pack("<H", 0x2000|reg)
    addrs=[]; i=0
    while True:
        j=d.find(b,i)
        if j<0: break
        addrs.append(base+j); i=j+1
    print("reg 0x%02X: %d hits %s" % (reg, len(addrs), [hex(a) for a in addrs[:6]]))
