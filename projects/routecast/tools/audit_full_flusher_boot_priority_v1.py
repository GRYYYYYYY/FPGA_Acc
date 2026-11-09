"""Full actual boot-start counter low-bit priority with unknown singleLine."""
import json,itertools,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/full_flusher_boot_priority_v1_2026-10-09';D.mkdir(exist_ok=True)
A=R/'experiments/full_flusher_counter_export_luts_v1_2026-10-09/audit.json';S=R/'experiments/full_source_export_fixed_bus_replay_v19_2026-10-09/reference.v';rs=json.loads(A.read_text())['records'];source=S.read_text();block='\n'.join(source.splitlines()[7423:7430]);assert "stageB_flusher_counter <= 8'h0;" in block and 'if(io_cpu_flush_payload_singleLine)' in block
inv=lambda a:{'0':'1','1':'0','x':'x'}[a]
def AND(a,b):return '0' if '0' in [a,b] else ('1' if a==b=='1' else 'x')
def ev(rec,values):
 pins=[r['constant'] if 'constant' in r else values.get(r['node'],'x') for r in rec['input_routes_lsb_first']]
 vs={rec['mask'][-1-sum(int(b)<<i for i,b in enumerate(bs))] for bs in itertools.product(*[['0','1'] if b=='x' else [b] for b in pins])};return next(iter(vs)) if len(vs)==1 else 'x'
for zero,line in itertools.product('01x',repeat=2):assert ev(rs[8],{'new_n6607':zero,'b516':line})==AND(inv(zero),line)
rows=[]
for lane,rec in enumerate(rs[:8]):
 for zero,line in itertools.product('01x',repeat=2):
  vals={'b3121':'1','new_n6607':zero,'b'+str(506+2*lane):line,'new_n6616':AND(inv(zero),line)}
  actual=ev(rec,vals);expected='0' if lane==7 else AND(inv(zero),line);assert actual==expected,(lane,zero,line,actual,expected)
  original='0' if lane==7 or zero!='0' else line
  rows.append({'lane':lane,'start':'1','zero_instruction':zero,'lineId_bit':line,'original_procedural_D':original,'native_export_D':actual,'different':actual!=original})
assert sum(r['different'] for r in rows)==14
out={'original_start_block':block,'rows':rows,'ternary_cases':72,'differences':14,'conclusion':'With knownstart1, nativecounterhighD0; low7D=!zeroInstruction AND lineIdbit. Original if(singleLineX) skips override and clearslow7D0. Each lowlane can differ when zeroInstructionX and lineIdbit1/X; knownlineId0 masks it.','scope':'Actual export8counter masks/routes plus foldedlane5AND6616 binding; local bootpriority semantic model with otherinputsunknown. Not newly observedfullcounterlowD/Q history or completefunctionaladmission.','hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [A,S]}}
(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print('PASS72actualcounterprioritycases;14unknownsemanticdifferences')
