import sys, time
sys.path.insert(0, "libs")
import serial
from serial.tools import list_ports

def crc16(d):
    c = 0
    for b in d:
        c ^= b << 8
        for _ in range(8):
            c = ((c << 1) ^ 0x1021) if c & 0x8000 else c << 1
            c &= 0xFFFF
    return c

body = bytes([0x01, 0x00, 0x00, len(b"BOOTLOADER")]) + b"BOOTLOADER"
frame = b"\xAA" + body + bytes([crc16(body) >> 8, crc16(body) & 0xFF, 0xEF])
print("ports:", [p.device for p in list_ports.comports()])
for p in list_ports.comports():
    try:
        s = serial.Serial(p.device, 115200, timeout=0.2)
        s.dtr = True; s.rts = True
        time.sleep(0.05)
        s.reset_input_buffer()
        s.write(frame)
        r = s.read(16)
        s.close()
        print(p.device, p.description[:40], "->", r.hex() if r else "(none)")
    except Exception as e:
        print(p.device, "ERR", str(e)[:60])
