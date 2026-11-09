"""Original-XML channel projection and exact existing-frame incremental replay."""
import hashlib,json,time,xml.etree.ElementTree as ET
from array import array
from collections import Counter,defaultdict
from fractions import Fraction
from pathlib import Path
from incremental_NET_group_ownership_v1 import Cache

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 out=Path('experiments/real_channel_incremental_v1_2026-10-18');out.mkdir(exist_ok=False)
 root=Path('experiments/mmc_typed_collision_risk_v1_2026-10-18');gpath=root/'groups.json';g=json.loads(gpath.read_text());config=json.loads((root/'protocol.json').read_text());groups={i:v['members'] for i,v in enumerate(g['groups']) if v['kind']=='geometry_channel'};group_of={n:gid for gid,ns in groups.items() for n in ns}
 ep=json.loads(Path(config['inputs']['case_01']['endpoint']).read_text());graph=Path(ep['inputs']['graph']['path']);assert sha(graph)==g['graph_sha256']
 vp=Path('experiments/mmc_typed_collision_risk_verification_v1_2026-10-18/verification.json');proof=json.loads(vp.read_text());assert proof['status']=='pass'
 methods=['native_retained_off','native_retained_on'];cases=['case_01','case_02','case_03'];bindings={str(p.resolve()):sha(p) for p in [gpath,root/'protocol.json',graph,vp,Path(__file__),Path('tools/incremental_NET_group_ownership_v1.py'),Path('tools/incremental_IPIN_feature_cache_v1.py'),Path('tools/net_group_collision_risk_v1.py')]}
 for case in cases:
  for method in methods:
   for path in [Path(config['inputs'][case]['predictions'][method]),root/(case+'__'+method+'.json')]:
    digest=sha(path);assert digest==proof['bindings'][str(path.resolve())];bindings[str(path.resolve())]=digest
 with (out/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,cases=cases,methods=methods,sequence='off->on->off per case',scope='Exact path projection and channel accounting, original XML edge order, no new native jobs or prediction promotion; exploratory component clocks only'),f,indent=2)
 starts=array('I');dest=array('I');stack=[];t=time.perf_counter()
 for action,e in ET.iterparse(graph,events=('start','end')):
  if action=='start':stack.append(e);continue
  parent=stack[-2] if len(stack)>1 else None
  if e.tag=='edge' and parent is not None and parent.tag=='rr_edges':
   starts.append(int(e.get('src_node')));dest.append(int(e.get('sink_node')));parent.remove(e);e.clear()
  elif e.tag=='node' and parent is not None and parent.tag=='rr_nodes':parent.remove(e);e.clear()
  stack.pop()
 assert len(dest)==8097539
 print('XML edge arrays verified',len(dest),'seconds',time.perf_counter()-t,flush=True)
 results=[]
 def project(case,method):
  frame=json.loads(Path(config['inputs'][case]['predictions'][method]).read_text());assert frame['graph_sha256']==g['graph_sha256'];rows=[]
  for r in frame['records']:
   node=r['source'];owned=set()
   if node in group_of:owned.add(node)
   for edge in r['answer']['physical_edge_ids']:
    assert type(edge) is int and 0<=edge<len(dest) and starts[edge]==node
    node=dest[edge]
    if node in group_of:owned.add(node)
   assert node==r['sink']
   rows.append(dict(connection_id=r['connection_id'],net_id=r['net_id'],nodes=sorted(owned)))
  rows.sort(key=lambda r:r['connection_id']);assert len(rows)==115572 and len({r['connection_id'] for r in rows})==len(rows)
  return rows
 def check(cache,rows,case,method):
  snap=cache.snapshot();refs=defaultdict(Counter)
  for r in rows:refs[r['net_id']].update(set(r['nodes']))
  nets={};hist=defaultdict(Counter)
  for net,counts in refs.items():
   ks=Counter(group_of[n] for n in counts);nets[net]=(dict(counts),dict(ks))
   for gid,k in ks.items():hist[gid][k]+=1
  assert snap['nets']==nets
  assert snap['queries']=={r['connection_id']:(r['net_id'],tuple(r['nodes'])) for r in rows}
  assert snap['histograms']=={gid:dict(v) for gid,v in hist.items()}
  journal=json.loads((root/(case+'__'+method+'.json')).read_text())['positive_group_histograms']
  for gid in groups:
   row=journal.get(str(gid));expected={} if row is None else {int(k):v for k,v in row['NET_occupancy_histogram'].items()}
   assert snap['histograms'].get(gid,{})==expected
   expected_feature=(Fraction(0),Fraction(1),Fraction(0)) if row is None else tuple(Fraction(row[k]) for k in ['expected_occupancy','probability_empty','expected_overflow'])
   assert snap['features'][gid]==expected_feature
 for case in cases:
  a,b=[project(case,m) for m in methods];assert all(x['connection_id']==y['connection_id'] and x['net_id']==y['net_id'] for x,y in zip(a,b))
  t=time.perf_counter();cache=Cache(g['graph_sha256'],groups,a);initial=time.perf_counter()-t;check(cache,a,case,methods[0]);case_rows=[]
  for old,new,method in [(a,b,methods[1]),(b,a,methods[0])]:
   delta=[dict(old=x,new=y) for x,y in zip(old,new) if x!=y];assert delta
   t=time.perf_counter();receipt=cache.commit(cache.prepare(g['graph_sha256'],cache.generation,delta));elapsed=time.perf_counter()-t
   check(cache,new,case,method);case_rows.append(dict(target=method,query_updates=len(delta),supplied_delta_prepare_commit_seconds=elapsed,receipt=receipt))
  results.append(dict(case=case,initial_construction_seconds=initial,transitions=case_rows));print('REAL CHANNEL REPLAY PASS',case,flush=True)
 for p,h in bindings.items():assert sha(p)==h
 with (out/'verification.json').open('x') as f:json.dump(dict(status='pass',bindings=bindings,groups=len(groups),queries_per_frame=115572,frames=6,transitions=6,results=results,scope='All original XML edge-chain endpoints, per-query channel sets, per-NET reference multiplicities and group-k histograms plus exact prior feature Fractions checked. Delay/RC certificates transferred from archived verification, no fresh route timing/native utility or combined endpoint+channel publication proof.'),f,indent=2)
 print('ALL REAL CHANNEL TRANSITIONS PASS',flush=True)
if __name__=='__main__':main()
