"""Frozen native namespace rejection probes, admitted only after nine controls."""
from pathlib import Path
import json,hashlib,subprocess,resource,os,shutil
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def save(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def main():
 parity=R/'experiments/mmc_preferred_hint_runtime_parity_v1_2026-10-19';proof=parity/'independent_verification_v1.json';assert json.loads(proof.read_text())['status']=='ALL9_FULL_ARTIFACT_CONNECTION_TRACE_NATIVE_WORK_AND_EMPTY_SCOPE_COVERAGE_PASS'
 fixture=R/'experiments/mmc_preferred_native_import_fault_protocol_v1_2026-10-19/protocol.json';spec=json.loads(fixture.read_text());plans=json.loads((parity/'execution_protocol.json').read_text())['jobs'];base=next(x for x in plans if x['mode']=='disabled' and x['case']=='episode_01' and x['arm']=='forecast');O=R/'experiments/mmc_preferred_native_import_faults_v1_2026-10-19';O.mkdir(exist_ok=False)
 binary=Path(base['argv'][0]);receipt=json.loads((binary.parent/'receipt.json').read_text());assert sha(binary)==receipt['binary_sha256'];bindings={str(p):sha(p) for p in [proof,fixture,binary,Path(__file__).resolve()]};jobs=[]
 expected={'wrong_graph':'schema/graph mismatch','wrong_NET_name':'owner identity/order/ignored','wrong_hint_bits':'claim context mismatch','truncated_last_claim':'truncated claims'}
 for fault in spec['cases']:
  file=Path(fault['path']);assert sha(file)==fault['sha256'];bindings[str(file)]=sha(file);d=O/fault['fault'];env={k:(str(d/Path(v).name) if base['cwd'] in v else v) for k,v in base['environment_set'].items()};env['ROUTECAST_PREFERRED_NET_CLAIMS']=str(file);jobs.append({'fault':fault['fault'],'cwd':str(d),'argv':base['argv'],'env':env,'expected_error':expected[fault['fault']]})
 save(O/'execution_protocol.json',{'jobs':jobs,'bindings':bindings,'scope':'Native strict import rejection only; no policy routing or utility accepted.'});rows=[]
 for job in jobs:
  d=Path(job['cwd']);d.mkdir()
  for name in ['design.blif','design.net','design.place']:shutil.copyfile(Path(base['reference'])/name,d/name)
  env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env.update(job['env'])
  def limits():resource.setrlimit(resource.RLIMIT_CORE,(0,0));resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30))
  with (d/'native.log').open('x') as f:
   child=subprocess.Popen(job['argv'],cwd=d,env=env,stdout=f,stderr=subprocess.STDOUT,preexec_fn=limits);save(O/'live_process.json',{'fault':job['fault'],'pid':child.pid,'startticks':Path(f'/proc/{child.pid}/stat').read_text().rsplit(')',1)[1].split()[19]});code=child.wait()
  text=(d/'native.log').read_text();absent=['output.route','design.net.post_routing','owner_trace.tsv','preload_state.bin','expiry_before.bin','expiry_after.bin','connection_trace.tsv'];ok=code!=0 and job['expected_error'] in text and all(not (d/name).exists() for name in absent) and 'ROUTECAST initial excess preload entries=' not in text and 'VPR succeeded' not in text
  rows.append({'fault':job['fault'],'returncode':code,'expected_error_found':job['expected_error'] in text,'all_post_import_artifacts_absent':all(not (d/name).exists() for name in absent),'passed':ok,'log_sha256':sha(d/'native.log')});save(O/'progress.json',{'rows':rows});print('IMPORT_FAULT',job['fault'],'PASS' if ok else 'FAIL',flush=True)
  if not ok:save(O/'terminal.json',{'status':'FAULT_REJECTION_TEST_FAILED','rows':rows});raise RuntimeError('Native import fault not admitted')
 save(O/'terminal.json',{'status':'ALL4_NATIVE_IMPORT_FAULTS_REJECTED_BEFORE_PRELOAD_OUTPUT','rows':rows,'scope':'Observed rejection before preload write/dump site; not a direct memory snapshot of rejected process.'})
if __name__=='__main__':main()
