"""Full revised frontend accounting and re-alignment to authenticated native audit."""
import json
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
root=Path('experiments/stereo_prospective_validation_2026-10-05');new=root/'endpoints_undriven_v2';old=root/'endpoints';native=root/'native_route_labels_audit'
if (new/'accounting_alignment_audit.json').exists():raise ValueError('fresh audit required')
receipt=json.loads((new/'receipt.json').read_text());protocol=json.loads((new/'protocol.json').read_text());assert receipt['protocol_sha256']==sha(new/'protocol.json');assert all(sha(new/n)==h for n,h in receipt['output_sha256'].items());assert all(sha(new/'source'/n)==h for n,h in protocol['source_sha256'].items())
previous=json.loads((old/'receipt.json').read_text());assert all(sha(old/n)==h for n,h in previous['output_sha256'].items())
e=json.loads((new/'endpoints.json').read_text());m=json.loads((new/'mapping.json').read_text());oe=json.loads((old/'endpoints.json').read_text());om=json.loads((old/'mapping.json').read_text())
assert e['graph_sha256']==oe['graph_sha256'];assert e['net_names']==oe['net_names'];assert m['pin_details']==om['pin_details']
old_excluded={r['net_id']:r for r in oe['excluded_nets']};excluded={r['net_id']:r for r in e['excluded_nets']};assert len(excluded)==len(e['excluded_nets']);assert all(excluded[n]==r for n,r in old_excluded.items())
added=set(excluded)-set(old_excluded)
for n in added:
 row=excluded[n];name=e['net_names'][str(n)];assert row['primitive_evidence']==m['undriven_outputs'][name];assert row['constant_value'] is None
assert e['connections']==[r for r in oe['connections'] if r['net_id'] not in added]
raw=Counter(r['net_id'] for r in m['pin_details'] if r['role']=='SINK');assert sum(raw.values())==len(e['connections'])+sum(r['sink_pins'] for r in excluded.values())
for n,r in excluded.items():assert raw[n]==r['sink_pins']
retained=Counter((r['net_id'],r['sink']) for r in e['connections']);expected=Counter((r['net_id'],r['rr_node']) for r in m['pin_details'] if r['role']=='SINK' and r['net_id'] not in excluded);assert retained==expected
nr=json.loads((native/'receipt.json').read_text());assert nr['physical_checks_pass'] and nr['overflow_units']==0 and nr['inputs_unchanged'];assert nr['protocol_sha256']==sha(native/'protocol.json');assert all(sha(native/n)==h for n,h in nr['outputs'].items())
labels=json.loads((native/'physical_branches.json').read_text());nets={r['net_id'] for r in e['connections']};fields=lambda r:(r['net_id'],r['source'],r['sink']);assert Counter(fields(r) for r in e['connections'])==Counter(fields(r) for r in labels['connections'] if r['net_id'] in nets)
result={'connections':len(e['connections']),'raw_sink_pin_details':sum(raw.values()),'excluded_sink_pins':sum(r['sink_pins'] for r in excluded.values()),'newly_excluded_nets':sorted(added),'all_original_physical_mapping_details_exact':True,'all_remaining_connection_records_exact':True,'full_raw_retained_excluded_accounting_exact':True,'native_retained_multiset_exact':True,'endpoint_sha256':sha(new/'endpoints.json'),'mapping_sha256':sha(new/'mapping.json'),'native_receipt_sha256':sha(native/'receipt.json'),'source_sha256':sha(__file__),'revision_provenance':protocol['revision'],'scope':'revised frontend full accounting and native cohort match; native physical evidence reused by hash, not rerun; no prediction/QoR or prospective holdout claim'}
(new/'accounting_alignment_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
