"""Canonical reload from actual synchronized packed netlist; full paths must remain."""
import json,sys,re,shutil
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
from loaded_native_canonical_reload import canonical_reload
from native_route_ledger_import_compact import physical_paths
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
S=R/'experiments/native_owner_candidate_reload_v5_2026-10-08';vp=S/'verification.json';v=json.loads(vp.read_text());assert all(sha(f)==h for f,h in v['bindings'].items())
assert not v['changed_physical_connection_ids'] and v['budget_violation_connection_ids']==[785,1637]
D=R/'experiments/native_owner_candidate_canonical_v5_2026-10-08';D.mkdir(exist_ok=False);source=D/'source';source.mkdir()
bindings={**v['bindings'],str(vp):sha(vp),**closure([Path(__file__)])}
for name in ('design.blif','design.net','design.net.post_routing','design.place'):
 f=S/name;bindings[str(f)]=sha(f);shutil.copyfile(f,source/name)
shutil.copyfile(S/'design.route',source/'output.route');text=(S/'reload.log').read_text();cpd=float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[-1])
original=json.loads((R/'experiments/budget_repair_native_reload_v1_2026-10-08/protocol.json').read_text())
p=dict(width=32,decision='R',command=['--route' if x=='--analysis' else x for x in original['command']],cpd_ns=cpd,files={str(f):sha(f) for f in source.iterdir()})
result=canonical_reload(p,source,D/'canonical')
normalize=lambda f:Counter((name,path) for name,paths in physical_paths(f).items() for path in paths)
assert normalize(D/'canonical/design.route')==normalize(S/'reconciled.route') and sum(normalize(D/'canonical/design.route').values())==1929
assert result['exit_code']==0 and result['mismatches']==result['fixups']==0
assert all(sha(f)==h for f,h in bindings.items())
report=dict(bindings=bindings,canonical=result,all1929_postsync_physical_paths_preserved=True,scope='Consistent post-sync packed netlist canonical original FULL/STA zero-fixup acceptance; original nonzero first-pass reconciliation retained, original HDL equivalence and full budgets/time/QoR gain unproved.')
(D/'receipt.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS canonical all1929 paths, zero mismatches/fixups, CPD',cpd)
