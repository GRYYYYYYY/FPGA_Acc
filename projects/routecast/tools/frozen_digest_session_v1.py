"""Scoped digest reuse for declared frozen files; never a persistent trust cache."""
import os
import hashlib
from pathlib import Path


class FrozenDigestSession:
    def __init__(self, expected, reader, budget=128 << 20):
        self.expected = {os.path.abspath(p): h for p, h in expected.items()}
        self.reader = reader
        self.cache = {}
        self.budget = budget
        self.cached_bytes = 0
        self.stats = dict(requests=0, hits=0, frozen_reads=0, uncached_reads=0)

    @staticmethod
    def signature(path):
        s = Path(path).stat()
        return s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns

    def __call__(self, path):
        self.stats['requests'] += 1
        key = os.path.abspath(path)
        if key not in self.expected:
            self.stats['uncached_reads'] += 1
            return self.reader(path)
        before = self.signature(path)
        cached = self.cache.get(key)
        # Metadata alone failed a real same-size rewrite/mtime restoration guard.
        # Always read all bytes; cache only avoids rehashing identical contents.
        if before[2] <= self.budget:
            data = Path(path).read_bytes()
            if self.signature(path) != before:
                raise RuntimeError('Frozen file changed during content read: ' + key)
            if cached is not None and cached[0] == data:
                self.stats['hits'] += 1
                return cached[1]
        else:
            data = None
        self.stats['frozen_reads'] += 1
        digest = hashlib.sha256(data).hexdigest() if data is not None else self.reader(path)
        if self.signature(path) != before:
            raise RuntimeError('Frozen file changed during digest read: ' + key)
        if digest != self.expected[key]:
            raise ValueError('Frozen input digest mismatch: ' + key)
        if data is not None and cached is None and self.cached_bytes + len(data) <= self.budget:
            self.cache[key] = data, digest
            self.cached_bytes += len(data)
        return digest
