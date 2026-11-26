#!/usr/bin/env python3
"""Talk to the radio over COMx.

  python tools/uart_mon.py COM10 monitor 6      # just listen, print text
  python tools/uart_mon.py COM10 probe          # KDH bootloader handshake (read-only)
  python tools/uart_mon.py COM10 send "r"       # send bytes, print the reply

pyserial is vendored under libs/.
"""
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "libs"))

import serial  # noqa: E402

HEADER, FOOTER = 0xAA, 0xEF


def crc16(d):
    c = 0
    for b in d:
        c ^= b << 8
        for _ in range(8):
            c = ((c << 1) ^ 0x1021) if c & 0x8000 else c << 1
            c &= 0xFFFF
    return c


def frame(cmd, args, data):
    body = bytes([cmd, args, len(data) >> 8, len(data) & 0xFF]) + data
    c = crc16(body)
    return bytes([HEADER]) + body + bytes([c >> 8, c & 0xFF, FOOTER])


def monitor(port, seconds):
    ser = serial.Serial(port, 115200, timeout=0.05)
    print("[*] listening on %s for %.1fs" % (port, seconds))
    end = time.monotonic() + seconds
    buf = bytearray()
    while time.monotonic() < end:
        chunk = ser.read(256)
        if chunk:
            buf += chunk
            text = chunk.decode("ascii", "replace")
            sys.stdout.buffer.write(text.encode("ascii", "replace"))
            sys.stdout.buffer.flush()
    print("\n[*] %d bytes total" % len(buf))
    if buf:
        print("[*] hex:", buf[:64].hex())
    ser.close()


def probe(port):
    ser = serial.Serial(port, 115200, timeout=0.3)
    ser.reset_input_buffer()
    ser.write(frame(0x01, 0, b"BOOTLOADER"))
    time.sleep(0.3)
    r = ser.read(64)
    ser.close()
    if not r:
        print("[-] no reply - radio is not in bootloader mode (or app has no UART)")
        return 1
    print("[+] reply: %s" % r.hex())
    if r[0] == HEADER:
        n = r[3] << 8 | r[4]
        body = r[1:5 + n]
        ok = (r[5 + n] << 8 | r[6 + n]) == crc16(body)
        print("[+] KDH bootloader, cmd=0x%02x status=0x%02x crc_ok=%s"
              % (body[0], body[1], ok))
        return 0
    return 1


def send(port, text, wait=2.5):
    ser = serial.Serial(port, 115200, timeout=0.2)
    ser.reset_input_buffer()
    ser.write(text.encode())
    end = time.monotonic() + wait
    buf = bytearray()
    while time.monotonic() < end:
        chunk = ser.read(256)
        if chunk:
            buf += chunk
    ser.close()
    print("[>] sent %r" % text)
    text_out = ("[<] %r" % buf.decode("ascii", "replace")).encode("ascii", "replace")
    sys.stdout.buffer.write(text_out + b"\n")
    sys.stdout.buffer.flush()


def main():
    port = sys.argv[1] if len(sys.argv) > 1 else "COM10"
    mode = sys.argv[2] if len(sys.argv) > 2 else "monitor"
    arg = sys.argv[3] if len(sys.argv) > 3 else None
    if mode == "monitor":
        monitor(port, float(arg or 5))
    elif mode == "probe":
        return probe(port)
    elif mode == "send":
        send(port, arg or "")
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
