"""Exact cold input replay with criticality observation and route-byte identity gate."""
import json,os,sys,subprocess,time,shutil,math
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];B=R/'build/native_initial_criticality_snapshot_v2_2026-10-10';O=R/'experiments/mmc_native_initial_criticality_snapshot_v2_2026-10-10';O.mkdir();cold=R/'experiments/mmc_manifest_scope_cold_comparator_v1_2026-10-10'
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
elapsed=time.perf_counter()-tick
assert status==0 and 'ROUTECAST INITIAL CRITICALITY SNAPSHOT 119473' in (O/'native.log').read_text()
assert not (O/'output.route').exists()
rows={};count=0
for line in (O/'criticality.tsv').read_text().splitlines():
 x=line.split();count+=1;assert len(x)==10 and x[0]=='C' and int(x[1])==count
 key=int(x[2]),int(x[4]);assert key not in rows
 value=float(x[5]);assert math.isfinite(value) and 0<=value<=float(x[6])+1e-7
 assert x[8] in ('0','1') and x[9] in ('0','1')
 rows[key]=x
assert count==119473 and {k for k,x in rows.items() if x[8]=='0'}==expected
extra=set(rows)-expected;assert len(extra)==3901 and all(rows[k][8]=='1' for k in extra)
old=R/'experiments/mmc_native_initial_criticality_snapshot_v1_2026-10-10';proof=old/'snapshot_verification.json';prior=json.loads(proof.read_text());assert all(sha(p)==h for p,h in prior['bindings'].items());bindings.update(prior['bindings']);bindings[str(proof)]=sha(proof)
previous={}
for line in (old/'criticality.tsv').read_text().splitlines():
 x=line.split();previous[int(x[2]),int(x[4])]=x
assert set(previous)==set(rows) and all(rows[k][2:8]==previous[k][2:8] for k in rows)
manifest_rows=[]
for line in manifest.read_text().splitlines():
 x=line.split()
 if x[0]=='Q':
  key=int(x[2]),int(x[3]);r=rows[key]
  manifest_rows.append(dict(connection_id=int(x[1]),net=key[0],local_sink_pin=key[1],global_pin=int(r[3]),source_rr=int(x[4]),target_rr=int(x[5]),criticality_float32_text=r[5],maximum_text=r[6],exponent_text=r[7]))
assert len(manifest_rows)==115572 and len({x['connection_id'] for x in manifest_rows})==115572
(O/'initial_connection_criticalities.json').write_text(json.dumps(manifest_rows,separators=(',',':'))+'\n')
for p in [O/'startup.json',O/'native.log',O/'criticality.tsv',O/'initial_connection_criticalities.json']:bindings[str(p)]=sha(p)
source=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vpr/src/route/route_net.cpp';bindings[str(source)]=sha(source)
assert all(sha(p)==h for p,h in bindings.items())
result=dict(bindings=bindings,exit_status=status,all_sink_pins=count,routed_connections=len(expected),extra_ignored_pins=len(extra),extra_ignored_global_pins=sum(rows[k][9]=='1' for k in extra),nonignored_pin_keys_exactly_manifest=True,all_values_and_pin_identities_equal_v1=True,process_seconds=elapsed,scope='Initial native timing proxy, per-pin manifest identities exported. All extra pins native ignored flag; global count separate. Startup and snapshot costs paid, no routing or speedup claim.')
(O/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('INITIAL CRITICALITY CLASSIFICATION PASS',count,len(expected),len(extra),flush=True)
