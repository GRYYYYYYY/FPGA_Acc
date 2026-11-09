"""Review existing successful compile without assuming headers are embedded in XO."""
import hashlib,json,re,sys,shutil,xml.etree.ElementTree as E
from decimal import Decimal
from pathlib import Path
from zipfile import ZipFile
R=Path(__file__).resolve().parents[1]
def main():
 origin=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();refs={}
 def sha(f):
  p=Path(f);key=str(p)
  if key not in refs:
   h=hashlib.sha256()
   with p.open('rb') as stream:
    for b in iter(lambda:stream.read(1048576),b''):h.update(b)
   refs[key]=h.hexdigest()
  return refs[key]
 x=json.loads((origin/'protocol.json').read_text());m=json.loads((origin/'manifest.json').read_text());assert m['compile_returncode']==0 and m['status']=='failed_or_prerequisite_not_met' and 'native_search_hbm_snapshot_search_sharded.hpp' in m['error']
 proc=Path('/proc')/str(m['pid'])/'cmdline';assert not proc.exists() or str(origin/'supervise.py').encode() not in proc.read_bytes()
 for group in ['source_sha256','prerequisite_sha256']:
  for f,h in x[group].items():assert sha(f)==h,f
 cmd=x['compile_command'];defines=[cmd[i+1] for i,v in enumerate(cmd[:-1]) if v=='-D'];assert {'DIEROUTE_NATIVE_HIGHER_G_TIE=1','DIEROUTE_NATIVE_PACKED_POTENTIAL8=1'}<=set(defines)
 top='dieroute_native_snapshot_search_sharded_hbm'
 with ZipFile(origin/'snapshot.xo') as z,ZipFile(x['parent_snapshot_xo']) as parent:
  k=E.fromstring(z.read(top+'/kernel.xml')).find('kernel');old=E.fromstring(parent.read(top+'/kernel.xml')).find('kernel');assert k.get('hwControlProtocol')==old.get('hwControlProtocol')=='ap_ctrl_chain'
  for tag in ['ports','args']:assert [v.attrib for v in k.find(tag)]==[v.attrib for v in old.find(tag)]
  assert hashlib.sha256(z.read(top+'/cpu_sources/native_snapshot_search_sharded_hbm.cpp')).hexdigest()==sha(origin/'source/native_snapshot_search_sharded_hbm.cpp')
  paths=[v for v in z.namelist() if v.endswith('/syn/report/csynth.xml')];assert len(paths)==1;xml=z.read(paths[0]);report=E.fromstring(xml);assert report.findtext('UserAssignments/Part')=='xcu280-fsvh2892-2L-e';assert Decimal(report.findtext('.//EstimatedClockPeriod'))<=Decimal('2.43309')
  embedded_headers=[v for v in z.namelist() if '/cpu_sources/' in v and v.endswith('.hpp')]
 preprocessed=list((origin/'snapshot_temp').rglob('native_snapshot_search_sharded_hbm.pp.0.cpp'));assert len(preprocessed)==1;pp=preprocessed[0];text=re.sub(r'\s+',' ',pp.read_text())
 for marker in ['if(packed)return (words[node>>3]>>((node&7u)*8u))&255UL;', 'return format <= (1?2u:1u);','return 1 && format==2;']:
  assert marker in text,marker
 for name in ['native_search_hbm_potential.hpp','native_search_hbm_snapshot_search_sharded.hpp','native_snapshot_search_sharded_hbm.cpp']:
  assert sha(origin/'source'/name)==sha(out/'source'/name)
 snapshot=out/'snapshot.xo'
 if not snapshot.exists():shutil.copy2(origin/'snapshot.xo',snapshot)
 assert sha(snapshot)==sha(origin/'snapshot.xo');(out/'compiled_csynth.xml').write_bytes(xml)
 for f in [origin/'protocol.json',origin/'manifest.json',origin/'compile.log',x['parent_snapshot_xo'],pp,Path(__file__).resolve()]:sha(f)
 result=dict(status='dual_snapshot_compiled_source_preprocessed_headers_ABI_numeric_gate_verified',compile_reused=True,compile_origin=str(origin),estimated_ns=report.findtext('.//EstimatedClockPeriod'),ports=len(k.find('ports')),arguments=len(k.find('args')),snapshot_xo_sha256=sha(snapshot),resources={v.tag:int(v.text) for v in report.find('.//AreaEstimates/Resources')},embedded_header_count=len(embedded_headers),source_sha256=refs,adopted=False,board_result=False,research_complete=False,scope='Successful original compile reused once. XO embeds CPP; immutable compiler input headers and actual saved preprocessed enabled decoder verified instead of requiring packaged headers. Original failed review preserved. No relink, runtime or performance result.')
 with (out/'compiled_XO_review.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'}))
if __name__=='__main__':main()
