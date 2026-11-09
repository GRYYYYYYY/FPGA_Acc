"""Review remaining full-task static-hop/order arms and the complete 2x2 panel."""
import hashlib,json,struct
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/native_policy_identity_ordering_cpu_20261015';OLD=R/'work/native_higher_g_tie_variant_20261015';Q=R/'work/native_policy_identity_hop_bound_20261015';cache={}
def sha(f):
 f=str(Path(f).resolve())
 if f not in cache:
  h=hashlib.sha256()
  with Path(f).open('rb') as v:
   for b in iter(lambda:v.read(1048576),b''):h.update(b)
  cache[f]=h.hexdigest()
 return cache[f]
def load(f):return json.loads(Path(f).read_text())
def refs(x):
 for field in ['source_sha256','input_source_sha256','artifacts']:
  for f,h in x.get(field,{}).items():assert sha(f)==h,f

def main():
 p=load(P/'protocol.json');m=load(P/'manifest.json');refs(p);refs(load(P/'launch_protocol.json'));refs(load(P/'review_protocol.json'));prior=load(OLD/'independent_audit.json');refs(prior);bound=load(Q/'independent_audit.json');refs(bound)
 assert m['status']=='two_ordering_arms_terminal_requires_review' and bound['source_potential']==42 and bound['eligible_edges']==212892069
 old=load(OLD/'protocol.json');rows=[]
 for arm,row,parent in zip(p['arms'],m['arms'],old['arms']):
  assert row['label']==arm['label'] and row['returncode']==0 and row['command']==arm['command'];cmd=arm['command'];assert cmd[:9]==parent['command'][:9] and cmd[10]==str(Q/'identity_quotient')
  d=P/arm['label'];a=d/'artifacts';r=struct.unpack('<8Q',(a/'result.raw').read_bytes());meta=struct.unpack('<8Q',(a/'metadata.raw').read_bytes());g=struct.unpack('<8Q',(a/'goal.raw').read_bytes());assert r[0]==0 and r[1]<=2097152 and r[4:7]==meta[:3] and g[1]==42
  path=[v[0] for v in struct.iter_unpack('<I',(a/'path_nodes.raw').read_bytes())];assert len(path)==len(set(path))==42 and path[-1]==g[3]==int(cmd[6]);assert (a/'observations.raw').stat().st_size==r[5]*64
  check=load(a/'path_audit.json');assert check['status']=='passed' and check['cost']==42 and check['path_edges']==42 and check['observations']==r[5]
  net=struct.unpack_from('<8Q',(Path(cmd[1])/'nets.raw').read_bytes(),int(cmd[5])*64);seed=struct.unpack('<8Q',(Path(cmd[1])/'tree_seeds.raw').read_bytes());qp=load(Q/'protocol.json');assert net[1]==qp['net_id']==287909 and seed[1]==qp['source'] and int(cmd[6])==qp['sink']
  for f in [*a.glob('*.raw'),a/'path_audit.json',d/'stdout.log',d/'stderr.log']:sha(f)
  rows.append(dict(arm=arm['label'],expanded=r[1],edge_visits=r[2],observations=r[5],labels=r[6],path_edges=len(path),cost=g[1]))
 assert [v['expanded'] for v in rows]==[1907,43]
 panel=[dict(heuristic='coarse',order=v['arm'],expanded=v['expanded'],cost=v['cost']) for v in prior['outcomes']]+[dict(heuristic='policy_identity_hops',order=v['arm'].removeprefix('identity_'),expanded=v['expanded'],cost=v['cost']) for v in rows]
 for f in [P/'protocol.json',P/'launch_protocol.json',P/'manifest.json',P/'review_protocol.json',OLD/'independent_audit.json',Q/'independent_audit.json',Path(__file__).resolve()]:sha(f)
 report=dict(status='four_original_task_CPU_heuristic_order_arms_reviewed_same_cost42',outcomes=rows,panel=panel,minimum_cost_certificate='For this one seed/immutable policy graph: globally consistent hop bound at source42, valid edge cost>=1, and independently replayed found path cost42 certify minimum modeled cost42.',preprocessing_bytes=bound['serialized_bytes'],preprocessing_BFS_expanded=bound['preparation_BFS_expanded'],source_sha256=cache,scope='Same full original CSR, net policy, authority,source/sink and2M bounds; only priority tie order and static-hop grouping differ. Every exported observation and path independently replayed. Identity graph construction/BFS/verification/storage are substantial extra CPU work; fewer online expansions do not establish end-to-end or FPGA acceleration. No new-path commit, hardware, global QoR or adoption proof.',adopted=False,board_result=False,research_complete=False)
 with (P/'independent_audit.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'}))
if __name__=='__main__':main()
