"""Independent full selector, physical serialization and current pin audit."""
import json,sys,re,hashlib,xml.etree.ElementTree as ET
from collections import Counter,defaultdict
from array import array
from pathlib import Path
from stream_native_route_audit import audit
from audit_native_route import NET,NODE
R=Path(__file__).resolve().parents[1];D=Path(sys.argv[1]);case=sys.argv[2];mode=sys.argv[3];registration=json.loads((D.parent.parent/'protocol.json').read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
p=D/'receipt.json';proof=json.loads(p.read_text());assert proof['complete_partition_and_capacity_pass']
assert all(sha(k)==h for k,h in proof['bindings'].items())
bindings={str(p):sha(p),str(Path(__file__).resolve()):sha(__file__)}
epfile=R/'experiments/mmc_multiplacement_inputs_v1_2026-10-18'/case/'demand/endpoints.json';ep=json.loads(epfile.read_text());graph=Path(ep['inputs']['graph']['path'])
for spec in ep['inputs'].values():assert sha(spec['path'])==spec['sha256'];bindings[spec['path']]=spec['sha256']
identity={x['name']:x for x in map(json.loads,Path(ep['inputs']['native_identity']['path']).read_text().splitlines())}
cap=array('Q');src=array('Q');dst=array('Q');switch=array('Q');sites={};stack=[]
for ev,e in ET.iterparse(graph,events=('start','end')):
 if ev=='start':stack.append(e.tag);continue
 if e.tag=='node' and stack[-2]=='rr_nodes':
  nid=int(e.get('id'));assert nid==len(cap);cap.append(int(e.get('capacity')))
  if e.get('type') in ['SOURCE','SINK']:
   a=e.find('loc').attrib;sites[nid]=tuple(int(a.get(k,'0')) for k in ['xlow','ylow','layer','ptc'])
  e.clear()
 elif e.tag=='edge' and stack[-2]=='rr_edges':src.append(int(e.get('src_node')));dst.append(int(e.get('sink_node')));switch.append(int(e.get('switch_id')));e.clear()
 stack.pop()
pin_indexes={}
for name,native in identity.items():
 sources=[p for p in native['pins'] if p['index']==0];sinks=defaultdict(list)
 for p in native['pins']:
  if p['index']>0:sinks[tuple(p[k] for k in ['x','y','layer','class'])].append(p)
 pin_indexes[name]=(sources,sinks)
rows=[]
for arm in [mode]:
 sketch=Path(registration['frames'][case][mode]);c=json.loads(sketch.read_text());bindings[str(sketch)]=sha(sketch);frameproof=Path(registration['frame_proofs'][case][mode]);fv=json.loads(frameproof.read_text());assert fv['bindings'][str(sketch)]==sha(sketch);assert all(sha(k)==h for k,h in fv['bindings'].items());bindings[str(frameproof)]=sha(frameproof);groups=defaultdict(list)
 for r in c['records']:groups[r['net_id']].append(r)
 own={}
 for net,rs in groups.items():
  used=set()
  for r in rs:
   u=r['source'];seen={u};used.add(u)
   for edge in r['answer']['physical_edge_ids']:
    assert src[edge]==u;u=dst[edge];assert u not in seen;seen.add(u);used.add(u)
   assert u==r['sink']
  own[net]=used
 ledger=Counter();kept=[];decisions=[]
 for net in sorted(groups,key=lambda n:(-len(groups[n]),len(own[n]),n)):
  blockers=sorted(n for n in own[net] if ledger[n]>=cap[n]);decisions.append(dict(net_id=net,admitted=not blockers,blocking_nodes=blockers))
  if not blockers:kept.append(net);ledger.update(own[net])
 d=D;subset=json.loads((d/'subset.json').read_text());pins=json.loads((d/'pin_bindings.json').read_text())
 expected_records=sorted((r for net in kept for r in groups[net]),key=lambda r:r['connection_id'])
 assert subset['records']==expected_records and subset['decisions']==decisions
 ids={r['connection_id'] for r in expected_records};allids={q['connection_id'] for q in ep['connections']}
 assert len(allids)==115572 and subset['pending']==sorted(allids-ids) and len(ids)==len(expected_records)
 assert set(pins)=={str(cid) for cid in ids}
 expected_ends=Counter();expected_pins={}
 for r in expected_records:
  cid=r['connection_id'];name=ep['net_names'][str(r['net_id'])];native=identity[name]
  source,index=pin_indexes[name];sink=index.get(sites[r['sink']],[])
  assert len(source)==len(sink)==1 and tuple(source[0][k] for k in ['x','y','layer','class'])==sites[r['source']]
  assert pins[str(cid)]==dict(net=native['net_id'],name=name,pin=sink[0]['index'])
  expected_ends[(native['net_id'],r['source'],r['sink'])]+=1;expected_pins[(native['net_id'],r['sink'])]=sink[0]['index']
 from native_route_ledger_import_compact import physical_paths
 expected_paths=defaultdict(Counter)
 for rec in expected_records:
  path=[(rec['source'],None)]
  for eid in rec['answer']['physical_edge_ids']:path.append((int(dst[eid]),int(switch[eid])))
  expected_paths[ep['net_names'][str(rec['net_id'])]][tuple(path)]+=1
 actual_paths={name:Counter(paths) for name,paths in physical_paths(d/'seed.route').items()}
 assert dict(expected_paths)==actual_paths
 a=audit(graph,d/'seed.route');assert a['overflow_units']==0 and {int(k):v for k,v in a['node_occupancy'].items()}==dict(ledger)
 assert Counter((q['net_id'],q['source'],q['sink']) for q in a['connections'])==expected_ends
 net=None;observed_pins={};names={}
 for line in (d/'seed.route').read_text().splitlines():
  m=NET.match(line)
  if m:net=int(m[1]);names[net]=m[2]
  m=NODE.match(line)
  if m and m[2]=='SINK':
   pin=re.search(r'Net_pin_index:\s*(\d+)',line);assert pin
   key=(net,int(m[1]));assert key not in observed_pins;observed_pins[key]=int(pin[1])
 assert observed_pins==expected_pins
 assert names=={identity[ep['net_names'][str(net)]]['net_id']:ep['net_names'][str(net)] for net in kept}
 auditfile=d/'independent_seed_physical_audit_v1.json'
 with auditfile.open('x') as f:json.dump(a,f);f.write('\n')
 for name in ['seed.route','subset.json','pin_bindings.json','independent_seed_physical_audit_v1.json']:bindings[str(d/name)]=sha(d/name)
 rows.append(dict(arm=arm,selected_connections=len(ids),pending_connections=len(allids-ids),selected_NETs=len(kept),all_selector_decisions_physical_unions_and_pin_indices_pass=True))
assert all(sha(k)==h for k,h in bindings.items())
with (D/'independent_verification_v1.json').open('x') as f:json.dump(dict(bindings=bindings,rows=rows,all_seed_selections_complete_partitions_XML_paths_capacity_and_current_pin_bindings_pass=True,scope='Complete expected node/switch paths, frozen selector, indexed unambiguous current native pins and capacity proof; partial seed only; every pending connection remains native work. Not full routing, STA, canonical reload, utility or timing result.'),f,indent=2);f.write('\n')
print(json.dumps(rows,indent=2))
