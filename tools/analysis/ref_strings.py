import re
d = open("baofeng-uv5rh-fw/ref/Dondji.fusion.bin","rb").read()
print("size", len(d))
strs = [(m.start(), m.group().decode("latin1")) for m in re.finditer(rb"[ -~]{5,}", d)]
print("strings", len(strs))
for off, s in strs[:60]:
    print("%06x %s" % (off, s[:70]))
