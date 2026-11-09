"""Structural actual-instance facts and a finite, explicit cycle witness."""
import itertools,json
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'ram_mapping_semantics_v1_2026-10-20';S=E/'preroute_family_admission_v1_2026-10-20'
def load(p):return json.loads(p.read_text())
def main():
 rows=[];bindings={str(Path(__file__)):sha(__file__)}
 for name in ['mcml','mkDelayWorker32B']:
  p=S/'primitive_interface_probe_v1'/name/'proc.json';design=load(p);modules=design['modules'];bindings[str(p)]=sha(p)
  def visit(module,path,stack):
   assert module not in stack;obj=modules[module]
   for cellname,c in obj.get('cells',{}).items():
    typ=c['type'];instance=path+'/'+cellname
    if typ=='dual_port_ram':
     con=c['connections'];assert con['we2']==['0'];a1,a2=con['addr1'],con['addr2'];disjoint=any(a in ['0','1'] and b in ['0','1'] and a!=b for a,b in zip(a1,a2));used=set(b for port in obj.get('ports',{}).values() if port['direction']=='output' for b in port['bits'])
     for othername,other in obj.get('cells',{}).items():
      if othername==cellname:continue
      for port,bits in other['connections'].items():
       if other.get('port_directions',{}).get(port)=='input':used.update(bits)
     rows.append(dict(name=name,instance=instance,second_write_enable_structurally_zero=True,first_write_enable=con['we1'],addresses_structurally_identical=a1==a2,addresses_provably_distinct_by_constant_bit=disjoint,second_read_output_has_local_consumers=bool(used&set(con.get('out2',[]))),collision_free_reachability_proven=False))
    elif typ in modules and not int(modules[typ].get('attributes',{}).get('blackbox','0'),2):visit(typ,instance,stack+(module,))
  visit(name,name,())
 assert len(rows)==16
 # Original two-process blocking RTL, at cycle-boundary observations. Enumerate
 # both complete-process orders and every concrete initial state at tiny depth.
 # Cycle1 writes address0 while port2 reads address1. Cycle2 reads address0
 # with no write, so its defined result is independent of collision ordering.
 observed=set();checks=0
 for initial in itertools.product(range(4),repeat=2):
  for orders in itertools.product([(1,2),(2,1)],repeat=2):
   mem=list(initial);q={}
   for cycle,order in enumerate(orders):
    for port in order:
     if port==1:
      if cycle==0:mem[0]=2
      q[1]=mem[0]
     else:q[2]=mem[1 if cycle==0 else 0]
   observed.add((q[1],q[2]));checks+=1
 assert observed=={(2,2)} and checks==64
 gate=D/'disabled_port_probe_v2/constant_zero_we2/proc.json';obj=load(gate)['modules']['probe'];assert obj['ports']['out2']['bits']==['x','x'];assert all(obj['netnames'][n]['bits']==['x','x'] for n in ['dut.Mem[0]','dut.Mem[1]']);bindings[str(gate)]=sha(gate)
 out=dict(status='ACTUAL_DISABLED_WRITE_PORTS_VERIFIED_CHECK_PASS_NOT_FUNCTIONAL_PROOF',instances=rows,actual_dual_RAM_instances=16,finite_reference_checks=checks,reference_cycle2_out1_out2=[2,2],optimized_gate_out2_bits=obj['ports']['out2']['bits'],scope='64finite concrete initial-state/process-order cycle checks,not HDLsimulator receipts or fullfourstate proof. Source trace avoids crossport write/read collision;optimized pinnedfrontend output is literalX. Doesnot indict productionVTRblackbox flow or prove whole source design wrong. Merely check-assert pass cannot certify this invalid-driver optimization experiment.',documentation=[dict(title='Yosys memory cell semantics',url='https://yosyshq.readthedocs.io/projects/yosys/en/0.47/cell/word_mem.html',role='Writepriority/undefinedcollision and transparency must be specified separately;not a certificate for this pinnedfrontend.')],original_full9_gate=False,bindings=bindings)
 with (D/'write_port_obligations_v1.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
 print(out['status'],len(rows),checks)
if __name__=='__main__':main()
