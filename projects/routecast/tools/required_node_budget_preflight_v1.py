"""Authenticated negative admission; absence of a certificate never admits."""
import json
from pathlib import Path
from pre_route_endpoints import sha
class EvidenceMismatch(ValueError):pass
def batch_preflight(verification_path,expected_verification_sha256,requests):
 path=Path(verification_path)
 if sha(path)!=expected_verification_sha256:raise EvidenceMismatch('verification artifact changed')
 verification=json.loads(path.read_text());bindings=dict(verification['bindings'])
 receipt_path=path.parent/'receipt.json'
 if str(receipt_path) not in bindings:raise EvidenceMismatch('receipt not bound')
 receipt=json.loads(receipt_path.read_text());bindings.update(receipt['bindings'])
 if not all(sha(p)==h for p,h in bindings.items()):raise EvidenceMismatch('certificate authority changed')
 result=[];seen=set()
 for request in requests:
  step=request['step']
  if step in seen or type(step)is not int or not 0<=step<4:raise EvidenceMismatch('invalid/duplicate step')
  seen.add(step);ep=Path(request['endpoints']);bp=Path(request['budgets'])
  for p in (ep,bp):
   if str(p) not in bindings or sha(p)!=bindings[str(p)]:raise EvidenceMismatch('unbound current input')
  meta=json.loads(ep.read_text());budgets=json.loads(bp.read_text());queries={q['connection_id']:q for q in meta['connections']}
  if len(queries)!=len(meta['connections']) or {b['connection_id'] for b in budgets}!=set(queries) or len(budgets)!=len(queries):raise EvidenceMismatch('input coverage mismatch')
  if not all(sha(x['path'])==x['sha256'] for x in meta['inputs'].values()):raise EvidenceMismatch('endpoint input changed')
  evidence=receipt_path.parent/f'step_{step}.json'
  if str(evidence) not in bindings:raise EvidenceMismatch('step certificate unbound')
  v=json.loads(evidence.read_text());certs={}
  for c in v['certificates']:
   cid=c['connection_id'];q=queries.get(cid)
   if q is None or q['net_id']!=c['net_id']:raise EvidenceMismatch('certificate endpoint identity mismatch')
   certs.setdefault(c['blocked_node'],set()).add(c['net_id'])
  # Bind requests to the actual archived step paths, not another step's input.
  root=receipt_path.parents[2]
  actual_ep=root/'experiments/adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json' if step==0 else root/f'experiments/adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json'
  actual_bp=root/f'experiments/adder_tree_online_move_rc_budgets_2026-10-06/step_{step}_budgets.json'
  if ep.resolve()!=actual_ep.resolve() or bp.resolve()!=actual_bp.resolve():raise EvidenceMismatch('request step differs from evidence')
  conflicts=[c for c in v['conflicts'] if len(certs.get(c['node'],set()))>c['capacity']]
  verified=verification['rows'][step]
  if verified['step']!=step or not verified['joint_original_model_budgets_infeasible'] or not conflicts:raise EvidenceMismatch('no independently verified negative decision')
  result.append(dict(step=step,decision='REJECT_CERTIFIED_MODEL_BUDGET_CAPACITY_CONFLICT',fallback='DIRECT_COLD_WITH_MODEL_BUDGET_FAILURES_REPORTED',conflicts=conflicts,scope='Archived additive RC model budgets only; no user-clock/STA infeasibility claim. Fallback proposed, not executed.'))
 if sha(path)!=expected_verification_sha256 or not all(sha(p)==h for p,h in bindings.items()):raise EvidenceMismatch('evidence changed during batch')
 return result
