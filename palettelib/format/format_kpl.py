from typing import Optional
from xml.dom import minidom
from zipfile import ZipFile

from palettelib.color import ColorRGB, ColorCMYK, ColorLAB, ColorGrayscale
from palettelib.io import PaletteFormat, RangePaletteNative, tonemap
from palettelib.palette import Palette, ColorSwatch, ColorGroup

RangeKplNative = (0, 1)
RangeKpl2LabL = (0, 100)
RangeKpl2LabAB = (-128, 127)


def none_if_empty(value: str) -> Optional[str]:
    if value.strip() == "":
        return None
    return value


def xml_to_swatch(element: minidom.Element, version: str) -> ColorSwatch:
    name = none_if_empty(element.getAttribute('name'))
    spot = bool(none_if_empty(element.getAttribute('spot')))

    if version == "1.0":
        range_lab_l = RangeKplNative
        range_lab_ab = RangeKplNative
    else:
        range_lab_l = RangeKpl2LabL
        range_lab_ab = RangeKpl2LabAB

    elements: list[minidom.Element] = element.childNodes

    el_rgb: list[minidom.Element] = [element for element in elements if element.nodeName == 'sRGB']
    rgb: Optional[ColorRGB] = None
    if len(el_rgb) > 0:
        r = float(el_rgb[0].getAttribute('r'))
        g = float(el_rgb[0].getAttribute('g'))
        b = float(el_rgb[0].getAttribute('b'))
        rgb = ColorRGB(
            tonemap(r, RangeKplNative, RangePaletteNative),
            tonemap(g, RangeKplNative, RangePaletteNative),
            tonemap(b, RangeKplNative, RangePaletteNative),
        )

    el_cmyk: list[minidom.Element] = [element for element in elements if element.nodeName == 'CMYK']
    cmyk: Optional[ColorCMYK] = None
    if len(el_cmyk) > 0:
        c = float(el_cmyk[0].getAttribute('c'))
        m = float(el_cmyk[0].getAttribute('m'))
        y = float(el_cmyk[0].getAttribute('y'))
        k = float(el_cmyk[0].getAttribute('k'))
        cmyk = ColorCMYK(
            tonemap(c, RangeKplNative, RangePaletteNative),
            tonemap(m, RangeKplNative, RangePaletteNative),
            tonemap(y, RangeKplNative, RangePaletteNative),
            tonemap(k, RangeKplNative, RangePaletteNative),
        )

    el_lab: list[minidom.Element] = [element for element in elements if element.nodeName == 'Lab']
    lab: Optional[ColorLAB] = None
    if len(el_lab) > 0:
        l = float(el_lab[0].getAttribute('L'))
        a = float(el_lab[0].getAttribute('a'))
        b = float(el_lab[0].getAttribute('b'))
        lab = ColorLAB(
            tonemap(l, range_lab_l, RangePaletteNative),
            tonemap(a, range_lab_ab, RangePaletteNative),
            tonemap(b, range_lab_ab, RangePaletteNative),
        )

    el_gray: list[minidom.Element] = [element for element in elements if element.nodeName == 'Gray']
    gray: Optional[ColorGrayscale] = None
    if len(el_gray) > 0:
        k = float(el_gray[0].getAttribute('g'))
        gray = ColorGrayscale(
            tonemap(k, RangeKplNative, RangePaletteNative),
        )

    return ColorSwatch(name, spot, rgb, cmyk, lab, gray)


def xml_to_group(element: minidom.Element, version: str) -> ColorGroup:
    name = none_if_empty(element.getAttribute('name'))
    swatches = [xml_to_swatch(element, version)
                for element in element.childNodes
                if element.nodeName == 'ColorSetEntry']
    return ColorGroup(name, swatches)


def xml_to_palette(document: minidom.Document) -> Optional[Palette]:
    node: minidom.Element
    colorset: minidom.Element = document.documentElement
    if colorset.nodeName != "ColorSet":
        raise Exception("invalid KPL XML: {0}".format(document.toprettyxml()))
    name = none_if_empty(colorset.getAttribute('name'))
    version = none_if_empty(colorset.getAttribute('version'))
    swatches = [xml_to_swatch(element, version)
                for element in colorset.childNodes
                if element.nodeName == 'ColorSetEntry']
    groups = [xml_to_group(element, version)
              for element in colorset.childNodes
              if element.nodeName == 'Group']
    return Palette(name, groups, swatches)


def read_kpl(filepath: str) -> Palette:
    with ZipFile(filepath, 'r') as data:
        with data.open('colorset.xml', 'r') as colorset:
            document = minidom.parse(colorset)
            return xml_to_palette(document)


