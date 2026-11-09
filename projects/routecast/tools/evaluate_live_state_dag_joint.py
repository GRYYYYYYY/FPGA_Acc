"""Retrospective timing-plus-physical-wire decision; no routing oracle in gate."""
import json,re
from pathlib import Path
import xml.etree.ElementTree as ET
from fractions import Fraction as F
from pre_route_endpoints import sha
from stream_native_route_audit_cached import audit
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'experiments/live_state_dag_screen_replay_2026-10-07'
rp=base/'receipt.json';r=json.loads(rp.read_text());ep=base/'native_decision_evaluation.json';ev=json.loads(ep.read_text());assert ev['bindings'][str(rp)]==sha(rp)
bindings={str(rp):sha(rp),str(ep):sha(ep)};contexts={};rows=[]
for x,label in zip(r['rows'],ev['rows']):
 w,i=x['width'],x['index'];assert (w,i)==(label['width'],label['index'])
 if w not in contexts:
  graph=ROOT/f'work/mux_crossbar_channel_pressure_2026-10-06/mux_w{w}_c128/rr_graph.xml';route=ROOT/f'experiments/mux_old_full_timing_graph_2026-10-06/w{w}/canonical/design.route';log=route.parent/'reload.log'
  bindings.update({str(p):sha(p) for p in (graph,route,log)})
  root=ET.parse(graph).getroot();spans={}
  for n in root.find('rr_nodes'):
   if n.get('type') in ('CHANX','CHANY'):
    loc=n.find('loc');spans[int(n.get('id'))]=1+int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))
  a=audit(graph,route);wire=sum(spans.get(int(n),0)*count for n,count in a['node_occupancy'].items())
  assert wire==int(re.findall(r'Total wirelength:\s*(\d+)',log.read_text())[-1])
  contexts[w]=(spans,wire)
 spans,oldwire=contexts[w]
 sf=ROOT/f'experiments/mux_full_cohort_cold_lifecycle_2026-10-06/mux_w{w}_m{i}_0/accepted_state.json';assert x['inputs'][str(sf)]==sha(sf)
 s=json.loads(sf.read_text());wire=sum(spans.get(int(n),0)*count for n,count in s['ledger'].items())
 modelpass=x['decision']['model_admitted'] and wire<=oldwire
 nativepass=label['native_timing_nonregression'] and wire<=oldwire
 rows.append(dict(width=w,index=i,published_wirelength=oldwire,candidate_wirelength=wire,model_joint_admitted=modelpass,native_joint_nonregression=nativepass,false_joint_admission=modelpass and not nativepass,missed_joint_nonregression=not modelpass and nativepass))
assert all(sha(p)==h for p,h in bindings.items())
result=dict(source_sha256=sha(Path(__file__)),bindings=bindings,rows=rows,admissions=sum(x['model_joint_admitted'] for x in rows),scope='DEVELOPMENT archived complete native cold-state vectors; actual NET-union physical spans and original published wire log parity. Candidate ledgers reuse prior authenticated complete-route proofs. Proposed native CPD evaluator only. No prospective prediction, new native run or netgain.')
(base/'joint_decision_evaluation.json').write_text(json.dumps(result,indent=2)+'\n');print(rows)
