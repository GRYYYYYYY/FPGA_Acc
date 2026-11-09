"""Matched frozen first-candidate root behavior, not timing or quality evidence."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
parents=[R/f'experiments/misex_net466_extra_owner_joint_v{v}_2026-10-07' for v in (9,10)];bindings={str(Path(__file__).resolve()):sha(__file__)};roots=[]
for p in parents:
 rp=p/'receipt.json';r=json.loads(rp.read_text());bindings[str(rp)]=sha(rp);ep=p/'event.json';bindings[str(ep)]=sha(ep);cp=p/'candidates.json';bindings[str(cp)]=sha(cp)
 assert r['files'][str(ep)]==sha(ep) and r['files'][str(cp)]==sha(cp)
 directory=p/'attempt0_branch0';bp=directory/'branch.json';b=json.loads(bp.read_text());assert r['files'][str(bp)]==sha(bp) and b['branch']['constraints']==[];bindings[str(bp)]=sha(bp);states={}
 for f in directory.glob('net*.json'):
  assert r['files'][str(f)]==sha(f);bindings[str(f)]=sha(f);states[f.name]=json.loads(f.read_text())
 roots.append(dict(event=json.loads(ep.read_text()),candidate=json.loads(cp.read_text())[0],meta=b,states=states))
a,b=roots;assert a['event']==b['event'] and a['candidate']==b['candidate'] and a['states'].keys()==b['states'].keys();rows=[]
for name in sorted(a['states']):
 x,y=a['states'][name],b['states'][name];xr={r['connection_id']:r for r in x['records']};yr={r['connection_id']:r for r in y['records']};common=xr.keys()&yr.keys();changed=[cid for cid in common if xr[cid]['answer']['physical_edge_ids']!=yr[cid]['answer']['physical_edge_ids']];rows.append(dict(net_file=name,changed_path_ids=sorted(changed),only_old=sorted(xr.keys()-yr.keys()),only_new=sorted(yr.keys()-xr.keys()),old_failure=x['failure'],new_failure=y['failure']))
assert all(sha(k)==v for k,v in bindings.items());out=R/'experiments/misex_net466_zero_penalty_root_comparison_v1_2026-10-07';out.mkdir();(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,old_conflicts=a['meta']['branch'].get('conflict_count'),new_conflicts=b['meta']['branch'].get('conflict_count'),scope='Same frozen first root only, connection paths and failures; not whole-search equal work, native QoR, from-empty or net gain.'),indent=2)+'\n');print('ROOT path changes',sum(len(row['changed_path_ids']) for row in rows))
