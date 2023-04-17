from typing import Optional

import swatch

from palettelib.color import ColorRGB, ColorCMYK, ColorLAB, ColorGrayscale
from palettelib.io import PaletteFormat
from palettelib.palette import Palette, ColorGroup, ColorSwatch


def dict_to_swatch(entry: dict) -> ColorSwatch:
    name = entry.get('name', None)

    spot = entry.get('type', None)
    spot = spot == 'Spot'

    data = entry.get('data', {})
    values = data.get('values', [])
    mode = data.get('mode')

    rgb = None
    if mode == 'RGB':
        r, g, b = values
        rgb = ColorRGB(r, g, b)
    cmyk = None
    if mode == 'CMYK':
        c, m, y, k = values
        cmyk = ColorCMYK(c, m, y, k)
    lab = None
    if mode == 'LAB':
        l, a, b = values
        lab = ColorLAB(l, a, b)
    gray = None
    if mode == 'Gray':
        k, = values
        gray = ColorGrayscale(k)
    return ColorSwatch(name, spot, rgb, cmyk, lab, gray)


def dict_to_group(data: dict) -> ColorGroup:
    name = data.get('name', "")
    entries: list[dict] = data.get('swatches', [])
    swatches = [dict_to_swatch(entry) for entry in entries]
    return ColorGroup(name, swatches)


def dict_to_palette(data: list[dict]) -> Palette:
    ungrouped_colors = [entry for entry in data if entry.get('type') in ['Process', 'Spot', 'Global']]
    groups = [dict_to_group(entry) for entry in data if entry.get('type') == 'Color Group']
    ungrouped_swatches = [dict_to_swatch(entry) for entry in ungrouped_colors]
    return Palette(name=None, groups=groups, swatches=ungrouped_swatches)


def swatch_to_dict(swatch: ColorSwatch) -> list[dict]:
    type = 'Spot' if swatch.spot else 'Process'
    name = swatch.name
    if name is None:
        name = "unnamed"
    result = []
    if swatch.rgb is not None:
        result.append({
            'name': name,
            'type': type,
            'data': {
                'mode': 'RGB',
                'values': [swatch.rgb.r, swatch.rgb.g, swatch.rgb.b]
            }
        })
    if swatch.cmyk is not None:
        result.append({
            'name': name,
            'type': type,
            'data': {
                'mode': 'CMYK',
                'values': [swatch.cmyk.c, swatch.cmyk.m, swatch.cmyk.y, swatch.cmyk.k]
            }
        })
    if swatch.lab is not None:
        result.append({
            'name': name,
            'type': type,
            'data': {
                'mode': 'LAB',
                'values': [swatch.lab.l, swatch.lab.a, swatch.lab.b]
            }
        })
    if swatch.gray is not None:
        result.append({
            'name': name,
            'type': type,
            'data': {
                'mode': 'Gray',
                'values': [swatch.gray.k]
            }
        })
    return result


def group_to_dict(group: ColorGroup) -> dict:
    name = group.name
    if name is None:
        name = "unnamed"
    return {
        'name': name,
        'type': 'Color Group',
        'swatches': [entry for swatch in group.swatches for entry in swatch_to_dict(swatch)]
    }


def palette_to_dict(data: Palette) -> list[dict]:
    result = []
    for group in data.groups:
        result.append(group_to_dict(group))
    for swatch in data.swatches:
        for entry in swatch_to_dict(swatch):
            result.append(entry)
    return result


def read_ase(filepath: str) -> Palette:
    return dict_to_palette(swatch.parse(filepath))


def write_ase(filepath: str, palette: Palette):
    data = palette_to_dict(palette)
    swatch.write(data, filepath)


PaletteFormatASE: PaletteFormat = ('.ase', read_ase, write_ase)
