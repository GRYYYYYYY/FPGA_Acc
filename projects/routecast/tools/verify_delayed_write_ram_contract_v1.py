"""Exhaustive one-step relational check for deferred writes, cross-port bypass and output hold."""
import itertools,json,hashlib,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/delayed_write_ram_contract_v1_2026-10-09';D.mkdir(exist_ok=False)
def write(mem,en,addr,data):
 out=list(mem)
 if en:out[addr]=data
 return tuple(out)
start=time.perf_counter();cases=0;different_read_schedules=0;bad_without_bypass=None
# Two words, one-bit lanes. All physical states, pending/current writes and source output holds.
for physical in itertools.product((0,1),repeat=2):
 for p_en,p_addr,p_data,w_en,w_addr,w_data,r_addr,r_en,old_q in itertools.product((0,1),repeat=9):
  logical=write(physical,p_en,p_addr,p_data)
  source_q=logical[r_addr] if r_en else old_q
  source_next=write(logical,w_en,w_addr,w_data)
  physical_next=write(physical,p_en,p_addr,p_data)
  target_logical_next=write(physical_next,w_en,w_addr,w_data)
  assert source_next==target_logical_next
  hit=p_en and p_addr==r_addr
  for raw in (physical[r_addr],physical_next[r_addr]):
   corrected=p_data if hit else raw
   # Post-edge Ereg=r_en; Hreg captures old visible output. No extra visible read latency.
   target_q=corrected if r_en else old_q
   assert target_q==source_q
   if bad_without_bypass is None and r_en and raw!=source_q:
    bad_without_bypass=dict(physical=physical,pending=[p_en,p_addr,p_data],read=[r_addr,r_en],raw=raw,expected=source_q)
   cases+=1
  different_read_schedules+=physical[r_addr]!=physical_next[r_addr]
assert bad_without_bypass is not None
# Reachable initial relation: pending WE=0 and output selector E=0, arbitrary logical data/old output.
for memory in itertools.product((0,1),repeat=2):assert write(memory,0,0,0)==memory
report=dict(bindings={str(Path(__file__).resolve()):hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},one_step_cases=cases,physical_cross_collision_cases=different_read_schedules,required_initial_state={'pending_write_enable':0,'output_read_enable_selector':0,'memory_contents':'arbitrary matched','output_hold':'arbitrary matched'},missing_bypass_counterexample=bad_without_bypass,seconds=time.perf_counter()-start,scope='Exhaustive finite one-bit/two-word abstract relational transition invariant. Covers both cross-port scheduling outcomes, read enable hold and no visible extra latency. Not implemented RTL/native RAM mapping, arbitrary-width formal proof, four-state unknown-enable semantics or silicon timing.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',cases,'schedule cases; missing bypass rejected')
