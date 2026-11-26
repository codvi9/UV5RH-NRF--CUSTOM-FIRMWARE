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

def frame(cmd, args, data):
    body = bytes([cmd, args, len(data) >> 8, len(data) & 0xFF]) + data
    c = crc16(body)
    return bytes([0xAA]) + body + bytes([c >> 8, c & 0xFF, 0xEF])

port = sys.argv[1] if len(sys.argv) > 1 else "COM10"
s = serial.Serial(port, 115200, timeout=0.2)
for dtr in (True, False):
    for rts in (True, False):
        s.dtr = dtr; s.rts = rts
        time.sleep(0.05)
        s.reset_input_buffer()
        s.write(frame(0x01, 0, b"BOOTLOADER"))
        buf = b""
        end = time.monotonic() + 1.5
        while time.monotonic() < end:
            buf += s.read(64)
        print("dtr=%s rts=%s -> %s" % (dtr, rts, buf[:24].hex() if buf else "(none)"))
s.close()
