#!/usr/bin/env python3
"""Exact XDC/HWDEF/HDL member equality; EDIF equivalence is a separate audit."""
import argparse,hashlib,json,zipfile
from pathlib import Path


def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
 return h.hexdigest()


def members(path):
 result={}
 with zipfile.ZipFile(path) as z:
  for info in z.infolist():
   if not info.filename.endswith(('.xdc','.hwdef','.v','.vhdl')):continue
   assert info.filename not in result,'duplicate archive member';h=hashlib.sha256()
   with z.open(info) as f:
    for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
   result[info.filename]=h.hexdigest()
 assert result and any(name.endswith('.xdc') for name in result),'missing constraint members'
 return result

if __name__=='__main__':
 if not __debug__:raise RuntimeError('assertions required')
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--control',type=Path,required=True);p.add_argument('--writeback',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 wb=a.writeback.resolve();m=json.loads((wb/'manifest.json').read_text());assert m['status']=='passed' and m['inputs_unchanged'] and m['physical_reload_equal'];control=a.control.resolve();routed=wb/'write/routed.dcp';original=sha(control);candidate=sha(routed);assert m['inputs'][str(control)]==original and m['artifacts']['write/routed.dcp']==candidate
 before=members(control);after=members(routed);assert before==after,'non-EDIF member change';assert sha(control)==original and sha(routed)==candidate
 result={'status':'passed','scope':'Exact XDC/HWDEF/HDL archive member equality; no EDIF, encrypted-logic or physical QoR claim','control_sha256':original,'routed_sha256':candidate,'members':before,'writeback_manifest_sha256':sha(wb/'manifest.json'),'inputs_unchanged':True};a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':'passed','members':len(before)}))
