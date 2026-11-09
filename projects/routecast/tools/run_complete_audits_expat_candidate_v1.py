"""Explicit one-reader substitution; all audit bodies and electrical reader unchanged."""
import json,runpy,sys
from pathlib import Path
from pre_route_endpoints import sha
from immutable_xml_expat_audit_v1 import ImmutableExpatAudit
import independent_audit_context_v1 as context
R=Path(__file__).resolve().parents[1];p=R/'experiments/immutable_expat_full_sha_contract_v1_2026-10-10/verification.json';v=json.loads(p.read_text());assert all(v['full_graph_equal'].values()) and v['original_verify_body_exact'] and all(sha(k)==h for k,h in v['bindings'].items());assert context.diagnostics()['context_loads']==0
context.ImmutableXMLAudit=ImmutableExpatAudit
sys.argv=[str(R/'tools/run_shared_actual_old_linear_direct_lattice_audits_v4.py'),*sys.argv[1:]]
runpy.run_path(sys.argv[0],run_name='__main__')
