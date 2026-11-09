import os,json,subprocess,shutil,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from pre_route_endpoints import sha
r=Path.cwd();out=r/'experiments/aes_ignored_identity_v1_2026-10-08';out.mkdir();binary=r/'build/native_ignored_identity_v1_2026-10-08/routecast_net_identity_vpr';arch=r.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vtr_flow/arch/COFFE_22nm/k6FracN10LB_mem20K_complexDSP_customSB_22nm.xml';bindings={str(p):sha(p) for p in [binary,arch,Path(__file__)]};results=[]
for name in ['aes_cipher','aes_inv_cipher']:
 w=out/name;w.mkdir();old=r/f'experiments/aes_mapped_full_workflow_v1_2026-10-08/{name}'
 for f in ['design.blif','design.net','design.place']:shutil.copyfile(old/f,w/f);bindings[str(w/f)]=sha(w/f)
 cmd=[str(binary),str(arch),'design.blif','--analysis','--net_file','design.net','--place_file','design.place','--route_file','missing.route','--route_chan_width','128','--num_workers','1','--seed','1','--check_route','full'];table=w/'identity.jsonl'
 with (w/'native.log').open('w') as f:code=subprocess.run(cmd,cwd=w,env={**{k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')},'ROUTECAST_IDENTITY_ONLY':'1','ROUTECAST_NET_IDENTITY_FILE':str(table)},stdout=f,stderr=subprocess.STDOUT,timeout=60).returncode
 assert code==1 and json.loads(Path(str(table)+'.phase.json').read_text())['rr_graph_skipped']
 records=[json.loads(x) for x in table.read_text().splitlines()];ep=json.loads((r/f'experiments/aes_rr_graph_only_v1_2026-10-08/{name}/endpoints.json').read_text());lookup={x['name']:x for x in records};counts={}
 for q in ep['connections']:
  net=ep['net_names'][str(q['net_id'])];assert net in lookup
  if lookup[net]['ignored']:counts[net]=counts.get(net,0)+1
 results.append({'name':name,'command':cmd,'identity_sha256':sha(table),'all_queries':len(ep['connections']),'native_ignored_queries':sum(counts.values()),'native_routable_queries':len(ep['connections'])-sum(counts.values()),'ignored_query_NET_counts':counts,'ignored_NET_names':[x['name'] for x in records if x['ignored']]})
assert all(sha(k)==v for k,v in bindings.items());(out/'receipt.json').write_text(json.dumps({'bindings':bindings,'results':results,'scope':'Original all-query scope preserved and explicitly partitioned by actual native ignored flags before routing. No revised model run and no labels used to determine flags.'},indent=2)+'\n');print(json.dumps(results,indent=2))
