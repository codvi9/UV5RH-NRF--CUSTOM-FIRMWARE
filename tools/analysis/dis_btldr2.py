import struct
from capstone import *
from capstone.arm import ARM_OP_IMM

p = "baofeng-uv5rh-fw/_repo/Baofeng-UV-5RM-5RH-RE-main/reverse_engineering/dumped_btldr.bin"
code = open(p, "rb").read()
sp, rst = struct.unpack("<II", code[:8])
base = 0x08000000
print("SP=%08x reset=%08x" % (sp, rst))
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS)
md.detail = True
start = rst & ~1
print("--- first 60 insns @%08x ---" % start)
n = 0
for ins in md.disasm(code[start-base:start-base+240], start):
    print("  %08x  %-8s %s" % (ins.address, ins.mnemonic, ins.op_str))
    n += 1
    if n > 60: break

targets = {0x40021000:"CRM", 0x48000000:"GPIOA", 0x48000400:"GPIOB", 0x48000800:"GPIOC",
           0x48000C00:"GPIOF", 0x40013800:"USART1", 0x40004400:"USART2", 0x1FFFE400:"SYSBTLDR"}
print("--- constants ---")
for ins in md.disasm(code, base):
    for op in ins.operands:
        if op.type == ARM_OP_IMM and op.imm in targets:
            print("  %08x  %-8s %-22s -> %s" % (ins.address, ins.mnemonic, ins.op_str, targets[op.imm]))
