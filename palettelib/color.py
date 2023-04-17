import math
from typing import NamedTuple


class ColorGrayscale(NamedTuple):
    k: float

    def __eq__(self, other):
        if not isinstance(other, ColorGrayscale):
            return False
        return math.isclose(self.k, other.k)


class ColorRGB(NamedTuple):
    r: float
    g: float
    b: float

    def __eq__(self, other):
        if not isinstance(other, ColorRGB):
            return False
        return math.isclose(self.r, other.r) \
            and math.isclose(self.g, other.g) \
            and math.isclose(self.b, other.b)


class ColorLAB(NamedTuple):
    l: float
    a: float
    b: float

    def __eq__(self, other):
        if not isinstance(other, ColorLAB):
            return False
        return math.isclose(self.l, other.l) \
            and math.isclose(self.a, other.a) \
            and math.isclose(self.b, other.b)


class ColorCMYK(NamedTuple):
    c: float
    m: float
    y: float
    k: float

    def __eq__(self, other):
        if not isinstance(other, ColorCMYK):
            return False
        return math.isclose(self.c, other.c) \
            and math.isclose(self.m, other.m) \
            and math.isclose(self.y, other.y) \
            and math.isclose(self.k, other.k)
