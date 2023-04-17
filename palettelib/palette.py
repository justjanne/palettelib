from typing import NamedTuple, Optional

from palettelib.color import ColorRGB, ColorCMYK, ColorLAB, ColorGrayscale


class ColorSwatch(NamedTuple):
    name: Optional[str] = None
    spot: bool = False
    rgb: Optional[ColorRGB] = None
    cmyk: Optional[ColorCMYK] = None
    lab: Optional[ColorLAB] = None
    gray: Optional[ColorGrayscale] = None


class ColorGroup(NamedTuple):
    name: Optional[str]
    swatches: list[ColorSwatch]


class Palette(NamedTuple):
    name: Optional[str] = None
    groups: list[ColorGroup] = []
    swatches: list[ColorSwatch] = []
