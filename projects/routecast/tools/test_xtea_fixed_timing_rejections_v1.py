"""Reject wrong graph, missing manifest query and changed logical pin identity."""
import json,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from frozen_timing_epoch_remap_v1 import remap
from source_binding_v2 import closure
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];proof=R/'experiments/xtea_fixed_timing_epoch_v1_2026-10-13/verification.json';v=json.loads(proof.read_text());bindings={**v['bindings'],str(proof):sha(proof),**closure([Path(__file__)])};assert all(sha(p)==h for p,h in bindings.items())
args=[v[k] for k in ['before_endpoint','after_endpoint','source_criticality_directory','before_manifest','after_manifest']];rows=[]
with tempfile.TemporaryDirectory(prefix='routecast_epoch_contract_') as td:
 d=Path(td)
 for mode,expected in [('wrong_graph','requires fixed graph and packed-netlist identity'),('missing_query','manifest coverage'),('changed_pin','native pin identity changed')]:
  call=list(args)
  if mode=='wrong_graph':
   data=json.loads(Path(args[1]).read_text());data['graph_sha256']='0'*64;p=d/'wrong_endpoint.json';p.write_text(json.dumps(data));call[1]=p
  else:
   lines=Path(args[4]).read_text().splitlines();i=next(i for i,l in enumerate(lines) if l.startswith('Q '))
   if mode=='missing_query':del lines[i]
   else:
    x=lines[i].split();x[3]=str(int(x[3])+100000);lines[i]=' '.join(x)
   p=d/(mode+'.queries');p.write_text('\n'.join(lines)+'\n');call[4]=p
  try:remap(*call)
  except ValueError as e:assert str(e)==expected;rows.append(dict(case=mode,rejection=str(e)))
  else:raise AssertionError(mode+' accepted')
assert all(sha(p)==h for p,h in bindings.items())
(proof.parent/'rejection_verification_v1.json').write_text(json.dumps(dict(bindings=bindings,cases=rows,all_invalid_contexts_rejected=True),indent=2)+'\n');print('PASS three frozen-epoch context/identity rejection cases')
