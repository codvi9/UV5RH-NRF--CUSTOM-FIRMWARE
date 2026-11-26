import struct, re
d = open("baofeng-uv5rh-fw/dump/fw/5RH_NRF_V0.13_231121-1.bin","rb").read()
base = 0x08001000
asm = open("baofeng-uv5rh-fw/dump/stock.asm", encoding="utf-8", errors="ignore").read().splitlines()
def pool_hits(val, name):
    b = struct.pack("<I", val)
    addrs = []
    i = 0
    while True:
        j = d.find(b, i)
        if j < 0: break
        if j % 4 == 0: addrs.append(base + j)
        i = j + 1
    print("%s 0x%08x -> pool addrs: %s" % (name, val, [hex(a) for a in addrs[:6]]))
    for a in addrs[:4]:
        pat = "@ (0x%x)" % a
        refs = [ln for ln in asm if pat in ln][:6]
        for r in refs: print("     ", r.strip())
for v, n in [(0x48000000,"GPIOA"),(0x48000400,"GPIOB"),(0x48000800,"GPIOC"),(0x48001400,"GPIOF"),(0x000001FF,"MASK_1FF"),(0x40021000,"CRM")]:
    pool_hits(v, n)
print("== movs immediates of interest ==")
for op, name in [(0x2067,"0x67"),(0x2078,"0x78"),(0x2038,"0x38"),(0x2039,"0x39"),(0x2030,"0x30"),(0x2040,"0x40"),(0x2047,"0x47")]:
    b = struct.pack("<H", op)
    addrs = []
    i = 0
    while True:
        j = d.find(b, i)
        if j < 0: break
        addrs.append(base + j); i = j + 1
    print("%s movs -> %d hits %s" % (name, len(addrs), [hex(a) for a in addrs[:8]]))
