from capstone import *
img = open("baofeng-uv5rh-fw/dump/fw/5RH_NRF_Fangti_V0.14_231124-1.bin","rb").read()
base = 0x08001000
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS)
lo, hi = 0x0800b220, 0x0800b2c0
print("=== code around 0xBFF1")
for ins in md.disasm(img[lo-base:hi-base], lo):
    print("  %08x  %-8s %s" % (ins.address, ins.mnemonic, ins.op_str))
print()
for pat, name in [(b"\x40\x60", "0x6040"), (b"\x47\x20", "movs r0,#0x47"), (b"\x47\x21", "movs r1,#0x47")]:
    hits=[]; i=img.find(pat)
    while i!=-1:
        hits.append(i); i=img.find(pat,i+1)
    print(name, len(hits), [hex(base+h) for h in hits[:8]])
