#!/usr/bin/env python3
"""news-image-20261123 -- draws a one-page newspaper front page that sums up
the world news of Monday 23 November 2026 and writes it to /output/entry.png.

Pure Python 3 standard library: the raster canvas, the 5x7 bitmap font, the
pictograms and the PNG encoder are all written here from scratch. No network,
no clock, no randomness -- the same input always produces the same bytes.
"""

import binascii
import math
import os
import struct
import zlib

W, H = 1024, 1024

PAPER = (247, 243, 234)   # warm newsprint
INK = (18, 18, 18)        # headline black
RED = (176, 42, 32)       # accent red
BLUE = (29, 78, 137)      # accent blue
GREY = (96, 92, 84)       # secondary text
LIGHT = (231, 225, 212)   # panel background
RULE = (120, 114, 102)    # thin rules

# ---------------------------------------------------------------- canvas
PIX = bytearray(PAPER[0] for _ in range(W * H))
_tmp = bytearray(W * H * 3)
for _i in range(W * H):
    _tmp[_i * 3] = PAPER[0]
    _tmp[_i * 3 + 1] = PAPER[1]
    _tmp[_i * 3 + 2] = PAPER[2]
CANVAS = _tmp


def px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        CANVAS[i] = c[0]
        CANVAS[i + 1] = c[1]
        CANVAS[i + 2] = c[2]


def rect(x, y, w, h, c):
    for yy in range(y, y + h):
        base = (yy * W + x) * 3
        for xx in range(w):
            i = base + xx * 3
            if 0 <= x + xx < W and 0 <= yy < H:
                CANVAS[i] = c[0]
                CANVAS[i + 1] = c[1]
                CANVAS[i + 2] = c[2]


def hline(x, y, w, c, t=1):
    for k in range(t):
        rect(x, y + k, w, 1, c)


def vline(x, y, h, c, t=1):
    for k in range(t):
        rect(x + k, y, 1, h, c)


def line(x0, y0, x1, y1, c):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        px(x0, y0, c)
        if x0 == x1 and y0 == y1:
            return
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def circle(cx, cy, r, c, fill=False):
    if fill:
        for yy in range(-r, r + 1):
            half = int(math.sqrt(max(0, r * r - yy * yy)))
            rect(cx - half, cy + yy, half * 2 + 1, 1, c)
        return
    x, y, d = 0, r, 3 - 2 * r
    while x <= y:
        for sx, sy in ((x, y), (y, x), (-x, y), (-y, x),
                       (x, -y), (y, -x), (-x, -y), (-y, -x)):
            px(cx + sx, cy + sy, c)
        if d < 0:
            d += 4 * x + 6
        else:
            d += 4 * (x - y) + 10
            y -= 1
        x += 1


def ellipse(cx, cy, rx, ry, c):
    steps = 160
    for k in range(steps):
        a = 2 * math.pi * k / steps
        px(cx + int(rx * math.cos(a)), cy + int(ry * math.sin(a)), c)


def poly(points, c):
    for a, b in zip(points, points[1:] + points[:1]):
        line(a[0], a[1], b[0], b[1], c)


def fill_poly(points, c):
    # scanline fill for a simple (convex-ish) polygon
    ys = [p[1] for p in points]
    for y in range(min(ys), max(ys) + 1):
        xs = []
        n = len(points)
        for i in range(n):
            x0, y0 = points[i]
            x1, y1 = points[(i + 1) % n]
            if (y0 <= y < y1) or (y1 <= y < y0):
                xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            rect(int(xs[k]), y, max(1, int(xs[k + 1]) - int(xs[k])), 1, c)

# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 bits, written as strings of 0/1, top row first.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    ':': ("00000", "01100", "00000", "00000", "00000", "01100", "00000"),
    ';': ("00000", "01100", "00000", "00000", "01100", "00100", "01000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    '$': ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '*': ("00000", "10101", "01110", "10101", "00000", "00000", "00000"),
    '<': ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    '>': ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
}


def text_w(s, scale):
    return len(s) * 6 * scale - scale


def draw_text(x, y, s, scale, c):
    s = s.upper()
    cx = x
    for ch in s:
        glyph = FONT.get(ch, FONT['?'])
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == '1':
                    rect(cx + col * scale, y + row * scale, scale, scale, c)
        cx += 6 * scale
    return cx


