"""Atomic serial full-cohort admission over an authenticated provided proof epoch."""
import json
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
from certified_budget_execution_gate_v2 import InvalidEvidence

def preflight_batch(authority_path,cases):
 if not cases:raise InvalidEvidence('Empty cohort')
 authority=Path(authority_path).resolve()
 paths={str(authority):authority};normalized=[]
 for case in cases:
  p=tuple(Path(case[k]).resolve() for k in ('admission','endpoints','budget'))
  normalized.append(p)
  for f in p:paths[str(f)]=f
 before={name:sha(p) for name,p in paths.items()}
 docs={name:json.loads(p.read_text()) for name,p in paths.items()}
 v=docs[str(authority)]
 if v.get('all_twelve_cases_independent_admission_pass') is not True:raise InvalidEvidence('Missing independent cohort verification')
 closure=dict(before)
 def bind(name,digest):
  if name in closure and closure[name]!=digest:raise InvalidEvidence('Conflicting evidence binding: '+name)
  closure[name]=digest
 for name,digest in v['bindings'].items():bind(name,digest)
 for ap,ep,bp in normalized:
  a=docs[str(ap)]
  if v['bindings'].get(str(ap))!=before[str(ap)]:raise InvalidEvidence('Admission not independently bound')
  for name,digest in a['bindings'].items():bind(name,digest)
  for p in (ep,bp):
   if a['bindings'].get(str(p))!=before[str(p)]:raise InvalidEvidence('Unbound current input')
 if any(sha(p)!=h for p,h in closure.items()):raise InvalidEvidence('Stale or changed proof epoch')
 decisions=[]
 for ap,ep,bp in normalized:
  a=docs[str(ap)];endpoints=docs[str(ep)];budget=docs[str(bp)]
  queries={q['connection_id']:q for q in endpoints['connections']};rows=a['rows']
  if len(queries)!=len(endpoints['connections']) or len(rows)!=len(queries) or {r['connection_id'] for r in rows}!=set(queries):raise InvalidEvidence('Incomplete or duplicate coverage')
  blockers=[]
  for r in rows:
   floor=F(r['minimum_seconds'])*10**9;limit=F(budget['budgets_ns'].get(str(r['connection_id']),budget['default_budget_ns']))
   if floor<0 or limit<0 or limit!=F(r['budget_ns']):raise InvalidEvidence('Invalid floor or budget')
   feasible=floor<=limit
   if r['relaxed_path_budget_feasible']!=feasible:raise InvalidEvidence('Incorrect admission arithmetic')
   if not feasible:blockers.append(dict(connection_id=r['connection_id'],minimum_ns=str(floor),budget_ns=str(limit),unavoidable_excess_ns=str(floor-limit)))
  if a['admitted']!=(not blockers):raise InvalidEvidence('Incorrect aggregate admission')
  decisions.append(dict(decision='SKIP_CERTIFIED_MODEL_INFEASIBLE' if blockers else 'CONTINUE_FULL_ROUTING_AND_ACCEPTANCE',run_candidate_pipeline=not blockers,connections=len(queries),blockers=blockers,bindings={str(p):before[str(p)] for p in (ap,authority,ep,bp)}))
 if any(sha(p)!=h for p,h in closure.items()):raise InvalidEvidence('Proof epoch changed during batch')
 return dict(decisions=decisions,bindings=closure,scope='One serial authenticated provided floor epoch; no persistent hash cache. All decisions published only after full closure reauthentication. Continue is not joint capacity/STA/HDL acceptance; prior proof generation excluded.')
