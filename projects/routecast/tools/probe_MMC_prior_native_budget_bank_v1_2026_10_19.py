"""Frozen prior-native actual-RC budgets; isolated and full-prior residual banks."""
import json,pathlib,hashlib,itertools
from collections import Counter,defaultdict
from MMC_zero_node_RC_shared_CSR_v1 import load
from coupled_NET_tree_candidates_csr_v2 import CSRIndex,tree_candidate,select
R=pathlib.Path(__file__).resolve().parents[1];O=R/'experiments/mmc_prior_native_budget_bank_v1_2026-10-19'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def main():
 O.mkdir(exist_ok=False);S=R/'experiments/mmc_native_source_checkpoint_v1_2026-10-18';A=R/'experiments/mmc_complete_tree_bank_csr_v2_2026-10-19';B=R/'experiments/mmc_residual_capacity_group_v1_2026-10-19';source=S/'initial.json';sp=S/'independent_xml_verification_v1.json';sv=json.loads(sp.read_text());assert sv['all_paths_original_XML_fraction_RC_budget_singleparent_and_uniqueNET_pass'] and not sv['original_zero_counter_gate'];assert sv['bindings'][str(source)]==sha(source);frame=json.loads(source.read_text());target=R/'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19/episode_01/demand/endpoints.json';ep=json.loads(target.read_text());new={q['connection_id']:q for q in ep['connections']};nets=[1395,1400,1404,1754,2925];records=defaultdict(list)
 for row in frame['records']:
  if row['net_id'] in nets:
   assert all(new[row['connection_id']][k]==row[k] for k in ['net_id','source','sink']);records[row['net_id']].append(row)
 graph=pathlib.Path(ep['inputs']['graph']['path']);assert sha(graph)==ep['graph_sha256'];proofs=[sp,A/'independent_XML_verification_v1.json',B/'independent_verification_v1.json'];bindings={str(p):sha(p) for p in [source,target,graph,pathlib.Path(__file__).resolve(),R/'tools/coupled_NET_tree_candidates_csr_v2.py',R/'tools/coupled_NET_tree_candidates_v1.py']+proofs}
 for net in nets:
  for p in [A/f'net_{net}_original.json',A/f'net_{net}_blocked.json',B/f'net_{net}_tree.json']:bindings[str(p)]=sha(p)
 write(O/'protocol.json',dict(bindings=bindings,NETs=nets,prior_budget_policy='Each unchanged connection upper bound is its exact certified pre-existing native path additive RC; no multiplier, no future labels. Preserve old failed diagnostic budgets as separate evidence.',candidate_origins=['original_lex_first','node646275_deleted_lex_first','fixed_order_residual','prior_native_actual_tree'],contexts=['isolated zero external occupancy','full prior native occupancy excluding exactly these five NETs'],scope='Five unchanged NET endpoint sets only. Full-prior context retains old-source routes of other NETs, so it is not a complete new-placement route. Native canonical semantic acceptance has330 ignored-pin fixups; original zero-counter gate remains false.'))
 offsets,dest,cost,caps,kinds,_=load(graph);index=CSRIndex(offsets,dest,cost,caps,kinds);banks={};accepted_origin={};native={};external=Counter({int(v):n for v,n in frame['ledger'].items()});rows=[];all_refs={}
 for net in nets:
  base=json.loads((A/f'net_{net}_original.json').read_text());floor={int(s):v for s,v in base['sink_floors'].items()};budget={r['sink']:r['answer']['delay'] for r in records[net]};assert len(budget)==len(records[net]) and set(budget)==set(floor);paths={r['sink']:r['answer']['physical_edge_ids'] for r in records[net]};c=tree_candidate(index,base['source'],paths,floor,budget);assert all(c['sink_costs'][s]==budget[s] for s in budget);native[net]=c;external.subtract(c['nodes']);np=O/f'net_{net}_prior_native.json';write(np,dict(net_id=net,source=base['source'],paths=paths,unique_nodes=sorted(c['nodes']),sink_costs=c['sink_costs'],sink_floors=floor,sink_budgets=budget,excess=c['excess'],connection_ids=sorted(r['connection_id'] for r in records[net])))
  refs=[A/f'net_{net}_original.json',A/f'net_{net}_blocked.json',B/f'net_{net}_tree.json',np];banks[net]=[];accepted_origin[net]=[];all_refs[net]=[str(p) for p in refs];bad_by_origin=[]
  for origin,p in enumerate(refs):
   x=json.loads(p.read_text());route={int(s):v for s,v in x['paths'].items()};costs=x.get('sink_costs') or {s:l[0] for s,l in x['sink_labels'].items()};bad=sum(v>budget[int(s)] for s,v in costs.items());bad_by_origin.append(bad)
   if bad:continue
   admitted=tree_candidate(index,base['source'],route,floor,budget);banks[net].append(admitted);accepted_origin[net].append(origin)
  rows.append(dict(net_id=net,connections=len(records[net]),prior_native_excess=c['excess'],prior_budget_violations_by_origin=bad_by_origin,accepted_origins=accepted_origin[net]));print(rows[-1],flush=True)
 assert all(0<=n<=caps[v] for v,n in external.items());fixed={v:n for v,n in external.items() if n};write(O/'fixed_prior_other_NET_occupancy.json',fixed);results={}
 for context,occupancy in [('isolated',{}),('full_prior',fixed)]:
  answer=select(banks,index.capacities,occupancy,max_states=100000);assert answer['status']=='OPTIMAL_WITHIN_CANDIDATES';answer['selected_origins']={n:accepted_origin[n][ci] for n,ci in answer['selection'].items()};results[context]=answer;print(context,answer,flush=True)
 write(O/'results.json',dict(status='FROZEN_PRIOR_NATIVE_BUDGET_BANK_SELECTION_PRODUCED',rows=rows,references=all_refs,contexts=results,prior_native_total_excess=sum(c['excess'] for c in native.values()),independent_verification_pending=True))
if __name__=='__main__':main()
