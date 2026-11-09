"""Source procedural issue chain is known after settled combinational evaluation."""
import json,hashlib,itertools
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/full_ibus_issue_procedural_semantics_v1_2026-10-09';D.mkdir(exist_ok=True)
f=R/'experiments/full_source_export_fixed_bus_replay_v19_2026-10-09/reference.v';s=f.read_text();block='\n'.join(s.splitlines()[3193:3221]);assert "assign IBusCachedPlugin_rsp_issueDetected = 1'b0;" in s
for n in ['239','244','250','256']:assert 'if(when_IBusCachedPlugin_l'+n+')' in block
rows=[]
for guards in itertools.product('01x',repeat=4):
 issue='0';history=[]
 for g in guards:
  if g=='1':issue='1'
  history.append(issue)
 lowered='1' if '1' in guards else ('x' if 'x' in guards else '0')
 rows.append({'guards':''.join(guards),'source_stages':history,'lowered_or':lowered,'different':issue!=lowered})
assert all('x' not in r['source_stages'] for r in rows);assert sum(r['different'] for r in rows)==15
out={'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'original_block':block,'cases':81,'rows':rows,'scope':'Semantic model of exact source four procedural set-to1 stages starting constant0. Guards are abstract independent ternary values; actual guard correlations and native export cone not claimed. Settled source issueX witness is unreachable in this chain; transient scheduler glitches not covered.'};(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print('81 cases: all source stages known; 15 abstract OR-lowering distinctions')
