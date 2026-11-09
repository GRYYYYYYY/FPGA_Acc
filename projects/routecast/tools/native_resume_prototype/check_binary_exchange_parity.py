"""Text vs binary kernel output parity and binary framing rejection."""
import sys,json,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(Path(__file__).resolve().parent)]
from pre_route_endpoints import sha
from reusable_rr_floor_context import ReusableRRFloors
from shared_rr_inventory import SharedRRInventory
from shared_inventory_exchange_binary import exchange
out=R/'experiments/native_binary_exchange_parity_2026-10-07';out.mkdir();ep=R/'experiments/adder_tree_2L032_move_sequence_2026-10-06/step_1_endpoints.json';ctx=ReusableRRFloors(ep,R/'build/native_resume_rr_floor_cpp_2026-10-07/rr_floor',out/'context');inv=SharedRRInventory(ctx);rows=[];binary=R/'build/native_resume_shared_exchange_binary_cpp_2026-10-07/exchange'
for i in (1,2,3):
 ep=R/f'experiments/adder_tree_2L032_move_sequence_2026-10-06/step_{i}_endpoints.json';ref=R/f'experiments/native_resume_live_integrated_adder_step{i}_workflow_2026-10-07';w=out/f'step{i}';result=exchange(ctx,ep,ref/'exchange_native/live.search/design.route',w,inv);old=ref/'exchange_native/live.search/exchange/output.jsonl';assert (w/'output.jsonl').read_bytes()==old.read_bytes();rows.append(dict(index=i,conversion_seconds=result['conversion_seconds'],compiled_child_seconds=result['compiled_child_seconds'],total_seconds=result['total_seconds'],reference_sha256=sha(old),output_sha256=sha(w/'output.jsonl'),all_attempts_decisions_paths_delays_byte_identical=True))
raw=(out/'step1/input.bin').read_bytes();guards=[]
for case,data in [('truncated_header',raw[:7]),('truncated_tail',raw[:-1]),('trailing_byte',raw+b'x'),('wrong_magic',b'\0'*8+raw[8:])]:
 p=out/(case+'.bin');p.write_bytes(data);run=subprocess.run([str(binary),str(p)],capture_output=True,timeout=20);assert run.returncode==2;error=run.stderr.decode().strip();assert error=={'truncated_header':'truncated','truncated_tail':'truncated','trailing_byte':'trailing','wrong_magic':'magic'}[case];guards.append(dict(case=case,error=error))
(out/'receipt.json').write_text(json.dumps(dict(rows=rows,guards=guards,binary_sha256=sha(binary),source_sha256=sha(R/'tools/native_resume_prototype/shared_exchange_binary_cpp/main.cpp'),checker_sha256=sha(__file__),scope='Entire text-kernel JSON output byte parity for three known live initial states, includes all attempts, decisions and 516 full paths each. Four framing rejections. Graph context initialization paid only in separate parity setup; not full routing speed claim.'),indent=2)+'\n');print(rows)
