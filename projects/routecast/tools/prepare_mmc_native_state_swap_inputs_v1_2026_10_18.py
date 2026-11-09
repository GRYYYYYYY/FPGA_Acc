"""Apply frozen MMC swap and capture endpoints without target routing labels."""
import json,sys,shutil,subprocess,os,time,resource
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha,placements,extract
from source_binding_v2 import closure
G=R/'experiments/mmc_native_state_geometry_v1_2026-10-18';gp=G/'protocol.json';p=json.loads(gp.read_text());ready=json.loads((G/'readiness_verification_v1.json').read_text());assert all(sha(k)==h for k,h in ready['bindings'].items());epfile=Path(p['previous_endpoint']);oldmeta=json.loads(epfile.read_text());src=Path(oldmeta['inputs']['net']['path']).parent;graph=Path(oldmeta['inputs']['graph']['path']);old=placements(src/'design.place',sha(src/'design.net'));pair=p['selected']['pair'];a,b=pair;assert list(old[a])==p['selected']['before_positions'][a] and list(old[b])==p['selected']['before_positions'][b]
D=R/'experiments/mmc_native_state_swap_inputs_v1_2026-10-18';D.mkdir(exist_ok=False);W=D/'mmc';W.mkdir();start=time.perf_counter();bindings={**closure([Path(__file__)]),str(gp):sha(gp),str(G/'readiness_verification_v1.json'):sha(G/'readiness_verification_v1.json')}
for name in ['design.place','design.net','design.blif','rr_graph.xml','endpoints.json','mapping.json']:bindings[str(src/name)]=sha(src/name)
for name in ['design.net','design.blif']:shutil.copyfile(src/name,W/name)
(W/'rr_graph.xml').symlink_to(graph);changes={n:p['selected']['after_positions'][n][:4] for n in pair};lines=[]
for line in (src/'design.place').read_text().splitlines():
 fields=line.split()
 if fields and fields[0] in changes:fields[1:5]=map(str,changes[fields[0]]);line='\t'.join(fields)
 lines.append(line)
with (W/'design.place').open('x') as f:f.write('\n'.join(lines)+'\n')
new=placements(W/'design.place',sha(W/'design.net'));assert set(new)==set(old) and all(new[n][4]==old[n][4] for n in old);assert {n for n in old if old[n]!=new[n]}==set(pair) and {x[:4] for x in old.values()}=={x[:4] for x in new.values()}
binary=R/'build/native_candidate_retained_search_2026-10-06/sequence_vpr';arch=R/'experiments/async_reset_arch_candidate_v2_2026-10-08/architecture.xml';cmd=[str(binary),str(arch),'design.blif','--analysis','--net_file','design.net','--place_file','design.place','--route_file','missing.route','--read_rr_graph',str(graph),'--route_chan_width','128','--num_workers','1','--seed','1','--check_route','full']
for f in [binary,arch,W/'design.place',W/'design.net',W/'design.blif']:bindings[str(f)]=sha(f)
with (D/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,selected=pair,hpwl_delta=p['selected']['hpwl_delta'],command=cmd,scope='Frozen MMC geometry only; no target route generated or quality outcome.'),f,indent=2);f.write('\n')
print('MMC PLACEMENT CHECK START',flush=True)
with (W/'placement_check.log').open('x') as log:code=subprocess.call(cmd,cwd=W,env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')},stdout=log,stderr=subprocess.STDOUT)
text=(W/'placement_check.log').read_text();assert code==1 and 'Completed placement consistency check successfully.' in text and 'Cannot open missing.route' in text and not list(W.glob('*.route'));print('MMC PLACEMENT PASS, ENDPOINT EXTRACTION START',flush=True)
ep,mapping=extract(W/'design.net',W/'design.place',W/'rr_graph.xml')
for name,data in [('endpoints.json',ep),('mapping.json',mapping)]:
 with (W/name).open('x') as f:json.dump(data,f);f.write('\n')
original=json.loads((src/'endpoints.json').read_text());oldmap=json.loads((src/'mapping.json').read_text());assert ep['net_names']==original['net_names'] and ep['excluded_nets']==original['excluded_nets'];assert len(mapping['pin_details'])==len(oldmap['pin_details'])
for x,y in zip(oldmap['pin_details'],mapping['pin_details']):assert {k:v for k,v in x.items() if k!='rr_node'}=={k:v for k,v in y.items() if k!='rr_node'}
a={q['connection_id']:q for q in original['connections']};b={q['connection_id']:q for q in ep['connections']};assert a.keys()==b.keys() and all(a[c]['net_id']==b[c]['net_id'] for c in a);assert any(a[c]!=b[c] for c in a);assert all(sha(k)==h for k,h in bindings.items())
row=dict(name='mmc',exit_code=code,status='GRAPH_AND_ENDPOINTS_CAPTURED',connections=len(a),graph_sha256=ep['graph_sha256'],files={str(f):sha(f) for f in W.iterdir() if f.is_file()})
with (D/'receipt.json').open('x') as f:json.dump(dict(bindings=bindings,rows=[row],native_route_labels_generated=False,preparation_seconds=time.perf_counter()-start),f,indent=2);f.write('\n')
print('MMC ENDPOINTS CAPTURED',len(a),flush=True)
