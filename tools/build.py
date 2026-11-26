#!/usr/bin/env python3
"""Build the test firmware, wrap it into a single-region .BF, report sizes."""
import glob, io, os, subprocess, sys, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIP = os.path.join(ROOT, "tools", "armgcc.zip")
TOOLS = os.path.join(ROOT, "tools")
FW = os.path.join(ROOT, "fw")


def find_gcc():
    hits = glob.glob(os.path.join(TOOLS, "**", "bin", "arm-none-eabi-gcc.exe"), recursive=True)
    if hits:
        return hits[0]
    if os.path.exists(ZIP):
        print("[*] extracting toolchain ...")
        with zipfile.ZipFile(ZIP) as z:
            z.extractall(TOOLS)
        hits = glob.glob(os.path.join(TOOLS, "**", "bin", "arm-none-eabi-gcc.exe"), recursive=True)
        if hits:
            return hits[0]
    raise SystemExit("no arm-none-eabi-gcc found")


def main():
    gcc = find_gcc()
    bindir = os.path.dirname(gcc)
    objcopy = os.path.join(bindir, "arm-none-eabi-objcopy.exe")
    size = os.path.join(bindir, "arm-none-eabi-size.exe")
    elf = os.path.join(FW, "fw.elf")
    bin_ = os.path.join(FW, "fw.bin")
    cmd = [gcc, "-mcpu=cortex-m4", "-mthumb", "-Os", "-ffreestanding", "-fno-builtin",
           "-Wall", "-nostdlib", "-T", os.path.join(FW, "link.ld"),
           os.path.join(FW, "startup.c"), os.path.join(FW, "main.c"),
           os.path.join(FW, "rf.c"),
           os.path.join(FW, "uart.c"),
           os.path.join(FW, "ebook.c"),
           "-o", elf, "-Wl,--gc-sections", "-Wl,-Map=" + os.path.join(FW, "fw.map")]
    print("[*]", " ".join(cmd))
    subprocess.check_call(cmd)
    subprocess.check_call([objcopy, "-O", "binary", elf, bin_])
    subprocess.check_call([size, elf])
    data = open(bin_, "rb").read()
    print("[*] binary: %d bytes" % len(data))
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import bf_tool
    blob = bf_tool.pack1(data)
    out = os.path.join(FW, "fw.BF")
    open(out, "wb").write(blob)
    print("[*] wrote %s (%d bytes)" % (out, len(blob)))
    print("[*] header: count=%d len1=%d" % (blob[0], int.from_bytes(blob[1:5], "big")))


if __name__ == "__main__":
    main()
