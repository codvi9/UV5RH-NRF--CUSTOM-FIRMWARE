import re, sys, os
base = "baofeng-uv5rh-fw/_mod/UV-5RM-Radio-Mod-main/UV-5RM Custom Firmware/firmware-source/at32f421-pac/src/"
files = ["usart1/ctrl1.rs","usart1/ctrl2.rs","usart1/brr.rs",
         "spi2/ctrl1.rs","spi2/ctrl2.rs","spi2/sts.rs","spi2/dt.rs",
         "gpioa/cfgr.rs","gpioa/muxh.rs","gpioa/pull.rs","gpioa/omode.rs"]
for f in files:
    p = base + f
    if not os.path.exists(p):
        print("MISSING", f); continue
    lines = open(p, encoding="utf-8").read().split("\n")
    out = []
    for i, ln in enumerate(lines):
        m = re.search(r"pub fn (\w+)\(&self\) -> (\w+) \{", ln)
        if not m: continue
        name = m.group(1)
        tail = " ".join(lines[i+1:i+3])
        s = re.search(r">> (\d+)", tail)
        k = re.search(r"& (0x[0-9a-fA-F]+)", tail)
        if s:
            out.append("%s=b%s" % (name, s.group(1)))
        elif k:
            v = int(k.group(1), 16)
            out.append("%s=b%s" % (name, (v & -v).bit_length()-1))
        else:
            out.append("%s=?" % name)
    print("==", f)
    print("   " + "  ".join(out))
