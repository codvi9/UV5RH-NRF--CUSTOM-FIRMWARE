#!/usr/bin/env python3
"""Build a GB2312 16x16 bitmap font for the radio.

Layout: 94x94 grid, 32 bytes per glyph (2 bytes per row, MSB = leftmost),
index = (b0-0xA1)*94 + (b1-0xA1). Size = 8836*32 = 282752 bytes.
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

FONT = r"C:\Windows\Fonts\simhei.ttf"
OUT = "fw/font_cn.bin"


def main():
    f = ImageFont.truetype(FONT, 16)
    buf = bytearray(94 * 94 * 32)
    ok = 0
    for b0 in range(0xA1, 0xF8):
        for b1 in range(0xA1, 0xFF):
            idx = (b0 - 0xA1) * 94 + (b1 - 0xA1)
            try:
                ch = bytes([b0, b1]).decode("gb2312")
            except UnicodeDecodeError:
                continue
            img = Image.new("L", (16, 16), 0)
            d = ImageDraw.Draw(img)
            d.text((0, -1), ch, font=f, fill=255)
            px = img.load()
            base = idx * 32
            for y in range(16):
                lo = hi = 0
                for x in range(8):
                    if px[x, y] > 100:
                        hi |= 1 << (7 - x)
                for x in range(8, 16):
                    if px[x, y] > 100:
                        lo |= 1 << (15 - x)
                buf[base + y * 2] = hi
                buf[base + y * 2 + 1] = lo
            ok += 1
    open(OUT, "wb").write(buf)
    print("wrote %s: %d bytes, %d glyphs" % (OUT, len(buf), ok))


if __name__ == "__main__":
    sys.exit(main())
