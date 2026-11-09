"""Fresh placement endpoint and ignored-NET partition checks, no routing labels."""
import json,subprocess,sys,time,hashlib
from pathlib import Path
from affected_connections import affected
R=Path(__file__).resolve().parents[1];D=Path(sys.argv[1]);src=D/'mmc';start=time.perf_counter();stages=[]
commands=[['verify_freecores_rr_endpoints_v1.py',str(src),str(D/'receipt.json')],['prepare_native_demand_no_timeout_v1.py',str(src),str(D/'demand')],['verify_freecores_native_demand_v1.py',str(D/'demand'),str(src/'endpoints.json')]]
for index,args in enumerate(commands):
 with (D/f'input_check_{index}.log').open('x') as f:code=subprocess.call([sys.executable,str(R/'tools'/args[0]),*args[1:]],cwd=R,stdout=f,stderr=subprocess.STDOUT)
 stages.append(dict(stage=args[0],exit_code=code))
 with (D/f'input_check_{index}_terminal.json').open('x') as f:json.dump(stages[-1],f);f.write('\n')
 if code:raise SystemExit(code)
protocol=json.loads((D/'protocol.json').read_text());oldpath=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/demand/mmc/endpoints.json';newpath=D/'demand/endpoints.json';old=json.loads(oldpath.read_text());new=json.loads(newpath.read_text());assert len(old['connections'])==len(new['connections'])==115572;delta=affected(old,new);assert delta['changed_connection_ids']
a={q['connection_id']:q for q in old['connections']};b={q['connection_id']:q for q in new['connections']};assert a.keys()==b.keys() and all(a[c]['net_id']==b[c]['net_id'] for c in a);assert not list(D.rglob('*.route'))
identities=[]
for meta in [old,new]:
 identityfile=Path(meta['inputs']['native_identity']['path'])
 identities.append([dict(row,pins=[{k:v for k,v in pin.items() if k not in ['x','y','layer']} for pin in row['pins']]) for row in map(json.loads,identityfile.read_text().splitlines())])
assert identities[0]==identities[1]
assert len({(q['net_id'],q['source'],q['sink']) for q in old['connections']})==115572
files=[Path(__file__),D/'protocol.json',D/'receipt.json',oldpath,newpath,D/'demand/verification.json',src/'verification.json'];bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
with (D/'staged_input_verification_v1.json').open('x') as f:json.dump(dict(bindings=bindings,stages=stages,selected=protocol['selected'],hpwl_delta=protocol['hpwl_delta'],affected=delta,connections=115572,all_native_logical_NET_local_pin_identities_preserved=True,old_endpoint_identity_unique=True,native_route_labels_generated=False,input_check_seconds=time.perf_counter()-start,scope='Native placement consistency plus original XML endpoints and native ignored-NET partition; no target route, candidate QoR or timing claim.'),f,indent=2);f.write('\n')
print('NEW TARGET',protocol['selected'][0],protocol['selected'][1],'HPWL delta',protocol['hpwl_delta'],'direct',len(delta['changed_connection_ids']),'closure NETs',len(delta['affected_net_ids']),'connections',len(delta['recompute_connection_ids']),flush=True)
