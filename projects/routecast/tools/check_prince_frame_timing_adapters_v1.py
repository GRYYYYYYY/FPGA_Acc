"""All12 positive current timing loads and cross-frame/epoch rejection tests."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from load_prince_current_initial_timing_v1 import load,epoch
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def main():
 root=R/'experiments/prince_frame_timings_v1_2026-10-20';vp=root/'verification.json';v=read(vp);assert len(v['rows'])==12 and all(sha(p)==h for p,h in v['bindings'].items());cases={r['case']:r for r in v['rows']};passed=[];rejected=[];data={}
 def reject(name,d,ep,tag):
  try:load(d,ep,expected_epoch=tag)
  except ValueError:rejected.append(name)
  else:raise AssertionError(name)
 for r in v['rows']:
  d=Path(r['timing_directory']);ep=Path(r['endpoint']);tag=r['timing_epoch_sha256'];assert epoch(d)==tag;rows=load(d,ep,expected_epoch=tag);assert len(rows)==4802;data[r['case']]=rows;passed.append(r['case']);reject(r['case']+':wrong_epoch',d,ep,'0'*64)
 for width in [96,128,160]:
  source=cases[f'w{width:03d}/source']
  for episode in range(1,4):
   target=cases[f'w{width:03d}/episode_{episode:02d}'];reject(target['case']+':stale_source_timing',source['timing_directory'],target['endpoint'],source['timing_epoch_sha256'])
  for other in [w for w in [96,128,160] if w!=width]:
   target=cases[f'w{other:03d}/source'];reject(source['case']+f':wrong_graph_width{other}',source['timing_directory'],target['endpoint'],source['timing_epoch_sha256'])
 assert len(passed)==12 and len(rejected)==27;changes=[]
 for width in [96,128,160]:
  source=data[f'w{width:03d}/source']
  for episode in range(1,4):
   case=f'w{width:03d}/episode_{episode:02d}';target=data[case];changes.append(dict(case=case,changed_native_float32_criticalities=sum(source[cid]['criticality_bits']!=target[cid]['criticality_bits'] for cid in source),scope='Input timing difference only, not label/quality or causal feature attribution.'))
 bindings={str(p):sha(p) for p in [vp,Path(__file__).resolve(),R/'tools/load_prince_current_initial_timing_v1.py']}
 with (root/'adapter_contract_verification_v1.json').open('x') as f:json.dump(dict(status='ALL12_CURRENT_FRAME_LOADS_AND27_STALE_FRAME_GRAPH_EPOCH_REJECTIONS_PASS',positive_cases=passed,rejected_contracts=rejected,current_input_differences=changes,total_verified_CIDs=12*4802,bindings=bindings,scope='Current initialized timing only. No budget, predictor or routed label evaluation; All12 PRINCE captures are fresh; no source or previous-design timing reused.'),f,indent=2)
 print('ALL12_TIMING_ADAPTERS_PASS',len(passed),len(rejected));print(json.dumps(changes))
if __name__=='__main__':main()
