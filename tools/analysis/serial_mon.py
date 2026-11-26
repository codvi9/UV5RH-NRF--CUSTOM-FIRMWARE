#!/usr/bin/env python3
"""Read whatever the radio prints on the programming port. Usage: serial_mon.py <port> [seconds]"""
import sys, time
sys.path.insert(0, "libs")
import serial

port_name = sys.argv[1]
secs = float(sys.argv[2]) if len(sys.argv) > 2 else 6.0
s = serial.Serial(port_name, 115200, timeout=0.1)
end = time.monotonic() + secs
buf = bytearray()
while time.monotonic() < end:
    buf += s.read(256)
s.close()
print("bytes:", len(buf))
print("ascii:", repr(bytes(buf)[:400]))
print("hex  :", bytes(buf)[:120].hex())
