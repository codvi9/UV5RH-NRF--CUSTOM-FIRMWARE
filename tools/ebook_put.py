#!/usr/bin/env python3
"""Put a book (or the GB2312 font) into the radio's SPI NOR over UART.

  python tools/ebook_put.py COM10 book.txt          # text, converted to GBK
  python tools/ebook_put.py COM10 --font fw/font_cn.bin

Protocol: 'e' (book) or 'F' (font) -> "READY" -> 4-byte LE length ->
"ERASE" -> 256-byte chunks, each answered with '.' -> "DONE".
"""
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "libs"))

import serial  # noqa: E402

MAX_LEN = 0x1B7F00


def wait_for(ser, token, timeout):
    end = time.monotonic() + timeout
    buf = bytearray()
    while time.monotonic() < end:
        chunk = ser.read(1)
        if chunk:
            buf += chunk
            if buf.endswith(token):
                return True
            if b"ERR" in buf:
                return False
            if len(buf) > 64:
                buf.clear()
    return False


def main():
    args = [a for a in sys.argv[1:]]
    if not args:
        print(__doc__)
        return 2
    port = args[0]
    font = "--font" in args
    if font:
        args.remove("--font")
    path = args[1] if len(args) > 1 else None
    if not path:
        print(__doc__)
        return 2

    raw = open(path, "rb").read()
    if font:
        data = raw
        cmd = b"F"
    else:
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("gbk", errors="replace")
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        data = text.encode("gbk", errors="replace")
        cmd = b"e"
    if len(data) > MAX_LEN:
        raise SystemExit("too big: %d > %d" % (len(data), MAX_LEN))
    print("[*] %s: %d bytes -> %s" % (path, len(raw), "font" if font else "book(gbk)"))

    ser = serial.Serial(port, 115200, timeout=0.05)
    ser.reset_input_buffer()
    ser.write(cmd)
    if not wait_for(ser, b"READY", 5):
        raise SystemExit("no READY from radio")
    print("[*] radio ready")

    ser.write(len(data).to_bytes(4, "little"))
    t0 = time.monotonic()
    if not wait_for(ser, b"ERASE", 90):
        raise SystemExit("erase did not start")
    if not wait_for(ser, b"OK", 120):
        raise SystemExit("erase did not finish")
    print("[*] erase done, streaming ...")

    off = 0
    while off < len(data):
        chunk = data[off:off + 256]
        ser.write(chunk)
        if not wait_for(ser, b".", 15):
            raise SystemExit("no ack at %d" % off)
        off += len(chunk)
        if off % 32768 == 0:
            print("    %d/%d (%.0f%%)" % (off, len(data), 100.0 * off / len(data)))
    ok = wait_for(ser, b"DONE", 25)
    print("[%s] %d bytes in %.1fs" % ("+" if ok else "!", len(data), time.monotonic() - t0))
    ser.close()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
