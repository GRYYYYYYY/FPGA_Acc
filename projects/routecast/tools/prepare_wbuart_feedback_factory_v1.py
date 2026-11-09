"""Bind the qualified nominal model to all12 exact current endpoint epochs."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'experiments/wbuart_feedback_factory_v1_2026-10-20';E=R/'experiments';B=E/'wbuart_nominal_contexts_v1_2026-10-20';C=E/'wbuart_delay_components_v1_2026-10-20';T=E/'wbuart_frame_timings_v1_2026-10-20'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 O.mkdir(exist_ok=False);proof=E/'wbuart_constant_setup_model_contract_v1_2026-10-20/verification.json';v=json.loads(proof.read_text());assert v['passed'] and len(v['rows'])==36
 for n,h in v['bindings'].items():assert sha(Path(n))==h
 certified={}
 def collect(path):
  d=json.loads(path.read_text())
  for n,h in d.get('bindings',{}).items():assert sha(Path(n))==h;certified[n]=h
  return d
 collect(B/'edge_CID_verification_v1.json')
 for r in collect(B/'verification.json')['rows']:collect(Path(r['verification']))
 for r in collect(C/'verification.json')['rows']:collect(Path(r['verification']))
 timing=collect(T/'verification.json')
 for r in timing['rows']:collect(Path(r['timing_verification']))
 rows=[]
 for r in timing['rows']:
  case=r['case'];ep=Path(r['endpoint']);e=json.loads(ep.read_text());base=B/case;comp=C/case/'scaled/components_before.tsv';mapping=base/'external_edge_CID_bindings_v1.json';initial=T/case/'initial_connection_criticalities.json';paths=[comp,mapping,initial,*[base/n for n in ['timing_nodes.tsv','timing_edges.tsv','timing_atoms.tsv','clock_constraints.tsv']]]
  for p in paths:assert certified.get(str(p))==sha(p),str(p)
  graph=Path(e['inputs']['graph']['path']);assert sha(graph)==e['graph_sha256'];deps={str(p):sha(p) for p in [ep,graph,*paths]};rows.append({'case':case,'endpoint':str(ep),'endpoint_sha256':sha(ep),'graph_sha256':e['graph_sha256'],'baseline':str(base),'components':str(comp),'mapping':str(mapping),'initial':str(initial),'graph':str(graph),'bindings':deps})
 codes=[R/'tools'/n for n in ['wbuart_fixed_nominal_feedback_factory_v1.py','fixed_nominal_timing_feedback_constants_v3.py','nominal_component_timing_bridge_constants_v3.py','native_setup_reference_constants_v3.py','load_native_clock_constraints_v1.py','zero_rc_native_float_delay_v1.py','zero_rc_budget_certificate_graph_v1.py']]
 bindings={str(p):sha(p) for p in [Path(__file__),proof,B/'verification.json',B/'edge_CID_verification_v1.json',C/'verification.json',T/'verification.json',*codes]}
 manifest={'schema':'WBUART_FIXED_NOMINAL_FEEDBACK_FACTORY_V1','rows':rows,'bindings':bindings,'qualified_model':'All-node native setup tags and data float32 parity for36 fixed current-packing synthetic vectors; explicit wildcard constants with native first-level behavior.','scope':'Fixed nominal local components; RR path delays accumulated switch-by-switch float32. Not physical IPIN remap or current routed native STA, generic hold/timing, unseen-family, prediction quality or net gain.','complete_prediction_utility_workflow_admitted':False,'target_route_labels_generated':False};(O/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('WBUART_FACTORY_MANIFEST_BOUND',len(rows),flush=True)
if __name__=='__main__':main()
