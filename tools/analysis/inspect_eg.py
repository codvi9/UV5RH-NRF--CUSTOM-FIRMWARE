import io, tarfile, struct, urllib.request
u = "https://crates.io/api/v1/crates/embedded-graphics/0.8.1/download"
d = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent":"uv5rh-fw"}), timeout=60).read()
tf = tarfile.open(fileobj=io.BytesIO(d), mode="r:gz")
names = tf.getnames()
raw = [n for n in names if n.endswith(".raw")]
print("raw files:", len(raw))
for n in raw[:20]: print("  ", n.split("/",1)[1], tf.getmember(n).size)
# inspect the 5x7 png header
for want in ("fonts/png/ascii/font_5x8.png","fonts/png/ascii/font_6x10.png"):
    n = [x for x in names if x.endswith(want)][0]
    b = tf.extractfile(n).read()
    w,h,bd,ct = struct.unpack(">IIBB", b[16:26])
    print(want, "size %dx%d bitdepth=%d colortype=%d bytes=%d" % (w,h,bd,ct,len(b)))
