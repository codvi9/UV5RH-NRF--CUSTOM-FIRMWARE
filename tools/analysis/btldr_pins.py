#!/usr/bin/env python3
"""Find the bootloader's UART pin setup: USART1 BRR/CR1 and GPIOA MODER/AFR."""
import struct, sys
from capstone import *
from capstone.arm import *

BIN = "_repo/Baofeng-UV-5RM-5RH-RE-main/reverse_engineering/dumped_btldr.bin"
code = open(BIN, "rb").read()
BASE = 0x08000000
print("bootloader %d bytes" % len(code))

md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS)
md.detail = True

insns = []
off = 0
while off < len(code) - 1:
    got = list(md.disasm(code[off:off + 256], BASE + off))
    if not got:
        off += 2
        continue
    insns.extend(got)
    off = (got[-1].address - BASE) + got[-1].size
print("disassembled", len(insns))

PER = {0x40013800: "USART1", 0x48000000: "GPIOA", 0x48000400: "GPIOB",
       0x48000800: "GPIOC", 0x40021000: "CRM"}


def lits(ins):
    if ins.mnemonic in ("ldr", "ldr.w") and len(ins.operands) == 2 \
            and ins.operands[0].type == ARM_OP_REG and ins.operands[1].type == ARM_OP_MEM \
            and ins.operands[1].mem.base == ARM_REG_PC:
        o = ins.address + 4 + ins.operands[1].mem.disp
        if 0 <= o and o + 4 <= len(code):
            return struct.unpack("<I", code[o:o + 4])[0]
    return None


print("\n=== all peripheral literals + following accesses ===")
for i, ins in enumerate(insns):
    v = lits(ins)
    if v is None or (v & 0xFFFFF000) not in (0x48000000, 0x48000400, 0x48000800, 0x40013000, 0x40021000):
        continue
    name = PER.get(v, "0x%08x" % v)
    reg = ins.operands[0].reg
    print("\n%08x  ldr r%d, =%s (%08x)" % (ins.address, reg, name, v))
    for b in insns[i + 1:i + 14]:
        mark = ""
        if b.mnemonic == "ldr" and len(b.operands) == 2 and b.operands[1].type == ARM_OP_MEM \
                and b.operands[1].mem.base == ARM_REG_PC:
            o = b.address + 4 + b.operands[1].mem.disp
            if 0 <= o and o + 4 <= len(code):
                mark = "  ; =0x%08x" % struct.unpack("<I", code[o:o + 4])[0]
        print("   %08x  %-8s %-24s%s" % (b.address, b.mnemonic, b.op_str, mark))
