"""Independent full control artifact, counter and empty-scope coverage review."""
import json,hashlib,re
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 O=R/'experiments/mmc_preferred_hint_runtime_parity_v1_2026-10-19';terminal=O/'terminal.json'
 if not terminal.exists():
  rows=json.loads((O/'progress.json').read_text())['rows'];print('WAITING_CONTROLS',len(rows),'/9');return
 t=json.loads(terminal.read_text());assert t['status']=='ALL9_DISABLED_AND_EMPTY_HINT_RUNTIME_PARITY_PASS';plans=json.loads((O/'execution_protocol.json').read_text())['jobs'];assert len(plans)==len(t['rows'])==9
 results=[];bindings={}
 for plan,row in zip(plans,t['rows']):
  assert (plan['mode'],plan['case'],plan['arm'])==(row['mode'],row['case'],row['arm'])
  d=Path(plan['cwd']);ref=Path(plan['reference']);pairs={}
  for name in ['design.blif','design.net','design.place','output.route','design.net.post_routing','owner_trace.tsv','preload_state.bin','expiry_before.bin','expiry_after.bin']:
   a,b=sha(d/name),sha(ref/name);assert a==b,(plan,name);pairs[name]=a
  # Reference has same observer version in a separate, previously verified run.
  obs=R/f"experiments/mmc_first_hint_connection_work_v2_2026-10-19/{plan['case']}/{plan['arm']}/connection_trace.tsv"
  assert sha(d/'connection_trace.tsv')==sha(obs)
  text=(d/'native.log').read_text();reference=(ref/'native.log').read_text();pattern=r'Router Stats: total_nets_routed: (\d+) total_connections_routed: (\d+) total_heap_pushes: (\d+) total_heap_pops: (\d+)';stats=re.findall(pattern,text);assert len(stats)==1 and stats==re.findall(pattern,reference)
  scope=re.findall(r'ROUTECAST preferred NET query scopes=(\d+)',text)
  if plan['mode']=='enabled_empty':assert scope==[stats[0][0]],(scope,stats)
  else:assert not scope
  results.append({'mode':plan['mode'],'case':plan['case'],'arm':plan['arm'],'exact_artifacts':pairs,'exact_full_connection_trace':True,'native_work':list(map(int,stats[0])),'scope_count':int(scope[0]) if scope else 0,'scope_count_matches_rerouted_NET_operations':True if scope else None})
 for p in [terminal,O/'execution_protocol.json',Path(__file__).resolve()]:bindings[str(p)]=sha(p)
 (O/'independent_verification_v1.json').open('x').write(json.dumps({'status':'ALL9_FULL_ARTIFACT_CONNECTION_TRACE_NATIVE_WORK_AND_EMPTY_SCOPE_COVERAGE_PASS','rows':results,'bindings':bindings,'scope':'Disabled6/empty3 controls only; no preferred policy utility, timing closure or generalization claim.'},indent=2)+'\n');print('INDEPENDENT_ALL9_PASS')
if __name__=='__main__':main()
