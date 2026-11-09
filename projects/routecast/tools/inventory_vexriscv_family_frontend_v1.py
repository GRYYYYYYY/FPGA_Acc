"""Whole frozen family parse/hierarchy/proc inventory, without routing or QoR selection."""
import json,subprocess,time
from collections import Counter
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'vexriscv_family_frontend_inventory_v1_2026-10-09';D.mkdir(exist_ok=False)
manifest=E/'prospective_family_candidates_2026-10-06/manifest.json';members=[r for r in json.loads(manifest.read_text())['records'] if r['family_candidate']=='vexriscv'];assert len(members)==32
old=json.loads((E/'vexriscv_smallest_frontend_candidate_2026-10-06/protocol.json').read_text());yosys=Path(old['yosys']['yosys_path']);assert sha(yosys)==old['yosys']['sha256']
bindings={str(p):sha(p) for p in (Path(__file__).resolve(),manifest,yosys)}
for r in members:
 p=R/r['archived_path'];assert sha(p)==r['sha256'];bindings[str(p)]=r['sha256']
plan=dict(bindings=bindings,members=members,policy='All 32 members, hierarchy -auto-top; proc only. No synth optimization or QoR selection.',timeout_each_s=120,unseen_family_status='UNPROVEN',scope='Frontend inventory only; no route labels, equivalence proof, timing requirements or holdout admission.')
(D/'protocol.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[]
for r in members:
 source=R/r['archived_path'];out=D/source.stem;out.mkdir();(out/'design.v').write_bytes(source.read_bytes());(out/'inventory.ys').write_text('read_verilog design.v\nhierarchy -check -auto-top\nproc\ncheck\nwrite_json design.json\n')
 start=time.perf_counter()
 with (out/'log.txt').open('x') as log:
  try:code=subprocess.run([str(yosys),'-s','inventory.ys'],cwd=out,stdout=log,stderr=subprocess.STDOUT,timeout=120).returncode
  except subprocess.TimeoutExpired:code='TIMEOUT'
 row=dict(member=source.stem,exit_code=code,seconds=time.perf_counter()-start)
 if code==0:
  modules=json.loads((out/'design.json').read_text())['modules'];tops=[n for n,m in modules.items() if int(m.get('attributes',{}).get('top','0'),2)==1];assert len(tops)==1
  types=Counter(c['type'] for m in modules.values() for c in m['cells'].values());init=[dict(module=n,net=k,value=v['attributes']['init']) for n,m in modules.items() for k,v in m['netnames'].items() if 'init' in v.get('attributes',{})]
  row.update(top=tops[0],modules=len(modules),hierarchical_cell_types=dict(types),init_nets=init,scope='Counts per module definition, not flattened instance multiplicity; proc-level cells only.')
 rows.append(row);(D/'progress.json').write_text(json.dumps(rows,indent=2)+'\n');print(source.stem,code,row.get('top'),flush=True)
files={str(p):sha(p) for p in D.rglob('*') if p.is_file()};(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,files=files,members=rows,scope=plan['scope']),indent=2)+'\n')
