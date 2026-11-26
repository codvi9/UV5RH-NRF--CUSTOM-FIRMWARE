#!/usr/bin/env python3
"""Dump a code range of the bootloader with PC-literal annotations."""
import struct, sys
from capstone import *
from capstone.arm import *

BIN = "_repo/Baofeng-UV-5RM-5RH-RE-main/reverse_engineering/dumped_btldr.bin"
code = open(BIN, "rb").read()
BASE = 0x08000000
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS)
md.detail = True

start = int(sys.argv[1], 16)
end = int(sys.argv[2], 16)
o = start - BASE
for ins in md.disasm(code[o:end - BASE], start):
    extra = ""
    if ins.mnemonic.startswith("ldr") and len(ins.operands) == 2 \
            and ins.operands[1].type == ARM_OP_MEM and ins.operands[1].mem.base == ARM_REG_PC:
        a = ins.address + 4 + ins.operands[1].mem.disp
        if 0 <= a - BASE and a - BASE + 4 <= len(code):
            extra = "   ; =0x%08x" % struct.unpack("<I", code[a - BASE:a - BASE + 4])[0]
    print("%08x  %-8s %-28s%s" % (ins.address, ins.mnemonic, ins.op_str, extra))
