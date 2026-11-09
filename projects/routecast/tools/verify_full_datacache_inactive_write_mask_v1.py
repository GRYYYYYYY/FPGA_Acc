import hashlib,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';F=E/'full_original_source_proc_state_v1_2026-10-09/source_proc.json';m=max(json.loads(F.read_text())['modules'].values(),key=lambda x:len(x.get('cells',{})));names=['io_cpu_writeBack_isValid','when_DataCache_l1090','stageB_flusher_counter','loader_done'];cuts=[m['netnames']['dataCache_1.'+n]['bits'][7 if n=='stageB_flusher_counter' else 0] for n in names];roots={n:m['netnames']['dataCache_1.'+n]['bits'] for n in ['dataWriteCmd_valid','tagsWriteCmd_valid']};drivers={b:(n,c) for n,c in m['cells'].items() for p,bs in c['connections'].items() if c['port_directions'][p]=='output' for b in bs};used={};leaves=set(cuts)
def walk(b):
 if not isinstance(b,int) or b in cuts:return
 entry=drivers.get(b)
 if entry is None or 'dff' in entry[1]['type'].lower() or entry[1]['type'].startswith('$memrd'):leaves.add(b);return
 n,c=entry
 if n in used:return
 used[n]=c
 for p,bs in c['connections'].items():
  if c['port_directions'][p]=='input':
   for x in bs:walk(x)
for bs in roots.values():
 for b in bs:walk(b)
ordered=sorted(leaves);D=E/'full_datacache_inactive_write_mask_v1_2026-10-09';D.mkdir(exist_ok=True);ports={'boundary':{'direction':'input','bits':ordered}}|{n:{'direction':'output','bits':bs} for n,bs in roots.items()};(D/'cone.json').write_text(json.dumps({'modules':{'cone':{'attributes':{},'ports':ports,'cells':used,'netnames':{}}}},indent=2)+'\n');premise=' | '.join(('~' if i==2 else '')+'boundary['+str(ordered.index(b))+']' for i,b in enumerate(cuts));v='module miter(input ['+str(len(ordered)-1)+':0] boundary,output good);\nwire dataWriteCmd_valid,tagsWriteCmd_valid;\ncone c(.boundary(boundary),.dataWriteCmd_valid(dataWriteCmd_valid),.tagsWriteCmd_valid(tagsWriteCmd_valid));\nassign good=('+premise+') || !(dataWriteCmd_valid || tagsWriteCmd_valid);\nendmodule\n';(D/'miter.v').write_text(v);yosys=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys';r=subprocess.run([str(yosys),'-p','read_json cone.json; read_verilog miter.v; prep -top miter; flatten; sat -verify -prove good 1 -show-inputs'],cwd=D,capture_output=True,text=True,timeout=60);(D/'check.log').write_text(r.stdout+r.stderr);out={'cut_conditions':dict(zip(names,cuts)),'cells':len(used),'boundary_bits':ordered,'exit_code':r.returncode,'success':'SAT proof finished - no model found: SUCCESS!' in r.stdout,'hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [F,D/'cone.json',D/'miter.v',D/'check.log']},'scope':'Exact original-source commands data/tag valid0 when writeBack-valid,refill-write,flush-active,loader-done all0; arbitrary other state including invalid raw args. This is conditional command suppression, not all memory requests, effective operation correspondence, reachable invariants or Full admission.'};(D/'mask_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['boundary_bits','hashes']},indent=2));assert r.returncode==0 and out['success']
