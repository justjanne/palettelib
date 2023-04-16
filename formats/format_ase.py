from typing import Optional

import swatch

from palette.format import PaletteFormat
from palette.color import ColorRGB, ColorCMYK, ColorLAB, ColorGrayscale
from palette.palette import Palette, ColorGroup, ColorSwatch


def dict_to_swatch(name: str, data: dict[str, list[int]]) -> ColorSwatch:
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
    return ColorSwatch(name, rgb, cmyk, lab, gray)


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
    return [dict_to_swatch(name, named_swatches[name]) for name in named_swatches]


def dict_to_group(data: dict) -> ColorGroup:
    name = data.get('name', "")
    swatches: list[dict] = data.get('swatches', [])
    return ColorGroup(name, dict_list_to_swatch_list(swatches))


def dict_to_palette(data: list[dict]) -> Palette:
    ungrouped_colors = [entry for entry in data if entry.get('type') in ['Process', 'Spot', 'Global']]
    groups = [dict_to_group(entry) for entry in data if entry.get('type') == 'Color Group']
    if len(ungrouped_colors):
        groups.append(ColorGroup(name=None, swatches=dict_list_to_swatch_list(ungrouped_colors)))
    return Palette(name=None, groups=groups)


def read_ase(filepath: str) -> Palette:
    return dict_to_palette(swatch.parse(filepath))


def write_ase(filepath: str, palette: Palette):
    pass


PaletteFormatASE: PaletteFormat = ('.ase', read_ase, write_ase)
