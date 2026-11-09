"""Validated frozen nominal driver/sink components + variable RR float32 delays."""
import csv,math
from collections import defaultdict
from pathlib import Path
from native_setup_reference_constants_v2 import SetupReference,f32
class NominalComponentTimingBridge:
 def __init__(self,baseline_folder,component_file,mapping):
  self.folder=Path(baseline_folder);self.mapping={int(q['edge']):(int(q['native_net_id']),int(q['local_sink_pin'])) for q in mapping};self.required=set(self.mapping.values());self.parts={}
  if len(self.mapping)!=len(mapping):raise ValueError('duplicate external edge')
  data=defaultdict(dict)
  for q in csv.DictReader(Path(component_file).open(),delimiter='\t'):data[int(q['edge']),q['mode']][int(q['component'])]=q
  for edge,key in self.mapping.items():
   for mode in ('MAX','MIN'):
    rows=data[edge,mode]
    if set(rows)!={0,1,2} or rows[1]['type']!='inter-block routing':raise ValueError('external component shape')
    a,b=f32(rows[0]['delay_s']),f32(rows[2]['delay_s'])
    if not all(math.isfinite(v) and v>=0 for v in (a,b)):raise ValueError('invalid nominal component')
    self.parts[edge,mode]=a,b
 def edge_weights(self,RR,mode='MAX'):
  if mode not in ('MAX','MIN'):raise ValueError('unsupported delay mode')
  if set(RR)!=self.required:raise ValueError('complete identical native pin domain required')
  values={key:f32(v) for key,v in RR.items()}
  if any(not math.isfinite(v) or v<0 for v in values.values()):raise ValueError('invalid RR delay')
  return {edge:f32(f32(self.parts[edge,mode][0]+values[key])+self.parts[edge,mode][1]) for edge,key in self.mapping.items()}
 def analyze(self,RR):
  weights=self.edge_weights(RR);ref=SetupReference(self.folder);edges=[];incoming=defaultdict(list);outgoing=defaultdict(list)
  for edge in ref.edges:
   eid,u,v,kind,w=edge
   if eid in weights:
    if kind!=3:raise ValueError('mapped non-interconnect edge')
    w=weights[eid]
   updated=(eid,u,v,kind,w);edges.append(updated);incoming[v].append(updated);outgoing[u].append(updated)
  if not set(weights).issubset({e[0] for e in edges}):raise ValueError('mapped disabled/absent edge')
  ref.edges=edges;ref.ins=incoming;ref.outs=outgoing
  return ref.analyze()
