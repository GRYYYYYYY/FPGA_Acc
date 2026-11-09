"""Independent Cartesian path-choice oracle for localized capacity conflict."""
import json,itertools
from pathlib import Path
from collections import defaultdict,Counter
from pre_route_endpoints import sha
from native_resume_prototype.source_binding_v2 import closure
from unified_rr_audit_inventory_v2 import read
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'adder_full871_local_capacity_v1_2026-10-09';D.mkdir(exist_ok=False);vp=E/'adder_full871_rup_core_verification_v1_2026-10-09/verification.json';v=json.loads(vp.read_text());bindings={**v['bindings'],str(vp):sha(vp),**closure([Path(__file__)])};assert all(sha(p)==h for p,h in bindings.items());bp=E/'adder_local_capacity_detours_v3_2026-10-09/step_3.json';bank={int(c):p for c,p in json.loads(bp.read_text())['bank'].items()};mp=E/'adder_tree_2L032_move_sequence_2026-10-06/step_3_endpoints.json';meta=json.loads(mp.read_text());q={x['connection_id']:x for x in meta['connections']};inv=read(meta['inputs']['graph']['path'],meta['graph_sha256']);cids=v['connection_ids'];nodes=set(v['capacity_nodes']);hist=Counter();tested=0;legal=[]
for choices in itertools.product(*(range(len(bank[c])) for c in cids)):
 owners=defaultdict(set)
 for cid,index in zip(cids,choices):
  for n,s in bank[cid][index]['path']:
   if n in nodes:owners[n].add(q[cid]['net_id'])
 conflicts=sorted(n for n,nets in owners.items() if len(nets)>int(inv.physical.nodes[n][1]));tested+=1
 if conflicts:hist[conflicts[0]]+=1
 else:legal.append(list(choices))
assert not legal,'Core mapping failed to yield direct physical capacity contradiction'
for p in (bp,mp):bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items());out=dict(bindings=bindings,status='LOCAL_CAPACITY_EXHAUSTED',connection_ids=cids,node_ids=sorted(nodes),candidate_counts={str(c):len(bank[c]) for c in cids},all_combinations=tested,capacity_legal_combinations=0,first_conflict_histogram=dict(hist),scope='Every original candidate combination of these9 CIDs exceeds original distinctNET capacity on these9 nodes, without parent constraints or SAT propagation. Fixed bank only, not physical graph infeasibility.');(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print({k:v for k,v in out.items() if k!='bindings'})
