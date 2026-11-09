"""Independent sequential before/after owner replay to round2 NET2 boundary."""
import json,sys
from pathlib import Path
from collections import defaultdict,Counter
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';I=E/'prospective_external_family_early_net_observer_v1_2026-10-19';D=E/'prospective_external_family_net85_net2_pressure_handoff_v2_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def replay(path):
 state=defaultdict(set);owners=defaultdict(set);first=None;observed={}
 for line in path.open():
  x=line.split();kind=x[0];it,order,net=map(int,x[1:4])
  if kind=='C':continue
  ns={int(t.split(':')[0]) for t in x[6:]}
  if it==2 and first is None:first={n:set(v) for n,v in owners.items()}
  if it==2 and net==2 and kind=='B':
   for t in x[6:]:
    n,occ,acc,pres=t.split(':');n=int(n);assert len(owners[n])==int(occ);observed[n]=(int(occ),float(acc),float(pres))
   return first,{n:set(v) for n,v in owners.items()},observed
  if kind=='B':assert ns==state[net]
  else:
   for n in state[net]-ns:owners[n].remove(net)
   for n in ns-state[net]:owners[n].add(net)
   state[net]=ns
 raise AssertionError('missing NET2 boundary')

def main():
 receipt=read(D/'verification.json');assert all(sha(p)==h for p,h in receipt['bindings'].items());source=read(I/'manifest.json')['cases'][0];old_endpoint=read(source['endpoint']);old={q['connection_id']:q for q in old_endpoint['connections']};a0,a,obs_a=replay(I/'source/early_net_trace.tsv');cases={c['case']:c for c in read(I/'target_manifest.json')['cases']};results=[]
 for r in receipt['rows']:
  c=cases[r['case']];b0,b,obs_b=replay(I/c['case']/'early_net_trace.tsv');assert obs_a.keys()==obs_b.keys();edited=set()
  for q in read(c['endpoint'])['connections']:
   p=old[q['connection_id']]
   if (q['source'],q['sink'])!=(p['source'],p['sink']):edited.add(q['net_id'])
  expected=a0.keys()|a.keys()|b0.keys()|b.keys();seen=set();changed=[]
  for line in (D/c['case']/'all_resource_owner_deltas.jsonl').read_text().splitlines():
   x=json.loads(line);n=x['id'];assert n not in seen;seen.add(n);aa=a.get(n,set());bb=b.get(n,set());aa0=a0.get(n,set());bb0=b0.get(n,set());assert (set(x['source_owners']),set(x['target_owners']),set(x['source_first_owners']),set(x['target_first_owners']))==(aa,bb,aa0,bb0);delta=len(bb)-len(aa);old85=int(85 in bb0)-int(85 in aa0);now85=int(85 in bb)-int(85 in aa);otherE=sum((z in bb)-(z in aa) for z in (aa|bb)-{85} if z in edited);otherC=sum((z in bb)-(z in aa) for z in (aa|bb)-{85} if z not in edited);assert [x[k] for k in ['occupancy_delta','prior_round_delta','NET85_prior_delta','NET85_current_delta','NET85_step_delta','other_edited_delta','other_clean_delta']]==[delta,len(bb0)-len(aa0),old85,now85,now85-old85,otherE,otherC];assert delta==now85+otherE+otherC;assert x['on_NET2_prior_support']==(n in obs_a)
   if n in obs_a:assert obs_b[n][0]-obs_a[n][0]==delta
   if n in obs_a and delta:changed.append(x)
  assert seen==expected and len(seen)==r['all_observed_CHANNEL_resources'];assert changed==r['changed_NET2_rows'];assert len(changed)==r['NET2_occupancy_changed_resources'];results.append(dict(case=c['case'],resources=len(seen),changed_NET2_resources=len(changed)))
 with (D/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='ALL3_SEQUENTIAL_OWNER_REPLAY_ENDPOINT_EDIT_CLASSES_AND_SIGNED_DECOMPOSITION_VERIFIED',rows=results,bindings={str(D/'verification.json'):sha(D/'verification.json'),str(Path(__file__).resolve()):sha(__file__)}),f,indent=2)
 print('ALL3_HANDOFF_DECOMPOSITIONS_VERIFIED')
if __name__=='__main__':main()