def palette_to_profiles_xml() -> str:
    document = minidom.Document()
    profiles = document.createElement('Profiles')
    document.appendChild(profiles)
    return document.toprettyxml(indent="    ")


def swatch_to_xml(document: minidom.Document, swatch: ColorSwatch, version: str) -> minidom.Element:
    el_swatch: minidom.Element = document.createElement('ColorSetEntry')
    el_swatch.setAttribute('name', swatch.name)
    el_swatch.setAttribute('spot', 'false')
    el_swatch.setAttribute('bitdepth', 'F32')

    if version == "1.0":
        range_lab_l = RangeKplNative
        range_lab_ab = RangeKplNative
    else:
        range_lab_l = RangeKpl2LabL
        range_lab_ab = RangeKpl2LabAB

    if swatch.rgb is not None:
        el_srgb: minidom.Element = document.createElement('sRGB')
        r = tonemap(swatch.rgb.r, RangePaletteNative, RangeKplNative)
        g = tonemap(swatch.rgb.g, RangePaletteNative, RangeKplNative)
        b = tonemap(swatch.rgb.b, RangePaletteNative, RangeKplNative)
        el_srgb.setAttribute('r', "{:.14f}".format(r))
        el_srgb.setAttribute('g', "{:.14f}".format(g))
        el_srgb.setAttribute('b', "{:.14f}".format(b))
        el_swatch.appendChild(el_srgb)
    if swatch.cmyk is not None:
        el_cmyk: minidom.Element = document.createElement('CMYK')
        c = tonemap(swatch.cmyk.c, RangePaletteNative, RangeKplNative)
        m = tonemap(swatch.cmyk.m, RangePaletteNative, RangeKplNative)
        y = tonemap(swatch.cmyk.y, RangePaletteNative, RangeKplNative)
        k = tonemap(swatch.cmyk.k, RangePaletteNative, RangeKplNative)
        el_cmyk.setAttribute('c', "{:.14f}".format(c))
        el_cmyk.setAttribute('m', "{:.14f}".format(m))
        el_cmyk.setAttribute('y', "{:.14f}".format(y))
        el_cmyk.setAttribute('k', "{:.14f}".format(k))
        el_swatch.appendChild(el_cmyk)
    if swatch.lab is not None:
        el_lab: minidom.Element = document.createElement('Lab')
        l = tonemap(swatch.lab.l, RangePaletteNative, range_lab_l)
        a = tonemap(swatch.lab.a, RangePaletteNative, range_lab_ab)
        b = tonemap(swatch.lab.b, RangePaletteNative, range_lab_ab)
        el_lab.setAttribute('L', "{:.14f}".format(l))
        el_lab.setAttribute('a', "{:.14f}".format(a))
        el_lab.setAttribute('b', "{:.14f}".format(b))
        el_lab.setAttribute("space", "Lab identity built-in")
        el_swatch.appendChild(el_lab)
    if swatch.gray is not None:
        el_gray: minidom.Element = document.createElement('Gray')
        k = tonemap(swatch.gray.k, RangePaletteNative, RangeKplNative)
        el_gray.setAttribute('g', "{:.14f}".format(k))
        el_swatch.appendChild(el_gray)
    return el_swatch


def palette_to_colorset_xml(palette: Palette, version: str) -> str:
    document: minidom.Document = minidom.Document()
    el_colorset: minidom.Element = document.createElement('ColorSet')
    el_colorset.setAttribute('version', version)
    el_colorset.setAttribute('name', palette.name)
    if len(palette.swatches) == 0:
        el_colorset.setAttribute("rows", "0")
        el_colorset.setAttribute("columns", "0")
    document.appendChild(el_colorset)
    for group in palette.groups:
        el_group: minidom.Element = document.createElement('Group')
        el_group.setAttribute('name', group.name)
        for swatch in group.swatches:
            el_group.appendChild(swatch_to_xml(document, swatch, version))
        el_colorset.appendChild(el_group)
    for swatch in palette.swatches:
        el_colorset.appendChild(swatch_to_xml(document, swatch, version))
    return document.toprettyxml(indent="    ")


def write_kpl(filepath: str, palette: Palette):
    version = "2.0"
    with ZipFile(filepath, 'w') as data:
        data.writestr('mimetype', 'krita/x-colorset')
        data.writestr('profiles.xml', palette_to_profiles_xml())
        data.writestr('colorset.xml', palette_to_colorset_xml(palette, version))


PaletteFormatKPL: PaletteFormat = ('.kpl', read_kpl, write_kpl)
