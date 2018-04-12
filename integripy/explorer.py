import hashlib
import os
from abc import ABCMeta, abstractmethod
from pathlib import Path

from integripy import application

meta_files = {}


class Item(metaclass=ABCMeta):
    def __init__(self, root: Path, path: Path):
        self._root = root
        self._path = path
        self._name = path.name

    @property
    def path(self) -> Path:
        return self._path

    @property
    def full_path(self) -> Path:
        return self._root / self._path

    @property
    def name(self) -> str:
        return self._name

    @abstractmethod
    def size(self) -> int:
        pass

    @abstractmethod
    def clean_hash(self) -> str:
        pass

    @abstractmethod
    def hash(self) -> str:
        pass

    @abstractmethod
    def corrupt(self) -> bool:
        pass


class Directory(Item):
    def __init__(self, root: Path, path: Path):
        super().__init__(root, path)

    @property
    def size(self) -> int:
        return sum((item.size for item in self.files_recursive()))

    @property
    def clean_hash(self) -> str:
        return ''

    @property
    def hash(self) -> str:
        return ''

    @property
    def corrupt(self) -> bool:
        return False

    def files_recursive(self):
        """Returns all whitelisted files in the directory tree."""
        files_recursive = []
        if self.full_path.is_dir():
            for d, dirs, files in os.walk(self.full_path):
                dirs = [d for d in dirs if not Path(d).name.startswith('.')]
                dirs.sort()
                files = [
                    f for f in files if
                    not Path(f).name.startswith('.')
                    and Path(f).suffix in application.config['EXTENSIONS']
                ]
                files.sort()
                files_recursive += [Explorer.item(self._root, Path(d).relative_to(self._root) / f) for f in files]
        return files_recursive


class File(Item):
    def __init__(self, root: Path, path: Path):
        super().__init__(root, path)
        self._hash_file_path = self.full_path.parent / f'{self.name}.blake2'

    @property
    def clean_hash(self) -> str:
        if self._hash_file_path.is_file():
            with open(self._hash_file_path, 'r') as f:
                return f.read()
        return ''

    @property
    def hash(self) -> str:
        if self.full_path.is_file():
            m = hashlib.blake2b()
            with open(self.full_path, 'rb') as f:
                while True:
                    chunk = f.read(application.config['CHUNK_SIZE'])
                    if not chunk:
                        break
                    m.update(chunk)
            return m.hexdigest()
        return ''

    @property
    def corrupt(self) -> bool:
        clean_hash = self.clean_hash
        return clean_hash != self.hash if clean_hash else False

    @property
    def size(self) -> int:
        # Add 128 for the hash file
        return self.full_path.stat().st_size + 128 if self.full_path.is_file() else 0

    def update_hash_file(self) -> None:
        """Creates or updates the hash file."""
        with open(self._hash_file_path, 'w') as f:
            f.write(self.hash)

    def mirror(self):
        """Returns its counterpart File."""
        return File(
            application.config['DST_ROOT'] if self._root == application.config['SRC_ROOT'] else application.config[
                'SRC_ROOT'], self._path)


class MetaFile:
    def __init__(self, name):
        self._name = name
        self._src_file = None
        self._dst_file = None

    @property
    def src_file(self) -> File:
        if self._src_file is not None and not self._src_file.full_path.is_file():
            self._src_file = None
        return self._src_file

    @property
    def dst_file(self) -> File:
        if self._dst_file is not None and not self._dst_file.full_path.is_file():
            self._dst_file = None
        return self._dst_file

    @src_file.setter
    def src_file(self, src_file: File) -> None:
        self._src_file = src_file

    @dst_file.setter
    def dst_file(self, dst_file: File) -> None:
        self._dst_file = dst_file


class Explorer:

    @staticmethod
    def item(root: Path, path: Path) -> Item:
        """Returns a Directory or File, and creates the associated MetaFile."""
        if (root / path).is_dir():
            return Directory(root, path)
        name = str(path)
        try:
            meta_file = meta_files[name]
        except KeyError:
            meta_file = MetaFile(name)
            meta_files[name] = meta_file
        if root == application.config['SRC_ROOT']:
            if meta_file.src_file is None:
                meta_file.src_file = File(root, path)
            return meta_file.src_file
        elif root == application.config['DST_ROOT']:
            if meta_file.dst_file is None:
                meta_file.dst_file = File(root, path)
            return meta_file.dst_file

    @staticmethod
    def meta_file(path: Path) -> MetaFile:
        return meta_files[str(path)]

    @staticmethod
    def sync(src: File, dst: File) -> None:
        """Synchronizes files (almost) like rsync."""
        if not dst.full_path.parent.is_dir():
            dst.full_path.parent.mkdir(parents=True)
        if dst.full_path.is_file():
            with open(src.full_path, 'rb') as s, open(dst.full_path, 'r+b') as d:
                while True:
                    position = s.tell()
                    src_chunk = s.read(application.config['CHUNK_SIZE'])
                    if not src_chunk:
                        d.truncate()
                        break
                    dst_chunk = d.read(application.config['CHUNK_SIZE'])
                    if not dst_chunk:
                        d.seek(position)
                        d.write(src_chunk)
                    else:
                        src_m = hashlib.blake2b()
                        src_m.update(src_chunk)
                        src_hash = src_m.hexdigest()
                        dst_m = hashlib.blake2b()
                        dst_m.update(dst_chunk)
                        dst_hash = dst_m.hexdigest()
                        if src_hash != dst_hash:
                            d.seek(position)
                            d.write(src_chunk)
        else:
            with open(src.full_path, 'rb') as s, open(dst.full_path, 'wb') as d:
                while True:
                    chunk = s.read(application.config['CHUNK_SIZE'])
                    if not chunk:
                        break
                    d.write(chunk)
