"""Audit changed-class score materialization against archived full RR vectors.

Serial in-process replay only. Patch digest binds payload, not producer trust.
No claim of crash atomicity or combined endpoint/vector commit.
"""
import hashlib,json,sys,time
from array import array
from pathlib import Path
from incremental_IPIN_feature_cache_v1 import Cache
from verify_incremental_IPIN_cache_v1_2026_10_18 import edits

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def main():
 out=Path('experiments/incremental_IPIN_score_patch_v1_2026-10-18');out.mkdir(exist_ok=False)
 gp=Path('experiments/mmc_typed_collision_risk_v1_2026-10-18/groups.json');g=json.loads(gp.read_text());epoch=g['graph_sha256']
 groups={v['sink_RR']:v['members'] for v in g['groups'] if v['kind']=='direct_sink_IPIN'};sizes={s:len(v) for s,v in groups.items()}
 nodes=sorted(n for members in groups.values() for n in members);position={n:i for i,n in enumerate(nodes)};indices={s:[position[n] for n in ns] for s,ns in groups.items()}
 sources={int(k) for k,v in g['fallback_reasons'].items() if v=='fixed_or_unsupported_type_SOURCE'}
 pp=Path('experiments/mmc_typed_collision_risk_v1_2026-10-18/protocol.json');p=json.loads(pp.read_text())
 old=json.loads(Path('experiments/mmc_native_state_geometry_v1_2026-10-18/protocol.json').read_text())['previous_endpoint']
 paths=[Path(old)]+[Path(v['endpoint']) for _,v in sorted(p['inputs'].items())]
 proof=Path('experiments/incremental_IPIN_cache_verification_v1_2026-10-18/verification.json');bindings=json.loads(proof.read_text())['bindings']
 for path,h in bindings.items():assert sha(path)==h
 manifest_path=Path('experiments/mmc_typed_collision_risk_v1_2026-10-18/vector_manifest.json');manifest=json.loads(manifest_path.read_text())
 bindings={**bindings,**{str(q.resolve()):sha(q) for q in [gp,pp,proof,manifest_path,Path(__file__)]}}
 protocol=dict(bindings=bindings,sequence=[1,2,3,0,3,2,1,0],scope='Serial in-process score replay; hash-bound payload and graph inventory, generation rejection; not crash-atomic combined state or untrusted-producer admission. No native or full-flow acceleration claim.',consumer='Two dense IPIN-only double arrays; validate patch before writing touched members, retain all other entries.',byteorder=sys.byteorder,clock='perf_counter_ns; exploratory single sequence')
 with (out/'protocol.json').open('x') as f:json.dump(protocol,f,indent=2)
 snapshots=[sorted(json.loads(q.read_text())['connections'],key=lambda r:r['connection_id']) for q in paths]
 cache=Cache(epoch,sizes,sources,snapshots[0]);generation=0
 values=[array('d',[0])*len(nodes),array('d',[0])*len(nodes)]
 for s in groups:
  ft=cache.class_feature(s)
  for i in indices[s]:values[0][i]=float(ft[1]);values[1][i]=float(ft[2])
 rows=[];current=0
 for target in protocol['sequence']:
  old_features={s:cache.class_feature(s) for s in groups}
  receipt=cache.commit(cache.prepare(epoch,cache.generation,edits(snapshots[current],snapshots[target])))
  start=time.perf_counter_ns()
  entries=[dict(sink=s,old=[str(v) for v in old_features[s][1:]],new=[str(v) for v in cache.class_feature(s)[1:]]) for s in receipt['changed_count_classes']]
  payload=dict(graph_epoch=epoch,inventory_sha256=bindings[str(gp.resolve())],before=generation,after=generation+1,entries=entries)
  patch=dict(payload=payload,sha256=digest(payload));encoded=json.dumps(patch,sort_keys=True).encode();producer_ms=(time.perf_counter_ns()-start)/1e6
  start=time.perf_counter_ns();received=json.loads(encoded);body=received['payload']
  assert digest(body)==received['sha256'] and body['before']==generation and body['after']==generation+1
  assert body['graph_epoch']==epoch and body['inventory_sha256']==bindings[str(gp.resolve())]
  from fractions import Fraction
  writes=[];seen=set()
  for e in body['entries']:
   s=e['sink'];assert s in groups and s not in seen;seen.add(s)
   old_v=[float(Fraction(x)) for x in e['old']];new_v=[float(Fraction(x)) for x in e['new']]
   for i in indices[s]:
    assert all(values[k][i]==old_v[k] for k in range(2));writes.append((i,new_v))
  # Serial replay after full validation; no external readers or crash guarantee.
  for i,new_v in writes:
   for k in range(2):values[k][i]=new_v[k]
  generation=body['after'];consumer_ms=(time.perf_counter_ns()-start)/1e6
  for s in groups:
   ft=cache.class_feature(s)
   for i in indices[s]:assert values[0][i]==float(ft[1]) and values[1][i]==float(ft[2])
  with (out/('patch_%02d.json'%generation)).open('xb') as f:f.write(encoded)
  rows.append(dict(generation=generation,target=target,changed_classes=len(entries),RR_updates=len(writes),payload_bytes=len(encoded),producer_ms=producer_ms,consumer_ms=consumer_ms))
  current=target
 # All archived source states are checked, including previous_native for each case.
 checked=0
 fullpos={n:i for i,n in enumerate(g['positive_RR_ids'])}
 for case in ['case_01','case_02','case_03']:
  for method in p['methods']:
   endpoint=0 if method=='previous_native' else int(case[-2:])
   ref=Cache(epoch,sizes,sources,snapshots[endpoint])
   for field,family in [(1,'typed_group_mean'),(2,'typed_NET_collision')]:
    item=manifest[case+'__'+method+'__'+family];assert sha(item['path'])==item['sha256']
    data=array('d');data.frombytes(Path(item['path']).read_bytes());assert len(data)==item['values']
    for s,members in groups.items():
     expected=float(ref.class_feature(s)[field])
     assert all(data[fullpos[n]]==expected for n in members)
    checked+=len(nodes)
 for path,h in bindings.items():assert sha(path)==h
 with (out/'verification.json').open('x') as f:json.dump(dict(status='pass',bindings=bindings,transitions=rows,archived_IPIN_values_checked=checked,IPIN_nodes=len(nodes),scope=protocol['scope'],remaining='Publish endpoint cache and consumer together through one immutable versioned state; add reject fixtures before treating as transport API.'),f,indent=2)
 print(json.dumps(dict(status='pass',transitions=rows,archived_values=checked)))
if __name__=='__main__':main()
