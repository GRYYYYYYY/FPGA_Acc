"""Independent exported minterm coverage, state ports and bound CEC transcript."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from verify_external_family_cut_v1_2026_10_18 import lines
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def main():
 root=R/'experiments/prospective_external_family_grounded_packed_cut_v1_2026-10-19';rp=root/'receipt.json';r=read(rp);pp=root/'protocol.json';p=read(pp);assert r['passed'] and r['exit_code']==0
 for d in [r,p]:
  for f,h in d['bindings'].items():assert sha(f)==h
 exported=root/'native_grounded_cut.blif';data=lines(exported);oldroot=R/'experiments/prospective_external_family_compile_cut_v2_2026-10-18';old=lines(oldroot/'design.blif');native=R/'experiments/prospective_external_family_native_packed_LUTs_v1_2026-10-19/loaded_LUTs.tsv';loaded={}
 for line in native.open():
  name,w,signals,mask=line.rstrip('\n').split('\t');loaded[name]=(int(w),signals.split(','),mask)
 def head(data,key):
  rows=[r[1:] for r in data if r[0]==key];assert len(rows)==1;return rows[0]
 ffs=[row for row in old if row[0]=='.latch'];assert len(ffs)==1938 and all(row[3:5]==['re','clk'] for row in ffs);expectedin=list(dict.fromkeys(head(old,'.inputs')+[row[2] for row in ffs]));expectedout=list(dict.fromkeys(head(old,'.outputs')+[row[1] for row in ffs]+['clk']));assert head(data,'.inputs')==expectedin and head(data,'.outputs')==expectedout and len(expectedin)==1982 and len(expectedout)==1971;assert not any(row[0] in ['.latch','.subckt'] for row in data)
 tables={};current=None
 for row in data:
  if row[0]=='.names':current=row[-1];assert current not in tables;tables[current]=(row[1:-1],set())
  elif row[0].startswith('.'):current=None
  else:
   assert current is not None;inputs,on=tables[current];assert len(row)==2 and row[1]=='1' and len(row[0])==len(inputs) and set(row[0])<=set('01');bits=tuple(map(int,row[0]));assert bits not in on;on.add(bits)
 assert set(tables)==set(loaded) and len(tables)==6483;checked=0
 for name,(inputs,on) in tables.items():
  w,signals,mask=loaded[name];positions=[i for i,s in enumerate(signals) if s!='open'];assert inputs==[signals[i] for i in positions]
  for value in range(1<<len(inputs)):
   bits=tuple((value>>j)&1 for j in range(len(inputs)));physical=sum(bit<<i for bit,i in zip(bits,positions));assert (bits in on)==(mask[physical]=='1');checked+=1
 assert checked==184360;log=root/'cec.log';text=log.read_text();assert text.count('Networks are equivalent')==1 and 'NOT EQUIVALENT' not in text
 with (root/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='ALL6483_EXPORTED_FUNCTIONS_FULL_FF_BOUNDARY_AND_CEC_BINDINGS_VERIFIED',LUTs=6483,grounded_assignments_checked=checked,FF_state_pairs=len(ffs),cut_inputs=1982,cut_outputs=1971,bindings={str(p):sha(p) for p in [rp,pp,exported,native,oldroot/'design.blif',log,Path(__file__).resolve()]},scope='Independent minterm decoding and complete source FF cut-interface check; CEC transcript bound to exact exported artifacts. Explicit-ground Boolean contract only, inherited packed FF semantics. Not native default-X, whole HDL four-state, physical timing, family admission or routing benefit.'),f,indent=2)
 print('INDEPENDENT_GROUNDED_CUT_PASS',len(tables),checked,len(ffs))
if __name__=='__main__':main()
