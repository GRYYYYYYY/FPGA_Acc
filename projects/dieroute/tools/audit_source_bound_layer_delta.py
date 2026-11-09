"""Verify a completed source-bound layer extension changes exactly one header."""
from pathlib import Path
import argparse,difflib,hashlib,json

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('build',type=Path);parser.add_argument('--output',type=Path,required=True);a=parser.parse_args();B=a.build.resolve();state=json.loads((B/'manifest.json').read_text());assert state['status']=='new_source_bound_build_completed_dependency_and_native_compatibility_audits_required' and state['layer_limit']==4 and state['frozen_sources_unchanged'];parent=Path(state['parent_build']);oldfile=parent/'source_manifest.json';newfile=B/'source_manifest.json';old=json.loads(oldfile.read_text());new=json.loads(newfile.read_text());refs={}
 def sha(f):
  f=Path(f);h=hashlib.sha256(f.read_bytes()).hexdigest();refs[str(f)]=h;return h
 assert sha(oldfile)==state['parent_source_manifest_sha256']==new['parent_source_manifest_sha256'];assert sha(newfile)==state['source_manifest_sha256'];assert set(old['files_sha256'])==set(new['files_sha256']);assert old['symlinks']==new['symlinks']
 changed=[name for name,h in old['files_sha256'].items() if new['files_sha256'][name]!=h];assert changed==['source_vtr/vpr/src/base/vpr_types.h'],changed
 name=changed[0];before=(parent/name).read_bytes();after=(B/name).read_bytes();needle=b'constexpr int MAX_NUM_LAYERS = 2;';assert before.count(needle)==1;assert after==before.replace(needle,b'constexpr int MAX_NUM_LAYERS = 4;');assert sha(parent/name)==old['files_sha256'][name] and sha(B/name)==new['files_sha256'][name]
 api='source_vtr/vpr/src/base/vpr_api.cpp';assert sha(parent/api)==sha(B/api)==old['files_sha256'][api]==new['files_sha256'][api]
 assert sha(state['binary'])==state['binary_sha256'];sha(B/'manifest.json');sha(Path(__file__).resolve())
 result={'status':'verified_exact_single_header_layer_bound_extension','frozen_regular_files':len(new['files_sha256']),'changed_files':changed,'strict_native_timing_hook_unchanged':True,'header_diff':''.join(difflib.unified_diff(before.decode().splitlines(True),after.decode().splitlines(True),fromfile='parent/vpr_types.h',tofile='new/vpr_types.h')),'source_sha256':refs,'scope':'Source-manifest keysets/symlinks,exactheaderdelta,unchangedhookandcompletedbinarybinding. Fullcompileddependencyclosure andobservednativecompatibilityneed theirseparate audits. No historicallegacybinaryidentity orall-inputequivalence.','research_complete':False,'board_result':False}
 with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in result.items() if k not in ['source_sha256','header_diff']}))
if __name__=='__main__':main()
