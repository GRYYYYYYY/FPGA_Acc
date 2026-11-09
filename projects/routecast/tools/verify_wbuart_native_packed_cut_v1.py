"""Native loaded LUT masks, exhaustive connected-input slice, whole Boolean cut CEC."""
import hashlib,itertools,json,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'experiments/wbuart_pack_v1_2026-10-20';M=R/'experiments/wbuart_boolean_cut_keepdc_v1_2026-10-20';N=R/'experiments/wbuart_native_packed_LUTs_v1_2026-10-20';O=R/'experiments/wbuart_native_packed_cut_v1_2026-10-20'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):
 with (O/n).open('x') as f:json.dump(d,f,indent=2);f.write('\n')
def records(p):
 out=[];pending=''
 for raw in p.read_text().splitlines():
  s=raw.split('#',1)[0].strip()
  if not s:continue
  if s.endswith('\\'):pending+=s[:-1]+' ';continue
  out.append((pending+s).split());pending=''
 assert not pending
 return out
def main():
 O.mkdir(exist_ok=False);receipt=json.loads((N/'receipt.json').read_text());assert receipt['exit_code']==0 and sha(N/'loaded_LUTs.tsv')==receipt['export_sha256']
 native_protocol=json.loads((N/'protocol.json').read_text())
 for n,h in native_protocol['bindings'].items():assert sha(Path(n))==h
 lp=R/'experiments/wbuart_packed_LUT_pins_v1_2026-10-20/verification.json';lutproof=json.loads(lp.read_text());fp=R/'experiments/wbuart_packed_FF_v2_2026-10-20/verification.json';ffproof=json.loads(fp.read_text())
 for d in [lutproof,ffproof]:
  for n,h in d['bindings'].items():assert sha(Path(n))==h
 atoms={};cur=None
 for row in records(P/'design.blif'):
  if row[0].startswith('.'):
   cur=None
   if row[0]=='.names':cur=row[-1];assert cur not in atoms;atoms[cur]={'inputs':row[1:-1],'cubes':[]}
  else:assert cur is not None;atoms[cur]['cubes'].append(row)
 assert set(atoms)==set(lutproof['atoms']) and len(atoms)==1101
 ref=records(M/'mapped_cut.blif');inputs=next(t[1:] for t in ref if t[0]=='.inputs');outputs=next(t[1:] for t in ref if t[0]=='.outputs');state=[t for t in records(M/'design.blif') if t[0]=='.latch'];assert len(state)==599
 bindings={str(p):sha(p) for p in [Path(__file__),N/'protocol.json',N/'receipt.json',N/'loaded_LUTs.tsv',lp,fp,P/'design.blif',P/'design.net',M/'mapped_cut.blif',M/'design.blif']}
 save('protocol.json',{'bindings':bindings,'scope':'All native loaded LUT masks and physical input identities, compared to independently resolved packed pins and original BLIF truth. Functional audit fixes unused physical inputs to0 explicitly. Does not change native writer default unconnected/X, certify full-HDL/four-state/timing, placement or family admission.','cut_inputs':len(inputs),'cut_outputs':len(outputs),'FF_records_inherited_exact':599,'expected_LUTs':1101})
 seen=set();checked=0;maskrows=0;openpins=0;offdefault=0;body=[];drivers=set(inputs);uses=set(outputs);nonzero_unused_diff=0
 for line in (N/'loaded_LUTs.tsv').read_text().splitlines():
  name,w,signals,mask=line.split('\t');w=int(w);signals=signals.split(',');assert name in atoms and name not in seen;seen.add(name);assert len(signals)==w and len(mask)==1<<w and set(mask)<=set('01')
  a=atoms[name];pin=lutproof['atoms'][name];assert a['inputs']==pin['inputs'];rotation=pin['physical_to_logical']
  if rotation is None:assert not a['inputs'] and all(s=='open' for s in signals)
  else:
   assert len(rotation)==w
   for i,j in enumerate(rotation):assert signals[i]==('open' if j=='open' else a['inputs'][int(j)])
  connected=[i for i,s in enumerate(signals) if s!='open'];names=[signals[i] for i in connected];assert len(names)==len(set(names)) and set(names)==set(a['inputs'])
  n=len(names);cubes=[]
  for row in a['cubes']:
   if not a['inputs']:assert len(row)==1 and row[0] in '01';cubes.append(('',int(row[0])))
   else:assert len(row)==2 and len(row[0])==len(a['inputs']) and set(row[0])<=set('01-') and row[1] in '01';cubes.append((row[0],int(row[1])))
  pol={v for _,v in cubes};assert len(pol)<=1;default=1-next(iter(pol)) if pol else 0;offdefault+=default==1
  source_truth=[]
  for assignment in range(1<<n):
   env={s:(assignment>>i)&1 for i,s in enumerate(names)};matches=[v for pattern,v in cubes if all(c=='-' or int(c)==env[s] for c,s in zip(pattern,a['inputs']))];value=matches[0] if matches else default;assert all(v==value for v in matches)
   physical=sum(((assignment>>j)&1)<<i for j,i in enumerate(connected));assert int(mask[physical])==value,(name,assignment);source_truth.append(value);checked+=1
  for assignment,v in enumerate(mask):
   logical=sum(((assignment>>i)&1)<<j for j,i in enumerate(connected));nonzero_unused_diff+=int(v)!=source_truth[logical]
  body.append('.names '+' '.join(names+[name]))
  for assignment in range(1<<n):
   physical=sum(((assignment>>j)&1)<<i for j,i in enumerate(connected))
   if mask[physical]=='1':body.append((''.join(str((assignment>>j)&1) for j in range(n))+' 1').strip())
  assert name not in drivers;drivers.add(name);uses.update(names);maskrows+=len(mask);openpins+=w-n
 assert seen==set(atoms) and not uses-drivers
 target=O/'native_zero_unused_cut.blif';target.write_text('\n'.join(['.model cut','.inputs '+' '.join(inputs),'.outputs '+' '.join(outputs),*body,'.end'])+'\n')
 abc=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/abc/abc';start=time.perf_counter()
 with (O/'cec.log').open('x') as f:p=subprocess.run([str(abc),'-c','cec '+str(M/'mapped_cut.blif')+' '+str(target)],cwd=O,stdout=f,stderr=subprocess.STDOUT,timeout=60)
 text=(O/'cec.log').read_text();passed=p.returncode==0 and 'Networks are equivalent' in text and 'non-driven' not in text
 for n,h in bindings.items():assert sha(Path(n))==h
 save('verification.json',{'status':'ALL_NATIVE_PACKED_LUT_TRUTHS_AND_ZERO_UNUSED_BOOLEAN_CUT_CEC_PASS' if passed else 'NATIVE_PACKED_BOOLEAN_CUT_CEC_UNPROVEN','passed':passed,'LUTs':len(seen),'FF_records_inherited_exact':599,'connected_assignments_checked':checked,'native_physical_mask_rows':maskrows,'open_physical_pins':openpins,'off_set_encoded_LUTs':offdefault,'rows_differing_if_unused_pins_are_nonzero':nonzero_unused_diff,'cec_exit_status':p.returncode,'cec_seconds':time.perf_counter()-start,'default_writer_full_four_state_equivalence':False,'strict_unseen_admitted':False,'new_placement_route_jobs':False,'bindings':{p.name:sha(p) for p in O.iterdir() if p.is_file()},'native_ABC_sha256':sha(abc)})
 print('PACKED_NATIVE_CUT',passed,len(seen),checked,maskrows,nonzero_unused_diff,flush=True);assert passed
if __name__=='__main__':main()
