"""Exact cold input replay with criticality observation and route-byte identity gate."""
import json,os,sys,subprocess,time,shutil,math
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];B=R/'build/native_initial_criticality_snapshot_v1_2026-10-10';O=R/'experiments/mmc_native_initial_criticality_snapshot_v1_2026-10-10';O.mkdir();cold=R/'experiments/mmc_manifest_scope_cold_comparator_v1_2026-10-10'
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
env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env['ROUTECAST_INITIAL_CRITICALITY']=str(O/'criticality.tsv');tick=time.perf_counter()
(O/'startup.json').write_text(json.dumps(dict(bindings=bindings,command=command),indent=2)+'\n')
with (O/'native.log').open('w') as log:status=subprocess.run(command,cwd=O,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
elapsed=time.perf_counter()-tick;assert status==0 and 'ROUTECAST INITIAL CRITICALITY SNAPSHOT 115572' in (O/'native.log').read_text()
assert not (O/'output.route').exists()
first={};hist=Counter();parameters=Counter();values={};count=0
for line in (O/'criticality.tsv').read_text().splitlines():
 tag,sequence,net,pin,index,value,maximum,exponent=line.split();count+=1;assert tag=='C' and int(sequence)==count
 key=(int(net),int(index));value=float(value);assert math.isfinite(value) and 0<=value<=float(maximum)+1e-7
 first.setdefault(key,value);hist[value]+=1;parameters[maximum,exponent]+=1;values.setdefault(key,set()).add(value)
assert set(first)==expected,'criticality observed pin coverage differs from complete native manifest'
for p in [O/'startup.json',O/'native.log',O/'criticality.tsv']:bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items())
observed=R/'experiments/mmc_native_criticality_observer_v1_2026-10-10'
op=observed/'verification.json';prior=json.loads(op.read_text());assert all(sha(q)==h for q,h in prior['bindings'].items())
prior_first={}
for line in (observed/'criticality.tsv').read_text().splitlines():
 x=line.split();prior_first.setdefault((int(x[2]),int(x[4])),float(x[5]))
assert set(prior_first)==set(first)
changed=[dict(net=k[0],local_pin=k[1],snapshot=first[k],observed_first=prior_first[k]) for k in first if first[k]!=prior_first[k]]
bindings.update(prior['bindings']);bindings[str(op)]=sha(op)
assert all(sha(q)==h for q,h in bindings.items())
result=dict(bindings=bindings,command=command,exit_status=status,connections=len(first),calls=count,initial_snapshot_equals_observed_first_per_pin=not changed,changed_connections=len(changed),changed_examples=changed[:20],native_snapshot_process_seconds=elapsed,scope='Snapshot at first wrapped getter invocation before returning to first connection search. Native initialization timing proxy, not final routing labels, completed routing, physical STA or speedup evidence.')
(O/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('INITIAL CRITICALITY SNAPSHOT PASS',count,'changed from first-per-pin',len(changed),flush=True)
