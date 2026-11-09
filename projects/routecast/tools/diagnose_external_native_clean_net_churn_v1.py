"""Full native-route owner churn split by endpoint edit class; diagnostic only."""
import json,sys,re
from pathlib import Path
from collections import Counter,defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];O=R/'experiments/prospective_external_family_temporal_owner_turnover_v1_2026-10-19';P=R/'experiments/prospective_external_family_temporal_prior_errors_v1_2026-10-19';D=R/'experiments/prospective_external_family_native_clean_net_churn_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 a=read(O/'verification.json');assert all(sha(p)==h for p,h in a['bindings'].items());cases=read(O/'protocol.json')['cases'];D.mkdir(exist_ok=False);bindings={str(O/'verification.json'):sha(O/'verification.json'),str(Path(__file__).resolve()):sha(__file__)};rows=[]
 (D/'protocol.json').write_text(json.dumps(dict(cases=cases,policy='All native NET support changes split by target endpoint edits; native route is diagnosis only, never inference input. Include every resource and clock in full-ledger route audit, then original dataNET/CHANNEL metric universe. Global occupancy transitions use disjoint old-owner/new-owner class masks, not summed NET changes.'),indent=2)+'\n')
 for c in cases:
  s=read(c['original_comparison_spec']);proof=read(s['label_proof']);assert all(sha(p)==h for p,h in proof['bindings'].items());physical=read(s['label_physical_audit']);route=Path(s['label_physical_audit']).parent/'output.route';assert sha(route)==physical['inputs_sha256']['route']==proof['bindings'][str(route)];unions={};net=None;printed=0
  for line in route.read_text().splitlines():
   words=line.split()
   if words and words[0]=='Net':
    net=int(words[1]) if line.rstrip().endswith(')') else None
    if net is not None:assert net not in unions;unions[net]=set()
   elif words and words[0]=='Node:':
    assert net is not None;unions[net].add(int(words[1]));printed+=1
  ledger=Counter(n for ns in unions.values() for n in ns);assert dict(ledger)=={int(n):v for n,v in physical['node_occupancy'].items()};assert printed==physical['printed_nodes']
  masks=[json.loads(x) for x in (O/c['case']/'owner_masks.jsonl').read_text().splitlines()];ids={x['id'] for x in masks};prior=defaultdict(set)
  for r in masks:
   for net in r['old_owners']:prior[net].add(r['id'])
  netdata=read(P/c['case']/'NETs.json');classes={r['net_id']:int(r['edit_mask']!=0) for r in netdata};assert classes.keys()<=unions.keys();target={net:unions[net]&ids for net in classes};stats=defaultdict(Counter);netrows=[];finalowners=defaultdict(set)
  for net in sorted(classes):
   old,new=prior[net],target[net];kind='edited' if classes[net] else 'clean';r=dict(net_id=net,kind=kind,changed_support=old!=new,removed=len(old-new),added=len(new-old),retained=len(old&new));netrows.append(r);stats[kind].update(NETs=1,changed_NETs=int(old!=new),removed=r['removed'],added=r['added'],retained=r['retained'])
   for n in new:finalowners[n].add(net)
  transitions=Counter();resources=[]
  for r in masks:
   n=r['id'];old=set(r['old_owners']);new=finalowners[n];om=sum(1<<k for k in {classes[x] for x in old});nm=sum(1<<k for k in {classes[x] for x in new});transitions[(bool(old),bool(new),om,nm)]+=1;resources.append(dict(id=n,prior_owners=sorted(old),final_owners=sorted(new),prior_class_mask=om,final_class_mask=nm))
  out=D/c['case'];out.mkdir(parents=True);(out/'NETs.json').write_text(json.dumps(netrows,indent=2)+'\n')
  with (out/'resources.jsonl').open('x') as f:
   for r in resources:f.write(json.dumps(r)+'\n')
  row=dict(case=c['case'],NET_class_stats={k:dict(v) for k,v in stats.items()},resource_transitions=[dict(prior=p,final=t,prior_class_mask=om,final_class_mask=nm,count=count) for (p,t,om,nm),count in sorted(transitions.items())],full_native_ledger_and_printed_nodes_verified=True);rows.append(row)
  for path in [route,Path(s['label_proof']),Path(s['label_physical_audit']),out/'NETs.json',out/'resources.jsonl',O/c['case']/'owner_masks.jsonl',P/c['case']/'NETs.json']:bindings[str(path)]=sha(path)
  print(c['case'],row['NET_class_stats'],flush=True)
 assert all(sha(p)==h for p,h in bindings.items());(D/'summary.json').write_text(json.dumps(dict(status='ALL3_NATIVE_FULL_LEDGER_AUDITED_AND_CLEAN_EDITED_NET_CHURN_PARTITIONED',rows=rows,bindings=bindings,scope='Observed cold-route churn only, not proof of causality, required reroute, or useful predictor. Native result never inference input.'),indent=2)+'\n')
if __name__=='__main__':main()
