"""Yosys SAT on actual read/write cones; RAM state abstracted explicitly."""
import json,hashlib,os,subprocess,time,functools
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'experiments/parmys_registered_bank_select_v1_2026-10-21';D=R/'experiments/parmys_bank_cones_sat_v1_2026-10-21'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);manifest=json.loads((R/'experiments/preroute_family_admission_v1_2026-10-20/structure_preflight_manifest_v5.json').read_text());binary=Path(manifest['yosys_binary']);runtime=Path(manifest['runtime_library']);env=os.environ.copy();env['LD_LIBRARY_PATH']=str(runtime.parent)+(':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '');protocol={'scope':'Actual repaired JSON combinational read mux and write decode, all defined binary addresses/enables and arbitrary independent RAM output bits. FF Q abstract inputs stand for sampled bank bits; no full-memory/4-state/collision proof.', 'bindings':{str(p):sha(p) for p in [Path(__file__),binary,runtime,P/'dp13x32/repaired.json',P/'dp16x36/repaired.json']}};(D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
 for name,a,w in [('dp13x32',13,32),('dp16x36',16,36)]:
  f=D/name;f.mkdir();m=json.loads((P/name/'repaired.json').read_text())['modules']['probe'];cells=m['cells'];ports=m['ports'];rams=[c for c in cells.values() if c['type']=='dual_port_ram'];ff=cells['$routecast_bank_sample'];b=a-11;drivers={bit:(c,i) for c in cells.values() if c['type'] in ['$and','$reduce_or','$reduce_and','$logic_not'] for i,bit in enumerate(c['connections']['Y'])}
  def port(k):return ports[k]['bits'][0]
  def value(bit,inputs):
   if bit=='0':return 0
   if bit=='1':return 1
   if bit in inputs:return inputs[bit]
   c,i=drivers[bit];z=c['connections'];aa=[value(x,inputs) for x in z['A']];t=c['type']
   if t=='$and':return aa[i]&value(z['B'][i],inputs)
   if t=='$reduce_and':return int(all(aa))
   if t=='$reduce_or':return int(any(aa))
   return int(not any(aa))
  placement={};predicates=[]
  for c in rams:
   z=c['connections'];assert z['clk']==ports['clk']['bits'] and z['we2']==['0'] and z['data2']==['0']
   for p in [1,2]:assert z[f'addr{p}']==[port(f'addr{p}~{i}') for i in range(b,a)]
   k=next(i for i in range(w) if z['data1']==[port(f'data1~{i}')]);enabled=[]
   for bank in range(1<<b):
    ins={port('we1'):1,**{port(f'addr1~{i}'):(bank>>i)&1 for i in range(b)}}
    if value(z['we1'][0],ins):enabled.append(bank)
   assert len(enabled)==1;bank=enabled[0];assert (bank,k) not in placement;placement[bank,k]=c;predicates.append((z['we1'][0],bank))
  assert len(placement)==(1<<b)*w
  # Full logical address map is bijective, no address truncation.
  pairs={(x&((1<<b)-1),x>>b) for x in range(1<<a)};assert len(pairs)==1<<a and max(v for _,v in pairs)==2047
  def bit(x):return 'n'+str(x) if isinstance(x,int) else "1'b"+x
  def vec(xs):return '{'+','.join(bit(x) for x in reversed(xs))+'}'
  free={x for p in ports.values() if p['direction']=='input' for x in p['bits']};free.update(ff['connections']['Q']);free.update(x for c in rams for p in ['out1','out2'] for x in c['connections'][p]);allnets={x for c in cells.values() for xs in c['connections'].values() for x in xs if isinstance(x,int)};s=['module proof('+','.join('input '+bit(x) for x in sorted(free))+',output ok);','wire '+','.join(bit(x) for x in sorted(allnets-free))+';']
  for c in cells.values():
   t=c['type'];z=c['connections']
   if t in ['dual_port_ram','$dff']:continue
   assert t in ['$and','$reduce_or','$reduce_and','$logic_not'];expr=vec(z['A'])+' & '+vec(z['B']) if t=='$and' else {'$reduce_or':'|','$reduce_and':'&','$logic_not':'!'}[t]+vec(z['A']);s.append('assign '+vec(z['Y'])+' = '+expr+';')
  assertions=[]
  for idx,(wire,bank) in enumerate(predicates):
   assertions.append('('+bit(wire)+' == ('+bit(port('we1'))+' & ('+vec([port(f'addr1~{i}') for i in range(b)])+f" == {b}'d{bank}"+')))')
  for p in [1,2]:
   select=ff['connections']['Q'][(p-1)*b:p*b]
   for k in range(w):
    terms=['(('+vec(select)+f" == {b}'d{bank}) & "+bit(placement[bank,k]['connections'][f'out{p}'][0])+')' for bank in range(1<<b)]
    assertions.append('('+bit(port(f'out{p}~{k}'))+' == ('+' | '.join(terms)+'))')
  s.append('assign ok = '+' & '.join(assertions)+';\nendmodule');v=f/'cone_proof.v';v.write_text('\n'.join(s)+'\n');ys=f/'commands.ys';ys.write_text(f'read_verilog {v}\nhierarchy -top proof\nproc\nopt\ncheck -assert\nsat -verify -prove ok 1 -show ok\n');start=time.monotonic()
  with (f/'yosys.log').open('w') as out:code=subprocess.call([str(binary),'-Q','-T','-s',str(ys)],cwd=f,env=env,stdout=out,stderr=subprocess.STDOUT)
  success=code==0 and 'SUCCESS' in (f/'yosys.log').read_text();rows.append(dict(case=name,exit_code=code,sat_proven=success,seconds=time.monotonic()-start,ram_cells=len(rams),boolean_obligations=len(assertions),address_bijection_count=len(pairs),bindings={str(p.relative_to(R)):sha(p) for p in [v,ys,f/'yosys.log']}));(D/'progress.json').write_text(json.dumps(rows,indent=2)+'\n');print(name,code,success,flush=True)
 (D/'results.json').write_text(json.dumps({'rows':rows},indent=2)+'\n')
if __name__=='__main__':main()
