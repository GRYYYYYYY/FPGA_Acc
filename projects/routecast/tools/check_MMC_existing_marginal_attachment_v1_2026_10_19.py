"""Input-only existing reference applicability pilot; not a new model or quality trial."""
from pathlib import Path
from collections import defaultdict
import json,hashlib,time,resource
from MMC_zero_node_RC_shared_CSR_v1 import load
from marginal_tree_growth_reference_v1 import grow
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
class Adjacency:
 def __init__(self,offsets,dest):self.offsets=offsets;self.dest=dest
 def get(self,node,default=()):return ((slot,self.dest[slot]) for slot in range(self.offsets[node],self.offsets[node+1]))
class Capacity:
 def __init__(self,values):self.values=values
 def get(self,node,default=0):return self.values[node] if 0<=node<len(self.values) else default
class AuditedAdjacency(Adjacency):
 def get(self,node,default=()):
  # Match the original model domain: no outgoing SINK traversal, no re-entry SOURCE.
  if self.kinds[node]=='SINK':return iter(())
  return ((slot,self.dest[slot]) for slot in range(self.offsets[node],self.offsets[node+1]) if self.kinds[self.dest[slot]]!='SOURCE')
def main():
 begin=time.perf_counter();resource.setrlimit(resource.RLIMIT_CORE,(0,0));resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30));O=R/'experiments/mmc_existing_marginal_attachment_pilot_v1_2026-10-19';O.mkdir(exist_ok=False);ep=R/'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19/episode_01/demand/endpoints.json';meta=json.loads(ep.read_text());groups=defaultdict(list)
 for q in meta['connections']:groups[q['net_id']].append(q)
 net=min(n for n,qs in groups.items() if len(qs)>=16);qs=sorted(groups[net],key=lambda q:q['connection_id']);assert len({q['source'] for q in qs})==1 and len({q['sink'] for q in qs})==len(qs);source=qs[0]['source'];indices=json.loads((R/'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19/episode_01/NET_contribution_indices.json').read_text());index=indices[sorted(groups).index(net)];bank=R/'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19/NET_contributions.jsonl'
 for line in bank.open():
  record=json.loads(line)
  if record['index']==index:break
 else:raise RuntimeError('NET bank index absent')
 assert record['net_id']==net and record['source']==source and set(record['sinks'])=={q['sink'] for q in qs};floors={q['sink']:record['support_distance'][str(q['sink'])][0] for q in qs};budgets={sink:max(10**9,(3*value+1)//2) for sink,value in floors.items()};graph=Path(meta['inputs']['graph']['path']);bindings={str(p):sha(p) for p in [ep,bank,Path(__file__).resolve(),R/'tools/marginal_tree_growth_reference_v1.py',R/'tools/MMC_zero_node_RC_shared_CSR_v1.py']};assert sha(graph)==meta['graph_sha256'];bindings[str(graph)]=meta['graph_sha256']
 protocol={'net_id':net,'fanout':len(qs),'source':source,'ordered_queries':qs,'selection':'First ascending input NETid with >=16 native nonignored sink connections, no route labels.','objective':'Existing zero-price marginal switch-delay branch extension; owned prefix objective sunk, raw prefix charged; ascending connection IDs.','budgets':budgets,'floor_costs':floors,'bindings':bindings,'scope':'Existing reference applicability and paid cost only; no predictor quality, novel mechanism, native policy, global feasibility or netgain claim.'};(O/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');print('PILOT_FROZEN_NET',net,'fanout',len(qs),flush=True)
 tick=time.perf_counter();offsets,dest,costs,caps,kinds,internal=load(graph);load_seconds=time.perf_counter()-tick;adj=AuditedAdjacency(offsets,dest);adj.kinds=kinds;tick=time.perf_counter();result=grow(source,[q['sink'] for q in qs],adj,costs,Capacity(caps),{},0,0,budgets);search_seconds=time.perf_counter()-tick;print('PILOT_GROW_TERMINAL',result['status'],flush=True);tick=time.perf_counter();checked=0
 if result['status']=='CANDIDATE':
  parent={};owned={source}
  for branch in result['branches']:
   u=branch['attachment'];assert u in owned;extension_cost=0
   for slot in branch['new_edges']:
    assert offsets[u]<=slot<offsets[u+1];v=dest[slot];assert v not in owned and caps[v]>0 and kinds[v]!='SOURCE';parent[v]=(u,slot);owned.add(v);extension_cost+=costs[slot];u=v
   assert u==branch['sink'] and extension_cost==branch['incremental_cost']
  assert parent==result['parent'] and owned==set(result['owned'])
  for q,r in zip(qs,result['records']):
   assert q['sink']==r['sink'];u=source;visited={u};raw=0
   for slot in r['edges']:
    assert offsets[u]<=slot<offsets[u+1];u=dest[slot];assert u not in visited and caps[u]>0;visited.add(u);raw+=costs[slot]
   assert u==q['sink'] and raw==r['delay']==result['raw'][u] and floors[u]<=raw<=budgets[u];checked+=1
  assert checked==len(qs)
 check_seconds=time.perf_counter()-tick;tick=time.perf_counter();out=O/'result.json';out.write_text(json.dumps(result,indent=2)+'\n');output_seconds=time.perf_counter()-tick
 (O/'verification.json').write_text(json.dumps({'status':'EXISTING_REFERENCE_ACTUAL_GRAPH_CANDIDATE_PASS' if result['status']=='CANDIDATE' else 'EXISTING_REFERENCE_ACTUAL_GRAPH_REJECTION_PRESERVED','net_id':net,'required_connections':len(qs),'checked_connections':checked,'terminal':result['status'],'costs_seconds':{'graph_load':load_seconds,'grow':search_seconds,'in_memory_audit':check_seconds,'result_output':output_seconds,'total_before_receipt':time.perf_counter()-begin},'peak_rss_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'bindings':{**bindings,str(O/'protocol.json'):sha(O/'protocol.json'),str(out):sha(out)},'independent_XML_physical_audit_pending':True,'scope':protocol['scope']},indent=2)+'\n');print('PILOT_COMPLETE',checked,'of',len(qs),'grow_seconds',search_seconds,flush=True)
if __name__=='__main__':main()
