"""Check serialized sink potential without shortest-path computation."""
import hashlib,json,struct
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/sb3_owner_search_suffix_certificate_20261015'
def main():
 audit=json.loads((P/'audit.json').read_text())
 for name,expected in audit['source_sha256'].items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==expected,name
 nodefile=next(Path(f) for f in audit['source_sha256'] if f.endswith('input.nodes'))
 edgefile=nodefile.with_suffix('.edges');nodes=list(struct.iter_unpack('<IHH',nodefile.read_bytes()));edges=list(struct.iter_unpack('<IHH',edgefile.read_bytes()))
 values=[v[0] for v in struct.iter_unpack('<Q',(P/'suffix.u64').read_bytes())];assert len(values)==len(nodes)
 def valid(potential):
  if potential[audit['sink']]!=0:return False
  for u,(start,count,_) in enumerate(nodes):
   for v,_,w in edges[start:start+count]:
    if potential[v]!=(1<<63) and potential[u]>w+potential[v]:return False
  return True
 assert valid(values)
 bad=list(values);bad[audit['sink']]=1;assert not valid(bad)
 u=next(u for u,(start,count,_) in enumerate(nodes) if u!=audit['sink'] and any(values[v]!=(1<<63) for v,_,w in edges[start:start+count]))
 bad=list(values);bad[u]=1<<63;assert not valid(bad)
 files=[P/'audit.json',P/'suffix.u64',nodefile,edgefile,Path(__file__).resolve()]
 report=dict(status='serialized_suffix_verified_without_shortest_path_and_two_corruptions_rejected',
  source_sha256={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},adopted=False,research_complete=False,
  scope='Serialized lower-bound proof only; supplemental reconstruction, not a retrospective identity check of prior in-memory potential.')
 with (P/'independent_audit.json').open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')
 print(report['status'])
if __name__=='__main__':main()
