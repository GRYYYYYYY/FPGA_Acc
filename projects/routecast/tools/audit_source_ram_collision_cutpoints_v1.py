"""Local combinational overapproximation of source RAM collision conditions."""
import copy,json,hashlib,os,subprocess,resource
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'experiments/preroute_family_admission_v1_2026-10-20';D=R/'experiments/source_ram_collision_cutpoints_v1_2026-10-21';COMB={'$mux','$pmux','$not','$and','$or','$xor','$eq','$ne','$add','$sub','$ge','$gt','$le','$lt','$logic_not','$logic_and','$logic_or','$reduce_bool','$reduce_and','$reduce_or','$neg','$mul'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);m=json.loads((P/'structure_preflight_manifest_v5.json').read_text());binary=Path(m['yosys_binary']);runtime=Path(m['runtime_library']);env=os.environ.copy();env['LD_LIBRARY_PATH']=str(runtime.parent)+(':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '');sources=[P/'structure_preflight_v5'/n/'proc.json' for n in ['mcml','mkDelayWorker32B']];protocol={'scope':'Local parent-module combinational overapproximation. Sequential, memory, and hierarchy outputs become independent arbitrary binary inputs. SAT is not reachable collision proof. UNSAT would prove local exclusion under this overapproximation. No source edits or reset/init assumptions.','bindings':{str(p):sha(p) for p in [Path(__file__),binary,runtime,*sources]}};(D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
 for src in sources:
  design=json.loads(src.read_text());family=src.parent.name
  for module,obj in design['modules'].items():
   for cellname,ram in obj.get('cells',{}).items():
    if not ram['type'].endswith('dual_port_ram'):continue
    f=D/(family+'__'+module+'__'+cellname);f.mkdir();con=ram['connections'];assert con['we2']==['0'];mobj=copy.deepcopy(obj);cut=[];inputs=set(b for p in obj['ports'].values() if p['direction']=='input' for b in p['bits'] if isinstance(b,int))
    for n,c in list(mobj['cells'].items()):
     if c['type'] not in COMB:
      outs=[b for k,bs in c['connections'].items() if c['port_directions'][k]=='output' for b in bs if isinstance(b,int)];inputs.update(outs);cut.append({'cell':n,'type':c['type'],'output_bits':outs});del mobj['cells'][n]
    mobj.pop('memories',None);mobj['attributes']={};mobj['ports']={f'free_{i}':{'direction':'input','bits':[i]} for i in sorted(inputs)}
    top=max(b for c in obj['cells'].values() for bs in c['connections'].values() for b in bs if isinstance(b,int))+1;eqbit,collision=top,top+1;a=len(con['addr1']);assert a==len(con['addr2'])
    mobj['cells']['$rc_equal']={'hide_name':1,'type':'$eq','parameters':{'A_SIGNED':'0','B_SIGNED':'0','A_WIDTH':format(a,'032b'),'B_WIDTH':format(a,'032b'),'Y_WIDTH':format(1,'032b')},'attributes':{},'port_directions':{'A':'input','B':'input','Y':'output'},'connections':{'A':con['addr1'],'B':con['addr2'],'Y':[eqbit]}}
    mobj['cells']['$rc_collision']={'hide_name':1,'type':'$and','parameters':{'A_SIGNED':'0','B_SIGNED':'0','A_WIDTH':format(1,'032b'),'B_WIDTH':format(1,'032b'),'Y_WIDTH':format(1,'032b')},'attributes':{},'port_directions':{'A':'input','B':'input','Y':'output'},'connections':{'A':[eqbit],'B':con['we1'],'Y':[collision]}}
    for k,bs in [('collision',[collision]),('addr1',con['addr1']),('addr2',con['addr2']),('we1',con['we1'])]:mobj['ports']['rc_'+k]={'direction':'output','bits':bs};mobj.setdefault('netnames',{})['rc_'+k]={'hide_name':0,'bits':bs,'attributes':{}}
    inp=f/'cutpoint.json';inp.write_text(json.dumps({'modules':{'cutpoint':mobj}})+'\n');(f/'cutpoints.json').write_text(json.dumps(cut,indent=2)+'\n');ys=f/'commands.ys';ys.write_text(f'read_json {inp}\nhierarchy -top cutpoint\nopt_clean\ncheck -assert\nsat -prove rc_collision 0 -show rc_collision,rc_addr1,rc_addr2,rc_we1 -dump_json {f/"witness.json"}\n')
    def limits():resource.setrlimit(resource.RLIMIT_AS,(8<<30,8<<30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    with (f/'yosys.log').open('w') as out:code=subprocess.call([str(binary),'-Q','-T','-s',str(ys)],cwd=f,env=env,stdout=out,stderr=subprocess.STDOUT,preexec_fn=limits)
    log=(f/'yosys.log').read_text();status='LOCAL_COMBINATIONAL_EXCLUSION' if 'no model found: SUCCESS' in log else ('CUTPOINT_COLLISION_POSSIBLE_NOT_REACHABILITY' if 'model found: FAIL' in log else 'TOOL_FAILURE');rows.append({'family':family,'parent_module':module,'ram_cell':cellname,'exit_code':code,'status':status,'cut_cell_count':len(cut),'reachable_collision_proven':False,'folder':str(f.relative_to(R))});(D/'progress.json').write_text(json.dumps(rows,indent=2)+'\n');print(family,module,cellname,status,flush=True)
 (D/'results.json').write_text(json.dumps({'rows':rows},indent=2)+'\n')
if __name__=='__main__':main()
