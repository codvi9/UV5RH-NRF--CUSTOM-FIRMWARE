import struct, sys
from capstone import *

p = "baofeng-uv5rh-fw/_repo/Baofeng-UV-5RM-5RH-RE-main/reverse_engineering/dumped_btldr.bin"
code = open(p, "rb").read()
print("size", len(code))
sp, rst = struct.unpack("<II", code[:8])
print("SP=%08x  reset=%08x" % (sp, rst))

md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS)
md.detail = True
base = 0x08000000
off = rst - base
print("--- reset handler @%08x ---" % rst)
for i, ins in enumerate(md.disasm(code[off:off+240], rst)):
    print("  %08x  %-8s %s" % (ins.address, ins.mnemonic, ins.op_str))
    if i > 60: break

print("--- peripheral constants ---")
targets = {0x40021000:"CRM", 0x48000000:"GPIOA", 0x48000400:"GPIOB", 0x48000800:"GPIOC", 0x48000C00:"GPIOF",
           0x40013800:"USART1", 0x40004400:"USART2", 0x40010000:"APB2", 0x40020000:"AHB1", 0x1FFFE400:"SYSBTLDR"}
for ins in md.disasm(code, base):
    for op in ins.operands:
        if op.type == ARM_OP_IMM and op.imm in targets:
            print("  %08x  %-8s %-20s -> %s" % (ins.address, ins.mnemonic, ins.op_str, targets[op.imm]))
