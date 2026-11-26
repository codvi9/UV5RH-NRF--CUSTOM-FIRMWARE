from capstone import *
img = open("baofeng-uv5rh-fw/dump/fw/5RH_NRF_Fangti_V0.14_231124-1.bin","rb").read()
base = 0x08001000
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS)
for lo, hi in [(0x08009cb0, 0x08009d70)]:
    print("=== %08x" % lo)
    for ins in md.disasm(img[lo-base:hi-base], lo):
        print("  %08x  %-7s %s" % (ins.address, ins.mnemonic, ins.op_str))
