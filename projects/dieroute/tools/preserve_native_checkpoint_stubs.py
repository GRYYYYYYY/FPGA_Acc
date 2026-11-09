#!/usr/bin/env python3
"""Restore original HDL stubs in a new DCP; verify every other member bytewise."""
import argparse,hashlib,json,shutil,zipfile
from pathlib import Path


def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for data in iter(lambda:f.read(8*1024*1024),b''):h.update(data)
 return h.hexdigest()


def inventory(path):
 result={}
 with zipfile.ZipFile(path) as z:
  for info in z.infolist():
   assert info.filename not in result,'duplicate archive member';h=hashlib.sha256()
   with z.open(info) as f:
    for data in iter(lambda:f.read(8*1024*1024),b''):h.update(data)
   result[info.filename]=h.hexdigest()
 return result

if __name__=='__main__':
 if not __debug__:raise RuntimeError('assertions required')
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--control',type=Path,required=True);p.add_argument('--writeback',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();control=a.control.resolve();wb=a.writeback.resolve();m=json.loads((wb/'manifest.json').read_text());assert m['status']=='passed' and m['inputs_unchanged'];source=wb/'write/routed.dcp';inputs={str(control):sha(control),str(source):sha(source)};assert m['inputs'][str(control)]==inputs[str(control)] and m['artifacts']['write/routed.dcp']==inputs[str(source)]
 a.output.mkdir(exist_ok=False);dest=a.output/'routed.dcp';before=inventory(source);original=inventory(control);stubs={name for name in before if name.endswith(('_stub.v','_stub.vhdl'))};assert stubs and stubs<=set(original)
 with zipfile.ZipFile(control) as old,zipfile.ZipFile(source) as src,zipfile.ZipFile(dest,'x',allowZip64=True) as dst:
  dst.comment=src.comment
  for info in src.infolist():
   selected=old if info.filename in stubs else src
   with selected.open(info.filename) as f,dst.open(info,'w',force_zip64=True) as target:shutil.copyfileobj(f,target,8*1024*1024)
 after=inventory(dest);assert set(after)==set(before)
 assert all(after[name]==(original[name] if name in stubs else before[name]) for name in before)
 auxiliary={name for name in after if name.endswith(('.xdc','.hwdef','.v','.vhdl'))};assert {name:after[name] for name in auxiliary}=={name:original[name] for name in original if name.endswith(('.xdc','.hwdef','.v','.vhdl'))}
 assert all(sha(path)==digest for path,digest in inputs.items());record={'status':'package_repaired_revalidation_required','inputs':inputs,'inputs_unchanged':True,'parent_writeback_manifest_sha256':sha(wb/'manifest.json'),'output':str(dest.resolve()),'output_sha256':sha(dest),'restored_stub_members':sorted(stubs),'all_other_member_payloads_equal':True,'auxiliary_members_equal_original':True,'scope':'Stub restoration only; fresh native loading/reports required before accepting this new DCP','board_result':False};(a.output/'manifest.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'status':record['status'],'stubs':sorted(stubs)}))
