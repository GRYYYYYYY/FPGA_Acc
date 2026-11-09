"""Check full actual counter reset/start/non-start binary transition behavior."""
import hashlib,json,runpy
from pathlib import Path
R=Path(__file__).resolve().parents[1];base=runpy.run_path(str(R/'tools/verify_full_flush_binary_start_capture_v1.py'));tables=base['tables'];ds=base['ds'];q=base['q'];m=base['m'];drivers=base['drivers'];start=base['start'];instruction=base['instruction'];reduced={};used={}
for n in ds:
 t=tables[n];j=t['inputs'].index(start);rows=[(r[0][:j]+r[0][j+1:],r[1]) for r in t['rows'] if r[0][j]!='1'];reduced[n]={'inputs':t['inputs'][:j]+t['inputs'][j+1:],'rows':rows}
leaves={'b'+str(b) for b in q+instruction}
def dependencies(n):
 if n in leaves:return {n}
 t=reduced.get(n,tables.get(n));assert t is not None,n;used[n]=t;result=set()
 for j,x in enumerate(t['inputs']):
  if any(r[0][j]!='-' for r in t['rows']):result|=dependencies(x)
 return result
all_deps=set().union(*(dependencies(n) for n in ds));assert all_deps<=leaves

def evaluate(n,values,cache):
 if n in values:return values[n]
 if n in cache:return cache[n]
 t=used[n];assert all(r[1]=='1' for r in t['rows'])
 result=str(int(any(all(p=='-' or p==evaluate(x,values,cache) for p,x in zip(pattern,t['inputs'])) for pattern,y in t['rows'])));cache[n]=result;return result
cases=0
for old in range(256):
 for field in range(32):
  values={'b'+str(b):str((old>>i)&1) for i,b in enumerate(q)}|{'b'+str(b):str((field>>i)&1) for i,b in enumerate(instruction)};cache={};native=sum(int(evaluate(n,values,cache))<<i for i,n in enumerate(ds))
  source=old
  if not(old&128):
   source=(old+1)&255
   if field!=0:source|=128
  assert native==source,(old,field,native,source);cases+=1
source_text=base['S'].read_text();assert 'assign when_DataCache_l850 = (! stageB_flusher_counter[7]);' in source_text;assert 'assign when_DataCache_l856 = (! stageB_flusher_hold);' in source_text
metadata=[]
for lane,b in enumerate(q):
 c=drivers[b];assert c['type']=='$_DFF_PP0_' and c['connections']['C']==[254] and c['connections']['R']==[255] and c['connections']['D']==[int(ds[lane][1:])];metadata.append({'lane':lane,'actual_cell':c})
source_lines=base['S'].read_text().splitlines();assert "  assign stageB_flusher_hold = 1'b0;" in '\n'.join(source_lines)
out={'nonstart_cases':cases,'start_cases':base['cases'],'total_binary_update_cases':cases+base['cases'],'nonstart_dependencies':sorted(all_deps),'nonstart_actual_tables':used,'reset_clock_metadata':metadata,'original_counter_block':{'first_line':7394,'lines':source_lines[7393:7431]},'hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [base['B'],base['G'],base['S']]},'scope':'Complete local counter binary reset/start/nonstart update with shared old counter/instruction/line values and actual hold0, clock254/reset255. Covers all8192 old-counter/instruction nonstart cases and4096 start cases, plus exact native reset0 cell metadata. Not a global current-state relation, arbitrary clock/reset event proof, initialization of other states, or Full/scientific admission.'}
d=R/'experiments/full_flush_binary_all_transitions_v1_2026-10-09';d.mkdir(exist_ok=True);(d/'transition_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['nonstart_actual_tables','reset_clock_metadata','original_counter_block','hashes']},indent=2))
