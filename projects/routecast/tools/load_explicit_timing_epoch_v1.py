"""Accept native initialized snapshots or explicit, authenticated fixed-epoch remaps."""
import json
from pathlib import Path
from load_initial_connection_criticalities_v1 import load as load_native
from frozen_timing_epoch_remap_v1 import remap
from pre_route_endpoints import sha

def load(directory):
 directory=Path(directory).resolve();proof=directory/'verification.json';v=json.loads(proof.read_text())
 if v.get('schema')!='ROUTECAST_FROZEN_TIMING_REMAP_V1':return load_native(directory)
 if not all(v.get(k) is True for k in ['all_native_pin_identities_preserved','all_values_equal_before_timing_epoch','all_endpoints_equal_after_placement']):raise ValueError('frozen epoch proof incomplete')
 if not all(sha(p)==h for p,h in v['bindings'].items()):raise ValueError('frozen epoch source changed')
 values,bindings,epoch=remap(*[v[k] for k in ['before_endpoint','after_endpoint','source_criticality_directory','before_manifest','after_manifest']])
 if epoch!=v['timing_epoch_sha256'] or len(values)!=v['connections']:raise ValueError('epoch identity mismatch')
 if any(v['bindings'].get(p)!=h for p,h in bindings.items()):raise ValueError('unbound epoch source')
 p=directory/'remapped_criticalities.json'
 if v['bindings'].get(str(p))!=sha(p):raise ValueError('unbound remapped values')
 if json.loads(p.read_text())!=[dict(values[k]) for k in sorted(values)]:raise ValueError('remapped values differ from frozen epoch')
 return values
