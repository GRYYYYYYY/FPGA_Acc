"""Graph-inventory native canonicalization parity against archived XML path."""
import json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from source_binding import closure
from reusable_rr_floor_context import ReusableRRFloors
from shared_rr_inventory import SharedRRInventory
from canonical_reload_inventory import canonical_reload
R=Path(__file__).resolve().parents[2];o=R/'experiments/native_resume_canonical_inventory_parity_2026-10-07';o.mkdir(exist_ok=False);inputs={}
for i in (1,2,3):
 b=R/f'experiments/native_resume_buffered_budget_adder_step{i}_workflow_2026-10-07';r=json.loads((b/'receipt.json').read_text());inputs[str(b/'receipt.json')]=sha(b/'receipt.json');inputs.update(r['canonical']['files'])
proto=dict(inputs=inputs,sources=closure([Path(__file__)]),scope='Fresh canonical native FULL/STA using existing inventory; archived XML-path native outputs as parity reference, no controlled timing or full net gain claim.')
(o/'protocol.json').write_text(json.dumps(proto,indent=2)+'\n');start=time.perf_counter();ctx=ReusableRRFloors(R/'experiments/adder_tree_2L032_move_sequence_2026-10-06/step_1_endpoints.json',R/'build/native_resume_rr_floor_cpp_2026-10-07/rr_floor',o/'context');inv=SharedRRInventory(ctx);bootstrap=time.perf_counter()-start;rows=[]
for i in (1,2,3):
 b=R/f'experiments/native_resume_buffered_budget_adder_step{i}_workflow_2026-10-07';r=json.loads((b/'receipt.json').read_text());source=Path(r['selected_work']);cmd=list(r['canonical']['command']);cmd[cmd.index('--analysis')]='--route';meta=dict(width=32,decision='R',command=cmd,cpd_ns=float(r['cpd_ns']),files={str(f):sha(f) for f in source.iterdir() if f.is_file()});start=time.perf_counter();new=canonical_reload(meta,source,o/f'step{i}',inv);seconds=time.perf_counter()-start
 for f in ('design.blif','design.net','design.place','design.route','identity.jsonl'):assert (o/f'step{i}'/f).read_bytes()==(b/'exchange_canonical'/f).read_bytes(),f
 assert all(new[k]==r['canonical'][k] for k in ('cpd_ns','pins','mismatches','fixups','graph_sha256','exit_code'))
 rows.append(dict(index=i,seconds=seconds,route_identity_place_net_bytes_exact=True,cpd_ns=new['cpd_ns'],mismatches=new['mismatches'],fixups=new['fixups']));print(rows[-1],flush=True)
# Wrong graph identity must fail before any output publication.
class WrongInventory:
 digest='0'*64
 def validate(self,graph,digest):raise ValueError('inventory graph mismatch')
try:canonical_reload(meta,source,o/'invalid_graph',WrongInventory())
except ValueError:assert not (o/'invalid_graph').exists()
else:raise AssertionError('wrong inventory accepted')
assert all(sha(f)==h for f,h in {**inputs,**proto['sources']}.items());(o/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(o/'protocol.json'),bootstrap_seconds=bootstrap,rows=rows,wrong_inventory_rejected_before_output=True,scope=proto['scope']),indent=2)+'\n')
