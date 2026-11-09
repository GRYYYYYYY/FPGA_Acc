"""Generate an authenticated dirty-only recipe from an audited warm fixture.

This is fixture extraction, not production of new dirty route/floor evidence.
"""
import json,time
from pathlib import Path
from pre_route_endpoints import sha
from source_binding_v2 import closure

def prepare(warm_directory,source_initial,output):
 start=time.perf_counter();warm_directory=Path(warm_directory).resolve();source_initial=Path(source_initial).resolve();output=Path(output).resolve()
 proof_path=warm_directory/'verification.json';proof=json.loads(proof_path.read_text())
 if not all(sha(p)==h for p,h in proof['bindings'].items()):raise ValueError('warm input changed')
 initial=warm_directory/'initial.json'
 if proof['bindings'].get(str(initial))!=sha(initial):raise ValueError('warm initial unbound')
 frame=json.loads(initial.read_text());source=json.loads(source_initial.read_text());dirty=set(proof['dirty_nets'])
 if [x['connection_id'] for x in frame['records']]!=[x['connection_id'] for x in source['records']]:raise ValueError('source record order changed')
 computed={'records','ledger','epochs','overflow_units','independent_connection_ledger'}
 payload=dict(schema='NATIVE_DIRTY_TRANSITION_RECIPE_V1',endpoint=proof['endpoint'],source_initial=str(source_initial),source_initial_sha256=sha(source_initial),dirty_nets=sorted(dirty),dirty_records=[x for x in frame['records'] if x['net_id'] in dirty],metadata={k:v for k,v in frame.items() if k not in computed},top_key_order=list(frame),key_orders={k:list(frame[k]) for k in ['ledger','independent_connection_ledger','epochs']},expected_initial_sha256=sha(initial))
 with output.open('x') as f:json.dump(payload,f);f.write('\n')
 bindings={**closure([Path(__file__)]),**proof['bindings'],str(proof_path):sha(proof_path),str(source_initial):sha(source_initial),str(output):sha(output)}
 result=dict(bindings=bindings,recipe=str(output),production_seconds=time.perf_counter()-start,full_connections=len(frame['records']),dirty_records=len(payload['dirty_records']),full_initial_bytes=initial.stat().st_size,recipe_bytes=output.stat().st_size,scope='Authenticated extraction from exposed certified fixture. Full warm/floor dependencies still hashed at runtime; recipe retains global serialization key order metadata. No production speedup.')
 with output.with_suffix('.proof.json').open('x') as f:json.dump(result,f,indent=2)
 return result
