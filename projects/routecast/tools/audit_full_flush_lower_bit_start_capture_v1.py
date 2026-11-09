"""Actual lower-counter capture LUT and carry cone dependency checks."""
import hashlib,itertools,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'full_ram_init_export_runtime_v8_2026-10-09/design.blif';G=E/'full_native_ram_gates_v3_2026-10-09/gates.json';lines=B.read_text().replace('\\\n',' ').splitlines();tables={};i=0
while i<len(lines):
 t=lines[i].split();i+=1
 if t and t[0]=='.names':
  rows=[]
  while i<len(lines) and not lines[i].lstrip().startswith('.'):
   z=lines[i].split();i+=1
   if z and not z[0].startswith('#'):rows.append(z)
  tables[t[-1]]={'inputs':t[1:-1],'rows':rows}
def ev(n,v):
 t=tables[n];pol={r[-1] for r in t['rows']};assert len(pol)==1;answers=set()
 for a in itertools.product(*[('0','1') if x=='x' else (x,) for x in v]):
  covered=any(all(p=='-' or p==x for p,x in zip(r[0],a)) for r in t['rows']);answers.add(str(int(covered)) if pol=={'1'} else str(int(not covered)))
 return next(iter(answers)) if len(answers)==1 else 'x'
t=tables['b2013'];assert t['inputs']==['new_n6607','b518','b2016','new_n6618','b2014','b3121'];count=0
for gate,line,high,carry,old in itertools.product('01x',repeat=5):
 expected=ev('b2013',[gate,line,high,carry,old,'1'])
 # With start1 the actual cover is !gate AND incoming line-address lane6.
 simple='0' if gate=='1' or line=='0' else '1' if gate=='0' and line=='1' else 'x'
 assert expected==simple;count+=1
m=max(json.loads(G.read_text())['modules'].values(),key=lambda x:len(x.get('cells',{})));assert m['netnames']['dataCache_1.stageB_flusher_counter']['bits'][6]==2014
linealiases=[n for n,v in m['netnames'].items() if 518 in v['bits'] and not n.startswith('$')];assert any('flush_payload_lineId' in n for n in linealiases)
# Expand only AND covers in actual carry cone.
visited={};leaves=set()
def walk(n):
 if n not in tables:leaves.add(n);return
 t=tables[n];assert t['rows']==[['1'*len(t['inputs']),'1']],(n,t);visited[n]=t
 for x in t['inputs']:walk(x)
walk('new_n6618');assert leaves=={'b2002','b2004','b2006','b2008','b2010','b2012'}
out={'start_capture_checked_cases':count,'lower_lane6_D_table':t,'actual_lower_lane6_Q':2014,'line_address_lane_aliases':linealiases,'carry_cone':visited,'carry_leaves':sorted(leaves),'start1_gateX_lineX_D':ev('b2013',['x','x','0','0','0','1']),'hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [B,G]},'scope':'Actual LUT reduction under start1 and exact lower-six-bit AND carry cone. Unknown incoming line/control gives lower D X while source procedural-if may skip, but actual first pre-edge values and source/native event pairing are not established here. No complete replay or causality admission.'}
d=E/'full_flush_lower_bit_start_capture_v1_2026-10-09';d.mkdir(exist_ok=True);(d/'capture_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['carry_cone','hashes','lower_lane6_D_table']},indent=2))
