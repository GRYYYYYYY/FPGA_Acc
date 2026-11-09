"""Compare mapped STA external increments with exact buffered RR path estimate."""
import json,re,time
from pathlib import Path
from native_route_ledger_import import physical_paths
from nonzero_rc_endpoint_context import load_endpoints
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_sta_rc_alignment_2026-10-06';out.mkdir();mapping=ROOT/'experiments/mux_timing_net_mapping_v2_2026-10-06';verified=json.loads((mapping/'verification.json').read_text());assert verified['receipt_sha256']==sha(mapping/'receipt.json');bindings={str(mapping/'verification.json'):sha(mapping/'verification.json')};rows=[]
for width in (8,16,32):
 ep=ROOT/f'experiments/mux_live_placement_updates_2026-10-06/w{width}/original_endpoints.json';graph,digest,nodes,f,rc,queries=load_endpoints(ep);edges={}
 for u in range(len(nodes)):
  for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
   key=(u,f['dest_ranks'][slot],f['switch_ids'][slot]);assert key not in edges;edges[key]=f['edge_ids'][slot]
 for mode in ('candidate','reference'):
  work=ROOT/(f'experiments/mux_candidate_timing_reports_v2_2026-10-06/w{width}/canonical'if mode=='candidate'else f'experiments/mux_budget_repair_quality_gate_2026-10-06/w{width}/canonical');route=work/'design.route';mp=mapping/f'w{width}_{mode}.json';data=json.loads(mp.read_text());bindings[str(route)]=sha(route);bindings[str(mp)]=sha(mp);branches=physical_paths(route);terminal_pins={};name=None
  for line in route.read_text().splitlines():
   m=re.match(r'^Net\s+\d+\s+\((.*?)\)',line)
   if m:name=m[1];terminal_pins[name]=[]
   if re.search(r'Node:\s*\d+\s+SINK\b',line):terminal_pins[name].append(int(re.search(r'Net_pin_index:\s*(\d+)',line)[1]))
  values={}
  for name,paths in branches.items():
   assert len(paths)==len(terminal_pins[name])
   for pin,path in zip(terminal_pins[name],paths):
    assert (name,pin)not in values;source=path[0][0];eid=[];current=source
    for node,switch in path[1:]:eid.append(edges[current,node,switch]);current=node
    values[name,pin]=float(rc.path(source,current,eid)*10**9/rc.scale)
  samples=[]
  for path in data['paths']:
   for segment in path['segments']:
    if segment['internal']:continue
    rr=values[segment['atom_net'],segment['native']['sink_pin_index']];sta=segment['increment_ns'];samples.append(dict(rank=path['rank'],atom_net=segment['atom_net'],sink_atom=segment['sink_atom'],sink_pin_index=segment['native']['sink_pin_index'],rr_path_ns=rr,sta_increment_ns=sta,residual_ns=sta-rr))
  file=out/f'w{width}_{mode}.json';file.write_text(json.dumps(samples,indent=2)+'\n');res=[s['residual_ns']for s in samples];rows.append(dict(width=width,mode=mode,samples=len(samples),negative_residuals=sum(x<-.001 for x in res),minimum_residual_ns=min(res),maximum_residual_ns=max(res),mean_residual_ns=sum(res)/len(res),samples_sha256=sha(file)))
 bindings[str(ep)]=sha(ep);bindings[str(graph)]=digest
(out/'receipt.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),bindings=bindings,rows=rows,scope='RR path includes source halfRC plus buffered-switch/node increments only; STA atom-to-atom segment includes intra-cluster propagation, pin choices, and native tree behavior. Residual is not pure wire error or causality. 0.001ns report precision, repeated path observations retained.'),indent=2)+'\n');print(rows)
