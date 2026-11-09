"""Prospective frontend compatibility candidate; preserve async reset semantics."""
import json,shutil,subprocess,time
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'vexriscv_flattened_candidate_v1_2026-10-09';D.mkdir(exist_ok=False)
prior=E/'vexriscv_smallest_frontend_candidate_2026-10-06';protocol=json.loads((prior/'protocol.json').read_text());receipt=json.loads((prior/'receipt.json').read_text());assert sha(prior/'protocol.json')==receipt['protocol_sha256']
source=R/protocol['input']['archived_path'];yosys=Path(protocol['yosys']['yosys_path']);assert sha(source)==protocol['input']['sha256'] and sha(yosys)==protocol['yosys']['sha256']
shutil.copyfile(source,D/'design.v')
script='read_verilog design.v\nhierarchy -check -top VexRiscvSmallest\nsynth -top VexRiscvSmallest -flatten -lut 6\ndffunmap\ncheck -assert\nstat\nwrite_json design.json\nwrite_blif design.blif\n';(D/'synth.ys').write_text(script)
bindings={str(p):sha(p) for p in (Path(__file__).resolve(),source,yosys,prior/'protocol.json',prior/'receipt.json',D/'design.v',D/'synth.ys')}
manifest=E/'prospective_family_candidates_2026-10-06/manifest.json';m=json.loads(manifest.read_text());family=[r for r in m['records'] if r['family_candidate']=='vexriscv']
for row in family:assert sha(R/row['archived_path'])==row['sha256']
plan=dict(bindings=bindings,whole_family_members=[dict(path=r['archived_path'],sha256=r['sha256']) for r in family],candidate='VexRiscvSmallest only for inherited frontend readiness; all32 variants remain one family',command=[str(yosys),'-s','synth.ys'],timeout_s=600,scope='Freeze before frontend only. No route labels, outcome selection, async2sync or reset stripping; no heldout, formal equivalence, physical endpoints or timing claim.')
(D/'protocol.json').write_text(json.dumps(plan,indent=2)+'\n');start=time.perf_counter()
with (D/'synthesis.log').open('x') as log:code=subprocess.run(plan['command'],cwd=D,stdout=log,stderr=subprocess.STDOUT,timeout=600).returncode
assert code==0
net=json.loads((D/'design.json').read_text());assert set(net['modules'])=={'VexRiscvSmallest'};module=net['modules']['VexRiscvSmallest'];types=Counter(cell['type'] for cell in module['cells'].values())
luts=[cell for cell in module['cells'].values() if cell['type']=='$lut'];assert all(int(cell['parameters']['WIDTH'],2)<=6 for cell in luts)
unsupported={k:v for k,v in types.items() if k!='$lut' and k!='$_DFF_P_'}
for p in D.iterdir():
 if p.is_file():bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items())
report=dict(bindings=bindings,exit_code=code,frontend_seconds=time.perf_counter()-start,module_count=1,cell_types=dict(types),lut_count=len(luts),unsupported_for_plain_lut_latch_native_frontend=unsupported,ready_for_unmodified_native_input=not unsupported,scope='Flattened mapped candidate, LUT width audit only; nonplain sequential cells retained and reported. No semantic equivalence or unseen-family claim, not routed.')
(D/'receipt.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k!='bindings'},flush=True)
