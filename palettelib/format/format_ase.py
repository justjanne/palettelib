import swatch as ase

from palettelib.color import ColorRGB, ColorCMYK, ColorLAB, ColorGrayscale
from palettelib.io import PaletteFormat, tonemap, RangePaletteNative
from palettelib.palette import Palette, ColorGroup, ColorSwatch

RangeAseNative = (0, 1)
RangeAseLabAB = (-128, 127)


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
        rgb = ColorRGB(
            tonemap(r, RangeAseNative, RangePaletteNative),
            tonemap(g, RangeAseNative, RangePaletteNative),
            tonemap(b, RangeAseNative, RangePaletteNative),
        )
    cmyk = None
    if mode == 'CMYK':
        c, m, y, k = values
        cmyk = ColorCMYK(
            tonemap(c, RangeAseNative, RangePaletteNative),
            tonemap(m, RangeAseNative, RangePaletteNative),
            tonemap(y, RangeAseNative, RangePaletteNative),
            tonemap(k, RangeAseNative, RangePaletteNative),
        )
    lab = None
    if mode == 'LAB':
        l, a, b = values
        lab = ColorLAB(
            tonemap(l, RangeAseNative, RangePaletteNative),
            tonemap(a, RangeAseLabAB, RangePaletteNative),
            tonemap(b, RangeAseLabAB, RangePaletteNative),
        )
    gray = None
    if mode == 'Gray':
        k, = values
        gray = ColorGrayscale(
            tonemap(k, RangeAseNative, RangePaletteNative),
        )
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
    swatch_type = 'Spot' if swatch.spot else 'Process'
    name = swatch.name
    if name is None:
        name = "unnamed"
    result = []
    if swatch.rgb is not None:
        result.append({
            'name': name,
            'type': swatch_type,
            'data': {
                'mode': 'RGB',
                'values': [
                    tonemap(swatch.rgb.r, RangePaletteNative, RangeAseNative),
                    tonemap(swatch.rgb.g, RangePaletteNative, RangeAseNative),
                    tonemap(swatch.rgb.b, RangePaletteNative, RangeAseNative),
                ]
            }
        })
    if swatch.cmyk is not None:
        result.append({
            'name': name,
            'type': swatch_type,
            'data': {
                'mode': 'CMYK',
                'values': [
                    tonemap(swatch.cmyk.c, RangePaletteNative, RangeAseNative),
                    tonemap(swatch.cmyk.m, RangePaletteNative, RangeAseNative),
                    tonemap(swatch.cmyk.y, RangePaletteNative, RangeAseNative),
                    tonemap(swatch.cmyk.k, RangePaletteNative, RangeAseNative),
                ]
            }
        })
    if swatch.lab is not None:
        result.append({
            'name': name,
            'type': swatch_type,
            'data': {
                'mode': 'LAB',
                'values': [
                    tonemap(swatch.lab.l, RangePaletteNative, RangeAseNative),
                    tonemap(swatch.lab.a, RangePaletteNative, RangeAseLabAB),
                    tonemap(swatch.lab.b, RangePaletteNative, RangeAseLabAB),
                ]
            }
        })
    if swatch.gray is not None:
        result.append({
            'name': name,
            'type': swatch_type,
            'data': {
                'mode': 'Gray',
                'values': [
                    tonemap(swatch.gray.k, RangePaletteNative, RangeAseNative),
                ]
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
    return dict_to_palette(ase.parse(filepath))


def write_ase(filepath: str, palette: Palette):
    data = palette_to_dict(palette)
    ase.write(data, filepath)


PaletteFormatASE: PaletteFormat = ('.ase', read_ase, write_ase)
