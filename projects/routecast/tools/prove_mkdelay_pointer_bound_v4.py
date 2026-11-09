"""One-edge actual source-cache forwarding proof with explicit RAM-output cutpoints."""
import json,copy,hashlib,subprocess,os,resource
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'mkdelay_pointer_bound_sat_v4_2026-10-21';SRC=E/'preserved_source_ram_mapping_v1_2026-10-21/mkDelayWorker32B/preserved_boundary.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);m=json.loads((E/'preroute_family_admission_v1_2026-10-20/structure_preflight_manifest_v5.json').read_text());binary=Path(m['yosys_binary']);runtime=Path(m['runtime_library']);env=os.environ.copy();env['LD_LIBRARY_PATH']=str(runtime.parent)+(':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '');(D/'protocol.json').write_text(json.dumps({'scope':'Actual optimized source top state transition. All original FF/combinational cells retained;9opaque RAM macro outputs explicit independent binary inputs. Actual11bit modular occupancy bound<=512: reset base under reset0, one-edge induction under deasserted reset1 and initial bound1, and unbounded initial-state negative control. Existing actual FF/comb preserved; RAM outputs abstract binary. If induction fails, retain counterexample, do not declare reset invariant. Source reset deasserted1. Two states=one edge. Not full reset reachability, low10bit collision immunity, antiopt output immunity, or source equivalence.','bindings':{str(p):sha(p) for p in [Path(__file__),SRC,binary,runtime]}},indent=2)+'\n');rows=[]
 for prefix,ramname in [('mesgRF','dpram1'),('mesgWF','dpram2')]:
  for mode in ['reset_base','induction','unbounded_negative']:
   f=D/(prefix+'_'+mode);f.mkdir();design=json.loads(SRC.read_text());obj=design['modules']['mkDelayWorker32B'];target=copy.deepcopy(obj['cells'][ramname]);cut=[];free=set()
   for n,c in list(obj['cells'].items()):
    if c['type'].endswith(('single_port_ram','dual_port_ram')):
     bits=[b for p,bs in c['connections'].items() if c['port_directions'][p]=='output' for b in bs if isinstance(b,int)];free.update(bits);cut.append({'cell':n,'type':c['type'],'output_bits':bits});del obj['cells'][n]
   for b in sorted(free):obj['ports'][f'rc_ram_free_{b}']={'direction':'input','bits':[b]}
   top=1+max([b for c in obj['cells'].values() for bs in c['connections'].values() for b in bs if isinstance(b,int)]+list(free)+[b for v in obj['netnames'].values() for b in v['bits'] if isinstance(b,int)])
   def allocate(w):
    nonlocal top
    bits=list(range(top,top+w));top+=w;return bits
   def bits(n):return obj['netnames'][n]['bits']
   def cell(n,t,con,par):obj['cells']['$rc_'+n]={'hide_name':1,'type':t,'parameters':par,'attributes':{},'port_directions':{p:('output' if p in ['Q','Y'] else 'input') for p in con},'connections':con}
   clock=target['connections']['clk'];we=target['connections']['we1'];data=target['connections']['data1'];wp=bits(prefix+'_rWrPtr');rp=bits(prefix+'_rRdPtr');value=bits(prefix+'_wDataOut__wget');assert len(wp)==len(rp)==11 and len(data)==len(value)==256;shadowwe,shadowdata,shadowwp=allocate(1),allocate(256),allocate(11)
   for n,d,q in [('we',we,shadowwe),('data',data,shadowdata),('wp',wp,shadowwp)]:cell(n,'$dff',{'CLK':clock,'D':d,'Q':q},{'CLK_POLARITY':'1','WIDTH':format(len(q),'032b')})
   def eq(n,a,b):
    y=allocate(1);cell(n,'$eq',{'A':a,'B':b,'Y':y},{'A_SIGNED':'0','B_SIGNED':'0','A_WIDTH':format(len(a),'032b'),'B_WIDTH':format(len(b),'032b'),'Y_WIDTH':format(1,'032b')});return y
   physical_match=eq('physical_match',target['connections']['addr1'],target['connections']['addr2']);shadow_match=allocate(1);cell('shadowmatch','$dff',{'CLK':clock,'D':physical_match,'Q':shadow_match},{'CLK_POLARITY':'1','WIDTH':format(1,'032b')})
   delta=allocate(11);cell('delta','$sub',{'A':wp,'B':rp,'Y':delta},{'A_SIGNED':'0','B_SIGNED':'0','A_WIDTH':format(11,'032b'),'B_WIDTH':format(11,'032b'),'Y_WIDTH':format(11,'032b')});bound=allocate(1);cell('bound','$le',{'A':delta,'B':list(reversed(format(512,'011b'))),'Y':bound},{'A_SIGNED':'0','B_SIGNED':'0','A_WIDTH':format(11,'032b'),'B_WIDTH':format(11,'032b'),'Y_WIDTH':format(1,'032b')});shadow_bound=allocate(1);cell('shadowbound','$dff',{'CLK':clock,'D':bound,'Q':shadow_bound},{'CLK_POLARITY':'1','WIDTH':format(1,'032b')})
   match=shadow_match
   if mode!='unbounded_collision_negative':
    match=allocate(1);cell('boundedmatch','$and',{'A':shadow_match,'B':shadow_bound,'Y':match},{'A_SIGNED':'0','B_SIGNED':'0','A_WIDTH':format(1,'032b'),'B_WIDTH':format(1,'032b'),'Y_WIDTH':format(1,'032b')})
   expected=shadowdata
   if mode=='wrong_data_negative':expected=allocate(256);cell('bad_data','$not',{'A':shadowdata,'Y':expected},{'A_SIGNED':'0','A_WIDTH':format(256,'032b'),'Y_WIDTH':format(256,'032b')})
   equal=eq('equal',value,expected);cond=allocate(1);cell('condition','$and',{'A':shadowwe,'B':match,'Y':cond},{'A_SIGNED':'0','B_SIGNED':'0','A_WIDTH':format(1,'032b'),'B_WIDTH':format(1,'032b'),'Y_WIDTH':format(1,'032b')});no=allocate(1);cell('notcondition','$not',{'A':cond,'Y':no},{'A_SIGNED':'0','A_WIDTH':format(1,'032b'),'Y_WIDTH':format(1,'032b')});ok=allocate(1);cell('ok','$or',{'A':no,'B':equal,'Y':ok},{'A_SIGNED':'0','B_SIGNED':'0','A_WIDTH':format(1,'032b'),'B_WIDTH':format(1,'032b'),'Y_WIDTH':format(1,'032b')})
   for name,bs in [('rc_ok',ok),('rc_write',we),('rc_condition',cond),('rc_bound',bound)]:obj['ports'][name]={'direction':'output','bits':bs};obj['netnames'][name]={'hide_name':0,'bits':bs,'attributes':{}}
   file=f/'proof.json';file.write_text(json.dumps({'modules':{'mkDelayWorker32B':obj}})+'\n');(f/'cutpoints.json').write_text(json.dumps(cut,indent=2)+'\n');ys=f/'commands.ys';ys.write_text(f'read_json {file}\nhierarchy -top mkDelayWorker32B\nopt_clean\ncheck -assert\nsat -seq 2 -set wciS0_MReset_n {0 if mode=="reset_base" else 1} {"-set-at 1 rc_bound 1" if mode=="induction" else ""} -prove rc_bound 1 -prove-skip 1 -show rc_bound -verify\n')
   def limits():resource.setrlimit(resource.RLIMIT_AS,(8<<30,8<<30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
   with (f/'yosys.log').open('w') as log:code=subprocess.call([str(binary),'-Q','-T','-s',str(ys)],cwd=f,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limits)
   text=(f/'yosys.log').read_text();rows.append({'prefix':prefix,'mode':mode,'exit_code':code,'proof_passed':'no model found: SUCCESS' in text,'proof_failed':'proof did fail' in text,'cut_RAM_cells':len(cut),'folder':str(f.relative_to(R))});(D/'progress.json').write_text(json.dumps(rows,indent=2)+'\n');print(rows[-1],flush=True)
 (D/'results.json').write_text(json.dumps({'rows':rows},indent=2)+'\n')
if __name__=='__main__':main()
