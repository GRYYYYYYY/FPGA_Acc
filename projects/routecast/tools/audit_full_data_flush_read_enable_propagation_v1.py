"""Exact BLIF reductions tied to actual existing counter/control observations."""
import hashlib,itertools,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'full_ram_init_export_runtime_v8_2026-10-09/design.blif';L=E/'full_source_export_startup_tag_write_trace_v21_2026-10-09/control.log';G=E/'full_native_ram_gates_v3_2026-10-09/gates.json';lines=B.read_text().replace('\\\n',' ').splitlines();tables={};i=0
while i<len(lines):
 t=lines[i].split();i+=1
 if t and t[0]=='.names':
  rows=[]
  while i<len(lines) and not lines[i].lstrip().startswith('.'):
   row=lines[i].split();i+=1
   if row and not row[0].startswith('#'):rows.append(row)
  tables[t[-1]]={'inputs':t[1:-1],'rows':rows}
def evaluate(node,vals):
 t=tables[node];assert len(vals)==len(t['inputs']);polarity={r[-1] for r in t['rows']};assert len(polarity)==1;outputs=set()
 for assignment in itertools.product(*[('0','1') if v=='x' else (v,) for v in vals]):
  covered=any(all(p=='-' or p==v for p,v in zip(row[0],assignment)) for row in t['rows']);outputs.add(('1' if covered else '0') if polarity=={'1'} else ('0' if covered else '1'))
 return next(iter(outputs)) if len(outputs)==1 else 'x'
assert tables['new_n5938']['inputs']==['b2018','b602','b574','new_n5939','b2016','b3451']
cases=0
for values in itertools.product('01x',repeat=5):
 a,b,c,d,high=values;assert evaluate('new_n5938',[a,b,c,d,high,'0'])==high;cases+=1
assert tables['new_n6108']['inputs']==['new_n5374','new_n5324','new_n5367','new_n5375','new_n5938','new_n5940']
for a,b,high in itertools.product('01x',repeat=3):assert evaluate('new_n6108',[a,'1',b,'0',high,'1'])==high;cases+=1
log=L.read_text();boundary={};nodes={}
for match in re.finditer(r'PIPE_BOUNDARY cycle=\s*(\d+) index=(\d+) value=([01x])',log):boundary[(int(match[1]),int(match[2]))]=match[3]
for match in re.finditer(r'PIPE_NODE cycle=\s*(\d+) net=(\S+) value=([01x])',log):nodes[(int(match[1]),match[2])]=match[3]
records=[]
for cycle in [3,4,5]:
 high=boundary[(cycle,1)];execute=boundary[(cycle,6)];assert execute=='0' and nodes[(cycle,'new_n5324')]=='1' and nodes[(cycle,'new_n5375')]=='0' and nodes[(cycle,'new_n5940')]=='1';assert nodes[(cycle,'new_n5938')]==high
 records.append({'cycle':cycle,'data_flush_high':high,'execute_valid':execute,'new_n5938':nodes[(cycle,'new_n5938')],'new_n5324':nodes[(cycle,'new_n5324')],'new_n5375':nodes[(cycle,'new_n5375')],'new_n5940':nodes[(cycle,'new_n5940')],'derived_new_n6108':high})
m=max(json.loads(G.read_text())['modules'].values(),key=lambda m:len(m.get('cells',{})));assert m['netnames']['dataCache_1.stageB_flusher_counter']['bits'][7]==2016
out={'exhaustive_reduction_cases':cases,'observations':records,'tables':{n:tables[n] for n in ['new_n5938','new_n6108']},'hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [B,L,G]},'conclusion':'Under observed execute_valid=0, new_n5938 equals actual DataCache flush counter[7] even with arbitrary other 0/1/X inputs. Under observed controls new_n6108 equals new_n5938. Combined with prior actual LUT audit, cycle4 counter-high X locally propagates to IBus read enable X.','scope':'Existing actual postedge observations and exact function reductions, not origin of counter X, proof of all mismatch causality or complete Full equivalence.'};D=E/'full_data_flush_read_enable_propagation_v1_2026-10-09';D.mkdir(exist_ok=True);(D/'propagation_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'reduction_cases':cases,'observations':records},indent=2))
