#!/usr/bin/env python3
"""一键把电子书刷进 UV-5RH（自动识别串口 / 转 GBK / 超长自动裁到行边界）。

  python tools/flash_ebook.py 三体.txt
  python tools/flash_ebook.py 三体.txt --font            # 首次使用，连字库一起传
  python tools/flash_ebook.py 三体.txt --port COM10
  python tools/flash_ebook.py --font-only                # 只更新字库

前置：电台停在主界面（菜单/电子书/频谱页不处理串口命令）。
"""
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "libs"))

import serial  # noqa: E402
import serial.tools.list_ports as ports  # noqa: E402

MAX_BOOK = 0x1B7F00          # 正文上限，正好停在书签扇区之前
FONT_PATH = os.path.join(ROOT, "fw", "font_cn.bin")
FONT_MARK = os.path.join(ROOT, "tools", ".font_ok")   # 字库已上传过的标记


def pick_port():
    cands = [p.device for p in ports.comports()]
    for prefer in ("COM10",):
        if prefer in cands:
            return prefer
    return cands[0] if cands else None


def wait_for(ser, token, timeout, quiet=False):
    end = time.monotonic() + timeout
    buf = bytearray()
    while time.monotonic() < end:
        b = ser.read(1)
        if not b:
            continue
        buf += b
        if buf.endswith(token):
            return True
        if b"ERR" in buf:
            return False
        if len(buf) > 64:
            buf.clear()
    return False


def send_blob(ser, cmd, data, label, timeout_erase=180):
    ser.reset_input_buffer()
    ser.write(cmd)
    if not wait_for(ser, b"READY", 6):
        raise SystemExit(
            "电台没有响应。请确认：\n"
            "  1) 电台已开机并停在【主界面】（菜单/电子书页不响应）\n"
            "  2) 串口 %s 正确，115200 8N1\n"
            "  3) 写频线插好（插线时内部喇叭会被断开，属正常）" % ser.port)
    ser.write(len(data).to_bytes(4, "little"))
    if not wait_for(ser, b"ERASE", 90):
        raise SystemExit("擦除没有开始")
    print("    擦除中 ...", end="", flush=True)
    if not wait_for(ser, b"OK", timeout_erase):
        raise SystemExit("\n擦除超时")
    print("\r    擦除完成，写入中 ...")

    t0 = time.monotonic()
    off = 0
    step = max(1, len(data) // 20)
    last = 0
    while off < len(data):
        chunk = data[off:off + 256]
        ser.write(chunk)
        if not wait_for(ser, b".", 15):
            raise SystemExit("\n在偏移 %d 处超时" % off)
        off += len(chunk)
        if off - last >= step:
            last = off
            pct = 100.0 * off / len(data)
            el = time.monotonic() - t0
            eta = el * (100.0 - pct) / pct if pct else 0
            print("\r    %5.1f%%  %6.1fs  ETA %4.0fs" % (pct, el, eta), end="", flush=True)
    ok = wait_for(ser, b"DONE", 30)
    print("\r    %s %s：%d 字节 / %.1f 秒" % ("[完成]" if ok else "[警告] 未收到 DONE",
                                             label, len(data), time.monotonic() - t0))
    return ok


def load_book(path):
    raw = open(path, "rb").read()
    try:
        txt = raw.decode("utf-8")
    except UnicodeDecodeError:
        txt = raw.decode("gbk", errors="replace")
    txt = txt.replace("\r\n", "\n").replace("\r", "\n")
    data = txt.encode("gbk", errors="replace")
    trimmed = 0
    if len(data) > MAX_BOOK:
        cut = MAX_BOOK
        while cut > 0 and data[cut - 1] != 0x0A:
            cut -= 1
        trimmed = len(data) - cut
        data = data[:cut]
    return data, trimmed


def main():
    argv = [a for a in sys.argv[1:]]
    port = None
    if "--port" in argv:
        i = argv.index("--port")
        port = argv[i + 1]
        del argv[i:i + 2]
    with_font = "--font" in argv
    font_only = "--font-only" in argv
    argv = [a for a in argv if a not in ("--font", "--font-only")]

    if font_only:
        with_font = True
    elif not argv:
        print(__doc__)
        return 2

    if not os.path.exists(FONT_MARK):
        with_font = True      # 第一次跑，自动把字库带上

    port = port or pick_port()
    if not port:
        raise SystemExit("找不到串口，请用 --port COMx 指定")
    print("[*] 串口 %s" % port)
    ser = serial.Serial(port, 115200, timeout=0.05)

    try:
        if with_font:
            if not os.path.exists(FONT_PATH):
                raise SystemExit("缺少字库 %s，先运行 python tools/make_font_cn.py" % FONT_PATH)
            font = open(FONT_PATH, "rb").read()
            print("[*] 上传字库：%d 字节（首次使用会自动传一次）" % len(font))
            send_blob(ser, b"F", font, "字库")
            open(FONT_MARK, "w").write("ok")
            if font_only:
                return 0

        path = argv[0]
        data, trimmed = load_book(path)
        print("[*] 电子书：%s" % path)
        print("    原始 %d 字节，GBK 后 %d 字节%s" %
              (os.path.getsize(path), len(data),
               "（超长，已按行裁掉 %d 字节）" % trimmed if trimmed else ""))
        ok = send_blob(ser, b"e", data, "电子书")
        return 0 if ok else 1
    finally:
        ser.close()


if __name__ == "__main__":
    sys.exit(main())
