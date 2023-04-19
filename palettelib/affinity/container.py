import contextlib
import datetime
import io
import os
from io import BufferedIOBase
from os import PathLike
from typing import BinaryIO, NamedTuple, Optional, Callable

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
    info: AffinityFileInfo
    file: Optional[BinaryIO]
    _close: Callable[[], None]
    position = 0

    def __init__(self, file: BinaryIO, info: AffinityFileInfo, close: Callable[[], None]):
        self.file = file
        self.info = info
        self._close = close

    def __enter__(self):
        return self

    def __exit__(self, _type, _value, _traceback):
        self.close()

    @contextlib.contextmanager
    def _remember_position(self):
        if self.file is None:
            raise ValueError("attempted to read file that is already closed")
        position = self.file.tell()
        yield
        self.file.seek(position)

    def close(self) -> None:
        if self.file is not None:
            self._close()
            self.file = None

    def peek(self, n=1) -> bytes:
        if n < 0:
            n = self.info.size_original - self.position
        data = None
        with self._remember_position():
            self.file.seek(self.position + self.info.offset)
            data = self.file.read(n)
        return data

    def readable(self):
        if self.file is None:
            raise ValueError("attempted to read file that is already closed")
        return True

    def read(self, n=-1) -> bytes:
        if n < 0:
            n = self.info.size_original - self.position
        data = self.peek(n)
        self.position += n
        return data

    def seekable(self):
        if self.file is None:
            raise ValueError("attempted to read file that is already closed")
        return self.file.seekable()

    def seek(self, offset, whence=0):
        if self.file is None:
            raise ValueError("attempted to read file that is already closed")
        if not self.seekable():
            raise io.UnsupportedOperation("underlying stream is not seekable")
        old_position = self.tell()
        if whence == 0:  # Seek from start of file
            new_position = offset
        elif whence == 1:  # Seek from current position
            new_position = old_position + offset
        elif whence == 2:  # Seek from EOF
            new_position = self.info.offset + offset
        else:
            raise ValueError("whence must be os.SEEK_SET (0), "
                             "os.SEEK_CUR (1), or os.SEEK_END (2)")

        if new_position > self.info.size_original:
            new_position = self.info.size_original

        if new_position < 0:
            new_position = 0
        self.position = new_position
        return self.tell()

    def tell(self):
        if self.file is None:
            raise ValueError("attempted to read file that is already closed")
        if not self.seekable():
            raise io.UnsupportedOperation("underlying stream is not seekable")
        return self.position


