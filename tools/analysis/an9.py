import glob, os, struct
files = sorted(glob.glob("baofeng-uv5rh-fw/dump/fw/*.bin"))
print("files:", len(files))
for f in files:
    d = open(f,"rb").read()
    marks = {}
    for t in [b"RADIO", b"FM\x00", b"87.5", b"108.0", b"MHz", b"FM "]:
        marks[t.decode("latin1")] = d.count(t)
    rda = {}
    for v in (0x88AF, 0xC011, 0xC001, 0xC00D, 0x8800):
        rda[hex(v)] = d.count(struct.pack("<H", v))
    print(os.path.basename(f), len(d), marks, rda)
