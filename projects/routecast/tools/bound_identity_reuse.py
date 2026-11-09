"""Synchronous experimental reuse anchored in a native identity cache receipt.

Caller pins the seed receipt hash. No signatures, concurrent mutation guarantee,
logical-equivalence proof, route/STA certification, or durable recovery.
"""
import json
from pathlib import Path
from guarded_identity_rebinding import rebind_identity
from native_identity_cache import NativeIdentityCache
from pre_route_endpoints import placements, physical_maps, sha

def bindings(command, cwd):
    cwd = Path(cwd)
    raw, probe = NativeIdentityCache.__new__(NativeIdentityCache)._bindings(command,cwd)
    indices = {'binary':0,'architecture':1,'blif':2,
               **{n:probe.index(f)+1 for n,f in [('net','--net_file'),('place','--place_file'),('graph','--read_rr_graph')]}}
    files = {n:str((cwd/probe[i]).resolve()) for n,i in indices.items()}
    normalized = probe.copy()
    for n,i in indices.items(): normalized[i] = '<'+n+'>'
    return dict(command=normalized,sha256=raw['inputs_sha256'],files=files)

def seed(command, cwd, cache_directory, destination):
    before = bindings(command,cwd)
    table, evidence = NativeIdentityCache(cache_directory).get(command,cwd)
    if bindings(command,cwd) != before: raise ValueError('inputs changed during seed')
    cache_receipt = table.parent/'receipt.json'
    proof = json.loads(cache_receipt.read_text())
    if proof['exit_code'] != 1 or proof['table_sha256'] != sha(table):
        raise ValueError('native seed proof mismatch')
    record = dict(bindings=before,table=str(table),table_sha256=sha(table),
                  native_receipt=str(cache_receipt),native_receipt_sha256=sha(cache_receipt),
                  log=str(table.parent/'identity.log'),log_sha256=sha(table.parent/'identity.log'),
                  source_sha256=sha(Path(__file__)),cache=evidence)
    destination = Path(destination)
    with destination.open('x') as stream: stream.write(json.dumps(record,indent=2)+'\n')
    return sha(destination)

def reuse(seed_path, expected_sha256, command, cwd):
    seed_path = Path(seed_path)
    if sha(seed_path) != expected_sha256: raise ValueError('seed receipt changed')
    record = json.loads(seed_path.read_text())
    if record['source_sha256'] != sha(Path(__file__)): raise ValueError('adapter changed')
    for path,expected in ((record['table'],record['table_sha256']),
                          (record['native_receipt'],record['native_receipt_sha256']),
                          (record['log'],record['log_sha256'])):
        if sha(path) != expected: raise ValueError('native evidence changed')
    old = record['bindings']
    if any(sha(p) != old['sha256'][n] for n,p in old['files'].items()):
        raise ValueError('seed inputs changed')
    target = bindings(command,cwd)
    if target['command'] != old['command']: raise ValueError('native options changed')
    for name in old['sha256']:
        if name != 'place' and target['sha256'][name] != old['sha256'][name]:
            raise ValueError('identity input changed: '+name)
    proof = json.loads(Path(record['native_receipt']).read_text())
    if proof['bindings']['inputs_sha256'] != old['sha256'] or proof['table_sha256'] != record['table_sha256']:
        raise ValueError('seed/native binding mismatch')
    old_place = placements(old['files']['place'],old['sha256']['net'])
    new_place = placements(target['files']['place'],target['sha256']['net'])
    table = [json.loads(s) for s in Path(record['table']).read_text().splitlines()]
    result = rebind_identity(table,old_place,new_place,physical_maps(target['files']['graph']))
    if bindings(command,cwd) != target or sha(seed_path) != expected_sha256:
        raise ValueError('inputs changed during reuse')
    if any(sha(p) != old['sha256'][n] for n,p in old['files'].items()):
        raise ValueError('seed inputs changed during reuse')
    return result
