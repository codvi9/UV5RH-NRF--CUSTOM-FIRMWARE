d = open("baofeng-uv5rh-fw/dump/fw/5RH_NRF_V0.13_231121-1.bin","rb").read()
for t in [b"RADIO", b"FM", b"87.5", b"108.0", b"MHz"]:
    i = d.find(t)
    print(t, "at", hex(0x08001000+i) if i>=0 else "NONE", "count", d.count(t))
# also region2
c = open("baofeng-uv5rh-fw/dump/fw/5RH_NRF_V0.13_231121-2.bin","rb").read()
for t in [b"RADIO", b"FM"]:
    print("region2", t, c.find(t))
