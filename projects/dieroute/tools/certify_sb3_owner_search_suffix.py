"""Persist a supplemental suffix potential and independently check its proof."""
import hashlib,heapq,json,struct
from pathlib import Path
R=Path(__file__).resolve().parents[1]
P=R/'work/sb3_owner_search_suffix_certificate_20261015'
def main():
 P.mkdir(exist_ok=False);refs={}
 def read(f):
  f=Path(f);data=f.read_bytes();refs[str(f)]=hashlib.sha256(data).hexdigest();return data
 prior=json.loads(read(R/'work/sb3_augmented_owner_search_potential_20261015/result.json'))
 protocol=json.loads(read(R/'work/sb3_fixed_feedback_pair_20261015/protocol.json'))
 case=next(c for c in protocol['cases'] if c['label']=='ex5p')
 nodes=list(struct.iter_unpack('<IHH',read(case['input_prefix']+'.nodes')))
 edges=list(struct.iter_unpack('<IHH',read(case['input_prefix']+'.edges')))
 for name in ['.nodes','.edges']:
  f=case['input_prefix']+name;assert refs[f]==prior['source_sha256'][f]
 reverse=[[] for _ in nodes]
 for u,(begin,count,_) in enumerate(nodes):
  for v,_,w in edges[begin:begin+count]:reverse[v].append((u,w))
 infinity=1<<63;distance=[infinity]*len(nodes);distance[14256]=0;pending=[(0,14256)]
 while pending:
  value,u=heapq.heappop(pending)
  if value!=distance[u]:continue
  for v,w in reverse[u]:
   if value+w<distance[v]:distance[v]=value+w;heapq.heappush(pending,(value+w,v))
 f=P/'suffix.u64';f.write_bytes(b''.join(struct.pack('<Q',v) for v in distance));read(f)
 # Reload only serialized bytes; edge inequalities + sink zero prove a lower bound.
 values=[v[0] for v in struct.iter_unpack('<Q',f.read_bytes())]
 assert values[14256]==0 and len(values)==len(nodes);checked=0
 for u,(begin,count,_) in enumerate(nodes):
  for v,_,w in edges[begin:begin+count]:
   if values[v]!=infinity:assert values[u]<=w+values[v];checked+=1
 assert checked==prior['suffix_edge_inequalities_checked']
 read(Path(__file__).resolve())
 audit=dict(status='serialized_suffix_lower_bound_checked_on_all_sink_reachable_edges',
  sink=14256,nodes=len(nodes),edge_inequalities=checked,source_lower_bound_ps=values[43804],
  source_sha256=refs,adopted=False,research_complete=False,
  scope='Supplemental serialized suffix reconstructed from identical graph. Sink0 and edge inequalities establish lower bound for every path to sink; does not retroactively bind prior in-memory array, prove whole-net repair, quality or performance.')
 (P/'audit.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps({k:v for k,v in audit.items() if k!='source_sha256'}))
if __name__=='__main__':main()
