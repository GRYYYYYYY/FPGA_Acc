"""Explicit physical implementation candidate, not an assertion that X means zero."""
import json,copy,hashlib,os,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'shallow_ram_address_completion_v1_2026-10-21';P=E/'source_ram_bank_sampling_v1_2026-10-21';B=E/'parmys_source_provenance_replay_v1_2026-10-21'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);v=json.loads((B/'verification_v1.json').read_text());m=json.loads((E/'preroute_family_admission_v1_2026-10-20/structure_preflight_manifest_v5.json').read_text());binary=Path(m['yosys_binary']);runtime=Path(m['runtime_library']);env=os.environ.copy();env['LD_LIBRARY_PATH']=str(runtime.parent)+(':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '');(D/'protocol.json').write_text(json.dumps({'scope':'Explicit physical row placement choice: unused high row bits tied0 in private candidate; logical low bits and all RAM clock/data/enable/output ports retained. Not four-state equivalence to X-padded mapped artifact. Logical source and functional library unchanged. Address injectivity and cross-port prefix consistency alone do not establish memory/source equivalence.','bindings':{str(p):sha(p) for p in [Path(__file__),B/'verification_v1.json',binary,runtime,*[P/r['source']/'candidate.json' for r in v['rows']]]}},indent=2)+'\n');rows=[]
 for row in v['rows']:
  n=row['source'];f=D/n;f.mkdir();design=json.loads((P/n/'candidate.json').read_text());old=copy.deepcopy(design);mod=design['modules'][n];changes=[];groups=[]
  for g in row['groups']:
   a=g['address_bits']
   if a>=11:continue
   count=0
   for cn in g['descendant_cells']:
    c=mod['cells'][cn]
    for port in ['addr1','addr2'] if c['type']=='dual_port_ram' else ['addr']:
     bits=c['connections'][port];assert len(bits)==11 and bits[a:]==['x']*(11-a);assert all(x not in ['x','z'] for x in bits[:a]);before=bits[:];bits[a:]=['0']*(11-a);changes.append({'cell':cn,'port':port,'before':before,'after':bits[:],'logical_address_bits':a});count+=11-a
   groups.append({'source_instance':g['source_instance'],'logical_address_bits':a,'lane_count':g['data_bits'],'physical_cells':len(g['descendant_cells']),'high_address_connections_completed':count,'logical_address_count':1<<a})
  (f/'candidate.json').write_text(json.dumps(design)+'\n');(f/'address_changes.json').write_text(json.dumps(changes)+'\n');ys=f/'check.ys';ys.write_text(f'read_json {f/"candidate.json"}\nhierarchy -top {n}\ncheck -assert\nstat\n')
  with (f/'check.log').open('w') as out:code=subprocess.call([str(binary),'-Q','-T','-s',str(ys)],cwd=f,env=env,stdout=out,stderr=subprocess.STDOUT)
  rows.append({'source':n,'groups':groups,'changed_address_ports':len(changes),'completed_high_bits':sum(g['high_address_connections_completed'] for g in groups),'structural_check_exit_code':code,'candidate_sha256':sha(f/'candidate.json')});print(n,code,rows[-1]['completed_high_bits'],flush=True)
 proofs=[]
 for a in sorted({g['logical_address_bits'] for row in rows for g in row['groups']}):
  for mode in ['shared_prefix','truncate_negative','mismatched_prefix_negative']:
   f=D/f'address{a}_{mode}';f.mkdir();aa='a';bb='b';pa='{prefix,a}';pb='{prefix,b}'
   if mode=='truncate_negative':pa='{prefix,1\'b0,a['+str(a-2)+':0]}';pb='{prefix,1\'b0,b['+str(a-2)+':0]}'
   if mode=='mismatched_prefix_negative':pb='{other_prefix,b}'
   verilog=f'module proof(input [{a-1}:0] a,b,input [{10-a}:0] prefix,other_prefix,output ok); wire[10:0] pa={pa},pb={pb}; assign ok=((pa==pb)==(a==b)); endmodule\n';vf=f/'proof.v';vf.write_text(verilog);ys=f/'commands.ys';ys.write_text(f'read_verilog {vf}\nhierarchy -top proof\nproc\nopt\nsat -verify -prove ok 1 -show a,b,pa,pb\n')
   with (f/'yosys.log').open('w') as out:code=subprocess.call([str(binary),'-Q','-T','-s',str(ys)],cwd=f,env=env,stdout=out,stderr=subprocess.STDOUT)
   text=(f/'yosys.log').read_text();proofs.append({'logical_bits':a,'mode':mode,'exit_code':code,'proof_passed':'no model found: SUCCESS' in text,'proof_failed':'proof did fail' in text});print('ADDRESS_PROOF',a,mode,code,flush=True)
 (D/'results.json').write_text(json.dumps({'rows':rows,'address_proofs':proofs},indent=2)+'\n')
if __name__=='__main__':main()
