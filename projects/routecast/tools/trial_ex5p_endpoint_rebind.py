"""Real original↔swapped endpoints on one RR/native context, rejected input isolation."""
import json,time,copy
from pathlib import Path
from pre_route_endpoints import sha
from persistent_rc_context import PersistentRCContext
root=Path(__file__).resolve().parents[1];out=root/'experiments/ex5p_endpoint_rebind_2026-10-06';out.mkdir();old=root/'experiments/nonzero_rc_ex5p_endpoints_2026-10-06/endpoints.json';new=root/'experiments/ex5p_placement_swap_2026-10-06/endpoints.json';receipt=json.loads((new.parent/'receipt.json').read_text());p={'inputs_sha256':{str(x):sha(x) for x in (old,new)},'context_source_sha256':sha(root/'tools/persistent_rc_context.py'),'policy':'Samegraph/netlist endpoint rebind original→swapped→original; preserve nativearrays/history/demand. Reject malformed identity/endpoints without state changes; route ledger update outside scope.'};(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');start=time.monotonic();ctx=PersistentRCContext(old);setup=time.monotonic()-start;identity=(id(ctx.rc),id(ctx.native),id(ctx.context[2]),id(ctx.context[3]));ctx.set_history({0:1});ctx.native.set_other({0:1});buffers=[a.tobytes() for a in ctx.native.arrays]+[ctx.native.other.tobytes()];history=copy.deepcopy(ctx.history);rows=[]
for path in (new,old,new):
 start=time.monotonic();result=ctx.bind_endpoints(path);elapsed=time.monotonic()-start
 assert result['changed_connection_ids']==receipt['changed_connection_ids'] and result['affected_net_ids']==receipt['affected_net_ids'] and result['affected_complete_net_connection_ids']==sorted(receipt['affected_complete_net_connection_ids'])
 assert identity==(id(ctx.rc),id(ctx.native),id(ctx.context[2]),id(ctx.context[3]));assert buffers==[a.tobytes() for a in ctx.native.arrays]+[ctx.native.other.tobytes()] and ctx.history==history;rows.append({'endpoint':str(path),'bind_s':elapsed,'affected':result})
base=json.loads(new.read_text());cases=[]
for kind in ('duplicate','missing','wrong_net','bad_sink','bad_hash'):
 data=copy.deepcopy(base)
 if kind=='duplicate':data['connections'].append(copy.deepcopy(data['connections'][0]))
 elif kind=='missing':data['connections'].pop()
 elif kind=='wrong_net':data['connections'][0]['net_id']+=1
 elif kind=='bad_sink':data['connections'][0]['sink']=data['connections'][0]['source']
 else:data['inputs']['place']['sha256']='0'*64
 file=out/(kind+'.json');file.write_text(json.dumps(data));before=ctx.context;meta=ctx.endpoint_metadata
 try:ctx.bind_endpoints(file)
 except ValueError:cases.append(kind)
 else:raise AssertionError('bad bind accepted')
 assert ctx.context is before and ctx.endpoint_metadata is meta and buffers==[a.tobytes() for a in ctx.native.arrays]+[ctx.native.other.tobytes()]
r={'context_setup_s':setup,'rebinds':rows,'rejected_cases':cases,'graph_native_identity_preserved':True,'mutable_buffers_preserved':True,'protocol_sha256':sha(out/'protocol.json'),'source_sha256':sha(Path(__file__))};(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print('setup',setup,'binds',[x['bind_s'] for x in rows],'rejections',cases)
