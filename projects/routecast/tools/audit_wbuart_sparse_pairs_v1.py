"""Label-free local compensation pairs from original2round complete candidates."""
import json,hashlib,sys
from pathlib import Path
from fractions import Fraction as F
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from criticality_net_admission_v1 import validate
from shared_snapshot_group_plan_v1 import evaluate
from audit_structural_node_base_v1 import audit as audit_base
E=R/'experiments';D=E/'wbuart_sparse_pair_feasibility_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);design=E/'wbuart_sparse_pair_design_v1_2026-10-20/protocol.json';contract=E/'shared_snapshot_group_contract_v2_2026-10-20/verification.json';forecast=E/'wbuart_forecasts_v1_2026-10-20/verification.json';manifest=E/'wbuart_forecasts_v1_2026-10-20/manifest.json';bindings={str(p):sha(p) for p in [Path(__file__),design,contract,forecast,manifest,R/'tools/shared_snapshot_group_plan_v1.py']};rows=[]
 for c in read(manifest)['cases']:
  arm=next(a for r in read(forecast)['rows'] if r['case']==c['case'] for a in r['arms'] if a['initializer']=='native_retained' and a['timing_policy']=='warm_timing_round_updated');out=Path(arm['output']);proof=read(out/'complete_event_audit.json');assert all(sha(p)==h for p,h in proof['bindings'].items());graph,digest,nodes,fields,rc,queries=load_endpoints(Path(c['endpoint']));slots={e:i for i,e in enumerate(fields['edge_ids'])};groups=defaultdict(list)
  for q in queries:groups[q['net_id']].append(q)
  warm=read(out/'initial.json');ledger={int(n):v for n,v in warm['ledger'].items()};oldrecords=defaultdict(list)
  for q in warm['records']:oldrecords[q['net_id']].append(q)
  criticality={q['connection_id']:F(q['criticality_numerator'],q['criticality_denominator']) for q in read(out/'timing_round0.json')['criticalities']};base=audit_base(graph,c['node_base_proof'],rc.scale);span={i:max(int(n.find('loc').get('xhigh'))-int(n.find('loc').get('xlow')),int(n.find('loc').get('yhigh'))-int(n.find('loc').get('ylow')))+1 for i,n in enumerate(nodes) if n.get('type') in ['CHANX','CHANY']};weight=rc.scale//20000000000
  def descriptor(net,records):
   audit=validate(fields,rc,slots,groups[net],records);users={};raw=F(0)
   for q in records:
    original=next(x for x in oldrecords[net] if x['connection_id']==q['connection_id']);assert {k:v for k,v in q.items() if k!='answer'}=={k:v for k,v in original.items() if k!='answer'};cr=criticality[q['connection_id']];raw+=cr*audit['delays'][q['connection_id']]
    for e in q['answer']['physical_edge_ids']:
     n=fields['dest_ranks'][slots[e]];users[n]=max(users.get(n,F(0)),cr)
   return {'owned':audit['owned'],'users':users,'weighted_raw':raw}
  old={n:descriptor(n,r) for n,r in oldrecords.items()};bank=[];seen=set()
  for rnd in read(out/'receipt.json')['rounds']:
   for index,event in enumerate(rnd['events']):
    for key in ['records','rejected_records']:
     if key not in event:continue
     net=event['net_id'];records=event[key];signature=(net,tuple(sorted((q['connection_id'],tuple(q['answer']['physical_edge_ids'])) for q in records)))
     if signature in seen:continue
     seen.add(signature);desc=descriptor(net,records)
     if records==oldrecords[net]:continue
     added=set(desc['owned'])-set(old[net]['owned']);removed=set(old[net]['owned'])-set(desc['owned']);single=evaluate(fields['capacities'],ledger,{net:old[net]},{net:desc},base,{},span,weight);bank.append({'id':len(bank),'net_id':net,'records':records,'desc':desc,'added':added,'removed':removed,'single_overflow_delta':single['overflow_delta'],'origin':{'round':rnd['round_index'],'index':index,'key':key}})
  adders=defaultdict(set);removers=defaultdict(set)
  for b in bank:
   for n in b['added']:adders[n].add(b['id'])
   for n in b['removed']:removers[n].add(b['id'])
  pairs=set()
  for n in adders.keys()&removers.keys():
   for i in adders[n]:
    for j in removers[n]:
     if i==j or bank[i]['net_id']==bank[j]['net_id']:continue
     if bank[i]['single_overflow_delta']<=0 and bank[j]['single_overflow_delta']<=0:continue
     pairs.add(tuple(sorted((i,j))))
  folder=D/c['case'];folder.mkdir(parents=True);payload=folder/'pairs.jsonl';counts=Counter();admitted=[]
  with payload.open('x') as f:
   for i,j in sorted(pairs):
    a,b=bank[i],bank[j];ns=[a['net_id'],b['net_id']];plan=evaluate(fields['capacities'],ledger,{n:old[n] for n in ns},{a['net_id']:a['desc'],b['net_id']:b['desc']},base,{},span,weight);row={'candidate_ids':[i,j],'NETs':ns,'accepted':plan['accepted'],'overflow_delta':plan['overflow_delta'],'objective_delta':str(plan['objective_delta']),'status':plan['status']};f.write(json.dumps(row)+'\n');counts[plan['status']]+=1
    if plan['accepted']:admitted.append(row)
  bp=folder/'bank.json';bp.write_text(json.dumps([{k:sorted(v) if isinstance(v,set) else v for k,v in b.items() if k!='desc'} for b in bank])+'\n');row={'case':c['case'],'endpoint':c['endpoint'],'base_proof':c['node_base_proof'],'model_output':str(out),'bank':str(bp),'pairs':str(payload),'candidates':len(bank),'sparse_pairs':len(pairs),'status_counts':dict(counts),'admitted_pairs':admitted};rows.append(row);print(c['case'],len(bank),len(pairs),dict(counts),flush=True)
  for p in [bp,payload,out/'complete_event_audit.json',Path(c['endpoint']),Path(c['node_base_proof'])]:bindings[str(p)]=sha(p)
 assert len(rows)==9
 (D/'verification.json').write_text(json.dumps({'status':'ALL9_LABEL_FREE_FIRST2ROUND_CANDIDATE_PAIRS_PHYSICALLY_ADMITTED_AND_ENUMERATED','rows':rows,'bindings':bindings,'scope':'Fixed warm snapshot, original2round candidate bank only, local add/remove compensation subset. No native target trees/quality labels read for selection. No actual commit, quality test, optimality/global-pair completeness or net-gain claim; independent sparse-domain and positive-witness checks pending.'},indent=2)+'\n')
if __name__=='__main__':main()
