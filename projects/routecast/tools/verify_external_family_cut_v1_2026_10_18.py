"""Independent BLIF records, public interfaces and exact synchronous boundary."""
import hashlib,json,re
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def lines(p):
 result=[];acc=''
 for raw in Path(p).read_text().splitlines():
  value=raw.strip()
  if not value or value.startswith('#'):continue
  if value.endswith('\\'):acc+=value[:-1]+' ';continue
  result.append((acc+value).split());acc=''
 assert not acc;return result

def main():
 root=R/'experiments/prospective_external_family_compile_cut_v2_2026-10-18';rp=root/'receipt.json';r=json.loads(rp.read_text());assert r['status']=='LUT6_cut_mapped_CEC_pass_FF_boundary_exact';out=R/'experiments/prospective_external_family_compile_verification_v1_2026-10-18';out.mkdir(exist_ok=False)
 for mapping in [r['bindings'],r['files']]:
  for p,h in mapping.items():assert sha(p)==h
 flat,cut,mapped,final=[lines(root/name) for name in ['flat.blif','cut.blif','mapped_cut.blif','design.blif']]
 def header(data,key):
  values=[x[1:] for x in data if x[0]==key];assert len(values)==1;return values[0]
 def body(data,include_latches):return [x for x in data if x[0] not in (['.model','.inputs','.outputs','.end'] if include_latches else ['.model','.inputs','.outputs','.end','.latch'])]
 ffs=[x for x in flat if x[0]=='.latch'];assert len(ffs)==r['FF_bits']==1938 and all(len(x)==6 and x[3:5]==['re','clk'] for x in ffs);assert [x for x in final if x[0]=='.latch']==ffs;assert header(final,'.model')==['chacha'];assert header(flat,'.inputs')==header(final,'.inputs') and header(flat,'.outputs')==header(final,'.outputs')
 assert header(cut,'.inputs')==list(dict.fromkeys(header(flat,'.inputs')+[x[2] for x in ffs]));assert header(cut,'.outputs')==list(dict.fromkeys(header(flat,'.outputs')+[x[1] for x in ffs]+['clk']));assert body(cut,False)==body(flat,False) and body(mapped,False)==body(final,False)
 assert not any(x[0] in ['.latch','.subckt'] for x in mapped);assert not any(x[0]=='.subckt' for x in final)
 luts=[x for x in final if x[0]=='.names'];assert len(luts)==r['LUTs'] and max(len(x)-2 for x in luts)<=6;drivers=header(final,'.inputs')+[x[-1] for x in luts]+[x[2] for x in ffs];uses=header(final,'.outputs')+[n for x in luts for n in x[1:-1]]+[n for x in ffs for n in [x[1],x[4]]];assert len(drivers)==len(set(drivers)) and not set(uses)-set(drivers)
 data=json.loads((root/'flat.json').read_text())['modules']['chacha'];types=Counter(c['type'] for c in data['cells'].values());assert types['$_DFF_P_']==len(ffs) and not any('FF' in k and k!='$_DFF_P_' for k in types)
 public_inputs=sum(len(p['bits']) for p in data['ports'].values() if p['direction']=='input');public_outputs=sum(len(p['bits']) for p in data['ports'].values() if p['direction']=='output');assert public_inputs==len(header(final,'.inputs')) and public_outputs==len(header(final,'.outputs'))
 assert all(x['exit_code']==0 for x in r['phases']) and 'Networks are equivalent' in (root/'cec.log').read_text()
 result=dict(status='mapped_Boolean_cut_and_exact_FF_boundary_independently_verified',LUT_nodes=len(luts),max_LUT_inputs=max(len(x)-2 for x in luts),FF_bits=len(ffs),primary_inputs=public_inputs,primary_outputs=public_outputs,full_port_and_next_state_cut_boundaries_checked=True,full_HDL_four_state_equivalence=False,packed_netlist_admission=False,strict_unseen_admitted=False,new_native_labels_read=False,scope='Independent BLIF tokenization and full body/port/state comparison, raw JSON positive-edge FF count and interface bit count, exact CEC transcript bound to mapped artifacts. Does not prove earlier HDL-to-lowered transformations or physical/native compatibility.',bindings={str(p):sha(p) for p in [Path(__file__),rp,root/'flat.json',root/'flat.blif',root/'cut.blif',root/'mapped_cut.blif',root/'design.blif',root/'cec.log']})
 with (out/'verification.json').open('x') as f:json.dump(result,f,indent=2)
 print('INDEPENDENT CUT/STATE CHECK PASS',len(luts),len(ffs),public_inputs,public_outputs,flush=True)
if __name__=='__main__':main()
