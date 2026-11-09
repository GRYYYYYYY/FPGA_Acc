"""Mutation/invalidation tests for actual files and scoped SHA provider aliases."""
import json,os,sys,types,hashlib
from pathlib import Path
from versioned_digest_cache_v1 import Cache,ORIGINAL_SHA
import pre_route_endpoints
R=Path(__file__).resolve().parents[1];D=R/'experiments/versioned_digest_cache_v1_2026-10-18';p=D/'mutable.dat';p.write_bytes(b'abcd')
c=Cache();first=c.digest(p);assert c.digest(p)==first and c.stats['hits']==1
p.write_bytes(b'wxyz');assert c.digest(p)!=first and c.stats['invalidations']==1
old=p.stat();p.write_bytes(b'1234');os.utime(p,ns=(old.st_atime_ns,old.st_mtime_ns));assert p.stat().st_ctime_ns!=old.st_ctime_ns;assert c.digest(p)==ORIGINAL_SHA(p) and c.stats['invalidations']==2
replacement=D/'replacement.dat';replacement.write_bytes(b'5678');replacement.replace(p);assert c.digest(p)==ORIGINAL_SHA(p) and c.stats['invalidations']==3
p.unlink()
try:c.digest(p)
except FileNotFoundError:pass
else:raise AssertionError('missing file admitted')
p.write_bytes(b'base')
def unstable(path):
 digest=ORIGINAL_SHA(path);path.write_bytes(b'next');return digest
u=Cache(hash_function=unstable)
try:u.digest(p)
except RuntimeError:pass
else:raise AssertionError('unstable admission accepted')
assert not u.entries and u.stats['unstable']==1
other=Cache();assert not other.entries
module=types.ModuleType('routecast_digest_fixture');module.sha=ORIGINAL_SHA;sys.modules[module.__name__]=module
with c.installed():
 assert pre_route_endpoints.sha is c.adapter and module.sha is c.adapter
 assert module.sha(p)==ORIGINAL_SHA(p)
 late=types.ModuleType('routecast_digest_late_fixture');late.sha=pre_route_endpoints.sha;sys.modules[late.__name__]=late
 try:
  with other.installed():pass
 except RuntimeError:pass
 else:raise AssertionError('nested adapters allowed')
assert pre_route_endpoints.sha is ORIGINAL_SHA and module.sha is ORIGINAL_SHA and late.sha is ORIGINAL_SHA
try:
 with other.installed():raise ValueError('intentional callback failure')
except ValueError:pass
assert pre_route_endpoints.sha is ORIGINAL_SHA and module.sha is ORIGINAL_SHA
with other.installed():assert module.sha(p)==ORIGINAL_SHA(p)
assert other.stats['misses']==1 and other.stats['hits']==0
for name in [module.__name__,late.__name__]:del sys.modules[name]
result=dict(status='pass',same_size_change=True,restored_mtime_ctime_invalidates=True,inode_replacement=True,missing_file_rejected=True,unstable_admission_rejected_without_cache_entry=True,nested_provider_rejected=True,independent_caches=True,late_import_alias_restored=True,exception_scope_restored=True,source_sha256=ORIGINAL_SHA(R/'tools/versioned_digest_cache_v1.py'),protocol=str(R/'experiments/mmc_resident_raw_local_abba_v1_2026-10-18/digest_reuse_protocol_v1.json'),stats=c.snapshot())
with (D/'verification.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(result),flush=True)
