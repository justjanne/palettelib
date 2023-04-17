from typing import NamedTuple


class ColorGrayscale(NamedTuple):
    k: float


class ColorRGB(NamedTuple):
    r: float
    g: float
    b: float


class ColorLAB(NamedTuple):
    l: float
    a: float
    b: float


class ColorCMYK(NamedTuple):
    c: float
    m: float
    y: float
    k: float
