"""Actual source-cache relation to one arbitrary tracked RAM row, no zero init."""
import json,hashlib,copy,subprocess,os,resource
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'message_read_alignment_sat_v1_2026-10-21';SRC=E/'preserved_source_ram_mapping_v1_2026-10-21/mkDelayWorker32B/preserved_boundary.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);cfg=json.loads((E/'preroute_family_admission_v1_2026-10-20/structure_preflight_manifest_v5.json').read_text());binary=Path(cfg['yosys_binary']);runtime=Path(cfg['runtime_library']);env=os.environ.copy();env['LD_LIBRARY_PATH']=str(runtime.parent)+(':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '');(D/'protocol.json').write_text(json.dumps({'scope':'Actual original cache/control FF and logic preserved.9RAM outputs become independent binary inputs. Add arbitrary fixed10bit row via self-holding FF, and256bit tracked memory row updated only by actual target writer1/data/address (no reset/init on tracked memory). One-edge read address alignment: next low10read pointer equals sampled actual RAM address2 under deasserted reset. Negative uses unadvanced previous pointer. No memory/read-data contract assumed in this alignment lemma, binary synchronous source IR only. Not full array/init/clock scheduling/aux-policy equivalence.','bindings':{str(p):sha(p) for p in [Path(__file__),SRC,binary,runtime]}},indent=2)+'\n');rows=[]
 for prefix,ram in [('mesgRF','dpram1'),('mesgWF','dpram2')]:
  for mode in ['read_alignment','old_pointer_negative']:
   f=D/(prefix+'_'+mode);f.mkdir();obj=copy.deepcopy(json.loads(SRC.read_text())['modules']['mkDelayWorker32B']);target=copy.deepcopy(obj['cells'][ram]);cut=[];free=set()
   for n,c in list(obj['cells'].items()):
    if c['type'].endswith('dual_port_ram'):
     bs=[b for p,bits in c['connections'].items() if c['port_directions'][p]=='output' for b in bits if isinstance(b,int)];cut.append({'cell':n,'output_bits':bs});free.update(bs);del obj['cells'][n]
   for b in sorted(free):obj['ports'][f'rc_ram_free_{b}']={'direction':'input','bits':[b]}
   top=1+max([b for c in obj['cells'].values() for bits in c['connections'].values() for b in bits if isinstance(b,int)]+list(free)+[b for v in obj['netnames'].values() for b in v['bits'] if isinstance(b,int)])
   def alloc(w):
    nonlocal top
    bs=list(range(top,top+w));top+=w;return bs
   def add(n,t,z,par):obj['cells']['$rc_'+n]={'hide_name':1,'type':t,'parameters':par,'attributes':{},'port_directions':{p:('output' if p in ['Y','Q'] else 'input') for p in z},'connections':z}
   def gate(n,t,a,b=None):
    y=alloc(1);z={'A':a,'Y':y};par={'A_SIGNED':'0','A_WIDTH':format(len(a),'032b'),'Y_WIDTH':format(1,'032b')}
    if b is not None:z['B']=b;par.update(B_SIGNED='0',B_WIDTH=format(len(b),'032b'))
    add(n,t,z,par);return y
   clk=target['connections']['clk'];row=alloc(10);mem=alloc(256);add('fixed_row','$dff',{'CLK':clk,'D':row,'Q':row},{'CLK_POLARITY':'1','WIDTH':format(10,'032b')});address=target['connections']['addr1'];we=target['connections']['we1'];data=target['connections']['data1'];assert len(address)==10 and len(data)==256 and target['connections']['we2']==['0'];write_row=gate('write_row','$eq',address,row);enable=gate('write_enable','$and',we,write_row)
   if mode=='no_memory_write_negative':enable=['0']
   if mode=='wrong_memory_data_negative':wrong=alloc(256);add('bad_data','$not',{'A':data,'Y':wrong},{'A_SIGNED':'0','A_WIDTH':format(256,'032b'),'Y_WIDTH':format(256,'032b')});data=wrong
   add('tracked_memory','$dffe',{'CLK':clk,'D':data,'EN':enable,'Q':mem},{'CLK_POLARITY':'1','EN_POLARITY':'1','WIDTH':format(256,'032b')});cache=obj['netnames'][prefix+'_rCache']['bits'];assert len(cache)==268;tag_match=gate('tag_match','$eq',cache[256:266],row);condition=gate('valid_match','$and',[cache[267]],tag_match);same=gate('data_equal','$eq',cache[:256],mem);no=gate('not_condition','$not',condition);ok=gate('relation','$or',no,same)
   sampled=alloc(10);sample_data=target['connections']['addr2'] if mode=='read_alignment' else obj['netnames'][prefix+'_rRdPtr']['bits'][:10];add('sampled_address','$dff',{'CLK':clk,'D':sample_data,'Q':sampled},{'CLK_POLARITY':'1','WIDTH':format(10,'032b')});ok=gate('read_aligned','$eq',obj['netnames'][prefix+'_rRdPtr']['bits'][:10],sampled)
   for name,bs in [('rc_relation',ok),('rc_row',row),('rc_valid_match',condition)]:obj['ports'][name]={'direction':'output','bits':bs};obj['netnames'][name]={'hide_name':0,'bits':bs,'attributes':{}}
   file=f/'proof.json';file.write_text(json.dumps({'modules':{'mkDelayWorker32B':obj}})+'\n');(f/'cutpoints.json').write_text(json.dumps(cut,indent=2)+'\n');ys=f/'commands.ys';reset=0 if mode=='reset_base' else 1;pre='' ;ys.write_text(f'read_json {file}\nhierarchy -top mkDelayWorker32B\nopt_clean\ncheck -assert\nsat -seq 2 -set wciS0_MReset_n {reset} {pre} -prove rc_relation 1 -prove-skip 1 -show rc_row,rc_valid_match,rc_relation -verify\n')
   def limits():resource.setrlimit(resource.RLIMIT_AS,(8<<30,8<<30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
   with (f/'yosys.log').open('w') as log:code=subprocess.call([str(binary),'-Q','-T','-s',str(ys)],cwd=f,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limits)
   text=(f/'yosys.log').read_text();rows.append({'prefix':prefix,'mode':mode,'exit_code':code,'proof_passed':'no model found: SUCCESS' in text,'proof_failed':'proof did fail' in text,'folder':str(f.relative_to(R))});(D/'progress.json').write_text(json.dumps(rows,indent=2)+'\n');print(prefix,mode,code,flush=True)
 (D/'results.json').write_text(json.dumps({'rows':rows},indent=2)+'\n')
if __name__=='__main__':main()
