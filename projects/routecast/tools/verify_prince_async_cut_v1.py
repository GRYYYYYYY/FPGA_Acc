"""Independent tokenized interfaces, complete async cell records and CEC binding."""
import json
from collections import Counter
from pathlib import Path
from verify_external_family_cut_v1_2026_10_18 import lines
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';S=E/'prince_compile_cut_v2_2026-10-20';D=E/'prince_async_cut_verification_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 r=read(S/'receipt.json')
 for mapping in [r['bindings'],r['files']]:assert all(sha(p)==h for p,h in mapping.items())
 flat,cut,mapped,final=[lines(S/name) for name in ['flat.blif','cut.blif','mapped_cut.blif','design.blif']]
 def header(rows,key):
  values=[row[1:] for row in rows if row[0]==key];assert len(values)==1;return values[0]
 ff=[row for row in flat if row[0]=='.subckt'];actual=[row for row in final if row[0]=='.subckt'];assert ff==actual and len(ff)==646 and not any(row[0]=='.latch' for row in flat+cut+mapped+final);types=Counter(row[1] for row in ff);assert types=={'$_DFF_PN0_':645,'$_DFF_PN1_':1};pins=[dict(pair.split('=',1) for pair in row[2:]) for row in ff];assert all(set(p)=={'C','D','Q','R'} and p['C']=='clk' and p['R']=='reset_n' for p in pins);assert len({p['Q'] for p in pins})==646
 assert header(final,'.model')==['prince'] and header(flat,'.inputs')==header(final,'.inputs') and header(flat,'.outputs')==header(final,'.outputs')
 assert header(cut,'.inputs')==list(dict.fromkeys(header(flat,'.inputs')+[p['Q'] for p in pins]));assert header(cut,'.outputs')==list(dict.fromkeys(header(flat,'.outputs')+[p['D'] for p in pins]+[p['C'] for p in pins]+[p['R'] for p in pins]))
 def logic(rows):return [row for row in rows if row[0] not in ['.model','.inputs','.outputs','.end','.subckt']]
 assert logic(flat)==logic(cut) and logic(mapped)==logic(final) and not any(row[0]=='.subckt' for row in cut+mapped)
 luts=[row for row in final if row[0]=='.names'];assert len(luts)==r['LUTs']==2096 and max(len(row)-2 for row in luts)<=6;drivers=header(final,'.inputs')+[row[-1] for row in luts]+[p['Q'] for p in pins];uses=header(final,'.outputs')+[i for row in luts for i in row[1:-1]]+[p[key] for p in pins for key in ['C','D','R']];assert len(drivers)==len(set(drivers)) and not set(uses)-set(drivers)
 data=read(S/'flat.json')['modules']['prince'];counts=Counter(cell['type'] for cell in data['cells'].values());assert {k:v for k,v in counts.items() if 'DFF' in k}==dict(types);assert sum(len(p['bits']) for p in data['ports'].values() if p['direction']=='input')==len(header(final,'.inputs'));assert sum(len(p['bits']) for p in data['ports'].values() if p['direction']=='output')==len(header(final,'.outputs'));assert all(p['exit_code']==0 for p in r['phases']) and 'Networks are equivalent' in (S/'cec.log').read_text()
 D.mkdir(exist_ok=False);files=[Path(__file__),R/'tools/verify_external_family_cut_v1_2026_10_18.py',S/'receipt.json',S/'flat.json',S/'flat.blif',S/'cut.blif',S/'mapped_cut.blif',S/'design.blif',S/'cec.log'];v={'status':'PASS_FULL_LOWERED_ASYNC_STATE_BOUNDARY_AND_COMBINATIONAL_CUT_AUDIT','FF_types':dict(types),'FF_bits':646,'LUTs':2096,'max_LUT_inputs':max(len(row)-2 for row in luts),'whole_original_async_subckt_records_equal':True,'cut_C_D_Q_R_interfaces_exact':True,'strict_unseen_admitted':False,'native_packing_admitted':False,'full_HDL_four_state_equivalence':False,'new_native_labels':False,'bindings':{str(p):sha(p) for p in files},'scope':'Full mapped lowered Boolean cut CEC plus identical asynchronous state records and interfaces. Does not prove original HDL lowering, characterized reset timing or support in current VPR architecture. No async2sync/polarity rewrite/state deletion.'};(D/'verification.json').write_text(json.dumps(v,indent=2)+'\n');print('PRINCE_ASYNC_CUT_INDEPENDENT_PASS',646,2096)
if __name__=='__main__':main()
