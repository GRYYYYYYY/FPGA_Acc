"""Exact nonpath record and narrowly declared protocol comparison.
Physical paths/ledgers are intentionally not equated; separate audits own them.
"""
import copy,json
POLICY='raw-only quotient A* reusing feedback graph; exact floors required, equal-cost paths may change'
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'))
def audit(candidate,baseline):
 def index(frame):
  rows=frame['records'];out={}
  for r in rows:
   cid=r['connection_id'];assert type(cid) is int and cid not in out;out[cid]=r
  return out
 a,b=index(candidate),index(baseline);assert a.keys()==b.keys();changed=0
 for cid in a:
  x,y=copy.deepcopy(a[cid]),copy.deepcopy(b[cid]);px=x['answer'].pop('physical_edge_ids');py=y['answer'].pop('physical_edge_ids')
  assert canonical(x)==canonical(y);changed+=px!=py
 return dict(connections=len(a),changed_equal_cost_initial_paths=changed,all_nonpath_record_fields_exactly_identical=True,initial_path_and_ledger_parity_claimed=False)
def protocol(candidate,baseline):
 assert set(candidate)==set(baseline)|{'initial_floor_policy'}
 assert candidate['initial_floor_policy']==POLICY
 for k in baseline:
  if k=='bindings':continue
  if k=='structural_objective':
   old=baseline[k];assert old.count('initial floor unchanged')==1
   assert candidate[k]==old.replace('initial floor unchanged','initial raw-only quotient floor engine')
  else:assert canonical(candidate[k])==canonical(baseline[k]),k
 return True
