"""Selection mask conformance: all parity, none exact unchanged, invalid flag."""
import json,sys,subprocess,struct
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(Path(__file__).resolve().parent)]
from pre_route_endpoints import sha
from reusable_rr_floor_context import ReusableRRFloors
from shared_rr_inventory import SharedRRInventory
from indexed_integer_rc import IndexedIntegerRC
from shared_inventory_exchange_local import exchange
from native_route_ledger_import_compact import physical_paths
out=R/'experiments/native_local_exchange_contract_2026-10-07';out.mkdir();ep=R/'experiments/adder_tree_2L032_move_sequence_2026-10-06/step_1_endpoints.json';ctx=ReusableRRFloors(ep,R/'build/native_resume_rr_floor_cpp_2026-10-07/rr_floor',out/'context');inv=SharedRRInventory(ctx);ctx.rc=IndexedIntegerRC(ctx.rc,ctx.fields,ctx.initial,inv);rows=[]
for i in (1,2,3):
 ep=R/f'experiments/adder_tree_2L032_move_sequence_2026-10-06/step_{i}_endpoints.json';source=R/f'experiments/native_resume_postroute_v5_integrated_adder_step{i}_workflow_2026-10-07/first/live.search';w=out/f'all_{i}';r=exchange(ctx,ep,source/'design.route',w,inv,policy='all');assert (w/'output.jsonl').read_bytes()==(source/'exchange/output.jsonl').read_bytes();assert r['attempted_connections']==516;rows.append(dict(index=i,all_output_bytes_equal=True,reference_sha256=sha(source/'exchange/output.jsonl')))
source=R/'experiments/native_resume_postroute_v5_integrated_adder_step3_workflow_2026-10-07/first/live.search';r=exchange(ctx,ep,source/'design.route',out/'none',inv,policy='none');assert r['attempted_connections']==0 and not r['active_net_names'];actual={}
for q in r['records']:
 p=[(q['source'],None)]
 for eid in q['answer']['physical_edge_ids']:
  u,v,sw=inv.edges[eid];assert p[-1][0]==u;p.append((v,sw))
 actual.setdefault(json.loads(ep.read_text())['net_names'][str(q['net_id'])],[]).append(tuple(p))
norm=lambda paths:{name:Counter(ps) for name,ps in paths.items() if ps};assert norm(actual)==norm(physical_paths(source/'design.route'))
raw=bytearray((out/'all_1/input.bin').read_bytes());magic,n,m,k,penalty=struct.unpack_from('<5Q',raw);offset=40+8*(4*n+1+2*m)+16;struct.pack_into('<Q',raw,offset,2);bad=out/'bad_active.bin';bad.write_bytes(raw);binary=R/'build/native_resume_shared_exchange_local_cpp_2026-10-07/exchange';run=subprocess.run([str(binary),str(bad)],capture_output=True,timeout=20);assert run.returncode==2 and run.stderr.decode().strip()=='active flag'
(out/'receipt.json').write_text(json.dumps(dict(rows=rows,none_paths_exactly_preserved=True,all_endpoints=516,invalid_active_flag_rejected=True,checker_sha256=sha(__file__),scope='All-mask byte parity to original policy on 3 initial states, no-mask exact physical paths/occupancy preserved, invalid mask flag rejected. Localized policy quality evaluated in separate fresh sequence, not inferred from these contracts.'),indent=2)+'\n');print('PASS')
