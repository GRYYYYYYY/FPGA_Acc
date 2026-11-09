"""Merge expected identities, then rehash every unique path on each validation pass."""
import hashlib
from pathlib import Path

def merge_expected(target,source):
 for path,expected in source.items():
  if not isinstance(path,str) or not isinstance(expected,str) or len(expected)!=64:raise ValueError('invalid SHA256 binding')
  if path in target and target[path]!=expected:raise ValueError(f'conflicting expected SHA256: {path}')
  target[path]=expected
 return target

def validate_expected(bindings):
 checked=0;byte_count=0
 for path,expected in sorted(bindings.items()):
  digest=hashlib.sha256()
  with Path(path).open('rb') as stream:
   while True:
    chunk=stream.read(8*1024*1024)
    if not chunk:break
    digest.update(chunk);byte_count+=len(chunk)
  if digest.hexdigest()!=expected:raise ValueError(f'SHA256 mismatch: {path}')
  checked+=1
 return dict(unique_paths_checked=checked,bytes_read=byte_count)
