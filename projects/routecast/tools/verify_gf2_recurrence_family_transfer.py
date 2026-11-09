"""Bind whole-family provenance, policy transfer, physical and native results."""
import json
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];e=root/'experiments';out=e/'gf2_recurrence_family_transfer_2026-10-06';out.mkdir();bindings={}
def read(directory,name):
 p=e/directory/name;bindings[str(p)]=sha(p);return json.loads(p.read_text())
f='gf2_recurrence_family_freeze_2026-10-06';p=read(f,'protocol.json');fr=read(f,'receipt.json');assert fr['protocol_sha256']==sha(e/f/'protocol.json') and p['input_widths']==[32,64,128]
assert all(sha(e/f/'source'/n)==h for n,h in p['sources_sha256'].items()) and all(sha(path)==h for path,h in p['native_inputs_sha256'].items())
front='gf2_recurrence_frontend_2026-10-06';mapping=read(front,'receipt.json');assert mapping['freeze_receipt_sha256']==sha(e/f/'receipt.json') and mapping['source_sha256']==sha(root/'tools/prepare_gf2_recurrence_frontend.py')
ref='gf2_recurrence_native_reference_2026-10-06';reference=read(ref,'receipt.json');rv=read(ref,'verification.json');rp=read(ref,'protocol.json');assert rv['receipt_sha256']==sha(e/ref/'receipt.json') and reference['protocol_sha256']==sha(e/ref/'protocol.json') and rp['family_freeze_sha256']==sha(e/f/'protocol.json')
pred='gf2_recurrence_joint_transfer_2026-10-06';candidate=read(pred,'receipt.json');pv=read(pred,'verification.json');pp=read(pred,'protocol.json');assert pv['receipt_sha256']==sha(e/pred/'receipt.json') and candidate['protocol_sha256']==sha(e/pred/'protocol.json') and pp['freeze_protocol_sha256']==sha(e/f/'protocol.json') and pp['policy']==p['policy']
assert all(sha(root/'tools'/n)==h==p['sources_sha256'][n] for n,h in pp['predictor_sources_sha256'].items())
imp='gf2_recurrence_native_import_2026-10-06';nr=read(imp,'receipt.json');np=read(imp,'protocol.json');assert nr['protocol_sha256']==sha(e/imp/'protocol.json') and np['parent_receipt_sha256']==sha(e/pred/'receipt.json');rows=[]
for i,width in enumerate(p['input_widths']):
 original=fr['records'][i];assert original['width']==width and sha(original['path'])==original['sha256']
 m=mapping['rows'][i];assert m['width']==width and m['complete_linear_basis_proof'] and m['ABC_CEC_equivalent'] and all(sha(path)==h for path,h in m['files_sha256'].items())
 q=reference['rows'][i];assert q['width']==width and q['native_success'] and all(sha(path)==h for path,h in q['files_sha256'].items());b=rv['rows'][i];assert b['width']==width
 c=candidate['rows'][i];cv=pv['rows'][i];assert c['width']==width and c['completed_connections']==c['required_connections']==cv['accepted_paths_checked']==b['sink_delays_checked']
 directory=e/pred/f'gf2_d{width}';assert sha(directory/'receipt.json')==c['candidate_sha256']==cv['original_candidate_sha256'];ep=json.loads((directory/'endpoints.json').read_text());assert set(ep['inputs'])=={'net','place','graph'} and all(sha(x['path'])==x['sha256'] for x in ep['inputs'].values())
 record=nr['rows'][i];assert record['width']==width and len(record['stages'])==2 and all(s['exit_code']==0 for s in record['stages'])
 for s in record['stages']:
  assert sha(root/'tools'/s['tool'])==np['cases'][i]['source_sha256'][s['tool']] and sha(e/imp/s['tool'].replace('.py','.log'))==s['log_sha256']
 native=e/f'gf2_d{width}_native_import_2026-10-06';r=json.loads((native/'receipt.json').read_text());v=json.loads((native/'verification.json').read_text());assert sha(native/'receipt.json')==record['candidate_receipt_sha256']==v['receipt_sha256'] and sha(native/'verification.json')==record['verification_sha256'];assert v['native_FULL_success'] and v['serialized_paths_exactly_match_selection'] and v['overflow_units']==0 and r['parent_sha256']==sha(directory/'receipt.json') and r['cpd_ns']==record['candidate_cpd_ns'] and v['reference_cpd_ns']==q['cpd_ns']
 for name in ('receipt.json','verification.json'):bindings[str(native/name)]=sha(native/name)
 rows.append({'width':width,'LUTs':m['mapped_luts'],'connections':c['required_connections'],'frozen_predictor_complete':True,'native_FULL_success':True,'reference_cpd_ns':q['cpd_ns'],'candidate_cpd_ns':r['cpd_ns'],'candidate_minus_reference_ns':r['cpd_ns']-q['cpd_ns'],'raw_packing_fixups':v['packing_trace_fixups'],'context_setup_s':c['context_setup_s'],'search_s':c['search_s']})
(out/'verification.json').write_text(json.dumps({'evidence_sha256':bindings,'rows':rows,'all_variants_one_family':True,'policy_retuned':False,'scope':'New local-generator family frozen before native routing; complete linear oracle and LUT6 CEC, nativeRC reference, untouched policy and all three raw candidate FULL/STA checked. Candidate serialized physical paths exact; postNET canonical zero-fixup proof/real updates/complete costs/resource-rank metrics remain open. Local prospective evidence only, not universal unseen-family or quality/speed/board gain.'},indent=2)+'\n');print(json.dumps(rows,indent=2))
