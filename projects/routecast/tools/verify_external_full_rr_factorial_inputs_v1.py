"""Independent every-node factorial toggle checks against frozen native snapshots."""
import json,sys
from pathlib import Path
from collections import Counter
sys.path[:0]=[str(Path(__file__).resolve().parent),str(Path(__file__).resolve().parent/'native_resume_prototype')]
from pre_route_endpoints import sha
from verify_external_full_rr_frontier_v1 import load
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prospective_external_family_full_rr_pressure_factorial_v1_2026-10-19';I=E/'prospective_external_family_full_rr_frontier_observer_v1_2026-10-19';C=E/'prospective_external_family_net2_pressure_intervention_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 p=read(D/'protocol.json');assert all(sha(q)==h for q,h in p['bindings'].items());_,source,_=load(I/'source/rr_frontier.tsv');rows=[]
 for c in p['cases']:
  _,target,_=load(I/c['case']/'rr_frontier.tsv')
  for arm in c['arms']:
   seen=set();modified=Counter();chan_projection=[]
   for line in Path(arm['pressure']).open():
    n,expected,desired=map(int,line.split());assert n not in seen;seen.add(n);t=target[n];s=source[n];channel=t['type'] in ['CHANX','CHANY'];replace=arm['source_CHANNEL'] if channel else arm['source_nonCHANNEL'];assert expected==t['occupancy'] and desired==(s['occupancy'] if replace else t['occupancy']);
    if expected!=desired:modified[t['type']]+=1
    if channel:chan_projection.append((n,expected,desired))
   assert seen==target.keys() and len(seen)==p['nodes']==129090;assert sum(modified.values())==arm['modified_nodes']
   if not arm['source_nonCHANNEL']:
    oldarm='source_pressure' if arm['source_CHANNEL'] else 'own_pressure';old=[tuple(map(int,line.split())) for line in (C/c['case']/oldarm/'pressure.tsv').open()];assert chan_projection==old
   rows.append(dict(case=c['case'],arm=arm['arm'],nodes=len(seen),modified_by_type=dict(modified)))
 with (D/'independent_input_verification_v1.json').open('x') as f:json.dump(dict(status='ALL12_EVERY_RR_TOGGLE_AND_OLD_CHANNEL_PROJECTION_INPUTS_VERIFIED',rows=rows,bindings={str(D/'protocol.json'):sha(D/'protocol.json'),str(Path(__file__).resolve()):sha(__file__)}),f,indent=2)
 print('ALL12_FULL_RR_INPUTS_VERIFIED')
if __name__=='__main__':main()
