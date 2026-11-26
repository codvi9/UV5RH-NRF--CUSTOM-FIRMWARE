import re, os
base = "baofeng-uv5rh-fw/_mod/UV-5RM-Radio-Mod-main/UV-5RM Custom Firmware/firmware-source/at32f421-pac/src/"
files = ["usart1/baudr.rs","usart1/sts.rs","usart1/dt.rs","spi1/ctrl1.rs","spi1/ctrl2.rs","spi1/sts.rs","spi1/dt.rs"]
for f in files:
    p = base + f
    if not os.path.exists(p): print("MISSING", f); continue
    lines = open(p, encoding="utf-8").read().split("\n")
    out = []
    for i, ln in enumerate(lines):
        m = re.search(r"pub fn (\w+)\(&self\) -> (\w+) \{", ln)
        if not m: continue
        tail = " ".join(lines[i+1:i+3])
        s = re.search(r">> (\d+)", tail); k = re.search(r"& (0x[0-9a-fA-F]+)", tail)
        if s: out.append("%s=b%s" % (m.group(1), s.group(1)))
        elif k:
            v = int(k.group(1),16); out.append("%s=b%s" % (m.group(1), (v&-v).bit_length()-1))
    print("==", f); print("   " + "  ".join(out))