class AffinityFile:
    file: Optional[BinaryIO]
    filename: str

    header: AffinityFileHeader
    offsets: AffinityFileOffsets
    protection: AffinityFileProtection
    directory: AffinityFileDirectory

    def __init__(self, file: PathLike | BinaryIO | str, mode: str = 'r'):
        if isinstance(file, os.PathLike):
            file = os.fspath(file)
        if isinstance(file, str):
            self.filename = file
            if mode == 'r':
                self.file = open(file, 'rb')
            elif mode == 'w':
                self.file = open(file, 'wb')
            else:
                raise ValueError("AffinityFile requires mode 'r', 'w'")
        else:
            self.file = file
            self.filename = getattr(file, 'name', None)
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
        entries = [
            ("File Name", "Modified", "Size"),
            *((entry.filename, date, str(entry.size_original)) for entry in self.directory.file_entries),
        ]
        filename_len = max(len(entry[0]) for entry in entries)
        modified_len = max(len(entry[1]) for entry in entries)
        size_len = max(len(entry[2]) for entry in entries)

        for entry in entries:
            filename, modified, size = entry
            print(
                "{0} {1} {2}".format(
                    filename.ljust(filename_len),
                    modified.ljust(modified_len),
                    size.rjust(size_len)
                ),
                file=file
            )

    def _find_entry(self, name: str) -> Optional[AffinityFileInfo]:
        for file_entry in self.directory.file_entries:
            if file_entry.filename == name:
                return file_entry
        return None

    def close(self):
        if self.file is not None:
            self.file.close()
            self.file = None

    def read(self, name):
        """Return file bytes for name."""
        with self.open(name, "r") as fp:
            return fp.read()

    def open(self, name, mode="r"):
        if mode not in ['r', 'w']:
            raise ValueError('open() requires mode "r" or "w"')
        if self.file is None:
            raise ValueError("attempted to read file that is already closed")
        if mode == 'w':
            raise ValueError("writing is currently not implemented")
        file = self._find_entry(name)
        if file is None:
            raise IOError("file does not exist")
        return AffinityExtFile(self.file, file, self.close)

    @contextlib.contextmanager
    def _remember_position(self):
        if self.file is None:
            raise ValueError("attempted to read file that is already closed")
        position = self.file.tell()
        yield
        self.file.seek(position)

    def _populate_info(self):
        self.header = self._read_header()
        self.offsets = self._read_offsets()
        self.protection = self._read_protection()
        self.directory = self._read_directory(self.offsets)

    def _read_tag(self) -> str:
        if self.file is None:
            raise ValueError("attempted to read file that is already closed")
        return self.file.read(4).decode('ascii')

    def _read_header(self) -> AffinityFileHeader:
        if self.file is None:
            raise ValueError("attempted to read file that is already closed")
        with self._remember_position():
            self.file.seek(0)
            magic = int.from_bytes(self.file.read(4), byteorder='little', signed=False)
            if magic != CONTAINER_MAGIC:
                raise ValueError("could not read file header, invalid magic: {0:x}".format(magic))
            version = int.from_bytes(self.file.read(2), byteorder='little', signed=False)
            flag = int.from_bytes(self.file.read(2), byteorder='little', signed=False)
            filetype = self._read_tag()[::-1]
            return AffinityFileHeader(version, flag, filetype)

    def _read_offsets(self) -> AffinityFileOffsets:
        if self.file is None:
            raise ValueError("attempted to read file that is already closed")
        with self._remember_position():
            self.file.seek(12)
            tag = self._read_tag()
            if tag != CONTAINER_TAG_INF:
                raise ValueError("could not read file offsets, invalid tag: " + tag)
            directory_offset = int.from_bytes(self.file.read(8), byteorder='little', signed=False)
            file_length = int.from_bytes(self.file.read(8), byteorder='little', signed=False)
            data_length = int.from_bytes(self.file.read(8), byteorder='little', signed=False)
            _ = int.from_bytes(self.file.read(8), byteorder='little', signed=False)
            creation_date = int.from_bytes(self.file.read(8), byteorder='little', signed=True)
            creation_date = datetime.datetime.fromtimestamp(creation_date)
            _ = int.from_bytes(self.file.read(4), byteorder='little', signed=False)
            _ = int.from_bytes(self.file.read(4), byteorder='little', signed=False)
            return AffinityFileOffsets(directory_offset, file_length, data_length, creation_date)

    def _read_protection(self) -> AffinityFileProtection:
        if self.file is None:
            raise ValueError("attempted to read file that is already closed")
        with self._remember_position():
            self.file.seek(64)
            tag = self._read_tag()
            if tag != CONTAINER_TAG_PROT:
                raise ValueError("could not read file protection, invalid tag: " + tag)
            flags = int.from_bytes(self.file.read(4), byteorder='little', signed=False)
            return AffinityFileProtection(flags)

    def _read_directory_entry(self, tag: str) -> AffinityFileInfo:
        if self.file is None:
            raise ValueError("attempted to read file that is already closed")
        index = int.from_bytes(self.file.read(4), byteorder='little', signed=False)
        _ = int.from_bytes(self.file.read(1), byteorder='little', signed=False)
        offset = int.from_bytes(self.file.read(8), byteorder='little', signed=False)
        size_real = int.from_bytes(self.file.read(8), byteorder='little', signed=False)
        size_stored = int.from_bytes(self.file.read(8), byteorder='little', signed=False)
        checksums = [
            int.from_bytes(self.file.read(4), byteorder='little', signed=False)
        ]
        compressed = bool.from_bytes(self.file.read(1), byteorder='little')
        version = None
        if tag >= CONTAINER_TAG_FT2:
            version = int.from_bytes(self.file.read(4), byteorder='little', signed=False)
        if tag >= CONTAINER_TAG_FT4:
            checksums.append(int.from_bytes(self.file.read(4), byteorder='little', signed=False))
        filename_length = int.from_bytes(self.file.read(2), byteorder='little', signed=False)
        filename = self.file.read(filename_length).decode('utf-8')
        return AffinityFileInfo(
            index, offset, size_real, size_stored, checksums, compressed, version, filename
        )

    def _read_directory(self, offsets: AffinityFileOffsets) -> AffinityFileDirectory:
        if self.file is None:
            raise ValueError("attempted to read file that is already closed")
        with self._remember_position():
            self.file.seek(offsets.directory_offset)
            tag = self._read_tag()
            flags = int.from_bytes(self.file.read(8), byteorder='little', signed=False)
            creation_date = int.from_bytes(self.file.read(8), byteorder='little', signed=True)
            creation_date = datetime.datetime.fromtimestamp(creation_date)
            file_length = int.from_bytes(self.file.read(8), byteorder='little', signed=False)
            data_length = int.from_bytes(self.file.read(8), byteorder='little', signed=False)
            _ = int.from_bytes(self.file.read(8), byteorder='little', signed=False)
            table_count = int.from_bytes(self.file.read(8), byteorder='little', signed=False)
            table_length = int.from_bytes(self.file.read(4), byteorder='little', signed=False)
            _ = self.file.read(3)
            file_entries = []
            end = self.file.tell() + table_length
            for _ in range(table_count):
                if self.file.tell() >= end:
                    raise ValueError("file table corrupt: trying to read over the end")
                file_entries.append(self._read_directory_entry(tag))
            return AffinityFileDirectory(flags, creation_date, file_length, data_length, file_entries)
