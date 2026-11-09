"""Fixed-packing timing feedback from complete physical CID edge paths.

Caller supplies a certified zero-RC graph. No dynamic packed pin remap is modeled.
"""
import csv,struct
from collections import defaultdict
from nominal_component_timing_bridge_v1 import NominalComponentTimingBridge
from zero_rc_native_float_delay_v1 import switch_path_delay,f32

def word(v):return struct.pack('>f',v).hex()
class FixedNominalTimingFeedback:
 def __init__(self,baseline,components,mapping,atoms,initial_rows,graph):
  self.bridge=NominalComponentTimingBridge(baseline,components,mapping);self.g=graph;self.meta={r['connection_id']:dict(r) for r in initial_rows};self.binding={}
  for row in mapping:
   cid=row['connection_id'];key=row['native_net_id'],row['local_sink_pin']
   if cid in self.binding and self.binding[cid]!=key:raise ValueError('ambiguous native pin')
   self.binding[cid]=key
   m=self.meta[cid]
   if (m['native_net_id'],m['local_sink_pin'],m['source_rr'],m['target_rr'])!=(*key,row['source_rr'],row['target_rr']):raise ValueError('mapping identity')
  if set(self.binding)!=set(self.meta):raise ValueError('incomplete CID mapping')
  self.atoms=defaultdict(list)
  for a in csv.DictReader(open(atoms),delimiter='\t'):
   if a['raw_criticality']:self.atoms[int(a['native_net']),int(a['local_pin'])].append(int(a['external_node']))
  if set(self.atoms)!=self.bridge.required:raise ValueError('atom aggregation domain')
  self.switch_delays={s:f32(w/1e18) for s,w in graph['weights'].items()}
  if any(float(r['exponent_text'])!=1 for r in initial_rows):raise ValueError('only verified exponent1 supported')
 def analyze_rr(self,RR):
  analysis=self.bridge.analyze(RR);rows={}
  for cid,key in self.binding.items():
   raw=max(analysis['criticality'][n] for n in self.atoms[key]);slack=min(min(analysis['slacks'][n].values()) for n in self.atoms[key]);old=self.meta[cid];maximum=f32(old['maximum_text']);value=min(maximum,f32(max(float(raw)-(1.0-maximum),0.0)));num,den=value.as_integer_ratio()
   rows[cid]=dict(old,net=old['endpoint_net_id'],criticality_float32_text=format(value,'.9g'),criticality_bits=word(value),raw_criticality_bits=word(raw),slack_bits=word(slack),criticality_numerator=num,criticality_denominator=den)
  return rows
 def from_records(self,records):
  RR={};seen=set();g=self.g
  for r in records:
   cid=r['connection_id']
   if cid in seen or cid not in self.meta:raise ValueError('duplicate/unknown CID')
   seen.add(cid);m=self.meta[cid]
   if (r['net_id'],r['source'],r['sink'])!=(m['endpoint_net_id'],m['source_rr'],m['target_rr']):raise ValueError('record identity')
   current=r['source'];switches=[];visited={current}
   for e in r['answer']['physical_edge_ids']:
    if type(e) is not int or not 0<=e<len(g['us']) or g['us'][e]!=current:raise ValueError('invalid physical arc chain')
    current=g['vs'][e]
    if current in visited:raise ValueError('cyclic path')
    visited.add(current);switches.append(g['switches'][e])
   if current!=r['sink']:raise ValueError('incomplete path')
   RR[self.binding[cid]]=switch_path_delay(switches,self.switch_delays)
  if seen!=set(self.meta):raise ValueError('incomplete record cohort')
  return self.analyze_rr(RR)
