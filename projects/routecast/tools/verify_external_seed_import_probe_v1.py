"""Compare actual native imported tree/pin/occupancy against static seed witnesses."""
import json,sys
from pathlib import Path
from collections import defaultdict,Counter
sys.path[:0]=[str(Path(__file__).resolve().parent),str(Path(__file__).resolve().parent/'native_resume_prototype')]
from pre_route_endpoints import sha
from zero_rc_budget_certificate_graph_v1 import load_graph
R=Path(__file__).resolve().parents[1];E=R/'experiments';I=E/'prospective_external_family_native_utility_seed_inputs_v1_2026-10-19';D=E/'prospective_external_family_seed_import_probe_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 terminal=read(D/'terminal.json');assert len(terminal['rows'])==3 and all(sha(p)==h for p,h in terminal['bindings'].items());static=read(I/'independent_verification_v1.json');assert all(sha(p)==h for p,h in static['bindings'].items());cases=read(I/'protocol.json')['cases'];g=load_graph(cases[0]['graph']);rows=[];bindings={str(D/'terminal.json'):sha(D/'terminal.json'),str(I/'independent_verification_v1.json'):sha(I/'independent_verification_v1.json'),str(Path(__file__).resolve()):sha(__file__)}
 for c,r in zip(cases,terminal['rows']):
  assert c['case']==r['case'];out=D/c['case'];assert all(sha(p)==h for p,h in r['files'].items());bindings[str(out/'receipt.json')]=sha(out/'receipt.json');result=dict(case=c['case'],process_exit=r['exit_status'],native_import_admitted=False)
  if r['exit_status']!=0 or not r['import_probe_marker_present']:
   result['reason']='Native read_route/probe failed; preserve full cohort';result['log_tail']=(out/'native.log').read_text().splitlines()[-12:];rows.append(result);continue
  assert not r['router_search_completed'] and not (out/'output.route').exists();subset=read(I/c['case']/'subset.json');pins=read(I/c['case']/'pin_bindings.json');expected_trees=defaultdict(set);expected_pins={};sources={}
  for q in subset['records']:
   bind=pins[str(q['connection_id'])];net=bind['net'];sources[net]=q['source'];expected_pins[net,bind['pin']]=q['sink'];expected_trees[net].add(q['source'])
   for e in q['answer']['physical_edge_ids']:expected_trees[net].add(g['vs'][e])
  trees={};nodes=defaultdict(list);observed_pins={};occupancy={};footer=None
  for line in (out/'native_import.tsv').open():
   x=line.split();tag=x[0]
   if tag=='T':n=int(x[1]);assert n not in trees;trees[n]=tuple(map(int,x[2:]))
   elif tag=='P':key=(int(x[1]),int(x[2]));assert key not in observed_pins;observed_pins[key]=int(x[3])
   elif tag=='N':nodes[int(x[1])].append(int(x[2]))
   elif tag=='O':n,occ,cap=map(int,x[1:]);assert n not in occupancy and cap==g['caps'][n] and occ>=0;occupancy[n]=occ
   elif tag=='F':assert footer is None;footer=tuple(map(int,x[1:]))
   else:assert tag=='H' and x[1]=='1'
  present={n for n,(ignored,has_tree,source,root) in trees.items() if has_tree};assert present==expected_trees.keys() and observed_pins==expected_pins
  for n,expected in expected_trees.items():
   ignored,has_tree,source,root=trees[n];assert ignored==0 and has_tree==1 and source==root==sources[n];assert set(nodes[n])==expected
  assert set(occupancy)==set(range(len(g['caps'])));ledger=Counter(n for ns in expected_trees.values() for n in ns);residual={n:occupancy[n]-ledger[n] for n in occupancy if occupancy[n]!=ledger[n]};overflow=sum(max(0,occ-g['caps'][n]) for n,occ in occupancy.items());assert footer==(len(expected_trees),len(expected_pins),15616);result.update(native_import_admitted=True,selected_native_NETs=len(present),selected_native_sink_pins=len(observed_pins),all_required_data_connections=footer[2],omitted_connections_still_required=15616-len(observed_pins),tree_support_exact=True,native_occupancy_residual_nodes=len(residual),native_overflow_units=overflow,scope='Actual read_route/current native pin/selected tree import only, no FULL/canonical/STA or routing utility; residual occupancy and overflow not silently discarded.');rows.append(result)
  for p in [out/'native_import.tsv',I/c['case']/'subset.json',I/c['case']/'pin_bindings.json']:bindings[str(p)]=sha(p)
 assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(status='ALL3_IMPORT_ONLY_NATIVE_OUTCOMES_INDEPENDENTLY_CHECKED',rows=rows,all3_import_admitted=all(r['native_import_admitted'] for r in rows),bindings=bindings,scope='Full cohort incl failures. Native import is not full route/canonical/STA/nonconfigurable final acceptance. Every omitted demand remains required.'),indent=2)+'\n');print(json.dumps(rows))
if __name__=='__main__':main()
