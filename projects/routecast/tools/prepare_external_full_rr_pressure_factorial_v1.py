"""Freeze all3 full2x2 CHANNEL/nonCHANNEL pressure toggles before outcomes."""
import json,sys
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parent),str(Path(__file__).resolve().parent/'native_resume_prototype')]
from pre_route_endpoints import sha
from verify_external_full_rr_frontier_v1 import load
R=Path(__file__).resolve().parents[1];E=R/'experiments';I=E/'prospective_external_family_full_rr_frontier_observer_v1_2026-10-19';C=E/'prospective_external_family_full_rr_frontier_comparison_v1_2026-10-19';D=E/'prospective_external_family_full_rr_pressure_factorial_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 receipt=read(C/'independent_verification_v1.json');assert all(sha(p)==h for p,h in receipt['bindings'].items());comparison=read(C/'summary.json');assert all(sha(p)==h for p,h in comparison['bindings'].items());D.mkdir(exist_ok=False);source=I/'source/rr_frontier.tsv';_,old,_=load(source);bindings={str(source):sha(source),str(C/'independent_verification_v1.json'):sha(C/'independent_verification_v1.json'),str(C/'summary.json'):sha(C/'summary.json'),str(Path(__file__).resolve()):sha(__file__)};cases=[]
 for c in read(I/'target_manifest.json')['cases']:
  case=c['case'];path=I/case/'rr_frontier.tsv';_,new,_=load(path);assert old.keys()==new.keys();arms=[]
  for chan,non in [(False,False),(True,False),(False,True),(True,True)]:
   name=f'channel_{int(chan)}_nonchannel_{int(non)}';out=D/case/name;out.mkdir(parents=True);pp=out/'pressure.tsv';changed=0
   with pp.open('x') as f:
    for n in sorted(old):
     a,b=old[n],new[n];is_channel=a['type'] in ['CHANX','CHANY'];replace=chan if is_channel else non;expected=b['occupancy'];desired=a['occupancy'] if replace else expected;changed+=expected!=desired;f.write(f'{n}\t{expected}\t{desired}\n')
   bindings[str(pp)]=sha(pp);arms.append(dict(arm=name,source_CHANNEL=chan,source_nonCHANNEL=non,pressure=str(pp),modified_nodes=changed,native_output=str(out/'native')))
  bindings[str(path)]=sha(path);cases.append(dict(case=case,original_manifest_case=c,arms=arms))
 (D/'protocol.json').write_text(json.dumps(dict(status='ALL12_FULL_RR_PRESSURE_FACTORIAL_INPUTS_FROZEN',cases=cases,nodes=len(old),bindings=bindings,policy='Same round2 order1 NET2 native call, fixed2x2 source CHANNEL and source nonCHANNEL occupancy toggles. Every129090 node including zeros, target expected counts checked first; pressure offsets restored after call. Source/target other exported RR fields and NET2 boundary match, hidden router state not presumed equal. Own arm must preserve full traces/final native route before intervention arms. All3 retained, no coefficient or case selection, no final labels or predictor/native utility/time claims; original quality/full9/family/hardware gates unchanged. Source-pressure arrays are shadow cost controls, not jointly tree-consistent while active. Native guard full-domain adaptation and contracts pending.'),indent=2)+'\n');print('ALL12_FULL_RR_ARMS_FROZEN')
if __name__=='__main__':main()
