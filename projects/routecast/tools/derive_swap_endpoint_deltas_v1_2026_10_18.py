"""Exact affected raw physical connections for outcome-blind development swaps."""
import json,collections
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
def main():
 base=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/rr/mmc';bp=base/'endpoints.json';mp=base/'mapping.json';ep=R/'experiments/prospective_layout_swap_endpoints_v2_2026-10-18/verification.json';sp=R/'experiments/prospective_layout_swap_real_MMC_v1_2026-10-18/verification.json';receipt=json.loads(ep.read_text());swaps=json.loads(sp.read_text());old=json.loads(bp.read_text());oldmap=json.loads(mp.read_text());bindings={str(p):sha(p) for p in [Path(__file__),R/'tools/pre_route_endpoints.py',bp,mp,ep,sp]}
 def reconstruct(endpoints,mapping):
  sources={};sinks=collections.defaultdict(list);order={};ignored={x['net_id'] for x in endpoints['excluded_nets']}
  for pin in mapping['pin_details']:
   nid=pin['net_id'];order.setdefault(nid,None)
   if pin['role']=='SOURCE':assert nid not in sources;sources[nid]=pin['rr_node']
   else:assert pin['role']=='SINK';sinks[nid].append(pin['rr_node'])
  expected=[]
  for nid in order:
   if nid in ignored:continue
   for sink in sinks[nid]:expected.append(dict(connection_id=len(expected),net_id=nid,source=sources[nid],sink=sink))
  assert expected==endpoints['connections']
 reconstruct(old,oldmap)
 out=R/'experiments/prospective_layout_swap_endpoint_deltas_v1_2026-10-18';out.mkdir(exist_ok=False);rows=[]
 for e,s in zip(receipt['episodes'],swaps['episodes']):
  assert e['episode']==s['episode'];p=Path(e['endpoints']);q=Path(e['mapping']);assert sha(p)==e['endpoints_sha256'] and sha(q)==e['mapping_sha256'];new=json.loads(p.read_text());mapping=json.loads(q.read_text());reconstruct(new,mapping);assert len(new['connections'])==len(old['connections'])==115973
  moved=set(s['changed_blocks']);changedpins=0
  assert len(oldmap['pin_details'])==len(mapping['pin_details'])
  for a,b in zip(oldmap['pin_details'],mapping['pin_details']):
   assert {k:v for k,v in a.items() if k!='rr_node'}=={k:v for k,v in b.items() if k!='rr_node'}
   changed=a['rr_node']!=b['rr_node'];assert changed==(a['block'] in moved);changedpins+=changed
  delta=[];kinds=collections.Counter();nets=set()
  for a,b in zip(old['connections'],new['connections']):
   assert a['connection_id']==b['connection_id'] and a['net_id']==b['net_id'];sc=a['source']!=b['source'];sk=a['sink']!=b['sink']
   if sc or sk:
    delta.append(dict(connection_id=a['connection_id'],net_id=a['net_id'],old_source=a['source'],old_sink=a['sink'],new_source=b['source'],new_sink=b['sink']));kinds['both' if sc and sk else 'source_only' if sc else 'sink_only']+=1;nets.add(a['net_id'])
  file=out/f'episode_{e["episode"]:02}_delta.json';file.write_text(json.dumps(delta,separators=(',',':')));rows.append(dict(episode=e['episode'],changed_blocks=sorted(moved),changed_physical_pins=changedpins,affected_connections=len(delta),affected_NETs=len(nets),change_kinds=dict(kinds),delta=str(file),delta_sha256=sha(file),unaffected_connections=len(old['connections'])-len(delta)))
  bindings[str(p)]=sha(p);bindings[str(q)]=sha(q)
 for p,h in bindings.items():assert sha(p)==h
 with (out/'verification.json').open('x') as f:json.dump(dict(status='all_three_exact_endpoint_deltas_reconstructed_from_physical_pin_records',bindings=bindings,episodes=rows,scope='Raw nonclock physical connection domain115973, before native ignored-NET filtering. All source and target connections independently reconstructed from per-pin source/sink lists; only moved blocks change pin RR IDs. Endpoint-affected NETs are not a bound on subsequent congestion-induced reroutes or whole-NET ownership changes. No routing, predictor or timing outcome.'),f,indent=2)
 print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
