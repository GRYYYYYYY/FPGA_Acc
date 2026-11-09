"""Terminal native availability only: full gates or certified fixed-limit algorithm failure."""
import json,re,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/prospective_external_family_corrected_width_sources_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 t=read(D/'terminal.json');m=read(D/'manifest.json');assert len(t['rows'])==len(m['cases'])==2;assert all(sha(k)==h for k,h in m['bindings'].items());bycase={c['case']:c for c in m['cases']};bindings={str(D/'terminal.json'):sha(D/'terminal.json'),str(D/'manifest.json'):sha(D/'manifest.json'),str(D/'protocol.json'):sha(D/'protocol.json'),str(Path(__file__).resolve()):sha(__file__)};rows=[]
 for tr in t['rows']:
  c=bycase[tr['case']];cmd=c['command'];assert cmd[cmd.index('--max_router_iterations')+1]=='300';assert cmd[cmd.index('--routing_failure_predictor')+1]=='off';assert cmd[cmd.index('--router_init_wirelength_abort_threshold')+1]=='1000000000';out=Path(c['output']);vp=out/'verification.json';v=read(vp);assert all(sha(k)==h for k,h in v['bindings'].items());log=out/'native.log';text=log.read_text();iterations=[]
  pattern=r'^\s*(\d+)\s+([0-9.]+)\s+([0-9.]+)\s+\d+\s+\S+\s+\d+\s+\d+\s+(\d+)\s+\([^)]*\)\s+(\d+)'
  for line in text.splitlines():
   if a:=re.match(pattern,line):iterations.append(dict(iteration=int(a[1]),reported_iteration_seconds=float(a[2]),pres_fac=float(a[3]),overused_nodes=int(a[4]),wirelength=int(a[5])))
  passed=v['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS';row=dict(case=c['case'],width=c['width'],source_conditioning_admitted=passed,native_exit=v['exit_status'],status=v['status'],iteration_rows=len(iterations),last_iteration=iterations[-1] if iterations else None)
  if passed:
   assert tr['process_exit']==v['exit_status']==0 and v['canonical']['semantic_consistency_gate_pass'];row['classification']='FULL_PHYSICAL_CANONICAL_SOURCE_ADMITTED'
  else:
   assert tr['process_exit']!=0 and v['exit_status']==2 and 'VPR failed to implement circuit' in text;assert [r['iteration'] for r in iterations]==list(range(1,301));assert iterations[-1]['overused_nodes']>0;assert 'RC_TIMING_GRAPH_SNAPSHOT' not in text;row['classification']='FIXED300_NATIVE_ITERATIONS_EXHAUSTED_WITH_OVERUSE_NOT_UNROUTEABILITY_PROOF';row['blocked_forecast_conditioning_cases']=[f"w{c['width']:03d}/episode_{i:02d}" for i in (1,2,3)]
  rows.append(row)
  for p in (vp,log):bindings[str(p)]=sha(p)
 assert all(sha(k)==h for k,h in bindings.items());(D/'verification_v2.json').write_text(json.dumps(dict(status='BOTH_CORRECTED_NATIVE_WIDTH_SOURCE_TERMINAL_OUTCOMES_AUDITED',rows=rows,bindings=bindings,full9_admitted=False,original_unavailable6_replaced=False,scope='Fixed binary/graph/options/300iteration native availability only. Native failure with overuse is not proof no legal route exists; target native outcomes not inferred from source failure. Full9 forecast conditioning requires accepted source plus complete target/forecast gates.'),indent=2)+'\n');print(json.dumps(rows))
if __name__=='__main__':main()
