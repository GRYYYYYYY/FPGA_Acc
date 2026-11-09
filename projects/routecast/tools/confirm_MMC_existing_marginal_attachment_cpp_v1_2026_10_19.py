"""Same frozen applicability input through prior bound C++ implementation."""
from pathlib import Path
import json,hashlib,time,resource
from MMC_zero_node_RC_shared_CSR_v1 import load
from marginal_tree_growth_cpp_v2 import Growth
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 begin=time.perf_counter();resource.setrlimit(resource.RLIMIT_CORE,(0,0));resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30));B=R/'experiments/mmc_existing_marginal_attachment_pilot_v1_2026-10-19';protocol=B/'protocol.json';p=json.loads(protocol.read_text());v=json.loads((B/'verification.json').read_text());assert v['status']=='EXISTING_REFERENCE_ACTUAL_GRAPH_REJECTION_PRESERVED';expected=json.loads((B/'result.json').read_text());O=R/'experiments/mmc_existing_marginal_attachment_cpp_confirmation_v1_2026-10-19';O.mkdir(exist_ok=False);contract=R/'experiments/marginal_tree_growth_cpp_contract_v2_2026-10-08/verification.json';c=json.loads(contract.read_text());binary=Path(next(n for n in c['bindings'] if n.endswith('.so')));assert sha(binary)==c['bindings'][str(binary)];wrapper=R/'tools/marginal_tree_growth_cpp_v2.py';assert sha(wrapper)==c['bindings'][str(wrapper)]
 for name,h in v['bindings'].items():assert sha(name)==h
 ep=next(Path(n) for n in p['bindings'] if n.endswith('/demand/endpoints.json'));meta=json.loads(ep.read_text());graph=Path(meta['inputs']['graph']['path']);tick=time.perf_counter();offsets,dest,costs,caps,kinds,_=load(graph);load_seconds=time.perf_counter()-tick;assert all(offsets[n]==offsets[n+1] for n,k in enumerate(kinds) if k=='SINK');assert all(kinds[n]!='SOURCE' for n in dest)
 fields={'row_offsets':offsets,'dest_ranks':dest,'capacities':caps,'edge_ids':range(len(dest))};tick=time.perf_counter();g=Growth(fields,costs,binary);g.prepare({},0);setup=time.perf_counter()-tick
 try:
  tick=time.perf_counter();actual=g.grow(p['source'],[q['sink'] for q in p['ordered_queries']],0,{int(n):b for n,b in p['budgets'].items()});seconds=time.perf_counter()-tick
 finally:g.close()
 assert actual==expected,(actual,expected)
 files=[protocol,B/'verification.json',B/'result.json',contract,binary,wrapper,Path(__file__).resolve()];(O/'verification.json').write_text(json.dumps({'status':'BOUND_CPP_AND_REFERENCE_SAME_FROZEN_ACTUAL_GRAPH_BUDGET_REJECTION','result':actual,'costs_seconds':{'graph_load':load_seconds,'cpp_workspace_and_prepare':setup,'grow':seconds,'total_before_receipt':time.perf_counter()-begin},'bindings':{str(f):sha(f) for f in files},'scope':'Two prior implementations agree on actual frozen NET5 rejection. No candidate paths emitted; no independent physical successful-tree certificate or constrained infeasibility proof. No native policy or predictor gain.'},indent=2)+'\n');print('CPP_CONFIRMATION_PASS',actual,flush=True)
if __name__=='__main__':main()
