"""Actual complete cut-export oracle audit with deliberate export corruptions."""
import copy,json
from pathlib import Path
from audit_vexriscv_cut_export_v1 import audit
from pre_route_endpoints import sha
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'vexriscv_cut_logic_v1_2026-10-09';D=E/'vexriscv_cut_export_audit_v1_2026-10-09';D.mkdir(exist_ok=False)
p=E/'vexriscv_flattened_candidate_v1_2026-10-09/design.json';module=json.loads(p.read_text())['modules']['VexRiscvSmallest'];text=(B/'original.blif').read_text();boundary=json.loads((B/'sequential_boundary.json').read_text());result=audit(module,text,boundary)
rejected=[]
def reject(label,t,b):
 try:audit(module,t,b)
 except (AssertionError,KeyError,ValueError):rejected.append(label)
 else:raise AssertionError('Corruption accepted: '+label)
b=copy.deepcopy(boundary);key=next(k for k,c in b['cells'].items() if c['type']=='$_DFF_PP0_');del b['cells'][key];reject('reset_cell_dropped',text,b)
b=copy.deepcopy(boundary);b['cells'][key]['connections']['R']=[-1];reject('reset_signal_changed',text,b)
reject('mux_truth_row_changed',text.replace('011 1','001 1',1),boundary)
lines=text.splitlines();index=next(i for i,line in enumerate(lines) if line.startswith('.inputs '));words=lines[index].split();lines[index]=' '.join(words[:-1]);reject('missing_cut_input','\n'.join(lines),boundary)
reject('extra_undeclared_gate',text.replace('.end','.names nonexistent ghost\n1 1\n.end'),boundary)
bindings=closure([Path(__file__)])
for path in (p,B/'original.blif',B/'sequential_boundary.json',B/'receipt.json'):bindings[str(path)]=sha(path)
receipt=json.loads((B/'receipt.json').read_text());assert all(sha(path)==h for path,h in receipt['bindings'].items());bindings.update(receipt['bindings'])
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,audit=result,rejected=rejected,scope='Independent all flattened JSON primitive truth/ports/cut boundary/driver reachability; original sequential cell records preserved verbatim. Combined with ABC CEC proves combinational mapping preparation, not HDL sequential equivalence or native async-reset support.'),indent=2)+'\n');print(dict(audit=result,rejected=rejected),flush=True)
