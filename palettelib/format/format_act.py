import os.path
import struct
from io import FileIO

from palettelib.color import ColorRGB
from palettelib.io import PaletteFormat
from palettelib.palette import Palette, ColorSwatch


def read_act(filepath: str) -> Palette:
    name = os.path.basename(filepath)[:-len('.act')]
    swatches: list[ColorSwatch] = []
    with open(filepath, 'rb') as stream:
        buffer = stream.read()
        for r, g, b in struct.iter_unpack('3B', buffer):
            color = ColorRGB(r / 255.0, g / 255.0, b / 255.0)
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
            stream.write(struct.pack('3B', int(255 * color.r), int(255 * color.g), int(255 * color.b)))
        stream.write(b'\x00\x00\x00' * (256 - len(colors)))
        stream.write(struct.pack('>H', len(colors)))
        stream.write(b'\xFF\xFF')


PaletteFormatACT: PaletteFormat = ('.act', read_act, write_act)
