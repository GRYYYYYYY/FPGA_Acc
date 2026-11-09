"""Completion checker: original full prediction matches the frozen 429 paths."""
import json
from pathlib import Path
from pre_route_endpoints import sha

def run():
 b=Path('experiments/stereo_prospective_validation_2026-10-05');out=b/'global_minimum_bypass_impact';p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text())
 assert r['protocol_sha256']==sha(out/'protocol.json') and r['full_connections']==81610 and r['affected_network_connections']==429 and r['replaced']==5 and r['unchanged_full_connections']==81605 and not r['budget_gate_passed'] and not r['committed']
 assert all(sha(k)==v for k,v in p['inputs'].items()) and all(sha(out/'source'/n)==h for n,h in p['sources'].items())
 parent=b/'ordinary_additive_class_cache_prediction_undriven_v2_authenticated_host';pred=json.loads((parent/'prediction.json').read_text());original={x['connection_id']:x for x in pred['connections'] if x['net_id'] in {3861,17288}};assert len(original)==429
 reference_protocol=json.loads((b/'minimum_bypass_whole_net_diagnosis/protocol.json').read_text());snapshot_bindings={};count=0
 for net in (3861,17288):
  path=b/f'completed_high_fanout_snapshots/net_{net}.json';digest=sha(path);assert reference_protocol['inputs'][str(path)]==digest;snapshot_bindings[str(path)]=digest;snapshot=json.loads(path.read_text())
  for row in snapshot['connections']:
   x=original[row['connection_id']]
   assert all(x[k]==row[k] for k in ('connection_id','net_id','source','sink')) and x['physical_edge_ids']==snapshot['net_result']['result']['paths'][str(row['sink'])];count+=1
 assert count==429
 if (out/'completion.json').exists():raise ValueError('fresh completion required')
 result={'receipt_sha256':sha(out/'receipt.json'),'original_snapshot_bindings':snapshot_bindings,'all429_full_prediction_original_paths_exact':True,'baseline_global_overflow_units':r['baseline_global_overflow_units'],'diagnostic_global_overflow_units':r['diagnostic_global_overflow_units'],'introduced_or_increased_overflow_resources':sum(x['introduced_or_increased_overflow'] for x in r['changed_resource_effects']),'budget_gate_passed':False,'committed':False,'scope':'full baseline occupancy effect only; modified full paths not independently audited; no native/legal/free-pin certificate','checker_sha256':sha(__file__)}
 (out/'completion.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
if __name__=='__main__':run()
