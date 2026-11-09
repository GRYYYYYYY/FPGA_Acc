"""Frozen ABC-CBA component replay with paid preparation and exact full results."""
from pathlib import Path
from fractions import Fraction
import json,hashlib,time,resource
from MMC_zero_node_RC_shared_CSR_v1 import load
from load_structural_node_base_v1 import load as load_base
from criticality_shared_tree_sparse_reference_v3 import Graph as Reference
from compiled_criticality_tree_v1 import Graph as Generic,BINARY
from compiled_criticality_tree_v2 import Graph as Frozen,FrozenPrices
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
class Prices:
 def __init__(self,values):self.values=values;self.calls=0
 def get(self,n,default=0):self.calls+=1;return self.values[n]
def norm(r):return dict(r,path_slots=list(r['path_slots'])) if 'path_slots' in r else r
def main():
 begin=time.perf_counter();resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30));resource.setrlimit(resource.RLIMIT_CORE,(0,0));O=R/'experiments/mmc_NET5_balanced_adapter_cost_v1_2026-10-19';O.mkdir(exist_ok=False);B=R/'experiments/mmc_NET5_structural_criticality_attachment_v1_2026-10-19';reference=B/'result.json';records=json.loads(reference.read_text());spec=json.loads((B/'protocol.json').read_text());admission=R/'experiments/mmc_NET5_compiled_adapter_cost_review_v1_2026-10-19/research_decision_v1.json';assert json.loads(admission.read_text())['all41_result_file_bytes_equal'];graph=Path(next(p for p in spec['bindings'] if p.endswith('rr_graph.xml')));assert sha(graph)==spec['bindings'][str(graph)];order=['reference','generic','frozen','frozen','generic','reference'];files=[admission,reference,B/'protocol.json',B/'independent_verification_v1.json',R/'tools/compiled_criticality_tree_v1.py',R/'tools/compiled_criticality_tree_v2.py',R/'tools/criticality_shared_tree_sparse_reference_v3.py',BINARY,Path(__file__).resolve()];bindings={str(p):sha(p) for p in files}
 (O/'protocol.json').write_text(json.dumps({'order':order,'bindings':bindings,'graph':str(graph),'queries_per_round':41,'scope':'Balanced component replay on exposed NET5 only; separate immutable workspaces per backend, common imported graph and exact static inputs. Preparation costs paid and reported, shared between each arm two calls. No full workflow/native/gain claim.','buffer_policy':'One static FrozenPrices pack and graph workspace per frozen arm epoch; reused only while identical immutable prices. Generic conversion stays inside every query.','failure_policy':'Stop on first parity mismatch; no retries or selecting faster repeat.'},indent=2)+'\n');tick=time.perf_counter();base,bb=load_base(904438,10**18);base_seconds=time.perf_counter()-tick;tick=time.perf_counter();offsets,dest,costs,caps,kinds,_=load(graph);graph_seconds=time.perf_counter()-tick;fields={'row_offsets':offsets,'dest_ranks':dest};initial=[0]*len(caps);instances={};setup={};prices={};rows=[]
 try:
  for mode,cls in [('reference',Reference),('generic',Generic),('frozen',Frozen)]:
   tick=time.perf_counter();instances[mode]=cls(fields,costs,initial);setup[mode]={'workspace_seconds':time.perf_counter()-tick};tick=time.perf_counter();prices[mode]=FrozenPrices(base) if mode=='frozen' else Prices(base);setup[mode]['price_snapshot_setup_seconds']=time.perf_counter()-tick
  frozen_bytes=hashlib.sha256(bytes(prices['frozen']._buffer.buffer)).hexdigest()
  for index,mode in enumerate(order):
   tree=instances[mode].tree(spec['source']);counter_before=prices[mode].calls if mode!='frozen' else None;native_before=list(instances[mode].total_stats) if mode!='reference' else None;tick=time.perf_counter();answers=[]
   for entry in records['queries_in_execution_order']:
    q=entry['query'];result=tree.expand(q['sink'],Fraction(*entry['criticality']),prices[mode],spec['budgets'][str(q['sink'])]);answers.append(norm(result))
   elapsed=time.perf_counter()-tick
   expected=[{k:v for k,v in e.items() if k not in ['connection_id','query','criticality']} for e in records['queries_in_execution_order']];assert answers==expected;assert tree.parents=={int(n):tuple(v) for n,v in records['parents'].items()} and tree.arrival=={int(n):v for n,v in records['arrival'].items()};native=[x-y for x,y in zip(instances[mode].total_stats,native_before)] if mode!='reference' else None
   if mode=='frozen':assert hashlib.sha256(bytes(prices['frozen']._buffer.buffer)).hexdigest()==frozen_bytes
   payload=O/f'round_{index+1:02d}_{mode}.json';payload.write_text(json.dumps(answers,indent=2)+'\n');bindings[str(payload)]=sha(payload);row={'round':index+1,'mode':mode,'seconds41_including_adapter':elapsed,'full_result_and_tree_equal':True,'native_stats':native,'price_getter_calls':prices[mode].calls-counter_before if mode!='frozen' else None};rows.append(row);(O/'progress.json').write_text(json.dumps({'rows':rows},indent=2)+'\n');print('BALANCED_ADAPTER',index+1,mode,elapsed,flush=True)
  assert len({tuple(r['native_stats']) for r in rows if r['native_stats'] is not None})==1;assert len({bindings[str(O/f"round_{r['round']:02d}_{r['mode']}.json")] for r in rows})==1
 finally:
  for g in instances.values():
   if hasattr(g,'close'):g.close()
 bindings.update(bb);bindings[str(O/'protocol.json')]=sha(O/'protocol.json');(O/'verification.json').write_text(json.dumps({'status':'ALL6_BALANCED_ADAPTER_RESULTS_TREES_NATIVE_WORK_AND_FROZEN_BUFFER_UNCHANGED_PASS','rows':rows,'setup_seconds':setup,'shared_base_load_seconds':base_seconds,'shared_graph_load_seconds':graph_seconds,'total_before_receipt_seconds':time.perf_counter()-begin,'frozen_buffer_sha256':frozen_bytes,'bindings':bindings,'scope':'Balanced component clocks, two observations per arm; no reset of OS caches, full-design, dynamic epoch or workflow speed proof.'},indent=2)+'\n');print('BALANCED_ADAPTER_ALL6_PASS',flush=True)
if __name__=='__main__':main()
