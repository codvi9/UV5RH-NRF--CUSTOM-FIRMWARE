import struct
d = open("baofeng-uv5rh-fw/dump/fw/5RH_NRF_V0.13_231121-1.bin","rb").read()
base = 0x08001000
def f16(v):
    out=[];i=0;b=struct.pack("<H",v)
    while True:
        j=d.find(b,i)
        if j<0: break
        out.append(base+j);i=j+1
    return out
def f32(v):
    out=[];i=0;b=struct.pack("<I",v)
    while True:
        j=d.find(b,i)
        if j<0: break
        out.append(base+j);i=j+1
    return out
for v,n in [(0xC001,"RDA 0xC001"),(0xC00D,"RDA 0xC00D"),(0x88AF,"RDA 0x88AF"),(0x8800,"0x8800"),(0xC011,"RDA 0xC011"),(0x0002,"2")]:
    print("%-12s %s" % (n, [hex(x) for x in f16(v)][:5]))
for v,n in [(0x40005400,"I2C1"),(0x40005800,"I2C2"),(0x40013800,"USART1"),(0x40004400,"USART2"),(0x48000000,"GPIOA32")]:
    print("%-12s %s" % (n, [hex(x) for x in f32(v)][:5]))
# PC15 mask 0x8000 16-bit, and 0x21 byte
print("byte 0x21 count", d.count(b"\x21"))
