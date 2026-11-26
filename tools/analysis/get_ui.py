import urllib.request, os
os.makedirs("baofeng-uv5rh-fw/ref/ui", exist_ok=True)
for name in ["AB_s.png", "main_only_s.png"]:
    u = "https://ethanyan6.github.io/Dondji/images/" + name
    try:
        d = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent":"Mozilla/5.0"}), timeout=60).read()
        open("baofeng-uv5rh-fw/ref/ui/" + name, "wb").write(d)
        print(name, len(d))
    except Exception as e:
        print(name, "ERR", str(e)[:80])
