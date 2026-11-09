"""Independent actual cone and all explicit premise/negative-control checks."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'aux_policy_composition_sat_v1_2026-10-21';SRC=E/'aux_word_forward_policy_v1_2026-10-21/candidate_boundary.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 for p,h in json.loads((D/'protocol.json').read_text())['bindings'].items():assert sha(Path(p))==h,p
 m=json.loads(SRC.read_text())['modules']['mkDelayWorker32B'];manifest=json.loads((D/'cone_manifest.json').read_text());dr={b:(n,c) for n,c in m['cells'].items() for p,bits in c['connections'].items() if c['port_directions'][p]=='output' for b in bits if isinstance(b,int)};seen=set();leaves=set()
 def walk(b):
  if isinstance(b,str):assert b in ['0','1'];return
  n,c=dr[b]
  if c['type'].endswith('dual_port_ram') or c['type'] in ['$sdffe','$sdff','$sdffce','$dff','$dffe']:leaves.add(b);return
  if n in seen:return
  seen.add(n)
  for p,bits in c['connections'].items():
   if c['port_directions'][p]=='input':
    for x in bits:walk(x)
 walk(m['ports']['prevent_hanging_nodes']['bits'][0]);assert len(seen)==23 and len(leaves)==1894;assert manifest['source_cells']=={n:m['cells'][n] for n in seen};assert manifest['free_bits']==sorted(leaves);assert len(manifest['other_read_bits'])==824
 other_bits=[];all_raw=[]
 for n,c in m['cells'].items():
  if c['type'].endswith('dual_port_ram'):
   port='out2' if n in ['dpram1','dpram2'] else 'out1';all_raw+=c['connections'][port]
   if n not in ['dpram1','dpram2']:other_bits+=c['connections'][port]
 assert manifest['other_read_bits']==other_bits
 for prefix,name in [('mesgRF','dpram1'),('mesgWF','dpram2')]:assert manifest['raw_read_bits'][prefix]==m['cells'][name]['connections']['out2']
 bit=lambda b:'n'+str(b) if isinstance(b,int) else "1'b"+b
 vec=lambda bits:'{'+','.join(bit(b) for b in reversed(bits))+'}'
 result=json.loads((D/'results.json').read_text())['rows'];assert len(result)==5;records=[]
 for r in result:
  mode=r['mode'];f=D/mode;code=(f/'proof.v').read_text();log=(f/'yosys.log').read_text();assert 'Found and reported 0 problems.' in log
  for n in seen:
   c=m['cells'][n];z=c['connections'];t=c['type']
   if t=='$mux':assert len(z['S'])==1;expr=vec(z['S'])+' ? '+vec(z['B'])+' : '+vec(z['A'])
   elif t=='$reduce_and':expr='&'+vec(z['A'])
   else:expr=vec(z['A'])+{'$and':' & ','$logic_and':' && ','$eq':' == '}[t]+vec(z['B'])
   assert 'assign '+vec(z['Y'])+' = '+expr+';' in code
  count=0;expected_conditions=[]
  assert 'wire reference=(&memoryRF)&&(&memoryWF)&&(&'+vec(other_bits)+');' in code
  for prefix,suffix in [('mesgRF','RF'),('mesgWF','WF')]:
   raw=manifest['raw_read_bits'][prefix];getter=m['netnames'][prefix+'_wDataOut__wget']['bits'];mux=next(c for c in m['cells'].values() if c['type']=='$mux' and c['connections'].get('Y')==getter);h=vec(mux['connections']['S']);cache=vec(mux['connections']['B']);memory='memory'+suffix;collision='collision'+suffix
   conditions=[('omit_cache_relation_negative','(!'+h+' || ('+cache+' == '+memory+'))'),('omit_noncollision_relation_negative','('+collision+' || ('+vec(raw)+' == '+memory+'))'),('omit_collision_hit_negative','(!'+collision+' || '+h+')')]
   for omitted,expr in conditions:
    if mode!=omitted:assert expr in code;count+=1;expected_conditions.append(expr)
    else:assert expr not in code
  assert count==(4 if mode.startswith('omit_') else 6)
  assert 'wire pre='+' && '.join(expected_conditions)+';' in code
  actual='(&'+vec(all_raw)+')' if mode=='original_raw_observer_negative' else bit(m['ports']['prevent_hanging_nodes']['bits'][0])
  assert 'assign ok=!pre || ('+actual+' == reference);' in code
  if mode=='full_contract':assert r['exit_code']==0 and r['proof_passed'] and 'no model found: SUCCESS' in log
  else:assert r['exit_code']==1 and r['proof_failed'] and 'proof did fail' in log
  records.append({'mode':mode,'expected_result_verified':True,'bindings':{str(p.relative_to(R)):sha(p) for p in [f/'proof.v',f/'commands.ys',f/'yosys.log']}})
 # Full-premise original-observer failure also proves those premises are satisfiable,
 # since the guard must be true for the guarded equality to fail.
 out={'status':'ACTUAL_AUX_POLICY_CONE_CONDITIONAL_COMPOSITION_VERIFIED','source_cone_cells':23,'binary_state_read_cut_bits':1894,'positive_proofs':1,'negative_controls_expected_failures':4,'full_premises_nonvacuity':'Original raw-observer negative uses same full guard and fails; full guard therefore satisfiable in the abstract model.','records':records,'scope':'Conditional binary combinational composition on actual policy cone. No reset-reachable full-state counterexample, arbitrary four-state or same-edge event proof, original-source equivalence, physical mapping correspondence or native admission.'};(D/'verification_v1.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status'])
if __name__=='__main__':main()
