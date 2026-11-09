"""Bind paired HLS area reduction to the actual hardware-compile XO and flags."""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json,re,xml.etree.ElementTree as E
R=Path(__file__).resolve().parents[1]
def main():
 B=R/'work/native_integrated_control_stages_hw_20261015';D=R/'work/native_start_validate_only_hw_20261017';P=R/'work/lean_start_actual_XO_comparison_20261017';P.mkdir(exist_ok=False)
 refs={}
 def sha(f):
  h=hashlib.sha256()
  with Path(f).open('rb') as stream:
   for block in iter(lambda:stream.read(1048576),b''):h.update(block)
  refs[str(f)]=h.hexdigest();return h.hexdigest()
 old=json.loads((B/'commit_compiled_XO_review.json').read_text());new=json.loads((D/'commit_compiled_XO_review.json').read_text());paired=json.loads((R/'work/native_start_validate_only_HLS_v2_20261016/independent_audit.json').read_text())
 assert old['resources']==paired['outcomes'][0]['resources'] and new['resources']==paired['outcomes'][1]['resources']
 assert sha(B/'commit.xo')==old['xo_sha256']==new['parent_xo_sha256'] and sha(D/'commit.xo')==new['xo_sha256']
 pp=Path(new['preprocessed']);assert sha(pp)==new['preprocessed_sha256'];text=re.sub(r'\s+','',pp.read_text())
 a=text.index('voidphase_start_only(');b=text.index('voidphase_execute(',a);helper=text[a:b];execute=text[b:]
 assert 'e.insert(' not in helper and 'e.load(net_space,other,false)' in helper
 assert 'op==commit_start' in execute and 'e.insert(' in execute
 name='dieroute_net_commit_sharded_hbm';interfaces=[]
 for directory,review in [(B,old),(D,new)]:
  with ZipFile(directory/'commit.xo') as z:
   root=E.fromstring(z.read(name+'/kernel.xml'));kernel=root if root.tag=='kernel' else root.find('kernel')
   interfaces.append(([v.attrib for v in kernel.find('ports')],[v.attrib for v in kernel.find('args')],kernel.get('hwControlProtocol')))
   assert hashlib.sha256(z.read(name+'/cpu_sources/net_commit_sharded_hbm.cpp')).hexdigest()==sha(directory/'source/net_commit_sharded_hbm.cpp')==review['source_sha256']
 assert interfaces[0]==interfaces[1]
 p=json.loads((D/'protocol.json').read_text());link=p['link_command']
 for label in ['worker','snapshot']:
  assert str(B/(label+'.xo')) in link and sha(B/(label+'.xo'))==json.loads((B/(label+'_compiled_XO_review.json')).read_text())['xo_sha256']
 for f in [B/'commit_compiled_XO_review.json',D/'commit_compiled_XO_review.json',R/'work/native_start_validate_only_HLS_v2_20261016/independent_audit.json',D/'protocol.json',Path(__file__)]:sha(f)
 result=dict(status='actual_hw_XO_matches_paired_HLS_area_ABI_and_validation_only_helper',old_resources=old['resources'],new_resources=new['resources'],resource_delta={k:new['resources'][k]-old['resources'][k] for k in old['resources']},start_helper_has_insertion=False,execute_has_start_and_insertion=True,source_sha256=refs,scope='Actual v++ hardware compilation, embedded sources and preprocessed helper split checked; frozen worker/snapshot binary reuse and external ABI preserved. No routed resource/timing/legality or unique congestion cause established.',adopted=False,research_complete=False,board_result=False)
 (P/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'}))
if __name__=='__main__':main()
