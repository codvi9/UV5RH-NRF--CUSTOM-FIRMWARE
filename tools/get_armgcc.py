import urllib.request, os, sys
U = "https://github.com/xpack-dev-tools/arm-none-eabi-gcc-xpack/releases/download/v13.2.1-1.1/xpack-arm-none-eabi-gcc-13.2.1-1.1-win32-x64.zip"
out = "baofeng-uv5rh-fw/tools/armgcc.zip"
tmp = out + ".part"
req = urllib.request.Request(U, headers={"User-Agent": "Mozilla/5.0"})
r = urllib.request.urlopen(req, timeout=60)
total = int(r.headers.get("Content-Length") or 0)
done = 0
with open(tmp, "wb") as f:
    while True:
        b = r.read(1 << 20)
        if not b:
            break
        f.write(b); done += len(b)
        if done % (20 << 20) < (1 << 20):
            print("%.0f%% %d/%d" % (100.0*done/total if total else 0, done, total), flush=True)
os.replace(tmp, out)
print("done", done, "bytes")
