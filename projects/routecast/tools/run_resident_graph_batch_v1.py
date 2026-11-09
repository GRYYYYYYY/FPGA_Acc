"""Cold-start included A-B-A warm-candidate batch, graph-only reuse optional."""
import json,sys,time,importlib
from pathlib import Path
from pre_route_endpoints import sha
from resident_graph_inputs_v1 import ResidentGraphInputs
R=Path(__file__).resolve().parents[1];E=R/'experiments';O=E/'xtea_placement_feedback_decisions_v1_2026-10-13'
def load(p):return json.loads(p.read_text())
def main():
 mode,out=sys.argv[1:];out=Path(out);out.mkdir(parents=True);producer=importlib.import_module('run_warm_compiled_context_v4');cache=ResidentGraphInputs(producer.load_endpoints)
 if mode=='resident':producer.load_endpoints=cache
 elif mode!='baseline':raise ValueError('mode')
 rows=[]
 for index,cid in enumerate([2,6,2]):
  source=O/f'candidate_{cid:02d}';prep=source/'prepared';target=out/f'case_{index}_{cid}/model';start=time.perf_counter();producer.predict(E/f'xtea_placement_feedback_cohort_v2_2026-10-13/candidate_{cid:02d}/demand/endpoints.json',target,prep/'base/verification.json',prep/'timing',prep/'warm','local');elapsed=time.perf_counter()-start
  for name in ['initial.json','sketch.json']:assert load(target/name)==load(source/'model'/name)
  actual=load(target/'receipt.json');reference=load(source/'model/receipt.json')
  for a,b in zip(actual['rounds'],reference['rounds']):assert {k:v for k,v in a.items() if k not in ['seconds','state_file']}=={k:v for k,v in b.items() if k not in ['seconds','state_file']}
  rows.append(dict(candidate_id=cid,index=index,model=str(target),producer_seconds=elapsed));print('GRAPH_BATCH_CASE',mode,index,cid,elapsed,flush=True)
 if mode=='resident':assert cache.stats==dict(requests=3,hits=2,misses=1)
 (out/'receipt.json').write_text(json.dumps(dict(mode=mode,rows=rows,cache_stats=cache.stats,bindings={str(p):sha(p) for p in [Path(__file__),R/'tools/resident_graph_inputs_v1.py',R/'tools/run_warm_compiled_context_v4.py']}),indent=2)+'\n')
if __name__=='__main__':main()
