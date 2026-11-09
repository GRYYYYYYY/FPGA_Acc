"""Freeze the current unknown 154-CID component as an exact SAT input artifact."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from native_resume_prototype.source_binding_v2 import closure
from unified_rr_audit_inventory_v2 import read
from finite_route_bank_cnf_v1 import encode
R=Path(__file__).resolve().parents[1];E=R/'experiments';T=E/'adder_online_direct_core_joint_components_v1_2026-10-09';D=E/'adder_online_direct_core_cnf_v1_2026-10-09';D.mkdir(exist_ok=False);vp=E/'adder_online_direct_core_joint_component_verification_v1_2026-10-09/verification.json';v=json.loads(vp.read_text());assert all(sha(p)==h for p,h in v['bindings'].items());bindings={**v['bindings'],str(vp):sha(vp),**closure([Path(__file__)])};p=E/'adder_online_direct_core_joint_search_v1_2026-10-09/step_3.json';bank={int(c):o for c,o in json.loads(p.read_text())['bank'].items()};d=json.loads((T/'decomposition.json').read_text());domains={int(c):ids for c,ids in d['domains'].items()};component=json.loads((T/'component_1.json').read_text())['connections'];bank={c:[bank[c][i] for i in domains[c]] for c in component};ep=E/'adder_tree_2L032_move_sequence_2026-10-06/step_3_endpoints.json';meta=json.loads(ep.read_text());q={x['connection_id']:x for x in meta['connections']};inv=read(meta['inputs']['graph']['path'],meta['graph_sha256']);cnf=encode(bank,q,{n:int(cap) for n,(kind,cap) in inv.physical.nodes.items()});jp=D/'encoding.json';jp.write_text(json.dumps(cnf,indent=2)+'\n');dim=D/'problem.cnf'
with dim.open('x') as f:
 f.write(f"p cnf {len(cnf['variables'])} {len(cnf['clauses'])}\n")
 for clause in cnf['clauses']:f.write(' '.join(map(str,clause))+' 0\n')
for p in (p,ep,jp,dim):bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items());out=dict(bindings=bindings,connections=len(component),variables=len(cnf['variables']),clauses=len(cnf['clauses']),status='FORMULATION_ONLY_UNSOLVED',scope=cnf['scope']);(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print({k:v for k,v in out.items() if k!='bindings'})
