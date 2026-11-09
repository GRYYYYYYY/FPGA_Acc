"""Exact cold input replay with criticality observation and route-byte identity gate."""
import json,os,sys,subprocess,time,shutil,math
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];B=R/'build/native_criticality_observer_v1_2026-10-10';O=R/'experiments/mmc_native_criticality_observer_v1_2026-10-10';O.mkdir();cold=R/'experiments/mmc_manifest_scope_cold_comparator_v1_2026-10-10'
b=json.loads((B/'receipt.json').read_text());assert sha(B/'sequence_vpr')==b['binary_sha256'] and all(sha(p)==h for p,h in b['bindings'].items())
proof=cold/'postchecks/verification.json';c=json.loads(proof.read_text());assert c['all115572_native_physical_queries_and_full_XML_capacity_pass'] and c['native_FULL_and_canonical_semantic_pass'] and c['explicit_ignored_pin_audit_pass'];assert all(sha(p)==h for p,h in c['bindings'].items())
bindings={**b['bindings'],**c['bindings'],str(proof):sha(proof),str(B/'receipt.json'):sha(B/'receipt.json'),str(B/'sequence_vpr'):sha(B/'sequence_vpr'),str(Path(__file__).resolve()):sha(Path(__file__))}
receipt=json.loads((cold/'native/receipt.json').read_text());command=receipt['command'].copy();command[0]=str(B/'sequence_vpr')
for name in ['design.blif','design.net','design.place']:shutil.copyfile(cold/'native'/name,O/name);bindings[str(O/name)]=sha(O/name)
manifest=R/'experiments/native_manifest_scope_preflight_v1_2026-10-10/mmc.queries';mp=manifest.with_name('mmc.verification.json');p=json.loads(mp.read_text());assert all(sha(q)==h for q,h in p['bindings'].items());bindings.update(p['bindings']);bindings[str(mp)]=sha(mp);bindings[str(manifest)]=sha(manifest)
expected=set()
for line in manifest.read_text().splitlines():
 x=line.split()
 if x[0]=='Q':expected.add((int(x[2]),int(x[3])))
assert len(expected)==115572
env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env['ROUTECAST_CRITICALITY_TRACE']=str(O/'criticality.tsv');tick=time.perf_counter()
(O/'startup.json').write_text(json.dumps(dict(bindings=bindings,command=command),indent=2)+'\n')
with (O/'native.log').open('w') as log:status=subprocess.run(command,cwd=O,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
elapsed=time.perf_counter()-tick;assert status==0 and 'VPR succeeded' in (O/'native.log').read_text()
assert (O/'output.route').read_bytes()==(cold/'native/output.route').read_bytes(),'observer route changed; no equivalence admission'
first={};hist=Counter();parameters=Counter();values={};count=0
for line in (O/'criticality.tsv').read_text().splitlines():
 tag,sequence,net,pin,index,value,maximum,exponent=line.split();count+=1;assert tag=='C' and int(sequence)==count
 key=(int(net),int(index));value=float(value);assert math.isfinite(value) and 0<=value<=float(maximum)+1e-7
 first.setdefault(key,value);hist[value]+=1;parameters[maximum,exponent]+=1;values.setdefault(key,set()).add(value)
assert set(first)==expected,'criticality observed pin coverage differs from complete native manifest'
for p in [O/'startup.json',O/'native.log',O/'output.route',O/'criticality.tsv']:bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items())
result=dict(bindings=bindings,command=command,exit_status=status,route_bytes_equal_fully_audited_cold=True,all115572_native_NET_local_pin_criticalities_observed=True,total_calls=count,distinct_connections=len(first),first_call_histogram=[dict(criticality=k,count=v) for k,v in sorted(Counter(first.values()).items())],all_call_histogram=[dict(criticality=k,count=v) for k,v in sorted(hist.items())],parameters=[dict(maximum=k[0],exponent=k[1],calls=v) for k,v in parameters.items()],connections_with_changing_criticality=sum(len(v)>1 for v in values.values()),native_observer_process_seconds=elapsed,scope='Same exposed MMC command/input/router objects plus return-unchanged logging wrapper. Byte-identical route transfers prior physical/canonical/ignored proof with identical inputs; no new independent physical parse. First observed call per pin, not an explicit routing-iteration timestamp. Observer IO time is not performance or real asynchronous STA evidence.')
(O/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('NATIVE CRITICALITY OBSERVER PASS',count,len(first),'first extrema',min(first.values()),max(first.values()),'changing',result['connections_with_changing_criticality'],flush=True)
