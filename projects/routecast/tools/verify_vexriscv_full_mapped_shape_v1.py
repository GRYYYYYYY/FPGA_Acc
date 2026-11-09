"""Independent mapped cut shape/DAG/declared boundary audit; not functional CEC."""
import json,hashlib
from pathlib import Path
from collections import deque,defaultdict
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'vexriscv_full_cut_mapping_v1_2026-10-09';D=E/'vexriscv_full_mapped_shape_v1_2026-10-09'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
plan=json.loads((B/'protocol.json').read_text())
for p,h in plan['bindings'].items():assert sha(p)==h
def parse(p):
 pending=[];lines=[]
 for raw in p.read_text().splitlines():
  w=raw.split()
  if not w or w[0].startswith('#'):continue
  continued=w[-1]==chr(92);pending.extend(w[:-1] if continued else w)
  if not continued:lines.append(pending);pending=[]
 assert not pending;ins=[];outs=[];gates={};current=None
 for w in lines:
  if w[0]=='.inputs':ins+=w[1:];current=None
  elif w[0]=='.outputs':outs+=w[1:];current=None
  elif w[0]=='.names':
   assert len(w)>=2 and w[-1] not in gates;current=w[-1];gates[current]=dict(inputs=w[1:-1],rows=[])
  elif w[0] in ('.model','.end'):current=None
  else:assert current is not None;gates[current]['rows'].append(w)
 assert len(ins)==len(set(ins)) and len(outs)==len(set(outs));return ins,outs,gates
p=B/'mapped.blif';digest=sha(p);original=parse(B/'original.blif');ins,outs,gates=parse(p);assert set(ins)==set(original[0]);assert set(outs)==set(original[1]);assert not set(ins)&set(gates)
for name,gate in gates.items():
 assert len(gate['inputs'])<=6
 for row in gate['rows']:
  if not gate['inputs']:assert row in (['0'],['1'])
  else:assert len(row)==2 and len(row[0])==len(gate['inputs']) and set(row[0])<=set('01-') and row[1] in ('0','1')
 dependents=defaultdict(list);degree={}
 for name,g in gates.items():
  deps=set(g['inputs'])-set(ins);assert deps<=set(gates);degree[name]=len(deps)
  for dep in deps:dependents[dep].append(name)
# DAG independently from physical path solvers.
queue=deque(n for n,d in degree.items() if d==0);visited=0
while queue:
 n=queue.popleft();visited+=1
 for child in dependents[n]:
  degree[child]-=1
  if degree[child]==0:queue.append(child)
assert visited==len(gates);assert set(outs)<=set(ins)|set(gates);assert sha(p)==digest
D.mkdir(exist_ok=False);report=dict(bindings={str(x):sha(x) for x in (Path(__file__).resolve(),B/'protocol.json',B/'original.blif',p)},cut_inputs=len(ins),cut_outputs=len(outs),lut_nodes=len(gates),max_inputs=max(len(g['inputs']) for g in gates.values()),dag_complete=True,boundary_sets_preserved=True,scope='Shape/DAG/declared boundary only. No mapped functional equivalence, HDL sequential equivalence, native or prediction admission.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k!='bindings'})
