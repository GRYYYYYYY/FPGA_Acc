import json,sys,subprocess,shutil,os,time,xml.etree.ElementTree as E
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha,extract
from source_binding_v2 import closure
src=R/'experiments/ethernet_fixed_place_v1_2026-10-08';proof=src/'verification.json';v=json.loads(proof.read_text());assert v['placement_netlist_hash_and_cluster_name_id_bijection_and_unique_slots_pass'] and all(sha(k)==v for k,v in v['bindings'].items());receipt=json.loads((src/'receipt.json').read_text());assert receipt['exit_code']==0 and all(sha(k)==v for k,v in receipt['bindings'].items()) and all(sha(k)==v for k,v in receipt['files'].items());out=R/'experiments/ethernet_rr_only_v1_2026-10-08';out.mkdir();bindings={**closure([Path(__file__)]),str(proof):sha(proof),str(src/'receipt.json'):sha(src/'receipt.json')}
for file in ['design.blif','design.net','design.place']:shutil.copyfile(src/file,out/file);bindings[str(src/file)]=sha(src/file)
cmd=json.loads((src/'protocol.json').read_text())['command'];cmd[cmd.index('--place')]='--analysis';cmd.extend(['--route_file','missing.route','--write_rr_graph','rr_graph.xml','--check_route','full']);bindings.update({str(Path(cmd[i])):sha(Path(cmd[i])) for i in [0,1]});root=E.parse(out/'design.net').getroot();assert root.get('architecture_id')=='SHA256:'+sha(cmd[1]) and root.get('atom_netlist_id')=='SHA256:'+sha(out/'design.blif');(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,command=cmd,timeout_seconds=300,scope='Complete experimental Ethernet fixed placement RR-only export followed by expected missing-route analysis stop. No native routing labels generated. Width128/seed1/worker1 and original span50ps two-round RC budget model retained. Async timing placeholders and unproven original HDL relation/heldout admission remain explicit.'),indent=2)+'\n');tick=time.perf_counter()
with (out/'graph.log').open('w') as log:
 try:code=subprocess.run(cmd,cwd=out,env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')},stdout=log,stderr=subprocess.STDOUT,timeout=300).returncode
 except subprocess.TimeoutExpired:code='TIMEOUT'
result=dict(exit_code=code,status='REJECTED',native_graph_process_seconds=time.perf_counter()-tick)
try:
 assert code==1 and (out/'rr_graph.xml').is_file() and not (out/'missing.route').exists();text=(out/'graph.log').read_text();assert 'Message: Cannot open missing.route routing file' in text and 'Completed placement consistency check successfully.' in text
 ep,mapping=extract(out/'design.net',out/'design.place',out/'rr_graph.xml');(out/'endpoints.json').write_text(json.dumps(ep)+'\n');(out/'mapping.json').write_text(json.dumps(mapping)+'\n');result.update(status='GRAPH_AND_ENDPOINTS_CAPTURED',connections=len(ep['connections']),graph_sha256=ep['graph_sha256'])
except Exception as error:result['error']=repr(error)
assert all(sha(k)==v for k,v in bindings.items());result.update(bindings=bindings,files={str(p):sha(p) for p in out.iterdir() if p.is_file()});(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print({k:result[k] for k in ['status','exit_code']},result.get('connections'),result.get('error'),flush=True)
