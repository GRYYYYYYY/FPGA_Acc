"""Read-only prior native analysis with direct setup-slack export, no target labels."""
import pathlib,json,hashlib,shutil,subprocess,os,time,re,resource
R=pathlib.Path(__file__).resolve().parents[1];O=R/'experiments/mmc_prior_setup_slack_export_v1_2026-10-19'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 O.mkdir(exist_ok=False);build=R/'build/native_prior_setup_slack_export_v2_2026-10-19/receipt.json';b=json.loads(build.read_text());assert b['status']=='PRIVATE_NATIVE_SETUP_SLACK_EXPORT_BUILT';binary=pathlib.Path(b['binary']);assert sha(binary)==b['binary_sha256'];C=R/'experiments/ultraembedded_mmc_limited_expat_workflow_v16_2026-10-10/cold/canonical';cp=C/'receipt.json';old=json.loads(cp.read_text())['rows'][0]['canonical'];source=C/'mmc';cmd=old['command'].copy();cmd[0]=str(binary);assert '--analysis' in cmd and '--route' not in cmd;bindings={str(p):sha(p) for p in [build,binary,cp,pathlib.Path(__file__).resolve()]}
 for name in ['design.blif','design.net','design.place','design.route']:
  p=source/name;shutil.copyfile(p,O/name);bindings[str(p)]=sha(p);assert sha(O/name)==sha(p)
 for p,h in b['bindings'].items():assert sha(pathlib.Path(p))==h
 (O/'protocol.json').write_text(json.dumps(dict(bindings=bindings,command=cmd,policy='Exact archived prior-source canonical analysis, no routing. Export native calculate_clb_net_pin_setup_slack and underlying atom setup_pin_slack in seconds plus exact float32 bits. No slack inversion from criticality and no automatic budget policy.',expected_CPD_ns=old['cpd_ns'],expected_native_wirelength=661370,target_native_labels_used=False,scope='Known old-source layout only; fresh prior timing instrumentation. Finite nonclock slack remains a local diagnostic, not jointly allocatable global timing margin or budget acceptance.'),indent=2)+'\n');env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};start=time.perf_counter()
 def limit():resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3))
 with (O/'native.log').open('x') as log:code=subprocess.call(cmd,cwd=O,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limit)
 text=(O/'native.log').read_text();cpd=re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text);wire=re.findall(r'Total wirelength:\s*(\d+)',text);m=re.findall(r'Found (\d+) mismatches',text);fix=re.findall(r'Fixed (\d+) routing traces',text);out=dict(status='PRIOR_NATIVE_SLACK_EXPORT_TERMINAL',exit_code=code,native_seconds=time.perf_counter()-start,CPD_ns=float(cpd[-1]) if cpd else None,wirelength=int(wire[-1]) if wire else None,full_pass='Completed routing consistency check successfully.' in text,vpr_success='VPR succeeded' in text,mismatches=int(m[-1]) if m else None,fixups=int(fix[-1]) if fix else None,original_zero_counter_gate=False,source_route_bytes_identical=(O/'design.route').read_bytes()==(source/'design.route').read_bytes(),source_packed_post_bytes_identical=(O/'design.net.post_routing').exists() and (O/'design.net').read_bytes()==(O/'design.net.post_routing').read_bytes(),bindings={**bindings,**{str(p):sha(p) for p in O.iterdir() if p.is_file()}},scope='Export production only, per-connection identity and slack/float accounting independently pending; no moved-endpoint timing budget admitted.')
 (O/'receipt.json').write_text(json.dumps(out,indent=2)+'\n');print({k:v for k,v in out.items() if k not in ['bindings','scope']},flush=True);assert code==0 and out['full_pass'] and out['CPD_ns']==old['cpd_ns'] and out['wirelength']==661370
if __name__=='__main__':main()
