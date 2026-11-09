"""Extend frozen declaration witnesses using explicit protocol SHA256 fields only."""
import datetime
import json
import resource
from collections import defaultdict
from pathlib import Path
from resolve_protocol_source_exposure_v1 import R, references, witnesses, sha, HEX


def protocol_digests(value):
    if isinstance(value,dict):
        for key,item in value.items():
            if isinstance(key,str) and (key == 'protocol_sha256' or key.endswith('_protocol_sha256')) and isinstance(item,str) and HEX.fullmatch(item):
                yield item
            yield from protocol_digests(item)
    elif isinstance(value,list):
        for item in value:
            yield from protocol_digests(item)


def main():
    # Explicit contract distinguishes protocol references from arbitrary source hashes.
    h='a'*64
    assert list(protocol_digests({'protocol_sha256':h,'graph_sha256':h,'source_sha256':h,'nested':[{'parent_protocol_sha256':h}]})) == [h,h]
    assert list(protocol_digests({'protocol_sha256':'bad','unknown_digest':h})) == []
    limit=512*2**20
    free=int(Path('/sys/fs/cgroup/memory.max').read_text())-int(Path('/sys/fs/cgroup/memory.current').read_text())
    assert free >= 28*2**30+limit
    resource.setrlimit(resource.RLIMIT_AS,(limit,limit))
    source=R/'experiments/design_exposure_inventory_v3_2026-10-15/receipt.json'
    previous=R/'experiments/protocol_source_exposure_resolution_v1_2026-10-15/verification.json'
    bound={str(p):sha(p) for p in (source,previous,Path(__file__))}
    inv=json.loads(source.read_text());old=json.loads(previous.read_text());frozen=inv['stable_protocol_hashes']
    assert not inv['protocols_changed_before_finish']
    by_digest=defaultdict(list)
    for name,digest in frozen.items():by_digest[digest].append(name)
    absolute={str(R/name):name for name in frozen}
    edges={name:set() for name in frozen};added=[];unmatched=0
    for name,expected in sorted(frozen.items()):
        p=R/name;assert p.stat().st_size <= 16*2**20
        raw=p.read_bytes();assert __import__('hashlib').sha256(raw).hexdigest()==expected
        data=json.loads(raw)
        for path,digest in references(data):
            target=absolute.get(path)
            if target is not None and frozen[target]==digest:edges[name].add(target)
        for digest in protocol_digests(data):
            targets=by_digest.get(digest,[])
            if not targets:unmatched+=1
            for target in targets:
                if target not in edges[name]:added.append(dict(source=name,target=target,sha256=digest,kind='explicit_protocol_digest_exact_snapshot_content_match'))
                edges[name].add(target)
    direct={}
    for i,row in enumerate(inv['declared_source_records']):
        if row['identity_hash_valid'] and row['protocol'] in frozen:direct.setdefault(row['protocol'],i)
    found=witnesses(edges,direct)
    assert set(old['witness_by_protocol']) <= set(found)
    for name,row in found.items():
        record=inv['declared_source_records'][row['declaration_record_index']]
        if row['distance']==0:assert row['next_protocol'] is None and record['protocol']==name
        else:
            nxt=row['next_protocol'];assert nxt in edges[name]
            assert found[nxt]['distance']==row['distance']-1
            assert found[nxt]['declaration_record_index']==row['declaration_record_index']
    assert all(sha(R/name)==digest for name,digest in frozen.items())
    assert all(sha(path)==digest for path,digest in bound.items())
    out=R/'experiments/protocol_digest_exposure_resolution_v2_2026-10-17';out.mkdir()
    newly=sorted(set(found)-set(old['witness_by_protocol']))
    value=dict(all_pass=True,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),bindings=bound,
        protocol_count=len(frozen),explicit_digest_added_edges=added,unmatched_explicit_protocol_digest_fields=unmatched,
        previous_reached=len(old['witness_by_protocol']),reached=len(found),newly_linked_protocols=newly,
        remaining_unresolved_protocols=sorted(set(frozen)-set(found)),witness_by_protocol=found,
        independently_checked_witness_edges_and_distances=True,strict_unseen_families_certified=0,
        new_native_labels_opened=False,new_model_or_frontend_launched=False,
        scope='Frozen historical declaration snapshot only. Explicit protocol hash references identify exact snapshot content, including identical copies; no filename guessing or arbitrary SHA link. Source declaration witness is not successful execution, actual label exposure, complete global history or unseen-family certification.',
        resources=dict(limit_bytes=limit,shared_headroom_bytes=free,reserved_stage_and_margin_bytes=28*2**30))
    (out/'verification.json').write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps({k:v for k,v in value.items() if k in ('all_pass','protocol_count','previous_reached','reached','strict_unseen_families_certified')}))
    print('added_edges',len(added),'newly_linked',len(newly))


if __name__=='__main__':main()
