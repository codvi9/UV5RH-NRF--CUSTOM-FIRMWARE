from capstone import *
img = open("baofeng-uv5rh-fw/dump/fw/5RH_NRF_Fangti_V0.14_231124-1.bin","rb").read()
base = 0x08001000
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS)
insns = list(md.disasm(img, base))
print("insns", len(insns))
hits = 0
for i, ins in enumerate(insns):
    m = ins.mnemonic
    if m in ("movs","mov","mov.w") and ins.op_str.replace(" ","") in ("r0,#0x47","r1,#0x47","r2,#0x47","r3,#0x47","r0,#0x47","r7,#0x47"):
        ctx = insns[i:i+6]
        print("---- @%08x" % ins.address)
        for c in ctx:
            print("   %08x %-7s %s" % (c.address, c.mnemonic, c.op_str))
        hits += 1
        if hits > 12: break
print("total hits shown", hits)
