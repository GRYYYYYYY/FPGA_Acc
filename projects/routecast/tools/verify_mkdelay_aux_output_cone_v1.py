"""Independent cone traversal, exact generated operator checks and SAT receipts."""
import json,hashlib,functools
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'mkdelay_aux_output_cone_v1_2026-10-21';SRC=E/'preserved_source_ram_mapping_v1_2026-10-21/mkDelayWorker32B/preserved_boundary.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 for p,h in json.loads((D/'protocol.json').read_text())['bindings'].items():assert sha(Path(p))==h,p
 m=json.loads(SRC.read_text())['modules']['mkDelayWorker32B'];manifest=json.loads((D/'cone_manifest.json').read_text());drivers={b:(n,c) for n,c in m['cells'].items() for p,bs in c['connections'].items() if c['port_directions'][p]=='output' for b in bs if isinstance(b,int)};seen=set();leaves=set()
 def walk(b):
  n,c=drivers[b]
  if c['type'].endswith('dual_port_ram'):leaves.add(b);return
  if n in seen:return
  seen.add(n);assert c['type'] in ['$and','$reduce_and']
  for p,bs in c['connections'].items():
   if c['port_directions'][p]=='input':
    for x in bs:walk(x)
 root=m['ports']['prevent_hanging_nodes']['bits'][0];walk(root);assert manifest['root_bit']==root;assert manifest['cells']=={n:m['cells'][n] for n in seen};assert manifest['input_bits_lsb_first']==sorted(leaves);assert len(leaves)==1336 and len(seen)==17
 index={b:i for i,b in enumerate(sorted(leaves))};code=(D/'cone.v').read_text();bits=lambda b:f'r[{index[b]}]' if b in leaves else f'n{b}';vec=lambda bs:'{'+','.join(bits(b) for b in reversed(bs))+'}';words=Counter()
 for b in leaves:
  n,c=drivers[b];port=next(p for p,bs in c['connections'].items() if c['port_directions'][p]=='output' and b in bs);assert manifest['leaf_bindings'][str(b)]=={'cell':n,'port':port,'bit_index':c['connections'][port].index(b)};words[n+'/'+port]+=1
 assert dict(words)==manifest['RAM_word_leaf_counts'] and len(words)==9
 for n in seen:
  c=m['cells'][n];z=c['connections'];assert len(z['Y'])==1;expr=vec(z['A'])+' & '+vec(z['B']) if c['type']=='$and' else '&'+vec(z['A']);assert f'assign n{z["Y"][0]} = {expr};' in code
 result=json.loads((D/'results.json').read_text())['rows'];assert len(result)==6;records=[]
 for row in result:
  f=D/row['name'];log=(f/'yosys.log').read_text();ys=(f/'commands.ys').read_text();assert 'Found and reported 0 problems.' in log
  if row['name'].endswith('_negative'):assert row['exit_code']==1 and row['proof_failed'] and 'proof did fail' in log
  else:assert row['exit_code']==0 and row['proof_passed'] and 'no model found: SUCCESS' in log
  if row['name'].endswith('_one_bit_clear'):
   cell=row['name'].removesuffix('_one_bit_clear');bit=m['cells'][cell]['connections']['out2'][0];value=['1']*1336;value[1335-index[bit]]='0';assert "-set r 1336'b"+''.join(value) in ys
  records.append({'name':row['name'],'verified':True,'bindings':{str(p.relative_to(R)):sha(p) for p in [f/'commands.ys',f/'yosys.log']}})
 out={'status':'AUX_TOP_OUTPUT_EXACT_AND_OF_1336_RAM_READ_BITS_VERIFIED','RAM_words':dict(words),'logic_cells':17,'positive_proofs':4,'negative_controls_expected_failures':2,'proof_receipts':records,'scope':'Exact actual auxiliary-output combinational function. Read word bits are independent abstract binary inputs; local sensitivity does not show reset-reachable word assignments or full-top inequivalence. This output cannot be discarded on cache-forwarding grounds alone.'};(D/'verification_v1.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status'])
if __name__=='__main__':main()
