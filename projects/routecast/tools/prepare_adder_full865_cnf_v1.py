"""Encode all516 connections in certified852 bank without residual filtering."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from native_resume_prototype.source_binding_v2 import closure
from unified_rr_audit_inventory_v2 import read
from finite_route_bank_cnf_v1 import encode
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'adder_full865_cnf_v1_2026-10-09';D.mkdir(exist_ok=False);vp=E/'adder_local_capacity_detours_verification_v2_2026-10-09/verification.json';v=json.loads(vp.read_text());bindings={**v['bindings'],str(vp):sha(vp),**closure([Path(__file__)])};assert all(sha(p)==h for p,h in bindings.items());bp=E/'adder_local_capacity_detours_v2_2026-10-09/step_3.json';bank={int(c):o for c,o in json.loads(bp.read_text())['bank'].items()};mp=E/'adder_tree_2L032_move_sequence_2026-10-06/step_3_endpoints.json';meta=json.loads(mp.read_text());q={x['connection_id']:x for x in meta['connections']};assert set(bank)==set(q) and len(bank)==516 and sum(map(len,bank.values()))==865;inv=read(meta['inputs']['graph']['path'],meta['graph_sha256']);cnf=encode(bank,q,{n:int(cap) for n,(kind,cap) in inv.physical.nodes.items()});ep=D/'encoding.json';ep.write_text(json.dumps(cnf,indent=2)+'\n');dim=D/'problem.cnf';dim.write_text(f"p cnf {len(cnf['variables'])} {len(cnf['clauses'])}\n"+''.join(' '.join(map(str,c))+' 0\n' for c in cnf['clauses']))
for p in (bp,mp,ep,dim):bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,status='FORMULATION_ONLY_UNSOLVED',connections=516,candidates=865),indent=2)+'\n');print(len(cnf['variables']),len(cnf['clauses']))
