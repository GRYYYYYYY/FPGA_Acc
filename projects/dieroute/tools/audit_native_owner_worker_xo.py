"""Audit packaged kernel ABI and proposed shared-master connectivity."""
from pathlib import Path
import argparse,json,hashlib,zipfile,xml.etree.ElementTree as ET,re,time
parser=argparse.ArgumentParser();parser.add_argument('build',type=Path);args=parser.parse_args();base=args.build
spec={
 'owner':('owner_die0','commands topology owners registry dirty_queue responses updates queue_control completion slots lanes die dies session command_capacity response_capacity update_capacity dirty_capacity command_read command_write response_read response_write update_read update_write max_commands max_updates max_visits subscriber_filter'.split(),{13,18,19,20,21,22,23,27},set(range(9))),
 'worker':('search_worker','labels queue journal parent observation_words metadata label_capacity queue_capacity journal_capacity dst edge session own present potential max_cost credit frontier_output operation'.split(),{11,13,14,15},{0,1,2,3,4,5,17}),
 'envelope':('owner_binding','packet envelope output_words status node owner worker membership serial session epoch operation ticket lane slot kind'.split(),{8,9,10,12},{0,1,2,3})}
entries=re.findall(r'^sp=(\w+\.\w+):HBM\[(\d+)\]$',(base/'connectivity.cfg').read_text(),re.M)
assert len(entries)==len({key for key,value in entries})
connections=dict(entries);assert set(connections)=={cu+'.'+names[i] for cu,names,u64,pointers in spec.values() for i in pointers}
cases={};total=0
for short,(cu,names,u64,pointers) in spec.items():
 xo=base/(short+'.xo')
 with zipfile.ZipFile(xo) as z:
  paths=[p for p in z.namelist() if p.endswith('/kernel.xml')];assert len(paths)==1
  payload=z.read(paths[0]);root=ET.fromstring(payload)
 arguments=sorted(root.iter('arg'),key=lambda a:int(a.attrib['id']))
 assert [a.attrib['name'] for a in arguments]==names
 assert [int(a.attrib['id']) for a in arguments]==list(range(len(names)))
 masters={p.attrib['name']:int(p.attrib['dataWidth']) for p in root.iter('port') if p.attrib['mode']=='master'}
 banks={}
 for i,a in enumerate(arguments):
  assert int(a.attrib['size'],16)==(8 if i in pointers or i in u64 else 4)
  if i in pointers:
   port=a.attrib['port'];assert port in masters
   bank=int(connections[cu+'.'+names[i]]);banks.setdefault(port,set()).add(bank)
  else:assert a.attrib['port']=='S_AXI_CONTROL'
 assert all(len(x)==1 for x in banks.values());assert set(banks)==set(masters)
 total+=len(masters);cases[short]={'cu':cu,'arguments':len(names),'master_widths':masters,'master_banks':{p:next(iter(b)) for p,b in banks.items()},'xo_sha256':hashlib.sha256(xo.read_bytes()).hexdigest(),'kernel_xml_sha256':hashlib.sha256(payload).hexdigest()}
assert total==9
assert cases['worker']['master_widths']=={'M_AXI_SEARCH_MEMORY':512,'M_AXI_TRAFFIC_MEMORY':512}
assert cases['envelope']['master_widths']=={'M_AXI_TRAFFIC_MEMORY':64,'M_AXI_OBSERVATIONS':512}
assert len(cases['owner']['master_widths'])==5 and all(width==512 for width in cases['owner']['master_widths'].values())
assert connections['owner_die0.responses']==connections['owner_die0.updates']==connections['owner_binding.packet']==connections['owner_binding.envelope']
assert connections['owner_binding.output_words']==connections['search_worker.observation_words']
result={'status':'passed','verified_ns':time.time_ns(),'cases':cases,'total_masters':total,'scope':'Actual packaged XO argument ABI and proposed cfg bank compatibility; final xclbin metadata/runtime groups and physical placement remain separate','board_result':False,'research_complete':False}
(base/'xo_abi_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':'passed','total_masters':total,'argument_counts':{k:v['arguments'] for k,v in cases.items()}}))
