"""All6 fixed canonical analysis replay with atom mapping; byte report parity required."""
import json,hashlib,os,shutil,subprocess,concurrent.futures
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'experiments/prospective_external_family_native_seed_delay_handoff_v1_2026-10-19';D=R/'experiments/prospective_external_family_final_atom_mapping_v1_2026-10-19';B=R/'build/native_external_final_atom_mapping_v1_2026-10-19'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 receipt=read(B/'receipt.json');assert sha(receipt['binary'])==receipt['binary_sha256'];assert all(sha(k)==h for k,h in receipt['bindings'].items());proof=read(P/'verification.json');assert all(sha(k)==h for k,h in proof['bindings'].items());D.mkdir(exist_ok=False)
 bindings={str(P/'verification.json'):sha(P/'verification.json'),str(B/'receipt.json'):sha(B/'receipt.json'),str(Path(__file__).resolve()):sha(__file__)};cases=[]
 for i in (1,2,3):
  for arm in ('cold','seed'):
   case=f'w160/episode_{i:02d}/{arm}';src=P/case/'native_canonical';cmd=read(P/case/'native/verification.json')['canonical']['command'].copy();cmd[0]=receipt['binary'];cases.append(dict(case=case,source=str(src),command=cmd))
   for name in ('design.blif','design.net','design.place','design.route','report_timing.setup.rpt','report_timing.hold.rpt','design.net.post_routing'):bindings[str(src/name)]=sha(src/name)
 (D/'protocol.json').write_text(json.dumps(dict(cases=cases,bindings=bindings,scope='Analysis-only replay, not reroute. Require all6 report and packed net byte parity, original canonical route immutable. Mapping captured after sync.'),indent=2)+'\n')
 def run(c):
  out=D/c['case'];out.mkdir(parents=True);src=Path(c['source'])
  for name in ('design.blif','design.net','design.place','design.route'):shutil.copyfile(src/name,out/name)
  env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env['ROUTECAST_FINAL_ATOM_MAPPING']=str(out/'atom_mapping.tsv')
  with (out/'analysis.log').open('x') as log:code=subprocess.run(c['command'],cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
  parity={n:(out/n).exists() and sha(src/n)==sha(out/n) for n in ('report_timing.setup.rpt','report_timing.hold.rpt','design.net.post_routing','design.route')};r=dict(case=c['case'],exit_code=code,mapping_exists=(out/'atom_mapping.tsv').exists(),byte_parity=parity);print(json.dumps(r),flush=True);return r
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,cases))
 assert all(sha(k)==h for k,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(status='ALL6_CANONICAL_MAPPING_ANALYSIS_TERMINAL',all6_parity_pass=all(r['exit_code']==0 and r['mapping_exists'] and all(r['byte_parity'].values()) for r in rows),rows=rows,bindings=bindings),indent=2)+'\n')
if __name__=='__main__':main()
