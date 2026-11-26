import itertools
base = "baofeng-uv5rh-fw/dump/fw/"
names = {"BK":"5RH_BK_V0.14_231123-1.bin","NRF":"5RH_NRF_V0.13_231121-1.bin","L":"5RH_AT1846S_V0.07_FangtiBlueBG_230918-1.bin"}
data = {k: open(base+v,"rb").read() for k,v in names.items()}
for a,b in itertools.combinations(names,2):
    x,y = data[a], data[b]; n = min(len(x),len(y))
    same = sum(1 for i in range(n) if x[i]==y[i])
    print("%s vs %s: %.1f%% identical over %d bytes" % (a,b,100*same/n,n))
for k,v in data.items():
    print(k, "len", len(v), "vector[0:8]", v[:8].hex(), "sp", v[0:4][::-1].hex())
