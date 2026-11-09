"""Archive terminal cosim vectors with streaming round-trip verification; retain inputs."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            result.update(block)
    return result.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    assert source.is_dir() and output != source and source not in output.parents
    output.mkdir(exist_ok=False)
    records = []
    for path in sorted(source.rglob('*')):
        assert not path.is_symlink(), path
        if not path.is_file():
            continue
        before = digest(path)
        size = path.stat().st_size
        destination = output / (str(path.relative_to(source)) + '.gz')
        destination.parent.mkdir(parents=True, exist_ok=True)
        with path.open('rb') as original, destination.open('xb') as raw:
            with gzip.GzipFile(filename='', fileobj=raw, mode='wb', compresslevel=3, mtime=0) as encoded:
                for block in iter(lambda: original.read(8 << 20), b''):
                    encoded.write(block)
        restored = hashlib.sha256()
        restored_size = 0
        with gzip.open(destination, 'rb') as decoded:
            for block in iter(lambda: decoded.read(8 << 20), b''):
                restored.update(block)
                restored_size += len(block)
        assert restored.hexdigest() == before == digest(path), path
        assert restored_size == size == path.stat().st_size, path
        records.append(dict(relative_path=str(path.relative_to(source)), bytes=size,
                            sha256=before, archive=str(destination.relative_to(output)),
                            archive_sha256=digest(destination), archive_bytes=destination.stat().st_size))
    assert records, 'No vector files'
    report = dict(status='all_archives_stream_roundtrip_verified_originals_retained',
                  source=str(source), files=records, research_complete=False)
    with (output / 'archive_manifest.json').open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')


if __name__ == '__main__':
    main()
