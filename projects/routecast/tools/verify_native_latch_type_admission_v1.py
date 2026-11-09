"""Current binary input admission evidence for re versus al; no timing claims."""
import json,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/native_latch_type_admission_v1_2026-10-10';assert not D.exists()
B=R/'build/native_candidate_retained_search_2026-10-06/sequence_vpr';A=R/'experiments/async_reset_arch_candidate_v2_2026-10-08/architecture.xml'
S=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vpr/src/base/read_blif.cpp'
bindings={str(p):sha(p) for p in [Path(__file__).resolve(),B,A,S]};D.mkdir();plans=[]
for mode in ['re','al']:
 w=D/mode;w.mkdir();p=w/'design.blif';p.write_text('.model fixture\n.inputs d c\n.outputs q\n.latch d q '+mode+' c 0\n.end\n');bindings[str(p)]=sha(p)
 plans.append(dict(mode=mode,command=[str(B),str(A),'design.blif','--pack','--timing_analysis','off','--route_chan_width','128','--num_workers','1']))
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,plans=plans,timeout_s=60,scope='Minimal fixed binary input-admission pair; no physical timing, bfly equivalence, routing or heldout proof.'),indent=2)+'\n');rows=[]
for plan in plans:
 w=D/plan['mode'];tick=time.perf_counter()
 with (w/'native.log').open('w') as log:
  try:code=subprocess.run(plan['command'],cwd=w,stdout=log,stderr=subprocess.STDOUT,timeout=60).returncode
  except subprocess.TimeoutExpired:code=124
 text=(w/'native.log').read_text();rows.append(dict(mode=plan['mode'],exit_code=code,seconds=time.perf_counter()-tick,only_rising_edge_rejection='Only rising edge latches supported' in text))
 for p in w.iterdir():
  if p.is_file():bindings[str(p)]=sha(p)
 print(rows[-1],flush=True)
assert rows[0]['exit_code']==0 and not rows[0]['only_rising_edge_rejection']
assert rows[1]['exit_code']!=0 and rows[1]['only_rising_edge_rejection']
assert all(sha(p)==h for p,h in bindings.items())
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,current_binary_re_accepts_al_rejects=True,scope='Input/parser/pack gate only. Exact binary rejects low-level storage without an architecture timing experiment; no source modification or FF substitution.'),indent=2)+'\n')
