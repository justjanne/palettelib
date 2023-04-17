from typing import Callable

from palettelib.palette import Palette

PaletteReader = Callable[[str], Palette]
PaletteWriter = Callable[[str, Palette], None]
PaletteFormat = tuple[str, PaletteReader, PaletteWriter]

RangePaletteNative = (0, 1)


def tonemap(value: float, old: (float, float), new: (float, float)) -> float:
    old_offset = old[1]
    old_range = old[1] - old[0]
    new_offset = new[1]
    new_range = new[1] - new[0]
    factor = new_range / old_range
    return (value - old_offset) * factor + new_offset
