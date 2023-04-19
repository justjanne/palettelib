import contextlib
import datetime
import io
import os
import zlib
from os import PathLike
from typing import NamedTuple, Optional
from typing.io import BinaryIO

import zstandard

from palettelib.util import print_columns

CONTAINER_MAGIC = 0x414bff00
CONTAINER_TAG_FAT = "#FAT"
CONTAINER_TAG_FT2 = "#FT2"
CONTAINER_TAG_FT3 = "#FT3"
CONTAINER_TAG_FT4 = "#FT4"
CONTAINER_TAG_INF = "#Inf"
CONTAINER_TAG_PROT = "Prot"
CONTAINER_TAG_THMB = "Thmb"
CONTAINER_TAG_FIL = "#Fil"


class AffinityFileHeader(NamedTuple):
    version: int
    flag: int
    filetype: str


class AffinityFileOffsets(NamedTuple):
    directory_offset: int
    file_length: int
    data_length: int
    creation_date: datetime.datetime


class AffinityFileProtection(NamedTuple):
    flags: int


class AffinityFileCompression(NamedTuple):
    algorithm: int
    flags: int

    def __str__(self):
        if self.algorithm == 0:
            return "raw"
        elif self.algorithm == 1:
            return "zlib"
        elif self.algorithm == 2:
            return "zstd"
        else:
            return "unknown"


class AffinityFileInfo(NamedTuple):
    index: int
    offset: int
    size_original: int
    size_stored: int
    checksums: list[int]
    compression: AffinityFileCompression
    version: int
    filename: str


class AffinityFileDirectory(NamedTuple):
    flags: int
    creation_date: datetime.datetime
    file_length: int
    data_length: int
    file_entries: list[AffinityFileInfo]


