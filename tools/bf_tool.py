#!/usr/bin/env python3
"""Baofeng UV-5RM/5RH .BF container tool (pack / unpack / info).

Container layout (header is 16 bytes, big-endian):
    0x00  1  region count (always 0x02)
    0x01  4  region1 length  (application image, runs at 0x08001000)
    0x05  4  region2 length  (config blob, written to system-bootloader area 0x1FFFE400)
    0x09  7  reserved, flasher ignores it (0xFF filler)
    0x10  N  region1 payload
         M  region2 payload

Payload crypto (symmetric), 1024-byte blocks:
    blocks 0,1                plaintext
    blocks i in [2, n-3]      XOR with KDHT if i%3==1, RBGI if i%3==2, plain if i%3==0
    blocks n-2, n-1           plaintext
XOR skips a byte when it is 0x00, 0xFF, equal to the key byte, or equal to key^0xFF.
"""
import struct
import sys

PKG = 1024
KEY1 = b"KDHT"
KEY2 = b"RBGI"


def xor_crypt(data: bytes, key: bytes) -> bytes:
    out = bytearray(len(data))
    for i, x in enumerate(data):
        k = key[i % 4]
        if x != 0 and x != 0xFF and x != k and x != (k ^ 0xFF):
            x ^= k
        out[i] = x
    return bytes(out)


def crypt(data: bytes) -> bytes:
    n = (len(data) + PKG - 1) // PKG
    if n <= 4:
        return bytes(data)
    out = bytearray(data[: 2 * PKG])
    for i in range(2, n - 2):
        blk = data[i * PKG:(i + 1) * PKG]
        if i % 3 == 1:
            blk = xor_crypt(blk, KEY1)
        elif i % 3 == 2:
            blk = xor_crypt(blk, KEY2)
        out += blk
    out += data[(n - 2) * PKG:]
    return bytes(out)[: len(data)]


def unpack(blob: bytes):
    count, size1, size2 = struct.unpack(">BLL", blob[:9])
    if count != 2:
        raise ValueError("unexpected region count %d" % count)
    r1 = blob[16:16 + size1]
    r2 = blob[16 + size1:16 + size1 + size2]
    return crypt(r1), crypt(r2), blob[9:16]


def pack1(r1: bytes, reserved: bytes = b"\xff" * 7) -> bytes:
    """Single-region container (count=1, no region2) - what the stock bootloader accepts."""
    hdr = struct.pack(">BLL", 1, len(r1), 0) + reserved
    return hdr + crypt(r1)


def pack(r1: bytes, r2: bytes, reserved: bytes = b"\xff" * 7) -> bytes:
    hdr = struct.pack(">BLL", 2, len(r1), len(r2)) + reserved
    return hdr + crypt(r1) + crypt(r2)


def _self_test():
    import os
    for size in (1, 1023, 1024, 2048, 3000, 4097, 60000, 61440):
        r1 = os.urandom(size)
        r2 = os.urandom(777)
        blob = pack(r1, r2)
        a, b, _ = unpack(blob)
        assert a == r1, "r1 mismatch at %d (got %d)" % (size, len(a))
        assert b == r2, "r2 mismatch at %d" % size
    print("self-test OK (sizes 1..61440, packed->unpacked identical)")


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd = argv[1]
    if cmd == "test":
        _self_test()
        return 0
    if cmd == "info":
        blob = open(argv[2], "rb").read()
        count, size1, size2 = struct.unpack(">BLL", blob[:9])
        print("file      :", argv[2], "(%d bytes)" % len(blob))
        print("regions   :", count)
        print("region1   :", size1, "bytes (app @0x08001000)")
        print("region2   :", size2, "bytes (cfg @0x1FFFE400)")
        print("reserved  :", blob[9:16].hex())
        print("expected  :", 16 + size1 + size2, "bytes")
        return 0
    if cmd == "unpack":
        r1, r2, hdr = unpack(open(argv[2], "rb").read())
        open(argv[3] + "-1.bin", "wb").write(r1)
        open(argv[3] + "-2.bin", "wb").write(r2)
        print("wrote", argv[3] + "-1.bin", len(r1), "bytes")
        print("wrote", argv[3] + "-2.bin", len(r2), "bytes")
        return 0
    if cmd == "pack":
        r1 = open(argv[2], "rb").read()
        r2 = open(argv[3], "rb").read() if len(argv) > 4 else b""
        blob = pack(r1, r2)
        open(argv[4] if len(argv) > 4 else argv[3], "wb").write(blob)
        print("wrote", len(blob), "bytes")
        return 0
    print("unknown command", cmd)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
