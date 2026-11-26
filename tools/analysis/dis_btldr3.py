import struct
from capstone import *
from capstone.arm import ARM_OP_IMM, ARM_OP_REG

p = "baofeng-uv5rh-fw/_repo/Baofeng-UV-5RM-5RH-RE-main/reverse_engineering/dumped_btldr.bin"
code = open(p, "rb").read()
base = 0x08000000
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS); md.detail = True

pat = {b"\x00\x38\x01\x40":"USART1/0x40013800", b"\x00\x44\x00\x40":"USART2/0x40004400",
       b"\x00\x00\x00\x48":"GPIOA/0x48000000", b"\x00\x10\x02\x40":"CRM/0x40021000",
       b"\x00\x04\x00\x48":"GPIOB/0x48000400", b"\x00\x0c\x00\x48":"GPIOF/0x48000C00"}
print("--- literal-pool hits ---")
for k, v in pat.items():
    i = code.find(k)
    while i != -1:
        print("  0x%08x  %s" % (base + i, v)); i = code.find(k, i+1)

print("--- movw/movt reconstructed ---")
regs = {}
for ins in md.disasm(code, base):
    if ins.mnemonic == "movw" and len(ins.operands) == 2 and ins.operands[1].type == ARM_OP_IMM:
        regs[ins.reg_name(ins.operands[0].reg)] = ins.operands[1].imm
    elif ins.mnemonic == "movt" and len(ins.operands) == 2 and ins.operands[1].type == ARM_OP_IMM:
        r = ins.reg_name(ins.operands[0].reg)
        lo = regs.get(r)
        if lo is not None:
            val = (ins.operands[1].imm << 16) | lo
            if 0x40000000 <= val <= 0x48002000:
                print("  0x%08x  %s = 0x%08x" % (ins.address, r, val))
