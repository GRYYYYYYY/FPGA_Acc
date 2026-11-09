"""Independent raw record transpose and printed-route target reconstruction."""
import json,subprocess
from pathlib import Path
from pre_route_endpoints import sha
from verify_prince_ownership_ledger_v2 import owner_payload
from evaluate_prince_ready_owner_forecast_v1 import final_owners
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_competitive_support_v1_2026-10-20';S=E/'prince_competitive_frontier_trial_v1_2026-10-20';B=R/'build/prince_competitive_support_audit_v1_2026-10-20/extract'
def load(p):return json.loads(Path(p).read_text())
def main():
 frozen=load(D/'frozen_inputs.json');v=load(D/'verification.json');by={r['case']:r for r in v['rows']};qf={r['case']:r for r in load(E/'prince_causal_query_frontier_v1_2026-10-20/frozen_inputs.json')['rows']};bindings={str(p):sha(p) for p in [D/'frozen_inputs.json',D/'verification.json',B,R/'tools/extract_prince_competitive_support_v1.cpp',Path(__file__)]};checked=records=0;rows=[]
 for row in frozen['rows']:
  if row['status']!='COMPETITIVE_SUPPORT_FROZEN_NO_LABELS':continue
  c=row['case'];t=row['ready_iteration'];src=S/c/'capture';cp=subprocess.run([str(B),str(src/'frontier.bin'),str(t)],capture_output=True,text=True);assert cp.returncode==0,cp.stderr;actual={tuple(map(int,fields[:3])):list(map(int,fields[3:])) for fields in map(str.split,cp.stdout.splitlines())};saved={};supports={'raw':{},'preheap':{},'pop':{}}
  for i,path in row['paths'].items():
   i=int(i);a=list(map(json.loads,Path(path).open()))
   for x in a:saved[i,x['net'],x['node']]=[x['preheap_accepted'],x['valid_pop']]
   supports['preheap'][i]={(x['net'],x['node']) for x in a if x['preheap_accepted']};supports['pop'][i]={(x['net'],x['node']) for x in a if x['valid_pop']};supports['raw'][i]={(x['net'],x['node']) for x in map(json.loads,Path(qf[c]['paths'][str(i)]).open())}
  assert saved==actual;records+=len(actual);it,ready=owner_payload(src/'owners'/f'owners_{t}.bin');assert it==t;truth=final_owners(src/'output.route');rp={(net,n) for net,ns in ready.items() for n in ns};fp={(net,n) for net,ns in truth.items() for n in ns};new=fp-rp;rn={n for net,n in rp};arrivals={n for net,n in new if n not in rn};expected=by[c];assert expected['new_final_owner_pairs']==len(new) and expected['global_arrivals']==len(arrivals)
  def verify(s,m):
   nonlocal checked
   eligible=s-rp;nodes={n for net,n in eligible if n not in rn};a,b=len(eligible&new),len(nodes&arrivals);result=dict(new_pair_candidates=len(eligible),true_new_final_pairs=a,new_pair_precision=a/len(eligible) if eligible else None,new_pair_recall=a/len(new),global_arrival_candidates=len(nodes),true_global_arrivals=b,global_arrival_precision=b/len(nodes) if nodes else None,global_arrival_recall=b/len(arrivals));assert result==m;checked+=1
  for mode,phases in [('ready',[t]),('two_phase_union',[t-1,t])]:
   ss={name:set().union(*(support[i] for i in phases)) for name,support in supports.items()}
   for name,s in ss.items():verify(s,expected['methods'][mode][name])
   for name,other in [('preheap','pop'),('pop','preheap'),('preheap','raw'),('pop','raw')]:
    m=dict(expected['differences'][mode][f'{name}_minus_{other}']);assert m.pop('total_pairs')==len(ss[name]-ss[other]);verify(ss[name]-ss[other],m)
  rows.append(dict(case=c,input_phase_NET_node_records=len(actual)));print('INDEPENDENT_COMPETITIVE_SUPPORT_PASS',c,len(actual),flush=True)
 assert len(rows)==6 and checked==84 and len(v['rows'])==9
 with (D/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='RAW_RECORD_COUNTS_AND84_PRINTED_ROUTE_SUPPORT_SUMMARIES_RECONCILED',input_phase_NET_node_records=records,verified_summaries=checked,rows=rows,bindings=bindings,scope='Independent full-record C++ parser matches Python offset extraction. Independent native-owner/printed-route set differences and exact counts reconcile primary inverse/terminal-ledger labels. Diagnostic only,not original metric admission.'),f,indent=2);f.write('\n')
if __name__=='__main__':main()
