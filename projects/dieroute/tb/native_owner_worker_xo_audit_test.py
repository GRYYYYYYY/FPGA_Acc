"""Fault-test ABI auditor using metadata-only temporary ZIP fixtures, not images."""
from pathlib import Path
import tempfile,zipfile,xml.etree.ElementTree as ET,subprocess,json,hashlib,time
root=Path(__file__).resolve().parent.parent;base=root/'work/native_owner_worker_hw_emu_link_v1_20261014';audit=root/'tools/audit_native_owner_worker_xo.py'
xml={}
for short in ['owner','worker','envelope']:
 with zipfile.ZipFile(base/(short+'.xo')) as z:
  name=next(n for n in z.namelist() if n.endswith('/kernel.xml'));xml[short]=(name,z.read(name))
config=(base/'connectivity.cfg').read_text();results=[]
for fault in ['none','argument_name','argument_id','scalar_width','master_width','split_master_bank','broken_shared_bank','duplicate_connection']:
 with tempfile.TemporaryDirectory(prefix='dieroute_xo_metadata_') as temp:
  out=Path(temp)
  for short,(name,payload) in xml.items():
   tree=ET.fromstring(payload)
   if short=='worker':
    args=list(tree.iter('arg'))
    if fault=='argument_name':args[0].set('name','foreign_labels')
    if fault=='argument_id':args[1].set('id','0')
    if fault=='scalar_width':args[11].set('size','0x4')
   if short=='envelope' and fault=='master_width':next(p for p in tree.iter('port') if p.attrib['mode']=='master').set('dataWidth','128')
   with zipfile.ZipFile(out/(short+'.xo'),'w') as z:z.writestr(name,ET.tostring(tree))
  cfg=config
  if fault=='split_master_bank':cfg=cfg.replace('sp=search_worker.queue:HBM[14]','sp=search_worker.queue:HBM[15]')
  if fault=='broken_shared_bank':cfg=cfg.replace('sp=owner_binding.output_words:HBM[13]','sp=owner_binding.output_words:HBM[12]')
  if fault=='duplicate_connection':cfg+='sp=search_worker.queue:HBM[14]\n'
  (out/'connectivity.cfg').write_text(cfg)
  p=subprocess.run(['python3',str(audit),str(out)],capture_output=True,text=True)
  assert (p.returncode==0)==(fault=='none'),(fault,p.stdout,p.stderr)
  if fault!='none':assert not (out/'xo_abi_audit.json').exists()
  results.append({'fault':fault,'returncode':p.returncode,'expected_accept':fault=='none'})
r={'status':'passed','verified_ns':time.time_ns(),'cases':results,'auditor_sha256':hashlib.sha256(audit.read_bytes()).hexdigest(),'scope':'Auditor fault checks with metadata-only ZIP fixtures, not compile/link/execution proof'}
(base/'xo_auditor_fault_checks.json').write_text(json.dumps(r,indent=2)+'\n');print('One valid metadata fixture accepted; seven corrupt fixtures rejected.')