class AffinityFile:
    _file: Optional[BinaryIO]
    _filename: str
    _refcount = 0
    _closed = False

    header: AffinityFileHeader
    offsets: AffinityFileOffsets
    protection: AffinityFileProtection
    directory: AffinityFileDirectory

    def __init__(self, file: PathLike | BinaryIO | str, mode: str = 'r'):
        if isinstance(file, os.PathLike):
            file = os.fspath(file)
        if isinstance(file, str):
            self._filename = file
            if mode == 'r':
                self._file = open(file, 'rb')
            elif mode == 'w':
                self._file = open(file, 'wb')
            else:
                raise ValueError("AffinityFile requires mode 'r', 'w'")
        else:
            self._file = file
            self._filename = getattr(file, 'name', None)
        self._populate_info()

    def __enter__(self):
        return self

    def __exit__(self, _type, _value, _traceback):
        self.close()

    def __del__(self):
        self.close()

    def listdir(self) -> dict[str, AffinityFileInfo]:
        return dict((data.filename, data) for data in self.directory.file_entries)

    def namelist(self) -> list[str]:
        return list(data.filename for data in self.directory.file_entries)

    def infolist(self) -> list[AffinityFileInfo]:
        return list(self.directory.file_entries)

    def printdir(self, file=None):
        date = self.directory.creation_date.strftime('%Y-%m-%d %H:%M:%S')
        print_columns(
            ("File Name", "Modified", "Original Size", "Stored Size", "Compression"),
            [(entry.filename, date, entry.size_original, entry.size_stored, str(entry.compression))
             for entry in self.directory.file_entries],
            file=file
        )

    def _find_entry(self, name: str) -> Optional[AffinityFileInfo]:
        for file_entry in self.directory.file_entries:
            if file_entry.filename == name:
                return file_entry
        return None

    def closed(self):
        if self._file is None or self._file.closed:
            self._closed = True
        return self._closed

    def close(self):
        self._closed = True
        if self._refcount > 0:
            return
        if self._file is None:
            return
        if self._file.closed:
            return
        self._file.close()

    def _close(self):
        self._refcount -= 1
        if self._closed:
            self.close()

    def read(self, name):
        with self.open(name, "r") as file:
            return file.read()

    def open(self, name, mode="r"):
        if mode not in ['r', 'w']:
            raise ValueError('open() requires mode "r" or "w"')
        if self.closed():
            raise ValueError("attempted to read file that is already closed")
        if mode == 'w':
            raise ValueError("writing is currently not implemented")
        file = self._find_entry(name)
        if file is None:
            raise IOError("file does not exist")
        with self._remember_position():
            self._file.seek(file.offset)
            tag = self._read_tag()
            if tag != CONTAINER_TAG_FIL:
                raise ValueError("file is corrupt, file header could not be found")
        self._refcount += 1
        with self._remember_position():
            self._file.seek(file.offset + 4)
            data = self._file.read(file.size_stored)
        if file.compression.algorithm == 0:
            return io.BytesIO(data)
        elif file.compression.algorithm == 1:
            return io.BytesIO(zlib.decompress(data))
        elif file.compression.algorithm == 2:
            return zstandard.open(io.BytesIO(data), 'rb')
        else:
            raise ValueError("unknown compression algorithm: {0}".format(file.compression))

    @contextlib.contextmanager
    def _remember_position(self):
        if self.closed():
            raise ValueError("attempted to read file that is already closed")
        position = self._file.tell()
        yield
        self._file.seek(position)

    def _populate_info(self):
        self.header = self._read_header()
        self.offsets = self._read_offsets()
        self.protection = self._read_protection()
        self.directory = self._read_directory(self.offsets)

    def _read_tag(self) -> str:
        if self.closed():
            raise ValueError("attempted to read file that is already closed")
        return self._file.read(4).decode('ascii')

    def _read_header(self) -> AffinityFileHeader:
        if self.closed():
            raise ValueError("attempted to read file that is already closed")
        with self._remember_position():
            self._file.seek(0)
            magic = int.from_bytes(self._file.read(4), byteorder='little', signed=False)
            if CONTAINER_MAGIC != magic:
                raise ValueError(
                    "could not read file header, invalid magic {0:x}, expected {1:x}"
                    .format(magic, CONTAINER_MAGIC)
                )
            version = int.from_bytes(self._file.read(2), byteorder='little', signed=False)
            flag = int.from_bytes(self._file.read(2), byteorder='little', signed=False)
            filetype = self._read_tag()[::-1]
            return AffinityFileHeader(version, flag, filetype)

    def _read_offsets(self) -> AffinityFileOffsets:
        if self._file is None:
            raise ValueError("attempted to read file that is already closed")
        with self._remember_position():
            self._file.seek(12)
            tag = self._read_tag()
            if tag != CONTAINER_TAG_INF:
                raise ValueError("could not read file offsets, invalid tag: " + tag)
            directory_offset = int.from_bytes(self._file.read(8), byteorder='little', signed=False)
            file_length = int.from_bytes(self._file.read(8), byteorder='little', signed=False)
            data_length = int.from_bytes(self._file.read(8), byteorder='little', signed=False)
            _ = int.from_bytes(self._file.read(8), byteorder='little', signed=False)
            creation_date = int.from_bytes(self._file.read(8), byteorder='little', signed=True)
            creation_date = datetime.datetime.fromtimestamp(creation_date)
            _ = int.from_bytes(self._file.read(4), byteorder='little', signed=False)
            _ = int.from_bytes(self._file.read(4), byteorder='little', signed=False)
            return AffinityFileOffsets(directory_offset, file_length, data_length, creation_date)

    def _read_protection(self) -> AffinityFileProtection:
        if self.closed():
            raise ValueError("attempted to read file that is already closed")
        with self._remember_position():
            self._file.seek(64)
            tag = self._read_tag()
            if tag != CONTAINER_TAG_PROT:
                raise ValueError("could not read file protection, invalid tag: " + tag)
            flags = int.from_bytes(self._file.read(4), byteorder='little', signed=False)
            return AffinityFileProtection(flags)

    def _read_directory_entry(self, tag: str) -> AffinityFileInfo:
        if self.closed():
            raise ValueError("attempted to read file that is already closed")
        index = int.from_bytes(self._file.read(4), byteorder='little', signed=False)
        _ = int.from_bytes(self._file.read(1), byteorder='little', signed=False)
        offset = int.from_bytes(self._file.read(8), byteorder='little', signed=False)
        size_real = int.from_bytes(self._file.read(8), byteorder='little', signed=False)
        size_stored = int.from_bytes(self._file.read(8), byteorder='little', signed=False)
        checksums = [
            int.from_bytes(self._file.read(4), byteorder='little', signed=False)
        ]
        compression = int.from_bytes(self._file.read(1), byteorder='little', signed=False)
        compression = AffinityFileCompression(
            flags=compression >> 2,
            algorithm=compression & 3
        )
        version = None
        if tag >= CONTAINER_TAG_FT2:
            version = int.from_bytes(self._file.read(4), byteorder='little', signed=False)
        if tag >= CONTAINER_TAG_FT4:
            checksums.append(int.from_bytes(self._file.read(4), byteorder='little', signed=False))
        filename_length = int.from_bytes(self._file.read(2), byteorder='little', signed=False)
        filename = self._file.read(filename_length).decode('utf-8')
        return AffinityFileInfo(
            index, offset, size_real, size_stored, checksums, compression, version, filename
        )

    def _read_directory(self, offsets: AffinityFileOffsets) -> AffinityFileDirectory:
        if self.closed():
            raise ValueError("attempted to read file that is already closed")
        with self._remember_position():
            self._file.seek(offsets.directory_offset)
            tag = self._read_tag()
            flags = int.from_bytes(self._file.read(8), byteorder='little', signed=False)
            creation_date = int.from_bytes(self._file.read(8), byteorder='little', signed=True)
            creation_date = datetime.datetime.fromtimestamp(creation_date)
            file_length = int.from_bytes(self._file.read(8), byteorder='little', signed=False)
            data_length = int.from_bytes(self._file.read(8), byteorder='little', signed=False)
            _ = int.from_bytes(self._file.read(8), byteorder='little', signed=False)
            table_count = int.from_bytes(self._file.read(8), byteorder='little', signed=False)
            table_length = int.from_bytes(self._file.read(4), byteorder='little', signed=False)
            _ = self._file.read(3)
            file_entries = []
            end = self._file.tell() + table_length
            for _ in range(table_count):
                if self._file.tell() >= end:
                    raise ValueError("file table corrupt: trying to read over the end")
                file_entries.append(self._read_directory_entry(tag))
            return AffinityFileDirectory(flags, creation_date, file_length, data_length, file_entries)
