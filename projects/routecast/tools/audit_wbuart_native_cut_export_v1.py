"""Independent native cut minterm decoding and complete state/clock interface audit."""
import hashlib,itertools,json
from pathlib import Path
from verify_external_family_cut_v1_2026_10_18 import lines
R=Path(__file__).resolve().parents[1];D=R/'experiments/wbuart_native_packed_cut_v1_2026-10-20';M=R/'experiments/wbuart_boolean_cut_keepdc_v1_2026-10-20'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 rp=D/'verification.json';r=json.loads(rp.read_text());pp=D/'protocol.json';p=json.loads(pp.read_text());assert r['passed'] and r['cec_exit_status']==0
 for n,h in r['bindings'].items():assert sha(D/n)==h
 for n,h in p['bindings'].items():assert sha(Path(n))==h
 export=D/'native_zero_unused_cut.blif';data=lines(export);old=lines(M/'design.blif');native=R/'experiments/wbuart_native_packed_LUTs_v1_2026-10-20/loaded_LUTs.tsv'
 def head(ls,k):
  rows=[r[1:] for r in ls if r[0]==k];assert len(rows)==1;return rows[0]
 ffs=[t for t in old if t[0]=='.latch'];assert len(ffs)==599 and all(t[3:5]==['re','i_clk'] for t in ffs)
 ci=list(dict.fromkeys(head(old,'.inputs')+[t[2] for t in ffs]));co=list(dict.fromkeys(head(old,'.outputs')+[t[1] for t in ffs]+['i_clk']));assert head(data,'.inputs')==ci and head(data,'.outputs')==co and not any(t[0] in ['.latch','.subckt'] for t in data)
 tables={};cur=None
 for row in data:
  if row[0]=='.names':cur=row[-1];assert cur not in tables;tables[cur]=(row[1:-1],set())
  elif row[0].startswith('.'):cur=None
  else:
   assert cur is not None;inp,on=tables[cur]
   if inp:assert len(row)==2 and row[1]=='1' and set(row[0])<=set('01') and len(row[0])==len(inp);bits=tuple(map(int,row[0]))
   else:assert row==['1'];bits=()
   assert bits not in on;on.add(bits)
 loaded={}
 for line in native.read_text().splitlines():
  n,w,s,m=line.split('\t');assert n not in loaded;loaded[n]=(int(w),s.split(','),m)
 assert set(tables)==set(loaded) and len(tables)==1101;checked=0
 for n,(inp,on) in tables.items():
  w,signals,mask=loaded[n];positions=[i for i,s in enumerate(signals) if s!='open'];assert inp==[signals[i] for i in positions] and len(mask)==1<<w
  for bits in itertools.product((0,1),repeat=len(inp)):
   physical=sum(b<<i for b,i in zip(bits,positions));assert (bits in on)==(mask[physical]=='1');checked+=1
 assert checked==29110;log=D/'cec.log';text=log.read_text();assert text.count('Networks are equivalent')==1 and 'NOT EQUIVALENT' not in text and 'non-driven' not in text
 paths=[Path(__file__),rp,pp,export,native,M/'design.blif',log];v={'status':'ALL1101_NATIVE_CUT_TABLES_AND599_STATE_INTERFACE_INDEPENDENTLY_VERIFIED','native_assignment_checks':checked,'FF_state_pairs':len(ffs),'cut_inputs':len(ci),'cut_outputs':len(co),'scope':'Explicit-zero unused-input Boolean cut only; no default-X/fullHDL/timing/unseen/route or performance claim.','bindings':{str(p):sha(p) for p in paths}}
 (D/'independent_verification_v1.json').write_text(json.dumps(v,indent=2)+'\n');print(v['status'])
if __name__=='__main__':main()
