"""Observe initialized native inputs of exposed XTEA, before connection routing."""
import json,os,sys,subprocess,shutil,time,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
R=Path(__file__).resolve().parents[1]
P=R/'experiments/xtea_swap_input_preflight_v1_2026-10-13'
O=R/'experiments/xtea_swap_native_inputs_v1_2026-10-13';O.mkdir()
proof=P/'verification.json';v=json.loads(proof.read_text());assert v['complete_native_identity_pin_to_physical_endpoint_assignment_pass']
bindings={**v['bindings'],str(proof):sha(proof),**closure([Path(__file__)])}
assert all(sha(p)==h for p,h in bindings.items())
ep=json.loads(Path(v['endpoint']).read_text());source=Path(ep['inputs']['net']['path']).parent
specs=[('criticality_v1','native_initial_criticality_snapshot_v1_2026-10-10','ROUTECAST_INITIAL_CRITICALITY','criticality.tsv'),('criticality','native_initial_criticality_snapshot_v2_2026-10-10','ROUTECAST_INITIAL_CRITICALITY','criticality.tsv'),('indexed','native_indexed_cost_dump_v1_2026-10-10','ROUTECAST_INDEXED_COST_DUMP','indexed.tsv')]
commands=[]
for name,build,envkey,filename in specs:
 B=R/'build'/build;b=json.loads((B/'receipt.json').read_text());assert sha(B/'sequence_vpr')==b['binary_sha256']
 bindings.update(b['bindings']);bindings.update(b.get('source_sha256',{}));bindings[str(B/'receipt.json')]=sha(B/'receipt.json');bindings[str(B/'sequence_vpr')]=b['binary_sha256']
 work=O/name;work.mkdir()
 for n in ['design.blif','design.net','design.place']:
  shutil.copyfile(source/n,work/n);bindings[str(work/n)]=sha(work/n);bindings[str(source/n)]=sha(source/n)
 cmd=[str(B/'sequence_vpr'),v['architecture'],'design.blif','--route','--net_file','design.net','--place_file','design.place','--route_file','output.route','--read_rr_graph',ep['inputs']['graph']['path'],'--route_chan_width','128','--num_workers','1','--seed','1','--max_router_iterations','100','--check_route','full']
 commands.append(dict(name=name,command=cmd,envkey=envkey,filename=filename))
assert all(sha(p)==h for p,h in bindings.items())
(O/'protocol.json').write_text(json.dumps(dict(bindings=bindings,commands=commands,heldout=False,scope='Exposed XTEA input portability; three frozen metadata-only native binaries, same placement and graph, no parameter selection or route labels.'),indent=2)+'\n')
bindings[str(O/'protocol.json')]=sha(O/'protocol.json')
for item in commands:
 work=O/item['name'];env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env[item['envkey']]=str(work/item['filename']);tick=time.perf_counter()
 with (work/'native.log').open('x') as log:code=subprocess.run(item['command'],cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
 (work/'terminal.json').write_text(json.dumps(dict(exit_status=code,seconds=time.perf_counter()-tick))+'\n')
 assert code==0 and not (work/'output.route').exists(),item['name']
 text=(work/'native.log').read_text();marker='ROUTECAST INITIAL CRITICALITY SNAPSHOT' if item['name']!='indexed' else 'ROUTECAST indexed cost metadata exported before routing';assert marker in text
 for p in [work/'native.log',work/'terminal.json',work/item['filename']]:bindings[str(p)]=sha(p)
 print(item['name'],'metadata captured',flush=True)
rows={};previous={}
for name,dest,width in [('criticality',rows,10),('criticality_v1',previous,8)]:
 for seq,line in enumerate((O/name/'criticality.tsv').read_text().splitlines(),1):
  x=line.split();assert len(x)==width and x[0]=='C' and int(x[1])==seq
  key=int(x[2]),int(x[4]);assert key not in dest
  value=float(x[5]);assert math.isfinite(value) and 0<=value<=float(x[6])<=1
  dest[key]=x
assert set(rows)==set(previous) and all(rows[k][2:8]==previous[k][2:8] for k in rows)
manifest=[line.split() for line in (P/'xtea.queries').read_text().splitlines() if line.startswith('Q ')]
expected={(int(x[2]),int(x[3])) for x in manifest};assert len(expected)==len(manifest)==2450
assert all(x[8] in ('0','1') and x[9] in ('0','1') for x in rows.values())
assert {k for k,x in rows.items() if x[8]=='0'}==expected
result=[]
for x in manifest:
 k=int(x[2]),int(x[3]);r=rows[k]
 result.append(dict(connection_id=int(x[1]),net=k[0],local_sink_pin=k[1],global_pin=int(r[3]),source_rr=int(x[4]),target_rr=int(x[5]),criticality_float32_text=r[5],maximum_text=r[6],exponent_text=r[7]))
path=O/'criticality/initial_connection_criticalities.json';path.write_text(json.dumps(result,separators=(',',':'))+'\n');bindings[str(path)]=sha(path)
assert all(sha(p)==h for p,h in bindings.items())
(O/'criticality/verification.json').write_text(json.dumps(dict(bindings=bindings,exit_status=0,routed_connections=len(expected),all_sink_pins=len(rows),extra_ignored_pins=len(rows)-len(expected),nonignored_pin_keys_exactly_manifest=True,all_values_and_pin_identities_equal_v1=True,scope='XTEA initialized snapshots v1/v2 exact agreement; original XML/native identity manifest pin alignment, no live getter manifest preflight or routing quality proof.'),indent=2)+'\n')
(O/'capture_terminal.json').write_text(json.dumps(dict(exit_status=0,all_three_observations_complete=True))+'\n')
print('XTEA initial criticality PASS',len(result),'connections',len(rows),'all sink pins',flush=True)
