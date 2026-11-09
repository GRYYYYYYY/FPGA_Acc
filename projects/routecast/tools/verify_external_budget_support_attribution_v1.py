"""Independent token branch replay and native budget-path support partitions."""
import json,sys
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';P=E/'prospective_external_family_supplementary_development_v1_2026-10-19';B=E/'prospective_external_family_native_label_budget_compatibility_v1_2026-10-19';D=E/'prospective_external_family_budget_path_support_attribution_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 summary=read(D/'summary.json');assert all(sha(p)==h for p,h in summary['bindings'].items());protocol=read(D/'protocol.json');rows=[]
 for c,result in zip(protocol['cases'],summary['rows']):
  case=c['case'];s=read(c['specification']);ep=read(s['endpoint']);ids={json.loads(x)['id'] for x in (Path(s['domain_proof']).parent/'resources.jsonl').read_text().splitlines()};budget={r['connection_id']:r['over_budget'] for r in read(B/case/'all_CIDs.json')};lookup={(q['net_id'],q['source'],q['sink']):q['connection_id'] for q in ep['connections']};native=Counter();net=None;paths={};previous=None;source=None;seen_cids=set()
  for line in (P/'native'/case/'output.route').open():
   x=line.split()
   if x and x[0]=='Net':net=int(x[1]);paths={};source=None;previous=None
   elif x and x[0]=='Node:':
    n=int(x[1]);kind=x[2]
    if kind=='SOURCE':source=n;paths[n]=frozenset({n}&ids)
    elif kind=='SINK':
     cid=lookup[net,source,n];assert cid not in seen_cids;seen_cids.add(cid);bit=2 if budget[cid] else 1
     for node in paths[previous]|({n}&ids):native[node]|=bit
    elif n not in paths:paths[n]=paths[previous]|({n}&ids)
    previous=n
  assert seen_cids==budget.keys();counts=Counter();stats={m:{str(k):dict(resources=0,supported=0,missed=0) for k in (0,1,2,3)} for m in c['methods']};ledgers={m:{int(n):v for n,v in read(arm['frame'])['ledger'].items()} for m,arm in c['methods'].items()};seen=set()
  for line in (D/case/'all_resources.jsonl').open():
   r=json.loads(line);n=r['id'];assert n in ids and n not in seen;seen.add(n);mask=native[n];assert mask==r['budget_path_mask'];counts[mask]+=1
   for m,l in ledgers.items():
    value=l.get(n,0);assert r['counts'][m]==value;stat=stats[m][str(mask)];stat['resources']+=1;stat['supported']+=value>0;stat['missed']+=value==0
  assert seen==ids and len(seen)==45584;assert {str(k):v for k,v in counts.items()}==result['mask_counts'];assert stats==result['method_strata'];rows.append(dict(case=case,resources=len(seen),methods=len(ledgers)))
 with (D/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='ALL136752_BUDGET_SUPPORT_MASKS_AND18_METHOD_PARTITIONS_INDEPENDENTLY_VERIFIED',rows=rows,bindings={str(D/'summary.json'):sha(D/'summary.json'),str(Path(__file__).resolve()):sha(__file__)},scope='Independent branch membership and full-domain ledger joins. For mask0, table missed means unsupported/correct native absence, not false negative. Budget-over-only is observed path membership, not graph impossibility.'),f,indent=2)
 print('ALL136752_MASKS_AND18_PARTITIONS_VERIFIED')
if __name__=='__main__':main()
