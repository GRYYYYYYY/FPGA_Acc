"""Admit independently verified current3 native epochs; preserve prior loaders."""
import json,math,struct
from pathlib import Path
from types import MappingProxyType
from pre_route_endpoints import sha
from load_initial_connection_criticalities_v2 import load as legacy
SCHEMA='ROUTECAST_CURRENT_INITIAL_TIMING_V1'
def load(directory):
 directory=Path(directory).resolve();admission=json.loads((directory/'verification.json').read_text())
 if admission.get('schema')!=SCHEMA:return legacy(directory)
 if not all(admission.get(k) is True for k in ['fresh_float32_values_and_pin_identities_independently_verified','nonignored_pin_keys_exactly_manifest','no_target_route_generated']):raise ValueError('current timing admission missing')
 if admission.get('all_values_and_pin_identities_equal_v1') is not None:raise ValueError('fresh current epoch cannot assert old value equality')
 binds=admission['bindings']
 if not all(sha(p)==h for p,h in binds.items()):raise ValueError('current timing source drift')
 proof=Path(admission['independent_snapshot_proof']).resolve();case=admission['source_case'];verified=json.loads(proof.read_text())
 if case not in ['episode_01','episode_02','episode_03'] or binds.get(str(proof))!=sha(proof) or verified.get('status')!='ALL3_CURRENT_INITIAL_TIMING_FLOAT32_PINS_XML_ENDPOINTS_NO_ROUTE_PASS':raise ValueError('current timing independent proof domain')
 if len(verified['rows'])!=3 or not any(r['case']==case and r['physical_connections']==115572 and r['fresh_float32_values_verified'] and r['current_XML_terminal_class_identities_verified'] and r['no_route_generated'] for r in verified['rows']):raise ValueError('current timing incomplete case proof')
 if not all(sha(p)==h for p,h in verified['bindings'].items()):raise ValueError('current independent source drift')
 payload=directory/'initial_connection_criticalities.json';original=proof.parent/case/payload.name;ep=Path(admission['after_endpoint']).resolve()
 if binds.get(str(payload))!=sha(payload) or verified['bindings'].get(str(original))!=sha(original) or sha(payload)!=sha(original) or binds.get(str(ep))!=sha(ep) or verified['bindings'].get(str(ep))!=sha(ep):raise ValueError('current timing payload/endpoint identity')
 endpoint=json.loads(ep.read_text());queries={q['connection_id']:q for q in endpoint['connections']};rows=json.loads(payload.read_text());out={};keys=set()
 for row in rows:
  cid=row['connection_id'];key=row['net'],row['local_sink_pin']
  if type(cid) is not int or cid<0 or cid in out or key in keys:raise ValueError('duplicate current pin/CID')
  q=queries.get(cid)
  if q is None or (q['net_id'],q['source'],q['sink'])!=(row['net'],row['source_rr'],row['target_rr']):raise ValueError('current endpoint mismatch')
  value=struct.unpack('<f',struct.pack('<f',float(row['criticality_float32_text'])))[0];maximum=struct.unpack('<f',struct.pack('<f',float(row['maximum_text'])))[0]
  if not math.isfinite(value) or not 0<=value<=maximum<=1:raise ValueError('current criticality domain')
  numerator,denominator=value.as_integer_ratio();out[cid]=MappingProxyType(dict(row,criticality=value,criticality_numerator=numerator,criticality_denominator=denominator));keys.add(key)
 if len(out)!=admission['routed_connections'] or set(out)!=set(queries) or len(queries)!=len(endpoint['connections']):raise ValueError('current timing coverage')
 return MappingProxyType(out)
