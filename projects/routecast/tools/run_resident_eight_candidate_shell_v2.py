"""Original frozen eight-move sketch shell, fresh graph versus sealed reuse."""
import json,sys,time,importlib,resource
from pathlib import Path
from pre_route_endpoints import sha
from resident_graph_inputs_v1 import ResidentGraphInputs
R=Path(__file__).resolve().parents[1];E=R/'experiments';O=E/'xtea_placement_feedback_decisions_v1_2026-10-13'
def load(p):return json.loads(p.read_text())
def main():
 mode,out=sys.argv[1:];out=Path(out);out.mkdir(parents=True);producer=importlib.import_module('run_warm_compiled_context_v4');cache=ResidentGraphInputs(producer.load_endpoints)
 if mode=='resident':producer.load_endpoints=cache
 elif mode!='baseline':raise ValueError('mode')
 old=load(O/'decision.json');frozen={r['candidate_id']:r for r in old['rows']};rows=[dict(candidate_id=0,hpwl=frozen[0]['hpwl'],sketch_overflow=frozen[0]['sketch_overflow'])]
 for cid in range(1,9):
  source=O/f'candidate_{cid:02d}';prep=source/'prepared';target=out/f'candidate_{cid:02d}/model';start=time.perf_counter();producer.predict(E/f'xtea_placement_feedback_cohort_v2_2026-10-13/candidate_{cid:02d}/demand/endpoints.json',target,prep/'base/verification.json',prep/'timing',prep/'warm','local');elapsed=time.perf_counter()-start
  for name in ['initial.json','sketch.json']:assert load(target/name)==load(source/'model'/name)
  actual=load(target/'receipt.json');reference=load(source/'model/receipt.json');assert len(actual['rounds'])==len(reference['rounds'])
  for a,b in zip(actual['rounds'],reference['rounds']):assert {k:v for k,v in a.items() if k not in ['seconds','state_file']}=={k:v for k,v in b.items() if k not in ['seconds','state_file']}
  rows.append(dict(candidate_id=cid,hpwl=frozen[cid]['hpwl'],sketch_overflow=load(target/'sketch.json')['overflow_units'],model=str(target),producer_seconds=elapsed));print('EIGHT_SHELL_CASE',mode,cid,elapsed,flush=True)
 admitted=[r for r in rows if r['sketch_overflow']<=rows[0]['sketch_overflow']];key=lambda r:(r['hpwl'],r['candidate_id']);off=min(rows,key=key)['candidate_id'];on=min(admitted,key=key)['candidate_id'];assert (off,on)==(old['off_candidate'],old['on_candidate']);assert [r['candidate_id'] for r in admitted]==old['on_admitted_candidates']
 if mode=='resident':assert cache.stats==dict(requests=8,hits=7,misses=1)
 (out/'receipt.json').write_text(json.dumps(dict(mode=mode,rows=rows,cache_stats=cache.stats,peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,off_candidate=off,on_candidate=on,on_admitted_candidates=[r['candidate_id'] for r in admitted],scope='Preparedcohort replay;baseline means samecompiled sketch with freshgraph,not SKETCHoff. Priorstate/cohortprep/nativevalidation unpaid. Historicalnative labels not rerun.',bindings={str(p):sha(p) for p in [Path(__file__),R/'tools/resident_graph_inputs_v1.py',R/'tools/run_warm_compiled_context_v4.py',O/'decision.json']}),indent=2)+'\n')
if __name__=='__main__':main()
