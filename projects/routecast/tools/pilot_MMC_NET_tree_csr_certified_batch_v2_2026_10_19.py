"""Fixed first16 multi-sink NETs, shared XML-derived CSR, no native labels."""
import pathlib,json,hashlib,time,resource,xml.etree.ElementTree as ET
from array import array
from fractions import Fraction
from collections import defaultdict
from shortest_NET_tree_csr_certified_v2 import prepare_csr
from shortest_NET_tree_ensemble_v1 import sample
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,j):
 with p.open('x') as f:json.dump(j,f,indent=2);f.write('\n')
def main():
 resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30));tick=time.perf_counter();ep=R/'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19/episode_01/demand/endpoints.json';meta=json.loads(ep.read_text());groups=defaultdict(list)
 for q in meta['connections']:groups[q['net_id']].append(q)
 selected=sorted(n for n,qs in groups.items() if len({q['sink'] for q in qs})>=2)[:16];assert len(selected)==16
 graph=pathlib.Path(meta['inputs']['graph']['path']);assert sha(graph)==meta['graph_sha256'];core=R/'experiments/shortest_NET_tree_csr_certified_core_v2_2026-10-19/verification.json';assert json.loads(core.read_text())['status']=='300_random_graph_early_stop_and_full_search_supports_match'
 O=R/'experiments/mmc_NET_tree_csr_certified_batch_v2_2026-10-19';O.mkdir();files=[ep,graph,core,pathlib.Path(__file__).resolve(),R/'tools/shortest_NET_tree_csr_certified_v2.py',R/'tools/shortest_NET_tree_ensemble_v1.py'];bindings={str(p):sha(p) for p in files};write(O/'protocol.json',dict(bindings=bindings,selected_NETs=selected,selection='First16 ascending physical NET IDs with >=2distinct sinks, episode01; no label read',samples_per_NET=16,seed=19,memory_limit_bytes=32*2**30,scope='Shared-graph feasibility and component cost, not full-design quality/fullworkflow timing. Fixed batch not representative sampling; no total-design extrapolation.'))
 caps=array('I');kinds=[];dest=array('I');costs=array('Q');offsets=array('Q');switches={};stack=[];last_source=-1;setup=time.perf_counter()
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='node' and parent=='rr_nodes':
   assert int(e.get('id'))==len(caps);caps.append(int(e.get('capacity')));kinds.append(e.get('type'));t=e.find('timing');assert Fraction(t.get('R'))==Fraction(t.get('C'))==0
  elif e.tag=='switch' and parent=='switches':
   t=e.find('timing');assert Fraction(t.get('Cinternal','0'))==0 and e.get('type') in ['buffer','mux','tristate'];value=Fraction(t.get('Tdel','0'))*10**18;assert value.denominator==1 and 0<=value<2**64;switches[int(e.get('id'))]=int(value)
  elif e.tag=='edge' and parent=='rr_edges':
   u,v,s=(int(e.get(k)) for k in ['src_node','sink_node','switch_id']);assert u>=last_source;last_source=u
   while len(offsets)<=u:offsets.append(len(dest))
   dest.append(v);costs.append(switches[s])
  if (e.tag,parent) in [('node','rr_nodes'),('switch','switches'),('edge','rr_edges')]:stack[-2].remove(e);e.clear()
  stack.pop()
 while len(offsets)<=len(caps):offsets.append(len(dest))
 assert len(caps)==904438 and len(dest)==8097539 and len(offsets)==len(caps)+1;graph_seconds=time.perf_counter()-setup;print('SHARED CSR READY',graph_seconds,flush=True)
 rows=[]
 for net in selected:
  qs=groups[net];sources={q['source'] for q in qs};assert len(sources)==1;source=sources.pop();sinks=sorted({q['sink'] for q in qs});begin=time.perf_counter();prepared=prepare_csr(offsets,dest,costs,caps,kinds,source,sinks);search=time.perf_counter()-begin;trees=[];sample_start=time.perf_counter()
  for i in range(16):
   tree=sample(prepared,seed=19,net_id=net,sample_index=i)
   for sink,path in tree['paths'].items():
    u=source;cost=0;seen={u}
    for eid in path:
     assert offsets[u]<=eid<offsets[u+1];u=dest[eid];assert u not in seen and caps[u]>0;seen.add(u);cost+=costs[eid]
    assert u==sink and (cost,len(path))==prepared['distance'][sink]
   trees.append(dict(nodes=sorted(tree['nodes']),paths={str(s):list(p) for s,p in tree['paths'].items()}))
  parent_assignments=1
  for choices in prepared['choices'].values():parent_assignments*=len(choices)
  for name in ['potential_cost','potential_hops']:
   certificate=O/f'net_{net}_{name}.bin';certificate.write_bytes(prepared[name].tobytes());bindings[str(certificate)]=sha(certificate)
  p=O/f'net_{net}.json';write(p,dict(source=source,sinks=sinks,choices={str(n):list(x) for n,x in prepared['choices'].items()},distance={str(n):list(x) for n,x in prepared['distance'].items()},samples=trees));bindings[str(p)]=sha(p);row=dict(net_id=net,sinks=len(sinks),support_nodes=len(prepared['distance']),branching_nodes=sum(len(x)>1 for x in prepared['choices'].values()),parent_assignments=str(parent_assignments),search_seconds=search,sample_and_path_audit_seconds=time.perf_counter()-sample_start,**prepared['search_stats']);rows.append(row);print('NET PASS',net,len(sinks),row['support_nodes'],row['parent_assignments'],flush=True)
 write(O/'receipt.json',dict(status='FIXED16_NET_CERTIFIED_CSR_POTENTIALS_AND_256_TREES_PRODUCED',bindings=bindings,rows=rows,graph_setup_seconds=graph_seconds,paid_component_seconds=time.perf_counter()-tick,independent_global_potential_audit_pending=True,scope='Input-only fixed16NET feasibility and component times. All physical graph nodes/edges available; no native labels. No complete55300NET forecast, quality, balanced full-time gain, global min dual, STA or hardware claim.'))
if __name__=='__main__':main()
