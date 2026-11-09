"""Independent raw NET2 after-call support parsing of all fixed factorial arms."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prospective_external_family_full_rr_pressure_factorial_v1_2026-10-19';I=E/'prospective_external_family_early_net_observer_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def support(path):
 matches=[]
 for line in path.open():
  x=line.split()
  if x[:4]==['A','2','1','2']:matches.append({int(y.split(':')[0]) for y in x[6:]});assert len(matches[-1])==int(x[5])
 assert len(matches)==1;return matches[0]
def main():
 a=read(D/'verification.json');assert len(a['rows'])==12 and all(sha(p)==h for p,h in a['bindings'].items());source=support(I/'source/early_net_trace.tsv');seen=set();rows=[]
 for r in a['rows']:
  key=(r['case'],r['arm']);assert key not in seen;seen.add(key)
  if not r['native_success']:continue
  target=support(I/r['case']/'early_net_trace.tsv');current=support(D/r['case']/r['arm']/'native/early_net_trace.tsv');assert len(current^target)==r['NET2_after2_CHANNEL_diff_to_original'] and len(current^source)==r['NET2_after2_CHANNEL_diff_to_source'];rows.append(dict(case=r['case'],arm=r['arm'],diff_to_original=len(current^target),diff_to_source=len(current^source)))
 assert len(seen)==12
 with (D/'independent_support_verification_v1.json').open('x') as f:json.dump(dict(status='ALL12_FACTORIAL_IDENTITIES_AND_SUCCESSFUL_NET2_SUPPORT_DIFFERENCES_VERIFIED',rows=rows,bindings={str(D/'verification.json'):sha(D/'verification.json'),str(Path(__file__).resolve()):sha(__file__)},scope='Exact CHANNEL support differences, not causal necessity or forecast gate metrics.'),f,indent=2)
 print(json.dumps(rows))
if __name__=='__main__':main()
