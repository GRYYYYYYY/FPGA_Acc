"""Original SHA160 BLIF pack compatibility experiment; no family/timing admission."""
import json,os,shutil,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];F=R/'experiments/sha1_frontend_readiness_v1_2026-10-10'
proofs=[F/'receipt.json',R/'experiments/sha1_json_blif_structure_v1_2026-10-10/verification.json',R/'experiments/sha1_archived_json_equivalence_v4_2026-10-10/receipt.json',R/'experiments/sha1_reset_alignment_sat_v1_2026-10-10/receipt.json']
bindings={str(Path(__file__).resolve()):sha(__file__)}
for p in proofs:
 d=json.loads(p.read_text());assert all(sha(k)==h for k,h in d['bindings'].items());bindings.update(d['bindings']);bindings[str(p)]=sha(p)
 if 'exit_code' in d:assert d['exit_code']==0
 if 'rows' in d:assert d['rows'][0]['all_ports_truth_tables_pins_clocks_initial_states_exact']
V=R/'build/native_candidate_retained_search_2026-10-06/sequence_vpr';A=R/'experiments/async_reset_arch_candidate_v2_2026-10-08/architecture.xml';D=R/'experiments/sha1_native_pack_v1_2026-10-10';assert not D.exists();D.mkdir();w=D/'sha1';w.mkdir();shutil.copyfile(F/'design.blif',w/'design.blif')
for p in [V,A,w/'design.blif']:bindings[str(p)]=sha(p)
cmd=[str(V),str(A),'design.blif','--pack','--route_chan_width','128','--num_workers','1','--seed','1']
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,command=cmd,timeout_seconds=600,scope='Single original full SHA160 pack attempt; no HDL changes, no route labels, no retry. Existing async architecture reused only as compatibility harness; timing and source-family/initial synchronization scope limitations remain.'),indent=2)+'\n');tick=time.perf_counter()
with (w/'pack.log').open('w') as log:
 try:code=subprocess.run(cmd,cwd=w,env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')},stdout=log,stderr=subprocess.STDOUT,timeout=600).returncode
 except subprocess.TimeoutExpired:code=124
assert not list(w.glob('*.route'));assert all(sha(k)==h for k,h in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,name='sha1',exit_code=code,seconds=time.perf_counter()-tick,status='PACK_NATIVE_SUCCESS_PENDING_PACKED_SIGNAL_AUDIT' if code==0 and 'VPR succeeded' in (w/'pack.log').read_text() and (w/'design.net').exists() else 'PACK_FAILED_OR_TIMEOUT',files={str(p):sha(p) for p in w.iterdir() if p.is_file()},native_route_labels_generated=False,heldout_admitted=False),indent=2)+'\n');print('SHA1 PACK',code,flush=True)
