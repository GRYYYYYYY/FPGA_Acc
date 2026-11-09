"""Independent regex route/owner set reconstruction of churn partitions."""
import json,re,sys
from pathlib import Path
from collections import defaultdict,Counter
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/prospective_external_family_native_clean_net_churn_v1_2026-10-19';O=R/'experiments/prospective_external_family_temporal_owner_turnover_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 summary=read(D/'summary.json');assert all(sha(p)==h for p,h in summary['bindings'].items());rows=[]
 for c,published in zip(read(D/'protocol.json')['cases'],summary['rows']):
  spec=read(c['original_comparison_spec']);route=Path(spec['label_physical_audit']).parent/'output.route';text=route.read_text();native={}
  for block in re.split(r'^Net ',text,flags=re.M)[1:]:
   header,*body=block.splitlines();m=re.fullmatch(r'(\d+) \(.*\)',header.strip())
   if m:native[int(m[1])]={int(n) for n in re.findall(r'^Node:\s+(\d+)', '\n'.join(body),flags=re.M)}
  led=Counter(n for ns in native.values() for n in ns);assert dict(led)=={int(n):v for n,v in read(spec['label_physical_audit'])['node_occupancy'].items()}
  records=read(D/c['case']/'NETs.json');classes={r['net_id']:r['kind']=='edited' for r in records};prior=defaultdict(set);owners={}
  for line in (O/c['case']/'owner_masks.jsonl').read_text().splitlines():
   r=json.loads(line);owners[r['id']]=set(r['old_owners'])
   for net in r['old_owners']:prior[net].add(r['id'])
  stats=defaultdict(Counter);finalowners=defaultdict(set)
  for r in records:
   net=r['net_id'];a,b=prior[net],native[net]&owners.keys();assert (r['changed_support'],r['removed'],r['added'],r['retained'])==(a!=b,len(a-b),len(b-a),len(a&b));stats[r['kind']].update(NETs=1,changed_NETs=int(a!=b),removed=len(a-b),added=len(b-a),retained=len(a&b))
   for n in b:finalowners[n].add(net)
  assert {k:dict(v) for k,v in stats.items()}==published['NET_class_stats'];counts=Counter();seen=set()
  for line in (D/c['case']/'resources.jsonl').read_text().splitlines():
   r=json.loads(line);n=r['id'];assert n not in seen;seen.add(n);assert set(r['prior_owners'])==owners[n] and set(r['final_owners'])==finalowners[n];a,b=[sum(1<<k for k in {int(classes[x]) for x in ns}) for ns in [owners[n],finalowners[n]]];assert (a,b)==(r['prior_class_mask'],r['final_class_mask']);counts[(bool(a),bool(b),a,b)]+=1
  assert seen==owners.keys() and len(seen)==45584;expected={(r['prior'],r['final'],r['prior_class_mask'],r['final_class_mask']):r['count'] for r in published['resource_transitions']};assert counts==expected;rows.append(dict(case=c['case'],NETs=len(records),resources=len(seen)))
 with (D/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='ALL3_NATIVE_NET_SUPPORT_CHURN_AND136752_DISJOINT_RESOURCE_PARTITIONS_VERIFIED',rows=rows,bindings={str(D/'summary.json'):sha(D/'summary.json'),str(Path(__file__).resolve()):sha(__file__)},scope='Independent route parser and set identities. Clean/edited class labels inherited from prior endpoint-audited table. No causal or inference claim.'),f,indent=2)
 print('ALL3_CHURN_PARTITIONS_INDEPENDENTLY_VERIFIED')
if __name__=='__main__':main()
