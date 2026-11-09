"""Exhaustive exact eight-bit native BLIF start capture versus original RTL rule."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'full_ram_init_export_runtime_v8_2026-10-09/design.blif';G=E/'full_native_ram_gates_v3_2026-10-09/gates.json';S=E/'full_source_export_fixed_bus_replay_v19_2026-10-09/reference.v';lines=B.read_text().splitlines();tables={};i=0
while i<len(lines):
 t=lines[i].split();i+=1
 if t and t[0]=='.names':
  rows=[]
  while i<len(lines) and not lines[i].lstrip().startswith('.'):
   z=lines[i].split();i+=1
   if z and not z[0].startswith('#'):rows.append(z)
  tables[t[-1]]={'inputs':t[1:-1],'rows':rows}
m=max(json.loads(G.read_text())['modules'].values(),key=lambda x:len(x.get('cells',{})));q=m['netnames']['dataCache_1.stageB_flusher_counter']['bits'];drivers={b:c for c in m['cells'].values() for p,bs in c['connections'].items() if c['port_directions'][p]=='output' for b in bs};ds=['b'+str(drivers[b]['connections']['D'][0]) for b in q];start='b'+str(m['netnames']['dataCache_1.stageB_flusher_start']['bits'][0]);assert start=='b3121';reduced={}
for n in ds:
 t=tables[n];assert {r[-1] for r in t['rows']}=={'1'};j=t['inputs'].index(start);rows=[(r[0][:j]+r[0][j+1:],r[1]) for r in t['rows'] if r[0][j]!='0'];inputs=t['inputs'][:j]+t['inputs'][j+1:];reduced[n]={'inputs':inputs,'rows':rows}
addr=m['netnames']['dataCache_1.io_cpu_flush_payload_lineId']['bits'];instruction=m['netnames']['execute_INSTRUCTION']['bits'][15:20];leaves={'b'+str(b) for b in addr+instruction};used={}
def dependencies(n):
 if n in leaves:return {n}
 t=reduced.get(n,tables.get(n));assert t is not None,n;used[n]=t;reached=set()
 for j,x in enumerate(t['inputs']):
  if any(r[0][j]!='-' for r in t['rows']):reached|=dependencies(x)
 return reached
actual_deps=set().union(*(dependencies(n) for n in ds));assert actual_deps<=leaves

def evaluate(n,values):
 if n in values:return values[n]
 t=used[n];covered=False
 for pattern,y in t['rows']:
  if all(p=='-' or p==evaluate(x,values) for p,x in zip(pattern,t['inputs'])):covered=True;break
 return str(int(covered))
cases=0
for field in range(32):
 for line in range(128):
  values={'b'+str(b):str((line>>i)&1) for i,b in enumerate(addr)}|{'b'+str(b):str((field>>i)&1) for i,b in enumerate(instruction)}
  native=sum(int(evaluate(n,values))<<i for i,n in enumerate(ds));source=line if field!=0 else 0;assert native==source,(field,line,native,source);cases+=1
source=S.read_text();assert 'if(stageB_flusher_start) begin' in source and "stageB_flusher_counter <= {1'b0,io_cpu_flush_payload_lineId};" in source
out={'exhaustive_cases':cases,'counter_Q_bits':q,'counter_D_nodes':ds,'start_bit':start,'actual_reduced_tables':used,'remaining_dependencies':sorted(actual_deps),'hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [B,G,S]},'scope':'Complete8-bit start1/reset0 update, all32 known instruction fields and128 known line addresses. Exact cube pruning proves old counter/other controls irrelevant under start1; no uninitialized state assigned0. Does not prove all non-start transitions, shared initial relation, memory/event semantics, or Full/scientific admission.'}
d=E/'full_flush_binary_start_capture_v1_2026-10-09';d.mkdir(exist_ok=True);(d/'binary_capture_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['actual_reduced_tables','hashes']},indent=2))
