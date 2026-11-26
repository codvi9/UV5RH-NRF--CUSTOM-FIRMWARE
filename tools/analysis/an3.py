import struct
d = open("baofeng-uv5rh-fw/dump/fw/5RH_NRF_V0.13_231121-1.bin","rb").read()
base = 0x08001000
def off(a): return a-base
def show(a0,a1):
    b=d[off(a0):off(a1)]
    out=[]
    cur=""
    for ch in b:
        if 32<=ch<127:
            cur+=chr(ch)
        else:
            if len(cur)>=3: out.append(cur)
            cur=""
    if len(cur)>=3: out.append(cur)
    return out
print("== menu strings 0x0800F000-0x0800F600 ==")
for s in show(0x0800F000,0x0800F600): print("  ", s)
print("== around CH-/VFO ==")
for s in show(0x080035C0,0x08003680): print("  ", s)
for s in show(0x0800D860,0x0800D8E0): print("  ", s)
print("== kHz constants ==")
def find(b):
    out=[]; i=0
    while True:
        j=d.find(b,i)
        if j<0: break
        out.append(j+base); i=j+1
    return out
for v in [136000,174000,400000,470000,108000,87500,76000,520000,1000000]:
    for fmt in ("<I","<H"):
        b=struct.pack(fmt, v)
        h=find(b)
        if h: print("  %-8d %-3s %d %s" % (v, fmt, len(h), [hex(x) for x in h[:3]]))
