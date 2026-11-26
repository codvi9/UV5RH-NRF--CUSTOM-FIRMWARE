import sys, time
sys.path.insert(0, "libs")
import serial

def crc16(d):
    c = 0
    for b in d:
        c ^= b << 8
        for _ in range(8):
            c = ((c << 1) ^ 0x1021) if c & 0x8000 else c << 1
            c &= 0xFFFF
    return c

body = bytes([0x01, 0x00, 0x00, 0x0A]) + b"BOOTLOADER"
c = crc16(body)
frame = b"\xAA" + body + bytes([c >> 8, c & 0xFF, 0xEF])

for baud in (9600, 19200, 38400, 57600, 115200):
    try:
        s = serial.Serial("COM10", baud, timeout=0.2)
        s.dtr = True; s.rts = True
        time.sleep(0.05)
        s.reset_input_buffer()
        s.write(frame)
        buf = b""
        end = time.monotonic() + 1.0
        while time.monotonic() < end:
            buf += s.read(64)
        s.close()
        print("%6d -> %s" % (baud, buf[:20].hex() if buf else "(none)"))
    except Exception as e:
        print(baud, "ERR", str(e)[:50])
