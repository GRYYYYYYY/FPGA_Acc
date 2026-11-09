"""Isolated semantic-policy candidate, not an equivalent-source replacement claim."""
import json,hashlib,copy,subprocess,os
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'aux_word_forward_policy_v1_2026-10-21';SRC=E/'preserved_source_ram_mapping_v1_2026-10-21/mkDelayWorker32B/preserved_boundary.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);before=json.loads(SRC.read_text());after=copy.deepcopy(before);m=after['modules']['mkDelayWorker32B'];changes=[]
 for prefix,ram in [('mesgRF','dpram1'),('mesgWF','dpram2')]:
  oldbits=m['cells'][ram]['connections']['out2'];getter=m['netnames'][prefix+'_wDataOut__wget']['bits'];assert len(oldbits)==len(getter)==256
  consumers=[(n,c) for n,c in m['cells'].items() if c['type']=='$reduce_and' and c['connections']['A']==oldbits];assert len(consumers)==1;n,c=consumers[0];c['connections']['A']=getter[:];changes.append({'prefix':prefix,'ram':ram,'cell':n,'old_read_word_bits':oldbits,'new_cached_getter_bits':getter})
 root=m['ports']['prevent_hanging_nodes']['bits'][0];assert not any(root in bs for c in m['cells'].values() for p,bs in c['connections'].items() if c['port_directions'][p]=='input')
 assert before['modules']['mkDelayWorker32B']['ports']==m['ports'];assert set(before['modules']['mkDelayWorker32B']['cells'])==set(m['cells']);changed={x['cell'] for x in changes}
 for n,c in before['modules']['mkDelayWorker32B']['cells'].items():
  if n not in changed:assert m['cells'][n]==c
  else:
   expected=copy.deepcopy(c);expected['connections']['A']=next(x['new_cached_getter_bits'] for x in changes if x['cell']==n);assert m['cells'][n]==expected
 candidate=D/'candidate_boundary.json';candidate.write_text(json.dumps(after)+'\n');(D/'change_manifest.json').write_text(json.dumps({'changes':changes,'added_cells':0,'added_register_bits':0,'all_other_cells_exact':True},indent=2)+'\n');cfg=json.loads((E/'preroute_family_admission_v1_2026-10-20/structure_preflight_manifest_v5.json').read_text());binary=Path(cfg['yosys_binary']);runtime=Path(cfg['runtime_library']);env=os.environ.copy();env['LD_LIBRARY_PATH']=str(runtime.parent)+(':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '');(D/'protocol.json').write_text(json.dumps({'scope':'Explicit auxiliary observation-policy candidate:2raw cross-read reductions use existing whole-word cache getter instead. Existing transaction data path/registers/RAM clocks/resets/addresses/data/enables untouched. No baseline/source-file overwrite. This may select write-forwarded value where original raw RAM observer depended on collision order; NOT claimed equivalent or admitted.','bindings':{str(p):sha(p) for p in [Path(__file__),SRC,binary,runtime,candidate,D/'change_manifest.json']}},indent=2)+'\n');ys=D/'check.ys';ys.write_text(f'read_json {candidate}\nhierarchy -top mkDelayWorker32B\ncheck -assert\nscc -select\nselect -assert-none %\n');
 with (D/'yosys.log').open('w') as log:code=subprocess.call([str(binary),'-Q','-T','-s',str(ys)],cwd=D,env=env,stdout=log,stderr=subprocess.STDOUT)
 (D/'results.json').write_text(json.dumps({'structural_and_combinational_loop_check_exit_code':code},indent=2)+'\n');print('AUX_POLICY_STRUCTURAL_CHECK',code)
if __name__=='__main__':main()
