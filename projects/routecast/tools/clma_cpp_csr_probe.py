"""Fixed first100-net host C++ transport/path parity; no speed claim."""
import json,subprocess,time,hashlib,shutil
from pathlib import Path
from prepared_csr import read,sha
out=Path('experiments/clma_cpp_csr_probe_2026-10-04')
if out.exists():raise ValueError('fresh output required')
csr=Path('experiments/clma_prepared_csr_2026-10-04/csr');reference=Path('experiments/clma_full_goal_astar_2026-10-04/prediction.json');binary=Path('build/routecast_csr_consumer').resolve()
assert sha(reference)=='e162fd20f6cd70bb2b713c57d5b607569c3d7889b596012aafa355c8958de68a'
data=json.loads(reference.read_text());manifest,fields=read(csr,data['physical_graph_sha256'],'6b51650f3ac0ba59b39ee3b556cfa201c336691a0a88721ac21437ea0ecd36f6');del fields
inputs={'reference':sha(reference),'manifest':sha(csr/'manifest.json'),'binary':sha(binary),'source':sha('tools/csr_consumer/main.cpp'),'driver':sha(__file__)}
groups={}
for c in data['connections']:groups.setdefault(c['net_id'],[]).append(c)
selected=sorted(groups)[:100];out.mkdir();shutil.copyfile('tools/csr_consumer/main.cpp',out/'main.cpp');shutil.copyfile(__file__,out/'driver.py');(out/'protocol.json').write_text(json.dumps({'inputs':inputs,'selection':'ascending first100netIDs; no quality-label selection','scope':'host C++ canonical paths, not HLS or performance proof'},indent=2)+'\n');start=time.monotonic();results=[];connections=0
for net in selected:
 cs=groups[net];assert len({c['source'] for c in cs})==1
 result=json.loads(subprocess.check_output([str(binary),str(csr),str(cs[0]['source']),*map(str,sorted({c['sink'] for c in cs}))],text=True))
 for c in cs:assert result['paths'][str(c['sink'])]==c['physical_edge_ids'];connections+=1
 assert not result['budget_exhausted'];results.append({'net_id':net,'result':result})
(out/'results.json').write_text(json.dumps(results)+'\n');assert sha(binary)==inputs['binary'] and sha(reference)==inputs['reference'];read(csr,data['physical_graph_sha256'],manifest['context_sha256'])
receipt={'nets':len(selected),'connections':connections,'all_canonical_paths_exact':True,'elapsed_s':time.monotonic()-start,'protocol_sha256':sha(out/'protocol.json'),'results_sha256':sha(out/'results.json'),'source_sha256':sha(out/'main.cpp'),'driver_sha256':sha(out/'driver.py')};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
