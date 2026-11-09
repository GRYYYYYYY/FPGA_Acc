"""Independent full-slot oracle and real-state exchange parity before integration."""
import json,sys,time
from pathlib import Path
from types import SimpleNamespace
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(Path(__file__).resolve().parent)]
from pre_route_endpoints import sha
from reusable_rr_floor_context import ReusableRRFloors
from indexed_integer_rc import IndexedIntegerRC
from shared_rr_inventory_slots_v2 import SharedRRInventorySlots,exchange_slot_index
from shared_inventory_exchange_slots_v2 import exchange
out=R/'experiments/native_exchange_slots_v2_contract_2026-10-07';out.mkdir()
fixture={'row_offsets':[0,3,3], 'dest_ranks':[1,1,1], 'switch_ids':[7,8,7]}
lookup=exchange_slot_index(fixture,2);assert dict(lookup)=={(0,1,7):2,(0,1,8):1}
try:lookup[0,1,7]=0
except TypeError:pass
else:raise AssertionError('mutable lookup')
for f in ({**fixture,'row_offsets':[0,4,3]}, {**fixture,'dest_ranks':[1,2,1]}, {**fixture,'switch_ids':[7]}):
 try:exchange_slot_index(f,2)
 except ValueError:pass
 else:raise AssertionError('malformed CSR accepted')
ep=R/'experiments/adder_tree_2L032_move_sequence_2026-10-06/step_1_endpoints.json';ctx=ReusableRRFloors(ep,R/'build/native_resume_rr_floor_cpp_2026-10-07/rr_floor',out/'context');start=time.perf_counter();inv=SharedRRInventorySlots(ctx);construction=time.perf_counter()-start;ctx.rc=IndexedIntegerRC(ctx.rc,ctx.fields,ctx.initial,inv)
f=ctx.fields;oracle={};counts={}
for u in range(ctx.n):
 for s in range(f['row_offsets'][u],f['row_offsets'][u+1]):
  arc=(u,f['dest_ranks'][s],f['switch_ids'][s]);oracle[arc]=s;counts[arc]=counts.get(arc,0)+1
slots,spans=inv.exchange_structure(ctx);assert dict(slots)==oracle
for n,(kind,loc) in inv.nodes.items():assert spans[n]==(1+int(loc['xhigh'])-int(loc['xlow'])+int(loc['yhigh'])-int(loc['ylow']) if kind in ('CHANX','CHANY') else 0)
for overrides in ({'fields':dict(ctx.fields)},{'n':ctx.n+1},{'digest':'bad'},{'graph':Path('/tmp/other')}):
 bad=SimpleNamespace(fields=ctx.fields,n=ctx.n,digest=ctx.digest,graph=ctx.graph);bad.__dict__.update(overrides)
 try:inv.exchange_structure(bad)
 except ValueError:pass
 else:raise AssertionError('context alias accepted')
rows=[];bindings={str(Path(__file__)):sha(__file__),str(ctx.graph):sha(ctx.graph)}
for i in (1,2,3):
 ep=R/f'experiments/adder_tree_2L032_move_sequence_2026-10-06/step_{i}_endpoints.json';base=R/f'experiments/native_resume_postroute_cost_profile_adder_step{i}_workflow_2026-10-07/first/live.search';reference=base/'exchange/receipt.json';ref=json.loads(reference.read_text());r=exchange(ctx,ep,base/'design.route',out/f'exchange_{i}',inv)
 for k in ('records','selected_net_names','policy','active_net_names','critical_net_names','top_wire_net_names','attempted_connections'):assert r[k]==ref[k],k
 for name in ('input.bin','output.jsonl'):assert (out/f'exchange_{i}'/name).read_bytes()==(base/'exchange'/name).read_bytes()
 bindings[str(reference)]=sha(reference);rows.append(dict(index=i,conversion_seconds=r['conversion_seconds'],total_seconds=r['total_seconds'],reference_conversion_seconds=ref['conversion_seconds'],reference_total_seconds=ref['total_seconds'],payload_and_output_bytes_equal=True));print('PASS',i,flush=True)
assert all(sha(p)==h for p,h in bindings.items())
(out/'receipt.json').write_text(json.dumps(dict(rows=rows,bindings=bindings,arc_count=len(slots),edge_count=len(f['edge_ids']),duplicate_arc_count=sum(n>1 for n in counts.values()),inventory_plus_index_construction_seconds=construction,synthetic_duplicate_last_slot_pass=True,readonly_mapping_pass=True,malformed_csr_rejections=3,context_mismatch_rejections=4,scope='Full real CSR slot/span parity plus three actual state binary payload/output and records/selection parity. Local timings exclude context construction except separately reported; no in-memory mutation/concurrent writer guarantee.'),indent=2)+'\n')
