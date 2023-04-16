from typing import Callable

from palette.palette import Palette

PaletteReader = Callable[[str], Palette]
PaletteWriter = Callable[[str, Palette], None]
PaletteFormat = tuple[str, PaletteReader, PaletteWriter]
