from typing import NamedTuple, Optional

from palette.color import ColorRGB, ColorCMYK, ColorLAB, ColorGrayscale


class ColorSwatch(NamedTuple):
    name: str
    spot: bool
    rgb: Optional[ColorRGB] = None
    cmyk: Optional[ColorCMYK] = None
    lab: Optional[ColorLAB] = None
    gray: Optional[ColorGrayscale] = None


class ColorGroup(NamedTuple):
    name: Optional[str]
    swatches: list[ColorSwatch]


class Palette(NamedTuple):
    name: Optional[str]
    groups: list[ColorGroup]
    swatches: list[ColorSwatch]
