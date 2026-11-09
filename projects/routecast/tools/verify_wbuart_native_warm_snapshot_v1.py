"""Check manual rescoring against actual physical/RC/objective admission code."""
import json,hashlib,sys
from pathlib import Path
from fractions import Fraction
from collections import defaultdict
from array import array
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from criticality_objective_admission_v1 import prepare,score
E=R/'experiments';D=E/'wbuart_native_warm_snapshot_rescore_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=D/'verification.json';v=read(p);assert all(sha(n)==h for n,h in v['bindings'].items());rows=[];total=0
 for case in v['rows']:
  graph,digest,nodes,f,rc,queries=load_endpoints(Path(case['endpoint']));warm=read(case['warm_frame']);old={q['connection_id']:q for q in warm['records']};ledger={int(n):x for n,x in warm['ledger'].items()};cr={q['connection_id']:q for q in read(case['timing_frame'])['criticalities']};base=array('Q');base.frombytes((Path(case['base_proof']).parent/'node_base.u64').read_bytes());slots={eid:i for i,eid in enumerate(f['edge_ids'])};groups=defaultdict(list)
  for q in queries:groups[q['net_id']].append(q)
  span={i:max(int(n.find('loc').get('xhigh'))-int(n.find('loc').get('xlow')),int(n.find('loc').get('yhigh'))-int(n.find('loc').get('ylow')))+1 for i,n in enumerate(nodes) if n.get('type') in ['CHANX','CHANY']};count=0
  for row in read(case['payload']):
   qs=groups[row['net_id']];a=[old[q['connection_id']] for q in qs];b=row['native_records'];owned={q['source'] for q in a}|{f['dest_ranks'][slots[e]] for q in a for e in q['answer']['physical_edge_ids']}
   class Costs:
    def get(self,n,default=0):
     other=ledger.get(n,0)-int(n in owned);return base[n]*(1+max(0,other-f['capacities'][n]+1))+(rc.scale//20000000000)*span.get(n,0)
   costs=Costs();ad={q['connection_id']:rc.path(q['source'],q['sink'],q['answer']['physical_edge_ids']) for q in a};bd={q['connection_id']:rc.path(q['source'],q['sink'],q['answer']['physical_edge_ids']) for q in b};assert all(bd[q['connection_id']]==q['answer']['delay'] for q in b);before,after=score(f,slots,a,cr,costs,ad),score(f,slots,b,cr,costs,bd);assert Fraction(row['old_score'])==before and Fraction(row['native_target_score'])==after and Fraction(row['objective_delta'])==after-before;bad={q['connection_id'] for q in b if bd[q['connection_id']]>q['budget_integer']};assert bad==set(row['budget_violating_CIDs'])
   if bad:
    try:prepare(f,rc,slots,qs,a,b,ledger,cr,costs)
    except ValueError as exc:assert 'budget' in str(exc)
    else:raise AssertionError('budget incompatible target admitted')
    assert row['status']=='BUDGET_INCOMPATIBLE'
   else:
    actual=prepare(f,rc,slots,qs,a,b,ledger,cr,costs);assert actual['objective_delta']==after-before and actual['prospective_overflow_delta']==row['overflow_delta'];assert actual['accepted']==(row['status']=='REFERENCE_ADMISSIBLE')
   count+=1
  assert count==1074;total+=count;rows.append({'case':case['case'],'NETs':count,'original_RC_objective_and_actual_admission_checked':True})
 assert len(rows)==9 and total==9666
 (D/'implementation_crosscheck_v1.json').write_text(json.dumps({'status':'ALL9666_WARM_REFERENCE_SCORES_CHECKED_AGAINST_ACTUAL_ADMISSION_IMPLEMENTATION','rows':rows,'bindings':{str(p):sha(p),str(Path(__file__)):sha(__file__)},'scope':'Independent manual formula cross-check against actual RC/score/admission implementation. Shared compact graph context, no global optimality or joint-state admission claim.'},indent=2)+'\n');print('ALL9666_WARM_REFERENCE_SCORES_CHECKED_AGAINST_ACTUAL_ADMISSION_IMPLEMENTATION')
if __name__=='__main__':main()
