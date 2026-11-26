import glob, os, re, sys
sys.path.insert(0, "baofeng-uv5rh-fw/tools")
import bf_tool

root = "baofeng-uv5rh-fw/_repo/Baofeng-UV-5RM-5RH-RE-main/factory_firmware"
os.makedirs("baofeng-uv5rh-fw/dump/fw", exist_ok=True)
for path in sorted(glob.glob(root + "/**/*.BF", recursive=True)):
    name = os.path.basename(path)[:-3]
    blob = open(path, "rb").read()
    try:
        r1, r2, _ = bf_tool.unpack(blob)
    except Exception as e:
        print(name, "UNPACK FAIL", e); continue
    out = "baofeng-uv5rh-fw/dump/fw/" + name
    open(out + "-1.bin", "wb").write(r1)
    open(out + "-2.bin", "wb").write(r2)
    hits = sorted({m.group().decode("latin1") for m in re.finditer(rb"[ -~]{6,}", r1)})
    idh = [h for h in hits if "5RH" in h or "NRF" in h or "YP0" in h or "BK" in h.upper()[:2]]
    print("%-45s r1=%6d r2=%5d  ids=%s" % (name, len(r1), len(r2), idh[:6]))
