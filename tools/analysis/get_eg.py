import io, tarfile, urllib.request
u = "https://crates.io/api/v1/crates/embedded-graphics/0.8.1/download"
req = urllib.request.Request(u, headers={"User-Agent": "uv5rh-fw"})
d = urllib.request.urlopen(req, timeout=60).read()
print("bytes", len(d))
tf = tarfile.open(fileobj=io.BytesIO(d), mode="r:gz")
names = tf.getnames()
fonts = [n for n in names if "/fonts/" in n or "mono_font" in n]
print("font-related entries:", len(fonts))
for n in fonts[:40]:
    m = tf.getmember(n)
    print("  %-70s %d" % (n.split("/",1)[1], m.size))
