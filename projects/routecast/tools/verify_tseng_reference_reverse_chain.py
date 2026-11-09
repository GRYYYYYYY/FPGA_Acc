"""Bind the two reference selections through the live next-update candidate."""
import json
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/tseng_reference_reverse_chain_2026-10-06';out.mkdir()
def read(p):return json.loads(p.read_text())
e=root/'experiments';bindings={}
for directory in ('tseng_swapped_quality_gate_2026-10-06','tseng_selected_reference_import_2026-10-06','tseng_reverse_native_import_2026-10-06','tseng_reverse_canonical_reload_2026-10-06','tseng_original_reference_canonical_reload_2026-10-06','tseng_reverse_quality_gate_2026-10-06'):
 for p in (e/directory).glob('*.json'):bindings[str(p)]=sha(p)
first=e/'tseng_swapped_quality_gate_2026-10-06';start=read(first/'selection.json');sv=read(first/'verification.json');assert sv['selection_sha256']==sha(first/'selection.json') and start['selected']=='reference' and sv['FULL_reload_success']
ledger=e/'tseng_selected_reference_import_2026-10-06';p=read(ledger/'protocol.json');r=read(ledger/'receipt.json');v=read(ledger/'verification.json');assert v['receipt_sha256']==sha(ledger/'receipt.json') and r['protocol_sha256']==sha(ledger/'protocol.json') and r['update_sha256']==sha(ledger/'update.json') and r['incumbent_sha256']==sha(ledger/'incumbent.json')
selected=root/'work/tseng_swapped_quality_gate_2026-10-06/design.route';assert p['inputs_sha256'][str(selected)]==start['files_sha256'][str(selected)]==sha(selected)
assert v['selected_native_paths_exact'] and v['next_candidate_connections']==1234 and r['live_state_restored']
imp=e/'tseng_reverse_native_import_2026-10-06';ir=read(imp/'receipt.json');iv=read(imp/'verification.json');assert ir['parent_sha256']==sha(ledger/'receipt.json') and iv['receipt_sha256']==sha(imp/'receipt.json') and iv['native_FULL_success'] and iv['serialized_paths_exactly_match_selection']
canonical=e/'tseng_reverse_canonical_reload_2026-10-06';cr=read(canonical/'receipt.json');cv=read(canonical/'verification.json');assert cr['parent_receipt_sha256']==sha(imp/'receipt.json') and cv['receipt_sha256']==sha(canonical/'receipt.json') and cv['verified_bundles']==1
last=e/'tseng_reverse_quality_gate_2026-10-06';lastp=read(last/'protocol.json');lr=read(last/'selection.json');lv=read(last/'verification.json');assert lastp['inputs_sha256']['predicted']==sha(canonical/'receipt.json') and lv['selection_sha256']==sha(last/'selection.json') and lr['selected']=='reference' and lv['FULL_reload_success'] and lv['packing_mismatches']==lv['trace_fixups']==0
for name,directory in [('predicted',canonical),('reference',e/'tseng_original_reference_canonical_reload_2026-10-06')]:assert lastp['inputs_sha256'][name]==sha(directory/'receipt.json')
assert all(sha(p)==h for p,h in lr['files_sha256'].items())
result={'source_sha256':sha(Path(__file__)),'evidence_sha256':bindings,'start_selection':'reference','start_reference_cpd_ns':start['reference_cpd_ns'],'next_candidate_cpd_ns':ir['cpd_ns'],'end_selection':'reference','end_reference_cpd_ns':lr['reference_cpd_ns'],'connections':1234,'scope':'Verified selected-reference import and one reverse-update staging/native/canonical/quality chain. Candidate discarded by CPD gate; no live publication/production concurrent commit, full sequential cost or speedup claim.'}
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('verified selected reference→imported ledger→reverse candidate→selected reference',ir['cpd_ns'],lr['reference_cpd_ns'])
