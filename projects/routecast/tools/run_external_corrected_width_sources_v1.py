"""Fixed w096/w128 source availability audit under corrected native, original300limit."""
import json,sys,copy,hashlib,subprocess,concurrent.futures
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prospective_external_family_corrected_width_sources_v1_2026-10-19';N=E/'prospective_external_family_corrected_native_epoch_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 old=read(E/'prospective_external_family_native_case_manifest_v1_2026-10-19/manifest.json');source=read(N/'source_manifest.json')['cases'][0];build=R/'build/native_external_shared_sink_native_v1_2026-10-19/receipt.json';b=read(build);assert sha(b['binary'])==b['binary_sha256'];assert all(sha(k)==h for k,h in b['bindings'].items());D.mkdir(exist_ok=False);cases=[]
 for width in (96,128):
  c=copy.deepcopy(next(c for c in old['cases'] if c['case']==f'w{width:03d}/source'));cmd=source['command'].copy();cmd[cmd.index('--read_rr_graph')+1]=c['command'][c['command'].index('--read_rr_graph')+1];cmd[cmd.index('--route_chan_width')+1]=str(width);c.update(command=cmd,output=str(D/'native'/c['case']),role='corrected_native_source_availability_development');cases.append(c)
 old['cases']=cases;old['full_workflow_admitted']=True;old['scope']='Native source availability only, no complete-workflow timing';old['bindings'].update({str(build):sha(build),b['binary']:b['binary_sha256'],str(Path(__file__).resolve()):sha(__file__)})
 mp=D/'manifest.json';mp.write_text(json.dumps(old,indent=2)+'\n');(D/'protocol.json').write_text(json.dumps(dict(cases=cases,bindings={str(mp):sha(mp)},fixed_iterations=300,policy='Same corrected own-index/groupOR native binary as w160. Both widths fixed before results, no reruns/increased iteration limits/graph changes/width selection. Original unavailable6 retained; new source pass alone does not admit3 targets or full9. Complete physical/canonical gate mandatory; failures are algorithm/config failures, not unrouteability proofs.'),indent=2)+'\n')
 def run(c):
  out=Path(c['output']);out.parent.mkdir(parents=True,exist_ok=True)
  with (D/(c['case'].replace('/','_')+'.log')).open('x') as f:code=subprocess.run([sys.executable,str(R/'tools/run_external_native_route_case_v1.py'),str(mp),c['case']],cwd=R,stdout=f,stderr=subprocess.STDOUT).returncode
  p=out/'verification.json';v=read(p) if p.exists() else {};row=dict(case=c['case'],process_exit=code,status=v.get('status','MISSING_VERIFICATION'),error=v.get('error'),verification=str(p),iterations=v.get('iterations'),wirelength=v.get('wirelength'),cpd_ns=v.get('diagnostic_cpd_ns'));print(json.dumps(row),flush=True);return row
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(run,cases))
 (D/'terminal.json').write_text(json.dumps(dict(status='BOTH_FIXED_CORRECTED_NATIVE_WIDTH_SOURCE_PROCESSES_TERMINAL',rows=rows,original_unavailable6_replaced=False,full9_admitted=False),indent=2)+'\n')
if __name__=='__main__':main()
