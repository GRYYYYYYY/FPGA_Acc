"""Independent XML path recurrence and component assembly for round timing audit.

Reuses the qualified setup recurrence, never calls producer path/bridge adapters.
"""
import csv,json,struct
from collections import defaultdict
from pathlib import Path
from native_setup_reference_constants_v3 import SetupReference,f32
R=Path(__file__).resolve().parents[1];E=R/'experiments'
def bits(v):return struct.pack('>f',v).hex()
def audit(out,index,policy,records,ep,xml,classes,switches):
 case='/'.join(Path(ep).parts[-3:-1]);base=E/'wbuart_nominal_contexts_v1_2026-10-20'/case
 mapping=json.loads((E/'wbuart_nominal_contexts_v1_2026-10-20'/case/'external_edge_CID_bindings_v1.json').read_text());meta=json.loads((E/'wbuart_frame_timings_v1_2026-10-20'/case/'initial_connection_criticalities.json').read_text());meta={q['connection_id']:q for q in meta};assert set(meta)=={q['connection_id'] for q in records};assert all(r==c==0 for r,c in classes) and all(r==0 for r,t in switches.values())
 RR={}
 for rec in records:
  cid=rec['connection_id'];m=meta[cid];assert rec['full_connection_id']==m['full_connection_id'];assert (rec['net_id'],rec['source'],rec['sink'])==(m['endpoint_net_id'],m['source_rr'],m['target_rr']);u=rec['source'];delay=f32(0);seen={u}
  for eid in rec['answer']['physical_edge_ids']:
   e=xml.graph.edges[eid];assert e.source==u and e.sink not in seen;seen.add(e.sink);u=e.sink;delay=f32(delay+f32(float(switches[e.switch_id][1])))
  assert u==rec['sink'];RR[cid]=delay
 components=defaultdict(dict)
 for q in csv.DictReader((E/'wbuart_delay_components_v1_2026-10-20'/case/'scaled/components_before.tsv').open(),delimiter='\t'):
  if q['mode']=='MAX':components[int(q['edge'])][int(q['component'])]=f32(q['delay_s'])
 weights={q['edge']:f32(f32(components[q['edge']][0]+RR[q['connection_id']])+components[q['edge']][2]) for q in mapping};ref=SetupReference(base);ref.ins=defaultdict(list);ref.outs=defaultdict(list);edges=[]
 for eid,u,v,kind,w in ref.edges:
  e=eid,u,v,kind,weights.get(eid,w);edges.append(e);ref.ins[v].append(e);ref.outs[u].append(e)
 ref.edges=edges;result=ref.analyze();atoms=defaultdict(list)
 for a in csv.DictReader((base/'timing_atoms.tsv').open(),delimiter='\t'):
  if a['raw_criticality']:atoms[int(a['native_net']),int(a['local_pin'])].append(int(a['external_node']))
 saved=json.loads((out/f'timing_round{index}.json').read_text());assert saved['policy']==policy and saved['round_index']==index
 expected_source=out/('initial.json' if index==0 or policy=='warm_timing_frozen' else f'round{index-1}.json');assert Path(saved['source_state'])==expected_source
 rows={q['connection_id']:q for q in saved['criticalities']};assert set(rows)==set(meta)
 from fractions import Fraction
 criticalities={}
 for cid,m in meta.items():
  nodes=atoms[m['native_net_id'],m['local_sink_pin']];raw=max(result['criticality'][n] for n in nodes);slack=min(min(result['slacks'][n].values()) for n in nodes);maximum=f32(m['maximum_text']);assert float(m['exponent_text'])==1;production=min(maximum,f32(max(raw-(1.-maximum),0.)));q=rows[cid]
  assert q['criticality_bits']==bits(production) and q['raw_criticality_bits']==bits(raw) and q['slack_bits']==bits(slack)
  assert (q['criticality_numerator'],q['criticality_denominator'])==production.as_integer_ratio();assert (q['net'],q['source_rr'],q['target_rr'])==(m['endpoint_net_id'],m['source_rr'],m['target_rr']);criticalities[cid]=Fraction(*production.as_integer_ratio())
 return criticalities
