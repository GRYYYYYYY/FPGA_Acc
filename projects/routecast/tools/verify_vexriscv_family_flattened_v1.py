"""Independent complete family census and frozen artifact authentication."""
import json,hashlib
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];B=R/'experiments/vexriscv_family_flattened_inventory_v1_2026-10-09';D=R/'experiments/vexriscv_family_flattened_verification_v1_2026-10-09'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
r=json.loads((B/'receipt.json').read_text());p=json.loads((B/'protocol.json').read_text())
for path,digest in {**r['bindings'],**r['files']}.items():assert sha(path)==digest
assert r['bindings']==p['bindings'];rows=r['members'];expected=[Path(x['archived_path']).stem for x in p['members']];assert len(expected)==32 and len(set(expected))==32;assert [x['member'] for x in rows]==expected
assert json.loads((B/'progress.json').read_text())==rows
models=Counter();failures=[];passing=[]
for x in rows:
 folder=B/x['member'];script=(folder/'inventory.ys').read_text();assert script=='read_verilog design.v\nhierarchy -check -auto-top\nsynth -flatten -noabc\ndffunmap\ncheck -assert\nwrite_json design.json\n'
 original=R/next(a['archived_path'] for a in p['members'] if Path(a['archived_path']).stem==x['member']);assert sha(folder/'design.v')==sha(original)
 if x['exit_code']!=0:
  failures.append(dict(member=x['member'],exit_code=x['exit_code'],errors=[line for line in (folder/'log.txt').read_text().splitlines() if 'ERROR:' in line]));continue
 modules=json.loads((folder/'design.json').read_text())['modules'];assert len(modules)==1 and list(modules)==[x['top']]
 census=Counter(c['type'] for m in modules.values() for c in m['cells'].values());assert dict(census)==x['hierarchical_cell_types'];models.update(census)
 init=[dict(module=n,net=k,value=v['attributes']['init']) for n,m in modules.items() for k,v in m['netnames'].items() if 'init' in v.get('attributes',{})];assert init==x['init_nets'];passing.append(dict(member=x['member'],cells=dict(census),init_net_count=len(init)))
D.mkdir(exist_ok=False);report=dict(bindings={str(Path(__file__).resolve()):sha(__file__),str(B/'receipt.json'):sha(B/'receipt.json'),str(B/'protocol.json'):sha(B/'protocol.json')},members=32,passed=len(passing),failed=len(failures),successful_members=passing,failures=failures,aggregate_cells=dict(models),scope='All-family structural flattened census and artifact/source authentication. No HDL equivalence, LUT mapping, reset timing, unseen admission or prediction quality proof.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(dict(members=32,passed=len(passing),failed=len(failures),models=dict(models)))