def draw_centered(y, s, scale, c):
    draw_text((W - text_w(s, scale)) // 2, y, s, scale, c)


def wrap(s, max_w, scale):
    lines, cur = [], ""
    for word in s.split(" "):
        trial = word if not cur else cur + " " + word
        if text_w(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def para(x, y, s, max_w, scale, c, leading=None):
    lh = leading if leading is not None else 9 * scale
    for ln in wrap(s, max_w, scale):
        draw_text(x, y, ln, scale, c)
        y += lh
    return y

# ---------------------------------------------------------------- pictograms
def draw_globe(cx, cy, r):
    circle(cx, cy, r, BLUE)
    ellipse(cx, cy, r, r // 3, BLUE)
    ellipse(cx, cy, r // 3, r, BLUE)
    hline(cx - r, cy, 2 * r, BLUE)
    # land blobs
    fill_poly([(cx - r + 6, cy - r // 2), (cx - r // 4, cy - r // 2 - 6),
               (cx - 4, cy - r // 4), (cx - r // 2, cy - 4),
               (cx - r + 2, cy - 8)], BLUE)
    fill_poly([(cx + 6, cy + 4), (cx + r // 2, cy + 2),
               (cx + r - 8, cy + r // 3), (cx + r // 2, cy + r // 2 + 4),
               (cx + 10, cy + r // 2)], BLUE)
    fill_poly([(cx + r // 4, cy - r + 8), (cx + r // 2, cy - r + 12),
               (cx + r // 3, cy - r // 2), (cx + 6, cy - r + 14)], BLUE)


def draw_rubble(cx, cy, w):
    # a broken apartment block: wall with a jagged top, leaning slab
    wx = cx - w // 2
    fill_poly([(wx, cy), (wx, cy - 36), (wx + 20, cy - 30),
               (wx + 34, cy - 38), (wx + w // 2 - 6, cy - 28),
               (wx + w // 2 - 6, cy)], INK)
    for k in range(3):
        rect(wx + 8, cy - 26 + k * 9, w // 2 - 22, 4, PAPER)
    fill_poly([(cx - 6, cy), (cx + w // 2, cy - 20), (cx + w // 2, cy - 8),
               (cx + 10, cy + 2)], GREY)
    poly([(cx - 6, cy), (cx + w // 2, cy - 20), (cx + w // 2, cy - 8),
          (cx + 10, cy + 2)], INK)
    line(cx - w // 2, cy + 6, cx + w // 2, cy + 6, INK)
    for dx in (-18, -4, 12, 26):
        circle(cx + dx, cy + 12, 3, GREY, fill=True)


def draw_chart(cx, cy, w, h):
    # falling market line with red arrow
    vline(cx - w // 2, cy - h // 2, h, INK, 2)
    hline(cx - w // 2, cy + h // 2, w, INK, 2)
    pts = [(cx - w // 2 + 4, cy - h // 2 + 8), (cx - w // 4, cy - 2),
           (cx, cy - h // 2 + 16), (cx + w // 4, cy + 10),
           (cx + w // 2 - 4, cy + h // 2 - 6)]
    for a, b in zip(pts, pts[1:]):
        line(a[0], a[1], b[0], b[1], RED)
        line(a[0], a[1] + 1, b[0], b[1] + 1, RED)
    ax, ay = pts[-1]
    fill_poly([(ax, ay + 8), (ax - 10, ay - 2), (ax + 2, ay - 6)], RED)


def draw_tanker(cx, cy, w):
    # oil tanker on waves, with a plume of smoke
    fill_poly([(cx - w // 2, cy), (cx + w // 2, cy), (cx + w // 2 - 10, cy + 16),
               (cx - w // 2 + 10, cy + 16)], INK)
    rect(cx - w // 4, cy - 16, 10, 16, INK)
    rect(cx + w // 8, cy - 12, 8, 12, INK)
    for k in range(3):
        circle(cx - w // 2 + 14 + k * 8, cy - 24 - k * 4, 4, GREY, fill=True)
    for dx in (-w // 2 - 6, -w // 4, 0, w // 4, w // 2 - 6):
        line(cx + dx, cy + 24, cx + dx + 12, cy + 24, BLUE)


def draw_warship(cx, cy, w):
    fill_poly([(cx - w // 2, cy), (cx + w // 2, cy), (cx + w // 2 - 8, cy + 14),
               (cx - w // 2 + 12, cy + 14)], BLUE)
    rect(cx - 6, cy - 22, 12, 22, BLUE)
    line(cx - 4, cy - 22, cx - 4, cy - 34, BLUE)
    line(cx + 4, cy - 22, cx + 4, cy - 30, BLUE)
    fill_poly([(cx + 4, cy - 34), (cx + 22, cy - 30), (cx + 4, cy - 26)], RED)
    for dx in (-w // 2 - 4, -w // 4, w // 4, w // 2 - 8):
        line(cx + dx, cy + 22, cx + dx + 10, cy + 22, BLUE)


def draw_badge(cx, cy, r):
    # a police badge / star
    pts = []
    for k in range(10):
        ang = -math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * 0.45
        pts.append((cx + int(rr * math.cos(ang)), cy + int(rr * math.sin(ang))))
    fill_poly(pts, RED)
    circle(cx, cy, r // 3, PAPER, fill=True)
    circle(cx, cy, r // 3, RED)


# ---------------------------------------------------------------- PNG encoder
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)
    return out


def encode_png():
    raw = bytearray()
    prev = bytearray(W * 3)
    for y in range(H):
        row = CANVAS[y * W * 3:(y + 1) * W * 3]
        if y == 0:
            raw.append(0)
            raw += row
        else:
            raw.append(2)  # Up filter
            for i in range(W * 3):
                raw.append((row[i] - prev[i]) & 0xFF)
        prev = row
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + _chunk(b"IEND", b""))


# ---------------------------------------------------------------- the page
def kicker(x, y, label, c=RED):
    draw_text(x, y, label, 2, c)
    return y + 16


def story(x, y, w, label, head, body, icon, head_scale=3):
    kicker(x, y, label)
    hy = y + 18
    for ln in wrap(head, w, head_scale):
        draw_text(x, hy, ln, head_scale, INK)
        hy += 9 * head_scale + 2
    iy = hy + 8
    icon(x + w // 2, iy + 34)
    by = iy + 78
    para(x, by, body, w, 2, INK, leading=17)
    return by


def build():
    # masthead
    draw_centered(26, "THE WORLD TODAY", 8, INK)
    hline(28, 96, W - 56, INK, 3)
    draw_centered(108, "MONDAY, 23 NOVEMBER 2026", 3, RED)
    draw_text(28, 108, "ONE DAY - ONE PICTURE", 2, GREY)
    r = "THE WORLD IN ONE PAGE"
    draw_text(W - 28 - text_w(r, 2), 108, r, 2, GREY)
    hline(28, 136, W - 56, INK, 1)
    hline(28, 140, W - 56, INK, 3)

    # ---- lead story: COP31 collapses (full width band)
    y = 158
    rect(28, y, W - 56, 236, LIGHT)
    # thin frame
    hline(28, y, W - 56, INK, 2)
    hline(28, y + 234, W - 56, INK, 2)
    vline(28, y, 236, INK, 2)
    vline(W - 30, y, 236, INK, 2)
    gx = 28 + 130
    draw_globe(gx, y + 118, 82)
    line(gx - 82, y + 118 + 82, gx + 82, y + 118 - 82, RED)
    line(gx - 82, y + 118 + 82, gx + 82, y + 118 - 82, RED)
    tx = 28 + 250
    kicker(tx, y + 16, "CLIMATE - ANTALYA, TURKEY")
    hy = y + 36
    for ln in ("COP31", "COLLAPSES"):
        draw_text(tx, hy, ln, 6, INK)
        hy += 58
    draw_text(tx, hy + 2, "CLIMATE TALKS END WITH NO DEAL", 3, RED)
    para(tx, hy + 34, "The UN climate summit in Antalya ended with no "
         "agreement after the EU and about 130 countries rejected a draft "
         "text that left out fossil fuels.", W - 56 - 250 - 24, 2, INK,
         leading=16)

    # ---- row of two: Ukraine strike + markets
    y = 412
    half = (W - 56 - 24) // 2
    vline(28 + half + 12, y, 250, RULE, 1)
    hline(28, y + 250, W - 56, RULE, 1)
    story(28, y + 12, half, "UKRAINE - DYMER, NEAR KYIV",
          "STRIKE KILLS 10 NEAR KYIV",
          "A Russian attack hits a block of flats; a boy of 7 is pulled "
          "alive from the rubble as rescuers search for the missing.",
          lambda cx, cy: draw_rubble(cx, cy, 150))
    story(28 + half + 24, y + 12, half, "MARKETS - TOKYO & NEW YORK",
          "AI SELL-OFF SHAKES MARKETS",
          "Tokyo's Nikkei falls 5.06% and the S&P 500 drops 3.7% on fears "
          "AI shares are overpriced; US futures rebound on Monday.",
          lambda cx, cy: draw_chart(cx, cy, 170, 64))

    # ---- row of three: Iran, Libya, Mexico
    y = 678
    third = (W - 56 - 48) // 3
    for k in (1, 2):
        vline(28 + third * k + 24 * k - 12, y, 252, RULE, 1)
    hline(28, y + 252, W - 56, RULE, 1)
    story(28, y + 12, third, "MIDDLE EAST - BAHRAIN",
          "IRAN HITS US BASE IN BAHRAIN",
          "Missiles and drones wound two; Trump threatens to sink "
          "Iranian vessels as tankers are hit in the Strait of Hormuz.",
          lambda cx, cy: draw_tanker(cx, cy, 170), head_scale=2)
    story(28 + third + 24, y + 12, third, "LIBYA - BENGHAZI",
          "RUSSIAN FRIGATE SUNK OFF LIBYA",
          "The Merkury is hit by a suspected Ukrainian sea drone at "
          "Benghazi; ten crew members are hurt.",
          lambda cx, cy: draw_warship(cx, cy, 170), head_scale=2)
    story(28 + 2 * third + 48, y + 12, third, "MEXICO - SINALOA",
          "'EL CHAPO ISIDRO' CAPTURED",
          "FBI most-wanted cartel boss Fausto Isidro Meza-Flores is "
          "seized and faces extradition to the United States.",
          lambda cx, cy: draw_badge(cx, cy, 34), head_scale=2)

    # ---- footer strip
    y = 946
    hline(28, y, W - 56, INK, 2)
    draw_text(28, y + 10, "ALSO TODAY:", 2, RED)
    para(28, y + 28, "Drone strikes kill five children in Khartoum, Sudan. "
         "Marc Marquez wins an eighth MotoGP title. Carlos Alcaraz wins "
         "the ATP Finals.", W - 56, 2, INK, leading=16)


def main():
    build()
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "entry.png"), "wb") as f:
        f.write(encode_png())


if __name__ == "__main__":
    main()
