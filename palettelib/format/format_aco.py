import struct
from typing import Optional, BinaryIO

from palettelib.color import ColorCMYK, ColorRGB, ColorLAB, ColorGrayscale
from palettelib.io import PaletteFormat
from palettelib.palette import Palette, ColorSwatch


def parse_swatch(stream: BinaryIO, version: int) -> ColorSwatch:
    swatch_type, = struct.unpack('!H', stream.read(2))

    rgb: Optional[ColorRGB] = None
    cmyk: Optional[ColorCMYK] = None
    lab: Optional[ColorLAB] = None
    gray: Optional[ColorGrayscale] = None
    if swatch_type == 0:
        r, g, b = struct.unpack_from('!3H', stream.read(8))
        rgb = ColorRGB(r / 65535.0, g / 65535.0, b / 65535.0)
    elif swatch_type == 2:
        c, m, y, k = struct.unpack_from('!4H', stream.read(8))
        cmyk = ColorCMYK(c / 65535.0, m / 65535.0, y / 65535.0, k / 65535.0)
    elif swatch_type == 7:
        l, a, b = struct.unpack_from('!Hhh', stream.read(8))
        lab = ColorLAB(l / 100.0, a / 100.0, b / 100.0)
    elif swatch_type == 8:
        k, = struct.unpack_from('!H', stream.read(8))
        gray = ColorGrayscale(k / 10000.0)
    else:
        raise Exception("unsupported color format: {0}".format(swatch_type))

    name: Optional[str] = None
    if version == 2:
        length, = struct.unpack_from('!i', stream.read(4))
        enc_name = stream.read(length * 2)
        enc_name = enc_name[:-2]
        name = enc_name.decode('UTF-16BE')

    return ColorSwatch(name, False, rgb, cmyk, lab, gray)


def parse_table(stream: BinaryIO) -> Optional[list[ColorSwatch]]:
    header = stream.read(4)
    if header is None or len(header) == 0:
        return None
    version, length = struct.unpack_from('!2H', header)
    return [parse_swatch(stream, version) for _ in range(length)]


def read_tables(stream: BinaryIO) -> list[ColorSwatch]:
    swatches = []
    while True:
        table = parse_table(stream)
        if table is None:
            break
        swatches = table
    return swatches


def read_aco(filepath: str) -> Palette:
    with open(filepath, 'rb') as stream:
        return Palette(swatches=read_tables(stream))


def write_color_rgb(stream: BinaryIO, color: ColorRGB):
    stream.write(struct.pack('!H', 0))
    buffer = bytearray(8)
    struct.pack_into('!3H', buffer, 0, int(color.r * 65535),
                     int(color.g * 65535), int(color.b * 65535))
    stream.write(buffer)


def write_color_cmyk(stream: BinaryIO, color: ColorCMYK):
    stream.write(struct.pack('!H', 2))
    buffer = bytearray(8)
    struct.pack_into('!4H', buffer, 0, int(color.c * 65535),
                     int(color.m * 65535), int(color.y * 65535), int(color.k * 65535))
    stream.write(buffer)


def write_color_lab(stream: BinaryIO, color: ColorLAB):
    stream.write(struct.pack('!H', 7))
    buffer = bytearray(8)
    struct.pack_into('!Hhh', buffer, 0, int(color.l * 100),
                     int(color.a * 100), int(color.b * 100))
    stream.write(buffer)


def write_color_gray(stream: BinaryIO, color: ColorGrayscale):
    stream.write(struct.pack('!H', 8))
    buffer = bytearray(8)
    struct.pack_into('!H', buffer, 0,
                     int(color.k * 10000))
    stream.write(buffer)


def write_name(stream: BinaryIO, name: str, version: int):
    if version == 2:
        if name == "" or name is None:
            stream.write(struct.pack('!i', 0))
        else:
            stream.write(struct.pack('!i', len(name) + 1))
            stream.write(name.encode('UTF-16BE'))
            stream.write(struct.pack('!H', 0))


def write_swatch(stream: BinaryIO, swatch: ColorSwatch, version: int):
    if swatch.rgb is not None:
        write_color_rgb(stream, swatch.rgb)
        write_name(stream, swatch.name, version)
    if swatch.cmyk is not None:
        write_color_cmyk(stream, swatch.cmyk)
        write_name(stream, swatch.name, version)
    if swatch.lab is not None:
        write_color_lab(stream, swatch.lab)
        write_name(stream, swatch.name, version)
    if swatch.gray is not None:
        write_color_gray(stream, swatch.gray)
        write_name(stream, swatch.name, version)


def count_colors(swatches: list[ColorSwatch]) -> int:
    count = 0
    for swatch in swatches:
        if swatch.rgb is not None:
            count += 1
        if swatch.cmyk is not None:
            count += 1
        if swatch.lab is not None:
            count += 1
        if swatch.gray is not None:
            count += 1
    return count


def write_table(stream: BinaryIO, swatches: list[ColorSwatch], version: int):
    stream.write(struct.pack('!2H', version, count_colors(swatches)))
    for swatch in swatches:
        write_swatch(stream, swatch, version)


def write_aco(filepath: str, palette: Palette):
    swatches = []
    for swatch in palette.swatches:
        swatches.append(swatch)
    for group in palette.groups:
        for swatch in group.swatches:
            swatches.append(swatch)
    with open(filepath, 'wb') as stream:
        write_table(stream, swatches, 1)
        write_table(stream, swatches, 2)
        stream.truncate()


PaletteFormatACO: PaletteFormat = ('.aco', read_aco, write_aco)
