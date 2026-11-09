"""Frozen label-free deterministic singlepass atomic pair sketch application."""
import json,hashlib,sys
from pathlib import Path
from fractions import Fraction as F
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from criticality_net_admission_v1 import validate
from audit_structural_node_base_v1 import audit as audit_base
from shared_snapshot_group_plan_v1 import evaluate
E=R/'experiments'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def apply(case,output):
 out=Path(output);out.mkdir(parents=True,exist_ok=False);design=E/'wbuart_sparse_pair_application_design_v1_2026-10-20/protocol.json';P=E/'wbuart_sparse_pair_feasibility_v1_2026-10-20';v=read(P/'verification.json');assert all(sha(p)==h for p,h in read(design)['bindings'].items());c=next(c for c in v['rows'] if c['case']==case);bindings={str(p):sha(p) for p in [Path(__file__),R/'tools/shared_snapshot_group_plan_v1.py',design,P/'verification.json',P/'independent_verification_v1.json',Path(c['bank']),Path(c['pairs'])]};graph,digest,nodes,f,rc,queries=load_endpoints(Path(c['endpoint']));slots={e:i for i,e in enumerate(f['edge_ids'])};warmfile=Path(c['model_output'])/'initial.json';warm=read(warmfile);records=defaultdict(list);qs=defaultdict(list)
 for q in warm['records']:records[q['net_id']].append(q)
 for q in queries:qs[q['net_id']].append(q)
 ledger={int(n):x for n,x in warm['ledger'].items()};epochs={int(n):x for n,x in warm['epochs'].items()};timingfile=Path(c['model_output'])/'timing_round0.json';cr={q['connection_id']:F(q['criticality_numerator'],q['criticality_denominator']) for q in read(timingfile)['criticalities']};base=audit_base(graph,c['base_proof'],rc.scale);span={i:max(int(n.find('loc').get('xhigh'))-int(n.find('loc').get('xlow')),int(n.find('loc').get('yhigh'))-int(n.find('loc').get('ylow')))+1 for i,n in enumerate(nodes) if n.get('type') in ['CHANX','CHANY']}
 def descriptor(n,rs):
  a=validate(f,rc,slots,qs[n],rs);users={};raw=F(0)
  for q in rs:
   critical=cr[q['connection_id']];raw+=critical*a['delays'][q['connection_id']]
   for e in q['answer']['physical_edge_ids']:
    node=f['dest_ranks'][slots[e]];users[node]=max(users.get(node,F(0)),critical)
  return {'owned':a['owned'],'users':users,'weighted_raw':raw}
 desc={n:descriptor(n,rs) for n,rs in records.items()};bank=read(c['bank']);cdesc={b['id']:descriptor(b['net_id'],b['records']) for b in bank};pairs=[json.loads(x) for x in Path(c['pairs']).read_text().splitlines()];pairs.sort(key=lambda p:(F(p['objective_delta']),p['overflow_delta'],tuple(sorted(p['NETs'])),tuple(p['candidate_ids'])));used=set();events=[];original={q['connection_id']:q for q in warm['records']}
 for rank,pair in enumerate(pairs):
  ids=pair['candidate_ids'];ns=pair['NETs'];event={'rank':rank,'candidate_ids':ids,'NETs':ns}
  if used&set(ns):event['status']='SKIP_NET_ALREADY_USED';events.append(event);continue
  candidates={bank[i]['net_id']:bank[i]['records'] for i in ids}
  for rs in candidates.values():
   for q in rs:assert {k:v for k,v in q.items() if k!='answer'}=={k:v for k,v in original[q['connection_id']].items() if k!='answer'}
  plan=evaluate(f['capacities'],ledger,{n:desc[n] for n in ns},{bank[i]['net_id']:cdesc[i] for i in ids},base,{},span,rc.scale//20000000000);strict=plan['objective_delta']<0 or plan['overflow_delta']<0;commit=plan['accepted'] and strict;event.update(status='COMMITTED' if commit else 'RETAIN_NO_STRICT_PROGRESS' if plan['accepted'] else plan['status'],old_score=str(plan['old_score']),candidate_score=str(plan['candidate_score']),objective_delta=str(plan['objective_delta']),overflow_delta=plan['overflow_delta'])
  if commit:
   for node,count in plan['updates'].items():
    if count:ledger[node]=count
    else:ledger.pop(node,None)
   for i in ids:
    n=bank[i]['net_id'];records[n]=bank[i]['records'];desc[n]=cdesc[i];epochs[n]+=1
   used.update(ns)
  events.append(event)
 full=Counter(n for d in desc.values() for n in d['owned']);assert dict(full)==ledger;allrecords=sorted([q for rs in records.values() for q in rs],key=lambda q:q['connection_id']);independent=Counter(n for q in allrecords for n in ({q['source']}|{f['dest_ranks'][slots[e]] for e in q['answer']['physical_edge_ids']}));state=dict(warm,records=allrecords,ledger=ledger,epochs=epochs,independent_connection_ledger=dict(independent),overflow_units=sum(max(0,x-f['capacities'][n]) for n,x in ledger.items()),overflow_nodes=sum(x>f['capacities'][n] for n,x in ledger.items()),eligible_for_legal_route_commit=False,status='COMPLETE_PAIR_DEMAND_SKETCH');(out/'initial.json').write_text(json.dumps(warm)+'\n');(out/'sketch.json').write_text(json.dumps(state)+'\n');(out/'events.json').write_text(json.dumps(events)+'\n')
 for p in [Path(c['endpoint']),Path(c['base_proof']),warmfile,timingfile,*list(out.glob('*.json'))]:bindings[str(p)]=sha(p)
 (out/'receipt.json').write_text(json.dumps({'case':case,'input_case':c,'fixed_order_count':len(pairs),'committed_groups':sum(e['status']=='COMMITTED' for e in events),'used_NETs':sorted(used),'bindings':bindings},indent=2)+'\n');print(case,'committed_groups',sum(e['status']=='COMMITTED' for e in events),flush=True)
if __name__=='__main__':apply(sys.argv[1],sys.argv[2])
