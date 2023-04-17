from typing import TextIO

from palettelib.color import ColorRGB
from palettelib.io import PaletteFormat, RangePaletteNative, tonemap
from palettelib.palette import Palette, ColorSwatch

RangeGplNative = (0, 255)


def read_gpl(filepath: str) -> Palette:
    with open(filepath, 'r') as stream:
        header = False
        attributes: dict[str, str] = {}
        swatches: list[ColorSwatch] = []
        for line in stream:
            line = line.strip()
            # Handle comments
            if '#' in line:
                line = line[0:line.index('#')]
            if not header:
                if line == "GIMP Palette":
                    header = True
                    continue
                else:
                    raise Exception("File is not a valid GIMP Palette")
            if not len(line):
                continue
            if line[0].isdigit():
                entries = line.split(maxsplit=3)
                name = None
                if len(entries) == 4:
                    r, g, b, name = entries
                elif len(entries) == 3:
                    r, g, b = entries
                else:
                    raise Exception("Entry is not a valid GIMP Palette entry: '" + line + "'")
                color_rgb = ColorRGB(
                    tonemap(int(r), RangeGplNative, RangePaletteNative),
                    tonemap(int(g), RangeGplNative, RangePaletteNative),
                    tonemap(int(b), RangeGplNative, RangePaletteNative),
                )
                swatch = ColorSwatch(name, False, rgb=color_rgb)
                swatches.append(swatch)
            else:
                key, value = line.split(': ')
                attributes[key.lower()] = value
        return Palette(name=attributes.get('name', None), groups=[], swatches=swatches)


def write_swatch(stream: TextIO, swatch: ColorSwatch):
    if swatch.rgb is not None:
        if swatch.name is None:
            stream.write("{0:>3} {1:>3} {2:>3}\n".format(
                int(tonemap(swatch.rgb.r, RangePaletteNative, RangeGplNative)),
                int(tonemap(swatch.rgb.g, RangePaletteNative, RangeGplNative)),
                int(tonemap(swatch.rgb.b, RangePaletteNative, RangeGplNative)),
            ))
        else:
            stream.write("{0:>3} {1:>3} {2:>3} {3}\n".format(
                int(tonemap(swatch.rgb.r, RangePaletteNative, RangeGplNative)),
                int(tonemap(swatch.rgb.g, RangePaletteNative, RangeGplNative)),
                int(tonemap(swatch.rgb.b, RangePaletteNative, RangeGplNative)),
                swatch.name
            ))


def write_gpl(filepath: str, palette: Palette):
    with open(filepath, 'wt') as stream:
        stream.write("GIMP Palette\n")
        if palette.name is not None:
            stream.write('Name: {0}\n'.format(palette.name))
        for swatch in palette.swatches:
            write_swatch(stream, swatch)
        for group in palette.groups:
            for swatch in group.swatches:
                write_swatch(stream, swatch)
        stream.truncate()


PaletteFormatGPL: PaletteFormat = ('.gpl', read_gpl, write_gpl)
