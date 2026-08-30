"""PNG post-processing with no third-party dependency.

Two operations earn their place: a binary alpha, because the transparent
background preview feathers the edges of flat shapes and that halo reads as a
smudge on a light surface, and a downscale, because an icon is validated at the
size it is displayed, not at the size it is rendered.
"""
from __future__ import annotations

import struct
import zlib
from pathlib import Path

Rows = list[bytearray]


class PngError(RuntimeError):
    pass


def read_rgba(path: Path) -> tuple[int, int, Rows]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise PngError(f"{path} is not a PNG")
    position, compressed = 8, bytearray()
    width = height = 0
    while position < len(data):
        length = struct.unpack(">I", data[position:position + 4])[0]
        kind = data[position + 4:position + 8]
        chunk = data[position + 8:position + 8 + length]
        if kind == b"IHDR":
            width, height, depth, color = struct.unpack(">IIBB", chunk[:10])
            if depth != 8 or color not in (2, 6):
                raise PngError("expected an 8-bit RGB or RGBA PNG")
            channels = 4 if color == 6 else 3
        elif kind == b"IDAT":
            compressed += chunk
        elif kind == b"IEND":
            break
        position += 12 + length
    rows = _unfilter(zlib.decompress(bytes(compressed)), width, height, channels)
    return width, height, rows if channels == 4 else _add_alpha(rows)


def write_rgba(path: Path, width: int, height: int, rows: Rows) -> None:
    raw = bytearray()
    for row in rows:
        raw.append(0)
        raw += row
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        # Level 9 measured at 0.437s/423024 bytes on a 1024x1024 photographic
        # fixture, level 6 at 0.069s/429239 bytes: 6.3x faster for 1.5% larger.
        + _chunk(b"IDAT", zlib.compress(bytes(raw), 6))
        + _chunk(b"IEND", b"")
    )


def harden_alpha(path: Path, threshold: int = 128) -> int:
    width, height, rows = read_rgba(path)
    snapped = 0
    for row in rows:
        for offset in range(3, len(row), 4):
            alpha = row[offset]
            if alpha in (0, 255):
                continue
            row[offset] = 255 if alpha >= threshold else 0
            snapped += 1
    write_rgba(path, width, height, rows)
    return snapped


def downscale(path: Path, target: int, out: Path) -> Path:
    width, height, rows = read_rgba(path)
    scale_x, scale_y = width / target, height / target
    scaled: Rows = []
    for y in range(target):
        line = bytearray(target * 4)
        y0, y1 = int(y * scale_y), max(int((y + 1) * scale_y), int(y * scale_y) + 1)
        for x in range(target):
            x0, x1 = int(x * scale_x), max(int((x + 1) * scale_x), int(x * scale_x) + 1)
            totals = [0, 0, 0, 0]
            samples = 0
            for source_y in range(y0, min(y1, height)):
                row = rows[source_y]
                for source_x in range(x0, min(x1, width)):
                    base = source_x * 4
                    for channel in range(4):
                        totals[channel] += row[base + channel]
                    samples += 1
            base = x * 4
            for channel in range(4):
                line[base + channel] = totals[channel] // samples if samples else 0
        scaled.append(line)
    write_rgba(out, target, target, scaled)
    return out


def alpha_report(path: Path) -> dict:
    _, _, rows = read_rgba(path)
    opaque = transparent = feathered = 0
    for row in rows:
        for offset in range(3, len(row), 4):
            alpha = row[offset]
            if alpha == 0:
                transparent += 1
            elif alpha == 255:
                opaque += 1
            else:
                feathered += 1
    return {"opaque": opaque, "transparent": transparent, "feathered": feathered}


def _chunk(kind: bytes, payload: bytes) -> bytes:
    body = kind + payload
    return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body))


def _add_alpha(rows: Rows) -> Rows:
    expanded: Rows = []
    for row in rows:
        line = bytearray(len(row) // 3 * 4)
        for index in range(len(row) // 3):
            line[index * 4:index * 4 + 3] = row[index * 3:index * 3 + 3]
            line[index * 4 + 3] = 255
        expanded.append(line)
    return expanded


def _unfilter(raw: bytes, width: int, height: int, channels: int = 4) -> Rows:
    stride, cursor = width * channels, 0
    rows: Rows = []
    previous = bytearray(stride)
    for _ in range(height):
        filter_type = raw[cursor]
        cursor += 1
        line = bytearray(raw[cursor:cursor + stride])
        cursor += stride
        if filter_type:
            for index in range(stride):
                left = line[index - channels] if index >= channels else 0
                up = previous[index]
                up_left = previous[index - channels] if index >= channels else 0
                if filter_type == 1:
                    line[index] = (line[index] + left) & 255
                elif filter_type == 2:
                    line[index] = (line[index] + up) & 255
                elif filter_type == 3:
                    line[index] = (line[index] + (left + up) // 2) & 255
                elif filter_type == 4:
                    pa, pb, pc = abs(up - up_left), abs(left - up_left), abs(left + up - 2 * up_left)
                    predictor = left if (pa <= pb and pa <= pc) else (up if pb <= pc else up_left)
                    line[index] = (line[index] + predictor) & 255
                else:
                    raise PngError(f"unsupported PNG filter {filter_type}")
        rows.append(line)
        previous = line
    return rows
