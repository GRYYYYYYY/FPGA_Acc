import json,time
from pathlib import Path
from fractions import Fraction
from collections import Counter,defaultdict
from pre_route_endpoints import sha
from prepared_csr import read
from csr_exact_buffered_rc import ExactBufferedRC
from buffered_rc_context import load as load_rc
from prepared_integer_rc_context import PreparedIntegerRC
from native_integer_rc_search import NativeIntegerRC
root=Path(__file__).resolve().parents[1];base=root/'experiments';cohort_path=base/'native_complete_move_queries_2026-10-06/adder_0.json';cohort=json.loads(cohort_path.read_text());assert all(sha(p)==h for p,h in cohort['inputs_sha256'].items());release_path=base/'native_move_release_contexts_2026-10-06/adder_0.json';release=json.loads(release_path.read_text());out=base/'native_complete_joint_rc_2026-10-06';out.mkdir();graph=next(p for p in cohort['inputs_sha256'] if p.endswith('rr_graph.xml'));digest=sha(graph);m,f=read(base/'adder_tree_family_length_switch_csr_2026-10-06/adder_tree_2L_032bits/csr',digest);rc=PreparedIntegerRC(ExactBufferedRC(f,*load_rc(base/'adder_tree_family_exact_buffered_rc_classes_2026-10-06/adder_tree_2L_032bits',digest)),base/'adder_tree_prepared_integer_rc_2026-10-06','7f8ce091f40c8f7f0f879a068293f20c76be9ebbbb3c0371462eca0f0724e617');native=NativeIntegerRC(rc);budget=(Fraction(1,10**9)*rc.scale).__floor__();slots={f['edge_ids'][i]:(u,f['dest_ranks'][i]) for u in range(m['nodes']) for i in range(f['row_offsets'][u],f['row_offsets'][u+1])};protocol={'cohort_sha256':sha(cohort_path),'release_sha256':sha(release_path),'graph_sha256':digest,'budget_integer':budget,'integer_scale':rc.scale,'max_labels':10000,'order':'Native NET id then pin index; no outcome-dependent ordering','scope':'Complete dirty NET connections, sequential cost-weighted soft demand; fixed isolated 1ns branch allowance, no full STA guarantee.'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');results=[];start=time.perf_counter()
for move in cohort['moves']:
 r=release['moves'][move['pair_index']];assert r['pair']==move['pair'];ledger=Counter({int(n):v for n,v in r['other_demand'].items()});unions=defaultdict(set);arcs=defaultdict(set);records=[];failure=None
 for q in sorted(move['queries'],key=lambda q:(q['net_id'],q['pin_index'])):
  net=q['net_id'];other=Counter(ledger)
  for node in unions[net]:assert other[node]>=1;other[node]-=1
  native.set_other(dict(+other));answer=native.query(q['source'],q['sink'],budget,max_labels=10000);records.append({**q,'result':answer})
  if answer['status']!='FOUND':failure=answer['status'];break
  used={q['source']};node=q['source']
  for eid in answer['physical_edge_ids']:
   u,v=slots[eid];assert u==node;node=v;used.add(node);arcs[net].add((u,v,eid))
  assert node==q['sink'];new=used-unions[net];ledger.update(new);unions[net].update(used)
 overflow={n:v-f['capacities'][n] for n,v in ledger.items() if v>f['capacities'][n]};bad_parents=[]
 for net,edges in arcs.items():
  parents=defaultdict(set)
  for u,v,e in edges:parents[v].add((u,e))
  bad_parents.extend({'net_id':net,'node':n,'parents':len(p)} for n,p in parents.items() if len(p)>1)
 result={'pair_index':move['pair_index'],'pair':move['pair'],'required_connections':len(move['queries']),'completed_connections':sum(x['result']['status']=='FOUND' for x in records),'failure':failure,'overflow_units':sum(overflow.values()),'overflow_nodes':overflow,'multi_parent_nodes':bad_parents,'records':records,'status':'DIAGNOSTIC_NOT_PUBLISHABLE'};file=out/f"pair_{move['pair_index']}.json";file.write_text(json.dumps(result,indent=2)+'\n');results.append({k:v for k,v in result.items() if k not in ('records','overflow_nodes','multi_parent_nodes')});results[-1]['multi_parent_count']=len(bad_parents);results[-1]['sha256']=sha(file);print(move['pair_index'],result['completed_connections'],result['overflow_units'],len(bad_parents),failure,flush=True)
(out/'receipt.json').write_text(json.dumps({'results':results,'wall_s':time.perf_counter()-start,'protocol_sha256':sha(out/'protocol.json'),'source_sha256':sha(Path(__file__))},indent=2)+'\n')
