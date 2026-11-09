"""Full-cohort batched host C++ transport/path parity; no speed claim."""
import json,subprocess,time,hashlib,shutil
from pathlib import Path
from prepared_csr import read,sha
out=Path('experiments/clma_cpp_workspace_full_2026-10-04')
if out.exists():raise ValueError('fresh output required')
csr=Path('experiments/clma_prepared_csr_2026-10-04/csr');reference=Path('experiments/clma_full_goal_astar_2026-10-04/prediction.json');binary=Path('build/routecast_csr_workspace').resolve()
assert sha(reference)=='e162fd20f6cd70bb2b713c57d5b607569c3d7889b596012aafa355c8958de68a'
data=json.loads(reference.read_text());manifest,fields=read(csr,data['physical_graph_sha256'],'6b51650f3ac0ba59b39ee3b556cfa201c336691a0a88721ac21437ea0ecd36f6');del fields
inputs={'reference':sha(reference),'manifest':sha(csr/'manifest.json'),'binary':sha(binary),'source':sha('tools/csr_consumer/workspace_main.cpp'),'driver':sha(__file__)}
inputs['headers']={name:sha(Path('include')/name) for name in ('indexed_heap.hpp','predecessor_path.hpp','search_workspace.hpp','search_cost.hpp','workspace_search.hpp','path_transaction.hpp')}
groups={}
for c in data['connections']:groups.setdefault(c['net_id'],[]).append(c)
selected=sorted(groups);out.mkdir();shutil.copyfile('tools/csr_consumer/workspace_main.cpp',out/'main.cpp');shutil.copyfile(__file__,out/'driver.py');(out/'protocol.json').write_text(json.dumps({'inputs':inputs,'selection':'all4809ascendingnetIDs; no quality-label selection','scope':'host C++ canonical paths, not HLS or performance proof'},indent=2)+'\n');start=time.monotonic();results=[];connections=0
for name,digest in inputs['headers'].items():
 assert sha(Path('include')/name)==digest;shutil.copyfile(Path('include')/name,out/name)
worker=subprocess.Popen([str(binary),str(csr),'--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
for net in selected:
 cs=groups[net];assert len({c['source'] for c in cs})==1
 worker.stdin.write(' '.join(map(str,[cs[0]['source'],*sorted({c['sink'] for c in cs})]))+'\n');worker.stdin.flush()
 result=json.loads(worker.stdout.readline())
 for c in cs:assert result['paths'][str(c['sink'])]==c['physical_edge_ids'];connections+=1
 assert not result['budget_exhausted'];results.append({'net_id':net,'result':result})
 if len(results)%100==0:print(json.dumps({'nets':len(results),'connections':connections}),flush=True)
worker.stdin.close();assert worker.wait()==0
assert connections==13458 and len(selected)==4809
(out/'results.json').write_text(json.dumps(results)+'\n');assert sha(binary)==inputs['binary'] and sha(reference)==inputs['reference'];read(csr,data['physical_graph_sha256'],manifest['context_sha256'])
assert all(sha(out/name)==digest==sha(Path('include')/name) for name,digest in inputs['headers'].items())
receipt={'nets':len(selected),'connections':connections,'all_canonical_paths_exact':True,'elapsed_s':time.monotonic()-start,'protocol_sha256':sha(out/'protocol.json'),'results_sha256':sha(out/'results.json'),'source_sha256':sha(out/'main.cpp'),'driver_sha256':sha(out/'driver.py')};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
