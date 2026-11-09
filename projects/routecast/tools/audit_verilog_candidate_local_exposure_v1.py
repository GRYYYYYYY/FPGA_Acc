"""Scoped local basename/hash references and declared module-name overlap."""
import json,sys,subprocess
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
p=R/'experiments/verilog_candidate_origin_inventory_v1_2026-10-10/inventory.json';v=json.loads(p.read_text());assert all(sha(r['path'])==r['sha256'] for r in v['rows']);D=R/'experiments/verilog_candidate_local_exposure_v1_2026-10-10';D.mkdir();bindings={str(Path(__file__)):sha(Path(__file__)),str(p):sha(p)};owners=defaultdict(set);rows=[]
for candidate in v['rows']:
 name=Path(candidate['path']).name
 for module in candidate['declared_module_names']:owners[module].add(name)
 # Ignore inventory-only provenance outputs; preserve all other matches as references, not route exposure proof.
 args=['rg','-l','-F','--max-filesize','2M','--glob','*.py','--glob','*.json','--glob','*.md','--glob','!verilog_candidate_origin_inventory_v1_2026-10-10/**','--glob','!verilog_candidate_local_exposure_v1_2026-10-10/**', '-e',name,'-e',candidate['sha256'],'tools','experiments']
 r=subprocess.run(args,cwd=R,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);assert r.returncode in [0,1],r.stderr
 paths=[x for x in r.stdout.splitlines() if 'verilog_candidate_origin_inventory_v1_2026-10-10/' not in x and 'verilog_candidate_local_exposure_v1_2026-10-10/' not in x and x!=str(Path(__file__).relative_to(R))]
 for x in paths:bindings[str(R/x)]=sha(R/x)
 rows.append(dict(name=name,source_sha256=candidate['sha256'],local_reference_files=paths,local_reference_detected=bool(paths),strict_family_admitted=False))
overlap=[dict(declared_module=module,files=sorted(names)) for module,names in sorted(owners.items()) if len(names)>1]
assert all(sha(k)==h for k,h in bindings.items())
(D/'audit.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,shared_declared_module_names=overlap,scope='Case-sensitive basename/hash string references in RouteCast tools/experiments py/json/md files <=2MiB, ignores two inventory outputs. Reference is not necessarily label/model exposure; absence not global unseen proof. Module declarations are regex-derived names, not structural equivalence or family proof. Excludes shared TilePlace history, archives/large vectors/binaries and global prior work. All strict admission flags false.'),indent=2)+'\n')
print('LOCAL EXPOSURE',len(rows),'candidates',sum(r['local_reference_detected'] for r in rows),'referenced;',len(overlap),'shared module names')
