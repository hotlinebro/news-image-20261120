#!/usr/bin/env python3
"""news-image-20261120: one image summing up Friday, November 20, 2026.

Pure Python 3.13 stdlib. Draws a light, airy newspaper front page:
masthead, three large hero scenes, a numbered world map, a 16-story
grid and a numbers strip. Deterministic: same bytes on every run.
Writes entry.png to $MAKEFUN_OUTPUT_DIR (default /output).
"""
import os
import struct
import zlib

W, H = 1024, 1024

PAPER = (246, 241, 227)
INK = (30, 27, 22)
CARD = (255, 255, 255)
RED = (192, 57, 43)
NAVY = (31, 58, 95)
TEAL = (20, 102, 107)
SAND = (232, 220, 192)
SEA = (215, 230, 232)
LAND = (233, 223, 190)
GREY = (107, 101, 88)
LIGHTGREY = (210, 204, 188)
ORANGE = (230, 126, 34)
YELLOW = (241, 196, 15)
DARKNAVY = (22, 35, 58)
DARKTEAL = (16, 68, 74)
SKY = (58, 74, 90)

# ---------------------------------------------------------------- PNG writer
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(path, rgb, width, height):
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = width * 3
    for y in range(height):
        raw.append(0)
        raw += rgb[y * stride:(y + 1) * stride]
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


