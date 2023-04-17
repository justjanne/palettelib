from typing import Callable

from palettelib.palette import Palette

PaletteReader = Callable[[str], Palette]
PaletteWriter = Callable[[str, Palette], None]
PaletteFormat = tuple[str, PaletteReader, PaletteWriter]
