from typing import Optional
from xml.dom import minidom
from zipfile import ZipFile

from palettelib.color import ColorRGB, ColorCMYK, ColorLAB, ColorGrayscale
from palettelib.io import PaletteFormat
from palettelib.palette import Palette, ColorSwatch, ColorGroup


def noneIfEmpty(value: str) -> Optional[str]:
    if value.strip() == "":
        return None
    return value


def xml_to_swatch(element: minidom.Element) -> ColorSwatch:
    name = noneIfEmpty(element.getAttribute('name'))
    spot = bool(noneIfEmpty(element.getAttribute('spot')))

    elements: list[minidom.Element] = element.childNodes

    el_rgb: list[minidom.Element] = [element for element in elements if element.nodeName == 'sRGB']
    rgb: Optional[ColorRGB] = None
    if len(el_rgb) > 0:
        r = float(el_rgb[0].getAttribute('r'))
        g = float(el_rgb[0].getAttribute('g'))
        b = float(el_rgb[0].getAttribute('b'))
        rgb = ColorRGB(r, g, b)

    el_cmyk: list[minidom.Element] = [element for element in elements if element.nodeName == 'CMYK']
    cmyk: Optional[ColorCMYK] = None
    if len(el_cmyk) > 0:
        c = float(el_cmyk[0].getAttribute('c'))
        m = float(el_cmyk[0].getAttribute('m'))
        y = float(el_cmyk[0].getAttribute('y'))
        k = float(el_cmyk[0].getAttribute('k'))
        cmyk = ColorCMYK(c, m, y, k)

    el_lab: list[minidom.Element] = [element for element in elements if element.nodeName == 'Lab']
    lab: Optional[ColorLAB] = None
    if len(el_lab) > 0:
        l = float(el_lab[0].getAttribute('L'))
        a = float(el_lab[0].getAttribute('a'))
        b = float(el_lab[0].getAttribute('b'))
        lab = ColorLAB(l, a, b)

    el_gray: list[minidom.Element] = [element for element in elements if element.nodeName == 'Gray']
    gray: Optional[ColorGrayscale] = None
    if len(el_gray) > 0:
        k = float(el_gray[0].getAttribute('g'))
        gray = ColorGrayscale(k)

    return ColorSwatch(name, spot, rgb, cmyk, lab, gray)


def xml_to_group(element: minidom.Element) -> ColorGroup:
    name = noneIfEmpty(element.getAttribute('name'))
    swatches = [xml_to_swatch(element)
                for element in element.childNodes
                if element.nodeName == 'ColorSetEntry']
    return ColorGroup(name, swatches)


def xml_to_palette(document: minidom.Document) -> Optional[Palette]:
    node: minidom.Element
    colorset: minidom.Element = document.documentElement
    if colorset.nodeName != "ColorSet":
        raise Exception("invalid KPL XML: {0}".format(document.toprettyxml()))
    name = noneIfEmpty(colorset.getAttribute('name'))
    swatches = [xml_to_swatch(element)
                for element in colorset.childNodes
                if element.nodeName == 'ColorSetEntry']
    groups = [xml_to_group(element)
              for element in colorset.childNodes
              if element.nodeName == 'Group']
    return Palette(name, groups, swatches)


def read_kpl(filepath: str) -> Palette:
    with ZipFile(filepath, 'r') as data:
        with data.open('colorset.xml', 'r') as colorset:
            document = minidom.parse(colorset)
            return xml_to_palette(document)


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
    if swatch.gray is not None:
        el_gray: minidom.Element = document.createElement('Gray')
        el_gray.setAttribute('g', str(swatch.gray.k))
        el_swatch.appendChild(el_gray)
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
