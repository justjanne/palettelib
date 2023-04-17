import os
from typing import Optional

from palettelib.format.format_aco import PaletteFormatACO
from palettelib.format.format_act import PaletteFormatACT
from palettelib.format.format_ase import PaletteFormatASE
from palettelib.format.format_gpl import PaletteFormatGPL
from palettelib.format.format_kpl import PaletteFormatKPL
from palettelib.format.format_yaml import PaletteFormatYAML
from palettelib.io import PaletteFormat, PaletteReader, PaletteWriter
from palettelib.palette import Palette

formats: list[PaletteFormat] = [
    PaletteFormatYAML, PaletteFormatGPL, PaletteFormatASE,
    PaletteFormatKPL, PaletteFormatACT, PaletteFormatACO
]
readers: dict[str, PaletteReader] = dict([(format, reader) for format, reader, writer in formats])
writers: dict[str, PaletteWriter] = dict([(format, writer) for format, reader, writer in formats if writer is not None])


def read_file(filepath: str) -> Palette:
    reader: Optional[PaletteReader] = None
    for format in readers:
        if filepath.endswith(format):
            reader = readers.get(format)
    if reader is None:
        raise Exception("unrecognized format: {0}".format(filepath))
    return reader(filepath)


def write_file(filepath: str, data: Palette):
    writer: Optional[PaletteWriter] = None
    for format in writers:
        if filepath.endswith(format):
            writer = writers.get(format)
    if writer is None:
        raise Exception("unrecognized format: {0}".format(filepath))
    return writer(filepath, data)


def main():
    os.makedirs('../build/test/resources', exist_ok=True)
    testfiles = [os.path.join('resources', filepath) for filepath in os.listdir('resources')]
    for filepath in testfiles:
        suffix = ""
        for format in readers:
            if filepath.endswith(format):
                suffix = format
        data = read_file(filepath)
        if data is None:
            raise Exception("could not load palette : {0}".format(filepath))
        name = os.path.basename(filepath)[:-len(suffix)]
        for format in writers:
            write_file("../build/test/resources/{0}{1}".format(name, format), data)


if __name__ == "__main__":
    main()
