from capstone import *
img = open("baofeng-uv5rh-fw/dump/fw/5RH_NRF_Fangti_V0.14_231124-1.bin","rb").read()
base = 0x08001000
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS)
md.skipdata = True
insns = list(md.disasm(img, base))
print("insns", len(insns))
def imm_of(ins):
    for op in ins.operands:
        if op.type == CS_OP_IMM: return op.imm
    return None
hits = 0
for i, ins in enumerate(insns):
    if ins.mnemonic.startswith("mov") and "r0, #0x47" in ins.op_str:
        print("---- @%08x" % ins.address)
        for c in insns[i:i+5]:
            print("   %08x %-7s %s" % (c.address, c.mnemonic, c.op_str))
        hits += 1
        if hits >= 8: break
print("hits", hits)
