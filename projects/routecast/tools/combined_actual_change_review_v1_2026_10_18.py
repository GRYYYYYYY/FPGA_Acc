"""Compose physical and budget diagnostics; never publishes accepted state."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from actual_change_budget_recheck_v1_2026_10_18 import BudgetRecheck,mapped_paths,authenticate
from actual_change_physical_delta_v1_2026_10_18 import PhysicalDelta
from stream_native_route_audit_unified_v1 import audit

class CombinedReview:
 def __init__(self,endpoint,route,inventory,memo):
  self.endpoint=Path(endpoint);self.endpoint_sha=sha(endpoint)
  meta=json.loads(self.endpoint.read_text());authenticate(meta)
  self.inventory=inventory;self.memo=memo
  if inventory.digest!=memo.digest or meta['graph_sha256']!=inventory.digest:raise ValueError('Epoch mismatch')
  self.graph=Path(meta['inputs']['graph']['path']);self.route=Path(route);self.route_sha=sha(route)
  self.old_full=audit(self.graph,route,inventory)
  if self.old_full['overflow_units']:raise ValueError('Infeasible previous physical state')
  self.budget=BudgetRecheck(meta,route,memo)
  self.physical=PhysicalDelta(mapped_paths(meta,route),{q['connection_id']:q for q in meta['connections']},inventory)
  if dict(self.physical.occupancy)!={int(n):v for n,v in self.old_full['node_occupancy'].items()}:raise ValueError('Old printed/terminal union mismatch')
  if sha(endpoint)!=self.endpoint_sha or sha(route)!=self.route_sha:raise ValueError('Initial state changed')
 def evaluate(self,endpoint,route,budget_file):
  if sha(self.endpoint)!=self.endpoint_sha or sha(self.route)!=self.route_sha:raise ValueError('Stale previous state')
  inputs={str(Path(p)):sha(p) for p in [endpoint,route,budget_file]}
  meta=json.loads(Path(endpoint).read_text());budget=json.loads(Path(budget_file).read_text());authenticate(meta)
  full=audit(self.graph,route,self.inventory)
  b=self.budget.evaluate(meta,route,budget,self.memo)
  p=self.physical.evaluate(mapped_paths(meta,route),{q['connection_id']:q for q in meta['connections']},self.inventory)
  if full['node_occupancy']!=p['node_occupancy'] or full['overflow_units']!=p['overflow_units']:raise ValueError('Printed/terminal union mismatch')
  authenticate(meta)
  if any(sha(k)!=v for k,v in inputs.items()) or sha(self.endpoint)!=self.endpoint_sha or sha(self.route)!=self.route_sha:raise ValueError('State changed during review')
  return dict(inputs_sha256=inputs,budget=b,physical_delta=p,full_printed_audit=full,canonical_gate='MISSING_NOT_EVALUATED',accepted=False,decision='REJECT_ORIGINAL_BUDGET' if b['violation_ids'] else 'REJECT_CAPACITY' if p['overflow_units'] else 'PENDING_CANONICAL_AND_NATIVE_ACCEPTANCE',scope='Composed diagnostics only; canonical pins/native FULL/STA and publication transaction are not implemented here.')
