"""Bind validated timing inputs to one current placement episode."""
import json
from pathlib import Path
from fixed_nominal_timing_feedback_v2 import FixedNominalTimingFeedback
from zero_rc_budget_certificate_graph_v1 import load_graph
R=Path(__file__).resolve().parents[1];E=R/'experiments'
def create(endpoint):
 ep=Path(endpoint).resolve();data=json.loads(ep.read_text());case='/'.join(ep.parts[-3:-1]);base=E/'prospective_external_family_clock_constraints_v1_2026-10-19'/case;comp=E/'prospective_external_family_delay_components_v1_2026-10-19'/case/'scaled/components_before.tsv';mapping=E/'prospective_external_family_current_timing_graph_v1_2026-10-19'/case/'external_edge_CID_bindings_v1.json';initial=E/'prospective_external_family_frame_timings_v1_2026-10-19'/case/'initial_connection_criticalities.json';proof=E/'prospective_external_family_fixed_nominal_feedback_contract_v2_2026-10-19/verification.json'
 from pre_route_endpoints import sha
 p=json.loads(proof.read_text());assert all(sha(k)==v for k,v in p['bindings'].items())
 assert data['graph_sha256']==sha(data['inputs']['graph']['path'])
 sources=[comp,mapping,initial,proof,*base.glob('*.tsv')];bindings={str(p):sha(p) for p in sources}
 return FixedNominalTimingFeedback(base,comp,json.loads(mapping.read_text()),base/'timing_atoms.tsv',json.loads(initial.read_text()),load_graph(data['inputs']['graph']['path'])),bindings
