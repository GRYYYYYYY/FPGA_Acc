"""Snapshot shape, graph topology, native pin criticality/slack aggregation; no new STA."""
import json,csv,hashlib,struct,math
from pathlib import Path
from collections import defaultdict,Counter,deque
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prospective_external_family_current_timing_graph_v1_2026-10-19';B=R/'build/native_external_current_timing_graph_v1_2026-10-19';BASE=E/'prospective_external_family_native_shared_sink_native_v1_2026-10-19'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def bits(x):return struct.pack('>f',float(x)).hex()
def main():
 terminal=read(D/'terminal.json');assert len(terminal['rows'])==3 and all(r['exit_code']==0 and r['marker'] and r['no_route_generated'] and r['initial_connection_bytes_equal'] for r in terminal['rows']);protocol=read(D/'protocol.json');assert all(sha(k)==h for k,h in protocol['bindings'].items());bindings={str(D/'terminal.json'):sha(D/'terminal.json'),str(D/'protocol.json'):sha(D/'protocol.json'),str(B/'sequence_vpr'):sha(B/'sequence_vpr'),str(Path(__file__).resolve()):sha(__file__)};rows=[]
 for row in terminal['rows']:
  case=row['case'];out=D/case;nodes={int(r['node']):int(r['type']) for r in csv.DictReader((out/'timing_nodes.tsv').open(),delimiter='\t')};edges=list(csv.DictReader((out/'timing_edges.tsv').open(),delimiter='\t'));ids={int(r['edge']) for r in edges};assert len(ids)==len(edges);incoming=Counter();following=defaultdict(list)
  for e in edges:
   u,v=int(e['source']),int(e['sink']);assert u in nodes and v in nodes
   assert all(math.isfinite(float(e[k])) for k in ['value_max_or_setup_s','value_min_or_hold_s'])
   if not int(e['disabled']):following[u].append(v);incoming[v]+=1
  queue=deque(n for n in nodes if incoming[n]==0);count=0
  while queue:
   n=queue.popleft();count+=1
   for v in following[n]:
    incoming[v]-=1
    if incoming[v]==0:queue.append(v)
  assert count==len(nodes)
  atoms=list(csv.DictReader((out/'timing_atoms.tsv').open(),delimiter='\t'));assert len({int(r['atom_pin']) for r in atoms})==len(atoms);grouped=defaultdict(list);nodegroups=defaultdict(set)
  for a in atoms:
   for field in ['external_node','internal_node']:
    if a[field]:assert int(a[field]) in nodes
   if a['raw_criticality']:
    key=(int(a['native_net']),int(a['local_pin']));assert key[1]>0;grouped[key].append(a);nodegroups[int(a['external_node'])].add(key)
  payload=E/'prospective_external_family_frame_timings_v1_2026-10-19'/case/'initial_connection_criticalities.json';original=read(payload);assert len(grouped)==len(original)==15616
  for r in original:
   gs=grouped[r['native_net_id'],r['local_sink_pin']];assert len(gs)==r['atom_count'];crit=max(float(a['raw_criticality']) for a in gs);slack=min(float(a['setup_slack_s']) for a in gs);assert bits(crit)==r['raw_criticality_bits'];assert bits(slack)==r['slack_bits']
  external_edges=[];covered=set();negative_offset=0;ambiguous=0;initial={(int(q['net']),int(q['pin'])):q for q in csv.DictReader((out/'initial_connections.tsv').open(),delimiter='\t')}
  for e in edges:
   if int(e['type'])!=3 or int(e['disabled']):continue
   keys=nodegroups.get(int(e['sink']),set())
   if len(keys)>1:ambiguous+=1
   for key in keys:
    covered.add(key);offset=float(e['value_max_or_setup_s'])-float(initial[key]['delay_s']);negative_offset+=offset<-1e-15;external_edges.append(dict(edge=int(e['edge']),native_net=key[0],local_pin=key[1],nominal_local_offset_s=offset))
  (out/'external_edge_candidates.json').write_text(json.dumps(external_edges)+'\n');rows.append(dict(case=case,timing_nodes=len(nodes),timing_edges=len(edges),edge_types=dict(Counter(int(e['type']) for e in edges)),disabled_edges=sum(int(e['disabled']) for e in edges),enabled_graph_acyclic=True,atom_pins=len(atoms),data_sink_atom_pins=sum(map(len,grouped.values())),all15616_raw_criticality_and_slack_aggregates_float32_equal=True,external_edge_candidates=len(external_edges),covered_native_connections=len(covered),ambiguous_external_destination_groups=ambiguous,negative_nominal_offset_candidates=negative_offset))
  for name in ['timing_nodes.tsv','timing_edges.tsv','timing_atoms.tsv','initial_connections.tsv','native.log','external_edge_candidates.json']:p=out/name;bindings[str(p)]=sha(p)
  bindings[str(payload)]=sha(payload);print(json.dumps(rows[-1]),flush=True)
 assert all(sha(k)==h for k,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(status='ALL3_CURRENT_TIMING_GRAPH_NATIVE_FLOAT32_PIN_BASELINES_VERIFIED',rows=rows,bindings=bindings,scope='Initial nominal packed mapping only. Typed clock-capture edges carry setup/hold constraints, not ordinary delay arcs. Native clock constraints raw log only, no validated machine-readable constraint import. External candidates are not yet source-pin/CID/offset-invariance certificates. No dynamic STA or feedback model acceptance.'),indent=2)+'\n')
if __name__=='__main__':main()
