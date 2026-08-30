from __future__ import annotations

import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skills" / "image-generation" / "scripts"))

import pngtools


def _crc_chunk(kind: bytes, payload: bytes) -> bytes:
    body = kind + payload
    return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body))


def _write_rgb_png(path: Path, width: int, height: int, *, pixels: list[tuple[int, int, int]]) -> None:
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        for x in range(width):
            raw += bytes(pixels[y * width + x])
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + _crc_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + _crc_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + _crc_chunk(b"IEND", b"")
    )


def _gradient_rows(width: int, height: int) -> pngtools.Rows:
    rows: pngtools.Rows = []
    for y in range(height):
        row = bytearray()
        for x in range(width):
            row += bytes([(x * 40) % 256, (y * 60) % 256, (x + y) % 256, (255 - x * 10) % 256])
        rows.append(row)
    return rows


class PngToolsTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.tmp_path = Path(self._tmpdir.name)

    def test_read_rgba_reads_8bit_rgba_png(self) -> None:
        width, height = 2, 1
        rows = [bytearray([10, 20, 30, 255, 40, 50, 60, 128])]
        path = self.tmp_path / "rgba.png"
        pngtools.write_rgba(path, width, height, rows)

        read_width, read_height, read_rows = pngtools.read_rgba(path)

        self.assertEqual((read_width, read_height), (width, height))
        self.assertEqual(read_rows, rows)

    def test_read_rgba_fills_alpha_for_rgb_png(self) -> None:
        width, height = 2, 1
        pixels = [(10, 20, 30), (40, 50, 60)]
        path = self.tmp_path / "rgb.png"
        _write_rgb_png(path, width, height, pixels=pixels)

        read_width, read_height, rows = pngtools.read_rgba(path)

        self.assertEqual((read_width, read_height), (width, height))
        self.assertEqual(rows, [bytearray([10, 20, 30, 255, 40, 50, 60, 255])])

    def test_write_then_read_round_trip_preserves_pixels(self) -> None:
        width, height = 3, 2
        rows = _gradient_rows(width, height)
        path = self.tmp_path / "roundtrip.png"

        pngtools.write_rgba(path, width, height, rows)
        _, _, read_rows = pngtools.read_rgba(path)

        self.assertEqual(read_rows, rows)

    def test_harden_alpha_snaps_partial_values_to_threshold(self) -> None:
        row = bytearray()
        for alpha in (50, 128, 200, 0, 255):
            row += bytes([1, 2, 3, alpha])
        path = self.tmp_path / "alpha.png"
        pngtools.write_rgba(path, 5, 1, [row])

        snapped = pngtools.harden_alpha(path, threshold=128)

        _, _, rows = pngtools.read_rgba(path)
        alphas = rows[0][3::4]
        self.assertEqual(list(alphas), [0, 255, 255, 0, 255])
        self.assertEqual(snapped, 3)

    def test_downscale_produces_target_dimensions(self) -> None:
        width, height, target = 4, 4, 2
        rows = _gradient_rows(width, height)
        source = self.tmp_path / "source.png"
        out = self.tmp_path / "out.png"
        pngtools.write_rgba(source, width, height, rows)

        pngtools.downscale(source, target, out)

        read_width, read_height, _ = pngtools.read_rgba(out)
        self.assertEqual(read_width, target)
        self.assertEqual(read_height, target)


if __name__ == "__main__":
    unittest.main()
