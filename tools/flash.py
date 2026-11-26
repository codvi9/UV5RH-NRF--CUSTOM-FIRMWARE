#!/usr/bin/env python3
"""Flash a single-region .BF to the KDH bootloader.  Usage: flash.py <port> <file.BF> [--go]"""
import struct, sys, time

sys.path.insert(0, "libs") if False else None
HEADER, FOOTER = 0xAA, 0xEF
CMD_HANDSHAKE, CMD_UPDATE, CMD_PACKAGES, CMD_END = 0x01, 0x03, 0x04, 0x45
ACK, CHUNK, RETRIES, TIMEOUT = 0x06, 1024, 5, 2.0
ERR = {0xE1: "handshake/command", 0xE2: "sequence/length", 0xE3: "flash write failed", 0xE5: "unknown command"}


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


def main():
    port_name, path = sys.argv[1], sys.argv[2]
    go = "--go" in sys.argv
    import serial

    raw = open(path, "rb").read()
    count, len1, len2 = struct.unpack_from(">BLL", raw, 0)
    if count != 1 or len2 != 0 or len(raw) != 16 + len1:
        raise SystemExit("not a single-region .BF: count=%d len1=%d len2=%d size=%d" % (count, len1, len2, len(raw)))
    region = raw[16:]
    if not (region[3] == 0x20 and region[7] == 0x08):
        raise SystemExit("vector table does not look like an app image: %s" % region[:8].hex())
    pkgs = -(-len1 // CHUNK)
    print("[*] %s: %d bytes, %d packages" % (path, len1, pkgs))
    if not go:
        print("[!] dry run only; add --go to write")
        return

    port = serial.Serial(port_name, 115200, timeout=0.03)
    port.dtr = True
    port.rts = True

    def read_frame(deadline):
        buf = bytearray()
        while time.monotonic() < deadline:
            buf += port.read(64)
            while buf and buf[0] != HEADER:
                buf.pop(0)
            if len(buf) >= 5:
                n = buf[3] << 8 | buf[4]
                if len(buf) >= 8 + n:
                    body = bytes(buf[1:5 + n])
                    got = buf[5 + n] << 8 | buf[6 + n]
                    return ("frame", body[0], body[1]) if got == crc16(body) else ("bad-crc",)
        return ("timeout", bool(buf))

    def send(cmd, args, data, retries=RETRIES, tolerate_silence=False):
        last, heard = "no attempts", False
        pkt = frame(cmd, args, data)
        for _ in range(retries):
            port.reset_input_buffer()
            port.write(pkt)
            r = read_frame(time.monotonic() + TIMEOUT)
            if r[0] == "frame":
                heard = True
                if r[2] == ACK:
                    return True
                if r[1] != 0xE2:
                    raise RuntimeError("cmd %#x refused: %s" % (cmd, ERR.get(r[1], hex(r[1]))))
                last = "seq err"
            elif r[0] == "timeout":
                heard = heard or r[1]
                last = "timeout"
            else:
                heard, last = True, "bad crc"
        if tolerate_silence and not heard:
            return False
        raise RuntimeError("cmd %#x failed: %s" % (cmd, last))

    try:
        send(CMD_HANDSHAKE, 0, b"BOOTLOADER")
        print("[*] handshake ok")
        send(CMD_PACKAGES, 0, bytes([pkgs]))
        t0 = time.monotonic()
        for seq in range(pkgs):
            chunk = region[seq * CHUNK:(seq + 1) * CHUNK].ljust(CHUNK, b"\x00")
            send(CMD_UPDATE, seq & 0xFF, chunk)
            if (seq + 1) % 10 == 0 or seq + 1 == pkgs:
                print("    %d/%d" % (seq + 1, pkgs))
        print("[*] all packages sent in %.1fs" % (time.monotonic() - t0))
        acked = send(CMD_END, 0, b"", retries=2, tolerate_silence=True)
        print("[*] end acked" if acked else "[*] end sent (radio rebooted)")
        print("[+] FLASH COMPLETE")
    finally:
        port.close()


if __name__ == "__main__":
    main()
