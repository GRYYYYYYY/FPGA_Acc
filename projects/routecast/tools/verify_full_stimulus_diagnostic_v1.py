"""Verify actual completion and classify bounded source/export comparison results."""
from pathlib import Path
import json,re,hashlib,sys
root=Path(__file__).resolve().parents[1]
p=root/'experiments'/sys.argv[1]
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
protocol=json.loads((p/'protocol.json').read_text())
for file,h in protocol['bindings'].items():assert sha(file)==h
stages=json.loads((p/'stages.json').read_text());assert len(stages)==3 and all(s['exit_code']==0 for s in stages)
receipt=json.loads((p/'receipt.json').read_text());assert receipt['exit_code']==0
log=(p/'control.log').read_text();match=re.search(r'ROUTECAST_FULL_COMPARE_DONE mismatches=\s*(\d+)',log);assert match and 'reason="finish"' in log
source=(p/'reference.v').read_text().split(');',1)[0];expected=set()
for direction,width,name in re.findall(r'^\s*(input|output)\s+(?:reg\s+)?(?:\[(\d+):0\]\s+)?(\w+)\s*,?\s*$',source,re.M):
 if direction=='output':expected.update([f'{name}[{i}]' for i in range(int(width)+1)] if width else [name])
tb=(p/'tb.v').read_text();checked=set(re.findall(r'signal=([^ ]+) export=',tb));assert checked==expected and len(checked)==145
assert 'for(i=0;i<128;i=i+1)' in tb
report={'output_mismatches':int(match[1]),'comparison_snapshots':129,'output_bits':145,'output_checks':18705,'execution_completed':True,'equality_on_this_trace':int(match[1])==0,'full_equivalence_proven':False,'bindings':{str(f):sha(f) for f in [Path(__file__),p/'protocol.json',p/'receipt.json',p/'control.log',p/'stages.json',p/'tb.v']},'scope':'Bounded deterministic arbitrary-input trace, diagnostic LUT consensus. No bus protocol validity, universal equivalence or physical initialization claim.'}
(p/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='bindings'}))
