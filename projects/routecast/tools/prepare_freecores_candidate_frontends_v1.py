"""Fixed three candidate frontend diagnostics, no route labels or result selection."""
import json,sys,subprocess,shutil,time
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
inventory=R/'experiments/freecores_unseen_candidate_inventory_v1_2026-10-08/inventory.json'
d=json.loads(inventory.read_text());assert [x['filename'] for x in d['candidates']]==['8051.v','mips_16.v','xtea.v']
assert all(sha(x['path'])==x['sha256'] for x in d['candidates'])
toolfile=R/'experiments/prospective_family_candidates_2026-10-06/frontend_availability.json';tool=json.loads(toolfile.read_text());yosys=Path(tool['yosys_path']);assert sha(yosys)==tool['sha256']
out=R/'experiments/freecores_candidate_frontends_v1_2026-10-08';out.mkdir()
bindings={**closure([Path(__file__)]),str(inventory):sha(inventory),str(toolfile):sha(toolfile),str(yosys):sha(yosys)}
cases=[]
for candidate,top in zip(d['candidates'],['oc8051_top','mips_16_core_top','xtea']):
 source=Path(candidate['path']);name=source.stem;w=out/name;w.mkdir();shutil.copyfile(source,w/'design.v');bindings[str(source)]=sha(source);bindings[str(w/'design.v')]=sha(w/'design.v')
 script=w/'synth.ys';script.write_text(f'read_verilog design.v\nhierarchy -check -top {top}\nsynth -top {top} -flatten -lut 6\ndffunmap\ncheck -assert\nstat\nwrite_json design.json\nwrite_blif design.blif\n');bindings[str(script)]=sha(script)
 cases.append(dict(name=name,top=top,command=[str(yosys),'-s','synth.ys']))
(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,cases=cases,timeout_per_case_seconds=120,order='8051 then MIPS16 then XTEA, all outcomes retained',scope='Candidate frontend compatibility diagnostics only, no native labels. Not HDL equivalence or global prior-use/family-split proof. Prospective source-project lineage differs from AES/Ethernet; processor/cryptography domains may overlap prior development, so no broad-domain unseen claim. Architecture not silently modified to fit results.'),indent=2)+'\n')
rows=[]
for case in cases:
 w=out/case['name'];tick=time.perf_counter()
 try:
  with (w/'synthesis.log').open('w') as log:code=subprocess.run(case['command'],cwd=w,stdout=log,stderr=subprocess.STDOUT,timeout=120).returncode
 except subprocess.TimeoutExpired:code='TIMEOUT'
 row=dict(name=case['name'],exit_code=code,seconds=time.perf_counter()-tick)
 if code==0:
  net=json.loads((w/'design.json').read_text());cells=net['modules'][case['top']]['cells'];row['cell_types']=dict(sorted(Counter(c['type'] for c in cells.values()).items()));row['cells']=len(cells)
 row['files']={str(p):sha(p) for p in w.iterdir() if p.is_file()};rows.append(row);(out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(case['name'],code,row.get('cell_types'),flush=True)
assert all(sha(k)==v for k,v in bindings.items())
(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,protocol_sha256=sha(out/'protocol.json'),rows=rows,frontend_only=True,native_labels_generated_or_read=False),indent=2)+'\n')
