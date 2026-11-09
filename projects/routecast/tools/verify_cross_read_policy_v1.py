"""Verify abstract coherence receipts and exact minimal candidate delta, no admission."""
import json,hashlib,copy
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'cross_read_word_coherence_v1_2026-10-21';P=E/'aux_word_forward_policy_v1_2026-10-21'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 for root in [D,P]:
  for p,h in json.loads((root/'protocol.json').read_text())['bindings'].items():assert sha(Path(p))==h,p
 rows=json.loads((D/'results.json').read_text())['rows'];assert len(rows)==3
 for r in rows:
  log=(D/r['name']/'yosys.log').read_text()
  if r['name']=='shared_choice':assert r['exit_code']==0 and r['proof_passed'] and 'no model found: SUCCESS' in log
  else:assert r['exit_code']==1 and r['proof_failed'] and 'proof did fail' in log
 w=json.loads((D/'explicit_witness.json').read_text());old,new,ch,mixed=[int(w[k],16) for k in ['old_hex','new_hex','lane_choices_hex','mixed_hex']];mask=(1<<256)-1;assert mixed==((ch&new)|((~ch)&old&mask))==mask and old!=mask and new!=mask
 proto=json.loads((P/'protocol.json').read_text());source=next(Path(p) for p in proto['bindings'] if p.endswith('/mkDelayWorker32B/preserved_boundary.json'));before=json.loads(source.read_text());after=json.loads((P/'candidate_boundary.json').read_text());manifest=json.loads((P/'change_manifest.json').read_text());assert len(manifest['changes'])==2;expected=copy.deepcopy(before);a=before['modules']['mkDelayWorker32B'];b=after['modules']['mkDelayWorker32B'];muxes=[]
 for r in manifest['changes']:
  n=r['cell'];ram=r['ram'];prefix=r['prefix'];assert a['cells'][n]['type']=='$reduce_and';assert a['cells'][n]['connections']['A']==r['old_read_word_bits']==a['cells'][ram]['connections']['out2'];getter=a['netnames'][prefix+'_wDataOut__wget']['bits'];assert getter==r['new_cached_getter_bits'];expected['modules']['mkDelayWorker32B']['cells'][n]['connections']['A']=getter
  mux=[(cn,c) for cn,c in a['cells'].items() if c['type']=='$mux' and c['connections']['Y']==getter];assert len(mux)==1;cn,c=mux[0];assert len(c['connections']['S'])==1 and c['connections']['A']==a['cells'][ram]['connections']['out2'] and c['connections']['B']==a['netnames'][prefix+'_rCache']['bits'][:256];assert b['cells'][cn]==c;muxes.append({'prefix':prefix,'getter_mux':cn,'word_width':256,'shared_select_width':1})
 assert expected==after;root=a['ports']['prevent_hanging_nodes']['bits'][0];assert not any(root in bs for c in a['cells'].values() for p,bs in c['connections'].items() if c['port_directions'][p]=='input');assert json.loads((P/'results.json').read_text())['structural_and_combinational_loop_check_exit_code']==0;log=(P/'yosys.log').read_text();assert 'Found and reported 0 problems.' in log and 'Found 0 SCCs' in log
 out={'status':'ABSTRACT_COHERENCE_OBLIGATION_AND_MINIMAL_POLICY_DELTA_VERIFIED','coherence_SAT_positive':1,'coherence_SAT_negative_expected_failures':2,'explicit_abstract_witness_reduce_AND':[0,0,1],'candidate_changed_reduction_cells':2,'added_cells':0,'added_register_bits':0,'existing_shared_word_muxes':muxes,'all_other_original_design_fields_exact':True,'scope':'Independent lane choices can violate whole-word old/new membership and auxiliary reduction in abstract model. Not actual reset-reachable mapper failure. Candidate changes auxiliary observation to existing cached getter, an explicit semantic policy needing separate relation/refinement proof. Neither exact delta nor shared mux structure proves original-source equivalence.','bindings':{str(p.relative_to(R)):sha(p) for p in [D/'explicit_witness.json',D/'results.json',P/'candidate_boundary.json',P/'change_manifest.json',P/'yosys.log']}};(P/'verification_v1.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status'])
if __name__=='__main__':main()
