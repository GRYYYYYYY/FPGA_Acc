"""Compare completed hash-bound Koios controls without changing metric rules.
Requires both full prediction and evaluator receipts; never launches workers.
"""
import argparse,json
from pathlib import Path
from pre_route_endpoints import sha

def load_evidence(prediction,evaluation):
 p=json.loads((prediction/'protocol.json').read_text())
 r=json.loads((prediction/'receipt.json').read_text())
 ep=json.loads((evaluation/'protocol.json').read_text())
 er=json.loads((evaluation/'receipt.json').read_text())
 if r['protocol_sha256']!=sha(prediction/'protocol.json') or er['protocol_sha256']!=sha(evaluation/'protocol.json'):raise ValueError('protocol identity mismatch')
 if not r['audit']['all_physical_and_union_checks_passed'] or r['audit']['requested']!=15138 or not er['exact_full15138_native_endpoint_multiset']:raise ValueError('full physical/endpoint audits required')
 for name,digest in r['outputs'].items():
  if sha(prediction/name)!=digest:raise ValueError('prediction output changed')
 for entry in ep['inputs'].values():
  if sha(entry['path'])!=entry['sha256']:raise ValueError('evaluation input changed')
 # Bind evaluated paths to this exact predictor, not merely valid unrelated files.
 for name in ['prediction','endpoints']:
  entry=ep['inputs'][name];expected=prediction/(name+'.json')
  if Path(entry['path']).resolve()!=expected.resolve() or entry['sha256']!=r['outputs'][name+'.json']:raise ValueError('evaluation is bound to another predictor')
 if ep['inputs']['graph']!=p['inputs']['rr_graph.xml']:raise ValueError('evaluated graph differs from predictor graph')
 if not r.get('inputs_unchanged') or not er.get('inputs_unchanged'):raise ValueError('immutable input audit required')
 if er['reports']['failed_connections']!=r['failed_connections']:raise ValueError('failure count mismatch')
 for name,digest in ep['source_sha256'].items():
  if sha(evaluation/'source'/name)!=digest:raise ValueError('archived evaluator source changed')
 if sha(evaluation/'spatial_maps.json')!=er['spatial_maps_sha256']:raise ValueError('spatial output changed')
 return p,r,ep,er

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);a=parser.parse_args()
 roots=[('rc',Path('experiments/koios_cpp_resume_2026-10-05'),Path('experiments/koios_cpp_resume_evaluation_2026-10-05')),('length_switch',Path('experiments/koios_length_switch_full_2026-10-05'),Path('experiments/koios_length_switch_evaluation_2026-10-05'))]
 rows={name:load_evidence(p,e) for name,p,e in roots}
 rc=rows['rc'];control=rows['length_switch']
 for name in ['rr_graph.xml','endpoints']:
  if rc[0]['inputs'][name]!=control[0]['inputs'][name]:raise ValueError('predictor cohort/graph differs')
 if rc[0]['binary_sha256']!=control[0]['binary_sha256']:raise ValueError('search executable differs')
 if rc[2]['inputs']['native']!=control[2]['inputs']['native']:raise ValueError('native truth differs')
 deltas={}
 for domain in ['resource','spatial']:
  x=rc[3]['reports'][domain];y=control[3]['reports'][domain]
  for k in ['universe_size','k','top_k_tie_rule','nonzero_truth','truth_k_boundary']:
   if x[k]!=y[k]:raise ValueError('metric domain/rule differs: '+k)
  deltas[domain]={k:None if x[k] is None or y[k] is None else x[k]-y[k] for k in ['spearman','precision_at_k','recall_at_k','mae']}
 if a.output.exists():raise ValueError('fresh output required')
 result={'reports':{name:e[3]['reports'] for name,e in rows.items()},'rc_minus_length_switch':deltas,'evidence_sha256':{name:{'prediction_receipt':sha(p/'receipt.json'),'evaluation_receipt':sha(e/'receipt.json')} for name,p,e in roots},'scope':'matched single Koios design/seed final occupancy comparison; no family-generalization/nativeQoR/feedback/acceleration claim'}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(deltas))

if __name__=='__main__':main()
