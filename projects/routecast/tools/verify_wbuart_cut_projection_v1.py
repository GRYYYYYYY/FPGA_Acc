"""Independent arbitrary-undriven-input CEC and exact state/port projection."""
import hashlib,json,os,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];A=R/'experiments/wbuart_boolean_cut_v1_2026-10-20';B=R/'experiments/wbuart_boolean_cut_v3_2026-10-20';O=R/'experiments/wbuart_cut_projection_audit_v1_2026-10-20'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def lines(p):
 result=[];pending=''
 for raw in p.read_text().splitlines():
  s=raw.split('#',1)[0].strip()
  if not s:continue
  if s.endswith('\\'):pending+=s[:-1]+' ';continue
  result.append(pending+s);pending=''
 assert not pending
 return result
def main():
 O.mkdir(exist_ok=False);raw=lines(A/'cut.blif');clean=lines(B/'cut.blif');mapped=lines(B/'mapped_cut.blif');flat=lines(B/'flat.blif');design=lines(B/'design.blif')
 get=lambda ls,key:next(s.split()[1:] for s in ls if s.startswith(key+' '))
 ins=get(raw,'.inputs');outs=get(raw,'.outputs');assert get(clean,'.inputs')==ins and get(clean,'.outputs')==outs
 drivers=set(ins);uses=set(outs)
 for s in raw:
  if s.startswith('.names '):t=s.split();drivers.add(t[-1]);uses.update(t[1:-1])
 undriven=sorted(uses-drivers);assert undriven==['tx.r_setup[28]','tx.r_setup[29]']
 state=lambda ls:[s for s in ls if s.startswith('.latch ')]
 assert state(flat)==state(design) and len(state(flat))==598
 for key in ['.inputs','.outputs']:assert get(flat,key)==get(design,key)
 files=[]
 for label,ls in [('raw_free',raw),('clean_free',clean),('mapped_free',mapped)]:
  idx=next(i for i,s in enumerate(ls) if s.startswith('.inputs '));base=ls[idx].split()[1:];assert set(base)==set(ins)
  ls[idx]='.inputs '+' '.join(ins+undriven);p=O/(label+'.blif');p.write_text('\n'.join(ls)+'\n');files.append(p)
 abc=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/abc/abc'
 protocol={'undriven_as_free_inputs':undriven,'policy':'All assignments of originally undriven nodes allowed; no constant grounding. CEC raw→pruned and pruned→mapped; exact lowered latch/control/init strings and physical primary ports restored. Does not prove RTL→lowered semantics.','bindings':{str(p):sha(p) for p in [Path(__file__),abc,A/'cut.blif',B/'cut.blif',B/'mapped_cut.blif',B/'flat.blif',B/'design.blif',*files]}}
 (O/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
 phases=[]
 for label,x,y in [('raw_to_pruned',files[0],files[1]),('pruned_to_mapped',files[1],files[2])]:
  p=O/(label+'.log')
  with p.open('x') as f:rc=subprocess.call([str(abc),'-c','cec '+str(x)+' '+str(y)],cwd=O,stdout=f,stderr=subprocess.STDOUT)
  text=p.read_text();assert rc==0 and 'Networks are equivalent' in text and 'non-driven' not in text
  phases.append({'stage':label,'exit_status':rc,'log_sha256':sha(p)})
 for n,h in protocol['bindings'].items():assert sha(Path(n))==h
 d={'status':'ARBITRARY_UNDRIVEN_DOMAIN_PROJECTION_AND_MAPPING_CEC_PASS','phases':phases,'FF_state_records_exact':598,'arbitrary_undriven_inputs':undriven,'source_RTL_equivalence_proven':False,'strict_unseen_certified':False,'physical_input_admitted':False,'bindings':{'protocol.json':sha(O/'protocol.json')}};(O/'verification.json').write_text(json.dumps(d,indent=2)+'\n');print(d['status'])
if __name__=='__main__':main()
