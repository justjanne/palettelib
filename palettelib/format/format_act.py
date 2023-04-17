import os.path
import struct
from io import FileIO

from palettelib.color import ColorRGB
from palettelib.io import PaletteFormat, tonemap, RangePaletteNative
from palettelib.palette import Palette, ColorSwatch

RangeActNative = (0, 255)


def read_act(filepath: str) -> Palette:
    name = os.path.basename(filepath)[:-len('.act')]
    swatches: list[ColorSwatch] = []
    with open(filepath, 'rb') as stream:
        buffer = stream.read()
        length = 256
        transparent = None
        if len(buffer) > 768:
            length, transparent = struct.unpack('!2H', buffer[768:])
            buffer = buffer[:768]
        for idx in range(length):
            if idx != transparent:
                r, g, b = struct.unpack_from('3B', buffer, idx * 3)
                color = ColorRGB(
                    tonemap(r, RangeActNative, RangePaletteNative),
                    tonemap(g, RangeActNative, RangePaletteNative),
                    tonemap(b, RangeActNative, RangePaletteNative)
                )
                swatch = ColorSwatch(rgb=color)
                swatches.append(swatch)
    return Palette(name=name, swatches=swatches, groups=[])


def write_act(filepath: str, data: Palette):
    stream: FileIO
    with open(filepath, 'wb') as stream:
        colors = []
        for swatch in data.swatches:
            if swatch.rgb is not None:
                colors.append(swatch.rgb)
        for group in data.groups:
            for swatch in group.swatches:
                if swatch.rgb is not None:
                    colors.append(swatch.rgb)
        for i in range(0, min(256, len(colors))):
            color = colors[i]
            stream.write(struct.pack(
                '3B',
                int(tonemap(color.r, RangePaletteNative, RangeActNative)),
                int(tonemap(color.g, RangePaletteNative, RangeActNative)),
                int(tonemap(color.b, RangePaletteNative, RangeActNative))))
        stream.write(b'\x00\x00\x00' * (256 - len(colors)))
        stream.write(struct.pack('>H', len(colors)))
        stream.write(b'\xFF\xFF')
        stream.truncate()


PaletteFormatACT: PaletteFormat = ('.act', read_act, write_act)
