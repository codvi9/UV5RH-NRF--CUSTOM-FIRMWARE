import re, json
p = "baofeng-uv5rh-fw/_mod/UV-5RM-Radio-Mod-main/UV-5RM Custom Firmware/firmware-source/src/drivers/fd6818b.rs"
src = open(p, encoding="utf-8").read()

consts = {}
for m in re.finditer(r"const (\w+): u(?:8|16) = (0x[0-9A-Fa-f]+);", src):
    consts[m.group(1)] = int(m.group(2), 16)

def val(tok):
    tok = tok.strip()
    if tok in consts: return consts[tok]
    if tok.startswith("0x"): return int(tok, 16)
    return None

# locate init body
i = src.index("pub fn init(&mut self")
j = src.index("\n    }\n", i)
body = src[i:j]
rows, unresolved = [], []
in_loop = False
for line in body.split("\n"):
    s = line.strip()
    if s.startswith("for ") or s.startswith("while "):
        in_loop = True; continue
    if in_loop and s == "}":
        in_loop = False; continue
    m = re.match(r"self\.write_reg\(syst, (\w+), (.+?)\);", s)
    if m and not in_loop:
        a = val(m.group(1)); v = val(m.group(2))
        if a is None or v is None:
            unresolved.append(s); continue
        rows.append((a, v))
    m2 = re.match(r"self\.read_reg\(syst, (\w+)\)", s)
    if m2 and not in_loop:
        unresolved.append(s)

print("consts:", len(consts), "init rows:", len(rows), "unresolved:", len(unresolved))
for u in unresolved[:8]: print("   unresolved:", u[:90])
print("first rows:", rows[:8])

hdr = ["/* generated from fd6818b.rs init() by tools/extract_rf.py */",
       "#pragma once", "#include <stdint.h>",
       "static const uint16_t RF_INIT_TBL[][2] = {"]
for a, v in rows:
    hdr.append("  {0x%02X, 0x%04X}," % (a, v))
hdr.append("};")
hdr.append("#define RF_INIT_COUNT %d" % len(rows))
open("baofeng-uv5rh-fw/fw/rf_init.h", "w").write("\n".join(hdr) + "\n")
print("wrote fw/rf_init.h")
