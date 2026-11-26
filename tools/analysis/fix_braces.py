p = "baofeng-uv5rh-fw/fw/main.c"
s = open(p, encoding="utf-8").read()
bal = s.count("{") - s.count("}")
print("brace balance", bal)
if bal > 0:
    s += "\n" + "}" * bal + "\n"
    open(p, "w", encoding="utf-8").write(s)
    print("appended", bal)
elif bal < 0:
    print("negative balance, manual fix needed")
