"""Bind fixed-input quality comparison; retain every family outcome."""
import json
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];a=ROOT/'experiments/mux_budget_repair_quality_gate_2026-10-06';b=ROOT/'experiments/mux_old_priority_quality_gate_2026-10-06';out=ROOT/'experiments/mux_old_priority_comparison_2026-10-06';out.mkdir();bindings={};results=[]
for d in (a,b):
 for name in ('protocol.json','receipt.json','verification.json'):bindings[str(d/name)]=sha(d/name)
 v=json.loads((d/'verification.json').read_text());assert v['receipt_sha256']==sha(d/'receipt.json')
ap,bp=[json.loads((d/'protocol.json').read_text())for d in (a,b)];assert ap['cases']==bp['cases'] and ap['binaries']==bp['binaries']
av,bv=[json.loads((d/'verification.json').read_text())['rows']for d in (a,b)]
for x,y in zip(av,bv):
 assert x['width']==y['width'] and x['reference_cpd_ns']==y['reference_cpd_ns'];results.append(dict(width=x['width'],baseline_prediction_cpd_ns=x['predicted_cpd_ns'],old_priority_prediction_cpd_ns=y['predicted_cpd_ns'],prediction_change_percent=100*(y['predicted_cpd_ns']/x['predicted_cpd_ns']-1),old_priority_worse_than_reference_percent=100*(y['predicted_cpd_ns']/y['reference_cpd_ns']-1),reference_cpd_ns=y['reference_cpd_ns'],selected=y['selected']))
(out/'report.json').write_text(json.dumps(dict(bindings=bindings,source_sha256=sha(Path(__file__)),rows=results,scope='Same frozen source/target pair/binaries/reference CPD, prediction policy differs; wholeNET ordering can alter ownership/repair paths. All outcomes retained. No statistical timing or universal quality improvement.'),indent=2)+'\n');print(results)
