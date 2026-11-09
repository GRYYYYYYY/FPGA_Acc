"""Development native timing diagnosis and explicit extra NET release."""
import json,re,sys
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
from buffered_rc_node_classes import read,arc_delay
ROOT=Path(__file__).resolve().parents[2]
base=ROOT/'experiments/native_resume_target_partial_v7_2026-10-07';rp=base/'repair_verification.json';r=json.loads(rp.read_text())
route=base/'resume/canonical/design.route';cold=ROOT/'experiments/mux32_continuous_cold_baseline_2026-10-07/canonical/design.route';old=ROOT/'work/mux_crossbar_channel_pressure_2026-10-06/mux_w32_c128/design.route'
report=route.parent/'report_timing.setup.rpt';coldreport=cold.parent/'report_timing.setup.rpt'
for file in (route,report):assert sha(file)==r['canonical']['files'][str(file)]
first=report.read_text().split('#Path 2')[0];assert 'out:y3_7.outpad[0]' in first and 'd1_7.inpad[0]' in first
paths=[physical_paths(f) for f in (old,route,cold)]
assert all(len(p['y3_7'])==1 for p in paths)
assert paths[0]['y3_7']==paths[1]['y3_7'] and paths[1]['y3_7']!=paths[2]['y3_7']
assert paths[0]['d1_7']==paths[1]['d1_7']==paths[2]['d1_7'] and paths[0]['new_n848']==paths[1]['new_n848']==paths[2]['new_n848']
graph=old.parent/'rr_graph.xml';indices,classes,switches,digest=read(graph)
def delay(path):
 source=path[0][0];res,cap=classes[indices[source]]
 return res*cap/2+sum((arc_delay(classes,switches,indices[node],switch) for node,switch in path[1:]),0)
delays=[delay(p['y3_7'][0]) for p in paths]
prior=ROOT/'experiments/native_target_partial_seed_2026-10-07';pr=json.loads((prior/'receipt.json').read_text());assert sha(prior/'partial.route')==pr['partial_route_sha256']
assert 'y3_7' not in pr['removed_net_names']
out=ROOT/'experiments/native_resume_critical_release_seed_2026-10-07';out.mkdir(exist_ok=False)
# Fixed development intervention: remove the retained output NET on resumed native worst path.
lines=(prior/'partial.route').read_text().splitlines(keepends=True);keep=True;output=[];removed=0
for line in lines:
 m=re.match(r'^Net\s+\d+\s+\((.*)\)\s*$',line)
 if m:keep=m[1]!='y3_7';removed+=not keep
 if keep:output.append(line)
assert removed==1
partial=out/'partial.route';partial.write_text(''.join(output))
remaining=physical_paths(partial);previous=physical_paths(prior/'partial.route')
assert {n:Counter(ps) for n,ps in remaining.items()}=={n:Counter(ps) for n,ps in previous.items() if n!='y3_7'}
files=(rp,route,cold,old,report,coldreport,graph,prior/'receipt.json',prior/'partial.route',Path(__file__))
result=dict(bindings={str(f):sha(f) for f in files},partial_route_sha256=sha(partial),released_net='y3_7',initially_endpoint_unchanged=True,initially_retained_old_path=True,first_two_critical_nets_identical_all_modes=True,single_connection_expansion_rc_ns=[str(d*10**9) for d in delays],expansion_delta_resume_minus_cold_ns=str((delays[1]-delays[2])*10**9),scope='Retrospective development diagnosis. Native resumed worst path drives extra wholeNET release; cold used only diagnosis, not path transplant. Exact Fraction buffered path expansion is not complete native shared-tree STA. Partialseed remains incomplete and unaccepted; missing NET delay policy stays1ns. No prospective guarantee or netgain.')
(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(result['expansion_delta_resume_minus_cold_ns'])
