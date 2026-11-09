"""Original procedural halt versus Boolean-lowered halt, logical ternary truth cases."""
from pathlib import Path
import json,hashlib,itertools
R=Path(__file__).resolve().parents[1];D=R/'experiments/full_ibus_ready_unknown_semantics_v1_2026-10-09';D.mkdir(exist_ok=True)
f=R/'experiments/full_source_export_fixed_bus_replay_v19_2026-10-09/reference.v';ls=f.read_text().splitlines();block='\n'.join(ls[3625:3634]);assert 'if(when_IBusCachedPlugin_l267)' in block and "halt = 1'b0" in block and "halt = 1'b1" in block
inv=lambda a:{'0':'1','1':'0','x':'x'}[a]
AND=lambda a,b:'0' if '0' in (a,b) else ('1' if a==b=='1' else 'x')
rows=[]
for stuck,issue in itertools.product('01x',repeat=2):
 original=AND(inv(stuck),inv('1' if issue=='1' else '0'))
 lowered=AND(inv(stuck),inv(issue))
 rows.append({'decode_stuck':stuck,'issue_detected':issue,'original_procedural_ready':original,'boolean_lowered_ready':lowered,'different':original!=lowered})
assert sum(r['different'] for r in rows)==1
out={'rows':rows,'original_block':block,'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'scope':'Logical ternary truth-case semantic model, not simulator/fulltrace. Under busy0/outputhalt0, original if(X) skips halt assignment. Boolean-lowered ready differs at stuck0/issueX. Actual source/native boundaries/history must be traced before diagnosing observed replay.'}
(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps([r for r in rows if r['different']],indent=2))
