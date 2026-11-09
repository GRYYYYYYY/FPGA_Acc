"""Symmetric context/cold policy proof and descriptive stage/work attribution."""
import sys,json
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from native_route_work_metrics import extract
R=Path(__file__).resolve().parents[2];s=R/'experiments/native_resume_shared_cold_adder_2026-10-07';seq=json.loads((s/'receipt.json').read_text());rows=[];bindings={str(Path(__file__)):sha(Path(__file__)),str(s/'receipt.json'):sha(s/'receipt.json')};stage_totals={'workflow':Counter(),'cold':Counter()};native_totals={'workflow':Counter(),'cold':Counter()}
for i in range(1,10):
 work=[]
 for mode in ('workflow','cold'):
  b=R/f'experiments/native_resume_shared_cold_adder_step{i}_{mode}_2026-10-07';r=json.loads((b/'receipt.json').read_text());p=json.loads((b/'protocol.json').read_text());assert r['protocol_sha256']==sha(b/'protocol.json');bindings[str(b/'receipt.json')]=sha(b/'receipt.json')
  for stage in r['stages']:stage_totals[mode][stage['stage']]+=stage['seconds']
  metric=extract((b/'first/run.log').read_text());assert metric['native_vpr_succeeded'] and metric['routing_success'];work.append(metric)
  for k in ('iterations','heap_pushes','rerouted_connection_attempts'):native_totals[mode][k]+=metric[k]
  if mode=='cold':assert r['feedback'] is None and not (b/'first_seed.route').exists() and not (b/'exchange').exists() and not any('previous' in k or k.endswith('design.route') for k in p['inputs'])
 wf=R/f'experiments/native_resume_shared_cold_adder_step{i}_workflow_2026-10-07/rr_floors.txt';cold=R/f'experiments/native_resume_shared_cold_adder_step{i}_cold_2026-10-07/rr_floors.txt';assert wf.read_bytes()==cold.read_bytes()
 a=json.loads((s/f'floor_context/epoch_{i}/receipt.json').read_text());b=json.loads((s/f'cold_floor_context/epoch_{i}/receipt.json').read_text());assert a['miss_pairs']==b['miss_pairs'] and a['hit_connections']==b['hit_connections'];assert a['answers']==b['answers']
 for prefix in ('floor_context','cold_floor_context'):bindings[str(s/f'{prefix}/epoch_{i}/receipt.json')]=sha(s/f'{prefix}/epoch_{i}/receipt.json')
 rows.append(dict(index=i,own_context_cache_hit_miss_and_answers_equal=True,native_floor_files_equal=True,first_native_workflow=work[0],first_native_cold=work[1]))
assert all(sha(p)==h for p,h in bindings.items());(s/'cost_diagnosis.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,stage_seconds={k:dict(v) for k,v in stage_totals.items()},initial_native_work={k:dict(v) for k,v in native_totals.items()},workflow_bootstrap_seconds=seq['bootstrap_seconds'],cold_bootstrap_seconds=seq['cold_bootstrap_seconds'],scope='Initial native counters exclude workflow exchange/conditional processing and repeated original-native feedback/proof. Native printed times are descriptive; stage wall times include all native/proof work within that stage. Complete bootstrap/rebind boundary remains separate. Cold has no previous route, seed or exchange; equal separately owned context answers verified.'),indent=2)+'\n');print(dict(stage_seconds={k:dict(v) for k,v in stage_totals.items()},initial_native_work={k:dict(v) for k,v in native_totals.items()}))
