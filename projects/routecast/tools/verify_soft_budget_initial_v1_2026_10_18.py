"""Audit actual initialized soft policy before terminal candidate output exists."""
import sys,pathlib,json
R=pathlib.Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from independent_fraction_arc_context_v2 import load_context
from exact_rc_lattice_direct_pairs_v2 import exact_scale
from audit_soft_budget_seed_v1 import reconstruct

def main():
 case=sys.argv[1];folder=R/f'experiments/mmc_soft_budget_all_NET_v1_2026-10-18/{case}';p=json.loads((folder/'protocol.json').read_text());epfile=R/f'experiments/mmc_multiplacement_inputs_v1_2026-10-18/{case}/demand/endpoints.json';ep=json.loads(epfile.read_text());xml,ids,classes,switches,digest=load_context(pathlib.Path(ep['inputs']['graph']['path']),ep['graph_sha256']);scale,_=exact_scale(ids,classes,switches,xml.graph.edges);warm=pathlib.Path(p['warm_seed_proof']);w=json.loads(warm.read_text());original=warm.parent/'initial.json';assert w['bindings'][str(original)]==sha(original);expected,maximum=reconstruct(xml,ids,classes,switches,scale,json.loads(original.read_text()));actual=json.loads((folder/'initial.json').read_text());assert expected==actual and maximum==p['maximum_graph_increment'];assert actual['required_connections']==115572;assert all(r['budget_integer']>=r['answer']['delay'] for r in actual['records']);bindings={**closure([pathlib.Path(__file__)]),**{str(f):sha(f) for f in [folder/'initial.json',folder/'protocol.json',warm,original,epfile,pathlib.Path(ep['inputs']['graph']['path'])]}};result=dict(status='independent_original_XML_simple_path_cap_and_complete_initial_transform_pass',bindings=bindings,case=case,connections=115572,maximum_graph_increment=maximum,minimum_cap=min(r['budget_integer'] for r in actual['records']),maximum_cap=max(r['budget_integer'] for r in actual['records']),all_original_paths_ledgers_floors_epochs_retained=True,original_budget_gate_claimed=False,scope='Complete initial-state policy transformation only. Final paths and all event replay remain pending; no native timing or utility claim.');target=folder/'independent_initial_soft_policy_v1.json';target.write_text(json.dumps(result,indent=2)+'\n');print(case,result['status'],maximum,flush=True)
if __name__=='__main__':main()
