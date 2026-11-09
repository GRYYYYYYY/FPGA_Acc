"""Check constraint-minus-slack against a real fixed-route 10ns-clock analysis."""
import hashlib,json,sys
from decimal import Decimal
from pathlib import Path
from native_setup_path_parser_v2 import parse
from native_setup_path_parser import parse as old

D=Path('work/native_nonzero_setup_constraint_probe_v3_20261016');report=D/'report_timing.setup.rpt';text=report.read_text();native=json.loads((D/'result.json').read_text())
try:parse(text)
except AssertionError as e:rejection=str(e)
else:raise AssertionError('Nonzero constraint silently accepted without domain map')
assert 'explicit global domain setup constraints' in rejection
paths=parse(text,{('pclk','pclk'):10});effective=max(Decimal(p['effective_delay_ns']) for p in paths)
assert abs(effective-Decimal(native['native_cpd_ns']))<=Decimal('0.0005')
assert max(Decimal(p['effective_delay_ns']) for p in old(text))!=effective
inputs=[report,D/'result.json',D/'launch.json',D/'clock10.sdc',Path('tools/native_setup_path_parser_v2.py'),Path(__file__)]
checks=[]
P=Path('work/native_joint_budget_net_repair_v2_20261016')
for name in ['ex5p','diffeq','alu4']:
    p=P/name/'initial/native_validation/report_timing.setup.rpt';a=old(p.read_text());b=parse(p.read_text())
    assert len(a)==len(b)
    for x,y in zip(a,b):assert all(y[k]==v for k,v in x.items())
    checks.append(dict(case=name,zero_constraint_paths_preserved=len(a)));inputs.append(p)
source=Path('work/vpr_four_layer_build_20261015/source_vtr/libs/EXTERNAL/libtatum/libtatum/tatum/timing_paths.cpp')
assert 'Time cpd = Time(constraint) - slack;' in source.read_text();inputs.append(source)
source=Path('work/vpr_four_layer_build_20261015/source_vtr/libs/EXTERNAL/libtatum/libtatum/tatum/TimingReporter.cpp');inputs.append(source)
O=Path('work/native_setup_constraint_accounting_checks_20261016');O.mkdir(exist_ok=False)
output=dict(status='explicit_global_constraint_parser_matches_native_nonzero_clock_and_preserves_zero_constraint_reports',native_cpd_ns=native['native_cpd_ns'],parsed_printed_effective_cpd_ns=str(effective),parsed_old_negative_slack_ns=str(max(Decimal(p['effective_delay_ns']) for p in old(text))),missing_constraint_rejected=True,zero_constraint_checks=checks,source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},research_complete=False,scope='One real pclk10ns fixed-route diffeq analysis. Uses explicit global domain constraint, not node-specific printed edge. Does not infer arbitrary SDC, validate exceptions/multicycle/cross-domain cases, reroute, alter original baseline or adopt parser into frozen policy.')
(O/'audit.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps({k:v for k,v in output.items() if k!='source_sha256'},indent=2))
