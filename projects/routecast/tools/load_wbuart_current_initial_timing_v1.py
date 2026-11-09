"""Strict current external timing adapter; never falls back to MMC/legacy inputs."""
import hashlib,json,math,struct
from pathlib import Path
from types import MappingProxyType
from pre_route_endpoints import sha
SCHEMA='ROUTECAST_WBUART_CURRENT_INITIAL_TIMING_V1'
def epoch(directory):
 d=Path(directory).resolve();v=json.loads((d/'verification.json').read_text());payload=d/'initial_connection_criticalities.json';ep=Path(v['after_endpoint']).resolve();files=[payload,ep,d/'protocol.json',d/'work/pin_manifest.tsv'];return hashlib.sha256(json.dumps([(str(p),sha(p)) for p in files],separators=(',',':')).encode()).hexdigest()
def load(directory,endpoint_path,*,expected_epoch=None):
 d=Path(directory).resolve();v=json.loads((d/'verification.json').read_text());ep=Path(endpoint_path).resolve();payload=d/'initial_connection_criticalities.json'
 if v.get('schema')!=SCHEMA or v.get('status')!='ALL2493_CURRENT_CIDS_PHYSICAL_PIN_IDENTITIES_FLOAT_BITS_AND_ATOM_AGGREGATES_VERIFIED':raise ValueError('unsupported external current timing admission')
 if not all(v.get(k) is True for k in ['current_float32_values_verified','current_XML_pin_and_endpoint_identities_verified','no_route_generated']):raise ValueError('incomplete current timing proof')
 if not all(sha(p)==h for p,h in v['bindings'].items()):raise ValueError('external timing source drift')
 if v['bindings'].get(str(payload))!=sha(payload) or sha(ep)!=v['bindings'].get(str(Path(v['after_endpoint']).resolve())):raise ValueError('timing endpoint/payload binding mismatch')
 if expected_epoch is not None and expected_epoch!=epoch(d):raise ValueError('timing epoch mismatch')
 e=json.loads(ep.read_text());qs={q['connection_id']:q for q in e['connections']};rows=json.loads(payload.read_text());out={};pins=set()
 if len(qs)!=len(e['connections']) or len(qs)!=v['connections']:raise ValueError('external query coverage mismatch')
 for row in rows:
  cid=row['connection_id'];q=qs.get(cid)
  if type(cid) is not int or q is None or cid in out:raise ValueError('duplicate or missing external CID')
  if row['full_connection_id']!=q['full_connection_id'] or (row['endpoint_net_id'],row['source_rr'],row['target_rr'])!=(q['net_id'],q['source'],q['sink']) or row['net_name']!=e['net_names'][str(q['net_id'])]:raise ValueError('external endpoint mismatch')
  key=(row['native_net_id'],row['local_sink_pin'])
  if key in pins or row['ignored'] or row['clock_net']:raise ValueError('invalid data pin identity')
  value=struct.unpack('<f',struct.pack('<f',float(row['criticality_float32_text'])))[0];maximum=struct.unpack('<f',struct.pack('<f',float(row['maximum_text'])))[0];bits=int.from_bytes(struct.pack('<f',value),'little')
  if not math.isfinite(value) or not 0<=value<=maximum<=1 or bits!=int(row['criticality_bits'],16):raise ValueError('external criticality domain/bits mismatch')
  num,den=value.as_integer_ratio()
  if (num,den)!=(row['criticality_numerator'],row['criticality_denominator']):raise ValueError('external criticality rational mismatch')
  pins.add(key);out[cid]=MappingProxyType(dict(row,criticality=value))
 if set(out)!=set(qs):raise ValueError('external timing coverage incomplete')
 return MappingProxyType(out)
