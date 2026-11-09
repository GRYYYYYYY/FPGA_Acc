"""Review isolated CPU ordering arms and their independently replayed paths."""
import hashlib,json,struct
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/native_higher_g_tie_variant_20261015';B=R/'work/native_fullgraph_cpu_full_search_20261015';cache={}
def sha(q):
 q=str(Path(q).resolve())
 if q not in cache:
  h=hashlib.sha256()
  with Path(q).open('rb') as f:
   for b in iter(lambda:f.read(1048576),b''):h.update(b)
  cache[q]=h.hexdigest()
 return cache[q]
def load(q):return json.loads(Path(q).read_text())
def refs(x):
 for field in ['source_sha256','input_source_sha256']:
  for f,h in x.get(field,{}).items():assert sha(f)==h,f

def main():
 p=load(P/'protocol.json');m=load(P/'manifest.json');refs(p);refs(load(P/'launch_protocol.json'));refs(load(P/'review_protocol.json'));assert m['status']=='two_ordering_arms_terminal_requires_review'
 changed=[]
 for f in (P/'include').glob('*.hpp'):
  if sha(f)!=sha(B/'include'/f.name):changed.append(f.name)
 assert changed==['native_search_hbm_queue.hpp'] and sha(P/'oracle.cpp')==sha(B/'oracle.cpp')
 ready=load(P/'readiness.json');assert ready['weighted_search_checks_per_mode']==4000 and ready['enabled_ASAN_UBSAN_passed']
 for name in ['default','higher_g','sanitized']:assert 'weighted_search_checks=4000 reachable=2602' in (P/('check_'+name+'.stdout')).read_text()
 assert not (P/'check_sanitized.stderr').read_bytes()
 rows=[];parent=load(B/'protocol.json')['command']
 for arm,row in zip(p['arms'],m['arms']):
  assert row['label']==arm['label'] and row['returncode']==0 and row['command']==arm['command'];cmd=arm['command'];assert cmd[1:9]==parent[1:9] and cmd[10:]==parent[10:]
  d=P/arm['label'];a=d/'artifacts';result=struct.unpack('<8Q',(a/'result.raw').read_bytes());meta=struct.unpack('<8Q',(a/'metadata.raw').read_bytes());goal=struct.unpack('<8Q',(a/'goal.raw').read_bytes());assert result[0]==0 and result[1]<=2097152 and result[4:7]==meta[:3] and goal[1]==42
  nodes=[v[0] for v in struct.iter_unpack('<I',(a/'path_nodes.raw').read_bytes())];assert len(nodes)==len(set(nodes))==42 and nodes[-1]==goal[3]==int(cmd[6]);assert (a/'observations.raw').stat().st_size==result[5]*64
  q=load(a/'path_audit.json');assert q['status']=='passed' and q['cost']==42 and q['path_edges']==42 and q['observations']==result[5]
  snap=Path(cmd[1]);info=load(snap/'snapshot.json');control=struct.unpack('<8Q',(snap/'control.raw').read_bytes());net=struct.unpack_from('<8Q',(snap/'nets.raw').read_bytes(),int(cmd[5])*64);assert info['net_slot']==int(cmd[5]) and info['sink']==int(cmd[6]) and info['net_id']==net[1] and info['config'][0]==control[5]&0xffffffff
  if arm['label']=='default':
   c=load(d/'compatibility.json');assert len(c['artifacts'])==7 and c['artifacts']==p['expected_control_artifacts']
   for name,h in c['artifacts'].items():assert sha(a/name)==h
   sha(d/'compatibility.json')
  for f in [*a.glob('*.raw'),a/'path_audit.json',d/'stdout.log',d/'stderr.log',snap/'snapshot.json']:sha(f)
  rows.append(dict(arm=arm['label'],expanded=result[1],edge_visits=result[2],raw_arcs=result[3],observations=result[5],labels=result[6],path_edges=len(nodes),cost=goal[1]))
 assert len(rows)==2 and rows[0]['expanded']==229746 and rows[1]['expanded']==58069
 for f in [P/'protocol.json',P/'launch_protocol.json',P/'review_protocol.json',P/'manifest.json',P/'readiness.json',Path(__file__).resolve()]:sha(f)
 report=dict(status='two_CPU_orderings_reviewed_same_path_cost_with_less_search_work',outcomes=rows,modified_headers=changed,default_control_artifact_comparisons=7,path_nodes_identical=sha(P/'default/artifacts/path_nodes.raw')==sha(P/'higher_g/artifacts/path_nodes.raw'),source_sha256=cache,scope='One fixed original full graph/snapshot/source/sink/quotient/2M bound, two CPU ordering arms. All exported observations and selected paths independently replayed; default7artifacts reproduce parent. Small weighted graph and heap controls, enabled ASAN/UBSAN pass. Less search work is not CPU wall/FPGA speedup, global QoR, modified-path commit, or whole-design correctness. Exact-hop arms remain unimplemented; not adopted.',adopted=False,board_result=False,research_complete=False)
 with (P/'independent_audit.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'}))
if __name__=='__main__':main()