# ---------------------------------------------------------------- Canvas
class Canvas:
    def __init__(self, width, height, bg):
        self.w = width
        self.h = height
        self.px = bytearray(bg * (width * height))
        self.clip = None

    def set_clip(self, x, y, w, h):
        self.clip = (x, y, x + w, y + h)

    def clear_clip(self):
        self.clip = None

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            if self.clip is not None:
                cx0, cy0, cx1, cy1 = self.clip
                if not (cx0 <= x < cx1 and cy0 <= y < cy1):
                    return
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def fill_rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if self.clip is not None:
            cx0, cy0, cx1, cy1 = self.clip
            x0 = max(x0, cx0)
            y0 = max(y0, cy0)
            x1 = min(x1, cx1)
            y1 = min(y1, cy1)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def rect(self, x, y, w, h, color, t=1):
        self.fill_rect(x, y, w, t, color)
        self.fill_rect(x, y + h - t, w, t, color)
        self.fill_rect(x, y, t, h, color)
        self.fill_rect(x + w - t, y, t, h, color)

    def hline(self, x, y, w, color, t=1):
        self.fill_rect(x, y, w, t, color)

    def vline(self, x, y, h, color, t=1):
        self.fill_rect(x, y, t, h, color)

    def line(self, x0, y0, x1, y1, color, t=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.fill_rect(x0, y0, t, t, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, color)

    def ellipse(self, cx, cy, rx, ry, color):
        for yy in range(cy - ry, cy + ry + 1):
            for xx in range(cx - rx, cx + rx + 1):
                if ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1.0:
                    self.set(xx, yy, color)

    def ellipse_outline(self, cx, cy, rx, ry, color, t=2):
        steps = max(48, int(3.14159 * (rx + ry)))
        for i in range(steps + 1):
            a = 2 * 3.14159 * i / steps
            import math
            x = int(cx + rx * math.cos(a))
            y = int(cy + ry * math.sin(a))
            self.fill_rect(x, y, t, t, color)

    def polygon(self, pts, color):
        # Scanline fill of a simple polygon.
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for y in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    x = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
                    xs.append(x)
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                xa = max(0, int(xs[j]))
                xb = min(self.w, int(xs[j + 1]) + 1)
                if xb > xa:
                    self.fill_rect(xa, y, xb - xa, 1, color)


# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 pixels, '#' = ink.
FONT = {
    "A": ("..#..", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "(": ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ")": ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
}

FONT.update({
    "a": (".....", ".....", ".###.", "....#", ".####", "#...#", ".####"),
    "b": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "####."),
    "c": (".....", ".....", ".####", "#....", "#....", "#....", ".####"),
    "d": ("....#", "....#", ".####", "#...#", "#...#", "#...#", ".####"),
    "e": (".....", ".....", ".###.", "#...#", "#####", "#....", ".###."),
    "f": ("..##.", ".#..#", ".#...", "####.", ".#...", ".#...", ".#..."),
    "g": (".....", ".####", "#...#", "#...#", ".####", "....#", ".###."),
    "h": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "i": (".....", "..#..", ".....", ".##..", "..#..", "..#..", ".###."),
    "j": (".....", "...#.", ".....", "..##.", "...#.", "...#.", "...#.", ".##.."),
    "k": ("#....", "#....", "#..#.", "#.#..", "##...", "#.#..", "#..#."),
    "l": (".##..", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "m": (".....", ".....", "##.#.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"),
    "n": (".....", ".....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "o": (".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."),
    "p": (".....", ".....", "####.", "#...#", "#...#", "####.", "#....", "#...."),
    "q": (".....", ".....", ".####", "#...#", "#...#", ".####", "....#", "....#"),
    "r": (".....", ".....", "#.##.", "##..#", "#....", "#....", "#...."),
    "s": (".....", ".....", ".####", "#....", ".###.", "....#", "####."),
    "t": (".#...", ".#...", "####.", ".#...", ".#...", ".#...", "..##."),
    "u": (".....", ".....", "#...#", "#...#", "#...#", "#...#", ".###."),
    "v": (".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "w": (".....", ".....", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."),
    "x": (".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"),
    "y": (".....", ".....", "#...#", "#...#", ".####", "....#", ".###."),
    "z": (".....", ".....", "#####", "...#.", "..#..", ".#...", "#####"),
})


def text_width(s, scale):
    return len(s) * 6 * scale


def draw_text(cv, s, x, y, scale, color, align="left"):
    if align == "center":
        x = x - text_width(s, scale) // 2
    elif align == "right":
        x = x - text_width(s, scale)
    cx = x
    for ch in s:
        glyph = FONT.get(ch)
        if glyph is None:
            cx += 6 * scale
            continue
        for row, bits in enumerate(glyph):
            for col, bit in enumerate(bits):
                if bit == "#":
                    cv.fill_rect(cx + col * scale, y + row * scale,
                                 scale, scale, color)
        cx += 6 * scale
    return cx


def wrap_text(s, max_width, scale):
    """Greedy word wrap; returns list of lines that fit max_width."""
    words = s.split(" ")
    lines = []
    cur = ""
    for w in words:
        trial = (cur + " " + w).strip()
        if text_width(trial, scale) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_lines(cv, lines, x, y, scale, color, line_h, align="left"):
    for ln in lines:
        draw_text(cv, ln, x, y, scale, color, align=align)
        y += line_h
    return y

# ---------------------------------------------------------------- Story data
# All 16 stories verified as Friday, November 20, 2026 events.
# Three single-source "VERIFY" items from prep were re-checked and
# DROPPED: Italy/Meta fine (Nov 14), FAA ground stop (Nov 13),
# IMF debt warning (Nov 19). No 19-Nov event is used as a hero.
HEROES = [
    ("CYCLONE AKVAN", "HITS ODISHA",
     "300,000 evacuated as the storm makes landfall"),
    ("KYIV BRIDGES", "HIT OVERNIGHT",
     "Russian strikes cut power across the capital"),
    ("COP31 DEADLOCK", "ON FINAL DAY",
     "Fossil-fuel wording dropped from draft text"),
]

STORIES = [
    "Cyclone Akvan hits Odisha",
    "Kyiv bridges hit, power cut",
    "COP31 deadlocked on final day",
    "Russia violates Polish airspace",
    "Estonia shuts Russia border",
    "Saudi stops Houthi missile",
    "US, Venezuela restore army ties",
    "Youth march in 25+ nations",
    "Kenya clears last Ebola case",
    "Nikkei falls 4.8% in Tokyo",
    "Iraq deploys at militia base",
    "Argentina passes disability law",
    "RAF Fairford trial set for 2027",
    "EU to summon Russian envoy",
    "Pakistan kills 22 militants",
    "India eases ship-age rules",
]

STATS = [
    ("300,000", "EVACUATED"),
    ("3", "BRIDGES HIT"),
    ("21", "ISSUES OPEN"),
    ("25+", "NATIONS"),
    ("-4.8%", "NIKKEI FALL"),
    ("37", "EBOLA DAYS"),
]

# Map dots: (lon, lat, dx, dy) — dx/dy nudge crowded European dots.
DOTS = [
    (84.9, 19.3, 0, 0),    # 1 Odisha
    (30.5, 50.45, 16, 4),  # 2 Kyiv
    (30.7, 36.9, 2, 8),    # 3 Antalya
    (21.0, 52.2, 8, 15),   # 4 Warsaw
    (24.7, 59.4, 6, -18),  # 5 Tallinn
    (46.7, 24.6, 6, 6),    # 6 Riyadh
    (-66.9, 10.5, 0, 0),   # 7 Caracas
    (13.4, 52.5, 10, -14), # 8 Berlin
    (36.8, -1.3, 0, 0),    # 9 Nairobi
    (139.7, 35.7, 0, 0),   # 10 Tokyo
    (44.4, 33.3, -1, -4),  # 11 Baghdad
    (-58.4, -34.6, 0, 0),  # 12 Buenos Aires
    (-0.1, 51.5, -30, -10), # 13 London
    (4.35, 50.85, -19, 24),  # 14 Brussels
    (71.6, 34.0, -5, -4),  # 15 Peshawar
    (72.8, 19.1, 0, 0),    # 16 Mumbai
]

MAP_X, MAP_Y, MAP_W, MAP_H = 24, 420, 976, 248


def proj(lon, lat):
    x = MAP_X + (lon + 168.0) / 360.0 * MAP_W
    y = MAP_Y + (78.0 - lat) / 136.0 * MAP_H
    return (int(x), int(y))


def proj_poly(lonlat):
    return [proj(lon, lat) for lon, lat in lonlat]


NA = [(-168, 66), (-162, 60), (-155, 58), (-148, 60), (-140, 60), (-135, 58),
      (-130, 54), (-126, 49), (-124, 42), (-121, 35), (-114, 29), (-110, 24),
      (-105, 20), (-97, 16), (-93, 15), (-89, 13), (-85, 11), (-82, 9),
      (-79, 9), (-81, 12), (-84, 15), (-87, 14), (-89, 18), (-92, 19),
      (-96, 19), (-97, 25), (-94, 29), (-89, 30), (-84, 30), (-81, 26),
      (-80, 32), (-76, 35), (-74, 39), (-71, 41), (-69, 44), (-66, 45),
      (-60, 47), (-56, 48), (-60, 52), (-64, 58), (-68, 57), (-70, 60),
      (-76, 62), (-82, 66), (-90, 66), (-94, 68), (-100, 68), (-110, 68),
      (-120, 69), (-130, 70), (-140, 70), (-150, 70), (-158, 71),
      (-165, 69), (-168, 66)]
GREENLAND = [(-58, 64), (-53, 60), (-44, 60), (-40, 64), (-32, 68),
             (-24, 70), (-20, 73), (-24, 77), (-32, 80), (-42, 80),
             (-52, 78), (-58, 75), (-60, 70), (-58, 64)]
SA = [(-79, 9), (-77, 4), (-80, -3), (-81, -6), (-77, -12), (-72, -18),
      (-70, -24), (-70, -31), (-73, -37), (-74, -44), (-71, -50),
      (-68, -52), (-66, -55), (-67, -50), (-63, -42), (-58, -38),
      (-52, -33), (-48, -28), (-42, -23), (-39, -17), (-35, -9),
      (-35, -6), (-40, -3), (-44, -2), (-50, 0), (-53, 4), (-58, 6),
      (-62, 9), (-68, 11), (-73, 11), (-77, 8), (-79, 9)]
AFRICA = [(-6, 35), (-10, 31), (-15, 27), (-17, 21), (-17, 15), (-16, 12),
          (-13, 8), (-8, 5), (-4, 5), (0, 6), (6, 4), (9, 4), (9, -1),
          (12, -5), (13, -11), (12, -17), (14, -22), (15, -27), (18, -33),
          (25, -34), (31, -29), (34, -26), (36, -22), (40, -16), (40, -11),
          (42, -5), (46, -1), (51, 2), (51, 11), (48, 11), (44, 11),
          (41, 13), (39, 16), (37, 20), (35, 24), (33, 28), (31, 31),
          (27, 32), (22, 33), (17, 33), (12, 34), (10, 37), (6, 37),
          (-2, 35), (-6, 35)]
EUROPE = [(-10, 36), (-9, 43), (-2, 44), (-1, 48), (1, 51), (4, 53),
          (8, 55), (8, 57), (11, 59), (6, 60), (5, 62), (10, 64),
          (15, 67), (20, 70), (26, 71), (30, 70), (30, 67), (26, 64),
          (22, 60), (24, 58), (28, 59), (30, 58), (27, 55), (24, 54),
          (20, 54), (16, 54), (12, 54), (8, 56), (5, 53), (3, 50),
          (0, 46), (3, 43), (0, 40), (-3, 37), (-7, 36), (-10, 36)]
ASIA = [(30, 36), (33, 36), (36, 36), (36, 33), (40, 31), (43, 30),
        (47, 30), (50, 29), (53, 28), (56, 26), (58, 25), (61, 25),
        (64, 25), (66, 24), (67, 22), (70, 20), (72, 20), (74, 19),
        (76, 17), (78, 15), (80, 13), (80, 10), (77, 8), (80, 7),
        (83, 9), (86, 12), (88, 15), (89, 18), (91, 22), (92, 21),
        (94, 17), (96, 16), (98, 12), (99, 9), (100, 7), (101, 5),
        (103, 2), (104, 1), (103, 4), (101, 7), (100, 10), (98, 14),
        (96, 18), (94, 22), (92, 22), (90, 22), (88, 22), (86, 20),
        (84, 18), (82, 16), (80, 14), (78, 12), (76, 10), (74, 12),
        (72, 16), (70, 20), (68, 22), (66, 25), (63, 25), (60, 25),
        (57, 26), (54, 27), (51, 29), (48, 30), (44, 29), (42, 31),
        (39, 32), (36, 36), (33, 36), (30, 36)]
SUMATRA = [(95, 5), (98, 2), (100, -1), (102, -3), (104, -5), (106, -6),
           (104, -5), (101, -2), (98, 1), (95, 5)]
BORNEO = [(109, 1), (112, 4), (116, 6), (118, 2), (117, -2), (114, -3),
          (110, -2), (109, 1)]
JAVA = [(105, -6), (108, -7), (112, -7), (114, -8), (114, -9), (110, -8),
        (106, -7), (105, -6)]
NEWGUINEA = [(131, -1), (136, -2), (141, -3), (146, -6), (150, -8),
             (147, -9), (143, -8), (139, -7), (135, -4), (131, -1)]
JAPAN = [(130, 31), (132, 33), (134, 34), (136, 35), (138, 35), (140, 36),
         (141, 39), (141, 41), (143, 42), (145, 44), (143, 44), (141, 42),
         (140, 39), (139, 37), (137, 35), (135, 34), (133, 33), (131, 32),
         (130, 31)]
UK = [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53),
      (-1, 51), (-3, 50), (-5, 50)]
AUSTRALIA = [(114, -22), (114, -30), (115, -34), (119, -34), (124, -33),
             (129, -32), (132, -32), (135, -35), (138, -35), (140, -38),
             (145, -38), (147, -39), (150, -37), (153, -32), (153, -27),
             (151, -24), (149, -21), (146, -19), (143, -15), (142, -11),
             (141, -13), (138, -12), (136, -12), (135, -15), (132, -12),
             (130, -13), (127, -14), (124, -16), (122, -17), (119, -20),
             (116, -21), (114, -22)]
NZ = [(167, -45), (170, -42), (173, -40), (175, -38), (178, -37),
      (176, -40), (174, -42), (171, -43), (168, -46), (167, -45)]
LAND_POLYS = [NA, GREENLAND, SA, AFRICA, EUROPE, ASIA, SUMATRA, BORNEO,
              JAVA, NEWGUINEA, JAPAN, UK, AUSTRALIA, NZ]


# ---------------------------------------------------------------- Hero scenes
def scene_storm(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h, SKY)
    cv.ellipse(x + 40, y + 18, 70, 16, (46, 60, 74))
    cv.ellipse(x + 180, y + 8, 80, 18, (46, 60, 74))
    cv.ellipse(x + 110, y + 30, 60, 12, (52, 66, 80))
    # lightning
    cv.line(x + 200, y + 22, x + 188, y + 48, YELLOW, 3)
    cv.line(x + 188, y + 48, x + 198, y + 48, YELLOW, 3)
    cv.line(x + 198, y + 48, x + 186, y + 74, YELLOW, 3)
    # rain
    rain = (178, 190, 196)
    for rx in range(x + 8, x + w - 8, 22):
        cv.line(rx, y + 52, rx - 8, y + 78, rain, 2)
        cv.line(rx + 10, y + 66, rx + 2, y + 92, rain, 2)
    # sea
    cv.fill_rect(x, y + h - 62, w, 62, DARKTEAL)
    cv.fill_rect(x, y + h - 62, w, 3, (120, 180, 180))
    wave = (190, 220, 220)
    cv.ellipse_outline(x + 70, y + h - 34, 62, 12, wave, 3)
    cv.ellipse_outline(x + 200, y + h - 22, 70, 12, wave, 3)
    cv.ellipse_outline(x + 260, y + h - 44, 55, 10, wave, 3)
    cv.ellipse_outline(x + 130, y + h - 12, 58, 9, wave, 3)


def scene_bridge(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h, DARKNAVY)
    for sx, sy in [(30, 14), (90, 30), (160, 12), (250, 26), (290, 10),
                   (60, 48), (210, 44), (280, 52)]:
        cv.fill_rect(x + sx, y + sy, 2, 2, (220, 225, 235))
    cv.circle(x + w - 42, y + 30, 14, (235, 230, 200))
    # river
    cv.fill_rect(x, y + h - 34, w, 34, (14, 26, 48))
    cv.fill_rect(x + 40, y + h - 22, 60, 2, ORANGE)
    cv.fill_rect(x + 180, y + h - 14, 70, 2, (120, 140, 170))
    # bridge deck + arches + towers
    deck_y = y + h - 62
    cv.fill_rect(x + 10, deck_y, w - 20, 6, (150, 155, 165))
    cv.ellipse_outline(x + 85, deck_y + 2, 58, 20, (150, 155, 165), 3)
    cv.ellipse_outline(x + 235, deck_y + 2, 58, 20, (150, 155, 165), 3)
    for ax in (85, 235):
        for off in (-30, 0, 30):
            cv.vline(x + ax + off, deck_y - 14, 14, (150, 155, 165), 2)
    cv.fill_rect(x + 78, y + 34, 6, deck_y - y - 30, (150, 155, 165))
    cv.fill_rect(x + 228, y + 34, 6, deck_y - y - 30, (150, 155, 165))
    # fire on the deck
    fx = x + 158
    cv.polygon([(fx - 16, deck_y), (fx, deck_y - 34), (fx + 16, deck_y)],
               ORANGE)
    cv.polygon([(fx - 9, deck_y), (fx, deck_y - 20), (fx + 9, deck_y)],
               YELLOW)
    cv.circle(fx - 24, deck_y - 6, 7, ORANGE)
    cv.circle(fx + 26, deck_y - 4, 5, ORANGE)
    # smoke
    cv.circle(fx - 6, deck_y - 46, 12, (120, 122, 128))
    cv.circle(fx + 10, deck_y - 62, 15, (100, 102, 108))
    cv.circle(fx + 2, deck_y - 80, 11, (90, 92, 98))


def scene_cop(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h, SAND)
    # screen
    sx = x + (w - 190) // 2
    cv.fill_rect(sx, y + 12, 190, 58, NAVY)
    cv.rect(sx, y + 12, 190, 58, INK, 2)
    draw_text(cv, "COP31", sx + 95, y + 20, 4, CARD, align="center")
    draw_text(cv, "ANTALYA", sx + 95, y + 50, 2, (200, 210, 225),
              align="center")
    # flags row
    flag_cols = [(31, 58, 95), (192, 57, 43), (20, 102, 107),
                 (230, 126, 34), (90, 120, 60)]
    for i, fc in enumerate(flag_cols):
        fx = x + 52 + i * 46
        cv.fill_rect(fx, y + 82, 26, 16, fc)
        cv.rect(fx, y + 82, 26, 16, INK, 1)
    # delegates behind the table
    for i, cc in enumerate([(120, 60, 60), (60, 90, 120), (150, 120, 60),
                            (80, 80, 90), (110, 110, 110)]):
        dx = x + 46 + i * 52
        cv.circle(dx + 12, y + 112, 9, cc)
        cv.fill_rect(dx, y + 122, 24, 12, cc)
    # table
    cv.polygon([(x + 8, y + h - 8), (x + w - 8, y + h - 8),
                (x + w - 26, y + 132), (x + 26, y + 132)], (122, 84, 52))
    cv.fill_rect(x + 60, y + 140, 34, 10, CARD)
    cv.fill_rect(x + 140, y + 140, 34, 10, CARD)
    cv.fill_rect(x + 220, y + 140, 34, 10, CARD)

# ---------------------------------------------------------------- Compose
def compose():
    cv = Canvas(W, H, PAPER)
    # Masthead
    draw_text(cv, "THE WORLD IN ONE DAY", 24, 24, 2, RED)
    draw_text(cv, "FRIDAY, NOVEMBER 20, 2026", 24, 46, 5, INK)
    cv.fill_rect(812, 22, 188, 64, RED)
    draw_text(cv, "16 STORIES", 906, 32, 2, CARD, align="center")
    draw_text(cv, "5 CONTINENTS", 906, 52, 2, CARD, align="center")
    draw_text(cv, "Storms, war, climate talks and markets - one day, "
                  "in one picture.", 24, 100, 2, GREY)
    cv.hline(24, 126, 976, INK, 2)

    # Heroes
    scenes = [scene_storm, scene_bridge, scene_cop]
    hero_x = [24, 353, 682]
    for i, (l1, l2, sub) in enumerate(HEROES):
        x = hero_x[i]
        y = 138
        cv.fill_rect(x, y, 318, 272, CARD)
        cv.rect(x, y, 318, 272, INK, 2)
        cv.set_clip(x + 2, y + 2, 314, 158)
        scenes[i](cv, x + 2, y + 2, 314, 158)
        cv.clear_clip()
        draw_text(cv, l1, x + 16, y + 170, 3, INK)
        draw_text(cv, l2, x + 16, y + 196, 3, INK)
        sub_lines = wrap_text(sub, 302, 2)
        draw_lines(cv, sub_lines[:2], x + 16, y + 228, 2, GREY, 16)

    # World map
    cv.fill_rect(MAP_X, MAP_Y, MAP_W, MAP_H, SEA)
    cv.rect(MAP_X, MAP_Y, MAP_W, MAP_H, INK, 2)
    for poly in LAND_POLYS:
        pts = proj_poly(poly)
        cv.polygon(pts, LAND)
    draw_text(cv, "ONE DOT PER STORY", 988, 430, 2, GREY, align="right")
    for label, lon, lat in [("NORTH AMERICA", -100, 48),
                            ("SOUTH AMERICA", -62, -12),
                            ("AFRICA", 10, 15),
                            ("ASIA", 95, 55),
                            ("AUSTRALIA", 134, -25)]:
        lx, ly = proj(lon, lat)
        draw_text(cv, label, lx, ly, 2, GREY)
    for i, (lon, lat, dx, dy) in enumerate(DOTS, start=1):
        cx, cy = proj(lon, lat)
        cx += dx
        cy += dy
        cv.circle(cx, cy, 13, CARD)
        cv.circle(cx, cy, 12, RED)
        draw_text(cv, str(i), cx, cy - 7, 2, CARD, align="center")

    # Story grid
    grid_y = [680, 745, 810, 875]
    grid_x = [24, 270, 516, 762]
    for idx, story in enumerate(STORIES):
        row, col = divmod(idx, 4)
        x = grid_x[col]
        y = grid_y[row]
        cv.fill_rect(x, y, 236, 57, CARD)
        cv.rect(x, y, 236, 57, LIGHTGREY, 1)
        cv.fill_rect(x, y, 4, 57, RED)
        draw_text(cv, str(idx + 1), x + 38, y + 8, 2, RED, align="right")
        lines = wrap_text(story, 182, 2)
        draw_lines(cv, lines[:3], x + 46, y + 8, 2, INK, 15)

    # Numbers strip
    strip_x = [24, 188, 352, 516, 680, 844]
    for i, (num, label) in enumerate(STATS):
        x = strip_x[i]
        y = 944
        cv.fill_rect(x, y, 156, 48, CARD)
        cv.rect(x, y, 156, 48, INK, 1)
        draw_text(cv, num, x + 78, y + 6, 3, RED, align="center")
        draw_text(cv, label, x + 78, y + 30, 2, INK, align="center")

    draw_text(cv, "ALL EVENTS FRIDAY, NOVEMBER 20, 2026", 512, 1002, 2,
              GREY, align="center")
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    cv = compose()
    path = os.path.join(out_dir, "entry.png")
    write_png(path, bytes(cv.px), W, H)
    print("wrote", path, os.path.getsize(path), "bytes")


if __name__ == "__main__":
    main()
