#!/usr/bin/env python3
"""Locate USART1 bring-up in the stock 5RH image: base-register tracking for
GPIOA / USART1 writes, then dump the surrounding code."""
import struct, sys
from capstone import *
from capstone.arm import *

BIN = sys.argv[1] if len(sys.argv) > 1 else "dump/fw/5RH_NRF_V0.13_231121-1.bin"
BASE = 0x08001000
code = open(BIN, "rb").read()
print("image %d bytes, base %08x end %08x" % (len(code), BASE, BASE + len(code)))

md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS)
md.detail = True

insns = []
off = 0
while off < len(code) - 1:
    got = list(md.disasm(code[off:off + 512], BASE + off))
    if not got:
        off += 2
        continue
    insns.extend(got)
    off += 512 if len(got) >= 100 else 2
    if len(got) < 100:
        off = (got[-1].address - BASE) + got[-1].size
print("disassembled", len(insns), "insns")

PERIPH = {0x40013800: "USART1", 0x48000000: "GPIOA", 0x48000400: "GPIOB",
          0x48000800: "GPIOC", 0x40021000: "CRM", 0x40004400: "USART2",
          0x40013804: "USART1+4"}

hits = []
for i, ins in enumerate(insns):
    if ins.mnemonic != "ldr":
        continue
    ops = ins.operands
    if len(ops) != 2 or ops[0].type != ARM_OP_REG or ops[1].type != ARM_OP_MEM:
        continue
    mem = ops[1].mem
    if mem.base != ARM_REG_PC:
        continue
    lit_addr = ins.address + 4 + mem.disp
    off_ = lit_addr - BASE
    if off_ < 0 or off_ + 4 > len(code):
        continue
    lit = struct.unpack("<I", code[off_:off_ + 4])[0]
    if lit not in PERIPH:
        continue
    base_reg = ops[0].reg
    for j in range(i + 1, min(i + 24, len(insns))):
        b = insns[j]
        if b.mnemonic not in ("str", "ldr", "strb", "strh"):
            continue
        bo = b.operands
        if len(bo) != 2 or bo[1].type != ARM_OP_MEM or bo[1].mem.base != base_reg:
            continue
        imm = bo[1].mem.disp
        if not (0 <= imm <= 0x40):
            continue
        val = None
        if b.mnemonic == "str" and bo[0].type == ARM_OP_IMM:
            val = bo[0].imm
        elif b.mnemonic == "str":
            val = "r%d" % bo[0].reg
        hits.append((ins.address, PERIPH[lit], b.mnemonic, imm, val, b.address))

print("\n=== peripheral base usage (first 60) ===")
for a, name, mn, imm, val, ba in hits[:60]:
    print("%08x  %-9s +0x%02x  %s %s" % (a, name, imm, mn, val))

by_addr = {ins.address: k for k, ins in enumerate(insns)}


def ctx(addr, before=20, after=12):
    k = by_addr.get(addr)
    if k is None:
        return
    print("--- context around %08x ---" % addr)
    for ins in insns[max(0, k - before):k + after]:
        lit = ""
        if ins.mnemonic == "ldr" and len(ins.operands) == 2 and ins.operands[1].type == ARM_OP_MEM \
                and ins.operands[1].mem.base == ARM_REG_PC:
            o = ins.address + 4 + ins.operands[1].mem.disp - BASE
            if 0 <= o + 4 <= len(code):
                lit = "  ; =0x%08x" % struct.unpack("<I", code[o:o + 4])[0]
        print("  %08x  %-7s %-26s%s" % (ins.address, ins.mnemonic, ins.op_str, lit))


print("\n=== USART1 BRR / CR1 writes ===")
seen = set()
for a, name, mn, imm, val, ba in hits:
    if name != "USART1" or imm not in (0x08, 0x0C):
        continue
    if ba in seen:
        continue
    seen.add(ba)
    print("\n[%s off=0x%02x val=%s]" % (mn, imm, val))
    ctx(a, 18, 10)

print("\n=== GPIOA AFR writes ===")
seen = set()
for a, name, mn, imm, val, ba in hits:
    if name != "GPIOA" or imm not in (0x20, 0x24):
        continue
    if ba in seen:
        continue
    seen.add(ba)
    print("\n[GPIOA+0x%02x %s %s]" % (imm, mn, val))
    ctx(a, 6, 4)
