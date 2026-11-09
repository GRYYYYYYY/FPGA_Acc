"""Proof-store admission for reverse-cut and exact terminal-domain certificates."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from conditional_budget_cut_admission_v1 import ContextMismatch,outside_hash,admit,evaluate
VERIFIED_FAMILIES={'BUDGET_RESOURCE_PATH_AND_BELLMAN_CERTIFICATES_INDEPENDENT_EXPAT_VERIFIED','ALL3_BUDGET_RESOURCE_PATH_AND_BELLMAN_CERTIFICATES_INDEPENDENT_EXPAT_VERIFIED','ALL_RELEVANT_NET_CID_TERMINAL_INGRESS_DOMAINS_EXACTLY_CERTIFIED'}
def verified_store(artifact,verification):
 artifact=Path(artifact).resolve();proof=json.loads(Path(verification).read_text())
 if proof.get('status') not in VERIFIED_FAMILIES:raise ValueError('unverified proof family')
 if proof['bindings'].get(str(artifact))!=sha(artifact):raise ValueError('cut artifact binding mismatch')
 if not all(sha(p)==h for p,h in proof['bindings'].items()):raise ValueError('proof input changed')
 data=json.loads(artifact.read_text())
 if data.get('status')!='PROOF_BOUND_NECESSARY_CONDITIONAL_RESOURCE_AVAILABILITY_CLAUSES':raise ValueError('clause schema')
 return tuple(data['clauses'])
