"""Independent quadratic sparse-domain check and full-state positive witnesses."""
import json,hashlib,sys
from pathlib import Path
from fractions import Fraction as F
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from criticality_net_admission_v1 import validate
from array import array
E=R/'experiments';D=E/'wbuart_sparse_pair_feasibility_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=D/'verification.json';v=read(p);assert all(sha(n)==h for n,h in v['bindings'].items());rows=[]
 for c in v['rows']:
  graph,digest,nodes,f,rc,queries=load_endpoints(Path(c['endpoint']));slots={e:i for i,e in enumerate(f['edge_ids'])};out=Path(c['model_output']);warm=read(out/'initial.json');ledger={int(n):x for n,x in warm['ledger'].items()};old=defaultdict(list);qs=defaultdict(list)
  for q in warm['records']:old[q['net_id']].append(q)
  for q in queries:qs[q['net_id']].append(q)
  criticalities={q['connection_id']:F(q['criticality_numerator'],q['criticality_denominator']) for q in read(out/'timing_round0.json')['criticalities']};base=array('Q');base.frombytes((Path(c['base_proof']).parent/'node_base.u64').read_bytes());spans={i:max(int(n.find('loc').get('xhigh'))-int(n.find('loc').get('xlow')),int(n.find('loc').get('yhigh'))-int(n.find('loc').get('ylow')))+1 for i,n in enumerate(nodes) if n.get('type') in ['CHANX','CHANY']}
  def owned(records):return {q['source'] for q in records}|{f['dest_ranks'][slots[e]] for q in records for e in q['answer']['physical_edge_ids']}
  oldnodes={n:owned(rs) for n,rs in old.items()};bank=read(c['bank']);initial_over=sum(max(0,x-f['capacities'][n]) for n,x in ledger.items())
  for b in bank:
   n=b['net_id'];validated=validate(f,rc,slots,qs[n],b['records']);b['nodes']=set(validated['owned']);assert set(b['added'])==b['nodes']-oldnodes[n] and set(b['removed'])==oldnodes[n]-b['nodes'];b['addset']=set(b['added']);b['remset']=set(b['removed']);delta=sum(max(0,ledger.get(k,0)+int(k in b['nodes'])-int(k in oldnodes[n])-f['capacities'][k])-max(0,ledger.get(k,0)-f['capacities'][k]) for k in b['nodes']^oldnodes[n]);assert delta==b['single_overflow_delta']
  expected=set()
  for i,a in enumerate(bank):
   for j in range(i+1,len(bank)):
    b=bank[j]
    if a['net_id']!=b['net_id'] and max(a['single_overflow_delta'],b['single_overflow_delta'])>0 and (a['addset']&b['remset'] or b['addset']&a['remset']):expected.add((i,j))
  records=[json.loads(l) for l in Path(c['pairs']).read_text().splitlines()];observed={tuple(x['candidate_ids']) for x in records};assert observed==expected and len(records)==len(observed)==c['sparse_pairs'];assert dict(Counter(x['status'] for x in records))==c['status_counts'];positive=[x for x in records if x['accepted']];assert positive==c['admitted_pairs'];strict=0
  for row in positive:
   a,b=[bank[i] for i in row['candidate_ids']];selection={a['net_id']:a,b['net_id']:b};rebuilt=Counter(n for net in old for n in (selection[net]['nodes'] if net in selection else oldnodes[net]));after=sum(max(0,x-f['capacities'][n]) for n,x in rebuilt.items());assert after-initial_over==row['overflow_delta']<=0;released=Counter(k for n in selection for k in oldnodes[n])
   def score(trees):
    value=F(0)
    for rs in trees:
     maximum={}
     for q in rs:
      cr=criticalities[q['connection_id']];value+=cr*rc.path(q['source'],q['sink'],q['answer']['physical_edge_ids'])
      for e in q['answer']['physical_edge_ids']:
       n=f['dest_ranks'][slots[e]];maximum[n]=max(maximum.get(n,F(0)),cr)
     for n,cr in maximum.items():
      other=ledger.get(n,0)-released[n];assert other>=0;cost=base[n]*(1+max(0,other-f['capacities'][n]+1))+(rc.scale//20000000000)*spans.get(n,0);value+=(1-cr)*cost
    return value
   delta=score([a['records'],b['records']])-score([old[n] for n in selection]);assert delta==F(row['objective_delta'])<=0;strict+=delta<0 or row['overflow_delta']<0
  rows.append({'case':c['case'],'bank_candidates':len(bank),'sparse_pairs':len(expected),'admitted_pairs':len(positive),'pairs_with_strict_objective_or_overflow_progress':strict,'all_sparse_domain_and_positive_witnesses_verified':True});print(rows[-1],flush=True)
 assert len(rows)==9
 (D/'independent_verification_v1.json').write_text(json.dumps({'status':'ALL9_SPARSE_DOMAINS_AND_POSITIVE_JOINT_FULL_STATE_OBJECTIVE_WITNESSES_VERIFIED','rows':rows,'bindings':{str(p):sha(p),str(Path(__file__)):sha(__file__)},'scope':'Independent all-pairs declared-domain enumeration and full uniqueNET-ledger/manual Fraction objective for every admitted witness. Negative objective decisions not independently rescored; no quality, legal complete route, sequential application or net-gain claim.'},indent=2)+'\n');print('ALL9_SPARSE_DOMAINS_AND_POSITIVE_JOINT_FULL_STATE_OBJECTIVE_WITNESSES_VERIFIED')
if __name__=='__main__':main()
