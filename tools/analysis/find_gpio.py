from capstone import *
img = open("baofeng-uv5rh-fw/dump/fw/5RH_NRF_Fangti_V0.14_231124-1.bin","rb").read()
base = 0x08001000
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS)
md.skipdata = True
insns = list(md.disasm(img, base))
print("insns", len(insns))
TARGETS = {0x48000000:"GPIOA", 0x48000400:"GPIOB", 0x48000800:"GPIOC"}
import struct
found = []
for i, ins in enumerate(insns):
    if ins.mnemonic != "ldr": continue
    ops = ins.op_str
    if "[pc," not in ops: continue
    try:
        imm = int(ops.split("#")[-1].rstrip("]"), 0)
    except Exception:
        continue
    # ldr literal: pc aligned + imm
    a = (ins.address + 4) & ~3
    val = struct.unpack_from("<I", img, a + imm - base)[0] if 0 <= a + imm - base <= len(img)-4 else 0
    if val in TARGETS:
        found.append((ins.address, TARGETS[val]))
print("literal refs:", len(found))
seen = set()
for addr, name in found[:40]:
    print("  %08x -> %s" % (addr, name))
