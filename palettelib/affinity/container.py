import contextlib
import datetime
import io
import os
from io import BufferedIOBase
from os import PathLike
from typing import BinaryIO, NamedTuple, Optional, Callable

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


class AffinityFileInfo(NamedTuple):
    index: int
    offset: int
    size_original: int
    size_stored: int
    checksums: list[int]
    compressed: bool
    version: int
    filename: str


class AffinityFileDirectory(NamedTuple):
    flags: int
    creation_date: datetime.datetime
    file_length: int
    data_length: int
    file_entries: list[AffinityFileInfo]


class AffinityExtFile(BufferedIOBase):
    _info: AffinityFileInfo
    _file: Optional[BinaryIO]
    _close: Callable[[], None]
    _position = 0

    def __init__(self, file: BinaryIO, info: AffinityFileInfo, close: Callable[[], None]):
        self._file = file
        self._info = info
        self._close = close

    def __enter__(self):
        return self

    def __exit__(self, _type, _value, _traceback):
        self.close()

    @contextlib.contextmanager
    def _remember_position(self):
        if self._file.closed:
            raise ValueError("attempted to read file that is already closed")
        position = self._file.tell()
        yield
        self._file.seek(position)

    def closed(self) -> bool:
        return self._file is None or self._file.closed

    def close(self) -> None:
        if self._file is not None:
            self._close()
            self._file = None

    def peek(self, n=1) -> bytes:
        if n < 0:
            n = self._info.size_original - self._position
        data = None
        with self._remember_position():
            self._file.seek(self._position + self._info.offset)
            data = self._file.read(n)
        return data

    def readable(self):
        if self.closed():
            raise ValueError("attempted to read file that is already closed")
        return True

    def read(self, n=-1) -> bytes:
        if n < 0:
            n = self._info.size_original - self._position
        data = self.peek(n)
        self._position += n
        return data

    def seekable(self):
        if self.closed():
            raise ValueError("attempted to read file that is already closed")
        return self._file.seekable()

    def seek(self, offset, whence=0):
        if self.closed():
            raise ValueError("attempted to read file that is already closed")
        if not self.seekable():
            raise io.UnsupportedOperation("underlying stream is not seekable")
        old_position = self.tell()
        if whence == 0:  # Seek from start of file
            new_position = offset
        elif whence == 1:  # Seek from current position
            new_position = old_position + offset
        elif whence == 2:  # Seek from EOF
            new_position = self._info.offset + offset
        else:
            raise ValueError("whence must be os.SEEK_SET (0), "
                             "os.SEEK_CUR (1), or os.SEEK_END (2)")

        if new_position > self._info.size_original:
            new_position = self._info.size_original

        if new_position < 0:
            new_position = 0
        self._position = new_position
        return self.tell()

    def tell(self):
        if self.closed():
            raise ValueError("attempted to read file that is already closed")
        if not self.seekable():
            raise io.UnsupportedOperation("underlying stream is not seekable")
        return self._position


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
            ("File Name", "Modified", "Original Size", "Stored Size"),
            [(entry.filename, date, entry.size_original, entry.size_stored)
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

    def open(self, name, mode="r") -> AffinityExtFile:
        if mode not in ['r', 'w']:
            raise ValueError('open() requires mode "r" or "w"')
        if self.closed():
            raise ValueError("attempted to read file that is already closed")
        if mode == 'w':
            raise ValueError("writing is currently not implemented")
        file = self._find_entry(name)
        if file is None:
            raise IOError("file does not exist")
        self._refcount += 1
        return AffinityExtFile(self._file, file, self._close)

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
            if magic != CONTAINER_MAGIC:
                raise ValueError("could not read file header, invalid magic: {0:x}".format(magic))
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
        compressed = bool.from_bytes(self._file.read(1), byteorder='little')
        version = None
        if tag >= CONTAINER_TAG_FT2:
            version = int.from_bytes(self._file.read(4), byteorder='little', signed=False)
        if tag >= CONTAINER_TAG_FT4:
            checksums.append(int.from_bytes(self._file.read(4), byteorder='little', signed=False))
        filename_length = int.from_bytes(self._file.read(2), byteorder='little', signed=False)
        filename = self._file.read(filename_length).decode('utf-8')
        return AffinityFileInfo(
            index, offset, size_real, size_stored, checksums, compressed, version, filename
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
