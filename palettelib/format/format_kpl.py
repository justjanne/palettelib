from xml.dom import minidom
from zipfile import ZipFile

from palettelib.io import PaletteFormat
from palettelib.palette import Palette, ColorSwatch


def read_kpl(filepath: str) -> Palette:
    pass


def palette_to_profiles_xml(palette: Palette) -> str:
    document = minidom.Document()
    profiles = document.createElement('Profiles')
    document.appendChild(profiles)
    return document.toprettyxml(indent="    ")


def swatch_to_xml(document: minidom.Document, swatch: ColorSwatch) -> minidom.Element:
    el_swatch: minidom.Element = document.createElement('ColorSetEntry')
    el_swatch.setAttribute('name', swatch.name)
    el_swatch.setAttribute('spot', 'false')
    el_swatch.setAttribute('bitdepth', 'F32')
    if swatch.rgb is not None:
        el_srgb: minidom.Element = document.createElement('sRGB')
        el_srgb.setAttribute('r', str(swatch.rgb.r))
        el_srgb.setAttribute('g', str(swatch.rgb.g))
        el_srgb.setAttribute('b', str(swatch.rgb.b))
        el_swatch.appendChild(el_srgb)
    if swatch.cmyk is not None:
        el_cmyk: minidom.Element = document.createElement('CMYK')
        el_cmyk.setAttribute('c', str(swatch.cmyk.c))
        el_cmyk.setAttribute('m', str(swatch.cmyk.m))
        el_cmyk.setAttribute('y', str(swatch.cmyk.y))
        el_cmyk.setAttribute('k', str(swatch.cmyk.k))
        el_swatch.appendChild(el_cmyk)
    if swatch.lab is not None:
        el_lab: minidom.Element = document.createElement('Lab')
        el_lab.setAttribute('l', str(swatch.lab.l))
        el_lab.setAttribute('a', str(swatch.lab.a))
        el_lab.setAttribute('b', str(swatch.lab.b))
        el_swatch.appendChild(el_lab)
    return el_swatch


def palette_to_colorset_xml(palette: Palette) -> str:
    document: minidom.Document = minidom.Document()
    el_colorset: minidom.Element = document.createElement('ColorSet')
    el_colorset.setAttribute('readonly', 'true')
    el_colorset.setAttribute('version', '1.0')
    el_colorset.setAttribute('name', palette.name)
    document.appendChild(el_colorset)
    for group in palette.groups:
        el_group: minidom.Element = document.createElement('Group')
        el_group.setAttribute('name', group.name)
        for swatch in group.swatches:
            el_group.appendChild(swatch_to_xml(document, swatch))
        el_colorset.appendChild(el_group)
    for swatch in palette.swatches:
        el_colorset.appendChild(swatch_to_xml(document, swatch))
    return document.toprettyxml(indent="    ")


def write_kpl(filepath: str, palette: Palette):
    with ZipFile(filepath, 'w') as data:
        data.writestr('mimetype', 'krita/x-colorset')
        data.writestr('profiles.xml', palette_to_profiles_xml(palette))
        data.writestr('colorset.xml', palette_to_colorset_xml(palette))


PaletteFormatKPL: PaletteFormat = ('.kpl', read_kpl, write_kpl)
