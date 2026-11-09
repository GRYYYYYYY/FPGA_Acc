"""Bounded Full comparison completion and aggregate instruction-response audit."""
from pathlib import Path
import json,re,hashlib
root=Path(__file__).resolve().parents[1]
p=root/'experiments/full_source_export_ibus_protocol_v6_2026-10-09'
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
protocol=json.loads((p/'protocol.json').read_text())
for name,h in protocol['bindings'].items():assert sha(name)==h
stages=json.loads((p/'stages.json').read_text());assert len(stages)==3 and all(s['exit_code']==0 for s in stages)
r=json.loads((p/'receipt.json').read_text());assert r['exit_code']==0
log=(p/'control.log').read_text();m=re.search(r'ROUTECAST_FULL_COMPARE_DONE mismatches=\s*(\d+)',log);cov=re.search(r'IBUS_COVERAGE requests=\s*(\d+) responses=\s*(\d+) outstanding=\s*(\d+)',log)
assert m and cov and 'reason="finish"' in log and 'Fatal:' not in log
req,rsp,outstanding=map(int,cov.groups());assert req>0 and rsp>=8 and 0<=outstanding<=8 and rsp+outstanding==8*req
source=(p/'reference.v').read_text().split(');',1)[0];expected=set()
for direction,width,name in re.findall(r'^\s*(input|output)\s+(?:reg\s+)?(?:\[(\d+):0\]\s+)?(\w+)\s*,?\s*$',source,re.M):
 if direction=='output':expected.update([f'{name}[{i}]' for i in range(int(width)+1)] if width else [name])
tb=(p/'tb.v').read_text();assert set(re.findall(r'signal=([^ ]+) export=',tb))==expected and len(expected)==145
assert 'for(i=0;i<512;i=i+1)' in tb
report={'requests':req,'response_words':rsp,'remaining_words':outstanding,'aggregate_conservation_passed':True,'output_mismatches':int(m[1]),'output_checks':513*145,'equality_on_this_trace':int(m[1])==0,'full_equivalence_proven':False,'bindings':{str(f):sha(f) for f in [Path(__file__),p/'protocol.json',p/'receipt.json',p/'control.log',p/'tb.v',p/'stages.json']},'scope':'Bounded diagnostic comparison and aggregate counters; on-cycle protocol assertions are testbench checks, no independent transaction trace replay or instruction retirement evidence.'}
(p/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='bindings'}))
