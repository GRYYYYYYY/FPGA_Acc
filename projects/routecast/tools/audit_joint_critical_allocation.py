import json,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter,defaultdict
from pre_route_endpoints import sha
from prepared_csr import read
root=Path(__file__).resolve().parents[1];base=root/'experiments';parent=base/'native_baseline_critical_move_release_rc_2026-10-06';verified=json.loads((parent/'verification.json').read_text());assert sha(parent/'results.json')==verified['results_sha256'];queries=json.loads((parent/'results.json').read_text())['results'];ctx_path=base/'native_other_net_contexts_2026-10-06/adder_0.json';ctx=json.loads(ctx_path.read_text());release_path=base/'native_move_release_contexts_2026-10-06/adder_0.json';release=json.loads(release_path.read_text());assert release['source_context_sha256']==sha(ctx_path);by_name={name:int(n) for n,name in ctx['net_names'].items()};original={int(n):set(v) for n,v in ctx['own_net_nodes'].items()};graph=next(p for p in ctx['inputs_sha256'] if p.endswith('.route'));protocol=json.loads((parent/'protocol.json').read_text());m,f=read(base/'adder_tree_family_length_switch_csr_2026-10-06/adder_tree_2L_032bits/csr',protocol['graph_sha256']);arcs={f['edge_ids'][i]:(u,f['dest_ranks'][i]) for u in range(m['nodes']) for i in range(f['row_offsets'][u],f['row_offsets'][u+1])};table=next(Path(p) for p in ctx['inputs_sha256'] if p.endswith('.tsv') and not p.endswith('resources.tsv'));pin_counts=Counter(int(line.split('\t')[0]) for line in table.read_text().splitlines()[2:]);out=base/'native_joint_critical_allocation_2026-10-06';out.mkdir(exist_ok=True);results=[]
original_graph=root/'work/adder_tree_family_native_capture_v2_2026-10-06/adder_tree_2L_032bits/rr_graph.xml';assert sha(original_graph)==protocol['graph_sha256'];stack=[];checked=0
for event,e in ET.iterparse(original_graph,events=('start','end')):
 if event=='start':stack.append(e);continue
 xml_parent=stack[-2].tag if len(stack)>1 else None
 if e.tag=='node' and xml_parent=='rr_nodes':assert int(e.get('capacity'))==f['capacities'][int(e.get('id'))];checked+=1
 if (e.tag,xml_parent) in (('node','rr_nodes'),('edge','rr_edges'),('switch','switches')):stack[-2].remove(e);e.clear()
 stack.pop()
assert checked==m['nodes']
for i,move in enumerate(release['moves']):
 selected=[q for q in queries if q['pair_index']==i];assert len(selected)==6;unions=defaultdict(set);branch_count=Counter()
 for q in selected:
  net=by_name[q['net_name']];branch_count[net]+=1;node=q['source'];unions[net].add(node)
  for eid in q['result']['physical_edge_ids']:
   u,v=arcs[eid];assert u==node;node=v;unions[net].add(node)
  assert node==q['sink']
 ledger=Counter({int(n):v for n,v in move['other_demand'].items()});dirty=set(move['dirty_native_nets'])
 for net,used in unions.items():
  if net not in dirty:
   for node in original[net]:assert ledger[node]>=1;ledger[node]-=1
   used.update(original[net])
  ledger.update(used)
 assert all(v>=0 for v in ledger.values());violations={n:v-f['capacities'][n] for n,v in ledger.items() if v>f['capacities'][n]};missing=sum(pin_counts[net]-branch_count[net] for net in dirty);assert missing>=0
 results.append({'pair_index':i,'pair':move['pair'],'predicted_nets':len(unions),'dirty_nets':len(dirty),'missing_dirty_connections':missing,'partial_overflow_units':sum(violations.values()),'overused_nodes':violations,'status':'PARTIAL_ONLY_NOT_PUBLISHABLE','scope':'Released occupancy plus queried critical NET unions; old full union retained for queried unchanged NETs. Dirty noncritical branches absent, so zero overflow is not full legality.'})
(out/'receipt.json').write_text(json.dumps({'pairs':results,'input_sha256':{str(p):sha(p) for p in (parent/'results.json',ctx_path,release_path,table)},'graph_sha256':protocol['graph_sha256'],'overflow_pairs':sum(x['partial_overflow_units']>0 for x in results),'incomplete_pairs':sum(x['missing_dirty_connections']>0 for x in results),'source_sha256':sha(Path(__file__))},indent=2)+'\n');print('partial overflow pairs',sum(x['partial_overflow_units']>0 for x in results),'incomplete pairs',sum(x['missing_dirty_connections']>0 for x in results))
