from typing import Optional

import yaml

from palettelib.color import ColorCMYK, ColorRGB, ColorLAB, ColorGrayscale
from palettelib.io import PaletteFormat
from palettelib.palette import Palette, ColorGroup, ColorSwatch


def swatch_to_dict(data: ColorSwatch) -> dict:
    serialized: dict = {}
    if data.name is not None:
        serialized['name'] = data.name
    if data.spot:
        serialized['spot'] = True
    if data.rgb is not None:
        serialized['rgb'] = [int(value * 255) for value in
                             [data.rgb.r, data.rgb.g, data.rgb.b]]
    if data.cmyk is not None:
        serialized['cmyk'] = [int(value * 100) for value in
                              [data.cmyk.c, data.cmyk.m, data.cmyk.y, data.cmyk.k]]
    if data.lab is not None:
        serialized['lab'] = [data.lab.l, data.lab.a, data.lab.b]
    if data.gray is not None:
        serialized['gray'] = [int(data.gray.k * 100.0)]
    return serialized


def group_to_dict(data: ColorGroup) -> Optional[dict]:
    return {
        'name': data.name,
        'swatches': [swatch_to_dict(swatch) for swatch in data.swatches],
    }


def palette_to_dict(data: Palette) -> dict:
    serialized = {}
    if data.name is not None:
        serialized['name'] = data.name
    if data.groups is not None and len(data.groups) > 0:
        serialized['groups'] = [group_to_dict(group) for group in data.groups]
    if data.swatches is not None and len(data.swatches) > 0:
        serialized['swatches'] = [swatch_to_dict(swatch) for swatch in data.swatches]
    return serialized


def dict_to_swatch(data: dict) -> ColorSwatch:
    name = data.get('name', "")
    spot = data.get('spot', False)
    rgb = data.get('rgb', [])
    if len(rgb) == 3:
        r, g, b = rgb
        rgb = ColorRGB(r / 255.0, g / 255.0, b / 255.0)
    else:
        rgb = None
    cmyk = data.get('cmyk', [])
    if len(cmyk) == 4:
        c, m, y, k = cmyk
        cmyk = ColorCMYK(c / 100.0, m / 100.0, y / 100.0, k / 100.0)
    else:
        cmyk = None
    lab = data.get('lab', [])
    if len(lab) == 3:
        l, a, b = lab
        lab = ColorLAB(l, a, b)
    else:
        lab = None
    gray = data.get('gray', [])
    if len(gray) == 1:
        k, = gray
        gray = ColorGrayscale(k)
    else:
        gray = None
    return ColorSwatch(name, spot, rgb, cmyk, lab, gray)


def dict_to_group(data: dict) -> ColorGroup:
    name = data.get('name', "")
    swatches = data.get('swatches', [])
    return ColorGroup(name, [dict_to_swatch(swatch) for swatch in swatches])


def dict_to_palette(data: dict) -> Palette:
    name = data.get('name', "")
    groups = data.get("groups", [])
    swatches = data.get("swatches", [])
    return Palette(name, [dict_to_group(group) for group in groups],
                   [dict_to_swatch(swatch) for swatch in swatches])


def read_yaml(filepath: str) -> Palette:
    with open(filepath, 'r') as stream:
        data = yaml.safe_load(stream)
        return dict_to_palette(data)


def write_yaml(filepath: str, palette: Palette):
    with open(filepath, 'wt') as stream:
        serialized = palette_to_dict(palette)
        yaml.safe_dump(serialized, stream, default_flow_style=None)


PaletteFormatYAML: PaletteFormat = ('.palette.yaml', read_yaml, write_yaml)
