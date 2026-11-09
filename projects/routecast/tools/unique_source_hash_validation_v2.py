"""Bounded concurrent unique content rehash; no cross-pass hash cache."""
import hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from unique_source_hash_validation_v1 import merge_expected

def _check(item):
 path,expected=item;digest=hashlib.sha256();size=0
 with Path(path).open('rb') as stream:
  while True:
   block=stream.read(8*1024*1024)
   if not block:break
   digest.update(block);size+=len(block)
 if digest.hexdigest()!=expected:raise ValueError(f'SHA256 mismatch: {path}')
 return size

def validate_expected(bindings,max_workers=8):
 if type(max_workers) is not int or not 1<=max_workers<=8:raise ValueError('worker bound must be1..8')
 checked=0;byte_count=0
 with ThreadPoolExecutor(max_workers=max_workers) as executor:
  for size in executor.map(_check,sorted(bindings.items())):checked+=1;byte_count+=size
 return dict(unique_paths_checked=checked,bytes_read=byte_count,max_workers=max_workers)
