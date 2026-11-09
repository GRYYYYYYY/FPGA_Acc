"""Actual inventory graph mismatch and input hash failures before publication."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from reusable_rr_floor_context import ReusableRRFloors
from shared_rr_inventory import SharedRRInventory
from canonical_reload_inventory import canonical_reload
R=Path(__file__).resolve().parents[2];o=R/'experiments/native_resume_canonical_inventory_contract_2026-10-07';o.mkdir(exist_ok=False);b=R/'experiments/native_resume_buffered_budget_adder_step3_workflow_2026-10-07';r=json.loads((b/'receipt.json').read_text());src=Path(r['selected_work']);cmd=list(r['canonical']['command']);cmd[cmd.index('--analysis')]='--route';p=dict(width=32,decision='R',command=cmd,cpd_ns=float(r['cpd_ns']),files={str(f):sha(f) for f in src.iterdir() if f.is_file()});ctx=ReusableRRFloors(R/'experiments/adder_tree_2L032_move_sequence_2026-10-06/step_3_endpoints.json',R/'build/native_resume_rr_floor_cpp_2026-10-07/rr_floor',o/'context');inv=SharedRRInventory(ctx);cases=[]
wrong=dict(p,command=list(cmd));wrong['command'][wrong['command'].index('--read_rr_graph')+1]=str(ctx.graph.parent/'different_graph.xml')
try:canonical_reload(wrong,src,o/'wrong_graph',inv)
except ValueError as e:assert str(e)=='inventory graph mismatch' and not (o/'wrong_graph').exists();cases.append('actual_inventory_mismatched_graph_rejected')
else:raise AssertionError('graph mismatch accepted')
wrong=dict(p,files={**p['files'],str(src/'design.blif'):'0'*64})
try:canonical_reload(wrong,src,o/'wrong_source_hash',inv)
except AssertionError:assert not (o/'wrong_source_hash').exists();cases.append('changed_source_binding_rejected')
else:raise AssertionError('source mismatch accepted')
(o/'receipt.json').write_text(json.dumps(dict(cases=cases,script_sha256=sha(Path(__file__)),inventory_module_sha256=sha(R/'tools/native_resume_prototype/canonical_reload_inventory.py'),source_bindings=p['files'],graph_sha256=ctx.digest,scope='Real inventory rejects a different graph path and invalid source hash before output directory creation. No concurrent writer or durable multi-epoch claim.'),indent=2)+'\n');print(cases)
