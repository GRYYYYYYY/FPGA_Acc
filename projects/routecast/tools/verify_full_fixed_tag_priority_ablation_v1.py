"""Single source-priority ablation under identical captured inputs and actual export."""
from pathlib import Path
import json,re,hashlib
R=Path(__file__).resolve().parents[1];E=R/'experiments';P=E/'full_source_export_fixed_tag_priority_ablation_v24_2026-10-09';B=E/'full_source_export_preedge_write_guard_trace_v23_2026-10-09';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();protocol=json.load(open(P/'protocol.json'))
for f,h in protocol['bindings'].items():assert sha(Path(f))==h
assert sha(B/'preedge_guard_audit.json')==protocol['baseline_audit_sha256']
for n in ['design.v','primitives.v','tb.v','control.py','run.py','frozen_bus_trace.json']:assert (P/n).read_bytes()==(B/n).read_bytes()
change=protocol['replacement'];assert (B/'reference.v').read_text().count(change['old'])==1;assert (P/'reference.v').read_text()==(B/'reference.v').read_text().replace(change['old'],change['new'])
stages=json.load(open(P/'stages.json'));assert len(stages)==3 and all(s['exit_code']==0 for s in stages);log=(P/'control.log').read_text();parent=(B/'control.log').read_text();assert 'Fatal' not in log
def records(text,prefix):return re.findall(r'@"('+prefix+r'[^\n]*?)\\n"',text)
def fields(text):return dict(re.findall(r'([A-Za-z_0-9]+)=\s*([^\s]+)',text))
inputs=records(log,'BUS_INPUT');original=records(parent,'BUS_INPUT');assert len(inputs)==len(original)==512
for actual,expected in zip(inputs,original):
 a,b=fields(actual),fields(expected)
 for key in ['cycle','reset','debugReset','ready','rsp_valid','rsp_data','rsp_error']:assert a[key]==b[key],key
native=records(log,'STARTUP_NATIVE_COMMIT');assert len(native)==1024 and native==records(parent,'STARTUP_NATIVE_COMMIT')
done=records(log,'ROUTECAST_FULL_COMPARE_DONE');assert len(done)==1;parent_done=records(parent,'ROUTECAST_FULL_COMPARE_DONE');coverage=records(log,'IBUS_COVERAGE');assert len(coverage)==1
guards=[fields(x) for x in records(log,'PREEDGE_WRITE_GUARD')];oldguards=[fields(x) for x in records(parent,'PREEDGE_WRITE_GUARD')];assert len(guards)==len(oldguards)==9
assert guards[0]['src_suppress']=='x' and guards[0]['native_we']=='x'
assert guards[0]['src_we'] in ['0','1','x','z']  # observe outcome, do not assume propagation across procedural RAM enable
native_guard_fields=['native_we','native_done','native_high','guard','guard8','guard9','guard2','guard3','native_refill','native_error','native_hit','native_uncached']
for a,b in zip(guards,oldguards):
 for key in native_guard_fields:assert a[key]==b[key],key
diff=records(log,'DIFF');old_diff=records(parent,'DIFF')
out={'source_single_change_verified':True,'actual_driver_input_cycles_identical':512,'actual_native_pending_records_identical':1024,'initial_source_we_baseline':oldguards[0]['src_we'],'initial_source_we_variant':guards[0]['src_we'],'native_we':guards[0]['native_we'],'mismatch_marker':done,'baseline_mismatch_marker':parent_done,'printed_diff_records_equal':diff==old_diff,'printed_diff_count':len(diff),'coverage':coverage,'guards':guards,'functional_admission':False,'scope':'Source diagnostic ablation only. Initial write-enable alignment changes are not a repair of original source/export. Aggregate and printed differences do not certify all mismatch positions or overall equivalence.','bindings':{str(f):sha(f) for f in [Path(__file__),P/'protocol.json',P/'control.log',P/'stages.json',B/'control.log']}}
(P/'tag_priority_ablation_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ['initial_source_we_baseline','initial_source_we_variant','native_we','mismatch_marker','baseline_mismatch_marker','printed_diff_records_equal','coverage']},indent=2))
