from typing import Optional

import swatch

from palettelib.color import ColorRGB, ColorCMYK, ColorLAB, ColorGrayscale
from palettelib.io import PaletteFormat
from palettelib.palette import Palette, ColorGroup, ColorSwatch


def dict_to_swatch(name: str, data: dict[str, list[int]]) -> ColorSwatch:
    spot = data.get('type', None)
    spot = spot == 'Spot'
    rgb = None
    if 'RGB' in data:
        r, g, b = data.get('RGB')
        rgb = ColorRGB(r, g, b)
    cmyk = None
    if 'CMYK' in data:
        c, m, y, k = data.get('CMYK')
        cmyk = ColorCMYK(c, m, y, k)
    lab = None
    if 'LAB' in data:
        l, a, b = data.get('LAB')
        lab = ColorLAB(l, a, b)
    gray = None
    if 'Gray' in data:
        k, = data.get('Gray')
        gray = ColorGrayscale(k)
    return ColorSwatch(name, spot, rgb, cmyk, lab, gray)


def dict_list_to_swatch_list(data: list[dict]) -> list[ColorSwatch]:
    named_swatches: dict[str, dict[str, list[int]]] = {}
    for swatch in data:
        name = swatch.get('name', "")
        entry: Optional[dict] = swatch.get('data', None)
        if entry is None:
            continue
        mode = entry.get('mode', None)
        if mode is None:
            continue
        if name not in named_swatches:
            named_swatches[name] = {}
        named_swatches[name][mode] = entry.get('values', [])
        named_swatches[name]['type'] = entry.get('type', None)
    return [dict_to_swatch(name, named_swatches[name]) for name in named_swatches]


def dict_to_group(data: dict) -> ColorGroup:
    name = data.get('name', "")
    swatches: list[dict] = data.get('swatches', [])
    return ColorGroup(name, dict_list_to_swatch_list(swatches))


def dict_to_palette(data: list[dict]) -> Palette:
    ungrouped_colors = [entry for entry in data if entry.get('type') in ['Process', 'Spot', 'Global']]
    groups = [dict_to_group(entry) for entry in data if entry.get('type') == 'Color Group']
    return Palette(name=None, groups=groups, swatches=dict_list_to_swatch_list(ungrouped_colors))


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
    print(data)
    swatch.write(data, filepath)


PaletteFormatASE: PaletteFormat = ('.ase', read_ase, write_ase)
