from typing import Optional

import yaml

from palettelib.color import ColorCMYK, ColorRGB, ColorLAB, ColorGrayscale
from palettelib.io import PaletteFormat, tonemap, RangePaletteNative
from palettelib.palette import Palette, ColorGroup, ColorSwatch

RangeYamlRgb = (0, 255)
RangeYamlCmyk = (0, 100)
RangeYamlLabL = (0, 100)
RangeYamlLabAB = (-100, 100)
RangeYamlGray = (0, 100)


def swatch_to_dict(data: ColorSwatch) -> dict:
    serialized: dict = {}
    if data.name is not None:
        serialized['name'] = data.name
    if data.spot:
        serialized['spot'] = True
    if data.rgb is not None:
        serialized['rgb'] = [
            int(tonemap(data.rgb.r, RangePaletteNative, RangeYamlRgb)),
            int(tonemap(data.rgb.g, RangePaletteNative, RangeYamlRgb)),
            int(tonemap(data.rgb.b, RangePaletteNative, RangeYamlRgb)),
        ]
    if data.cmyk is not None:
        serialized['cmyk'] = [
            int(tonemap(data.cmyk.c, RangePaletteNative, RangeYamlCmyk)),
            int(tonemap(data.cmyk.m, RangePaletteNative, RangeYamlCmyk)),
            int(tonemap(data.cmyk.y, RangePaletteNative, RangeYamlCmyk)),
            int(tonemap(data.cmyk.k, RangePaletteNative, RangeYamlCmyk)),
        ]
    if data.lab is not None:
        serialized['lab'] = [
            tonemap(data.lab.l, RangePaletteNative, RangeYamlLabL),
            tonemap(data.lab.a, RangePaletteNative, RangeYamlLabAB),
            tonemap(data.lab.b, RangePaletteNative, RangeYamlLabAB),
        ]
    if data.gray is not None:
        serialized['gray'] = [
            int(tonemap(data.gray.k, RangePaletteNative, RangeYamlGray)),
        ]
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
        rgb = ColorRGB(
            tonemap(r, RangeYamlRgb, RangePaletteNative),
            tonemap(g, RangeYamlRgb, RangePaletteNative),
            tonemap(b, RangeYamlRgb, RangePaletteNative),
        )
    else:
        rgb = None
    cmyk = data.get('cmyk', [])
    if len(cmyk) == 4:
        c, m, y, k = cmyk
        cmyk = ColorCMYK(
            tonemap(c, RangeYamlCmyk, RangePaletteNative),
            tonemap(m, RangeYamlCmyk, RangePaletteNative),
            tonemap(y, RangeYamlCmyk, RangePaletteNative),
            tonemap(k, RangeYamlCmyk, RangePaletteNative),
        )
    else:
        cmyk = None
    lab = data.get('lab', [])
    if len(lab) == 3:
        l, a, b = lab
        lab = ColorLAB(
            tonemap(l, RangeYamlLabL, RangePaletteNative),
            tonemap(a, RangeYamlLabAB, RangePaletteNative),
            tonemap(b, RangeYamlLabAB, RangePaletteNative),
        )
    else:
        lab = None
    gray = data.get('gray', [])
    if len(gray) == 1:
        k, = gray
        gray = ColorGrayscale(
            tonemap(k, RangeYamlGray, RangePaletteNative),
        )
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
