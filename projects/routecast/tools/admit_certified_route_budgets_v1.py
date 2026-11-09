"""Complete-cohort budget admission against an authenticated relaxed-floor certificate."""
import argparse,json
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha

def admission(endpoints,budgets,floors,verification,protocol):
 assert verification['connections']==len(endpoints['connections'])
 assert floors['graph_sha256']==endpoints['graph_sha256']
 assert floors['scale']>0
 queries={q['connection_id']:q for q in endpoints['connections']}
 assert len(queries)==len(endpoints['connections'])==len(floors['rows'])
 assert {x['query']['connection_id'] for x in floors['rows']}==set(queries)
 assert all(sha(f)==h for f,h in protocol['inputs'].items())
 assert all(sha(x['path'])==x['sha256'] for x in endpoints['inputs'].values())
 assert all(sha(c['path'])==c['sha256'] for c in floors['certificates'])
 blockers=[];rows=[]
 for x in floors['rows']:
  q=x['query'];assert q==queries[q['connection_id']] and x['status']=='FOUND'
  value=Fraction(x['minimum_integer'],floors['scale']);limit=Fraction(budgets['budgets_ns'].get(str(q['connection_id']),budgets['default_budget_ns']))
  assert value>=0 and limit>=0
  row=dict(connection_id=q['connection_id'],minimum_seconds=str(value),budget_ns=str(limit),relaxed_path_budget_feasible=value*10**9<=limit)
  rows.append(row)
  if not row['relaxed_path_budget_feasible']:blockers.append(row)
 return dict(connections=len(queries),admitted=not blockers,decision='RELAXED_PATH_BUDGET_ADMISSIBLE' if not blockers else 'REJECT_CERTIFIED_MODEL_BUDGET_INFEASIBLE',blockers=blockers,rows=rows,scope='Admission only: individual relaxed path floors, not joint shared-tree/capacity/native timing feasibility. No query omission or budget adjustment.')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--endpoints',type=Path,required=True);p.add_argument('--budget',type=Path,required=True);p.add_argument('--floors',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 rp=a.floors/'receipt.json';vp=a.floors/'verification.json';pp=a.floors/'protocol.json';r,v,protocol=[json.loads(x.read_text()) for x in (rp,vp,pp)]
 assert sha(rp)==v['receipt_sha256'] and sha(pp)==r['protocol_sha256']
 bindings={str(x.resolve()):sha(x) for x in (a.endpoints,a.budget,rp,vp,pp,Path(__file__))}
 report=admission(json.loads(a.endpoints.read_text()),json.loads(a.budget.read_text()),r,v,protocol);report['bindings']={**protocol['inputs'],**bindings,**{c['path']:c['sha256'] for c in r['certificates']}}
 assert all(sha(f)==h for f,h in report['bindings'].items())
 with a.output.open('x') as out:out.write(json.dumps(report,indent=2)+'\n')
 print(report['decision'],'complete cohort',report['connections'],'blockers',len(report['blockers']))
