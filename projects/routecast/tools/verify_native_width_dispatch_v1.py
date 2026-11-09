"""Full observed width guards/mode switches, complete reference paths and work parity."""
import json,re
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/sha_resident_adaptive_width_seed_complete_workflow_v1_2026-10-10';T=R/'experiments/native_width_mode_switch_v1_2026-10-10';files=[Path(__file__)];results=[]
for path in [D/'verification.json',D/'wire_transaction_verification.json',D/'handoff_parity_verification.json',T/'receipt.json']:
 v=json.loads(path.read_text());assert all(sha(p)==h for p,h in v['bindings'].items());files.append(path)
assert v['all18819_paths_and_raw_costs_equal_original128'] and v['all_actual_native_routes_byte_equal']
for log,expected_prices,expected_bits in [(D/'seed/native/sha1/native.log',[0,0,19,20],[64,64,64,64]),(T/'adaptive/native.log',[0,0,2**64-1,0],[64,64,128,64])]:
 rows=[]
 for m in re.finditer(r'ROUTECAST_WIDTH phase=(\d+) bits=(\d+) bound_hi=(\d+) bound_lo=(\d+) max_price=(\d+)',log.read_text()):
  phase,bits,high,low,maximum=map(int,m.groups());weight=0 if phase==0 else 50000000;bound=2*91088*(312900011+weight*maximum);assert bound==(high<<64)+low and bits==(64 if bound<2**64-1 else 128);rows.append(dict(phase=phase,bits=bits,maximum_price=maximum,bound=bound))
 assert [r['maximum_price'] for r in rows]==expected_prices and [r['bits'] for r in rows]==expected_bits;files.append(log);results.append(rows)
N=D/'seed/native/sha1';original=R/'experiments/sha_resident_work_profile_seed_complete_workflow_v1_2026-10-10/seed/native/sha1/work.tsv';assert (N/'work.tsv').read_bytes()==original.read_bytes();files.extend([N/'work.tsv',original])
A=T/'original128/responses.jsonl';B=T/'adaptive/responses.jsonl';assert A.read_bytes()==B.read_bytes();files.extend([A,B]);
(D/'width_dispatch_verification.json').write_text(json.dumps(dict(bindings={str(p):sha(p) for p in files},all_runtime_guard_bounds_and_modes_pass=True,normal_all7459_work_records_equal_original128=True,all18819_three_phase_mode_switch_paths_costs_equal=True,mode_cases=results,scope='Runtime observed normal64 and extreme64->128->64 on complete realgraph query corpus. Independent original128 headers preserved, raw/parent outputs separate perbackend; no dynamic admission/fallback objective policy changes. Boundary high prices controlled, not learned/heldout labels.'),indent=2)+'\n');print('FULL WIDTH DISPATCH AND WORK PARITY')
