from capstone import *
p = "baofeng-uv5rh-fw/_repo/Baofeng-UV-5RM-5RH-RE-main/reverse_engineering/dumped_btldr.bin"
code = open(p,"rb").read(); base = 0x08000000
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS)
for lo, hi, tag in [(0x08000340,0x080003A0,"GPIOB #1"),(0x08000780,0x08000800,"GPIOB #2"),(0x08000d20,0x08000d80,"USART1")]:
    print("=== %s" % tag)
    for ins in md.disasm(code[lo-base:hi-base], lo):
        print("  %08x  %-7s %s" % (ins.address, ins.mnemonic, ins.op_str))
