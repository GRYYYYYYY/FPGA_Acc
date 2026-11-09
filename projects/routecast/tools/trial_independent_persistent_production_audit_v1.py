"""Real three-step oracle checks plus corrupted clause/path/model rejection."""
import json,copy,time
from pathlib import Path
from fractions import Fraction as F
from independent_persistent_production_audit_v1 import audit
from unified_rr_audit_inventory_v2 import read
from pre_route_endpoints import sha
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'independent_persistent_production_audit_v1_2026-10-09';D.mkdir(exist_ok=False);bindings=closure([Path(__file__)])
g=R/'work/adder_tree_family_native_capture_v2_2026-10-06/adder_tree_2L_032bits/rr_graph.xml';inv=read(g,sha(g));bindings[str(g)]=sha(g);rows=[]
for step in range(1,4):
 p=E/f'persistent_complete_chain_v1_2026-10-09/step_{step}_result.json';h=E/f'persistent_complete_chain_v1_2026-10-09/step_{step}_history.json';ep=E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json';bp=E/f'adder_legal_route_budget_fixture_v1_2026-10-09/step_{step}_budgets.json'
 data=json.loads(p.read_text());history=json.loads(h.read_text());q={x['connection_id']:x for x in json.loads(ep.read_text())['connections']};budgets={x['connection_id']:F(*x['exact_delay_s']) for x in json.loads(bp.read_text())}
 tick=time.perf_counter();row=audit(data,history,q,budgets,inv);row.update(step=step,audit_seconds=time.perf_counter()-tick);rows.append(row)
 for path in (p,h,ep,bp):bindings[str(path)]=sha(path)
rejections=[]
def reject(label,bad):
 try:audit(bad,history,q,budgets,inv)
 except (AssertionError,KeyError,ValueError):rejections.append(label)
 else:raise AssertionError(label+' accepted')
bad=copy.deepcopy(data);bad['rounds'][0]['encoding']['clauses'].pop();reject('missing_formula_clause',bad)
bad=copy.deepcopy(data);cid=next(iter(bad['bank']));bad['bank'][cid][0]['path'][1][1]=999999;reject('invalid_physical_switch',bad)
bad=copy.deepcopy(data);key=next(iter(bad['paths']));bad['paths'][key].append(bad['paths'][key][0]);reject('corrupted_selected_path',bad)
bad=copy.deepcopy(data);var=next(iter(bad['result']['model']));bad['result']['model'][var]=not bad['result']['model'][var];reject('terminal_model_changed_without_round',bad)
assert all(sha(p)==h for p,h in bindings.items())
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,rejections=rejections,scope='Independent reusable all-bank XML/Fraction audit, each prefix structural CNF/naive RUP/model, physical search events and selected/partial NET capacity/parent. Supplied immutable inventory must be authenticated by caller; no production/cache imports.'),indent=2)+'\n');print(dict(rows=rows,rejections=rejections),flush=True)
