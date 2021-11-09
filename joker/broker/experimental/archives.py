#!/usr/bin/env python3
# coding: utf-8

import tarfile
import zipfile
from functools import cached_property
from typing import List


class Archive:
    @cached_property
    def inner_paths(self) -> List[str]:
        raise NotImplementedError

    @cached_property
    def entry_path(self) -> str:
        paths = [p for p in self.inner_paths if p.endswith('index.html')]
        if not paths:
            return ''
        return min(paths, key=lambda s: len(s))

    def extract_as_bytes(self, inner_path: str) -> bytes:
        raise NotImplementedError

    def open_inner_file(self, inner_path: str):
        raise NotImplementedError

    @staticmethod
    def open(path: str) -> 'Archive':
        if path.endswith('.zip'):
            return ZipArchive(path)
        tar_suffixes = ['.tar', '.tgz', '.tar.gz']
        for suffix in tar_suffixes:
            if path.endswith(suffix):
                return TarArchive(path)

    def __enter__(self):
        archive_file = getattr(self, 'archive_file', None)
        if hasattr(archive_file, '__enter__'):
            archive_file.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        archive_file = getattr(self, 'archive_file', None)
        if hasattr(archive_file, '__exit__'):
            archive_file.__exit__(exc_type, exc_val, exc_tb)
        return self


class TarArchive(Archive):
    def __init__(self, path: str):
        self.archive_file = tarfile.open(path)

    @cached_property
    def inner_paths(self) -> List[str]:
        return self.archive_file.getnames()

    def extract_as_bytes(self, inner_path: str) -> bytes:
        return self.archive_file.extractfile(inner_path).read()

    def open_inner_file(self, inner_path: str):
        return self.archive_file.extractfile(inner_path)


class ZipArchive(Archive):
    def __init__(self, path: str):
        self.archive_file = zipfile.ZipFile(path)

    def __enter__(self):
        self.archive_file.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.archive_file.__exit__(exc_type, exc_val, exc_tb)

    @cached_property
    def inner_paths(self) -> List[str]:
        return self.archive_file.namelist()

    def extract_as_bytes(self, inner_path: str) -> bytes:
        return self.archive_file.open(inner_path).read()

    def open_inner_file(self, inner_path: str):
        return self.archive_file.open(inner_path)
