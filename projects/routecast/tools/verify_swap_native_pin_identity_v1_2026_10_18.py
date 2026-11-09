"""Exact native/physical pin multiset and demand-partition verification."""
import sys,json,collections
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import placements,sha

def main():
 root=R/'experiments/prospective_layout_swap_native_partition_v1_2026-10-18';rp=root/'verification.json';r=json.loads(rp.read_text());mapping_root=R/'experiments/prospective_layout_swap_endpoints_v2_2026-10-18';out=R/'experiments/prospective_layout_swap_native_pin_identity_v1_2026-10-18';out.mkdir(exist_ok=False);bindings={str(p):sha(p) for p in [Path(__file__),R/'tools/pre_route_endpoints.py',rp]};rows=[]
 for e in r['episodes']:
  for path,h in e['files'].items():assert sha(path)==h
  d=root/f'episode_{e["episode"]:02}';mp=mapping_root/f'episode_{e["episode"]:02}/mapping.json';rawp=mapping_root/f'episode_{e["episode"]:02}/endpoints.json';mapping=json.loads(mp.read_text());raw=json.loads(rawp.read_text());pos=placements(d/'design.place',sha(d/'design.net'));records=[json.loads(line) for line in (d/'identity.jsonl').read_text().splitlines()];native={t['name']:t for t in records};assert len(native)==len(records)
  actual=collections.Counter((t['name'],p['block'],p['port'],p['bit'],p['physical_pin'],p['class'],p['x'],p['y'],p['layer'],'SOURCE' if p['index']==0 else 'SINK') for t in records for p in t['pins'])
  expected=collections.Counter((p['net'],p['block'],p['port'],p['bit'],p['physical_pin_ptc'],p['class_id'],pos[p['block']][0],pos[p['block']][1],pos[p['block']][3],p['role']) for p in mapping['pin_details'])
  assert actual==expected,(e['episode'],sum((actual-expected).values()),sum((expected-actual).values()))
  filtered=json.loads((d/'endpoints.json').read_text());partition=json.loads((d/'partition.json').read_text());wanted=[];ignored=[];translation=[]
  for c in raw['connections']:
   name=raw['net_names'][str(c['net_id'])];entry=native[name];assert type(entry['ignored']) is bool
   if entry['ignored']:ignored.append(c['connection_id'])
   else:translation.append(c['connection_id']);wanted.append(dict(c,connection_id=len(wanted)))
  assert filtered['connections']==wanted and partition['physical_to_original_connection_ids']==translation and partition['ignored_original_connection_ids']==ignored
  assert len(set(translation+ignored))==len(raw['connections']) and set(translation).isdisjoint(ignored)
  for p in [mp,rawp,d/'identity.jsonl',d/'endpoints.json',d/'partition.json',d/'design.place',d/'design.net']:bindings[str(p)]=sha(p)
  rows.append(dict(episode=e['episode'],all_native_and_packed_physical_pins=sum(actual.values()),extra_pins=0,missing_pins=0,source_sink_roles_equal=True,physical_connections=len(wanted),ignored_connections=len(ignored),complete_partition_verified=True))
 for path,h in bindings.items():assert sha(path)==h
 with (out/'verification.json').open('x') as f:json.dump(dict(status='all_three_complete_native_physical_pin_multisets_and_partitions_match',bindings=bindings,episodes=rows,scope='Native identity table pins versus packed/RR-derived pins including root clocks, source/sink role, physical pin/class and placed coordinates, exact multiplicities. Full raw-to-native demand partition checked. This strengthens physical input identity only; no native RR consistency run, route existence, timing, forecasting quality or complete-time utility certificate.'),f,indent=2)
 print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
