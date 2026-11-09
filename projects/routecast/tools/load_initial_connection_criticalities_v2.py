"""Explicit fresh native criticality admission; legacy semantics unchanged."""
import json,struct,math
from pathlib import Path
from types import MappingProxyType
from pre_route_endpoints import sha
from load_initial_connection_criticalities_v1 import load as load_legacy
SCHEMA='ROUTECAST_FRESH_INITIAL_TIMING_V1'
def load(directory):
 directory=Path(directory).resolve();admission=json.loads((directory/'verification.json').read_text())
 if admission.get('schema')!=SCHEMA:return load_legacy(directory)
 if not all(admission.get(k) is True for k in ['nonignored_pin_keys_exactly_manifest','fresh_float32_values_and_pin_identities_independently_verified','no_target_route_generated']):raise ValueError('fresh criticality admission missing')
 if admission.get('all_values_and_pin_identities_equal_v1') is not None:raise ValueError('fresh epoch must not claim legacy value equality')
 binds=admission['bindings']
 if not all(sha(p)==h for p,h in binds.items()):raise ValueError('fresh criticality source changed')
 proof=Path(admission['independent_snapshot_proof']).resolve();verified=json.loads(proof.read_text());case=admission['source_case']
 if case not in ['case_01','case_02','case_03']:raise ValueError('fresh criticality case missing')
 if binds.get(str(proof))!=sha(proof) or verified.get('status')!='pass' or not verified.get('all4_TSV_global_pin_manifest_and_float32_comparisons_independently_replayed') or not verified.get('all4_inputs_unchanged_and_no_routes_generated'):raise ValueError('fresh independent snapshot admission missing')
 if not any(r['case']==case and r['physical_queries']==admission['routed_connections'] for r in verified['rows']):raise ValueError('fresh case domain mismatch')
 if not all(sha(p)==h for p,h in verified['bindings'].items()):raise ValueError('fresh independent sources changed')
 path=directory/'initial_connection_criticalities.json';source=proof.parent/case/'initial_connection_criticalities.json';endpoint_path=Path(admission['after_endpoint']).resolve()
 if binds.get(str(path))!=sha(path) or verified['bindings'].get(str(source))!=sha(source) or sha(path)!=sha(source):raise ValueError('fresh values differ from independently observed source')
 if binds.get(str(endpoint_path))!=sha(endpoint_path) or verified['bindings'].get(str(endpoint_path))!=sha(endpoint_path):raise ValueError('fresh endpoint snapshot unbound')
 rows=json.loads(path.read_text());by_id={};keys=set()
 for row in rows:
  cid=row['connection_id'];key=row['net'],row['local_sink_pin']
  if type(cid) is not int or cid<0 or cid in by_id or key in keys:raise ValueError('duplicate/invalid connection identity')
  value=struct.unpack('f',struct.pack('f',float(row['criticality_float32_text'])))[0]
  maximum=struct.unpack('f',struct.pack('f',float(row['maximum_text'])))[0]
  if not math.isfinite(value) or not 0<=value<=maximum<=1:raise ValueError('invalid criticality')
  numerator,denominator=value.as_integer_ratio()
  by_id[cid]=MappingProxyType(dict(row,criticality=value,criticality_numerator=numerator,criticality_denominator=denominator))
  keys.add(key)
 if len(by_id)!=admission['routed_connections']:raise ValueError('incomplete criticality vector')
 endpoint=json.loads(endpoint_path.read_text());queries={q['connection_id']:q for q in endpoint['connections']}
 if len(queries)!=len(endpoint['connections']) or set(queries)!=set(by_id):raise ValueError('fresh criticality endpoint coverage mismatch')
 for cid,q in queries.items():
  row=by_id[cid]
  if (q['net_id'],q['source'],q['sink'])!=(row['net'],row['source_rr'],row['target_rr']):raise ValueError('fresh criticality endpoint identity mismatch')
 return MappingProxyType(by_id)
