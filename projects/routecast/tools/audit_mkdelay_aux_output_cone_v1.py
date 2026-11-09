"""Exact auxiliary output cone with explicit independent read-word abstraction."""
import json,hashlib,functools,subprocess,os
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'mkdelay_aux_output_cone_v1_2026-10-21';SRC=E/'preserved_source_ram_mapping_v1_2026-10-21/mkDelayWorker32B/preserved_boundary.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);m=json.loads(SRC.read_text())['modules']['mkDelayWorker32B'];drivers={b:(n,c) for n,c in m['cells'].items() for p,bs in c['connections'].items() if c['port_directions'][p]=='output' for b in bs if isinstance(b,int)};visited=set();ramleaf={}
 @functools.lru_cache(None)
 def visit(bit):
  assert isinstance(bit,int);n,c=drivers[bit]
  if c['type'].endswith('dual_port_ram'):
   p=next(p for p,bs in c['connections'].items() if c['port_directions'][p]=='output' and bit in bs);ramleaf[bit]={'cell':n,'port':p,'bit_index':c['connections'][p].index(bit)};return frozenset([bit])
  assert c['type'] in ['$and','$reduce_and'];visited.add(n);out=frozenset()
  for p,bs in c['connections'].items():
   if c['port_directions'][p]=='input':
    for b in bs:out=out|visit(b)
  return out
 root=m['ports']['prevent_hanging_nodes']['bits'][0];leaves=sorted(visit(root));assert len(leaves)==1336 and len(visited)==17;index={b:i for i,b in enumerate(leaves)};counter=Counter((v['cell'],v['port']) for v in ramleaf.values());manifest={'root_bit':root,'cells':{n:m['cells'][n] for n in sorted(visited)},'input_bits_lsb_first':leaves,'leaf_bindings':{str(b):ramleaf[b] for b in leaves},'RAM_word_leaf_counts':{'/'.join(k):v for k,v in counter.items()}};(D/'cone_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');statements=[];done=set()
 def signal(bit):
  if bit in index:return f'r[{index[bit]}]'
  n,c=drivers[bit]
  if n not in done:
   done.add(n);z=c['connections'];assert len(z['Y'])==1
   vec=lambda xs:'{'+','.join(signal(b) for b in reversed(xs))+'}'
   expr=vec(z['A'])+' & '+vec(z['B']) if c['type']=='$and' else '&'+vec(z['A']);statements.append('wire n'+str(bit)+'; assign n'+str(bit)+' = '+expr+';')
  return 'n'+str(bit)
 out=signal(root);verilog='module proof(input[1335:0]r,output actual,same_and,same_or);\n'+'\n'.join(statements)+f'\nassign actual={out}; assign same_and=(actual==(&r));assign same_or=(actual==(|r));\nendmodule\n';vf=D/'cone.v';vf.write_text(verilog);config=json.loads((E/'preroute_family_admission_v1_2026-10-20/structure_preflight_manifest_v5.json').read_text());binary=Path(config['yosys_binary']);runtime=Path(config['runtime_library']);env=os.environ.copy();env['LD_LIBRARY_PATH']=str(runtime.parent)+(':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '');tests=[('exact_AND','same_and',1,None),('all_words_ones','actual',1,'1'*1336),('constant_zero_negative','actual',0,None),('OR_replacement_negative','same_or',1,None)]
 for n in ['dpram1','dpram2']:
  b=m['cells'][n]['connections']['out2'][0];value=['1']*1336;value[1335-index[b]]='0';tests.append((n+'_one_bit_clear','actual',0,''.join(value)))
 protocol={'scope':'Original17-cell auxiliary output cone,1336read bits abstracted as independent binary inputs. Prove exact AND function and local influence. Const0/OR negative failures are not reset-reachable source counterexamples. No output pruning, source edit or native admission.','tests':[{'name':n,'signal':s,'expected':v,'r_fixed':r is not None} for n,s,v,r in tests],'bindings':{str(p):sha(p) for p in [Path(__file__),SRC,vf,D/'cone_manifest.json',binary,runtime]}};(D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
 for n,s,v,r in tests:
  f=D/n;f.mkdir();ys=f/'commands.ys';constraint="-set r 1336'b"+r if r is not None else '';ys.write_text(f'read_verilog {vf}\nhierarchy -top proof\nproc\nopt\ncheck -assert\nsat {constraint} -prove {s} {v} -show actual,same_and,same_or -verify\n')
  with (f/'yosys.log').open('w') as log:code=subprocess.call([str(binary),'-Q','-T','-s',str(ys)],cwd=f,env=env,stdout=log,stderr=subprocess.STDOUT)
  text=(f/'yosys.log').read_text();rows.append({'name':n,'exit_code':code,'proof_passed':'no model found: SUCCESS' in text,'proof_failed':'proof did fail' in text});print(rows[-1],flush=True)
 (D/'results.json').write_text(json.dumps({'rows':rows},indent=2)+'\n')
if __name__=='__main__':main()
