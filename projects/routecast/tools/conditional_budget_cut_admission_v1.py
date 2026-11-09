"""Exact-premise admission and unit-node availability clauses for verified cuts."""
import json,hashlib
from pathlib import Path
from pre_route_endpoints import sha
class ContextMismatch(ValueError):pass

def outside_hash(occupancy):
 rows=[]
 for node,count in occupancy.items():
  if type(node) is not int or node<0 or type(count) is not int or count<0:raise ValueError('invalid unique-NET occupancy')
  if count:rows.append((node,count))
 return hashlib.sha256(json.dumps(sorted(rows),separators=(',',':')).encode()).hexdigest()

def verified_store(artifact,verification):
 artifact=Path(artifact).resolve();verification=Path(verification).resolve();proof=json.loads(verification.read_text())
 if proof.get('status')!='ALL3_BUDGET_RESOURCE_PATH_AND_BELLMAN_CERTIFICATES_INDEPENDENT_EXPAT_VERIFIED':raise ValueError('unverified cut artifact')
 if proof['bindings'].get(str(artifact))!=sha(artifact):raise ValueError('cut artifact binding mismatch')
 if not all(sha(p)==h for p,h in proof['bindings'].items()):raise ValueError('proof input changed')
 data=json.loads(artifact.read_text());assert data['status']=='PROOF_BOUND_NECESSARY_CONDITIONAL_RESOURCE_AVAILABILITY_CLAUSES'
 return tuple(data['clauses'])

def admit(clause,case,graph_sha256,query,outside):
 checks=dict(case=(clause['case'],case),graph=(clause['graph_sha256'],graph_sha256),connection=(clause['connection_id'],query['connection_id']),NET=(clause['NET'],query['net_id']),source=(clause['source'],query['source']),sink=(clause['sink'],query['sink']),budget=(clause['budget_integer'],query['budget_integer']),outside=(clause['outside_unique_NET_occupancy_sha256'],outside_hash(outside)))
 for name,(expected,actual) in checks.items():
  if type(expected) is not type(actual) or expected!=actual:raise ContextMismatch(name)
 return clause

def evaluate(clause,ownership,outside):
 target=clause['NET'];available=[];blocked={}
 for node in clause['conditional_budget_cut']:
  owners=sorted(net for net,nodes in ownership.items() if net!=target and node in nodes)
  if outside.get(node,0)==0 and not owners:available.append(node)
  else:blocked[node]=dict(outside_owners=outside.get(node,0),package_other_NETs=owners)
 return dict(satisfied=bool(available),available_nodes=available,blocked_nodes=blocked)
