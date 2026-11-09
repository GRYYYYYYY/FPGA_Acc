"""Actual auxiliary cone composition under explicit binary memory/read/hit premises."""
import json,hashlib,subprocess,os
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'aux_policy_composition_sat_v1_2026-10-21';SRC=E/'aux_word_forward_policy_v1_2026-10-21/candidate_boundary.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);m=json.loads(SRC.read_text())['modules']['mkDelayWorker32B'];dr={b:(n,c) for n,c in m['cells'].items() for p,bs in c['connections'].items() if c['port_directions'][p]=='output' for b in bs if isinstance(b,int)};leaf=set();selected={}
 def walk(b):
  if isinstance(b,str):assert b in ['0','1'];return
  n,c=dr[b]
  if c['type'].endswith('dual_port_ram') or c['type'] in ['$sdffe','$sdff','$sdffce','$dff','$dffe']:leaf.add(b);return
  if n in selected:return
  assert c['type'] in ['$and','$reduce_and','$mux','$logic_and','$eq'];selected[n]=c
  for p,bs in c['connections'].items():
   if c['port_directions'][p]=='input':
    for x in bs:walk(x)
 root=m['ports']['prevent_hanging_nodes']['bits'][0];walk(root)
 def bit(b):return 'n'+str(b) if isinstance(b,int) else "1'b"+b
 def vec(bs):return '{'+','.join(bit(b) for b in reversed(bs))+'}'
 wires=sorted({b for c in selected.values() for p,bs in c['connections'].items() if c['port_directions'][p]=='output' for b in bs});lines=['wire '+','.join(bit(b) for b in wires)+';']
 for n,c in selected.items():
  z=c['connections'];t=c['type']
  if t=='$mux':assert len(z['S'])==1;expr=vec(z['S'])+' ? '+vec(z['B'])+' : '+vec(z['A'])
  elif t=='$reduce_and':expr='&'+vec(z['A'])
  else:expr=vec(z['A'])+{'$and':' & ','$logic_and':' && ','$eq':' == '}[t]+vec(z['B'])
  lines.append('assign '+vec(z['Y'])+' = '+expr+';')
 changes=json.loads((E/'aux_word_forward_policy_v1_2026-10-21/change_manifest.json').read_text())['changes'];raw={};hit={};cache={}
 for r in changes:
  p=r['prefix'];raw[p]=r['old_read_word_bits'];getter=r['new_cached_getter_bits'];mux=next(c for c in selected.values() if c['type']=='$mux' and c['connections']['Y']==getter);hit[p]=vec(mux['connections']['S']);cache[p]=vec(mux['connections']['B'])
 allraw=[];others=[]
 for n,c in m['cells'].items():
  if c['type'].endswith('dual_port_ram'):
   out='out2' if n in ['dpram1','dpram2'] else 'out1';allraw+=c['connections'][out]
   if n not in ['dpram1','dpram2']:others+=c['connections'][out]
 assert len(others)==824 and len(allraw)==1336
 fixed='module proof('+','.join('input '+bit(b) for b in sorted(leaf))+',input[255:0]memoryRF,memoryWF,input collisionRF,collisionWF,output ok);\n'+'\n'.join(lines)+'\nwire reference=(&memoryRF)&&(&memoryWF)&&(&'+vec(others)+');\n'
 config=json.loads((E/'preroute_family_admission_v1_2026-10-20/structure_preflight_manifest_v5.json').read_text());binary=Path(config['yosys_binary']);runtime=Path(config['runtime_library']);env=os.environ.copy();env['LD_LIBRARY_PATH']=str(runtime.parent)+(':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '');cases=['full_contract','omit_cache_relation_negative','omit_noncollision_relation_negative','omit_collision_hit_negative','original_raw_observer_negative'];protocol={'scope':'Actual23cell policy cone, binary FF/RAM-output cutpoints. Given cache hit->current memory equality, noncollision raw read->current memory equality, collision->cache hit, prove retained auxiliary output equals current-word reference. Not a proof that all premises hold in full source/fourstate/delta/physical system. Raw-observer negative is abstract, not reset-reachable failure.','cases':cases,'bindings':{str(p):sha(p) for p in [Path(__file__),SRC,binary,runtime,E/'cache_memory_relation_sat_v1_2026-10-21/verification_v1.json']}};(D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');(D/'cone_manifest.json').write_text(json.dumps({'source_cells':selected,'free_bits':sorted(leaf),'root_bit':root,'other_read_bits':others,'raw_read_bits':raw,'cache_mux_hit':hit,'cache_mux_data':cache},indent=2)+'\n');rows=[]
 for mode in cases:
  f=D/mode;f.mkdir();conditions=[]
  for prefix,suffix in [('mesgRF','RF'),('mesgWF','WF')]:
   h=hit[prefix];memory='memory'+suffix;collision='collision'+suffix
   if mode!='omit_cache_relation_negative':conditions.append('(!'+h+' || ('+cache[prefix]+' == '+memory+'))')
   if mode!='omit_noncollision_relation_negative':conditions.append('('+collision+' || ('+vec(raw[prefix])+' == '+memory+'))')
   if mode!='omit_collision_hit_negative':conditions.append('(!'+collision+' || '+h+')')
  actual='(&'+vec(allraw)+')' if mode=='original_raw_observer_negative' else bit(root);vf=f/'proof.v';vf.write_text(fixed+'wire pre='+' && '.join(conditions)+';\nassign ok=!pre || ('+actual+' == reference);\nendmodule\n');ys=f/'commands.ys';ys.write_text(f'read_verilog {vf}\nhierarchy -top proof\nproc\nopt\ncheck -assert\nsat -prove ok 1 -show ok,reference -verify\n')
  with (f/'yosys.log').open('w') as log:code=subprocess.call([str(binary),'-Q','-T','-s',str(ys)],cwd=f,env=env,stdout=log,stderr=subprocess.STDOUT)
  log=(f/'yosys.log').read_text();rows.append({'mode':mode,'exit_code':code,'proof_passed':'no model found: SUCCESS' in log,'proof_failed':'proof did fail' in log});print(rows[-1],flush=True)
 (D/'results.json').write_text(json.dumps({'rows':rows},indent=2)+'\n')
if __name__=='__main__':main()
