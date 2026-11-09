"""Canonical zero-fixup physical path preservation and published QoR check."""
import json,re
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
from stream_native_route_audit_cached import audit
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'experiments/mux32_continuous_canonical_2026-10-07';rp=base/'receipt.json';r=json.loads(rp.read_text());p=json.loads((base/'protocol.json').read_text());assert r['protocol_sha256']==sha(base/'protocol.json') and all(sha(f)==h for f,h in {**p['sources'],**p['inputs']}.items());reload=r['reload'];assert reload['exit_code']==0 and reload['mismatches']==reload['fixups']==0 and all(sha(f)==h for f,h in reload['files'].items())
raw=ROOT/'experiments/mux32_continuous_native_2026-10-07';rv=json.loads((raw/'verification.json').read_text());assert rv['joint_nonregression'] and r['parent_native_receipt_sha256']==sha(raw/'receipt.json')
route=next(Path(f) for f in reload['files'] if f.endswith('/design.route'));original=raw/'design.route';paths=lambda file:{k:sorted(v) for k,v in physical_paths(file).items() if v};assert paths(route)==paths(original)
logpath=next(Path(f) for f in reload['files'] if f.endswith('/reload.log'));log=logpath.read_text()
for marker in ('RouterOpts.check_route: FULL','Completed routing consistency check successfully.','VPR succeeded'):assert marker in log
wire=int(re.findall(r'Total wirelength:\s*(\d+)',log)[-1]);cpd=re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[-1];assert wire==rv['raw_native_wirelength'] and F(cpd)==F(rv['raw_native_cpd_ns']) and wire<=rv['published_wirelength'] and F(cpd)<=F(rv['published_native_cpd_ns'])
graph=Path(reload['command'][reload['command'].index('--read_rr_graph')+1]);a=audit(graph,route);assert a['overflow_units']==0 and len(a['connections'])==1929
result=dict(source_sha256=sha(Path(__file__)),receipt_sha256=sha(rp),raw_verification_sha256=sha(raw/'verification.json'),canonical_route_sha256=sha(route),original_route_sha256=sha(original),connections=1929,canonical_cpd_ns=cpd,canonical_wirelength=wire,zero_fixups=True,physical_paths_preserved=True,joint_nonregression=True,scope='Development single move canonical own-packing FULL/STA, exact NET-name paths and original physical capacity audit. No live publication, prospective result or full-loop time gain.')
(base/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
